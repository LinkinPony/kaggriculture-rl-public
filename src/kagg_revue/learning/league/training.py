"""Six-epoch isolated BC followed by synchronous, on-policy mutual learning."""

import gc
import time
from typing import Any

import orjson
import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.strata.loading import ResidentDataset
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.distributed import any_stop, barrier, gather, rank_world
from kagg_revue.learning.league import storage
from kagg_revue.learning.league.collection import collect
from kagg_revue.learning.league.config import League
from kagg_revue.learning.league.evaluation import evaluate
from kagg_revue.learning.league.telemetry import combine_pairs, member_outcomes
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.learning.pretraining.config import Demonstrations
from kagg_revue.learning.pretraining.train import initialize
from kagg_revue.learning.train import StopRequest
from kagg_revue.policy.inference import ActorRuntime


def _pretrain(config: League, state: dict[str, Any], stop: StopRequest) -> bool:
    rank, _ = rank_world()
    device = torch.device(
        config.experiment.execution.devices[rank]
        if config.experiment.execution
        else config.experiment.device
    )
    for name in config.members:
        recipe = config.member(name)
        child = orjson.loads((recipe.output_dir / "state.json").read_bytes())

        def requested(child: dict[str, Any] = child) -> bool:
            if (
                config.stop_after_bc_shards is not None
                and child.get("pretraining", {}).get("cursor", 0) >= config.stop_after_bc_shards
            ):
                stop.requested = True
            return stop.requested

        if rank == 0:
            write_json(
                config.experiment.output_dir / "league-progress.json",
                {
                    "phase": "bc",
                    "active_member": name,
                    "epochs": config.bc_epochs,
                    "members": state["members"],
                },
            )
        initialize(
            recipe, runtime_settings(recipe), child, requested, dataset_class=ResidentDataset
        )
        if any_stop(stop.requested, device):
            return False
        if "rl_initial" not in child or len(child["pretraining"]["records"]) != config.bc_epochs:
            raise ValueError("league member did not finish every BC epoch")
        if any(
            record["train_rows"]
            != config.sources()["views"][name]["coverage"]["train"]["usable_rows"]
            for record in child["pretraining"]["records"]
        ):
            raise ValueError("BC epoch did not consume exactly the selected training rows")
        state["members"][name].update(
            bc_path=child["rl_initial"],
            bc_sha256=child["members"][child["rl_initial"]],
            bc_epochs=config.bc_epochs,
            bc_rows=child["pretraining"]["rows"],
        )
        if rank == 0:
            write_json(config.experiment.output_dir / "league.json", state)
        barrier()
        gc.collect()
        torch.cuda.empty_cache()
    return True


def _learners(config: League, state: dict[str, Any]) -> list[Learner]:
    rank, _ = rank_world()
    settings = runtime_settings(config.experiment)
    device = torch.device(settings.devices[rank])
    learners = []
    for name in config.members:
        child = orjson.loads((config.experiment.output_dir / name / "state.json").read_bytes())
        recipe = config.member(
            name, committed=Demonstrations.model_validate(child["protocol"]["demonstrations"])
        )
        origin = state["members"][name]
        if digest(recipe.output_dir / origin["bc_path"]) != origin["bc_sha256"]:
            raise ValueError("BC endpoint differs from registered league origin")
        actor, _ = artifacts.load_member(recipe, child, origin["bc_path"], device)
        # Match critic initialization across experts; no BC optimizer enters PPO.
        with torch.random.fork_rng(devices=[device]):
            torch.manual_seed(config.experiment.seed + 1)
            critic = PrefixCritic(actor.layout).to(device)
        learners.append(Learner(settings, actor, critic, None))
    return learners


def _combine(workers: list[dict[str, Any]], update: int, config: League) -> dict[str, Any]:
    pairs = combine_pairs(workers)
    return {
        "update": update,
        "physical_games": config.experiment.games,
        "cumulative_physical_games": update * config.experiment.games,
        "pairs": pairs,
        "member_populations": {name: member_outcomes(pairs, name) for name in config.members},
        "selfplay_physical_games": len(config.members) * config.selfplay_games_per_member,
        "mutual_physical_games": len(config.members)
        * (len(config.members) - 1)
        // 2
        * config.games_per_pair,
        "script_physical_games": len(config.members)
        * len(config.script_names)
        * config.games_per_script_per_member,
        "workers": workers,
        "update_seconds": max(worker["update_seconds"] for worker in workers),
        "created_at": time.time(),
    }


def train(config: League, state: dict[str, Any], stop: StopRequest) -> None:
    """Keep opponents fixed throughout collection and train only each member's tape."""
    rank, world = rank_world()
    root = config.experiment.output_dir
    if state["phase"] == "bc" and not _pretrain(config, state, stop):
        return
    learners = _learners(config, state)
    settings = runtime_settings(config.experiment)
    device = learners[0].device
    count = config.trajectories_per_member // world
    torch.manual_seed(config.experiment.seed + 1000000007 * rank + 90)
    runtimes = [
        ActorRuntime(
            learner.policy,
            count,
            sample=True,
            temperature=settings.ppo.temperature,
            precision=settings.precision,
            bf16_reduced_precision_reduction=False,
            compile_inference=bool(
                config.experiment.execution and config.experiment.execution.compile_inference
            ),
        )
        for learner in learners
    ]
    if state["latest"]:
        storage.load_latest(config, state, learners)
    else:
        storage.save(config, state, learners, 0, [])
        storage.export(config, state, learners, 0)
    revisions = state.get("population_history", [])
    boundary = revisions[-1]["effective_from_update"] - 1 if revisions else 0
    if state["completed_update"] == boundary:
        evaluate(config, settings, runtimes, state["completed_update"])
    pending: list[dict[str, Any]] = []
    for update in range(state["completed_update"] + 1, config.experiment.updates + 1):
        if config.stop_after_update is not None and update > config.stop_after_update:
            stop.requested = True
        if any_stop(stop.requested, device):
            break
        started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)
        tapes, worker = collect(config, settings, runtimes, update)
        optimization = {}
        for name, learner, tape in zip(config.members, learners, tapes, strict=True):
            optimization[name] = {
                **learner.update(tape),
                "opponents": member_outcomes(worker["pairs"], name),
            }
        del tapes
        worker.update(
            optimization=optimization,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(device),
            update_seconds=time.perf_counter() - started,
        )
        metrics = _combine(gather(worker), update, config)
        pending.append(metrics)
        if rank == 0:
            with (root / "metrics.jsonl").open("ab") as stream:
                stream.write(orjson.dumps(metrics) + b"\n")
            write_json(
                root / "league-progress.json",
                {
                    "phase": "rl",
                    "completed_update": update,
                    "budget": config.experiment.updates,
                    "cumulative_physical_games": update * config.experiment.games,
                    "pairs": metrics["pairs"],
                    "update_seconds": metrics["update_seconds"],
                    "members": state["members"],
                },
            )
            print(orjson.dumps({"phase": "league_rl", **metrics}).decode(), flush=True)
        halt = any_stop(stop.requested, device)
        if (
            update % config.experiment.checkpoint_interval == 0
            or update == config.experiment.updates
            or halt
        ):
            storage.save(config, state, learners, update, pending)
            pending = []
        if (
            update % config.experiment.evaluation.interval == 0
            or update == config.experiment.updates
        ):
            storage.export(config, state, learners, update)
            evaluate(config, settings, runtimes, update)
        if halt:
            break
    if pending:
        storage.save(config, state, learners, pending[-1]["update"], pending)
    if rank == 0:
        write_json(
            root / "league-progress.json",
            {
                "phase": "stopped" if stop.requested else "complete",
                "completed_update": state["completed_update"],
                "budget": config.experiment.updates,
                "members": state["members"],
            },
        )
