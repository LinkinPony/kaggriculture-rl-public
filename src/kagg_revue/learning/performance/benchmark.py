"""Benchmark authenticated own-run weights without advancing its training ledger."""

import copy
import json
import os
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

import hydra
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.population import script_games
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.curriculum import collect_update
from kagg_revue.learning.distributed import bind_cpus, gather, rank_world
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.learning.optimization.settings import HistoricalPopulation
from kagg_revue.policy.inference import ActorRuntime


def benchmark(options: dict[str, Any]) -> None:
    """Measure cold and warm collection/optimization on the same checkpoint."""
    directory = Path(options["run"])
    state = json.loads((directory / "state.json").read_text())
    execution = Execution.model_validate(options["execution"])
    rank, world = rank_world()
    device = torch.device(execution.devices[rank])
    torch.cuda.set_device(device)
    torch.set_num_threads(execution.cpu_threads_per_rank)
    config = Experiment.model_validate(
        {
            **state["protocol"],
            "execution": execution.model_dump(),
            "device": execution.devices[0],
            "batch_rows": options.get("batch_rows", state["protocol"]["batch_rows"]),
            "sequence_games_per_rank": options.get(
                "sequence_games_per_rank", state["protocol"].get("sequence_games_per_rank", 4)
            ),
            "actor_learning_rate": options.get(
                "actor_learning_rate", state["protocol"]["actor_learning_rate"]
            ),
            "target_kl": options.get("target_kl", state["protocol"]["target_kl"]),
            "kl_control": options.get(
                "kl_control", state["protocol"].get("kl_control", "rollback")
            ),
            **(
                {
                    "population": {
                        **state["protocol"]["population"],
                        "fraction": 0.0,
                        "pfsp": None,
                    },
                    "script_population": None,
                }
                if options.get("pure_selfplay")
                else {}
            ),
        }
    )
    settings = runtime_settings(config)
    actor, payload = artifacts.load_member(config, state, state["latest"], device)
    critic: PrefixCritic
    if config.memory_turns:
        from kagg_revue.learning.sequences.critic import MemoryCritic
        from kagg_revue.learning.sequences.learner import SequenceLearner
        from kagg_revue.policy.memory.policy import MemoryPolicy

        assert isinstance(actor, MemoryPolicy)
        critic = MemoryCritic(actor.layout).to(device)
        learner: Learner = SequenceLearner(settings, actor, critic)
    else:
        critic = PrefixCritic(actor.layout).to(device)
        learner = Learner(settings, actor, critic, None)
    runtime = ActorRuntime(
        actor,
        int(config.games * (2 - config.population.fraction)) // world
        - script_games(settings, config.games // world),
        sample=True,
        precision=config.precision,
        bf16_reduced_precision_reduction=False,
        compile_inference=execution.compile_inference,
    )
    history = None
    if config.population.fraction:
        opponent, _ = artifacts.load_member(config, state, state["pool"][-1], device)
        opponent.requires_grad_(False)
        history = ActorRuntime(
            opponent,
            int(config.games * config.population.fraction) // world,
            sample=True,
            precision=config.precision,
            bf16_reduced_precision_reduction=False,
            compile_inference=execution.compile_inference,
        )
        settings = settings.model_copy(
            update={
                "ppo": settings.ppo.model_copy(
                    update={
                        "history": HistoricalPopulation(
                            checkpoint=directory / state["pool"][-1],
                            fraction=config.population.fraction,
                        ),
                    }
                )
            }
        )
    rows = []
    for iteration in range(int(options["repetitions"])):
        actor.load_state_dict(payload["model"])
        critic.load_state_dict(payload["critic"])
        learner.restore_optimizers(
            copy.deepcopy(payload["actor_optimizer"]), copy.deepcopy(payload["critic_optimizer"])
        )
        torch.manual_seed(config.seed + rank)
        torch.cuda.reset_peak_memory_stats(device)
        started_at = time.time()
        started = time.perf_counter()
        rollout, _ = collect_update(
            config, settings, actor, runtime, history, None, state["completed_update"] + 1
        )
        learning_started_at = time.time()
        optimization = learner.update(rollout)
        record = {
            "iteration": iteration,
            "started_at": started_at,
            "learning_started_at": learning_started_at,
            "finished_at": time.time(),
            "rollout": rollout.timing,
            "optimization": optimization,
            "seconds": time.perf_counter() - started,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        }
        del rollout
        workers = gather(record)
        # Each worker must apply exactly the same globally reduced optimizer steps.
        parameters = torch.cat([p.detach().flatten() for p in actor.parameters()])
        reference = parameters.clone()
        if world > 1:
            dist.broadcast(reference, src=0)
        difference = float((reference - parameters).abs().max())
        differences = gather(difference)
        if any(differences):
            raise RuntimeError(f"learner ranks diverged: {differences}")
        record = {
            **workers[0],
            "seconds": max(w["seconds"] for w in workers),
            "workers": workers,
            "maximum_rank_parameter_difference": max(differences),
        }
        rows.append(record)
        if rank == 0:
            print(json.dumps(record), flush=True)
            write_json(
                Path(options["output"]),
                {
                    "run_id": state["run_id"],
                    "update": state["completed_update"],
                    "checkpoint_sha256": state["members"][state["latest"]],
                    "execution": execution.model_dump(),
                    "batch_rows": config.batch_rows,
                    "physical_games": config.games,
                    "pure_selfplay": config.population.fraction == 0
                    and config.script_population is None,
                    "sequence_games_per_rank": config.sequence_games_per_rank,
                    "actor_learning_rate": config.actor_learning_rate,
                    "measurements": rows,
                    "inference_capture_seconds": runtime.capture_seconds
                    + (history.capture_seconds if history else 0),
                },
            )


def _rank(rank: int, options: dict[str, Any], rendezvous: str) -> None:
    execution = Execution.model_validate(options["execution"])
    bind_cpus(rank, len(execution.devices))
    device = torch.device(execution.devices[rank])
    torch.cuda.set_device(device)
    dist.init_process_group(
        "nccl",
        init_method=rendezvous,
        rank=rank,
        world_size=len(execution.devices),
        device_id=device,
        timeout=timedelta(minutes=30),
    )
    try:
        benchmark(options)
    finally:
        dist.destroy_process_group()


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_benchmark",
)
def main(configuration: DictConfig) -> None:
    """Resolve explicitly named component measurements through Hydra."""
    options = OmegaConf.to_container(configuration.benchmark, resolve=True)
    assert isinstance(options, dict)
    execution = Execution.model_validate(options["execution"])
    if len(execution.devices) == 1:
        benchmark(options)  # type: ignore[arg-type]
    else:
        rendezvous = Path(f"tmp/dual-h200/benchmark-{os.getpid()}").resolve()
        rendezvous.parent.mkdir(parents=True, exist_ok=True)
        try:
            mp.spawn(  # type: ignore[attr-defined, no-untyped-call]
                _rank, args=(options, rendezvous.as_uri()), nprocs=len(execution.devices)
            )
        finally:
            rendezvous.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
