"""Long-running terminal-W/D/L PPO for atomic-effect policies."""

from __future__ import annotations

import faulthandler
import json
import os
import random
import signal
import time
import traceback
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import multiprocessing as torch_multiprocessing
from torch import nn
from torch.nn.parallel import DistributedDataParallel
from torch.optim import AdamW, Optimizer

from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.model import parameter_count
from kagg_revue.rl.distributed import (
    DistributedContext,
    destroy_context,
    initialize_context,
    single_process_context,
)
from kagg_revue.rl.effects.checkpoint import (
    EffectCheckpointStore,
    capture_rng,
    load_checkpoint,
    restore_rng,
)
from kagg_revue.rl.effects.config import EffectRlSettings
from kagg_revue.rl.effects.coordination import (
    aggregate_rollouts,
    distributed_rng_state,
    local_population_jobs,
    outcome_metrics,
    rank_rng_state,
    rollout_payload,
)
from kagg_revue.rl.effects.fleet import EffectRolloutFleet
from kagg_revue.rl.effects.initialization import (
    configure_effect_trainable,
    effect_optimizer_parameters,
    initialize_challenger,
    initialize_effect_model,
)
from kagg_revue.rl.effects.learning import (
    EffectSequenceEvaluator,
    audit_effect_behavior,
    optimize_effect_batch,
)
from kagg_revue.rl.effects.optimizers import IndependentAdamW
from kagg_revue.rl.effects.population import effect_opponent_identities
from kagg_revue.rl.effects.runtime import (
    configure_optimizer_device,
    integer_metric,
    native_contract,
    output_directory,
    prepare_output_directory,
    profile_row,
    steady_profile,
    stored_training_contract,
    validate_model_profile,
)

_BEHAVIOR_AUDIT_EPISODES_PER_RANK = 32


def _train_effect_worker(
    settings: EffectRlSettings,
    repository_root: Path,
    context: DistributedContext,
    *,
    smoke: bool,
    output_prepared: bool,
) -> dict[str, object]:
    """Run one rank-local complete-game collector and synchronized learner."""
    root = repository_root.resolve()
    source = source_identity(root)
    if not smoke and source["worktree_dirty"]:
        raise RuntimeError("long effect training requires a clean committed revision")
    output_dir = output_directory(settings, root)
    if context.primary and not output_prepared:
        prepare_output_directory(settings, root)
    context.barrier()
    device = context.device
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("effect training requested CUDA but no GPU is available")
    if device.type == "cuda" and (
        device.index is None or device.index >= torch.cuda.device_count()
    ):
        raise RuntimeError(f"effect training requested an unavailable device: {device}")
    if device.type == "cpu":
        torch.set_num_threads(settings.cpu_threads)
    torch.manual_seed(settings.seed)
    np.random.seed(settings.seed)
    randomizer = random.Random(settings.seed)
    stream_count = settings.rollout.actor_streams_per_device
    action_generators = tuple(
        torch.Generator(device=device).manual_seed(
            settings.seed + 1 + context.rank * stream_count + stream
        )
        for stream in range(stream_count)
    )
    stream_devices = (device,) * stream_count
    backend = load_backend(root)
    resolved = settings.model_dump(mode="json")
    contract = native_contract(backend, settings.environment)
    opponent_identities = {
        "population": effect_opponent_identities(
            backend,
            root,
            settings.population.weights,
            settings.public_agent_manifest,
        ),
        "native_backend": backend.identity,
    }
    context.consistent_text(
        json.dumps(opponent_identities, sort_keys=True, default=str),
        "effect opponent identities",
    )
    initial_metadata: dict[str, object] | None = None
    resume_metadata: dict[str, object] | None = None
    if settings.resume_checkpoint is None:
        if settings.initial_checkpoint is None:
            model, measured_contract, source_actor = initialize_effect_model(
                root / settings.initial_actor,
                backend,
                settings.environment,
                settings.unit_limit,
                settings.model,
                device,
            )
            if measured_contract != contract:
                raise RuntimeError("effect initialization observed an unstable native ABI")
        else:
            model, initial_metadata = load_checkpoint(
                root / settings.initial_checkpoint,
                contract,
                device,
            )
            model = initialize_challenger(model, settings.model)
            validate_model_profile(model, settings, backend, contract)
            raw_source_actor = initial_metadata.get("source_actor")
            if not isinstance(raw_source_actor, Mapping):
                raise ValueError("effect initial checkpoint lacks source actor identity")
            source_actor = dict(raw_source_actor)
        start_update = 1
    else:
        model, resume_metadata = load_checkpoint(
            root / settings.resume_checkpoint,
            contract,
            device,
        )
        validate_model_profile(model, settings, backend, contract)
        if stored_training_contract(resume_metadata) != settings.checkpoint_contract():
            raise ValueError("effect resume profile changes training semantics")
        if resume_metadata.get("source_revision") != source:
            raise ValueError("effect resume source revision changed")
        if resume_metadata.get("opponent_identities") != opponent_identities:
            raise ValueError("effect resume opponent identities changed")
        population_state = resume_metadata.get("population_state")
        if not isinstance(population_state, Mapping) or population_state.get("weights") != dict(
            settings.population.weights
        ):
            raise ValueError("effect resume population state changed")
        raw_source_actor = resume_metadata.get("source_actor")
        if not isinstance(raw_source_actor, Mapping):
            raise ValueError("effect resume checkpoint lacks source actor identity")
        source_actor = dict(raw_source_actor)
        raw_update = resume_metadata.get("update")
        if not isinstance(raw_update, int) or isinstance(raw_update, bool):
            raise ValueError("effect resume checkpoint has an invalid update")
        start_update = raw_update + 1
        if start_update > settings.updates:
            raise ValueError("effect resume checkpoint is past the requested updates")
    configure_effect_trainable(
        model,
        train_turn_encoder=settings.model.train_turn_encoder,
    )
    actor_parameters, critic_parameters = effect_optimizer_parameters(model)
    optimizer: Optimizer = AdamW(
        [
            {
                "params": actor_parameters,
                "lr": settings.optimization.actor_learning_rate,
            },
            {
                "params": critic_parameters,
                "lr": settings.optimization.critic_learning_rate,
            },
        ],
        weight_decay=settings.optimization.weight_decay,
        fused=device.type == "cuda",
    )
    if model.critic is not None:
        optimizer = IndependentAdamW(
            actor_parameters,
            critic_parameters,
            actor_lr=settings.optimization.actor_learning_rate,
            critic_lr=settings.optimization.critic_learning_rate,
            weight_decay=settings.optimization.weight_decay,
            fused=device.type == "cuda",
        )
    if resume_metadata is not None:
        optimizer_state = resume_metadata.get("optimizer_state")
        if not isinstance(optimizer_state, Mapping):
            raise ValueError("effect resume checkpoint lacks optimizer state")
        optimizer.load_state_dict(cast(dict[str, Any], optimizer_state))
        configure_optimizer_device(optimizer, device)
        restore_rng(
            rank_rng_state(resume_metadata.get("rng_state"), context),
            randomizer,
            action_generators,
            stream_devices,
        )
    evaluator: nn.Module = EffectSequenceEvaluator(
        model,
        critic_actor_gradient=settings.optimization.critic_actor_gradient,
    )
    if context.enabled:
        if device.type != "cuda" or device.index is None:
            raise ValueError("distributed effect learner requires indexed CUDA devices")
        evaluator = DistributedDataParallel(
            evaluator,
            device_ids=[device.index],
            output_device=device.index,
            forward_sync_buffers=False,
            find_unused_parameters=False,
            gradient_as_bucket_view=True,
            static_graph=False,
        )
        context.barrier()
        torch.cuda.synchronize(device)
    reference_model = deepcopy(model).to(device)
    if context.primary:
        (output_dir / "resolved-config.json").write_text(
            json.dumps(resolved, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    context.barrier()
    checkpoint_store = (
        EffectCheckpointStore(output_dir, settings.checkpoint) if context.primary else None
    )
    collector = EffectRolloutFleet(
        backend,
        model,
        contract,
        settings.environment,
        unit_limit=settings.unit_limit,
        cpu_workers=settings.rollout.cpu_workers,
        device=device,
        action_generators=action_generators,
        maximum_graph_variants=settings.rollout.maximum_graph_variants,
    )
    metrics_path = output_dir / "metrics.jsonl"
    final_metrics: dict[str, object] = {}
    profiles: list[dict[str, object]] = []
    started = time.perf_counter()
    phase = "startup"
    update = start_update
    try:
        for update in range(start_update, settings.updates + 1):
            update_started = time.perf_counter()
            if device.type == "cuda":
                torch.cuda.reset_peak_memory_stats(device)
            seed_start = (
                settings.rollout_seed_start + (update - 1) * settings.rollout.seeds_per_update
            )
            seeds = tuple(range(seed_start, seed_start + settings.rollout.seeds_per_update))
            sampling_seed = settings.seed + update * 1_000_003
            jobs = local_population_jobs(
                seeds,
                settings.population.weights,
                context,
                sampling_seed=sampling_seed,
            )
            phase = "rollout"
            rollout = collector.collect_jobs(jobs)
            rollout_diagnostics, games = aggregate_rollouts(
                context.all_gather(rollout_payload(rollout, context))
            )
            behavior_started = time.perf_counter()
            phase = "behavior_replay"
            local_behavior = (
                audit_effect_behavior(
                    model,
                    rollout.batch,
                    device,
                    episodes_per_batch=(settings.optimization.effective_episodes_per_microbatch),
                    maximum_episodes=_BEHAVIOR_AUDIT_EPISODES_PER_RANK,
                    candidate_elements_per_chunk=(
                        settings.optimization.candidate_elements_per_chunk
                    ),
                    failure_batch_path=str(output_dir / f"behavior-failure-rank-{context.rank}.pt"),
                )
                if update == start_update
                else None
            )
            behavior_seconds = context.maximum(time.perf_counter() - behavior_started)
            behavior = (
                {name: context.maximum(value) for name, value in local_behavior.items()}
                if local_behavior is not None
                else None
            )
            if local_behavior is not None and device.type == "cuda":
                torch.cuda.empty_cache()
            optimization_started = time.perf_counter()
            phase = "learner"
            learning = optimize_effect_batch(
                model,
                optimizer,
                rollout.batch,
                settings.optimization,
                device,
                randomizer,
                training_model=evaluator,
                reference_model=reference_model,
                context=context,
                actor_requested=(update > settings.optimization.critic_warmup_updates),
                gae_lambda=settings.gae_lambda,
                critic_actor_gradient=settings.optimization.critic_actor_gradient,
            )
            optimization_seconds = context.maximum(time.perf_counter() - optimization_started)
            local_rng = capture_rng(randomizer, action_generators, stream_devices)
            rank_rng = context.all_gather(local_rng)
            checkpoint_rng = (
                distributed_rng_state(rank_rng, settings.rollout_devices)
                if context.enabled
                else local_rng
            )
            checkpoint_started = time.perf_counter()
            phase = "checkpoint"
            checkpoint = (
                checkpoint_store.publish(
                    update,
                    model,
                    optimizer,
                    final=update == settings.updates,
                    contract=contract,
                    resolved_config=resolved,
                    source_actor=source_actor,
                    source_revision=source,
                    opponent_identities=opponent_identities,
                    population_state={
                        "schema_version": "atomic-effect-weighted-population-v1",
                        "weights": dict(settings.population.weights),
                        "sampling_seed": sampling_seed,
                    },
                    rng_state=checkpoint_rng,
                )
                if checkpoint_store is not None
                else None
            )
            checkpoint_seconds = context.maximum(time.perf_counter() - checkpoint_started)
            context.barrier()
            update_seconds = context.maximum(time.perf_counter() - update_started)
            physical_games = integer_metric(rollout_diagnostics, "physical_games")
            timing = {
                "behavior_replay_seconds": behavior_seconds,
                "optimization_seconds": optimization_seconds,
                "checkpoint_seconds": checkpoint_seconds,
                "update_seconds": update_seconds,
                "physical_games_per_second": physical_games / update_seconds,
            }
            memory: dict[str, object] | None = None
            if device.type == "cuda":
                memory_rows = context.all_gather(
                    {
                        "device": str(device),
                        "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
                        "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
                    }
                )
                memory = {
                    str(row["device"]): {
                        "peak_allocated_bytes": integer_metric(row, "peak_allocated_bytes"),
                        "peak_reserved_bytes": integer_metric(row, "peak_reserved_bytes"),
                    }
                    for row in memory_rows
                }
            final_metrics = {
                "update": update,
                "seeds": [seeds[0], seeds[-1]],
                **outcome_metrics(games),
                "rollout": rollout_diagnostics,
                "behavior_replay": behavior,
                "optimization": learning,
                "timing": timing,
                "cuda_memory": memory,
                "checkpoint": checkpoint,
            }
            profile = profile_row(
                update,
                rollout_diagnostics,
                learning,
                timing,
                memory,
            )
            profiles.append(profile)
            if context.primary:
                with metrics_path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(final_metrics, sort_keys=True) + "\n")
            phase = "release_rollout"
            del rollout
            if device.type == "cuda":
                torch.cuda.empty_cache()
    except BaseException:
        failure = {
            "update": update,
            "rank": context.rank,
            "phase": phase,
            "traceback": traceback.format_exc(),
            "source": source,
        }
        # Persist the first exception before graph/pinned-memory cleanup can
        # surface a secondary CUDA exception and obscure the causal operation.
        (output_dir / f"failure-rank-{context.rank}.json").write_text(
            json.dumps(failure, indent=2),
            encoding="utf-8",
        )
        traceback.print_exc()
        raise
    else:
        collector.close()
    warmup_profiles = [
        profile
        for profile in profiles
        if integer_metric(profile, "update") <= settings.optimization.critic_warmup_updates
    ]
    actor_profiles = [
        profile
        for profile in profiles
        if integer_metric(profile, "update") > settings.optimization.critic_warmup_updates
    ]
    steady_actor_profiles = actor_profiles if warmup_profiles else actor_profiles[1:]
    report = {
        "schema_version": "atomic-effect-training-report-v1",
        "status": "complete",
        "smoke": smoke,
        "source": source,
        "native_effect_abi": contract.version,
        "native_backend": backend.identity,
        "opponents": opponent_identities["population"],
        "source_actor": source_actor,
        "initial_checkpoint": (
            None if initial_metadata is None else initial_metadata["checkpoint_identity"]
        ),
        "parameter_count": parameter_count(model),
        "trainable_parameter_count": sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        ),
        "distributed_world_size": context.world_size,
        "updates_completed": max(0, settings.updates - start_update + 1),
        "final_update": settings.updates,
        "elapsed_seconds": time.perf_counter() - started,
        "cold_start_profile": profiles[0] if profiles else None,
        "critic_warmup_profile": steady_profile(warmup_profiles[1:]),
        "steady_state_profile": steady_profile(steady_actor_profiles),
        "update_profiles": profiles,
        "final_metrics": final_metrics,
    }
    if context.primary:
        (output_dir / "training-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    context.barrier()
    return report if context.primary else {}


def _distributed_worker_entry(
    rank: int,
    settings_payload: dict[str, object],
    repository_root_value: str,
    rendezvous_value: str,
    smoke: bool,
) -> None:
    # A stalled native/CUDA worker may not surface an exception. Keep an
    # on-demand all-thread dump available without polling the training loop.
    faulthandler.register(signal.SIGUSR1, all_threads=True)
    compiler_cache = os.environ.get("TORCHINDUCTOR_CACHE_DIR")
    if compiler_cache:
        os.environ["TORCHINDUCTOR_CACHE_DIR"] = str(Path(compiler_cache) / f"rank-{rank}")
    settings = EffectRlSettings.model_validate(settings_payload)
    context = initialize_context(
        rank,
        settings.rollout_devices,
        Path(rendezvous_value),
    )
    _train_effect_worker(
        settings,
        Path(repository_root_value),
        context,
        smoke=smoke,
        output_prepared=True,
    )
    # Graceful NCCL teardown can wait forever if a peer is still in a
    # collective. Let failures reach the spawn supervisor, which stops peers.
    destroy_context(context)


def train_effects(
    settings: EffectRlSettings,
    repository_root: Path,
    *,
    smoke: bool,
) -> dict[str, object]:
    """Run single-rank or NCCL-synchronized atomic-effect PPO."""
    root = repository_root.resolve()
    devices = settings.rollout_devices
    if len(devices) == 1:
        return _train_effect_worker(
            settings,
            root,
            single_process_context(torch.device(devices[0])),
            smoke=smoke,
            output_prepared=False,
        )
    if not torch.cuda.is_available():
        raise RuntimeError("distributed effect training requested without CUDA")
    available = torch.cuda.device_count()
    for device_name in devices:
        device = torch.device(device_name)
        if device.type != "cuda" or device.index is None or device.index >= available:
            raise RuntimeError(f"distributed effect device is unavailable: {device_name}")
    source = source_identity(root)
    if not smoke and source["worktree_dirty"]:
        raise RuntimeError("long effect training requires a clean committed revision")
    output_dir = prepare_output_directory(settings, root)
    rendezvous = output_dir / ".ddp-rendezvous"
    try:
        torch_multiprocessing.spawn(  # type: ignore[attr-defined, no-untyped-call]
            _distributed_worker_entry,
            args=(
                settings.model_dump(mode="python"),
                str(root),
                str(rendezvous),
                smoke,
            ),
            nprocs=len(devices),
            join=True,
        )
    finally:
        rendezvous.unlink(missing_ok=True)
    report_path = output_dir / "training-report.json"
    report_value: object = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report_value, dict):
        raise ValueError("distributed effect report is not a mapping")
    return cast(dict[str, object], report_value)


__all__ = ["train_effects"]
