"""Complete-game multi-GPU training with reproducible 50-update qualification."""

import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import psutil  # type: ignore[import-untyped]
import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.collection.population import historical_games, policy_rows, script_games
from kagg_revue.learning.collection.population import outcomes as population_outcomes
from kagg_revue.learning.collection.sampling import collect
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Critic
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.cadence import rehearsal_steps
from kagg_revue.production.config import Settings
from kagg_revue.production.data import load_shard
from kagg_revue.production.evaluation import panel
from kagg_revue.production.imitation import train as train_bc
from kagg_revue.production.recovery import check_regression, validate_preflight
from kagg_revue.production.reporting import (
    check_metrics_resume,
    evaluation_report,
    publish_selection,
    qualify_prefix_pipeline,
    retain_checkpoints,
)
from kagg_revue.production.restoration import restore_training


def _gather(value: Any, world: int) -> list[Any]:
    if world == 1:
        return [value]
    output: list[Any] = [None] * world
    dist.all_gather_object(output, value)
    return output


def _rank(rank: int, resolved: dict[str, Any], initial: str, rendezvous: str) -> None:
    rank_started = time.perf_counter()
    settings = Settings.model_validate(resolved)
    world = len(settings.devices)
    torch.set_num_threads(settings.cpu_threads)
    device = torch.device(settings.devices[rank])
    torch.cuda.set_device(device)
    if world > 1:
        dist.init_process_group(
            "nccl", init_method=rendezvous, rank=rank, world_size=world, device_id=device
        )
    torch.manual_seed(settings.seed)
    policy, checkpoint = load_policy(Path(initial), device)
    baseline_checkpoint = str(checkpoint.get("baseline_checkpoint", initial))
    if policy.layout != ContractLayout.resolve(settings):
        raise ValueError(
            "checkpoint and resolved production profile have different model semantics"
        )
    critic = (
        PrefixCritic(policy.layout)
        if settings.ppo.ratio_scope == "prefix"
        else Critic(policy.layout)
    ).to(device)
    training_shards = []
    bc_times = None
    if settings.ppo.bc_weight:
        manifest = json.loads((settings.bc.directory / "manifest.json").read_text())
        bc_times = rehearsal_steps(manifest, policy.layout, device)
        training_shards = manifest["shards"][:-1]
        if not training_shards:
            raise ValueError("BC rehearsal requires training shards separate from held-out data")
    learner = Learner(settings, policy, critic, None)
    first_update = restore_training(settings, checkpoint, critic, learner, rank)
    if first_update > settings.ppo.updates:
        raise ValueError("training endpoint must follow the restored checkpoint")
    count = settings.ppo.games_per_update // world
    scripts = script_games(settings, count)
    history = historical_games(settings, count)
    single_seat = scripts + history
    runtime = ActorRuntime(
        policy,
        2 * count - single_seat,
        sample=True,
        temperature=settings.ppo.temperature_at(first_update),
        dynamic_temperature=settings.ppo.temperature_schedule is not None,
        precision=settings.precision,
        bf16_reduced_precision_reduction=settings.bf16_reduced_precision_reduction,
    )
    history_runtime = None
    if settings.ppo.history is not None:
        # Loading a frozen module must not consume the restored rank's sampling RNG.
        with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
            frozen, frozen_payload = load_policy(settings.ppo.history.checkpoint, device)
            del frozen_payload
            if frozen.layout != policy.layout:
                raise ValueError("historical opponent must share the actor's native contract")
            frozen.requires_grad_(False)
            history_runtime = ActorRuntime(
                frozen,
                history,
                sample=True,
                temperature=settings.ppo.temperature,
                precision=settings.precision,
                bf16_reduced_precision_reduction=settings.bf16_reduced_precision_reduction,
            )
    identity = provenance(settings) if rank == 0 else {}
    metrics_path = settings.output_dir / "metrics.jsonl"
    check_metrics_resume(metrics_path, first_update - 1)
    if rank == 0:
        write_json(settings.output_dir / "resolved-config.json", settings.model_dump(mode="json"))
        write_json(settings.output_dir / "source.json", identity)
        write_json(
            settings.output_dir / "model.json",
            {
                "actor_parameters": sum(parameter.numel() for parameter in policy.parameters()),
                "critic_parameters": sum(parameter.numel() for parameter in critic.parameters()),
                "observation_features": policy.layout.observation.features,
                "architecture": policy.layout.network.architecture,
                "source_revision": identity["revision"],
            },
        )
    try:
        stopped = False
        completed_update = first_update - 1
        for update in range(first_update, settings.ppo.updates + 1):
            started = rank_started if update == first_update else time.perf_counter()
            torch.cuda.reset_peak_memory_stats(device)
            temperature = settings.ppo.temperature_at(update)
            actor_rate = settings.ppo.actor_rate_at(update)
            runtime.set_temperature(temperature)
            for group in learner.actor_optimizer.param_groups:
                group["lr"] = actor_rate * group.get("guard_lr_scale", 1.0)
            if bc_times is not None:
                shard_index = (update - 1) % len(training_shards)
                observations, actions, steps = load_shard(
                    settings.bc.directory, training_shards[shard_index], device
                )
                learner.rehearsal = (observations, actions, bc_times[steps])
            seed_start = settings.ppo.seed_start + (update - 1) * settings.ppo.games_per_update
            seeds = list(range(seed_start + rank * count, seed_start + (rank + 1) * count))
            rollout = collect(settings, policy, runtime, seeds, history_runtime)
            optimization = learner.update(
                rollout, actor_training=update > settings.ppo.prefix_warmup_updates
            )
            actor_rate = float(learner.actor_optimizer.param_groups[0]["lr"])
            local = {
                "rank": rank,
                "device": str(device),
                "rollout": rollout.timing,
                "optimization": optimization,
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
                "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
                "host_rss_bytes": psutil.Process().memory_info().rss,
                "cash": rollout.cash.tolist(),
                "opponents": rollout.opponents,
            }
            workers = _gather(local, world)
            del rollout
            checkpoint_seconds = 0.0
            evaluate_now = (
                settings.ppo.evaluation_interval > 0
                and update % settings.ppo.evaluation_interval == 0
            )
            if (
                update % settings.ppo.checkpoint_interval == 0
                or update == settings.ppo.updates
                or evaluate_now
            ):
                checkpoint_started = time.perf_counter()
                rngs = _gather(
                    {"cpu": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state(device)}, world
                )
                if rank == 0:
                    path = settings.output_dir / "checkpoints" / f"update-{update:04d}.pt"
                    save_policy(
                        path,
                        policy,
                        settings,
                        update=update,
                        critic=critic.state_dict(),
                        actor_optimizer=learner.actor_optimizer.state_dict(),
                        critic_optimizer=learner.critic_optimizer.state_dict(),
                        rank_rng=rngs,
                        provenance=identity,
                        baseline_checkpoint=baseline_checkpoint,
                        sampling={"temperature": temperature, "actor_learning_rate": actor_rate},
                    )
                    write_json(
                        settings.output_dir / "checkpoints" / "latest.json",
                        {"update": update, "path": str(path)},
                    )
                    retain_checkpoints(path.parent, settings.ppo.retain_checkpoints)
                if world > 1:
                    dist.barrier()
                checkpoint_seconds = time.perf_counter() - checkpoint_started
            elapsed = time.perf_counter() - started
            if rank == 0:
                cash = np.concatenate([np.array(worker.pop("cash")) for worker in workers])
                names = [name for worker in workers for name in worker.pop("opponents")]
                learned_cash = np.concatenate(
                    [policy_rows(part, count - single_seat) for part in np.split(cash, world)]
                )
                # Average the two learned seats within self-play games, then average games.
                per_game_cash = np.where(np.asarray(names) == "self_play", cash.mean(1), cash[:, 0])
                outcomes = np.sign(cash[:, 0] - cash[:, 1])
                record = {
                    "update": update,
                    "population": settings.ppo.population,
                    "prefix_trace_lambda": settings.ppo.prefix_trace_lambda,
                    "temperature": temperature,
                    "actor_learning_rate": actor_rate,
                    "cash_weight": settings.ppo.cash_weight,
                    "win_weight": settings.ppo.win_weight,
                    "physical_games": settings.ppo.games_per_update,
                    "training_trajectories": len(learned_cash),
                    "selfplay_games": settings.ppo.games_per_update - single_seat * world,
                    "historical_games": history * world,
                    "script_games": scripts * world,
                    "official_transitions": settings.ppo.games_per_update * settings.turns,
                    "mean_cash": float(per_game_cash.mean()),
                    "p10_cash": float(np.quantile(learned_cash, 0.1)),
                    "mean_cash_difference": float((cash[:, 0] - cash[:, 1]).mean()),
                    "wins": int((outcomes > 0).sum()),
                    "ties": int((outcomes == 0).sum()),
                    "losses": int((outcomes < 0).sum()),
                    "outcomes": population_outcomes(cash, names),
                    "workers": workers,
                    "checkpoint_seconds": checkpoint_seconds,
                    "update_seconds": elapsed,
                    "physical_games_per_second": settings.ppo.games_per_update / elapsed,
                    "cold_graph_seconds": runtime.capture_seconds
                    if update == first_update
                    else 0.0,
                }
                with metrics_path.open("a") as stream:
                    stream.write(json.dumps(record) + "\n")
                print(
                    json.dumps({key: value for key, value in record.items() if key != "workers"}),
                    flush=True,
                )
                if (
                    settings.ppo.ratio_scope == "prefix"
                    and update >= settings.ppo.prefix_warmup_updates + 3
                    and not (settings.output_dir / "qualification.json").exists()
                ):
                    qualify_prefix_pipeline(settings, identity)
            if world > 1:
                dist.barrier()
            if evaluate_now and rank == 0:
                result = panel(settings, policy, settings.evaluation_seed)
                publish_selection(settings, result, identity, path, update)
                stopped = check_regression(settings, policy, result, path, update)
            if evaluate_now and world > 1:
                stop_signal = torch.tensor(int(stopped), device=device)
                dist.broadcast(stop_signal, src=0)
                stopped = bool(stop_signal)
            completed_update = update
            if stopped:
                break
        if rank == 0:
            training_seconds = time.perf_counter() - rank_started
            write_json(
                settings.output_dir / "training-report.json",
                {
                    "schema_version": "spatial-contract-selfplay-v1",
                    "completed_update": completed_update,
                    "stopped_for_regression": stopped,
                    "source_revision": identity["revision"],
                    "population": settings.ppo.population,
                    "initial_checkpoint": str(initial),
                    "training_seconds": training_seconds,
                    "physical_games": settings.ppo.games_per_update
                    * max(0, completed_update - first_update + 1),
                    "graph_capture_seconds": runtime.capture_seconds,
                },
            )
        if rank == 0 and settings.mode == "train" and not stopped:
            confirmation = panel(settings, policy, settings.confirmation_seed)
            write_json(settings.output_dir / "confirmation.json", confirmation)
            sampled = panel(settings, policy, settings.confirmation_seed, sample=True)
            write_json(settings.output_dir / "confirmation-sampled.json", sampled)
            baseline, _ = load_policy(Path(baseline_checkpoint), device)
            baseline_confirmation = panel(settings, baseline, settings.confirmation_seed)
            baseline_sampled = panel(settings, baseline, settings.confirmation_seed, sample=True)
            write_json(settings.output_dir / "baseline-confirmation.json", baseline_confirmation)
            write_json(settings.output_dir / "baseline-confirmation-sampled.json", baseline_sampled)
            evaluation_report(
                settings,
                {
                    "PPO greedy": confirmation,
                    "PPO sampled": sampled,
                    "initial greedy": baseline_confirmation,
                    "initial sampled": baseline_sampled,
                },
                identity,
            )
            print(
                json.dumps(
                    {
                        "phase": "confirmation",
                        "mean_cash": confirmation["mean_cash"],
                        "sampled_mean_cash": sampled["mean_cash"],
                        "wins": confirmation["wins"],
                        "losses": confirmation["losses"],
                    }
                ),
                flush=True,
            )
        if world > 1:
            dist.barrier()
    finally:
        if dist.is_initialized():
            dist.destroy_process_group()


def launch(settings: Settings) -> None:
    """Run the exact profile in the caller's named tmux session."""
    validate_preflight(settings)
    initial = settings.checkpoint or settings.output_dir / "bc" / "best.pt"
    if settings.checkpoint is not None and not initial.exists():
        raise FileNotFoundError(initial)
    if not initial.exists():
        initial = train_bc(settings)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    status_path = settings.output_dir / "run-status.json"
    write_json(settings.output_dir / "resolved-config.json", settings.model_dump(mode="json"))
    write_json(status_path, {"status": "running", "pid": os.getpid(), "started_at": time.time()})
    rendezvous = (Path("tmp") / "parallel-policy" / f"nccl-{time.time_ns()}").resolve()
    rendezvous.parent.mkdir(parents=True, exist_ok=True)
    try:
        if len(settings.devices) > 1:
            mp.spawn(  # type: ignore[attr-defined, no-untyped-call]
                _rank,
                args=(settings.model_dump(mode="json"), str(initial), rendezvous.as_uri()),
                nprocs=len(settings.devices),
                join=True,
            )
        else:
            _rank(0, settings.model_dump(mode="json"), str(initial), rendezvous.as_uri())
    except BaseException:
        write_json(status_path, {"status": "failed", "pid": os.getpid()})
        raise
    else:
        recovery_status = settings.output_dir / "recovery-status.json"
        quarantined = (
            recovery_status.exists()
            and json.loads(recovery_status.read_text())["stopped_for_regression"]
        )
        write_json(
            status_path,
            {"status": "quarantined" if quarantined else "complete", "pid": os.getpid()},
        )
    finally:
        rendezvous.unlink(missing_ok=True)
