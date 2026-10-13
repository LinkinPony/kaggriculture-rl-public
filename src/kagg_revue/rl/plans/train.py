"""Long-running pure terminal-W/D/L PPO over event-driven plans."""

from __future__ import annotations

import json
import math
import random
import time
from contextlib import ExitStack
from pathlib import Path
from typing import cast

import numpy as np
import torch
from torch import multiprocessing as torch_multiprocessing
from torch import nn
from torch.nn.parallel import DistributedDataParallel

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import load_backend
from kagg_revue.core.observability import ScalarLogger, observability_report
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.plans.grammar import CONTINUE, GLOBAL_KEEP, LINE_KEEP, STOP
from kagg_revue.policy.plans.model import StructuredPlanPolicy
from kagg_revue.rl.distributed import (
    DistributedContext,
    destroy_context,
    initialize_context,
    local_value,
    single_process_context,
)
from kagg_revue.rl.plans.artifacts import (
    architecture,
    artifact_identities,
    outcome_metrics,
    prepare_output,
    resolve_settings,
    validate_native_abi,
)
from kagg_revue.rl.plans.checkpoint import (
    PlanCheckpointStore,
    build_plan_checkpoint,
    capture_plan_rng_state,
    combine_plan_rng_states,
    restore_plan_checkpoint,
)
from kagg_revue.rl.plans.config import StructuredPlanRlSettings
from kagg_revue.rl.plans.distributed import summarize_plan_rollout
from kagg_revue.rl.plans.health import PlanCollapseGuard, PlanHealthObservation
from kagg_revue.rl.plans.initialization import initialize_plan_backbone
from kagg_revue.rl.plans.learning import (
    PlanPolicyEvaluator,
    audit_plan_behavior_likelihood,
    optimize_plan_batch,
)
from kagg_revue.rl.plans.metrics import PlanLocalUpdate, aggregate_plan_updates
from kagg_revue.rl.plans.population import PlanSelfPlayPopulation
from kagg_revue.rl.plans.rollout import StructuredPlanRolloutCollector


def _plan_optimizer(
    model: StructuredPlanPolicy,
    settings: StructuredPlanRlSettings,
) -> torch.optim.AdamW:
    """Keep actor trust-region steps independent from critic fitting speed."""
    critic_parameters = tuple(model.outcome_head.parameters())
    critic_ids = {id(parameter) for parameter in critic_parameters}
    actor_parameters = tuple(
        parameter for parameter in model.parameters() if id(parameter) not in critic_ids
    )
    if not actor_parameters or not critic_parameters:
        raise RuntimeError("structured-plan actor and critic parameter groups must be nonempty")
    optimization = settings.optimization
    return torch.optim.AdamW(
        [
            {
                "params": actor_parameters,
                "lr": optimization.actor_learning_rate,
            },
            {
                "params": critic_parameters,
                "lr": optimization.critic_learning_rate,
            },
        ],
        weight_decay=optimization.weight_decay,
    )


def _train_structured_plan_worker(
    settings: StructuredPlanRlSettings,
    repository_root: Path,
    *,
    smoke: bool,
    context: DistributedContext,
    output_prepared: bool,
) -> dict[str, object]:
    """Train one synchronized rank of the structured-plan lineage."""
    root = repository_root.resolve()
    devices = tuple(torch.device(value) for value in settings.devices)
    device = context.device
    torch.cuda.set_device(device)
    torch.set_num_threads(local_value(settings.cpu_threads, context.world_size, "cpu_threads"))
    random.seed(settings.seed)
    np.random.seed(settings.seed % (2**32))
    torch.manual_seed(settings.seed)
    torch.cuda.manual_seed_all(settings.seed)
    randomizer = random.Random(settings.seed + 1)
    action_generator = torch.Generator(device=device)
    action_generator.manual_seed(settings.seed + 2 + context.rank * 1_000_003)

    backend = load_backend(root)
    native_spec = validate_native_abi(backend, settings)
    resolved_environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    episode_steps = resolved_environment.get("episodeSteps")
    turns_per_day = resolved_environment.get("turnsPerDay")
    if not isinstance(episode_steps, int) or not isinstance(turns_per_day, int):
        raise TypeError("structured-plan resolved day schedule is invalid")
    season_days = math.ceil(episode_steps / turns_per_day)
    if season_days > settings.model.max_history:
        raise ValueError("structured-plan day history cannot hold the resolved season")
    identities = artifact_identities(backend, settings)
    source = source_identity(root)
    revision = context.consistent_text(str(source["commit"]), "source revision")
    if not smoke and bool(source["worktree_dirty"]):
        raise RuntimeError(
            "long structured-plan training requires a clean committed source revision"
        )

    model = StructuredPlanPolicy(architecture(settings)).to(device)
    initialization: dict[str, object]
    if settings.resume_checkpoint is not None:
        initialization = {
            "mode": "checkpoint_resume",
            "configured_initialization": settings.actor_initialization,
            "applied": False,
        }
    elif settings.actor_initialization == "bc_backbone":
        if settings.initial_actor is None:
            raise RuntimeError("validated BC initialization lost its actor artifact")
        initialization = initialize_plan_backbone(model, settings.initial_actor)
    else:
        initialization = {
            "mode": "random",
            "transferred_groups": {},
            "excluded_groups": [],
        }
    if settings.resume_checkpoint is None:
        initialization["new_action_head_prior"] = (
            model.action_initialization_report()
        )
    optimizer = _plan_optimizer(model, settings)
    population = PlanSelfPlayPopulation(
        model.architecture,
        capacity=settings.self_play.history_capacity,
        snapshot_interval=settings.self_play.snapshot_interval,
        selection_seed=settings.seed + 7_919,
        device=device,
    )
    health = PlanCollapseGuard(
        warmup_updates=settings.health.warmup_updates,
        anchor_panels=settings.health.anchor_panels,
        stop_fraction_floor=settings.health.stop_fraction_floor,
        plan_change_fraction_ceiling=settings.health.plan_change_fraction_ceiling,
        anchor_loss_rate_floor=settings.health.anchor_loss_rate_floor,
    )
    start_update = 1
    resume: dict[str, object] | None = None
    if settings.resume_checkpoint is not None:
        restored = restore_plan_checkpoint(
            settings.resume_checkpoint,
            model,
            optimizer,
            population,
            health,
            settings,
            source_revision=revision,
            artifact_identities=identities,
            randomizer=randomizer,
            action_generator=action_generator,
            device=device,
            distributed_rank=context.rank,
        )
        start_update = restored.start_update
        resume = {
            "path": str(settings.resume_checkpoint),
            "sha256": sha256_file(settings.resume_checkpoint),
            "checkpoint_version": restored.checkpoint["checkpoint_version"],
            "completed_update": restored.checkpoint["completed_update"],
            "source_revision": restored.checkpoint["source_revision"],
        }
    else:
        population.snapshot(0, model, force=True)

    evaluator = PlanPolicyEvaluator(model)
    training_model: nn.Module = evaluator
    if context.enabled:
        if device.index is None:
            raise ValueError("structured-plan distributed CUDA index is absent")
        training_model = DistributedDataParallel(
            evaluator,
            device_ids=[device.index],
            output_device=device.index,
            forward_sync_buffers=False,
            find_unused_parameters=True,
            gradient_as_bucket_view=True,
        )

    if context.primary and not output_prepared:
        prepare_output(settings, root)
    context.barrier()
    metadata = {
        "structured_plan_rl": settings.model_dump(mode="json"),
        "resolved_environment": resolved_environment,
        "resolved_season_days": season_days,
        "native_structured_plan_spec": native_spec,
        "source": source,
        "artifact_identities": identities,
        "model": {
            "architecture": model.architecture.payload(),
            "parameters": model.parameter_report(),
        },
        "resume": resume,
        "actor_initialization": initialization,
        "distributed": {
            "world_size": context.world_size,
            "devices": [str(value) for value in devices],
        },
        "decision_surface": "complete official-rule terminal W/D/L",
        "cash_role": "terminal diagnostic only",
    }
    if context.primary:
        (settings.output_dir / "resolved-settings.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
    checkpoint_store = (
        PlanCheckpointStore(settings.output_dir, settings.checkpoint)
        if context.primary
        else None
    )
    initial_rng_state = (
        combine_plan_rng_states(
            context.all_gather(
                capture_plan_rng_state(randomizer, action_generator, device)
            )
        )
        if resume is None
        else None
    )
    if resume is None and checkpoint_store is not None:
        if initial_rng_state is None:
            raise RuntimeError("structured-plan initial RNG checkpoint is absent")
        initial_payload = build_plan_checkpoint(
            model,
            optimizer,
            completed_update=0,
            settings=settings,
            source_revision=revision,
            artifact_identities=identities,
            rng_state=initial_rng_state,
            population_state=population.state_dict(),
            health_state=health.state_dict(),
        )
        checkpoint_store.publish(0, initial_payload, final=False)

    collector = StructuredPlanRolloutCollector(
        backend,
        model,
        population,
        resolved_environment,
        settings.versions.contract(),
        historical_fraction=settings.self_play.historical_fraction,
        event_count=settings.abi.event_features,
        inference_batch_size=settings.rollout.inference_batch_size,
        event_cuda_graph_max_batch_size=(
            settings.rollout.event_cuda_graph_max_batch_size
        ),
        cpu_workers=local_value(
            settings.rollout.cpu_workers,
            context.world_size,
            "rollout cpu_workers",
        ),
        device=device,
        historical_device=device,
        rollout_rank=context.rank,
        rollout_world_size=context.world_size,
        sampling_seed=settings.seed + 3,
        action_generator=action_generator,
    )

    final_update = min(settings.updates, start_update if smoke else settings.updates)
    seed_count = (
        min(4, settings.rollout.seeds_per_update) if smoke else settings.rollout.seeds_per_update
    )
    metrics_path = settings.output_dir / "metrics.jsonl"
    latest: dict[str, object] | None = None
    run_status = "running"
    training_started = time.perf_counter()
    with ExitStack() as stack:
        logger = (
            stack.enter_context(
                ScalarLogger(
                    settings.output_dir,
                    settings.observability,
                    run_metadata=metadata,
                )
            )
            if context.primary
            else None
        )
        for update in range(start_update, final_update + 1):
            update_started = time.perf_counter()
            torch.cuda.reset_peak_memory_stats(device)
            first_seed = (
                settings.rollout_seed_start + (update - 1) * settings.rollout.seeds_per_update
            )
            seeds = tuple(range(first_seed, first_seed + seed_count))
            rollout_started = time.perf_counter()
            rollout = collector.collect(seeds, update=update)
            rollout_seconds = time.perf_counter() - rollout_started
            host_bytes = rollout.batch.tensor_bytes()
            host_limit = int(
                settings.rollout.host_memory_limit_gib * 1024**3 / context.world_size
            )
            if host_bytes > host_limit:
                raise MemoryError("structured-plan rollout exceeds configured host memory")
            reclaim_started = time.perf_counter()
            torch.cuda.empty_cache()
            memory_reclaim_seconds = time.perf_counter() - reclaim_started
            free_gpu, _total_gpu = torch.cuda.mem_get_info(device)
            if host_bytes > int(free_gpu * settings.rollout.gpu_memory_fraction):
                raise MemoryError("structured-plan PPO batch exceeds free GPU fraction")
            transfer_started = time.perf_counter()
            device_batch = rollout.batch.to(device)
            transfer_seconds = time.perf_counter() - transfer_started
            behavior_replay = (
                audit_plan_behavior_likelihood(model, device_batch)
                if smoke
                else None
            )
            optimize_started = time.perf_counter()
            optimized = optimize_plan_batch(
                model,
                training_model,
                optimizer,
                device_batch,
                settings,
                randomizer,
                context,
            )
            optimization_seconds = time.perf_counter() - optimize_started
            optimizer.zero_grad(set_to_none=True)
            mode = device_batch.actions.mode
            plan_changed = (
                (device_batch.actions.line_operations != LINE_KEEP).any(dim=1)
                | (device_batch.actions.global_operation != GLOBAL_KEEP)
            )
            local_update = PlanLocalUpdate(
                rollout=summarize_plan_rollout(
                    rollout,
                    rank=context.rank,
                    device=str(device),
                ),
                behavior_replay=behavior_replay,
                decisions=device_batch.decisions,
                continues=int(torch.count_nonzero(mode == CONTINUE)),
                stops=int(torch.count_nonzero(mode == STOP)),
                patches=int(torch.count_nonzero(plan_changed)),
                active_lines=float(
                    device_batch.inputs.active_line_mask.float().sum()
                ),
                episodes=device_batch.episodes,
                host_bytes=host_bytes,
                rollout_seconds=rollout_seconds,
                memory_reclaim_seconds=memory_reclaim_seconds,
                transfer_seconds=transfer_seconds,
                optimization_seconds=optimization_seconds,
                cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated(device),
                cuda_peak_reserved_bytes=torch.cuda.max_memory_reserved(device),
            )
            aggregated = aggregate_plan_updates(context.all_gather(local_update))
            global_rollout = aggregated.rollout
            historical_games = tuple(
                game
                for game in global_rollout.games
                if game.opponent_id == global_rollout.historical_opponent_id
            )
            historical_evaluation = population.record_outcomes(
                global_rollout.historical_opponent_id,
                update,
                tuple(game.outcome for game in historical_games),
            )
            snapshot_added = population.snapshot(update, model)
            outcomes = outcome_metrics(global_rollout.games)
            health_report = health.observe(
                PlanHealthObservation(
                    update=update,
                    opponent_update=global_rollout.historical_opponent_update,
                    stop_fraction=aggregated.stop_fraction,
                    plan_change_fraction=aggregated.patch_fraction,
                    wins=historical_evaluation.wins,
                    ties=historical_evaluation.ties,
                    losses=historical_evaluation.losses,
                )
            )
            global_update_elapsed = context.maximum(
                time.perf_counter() - update_started
            )
            global_elapsed = context.maximum(
                time.perf_counter() - training_started
            )
            row: dict[str, object] = {
                "update": update,
                "rollout_seed_start": first_seed,
                "source_revision": revision,
                "version_contract": settings.versions.contract().fingerprint,
                "outcomes": outcomes,
                "rollout": global_rollout.diagnostics,
                "optimization": optimized,
                "behavior_replay": aggregated.behavior_replay,
                "health": health_report,
                "population_after_update": {
                    "snapshot_added": snapshot_added,
                    **population.report(),
                },
                "policy": {
                    "continue_fraction": aggregated.continue_fraction,
                    "patch_fraction": aggregated.patch_fraction,
                    "stop_fraction": aggregated.stop_fraction,
                    "active_lines": aggregated.active_lines,
                },
                "batch": {
                    "episodes": aggregated.episodes,
                    "decisions": aggregated.decisions,
                    "host_bytes": aggregated.host_bytes,
                },
                "timing": {
                    "rollout_seconds": aggregated.rollout_seconds,
                    "memory_reclaim_seconds": aggregated.memory_reclaim_seconds,
                    "transfer_seconds": aggregated.transfer_seconds,
                    "optimization_seconds": aggregated.optimization_seconds,
                },
                "system": {
                    "device_count": context.world_size,
                    "update_elapsed_seconds": global_update_elapsed,
                    "cuda_peak_allocated_bytes": (
                        aggregated.cuda_peak_allocated_bytes
                    ),
                    "cuda_peak_reserved_bytes": (
                        aggregated.cuda_peak_reserved_bytes
                    ),
                },
                "elapsed_seconds": global_elapsed,
            }
            quarantined = health.quarantined
            final = update == final_update or quarantined
            checkpoint_record: dict[str, object] | None = None
            checkpoint_due = (
                final
                or update % settings.checkpoint.rolling_interval == 0
                or update % settings.checkpoint.permanent_interval == 0
            )
            checkpoint_rng_state = (
                combine_plan_rng_states(
                    context.all_gather(
                        capture_plan_rng_state(
                            randomizer,
                            action_generator,
                            device,
                        )
                    )
                )
                if checkpoint_due
                else None
            )
            if checkpoint_store is not None and checkpoint_store.due(
                update,
                final=final,
            ):
                if checkpoint_rng_state is None:
                    raise RuntimeError("structured-plan due RNG checkpoint is absent")
                checkpoint_record = checkpoint_store.publish(
                    update,
                    build_plan_checkpoint(
                        model,
                        optimizer,
                        completed_update=update,
                        settings=settings,
                        source_revision=revision,
                        artifact_identities=identities,
                        rng_state=checkpoint_rng_state,
                        population_state=population.state_dict(),
                        health_state=health.state_dict(),
                    ),
                    final=final,
                )
            row["checkpoint"] = checkpoint_record
            if context.primary:
                with metrics_path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, sort_keys=True) + "\n")
                    stream.flush()
                status = settings.output_dir / "run-status.json"
                temporary = status.with_suffix(".json.tmp")
                temporary.write_text(
                    json.dumps(
                        {
                            "status": (
                                "quarantined"
                                if quarantined
                                else "complete" if final else "running"
                            ),
                            "latest": row,
                        },
                        indent=2,
                        sort_keys=True,
                    ),
                    encoding="utf-8",
                )
                temporary.replace(status)
                if logger is None:
                    raise RuntimeError("structured-plan primary logger is absent")
                history_outcomes = cast(
                    dict[str, object],
                    outcomes[global_rollout.historical_opponent_id],
                )
                scalar_row = {
                    **row,
                    "outcomes": {
                        "overall": outcomes["overall"],
                        "self_play": outcomes["self_play"],
                        "history": {
                            **history_outcomes,
                            "opponent_update": (
                                global_rollout.historical_opponent_update
                            ),
                        },
                    },
                }
                logger.scalars("structured_plan_rl", scalar_row, update)
                print(json.dumps(row, sort_keys=True), flush=True)
            latest = row
            if quarantined:
                run_status = "quarantined"
                break
            if final:
                run_status = "complete"
        logging_report = (
            observability_report(logger) if logger is not None else None
        )

    context.barrier()
    report = {
        "status": (
            "quarantined"
            if run_status == "quarantined"
            else "smoke_complete" if smoke else "training_complete"
        ),
        "completed_update": None if latest is None else latest["update"],
        "output_dir": str(settings.output_dir),
        "source_revision": revision,
        "observability": logging_report,
        "latest": latest,
    }
    if context.primary:
        (settings.output_dir / "training-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
    return report


def _distributed_worker_entry(
    rank: int,
    settings: StructuredPlanRlSettings,
    repository_root_value: str,
    smoke: bool,
    rendezvous_value: str,
) -> None:
    """Spawn one process that owns exactly one rollout and PPO device."""
    context = initialize_context(
        rank,
        settings.devices,
        Path(rendezvous_value),
    )
    try:
        _train_structured_plan_worker(
            settings,
            Path(repository_root_value),
            smoke=smoke,
            context=context,
            output_prepared=True,
        )
    finally:
        destroy_context(context)


def train_structured_plan(
    raw_settings: StructuredPlanRlSettings,
    repository_root: Path,
    *,
    smoke: bool,
) -> dict[str, object]:
    """Run one single-rank or NCCL-synchronized structured-plan lineage."""
    root = repository_root.resolve()
    settings = resolve_settings(raw_settings, root)
    devices = tuple(torch.device(value) for value in settings.devices)
    available_devices = torch.cuda.device_count()
    if any(
        device.index is None or device.index >= available_devices for device in devices
    ):
        raise RuntimeError("structured-plan training device is unavailable")
    if len(devices) == 1:
        return _train_structured_plan_worker(
            settings,
            root,
            smoke=smoke,
            context=single_process_context(devices[0]),
            output_prepared=False,
        )
    source = source_identity(root)
    if not smoke and bool(source["worktree_dirty"]):
        raise RuntimeError(
            "long structured-plan training requires a clean committed source revision"
        )
    prepare_output(settings, root)
    rendezvous = settings.output_dir / ".ddp-rendezvous"
    try:
        torch_multiprocessing.spawn(  # type: ignore[attr-defined, no-untyped-call]
            _distributed_worker_entry,
            args=(
                settings,
                str(root),
                smoke,
                str(rendezvous),
            ),
            nprocs=len(devices),
            join=True,
        )
    finally:
        rendezvous.unlink(missing_ok=True)
    report_path = settings.output_dir / "training-report.json"
    value: object = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("distributed structured-plan report is not a mapping")
    return cast(dict[str, object], value)


__all__ = ["train_structured_plan"]
