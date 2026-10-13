"""Production-scale distillation that switches to WDL PPO when the table reaches zero."""

import faulthandler
import json
import os
import shutil
import signal
import time
import traceback
from pathlib import Path
from typing import Any, cast

import hydra
import numpy as np
import psutil  # type: ignore[import-untyped]
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.collection.population import outcomes, script_games
from kagg_revue.learning.collection.sampling import collect
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import Settings
from kagg_revue.production.migration.artifacts import evaluate_student, load_migration, save_student
from kagg_revue.production.migration.config import MigrationSettings
from kagg_revue.production.migration.objectives import scheduled_scale
from kagg_revue.production.migration.stages import TrainingStage
from kagg_revue.production.reporting import retain_checkpoints
from kagg_revue.production.train import _gather


def _runtime(settings: Settings, student: WorkPolicy, count: int) -> ActorRuntime:
    return ActorRuntime(
        student,
        2 * count - script_games(settings, count),
        sample=True,
        temperature=settings.ppo.temperature,
        precision=settings.precision,
        bf16_reduced_precision_reduction=settings.bf16_reduced_precision_reduction,
    )


def _rank(rank: int, resolved: dict[str, Any], rendezvous: str) -> None:
    faulthandler.register(signal.SIGUSR1, all_threads=False)
    config = MigrationSettings.model_validate(resolved)
    settings = config.production
    world = len(settings.devices)
    device = torch.device(settings.devices[rank])
    torch.set_num_threads(settings.cpu_threads)
    torch.cuda.set_device(device)
    torch.set_float32_matmul_precision("highest")
    if world > 1:
        dist.init_process_group(
            "nccl", init_method=rendezvous, rank=rank, world_size=world, device_id=device
        )
    torch.manual_seed(settings.seed + rank)
    directory = settings.output_dir
    latest_path = directory / "checkpoints" / "latest.json"
    latest = json.loads(latest_path.read_text()) if latest_path.exists() else None
    saved_path = Path(latest["path"]) if latest else config.resume_from
    saved = load_migration(saved_path, config, continuation=latest is None) if saved_path else None
    update, scale = (saved["migration_update"], saved["scale"]) if saved else (0, 1.0)
    # New continuations start their clock at the frozen checkpoint. Ordinary
    # restarts retain that clock, including time spent after reaching zero.
    fade_start_update = saved["fade_start_update"] if saved and latest else update
    fade_start_scale = saved["fade_start_scale"] if saved and latest else scale
    loaded, initial = load_policy(saved_path or config.teacher, torch.device("cpu"))
    student = cast(WorkPolicy, loaded.to(device)).eval()
    critic_state = initial["critic"]
    del initial, loaded
    teacher = None
    if student.layout.network.time_prior:
        loaded, unused = load_policy(config.teacher, torch.device("cpu"))
        teacher = cast(WorkPolicy, loaded.to(device)).eval()
        del unused, loaded
    if student.layout.network.time_prior:
        student.prior_scale.fill_(scale)
    learner = TrainingStage(config, student, critic_state, teacher, saved)
    del teacher, critic_state
    if saved:
        if len(saved["rank_rng"]) != world:
            raise ValueError("migration resume requires the saved learner rank count")
        rng = saved["rank_rng"][rank]
        torch.set_rng_state(rng["cpu"])
        torch.cuda.set_rng_state(rng["cuda"], device)
    del saved
    count = settings.ppo.games_per_update // world
    runtime = _runtime(settings, student, count)
    identity = provenance(settings) if rank == 0 else {}
    if rank == 0:
        write_json(directory / "source.json", identity)
        write_json(directory / "resolved-config.json", resolved)
        write_json(
            directory / "teacher.json",
            {"path": str(config.teacher), "sha256": digest(config.teacher)},
        )
        write_json(
            directory / "schedule.json",
            {
                "start_update": fade_start_update,
                "start_scale": fade_start_scale,
                "interval": config.scale_interval,
                "decrement": config.scale_step,
                "continue_after_zero": True,
                "objective_after_zero": "pure_wdl_ppo",
                "outcome_gate": False,
            },
        )
        if config.resume_from is not None:
            write_json(
                directory / "continuation.json",
                {"checkpoint": str(config.resume_from), "sha256": digest(config.resume_from)},
            )
    if world > 1:
        dist.barrier()
    first_update = True
    try:
        while True:
            started = time.perf_counter()
            torch.cuda.reset_peak_memory_stats(device)
            update += 1
            scale = scheduled_scale(
                fade_start_scale,
                update - fade_start_update,
                config.scale_interval,
                config.scale_step,
            )
            removed_now = student.layout.network.time_prior and scale == 0
            if student.layout.network.time_prior:
                student.prior_scale.fill_(scale)
            if removed_now:
                # Retire the table and teacher before collecting the first PPO rollout.
                torch.cuda.synchronize(device)
                del runtime
                learner.start_ppo()
                runtime = _runtime(settings, student, count)
                rngs = _gather(
                    {"cpu": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state(device)},
                    world,
                )
                if rank == 0:
                    initial_ppo = directory / "release" / "ppo-initial.pt"
                    save_student(
                        initial_ppo,
                        student,
                        settings,
                        scale,
                        migration_update=update - 1,
                        scale=scale,
                        fade_start_update=fade_start_update,
                        fade_start_scale=fade_start_scale,
                        migration_configuration=resolved,
                        rank_rng=rngs,
                        provenance=identity,
                        teacher_checkpoint=str(config.teacher),
                        **learner.state_dict(),
                    )
                    write_json(
                        directory / "ppo-transition.json",
                        {
                            "first_ppo_update": update,
                            "checkpoint": str(initial_ppo),
                            "sha256": digest(initial_ppo),
                            "source": identity,
                            "actor_optimizer": "fresh; distillation moments discarded",
                            "critic_initialization": str(config.teacher),
                            "teacher_released": True,
                        },
                    )
            start = (
                settings.ppo.seed_start
                + (update - 1) * settings.ppo.games_per_update
                + rank * count
            )
            rollout = collect(settings, student, runtime, list(range(start, start + count)))
            optimization: dict[str, float | int] = {}
            if first_update and learner.distiller is not None:
                optimization["initial_plan_kl"] = learner.distiller.check_likelihood(rollout)
                print({"rank": rank, "phase": "likelihood_measured", **optimization}, flush=True)
            optimization.update(learner.update(rollout))
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
            rngs = _gather(
                {"cpu": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state(device)}, world
            )
            if rank == 0:
                checkpoint_started = time.perf_counter()
                checkpoint = directory / "checkpoints" / f"update-{update:04d}.pt"
                save_student(
                    checkpoint,
                    student,
                    settings,
                    scale,
                    migration_update=update,
                    scale=scale,
                    fade_start_update=fade_start_update,
                    fade_start_scale=fade_start_scale,
                    migration_configuration=resolved,
                    rank_rng=rngs,
                    provenance=identity,
                    teacher_checkpoint=str(config.teacher),
                    **learner.state_dict(),
                )
                if not student.layout.network.time_prior:
                    exported = directory / "release" / "model-no-prior.pt"
                    if not exported.exists():
                        exported.parent.mkdir(parents=True, exist_ok=True)
                        temporary = exported.with_suffix(".partial")
                        shutil.copy2(checkpoint, temporary)
                        temporary.replace(exported)
                        write_json(
                            exported.with_suffix(".json"),
                            {
                                "checkpoint": str(exported),
                                "sha256": digest(exported),
                                "update": update,
                                "training_continues": True,
                            },
                        )
                checkpoint_seconds = time.perf_counter() - checkpoint_started
                if update % config.evaluation_interval == 0:
                    evaluate_student(
                        directory / "selection" / f"update-{update:04d}",
                        settings,
                        student,
                        scale,
                        settings.evaluation_seed,
                        identity,
                        checkpoint,
                    )
                write_json(
                    latest_path,
                    {
                        "path": str(checkpoint),
                        "update": update,
                        "scale": scale,
                        "training_phase": learner.name,
                    },
                )
                cash = np.concatenate([np.asarray(item.pop("cash")) for item in workers])
                names = [name for item in workers for name in item.pop("opponents")]
                record: dict[str, Any] = {
                    "update": update,
                    "training_phase": learner.name,
                    "prior_scale": scale,
                    "table_removed": not student.layout.network.time_prior,
                    "physical_games": settings.ppo.games_per_update,
                    "outcomes": outcomes(cash, names),
                    "workers": workers,
                    "checkpoint_seconds": checkpoint_seconds,
                    "update_seconds": time.perf_counter() - started,
                    "cold_graph_seconds": runtime.capture_seconds
                    if first_update or removed_now
                    else 0,
                }
                record["physical_games_per_second"] = (
                    settings.ppo.games_per_update / record["update_seconds"]
                )
                with (directory / "metrics.jsonl").open("a") as stream:
                    stream.write(json.dumps(record) + "\n")
                print(json.dumps(record), flush=True)
                retain_checkpoints(checkpoint.parent, settings.ppo.retain_checkpoints)
            first_update = False
            if world > 1:
                dist.barrier()
    except BaseException:
        # Collective teardown on failure can deadlock against a peer's next gather.
        traceback.print_exc()
        raise


def launch(config: MigrationSettings) -> None:
    """Run the scheduled migration until the user stops it or execution fails."""
    directory = config.production.output_dir
    directory.mkdir(parents=True, exist_ok=True)
    status = directory / "run-status.json"
    write_json(status, {"status": "running", "pid": os.getpid(), "started_at": time.time()})
    rendezvous = (Path("tmp") / "parallel-policy" / f"migration-{time.time_ns()}").resolve()
    rendezvous.parent.mkdir(parents=True, exist_ok=True)
    try:
        mp.spawn(  # type: ignore[attr-defined, no-untyped-call]
            _rank,
            args=(config.model_dump(mode="json"), rendezvous.as_uri()),
            nprocs=len(config.production.devices),
            join=True,
        )
    except BaseException:
        write_json(status, {"status": "failed", "pid": os.getpid()})
        raise
    finally:
        rendezvous.unlink(missing_ok=True)


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="production_migration"
)
def main(configuration: DictConfig) -> None:
    """Resolve the complete migration route before starting any GPU work."""
    launch(MigrationSettings.model_validate(OmegaConf.to_container(configuration, resolve=True)))


if __name__ == "__main__":
    main()
