"""Complete-match terminal-W/D/L conditional-program training."""

from __future__ import annotations

import json
import random
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypedDict, cast

import numpy as np
import torch
from torch import multiprocessing as torch_multiprocessing
from torch import nn
from torch.nn.parallel import DistributedDataParallel

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.model import parameter_count
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.rl.distributed import (
    DistributedContext,
    destroy_context,
    initialize_context,
    local_value,
    single_process_context,
)
from kagg_revue.rl.programs.checkpoint import (
    ProgramCheckpointStore,
    capture_program_rng_state,
    load_program_checkpoint,
    restore_program_rng_state,
)
from kagg_revue.rl.programs.config import ProgramRlSettings
from kagg_revue.rl.programs.initialization import initialize_program_model
from kagg_revue.rl.programs.learning import optimize_program_rollout
from kagg_revue.rl.programs.metrics import (
    outcome_metrics,
)
from kagg_revue.rl.programs.metrics import (
    outcome_rows as extract_outcome_rows,
)
from kagg_revue.rl.programs.model import ProgramActorCritic
from kagg_revue.rl.programs.rollout import ProgramRolloutCollector
from kagg_revue.rl.programs.schedule import rollout_seed_offset, update_range


class _RolloutPayload(TypedDict):
    """Small rank-local rollout summary safe to gather through NCCL."""

    rank: int
    device: str
    seconds: float
    physical_games: int
    training_trajectories: int
    official_turns: int
    program_decisions: int
    official_decisions: int
    maximum_actor_seconds: float
    remaining_overage_seconds: float
    host_bytes: int
    rollout_device_bytes: int
    phase_seconds: dict[str, float]
    program_phase_seconds: dict[str, float]
    outcomes: list[tuple[str, int, float, float]]


class _MemoryPayload(TypedDict):
    """Per-rank peak HBM telemetry."""

    device: str
    bytes: int
    fraction: float


def resolve_program_settings(settings: ProgramRlSettings, root: Path) -> ProgramRlSettings:
    """Resolve repository-relative artifact paths after Hydra validation."""

    def resolve(path: Path) -> Path:
        return path.resolve() if path.is_absolute() else (root / path).resolve()

    return settings.model_copy(
        update={
            "initial_actor": resolve(settings.initial_actor),
            "initial_checkpoint": (
                resolve(settings.initial_checkpoint)
                if settings.initial_checkpoint is not None
                else None
            ),
            "resume_checkpoint": (
                resolve(settings.resume_checkpoint)
                if settings.resume_checkpoint is not None
                else None
            ),
            "public_agent_manifest": (
                resolve(settings.public_agent_manifest)
                if settings.public_agent_manifest is not None
                else None
            ),
            "output_dir": resolve(settings.output_dir),
        }
    )


def _prepare_output(settings: ProgramRlSettings, root: Path) -> None:
    output_root = (root / "outputs").resolve()
    if not settings.output_dir.is_relative_to(output_root):
        raise ValueError("conditional-program output escaped repository outputs/")
    if settings.resume_checkpoint is None:
        if settings.output_dir.exists():
            raise FileExistsError(
                f"conditional-program output already exists: {settings.output_dir}"
            )
        settings.output_dir.mkdir(parents=True)
        return
    if not settings.output_dir.is_dir():
        raise FileNotFoundError("conditional-program resume output directory is absent")
    checkpoint_root = (settings.output_dir / "checkpoints").resolve()
    if not settings.resume_checkpoint.is_relative_to(checkpoint_root):
        raise ValueError("conditional-program resume checkpoint belongs to another run")


def _contract(backend: BackendApi, settings: ProgramRlSettings) -> NativeProgramContract:
    raw = cast(
        Mapping[str, object],
        backend.conditional_program_spec(settings.environment, settings.abi.unit_limit),
    )
    return NativeProgramContract.from_spec(raw)


def _contract_identity(contract: NativeProgramContract) -> dict[str, object]:
    """Return measured native dimensions stored with generated artifacts."""
    return {
        "version": contract.version,
        "board_size": contract.board_size,
        "unit_limit": contract.unit_limit,
        "maximum_market_orders": contract.maximum_market_orders,
        "maximum_decisions": contract.maximum_decisions,
        "root_feature_count": contract.root_feature_count,
        "option_feature_count": contract.option_feature_count,
        "maximum_exact_quantity": contract.maximum_exact_quantity,
        "exact_quantity_bits": contract.exact_quantity_bits,
    }


def _validate_architecture(
    model: ProgramActorCritic,
    contract: NativeProgramContract,
    settings: ProgramRlSettings,
) -> None:
    expected = contract.architecture(
        context_width=model.actor.architecture.model_width,
        model_width=settings.model.model_width,
        feedforward_width=settings.model.feedforward_width,
    )
    if model.programs.architecture != expected:
        raise ValueError("conditional-program checkpoint architecture differs from profile")


def _configure_optimizer(optimizer: torch.optim.Optimizer, device: torch.device) -> None:
    fused = device.type == "cuda"
    for group in optimizer.param_groups:
        group["fused"] = fused
    if fused:
        for state in optimizer.state.values():
            step = state.get("step")
            if isinstance(step, torch.Tensor) and step.device != device:
                state["step"] = step.to(device=device)


def _initialize(
    settings: ProgramRlSettings,
    contract: NativeProgramContract,
    device: torch.device,
    randomizer: random.Random,
) -> tuple[
    ProgramActorCritic,
    torch.optim.Optimizer,
    dict[str, object],
    int,
]:
    if settings.resume_checkpoint is None and settings.initial_checkpoint is None:
        model, actor_identity = initialize_program_model(
            settings.initial_actor, contract, settings.model, device
        )
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=settings.optimization.learning_rate,
            weight_decay=settings.optimization.weight_decay,
            fused=device.type == "cuda",
        )
        return model, optimizer, actor_identity, 1
    if settings.resume_checkpoint is None:
        if settings.initial_checkpoint is None:
            raise RuntimeError("conditional-program initialization is ambiguous")
        model, metadata = load_program_checkpoint(settings.initial_checkpoint, contract, device)
        _validate_architecture(model, contract, settings)
        raw_actor_identity = metadata.get("source_actor_identity")
        checkpoint_identity = metadata.get("checkpoint_identity")
        if (
            not isinstance(raw_actor_identity, Mapping)
            or not isinstance(checkpoint_identity, Mapping)
            or Path(str(raw_actor_identity.get("path"))).resolve()
            != settings.initial_actor.resolve()
            or not settings.initial_actor.is_file()
            or raw_actor_identity.get("sha256") != sha256_file(settings.initial_actor)
        ):
            raise ValueError("conditional-program BC checkpoint source actor changed")
        actor_identity = {
            **dict(raw_actor_identity),
            "initial_program_checkpoint": dict(checkpoint_identity),
            "initial_program_optimizer_imported": False,
            "initial_program_rng_imported": False,
        }
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=settings.optimization.learning_rate,
            weight_decay=settings.optimization.weight_decay,
            fused=device.type == "cuda",
        )
        return model, optimizer, actor_identity, 1
    model, metadata = load_program_checkpoint(settings.resume_checkpoint, contract, device)
    _validate_architecture(model, contract, settings)
    resumed_actor_identity = metadata.get("source_actor_identity")
    optimizer_state = metadata.get("optimizer_state")
    update = metadata.get("update")
    if (
        not isinstance(resumed_actor_identity, Mapping)
        or not isinstance(optimizer_state, Mapping)
        or not isinstance(update, int)
    ):
        raise ValueError("conditional-program resume checkpoint is incomplete")
    if (
        Path(str(resumed_actor_identity.get("path"))).resolve() != settings.initial_actor.resolve()
        or not settings.initial_actor.is_file()
        or resumed_actor_identity.get("sha256") != sha256_file(settings.initial_actor)
    ):
        raise ValueError("conditional-program resume source actor changed")
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=settings.optimization.learning_rate,
        weight_decay=settings.optimization.weight_decay,
        fused=device.type == "cuda",
    )
    optimizer.load_state_dict(cast(dict[str, Any], optimizer_state))
    _configure_optimizer(optimizer, device)
    restore_program_rng_state(metadata.get("rng_state"), randomizer, device)
    return model, optimizer, dict(resumed_actor_identity), update + 1


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, default=str), encoding="utf-8")
    temporary.replace(path)


def _train_conditional_program_worker(
    raw_settings: ProgramRlSettings,
    repository_root: Path,
    context: DistributedContext,
    *,
    smoke: bool,
    output_prepared: bool,
) -> dict[str, object]:
    """Run one rank-local rollout and synchronized conditional-program PPO."""
    settings = resolve_program_settings(raw_settings, repository_root)
    device = context.device
    source = source_identity(repository_root)
    if not smoke and source["worktree_dirty"]:
        raise RuntimeError("long conditional-program training requires a clean revision")
    if context.primary and not output_prepared:
        _prepare_output(settings, repository_root)
    context.barrier()
    random.seed(settings.seed)
    np.random.seed(settings.seed)
    torch.manual_seed(settings.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed(settings.seed)
    randomizer = random.Random(settings.seed)
    backend = load_backend(repository_root)
    environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    settings = settings.model_copy(update={"environment": environment})
    contract = _contract(backend, settings)
    model, optimizer, actor_identity, first_update = _initialize(
        settings, contract, device, randomizer
    )
    _validate_architecture(model, contract, settings)
    training_model: nn.Module = model
    if context.enabled:
        if device.type != "cuda" or device.index is None:
            raise ValueError("distributed conditional-program CUDA device is invalid")
        training_model = DistributedDataParallel(
            model,
            device_ids=[device.index],
            output_device=device.index,
            forward_sync_buffers=False,
            find_unused_parameters=False,
            gradient_as_bucket_view=True,
            static_graph=True,
        )
    collector = ProgramRolloutCollector(
        backend,
        model,
        contract,
        repository_root,
        settings.public_agent_manifest,
        environment,
        settings.opponent_weights,
        device,
        batch_games=local_value(
            settings.rollout.batch_games,
            context.world_size,
            "conditional-program rollout batch_games",
        ),
        cpu_workers=local_value(
            settings.rollout.cpu_workers,
            context.world_size,
            "conditional-program rollout cpu_workers",
        ),
        actor_streams=local_value(
            settings.rollout.actor_streams,
            context.world_size,
            "conditional-program rollout actor_streams",
        ),
        cpu_threads=local_value(
            settings.cpu_threads,
            context.world_size,
            "conditional-program cpu_threads",
        ),
        host_memory_limit_gib=(settings.rollout.host_memory_limit_gib / context.world_size),
        sampling_seed=settings.seed + 17_171,
        act_timeout_seconds=settings.act_timeout_seconds,
        remaining_overage_seconds=settings.remaining_overage_seconds,
        rank=context.rank,
        world_size=context.world_size,
    )
    resolved = settings.model_dump(mode="json")
    opponent_identities = json.loads(
        context.consistent_text(
            json.dumps(collector.opponent_identities, sort_keys=True, default=str),
            "conditional-program opponent identities",
        )
    )
    manifest = {
        "schema_version": "conditional-program-run-v1",
        "smoke": smoke,
        "source": source,
        "backend": backend.identity,
        "source_actor": actor_identity,
        "native_program": _contract_identity(contract),
        "program_architecture": model.programs.architecture.model_dump(mode="json"),
        "actor_architecture": model.actor.architecture_json(),
        "parameter_count": parameter_count(model),
        "opponents": opponent_identities,
        "resolved_config": resolved,
        "distributed": {
            "world_size": context.world_size,
            "devices": list(settings.rollout.devices),
        },
    }
    if context.primary:
        _write_json(settings.output_dir / "resolved-settings.json", resolved)
        _write_json(settings.output_dir / "run-manifest.json", manifest)
    context.barrier()
    checkpoint_store = (
        ProgramCheckpointStore(settings.output_dir, settings.checkpoint)
        if context.primary
        else None
    )
    metrics_path = settings.output_dir / "metrics.jsonl"
    updates: list[dict[str, object]] = []
    final_update = settings.updates
    for update in update_range(first_update, final_update):
        started = time.perf_counter()
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        seed_offset = rollout_seed_offset(
            settings.rollout_seed_start,
            update,
            settings.rollout.seeds_per_update,
        )
        seeds = tuple(range(seed_offset, seed_offset + settings.rollout.seeds_per_update))
        rollout_started = time.perf_counter()
        rollout = collector.collect(seeds, update=update, sample=True)
        local_rollout_seconds = time.perf_counter() - rollout_started
        rollout_seconds = context.maximum(local_rollout_seconds)
        rollout_payload: _RolloutPayload = {
            "rank": context.rank,
            "device": str(device),
            "seconds": local_rollout_seconds,
            "physical_games": rollout.physical_games,
            "training_trajectories": len(rollout.episodes),
            "official_turns": rollout.official_turns,
            "program_decisions": rollout.program_decisions,
            "official_decisions": rollout.official_decisions,
            "maximum_actor_seconds": rollout.maximum_actor_seconds,
            "remaining_overage_seconds": rollout.remaining_overage_seconds,
            "host_bytes": rollout.host_bytes,
            "rollout_device_bytes": rollout.device_bytes,
            "phase_seconds": dict(rollout.phase_seconds),
            "program_phase_seconds": dict(rollout.program_phase_seconds),
            "outcomes": extract_outcome_rows(rollout.episodes),
        }
        rollout_payloads = context.all_gather(rollout_payload)
        optimization_started = time.perf_counter()
        optimization = optimize_program_rollout(
            model,
            training_model,
            optimizer,
            rollout.episodes,
            contract,
            settings.optimization,
            device,
            randomizer,
            context,
        )
        optimization_seconds = context.maximum(time.perf_counter() - optimization_started)
        if device.type == "cuda":
            local_peak_device_bytes = torch.cuda.max_memory_allocated(device)
            local_peak_device_fraction = (
                local_peak_device_bytes / torch.cuda.get_device_properties(device).total_memory
            )
        else:
            local_peak_device_bytes = 0
            local_peak_device_fraction = 0.0
        memory_payload: _MemoryPayload = {
            "device": str(device),
            "bytes": local_peak_device_bytes,
            "fraction": local_peak_device_fraction,
        }
        memory_payloads = context.all_gather(memory_payload)
        peak_device_bytes_by_device = {
            str(payload["device"]): int(payload["bytes"]) for payload in memory_payloads
        }
        peak_device_fraction_by_device = {
            str(payload["device"]): float(payload["fraction"]) for payload in memory_payloads
        }
        checkpoint = (
            checkpoint_store.publish(
                update,
                model,
                optimizer,
                final=update == final_update,
                contract=contract,
                source_actor_identity=actor_identity,
                resolved_config=resolved,
                opponent_identities=opponent_identities,
                source_identity=source,
                rng_state=capture_program_rng_state(randomizer, device),
            )
            if checkpoint_store is not None
            else None
        )
        context.barrier()
        elapsed = context.maximum(time.perf_counter() - started)
        physical_games = sum(int(payload["physical_games"]) for payload in rollout_payloads)
        trajectories = sum(int(payload["training_trajectories"]) for payload in rollout_payloads)
        official_turns = sum(int(payload["official_turns"]) for payload in rollout_payloads)
        program_decisions = sum(int(payload["program_decisions"]) for payload in rollout_payloads)
        official_decisions = sum(int(payload["official_decisions"]) for payload in rollout_payloads)
        phase_names = {name for payload in rollout_payloads for name in payload["phase_seconds"]}
        program_phase_names = {
            name for payload in rollout_payloads for name in payload["program_phase_seconds"]
        }
        outcome_rows = [row for payload in rollout_payloads for row in payload["outcomes"]]
        update_metrics: dict[str, object] = {
            "update": update,
            "seeds": list(seeds),
            "outcomes": outcome_metrics(outcome_rows),
            "rollout": {
                "seconds": rollout_seconds,
                "physical_games": physical_games,
                "physical_games_per_second": physical_games / rollout_seconds,
                "training_trajectories": trajectories,
                "training_trajectories_per_second": trajectories / rollout_seconds,
                "official_turns": official_turns,
                "turns_per_second": official_turns / rollout_seconds,
                "program_decisions": program_decisions,
                "program_decisions_per_second": program_decisions / rollout_seconds,
                "official_decisions": official_decisions,
                "maximum_actor_seconds": max(
                    float(payload["maximum_actor_seconds"]) for payload in rollout_payloads
                ),
                "remaining_overage_seconds": min(
                    float(payload["remaining_overage_seconds"]) for payload in rollout_payloads
                ),
                "host_bytes": sum(int(payload["host_bytes"]) for payload in rollout_payloads),
                "rollout_device_bytes": sum(
                    int(payload["rollout_device_bytes"]) for payload in rollout_payloads
                ),
                "phase_seconds": {
                    name: max(
                        payload["phase_seconds"].get(name, 0.0) for payload in rollout_payloads
                    )
                    for name in phase_names
                },
                "program_phase_seconds": {
                    name: max(
                        payload["program_phase_seconds"].get(name, 0.0)
                        for payload in rollout_payloads
                    )
                    for name in program_phase_names
                },
                "rank_seconds": [float(payload["seconds"]) for payload in rollout_payloads],
            },
            "optimization": {
                **optimization,
                "seconds": optimization_seconds,
                "peak_device_bytes": max(peak_device_bytes_by_device.values()),
                "peak_device_fraction": max(peak_device_fraction_by_device.values()),
                "peak_device_bytes_by_device": peak_device_bytes_by_device,
                "peak_device_fraction_by_device": peak_device_fraction_by_device,
            },
            "checkpoint": checkpoint,
            "seconds": elapsed,
        }
        if context.primary:
            with metrics_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(update_metrics, sort_keys=True, default=str) + "\n")
            updates.append(update_metrics)
            print(json.dumps(update_metrics, sort_keys=True, default=str), flush=True)
        del rollout
    collector.close()
    report = {
        "schema_version": "conditional-program-training-report-v1",
        "output_dir": str(settings.output_dir),
        "first_update": first_update,
        "final_update": final_update,
        "updates": updates,
        "source": source,
        "smoke": smoke,
        "distributed_world_size": context.world_size,
    }
    if context.primary:
        _write_json(settings.output_dir / "training-report.json", report)
    context.barrier()
    return report if context.primary else {}


def _distributed_worker_entry(
    rank: int,
    settings_payload: dict[str, object],
    repository_root_value: str,
    rendezvous_value: str,
    smoke: bool,
) -> None:
    """Run one NCCL rank with local rollout and PPO storage."""
    settings = ProgramRlSettings.model_validate(settings_payload)
    context = initialize_context(
        rank,
        settings.rollout.devices,
        Path(rendezvous_value),
    )
    try:
        _train_conditional_program_worker(
            settings,
            Path(repository_root_value),
            context,
            smoke=smoke,
            output_prepared=True,
        )
    finally:
        destroy_context(context)


def train_conditional_program(
    raw_settings: ProgramRlSettings,
    repository_root: Path,
    *,
    smoke: bool,
) -> dict[str, object]:
    """Run single-rank or NCCL-synchronized conditional-program PPO."""
    devices = raw_settings.rollout.devices
    if len(devices) == 1:
        return _train_conditional_program_worker(
            raw_settings,
            repository_root,
            single_process_context(torch.device(devices[0])),
            smoke=smoke,
            output_prepared=False,
        )
    if not torch.cuda.is_available():
        raise RuntimeError("distributed conditional-program training requested without CUDA")
    available = torch.cuda.device_count()
    for value in devices:
        device = torch.device(value)
        if device.index is None or device.index >= available:
            raise RuntimeError(f"distributed conditional-program device is unavailable: {value}")
    settings = resolve_program_settings(raw_settings, repository_root.resolve())
    source = source_identity(repository_root.resolve())
    if not smoke and source["worktree_dirty"]:
        raise RuntimeError("long conditional-program training requires a clean revision")
    _prepare_output(settings, repository_root.resolve())
    rendezvous = settings.output_dir / ".ddp-rendezvous"
    try:
        torch_multiprocessing.spawn(  # type: ignore[attr-defined, no-untyped-call]
            _distributed_worker_entry,
            args=(
                raw_settings.model_dump(mode="python"),
                str(repository_root),
                str(rendezvous),
                smoke,
            ),
            nprocs=len(devices),
            join=True,
        )
    finally:
        rendezvous.unlink(missing_ok=True)
    report_path = settings.output_dir / "training-report.json"
    report_value: object = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report_value, dict):
        raise ValueError("distributed conditional-program report is not a mapping")
    return cast(dict[str, object], report_value)


__all__ = ["resolve_program_settings", "train_conditional_program"]
