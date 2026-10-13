"""Long-running terminal-W/D/L PPO for canonical intent ledgers."""

from __future__ import annotations

import json
import random
import subprocess
import time
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import multiprocessing as torch_multiprocessing
from torch import nn
from torch.nn.parallel import DistributedDataParallel
from torch.optim import AdamW

from kagg_revue.core.backend import load_backend
from kagg_revue.policy.intents.contract import NativeIntentContract
from kagg_revue.policy.intents.model import IntentActorCritic
from kagg_revue.policy.model import parameter_count
from kagg_revue.rl.distributed import (
    DistributedContext,
    destroy_context,
    initialize_context,
    single_process_context,
)
from kagg_revue.rl.intents.checkpoint import (
    IntentCheckpointStore,
    capture_rng,
    load_checkpoint,
    restore_rng,
)
from kagg_revue.rl.intents.config import IntentRlSettings
from kagg_revue.rl.intents.coordination import (
    aggregate_rollouts,
    distributed_rng_state,
    local_seeds,
    outcome_metrics,
    rank_rng_state,
    rollout_payload,
)
from kagg_revue.rl.intents.initialization import initialize_intent_model
from kagg_revue.rl.intents.learning import (
    IntentSequenceEvaluator,
    audit_intent_behavior,
    optimize_intent_batch,
)
from kagg_revue.rl.intents.rollout import IntentRolloutFleet

_BEHAVIOR_AUDIT_EPISODES_PER_RANK = 32


def _integer(values: Mapping[str, object], name: str) -> int:
    value = values.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"intent environment {name} must be an integer")
    return value


def _source_identity(root: Path) -> dict[str, object]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return {"revision": revision, "worktree_dirty": bool(status.strip())}


def _contract(backend: Any, environment: Mapping[str, object]) -> NativeIntentContract:
    spec = backend.intent_ledger_spec()
    if not isinstance(spec, Mapping):
        raise TypeError("native intent spec must be a mapping")
    return NativeIntentContract.from_spec(spec, board_size=_integer(environment, "boardSize"))


def _validate_resumed_model(
    model: IntentActorCritic,
    settings: IntentRlSettings,
    backend: Any,
) -> None:
    actor = model.actor.architecture
    intent = model.intents.architecture
    encoder = backend.actor_encoder_spec()
    codec = backend.action_codec_spec()
    if not isinstance(encoder, Mapping) or not isinstance(codec, Mapping):
        raise TypeError("native actor specs must be mappings")
    if (
        actor.board_shape[-1] != _integer(settings.environment, "boardSize")
        or actor.unit_shape[1] != settings.unit_limit
        or actor.max_history < _integer(settings.environment, "episodeSteps") - 1
        or actor.board_shape[1] != int(encoder["board_channels"])
        or actor.unit_shape[2] != int(encoder["unit_feat"])
        or actor.global_features != int(encoder["global_feat"])
        or actor.action_tokens != len(codec["keys"])
        or intent.item_count != int(encoder["num_items"])
        or intent.maximum_market_orders != _integer(settings.environment, "maxMarketOrdersPerTurn")
        or intent.model_width != settings.model.model_width
        or intent.feedforward_width != settings.model.feedforward_width
    ):
        raise ValueError("resumed intent model differs from the resolved profile")


def _output_dir(settings: IntentRlSettings, root: Path) -> Path:
    """Resolve and validate one repository-owned output directory."""
    output_dir = (root / settings.output_dir).resolve()
    if not output_dir.is_relative_to((root / "outputs").resolve()):
        raise ValueError("intent training output escaped repository outputs/")
    return output_dir


def _prepare_output(settings: IntentRlSettings, root: Path) -> Path:
    """Create one new run directory before workers enter collectives."""
    output_dir = _output_dir(settings, root)
    if output_dir.exists():
        raise FileExistsError(f"intent training output already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    return output_dir


def _configure_optimizer(optimizer: AdamW, device: torch.device) -> None:
    """Keep restored AdamW state on its rank-local learner device."""
    for group in optimizer.param_groups:
        group["fused"] = device.type == "cuda"
    if device.type == "cuda":
        for state in optimizer.state.values():
            step = state.get("step")
            if isinstance(step, torch.Tensor) and step.device != device:
                state["step"] = step.to(device=device)


def _train_intent_worker(
    settings: IntentRlSettings,
    repository_root: Path,
    context: DistributedContext,
    *,
    smoke: bool,
    output_prepared: bool,
) -> dict[str, object]:
    """Run rank-local rollout and synchronized intent PPO."""
    root = repository_root.resolve()
    source = _source_identity(root)
    if not smoke and source["worktree_dirty"]:
        raise RuntimeError("long intent training requires a clean committed revision")
    output_dir = _output_dir(settings, root)
    if context.primary and not output_prepared:
        _prepare_output(settings, root)
    context.barrier()
    device = context.device
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("intent training requested CUDA but no GPU is available")
    if device.type == "cpu":
        torch.set_num_threads(settings.cpu_threads)
    rollout_devices = tuple(torch.device(raw) for raw in settings.rollout_devices)
    if any(rollout_device.type == "cuda" for rollout_device in rollout_devices):
        available_devices = torch.cuda.device_count()
        if any(
            rollout_device.index is None or rollout_device.index >= available_devices
            for rollout_device in rollout_devices
        ):
            raise RuntimeError("intent rollout requested an unavailable CUDA device")
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
    actor_path = root / settings.initial_actor
    contract = _contract(backend, settings.environment)
    initial_metadata: dict[str, object] | None = None
    resume_metadata: dict[str, object] | None = None
    if settings.resume_checkpoint is None:
        if settings.initial_checkpoint is None:
            model, measured_contract, source_actor = initialize_intent_model(
                actor_path,
                backend,
                settings.environment,
                settings.unit_limit,
                settings.model,
                device,
            )
            if measured_contract != contract:
                raise RuntimeError("intent initialization observed an unstable native ABI")
        else:
            model, initial_metadata = load_checkpoint(
                root / settings.initial_checkpoint,
                contract,
                device,
            )
            _validate_resumed_model(model, settings, backend)
            raw_source_actor = initial_metadata.get("source_actor")
            if not isinstance(raw_source_actor, Mapping):
                raise ValueError("intent initial checkpoint lacks source actor identity")
            source_actor = dict(raw_source_actor)
        start_update = 1
    else:
        model, resume_metadata = load_checkpoint(
            root / settings.resume_checkpoint, contract, device
        )
        _validate_resumed_model(model, settings, backend)
        stored_config = resume_metadata.get("resolved_config")
        if not isinstance(stored_config, Mapping):
            raise ValueError("intent resume checkpoint lacks resolved config")
        stored_contract = dict(stored_config)
        for name in (
            "initial_checkpoint",
            "resume_checkpoint",
            "output_dir",
            "updates",
            "checkpoint",
        ):
            stored_contract.pop(name, None)
        if stored_contract != settings.checkpoint_contract():
            raise ValueError("intent resume profile changes training semantics")
        raw_source_actor = resume_metadata.get("source_actor")
        if not isinstance(raw_source_actor, Mapping):
            raise ValueError("intent resume checkpoint lacks source actor identity")
        source_actor = dict(raw_source_actor)
        raw_update = resume_metadata.get("update")
        if not isinstance(raw_update, int) or isinstance(raw_update, bool):
            raise ValueError("intent resume checkpoint has an invalid update")
        start_update = raw_update + 1
        if start_update > settings.updates:
            raise ValueError("intent resume checkpoint is already past requested updates")
    model.actor.requires_grad_(False)
    if settings.model.train_turn_encoder:
        model.actor.scene.requires_grad_(True)
        model.actor.temporal.requires_grad_(True)
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    if not parameters:
        raise RuntimeError("intent profile froze every trainable parameter")
    optimizer = AdamW(
        parameters,
        lr=settings.optimization.learning_rate,
        weight_decay=settings.optimization.weight_decay,
        fused=device.type == "cuda",
    )
    if resume_metadata is not None:
        optimizer_state = resume_metadata.get("optimizer_state")
        if not isinstance(optimizer_state, Mapping):
            raise ValueError("intent resume checkpoint lacks optimizer state")
        optimizer.load_state_dict(cast(dict[str, Any], optimizer_state))
        _configure_optimizer(optimizer, device)
        restore_rng(
            rank_rng_state(resume_metadata.get("rng_state"), context),
            randomizer,
            action_generators,
            stream_devices,
        )
    evaluator: nn.Module = IntentSequenceEvaluator(model)
    if context.enabled:
        if device.type != "cuda" or device.index is None:
            raise ValueError("distributed intent learner requires indexed CUDA devices")
        evaluator = DistributedDataParallel(
            evaluator,
            device_ids=[device.index],
            output_device=device.index,
            forward_sync_buffers=False,
            find_unused_parameters=False,
            gradient_as_bucket_view=True,
            static_graph=False,
        )
    reference_model = deepcopy(model).to(device)
    if context.primary:
        (output_dir / "resolved-config.json").write_text(
            json.dumps(resolved, indent=2, sort_keys=True), encoding="utf-8"
        )
    context.barrier()
    checkpoint_store = (
        IntentCheckpointStore(output_dir, settings.checkpoint) if context.primary else None
    )
    collector = IntentRolloutFleet(
        backend,
        model,
        contract,
        settings.environment,
        unit_limit=settings.unit_limit,
        cpu_workers=settings.rollout.cpu_workers,
        max_transaction_steps=settings.rollout.max_transaction_steps,
        devices=(device,),
        action_generators=action_generators,
        actor_streams_per_device=stream_count,
    )
    metrics_path = output_dir / "metrics.jsonl"
    final_metrics: dict[str, object] = {}
    started = time.perf_counter()
    for update in range(start_update, settings.updates + 1):
        update_started = time.perf_counter()
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        seed_start = settings.rollout_seed_start + (update - 1) * settings.rollout.seeds_per_update
        seeds = tuple(range(seed_start, seed_start + settings.rollout.seeds_per_update))
        rollout = collector.collect(local_seeds(seeds, context))
        rollout_diagnostics, games = aggregate_rollouts(
            context.all_gather(rollout_payload(rollout, context))
        )
        behavior_started = time.perf_counter()
        local_behavior = (
            audit_intent_behavior(
                model,
                rollout.batch,
                device,
                episodes_per_batch=settings.optimization.effective_episodes_per_microbatch,
                maximum_episodes=_BEHAVIOR_AUDIT_EPISODES_PER_RANK,
            )
            if update == start_update
            else None
        )
        local_behavior_seconds = time.perf_counter() - behavior_started
        behavior_seconds = context.maximum(local_behavior_seconds)
        behavior = (
            {name: context.maximum(value) for name, value in local_behavior.items()}
            if local_behavior is not None
            else None
        )
        if local_behavior is not None and device.type == "cuda":
            # The audit uses inference-only shapes that the learner does not
            # reuse.  Return those cached blocks before autograd starts so its
            # first large allocation cannot be fragmented by the audit.
            torch.cuda.empty_cache()
        optimization_started = time.perf_counter()
        learning = optimize_intent_batch(
            model,
            optimizer,
            rollout.batch,
            settings.optimization,
            device,
            randomizer,
            training_model=evaluator,
            reference_model=reference_model,
            context=context,
        )
        optimization_seconds = context.maximum(time.perf_counter() - optimization_started)
        final_metrics = {
            "update": update,
            "seeds": list(seeds),
            **outcome_metrics(games),
            "rollout": rollout_diagnostics,
            "behavior_replay": behavior,
            "optimization": learning,
        }
        local_rng = capture_rng(randomizer, action_generators, stream_devices)
        rank_rng = context.all_gather(local_rng)
        checkpoint_rng = (
            distributed_rng_state(rank_rng, settings.rollout_devices)
            if context.enabled
            else local_rng
        )
        checkpoint_started = time.perf_counter()
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
                rng_state=checkpoint_rng,
            )
            if checkpoint_store is not None
            else None
        )
        checkpoint_seconds = context.maximum(time.perf_counter() - checkpoint_started)
        context.barrier()
        update_seconds = context.maximum(time.perf_counter() - update_started)
        physical_games = _integer(rollout_diagnostics, "physical_games")
        final_metrics["timing"] = {
            "behavior_replay_seconds": behavior_seconds,
            "optimization_seconds": optimization_seconds,
            "checkpoint_seconds": checkpoint_seconds,
            "update_seconds": update_seconds,
            "physical_games_per_second": physical_games / update_seconds,
        }
        if device.type == "cuda":
            memory = context.all_gather(
                {
                    "device": str(device),
                    "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
                    "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
                }
            )
            final_metrics["cuda_memory"] = {
                str(row["device"]): {
                    "peak_allocated_bytes": _integer(row, "peak_allocated_bytes"),
                    "peak_reserved_bytes": _integer(row, "peak_reserved_bytes"),
                }
                for row in memory
            }
        final_metrics["checkpoint"] = checkpoint
        if context.primary:
            with metrics_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(final_metrics, sort_keys=True) + "\n")
        del rollout
        if device.type == "cuda":
            torch.cuda.empty_cache()
    collector.close()
    report = {
        "schema_version": "canonical-intent-ledger-training-report-v1",
        "status": "complete",
        "smoke": smoke,
        "source": source,
        "native_intent_abi": contract.version,
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
        "final_metrics": final_metrics,
    }
    if context.primary:
        (output_dir / "training-report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
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
    """Run one intent rollout and learner rank."""
    settings = IntentRlSettings.model_validate(settings_payload)
    context = initialize_context(
        rank,
        settings.rollout_devices,
        Path(rendezvous_value),
    )
    try:
        _train_intent_worker(
            settings,
            Path(repository_root_value),
            context,
            smoke=smoke,
            output_prepared=True,
        )
    finally:
        destroy_context(context)


def train_intents(
    settings: IntentRlSettings,
    repository_root: Path,
    *,
    smoke: bool,
) -> dict[str, object]:
    """Run single-rank or NCCL-synchronized intent rollout and PPO."""
    root = repository_root.resolve()
    devices = settings.rollout_devices
    if len(devices) == 1:
        return _train_intent_worker(
            settings,
            root,
            single_process_context(torch.device(devices[0])),
            smoke=smoke,
            output_prepared=False,
        )
    if not torch.cuda.is_available():
        raise RuntimeError("distributed intent training requested without CUDA")
    available = torch.cuda.device_count()
    for device_name in devices:
        device = torch.device(device_name)
        if device.type != "cuda" or device.index is None or device.index >= available:
            raise RuntimeError(f"distributed intent device is unavailable: {device_name}")
    source = _source_identity(root)
    if not smoke and source["worktree_dirty"]:
        raise RuntimeError("long intent training requires a clean committed revision")
    output_dir = _prepare_output(settings, root)
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
        raise ValueError("distributed intent report is not a mapping")
    return cast(dict[str, object], report_value)


__all__ = ["train_intents"]
