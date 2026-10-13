"""Complete-match terminal-WDL training for the unit-task-tape challenger."""

from __future__ import annotations

import json
import random
import time
from collections.abc import Mapping, Sequence
from dataclasses import fields
from pathlib import Path
from typing import cast

import numpy as np
import torch
from torch import multiprocessing as torch_multiprocessing
from torch import nn
from torch.nn.parallel import DistributedDataParallel

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.rl.data import TrajectoryTurns
from kagg_revue.rl.distributed import (
    DistributedContext,
    destroy_context,
    initialize_context,
    local_value,
    single_process_context,
)
from kagg_revue.rl.tasks.checkpoint import (
    TaskCheckpointStore,
    capture_task_rng_state,
    load_task_checkpoint,
    restore_task_rng_state,
)
from kagg_revue.rl.tasks.compact import compact_task_bytes
from kagg_revue.rl.tasks.config import TaskRlSettings
from kagg_revue.rl.tasks.data import TaskDecisionRecord, TaskTapeEpisode
from kagg_revue.rl.tasks.incumbent import incumbent_identity, resolve_incumbent
from kagg_revue.rl.tasks.initialization import initialize_task_model
from kagg_revue.rl.tasks.learning import optimize_task_rollout
from kagg_revue.rl.tasks.model import TaskTapeActorCritic
from kagg_revue.rl.tasks.rollout import TaskRolloutCollector
from kagg_revue.rl.tasks.storage import CompactTaskEpisodeTurns

OutcomeRow = tuple[str, int, int, int, float, float]


def _as_int(value: object, name: str) -> int:
    """Narrow one JSON-compatible numeric diagnostic to an integer."""
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"unit-task {name} is not numeric")
    return int(value)


def _as_float(value: object, name: str) -> float:
    """Narrow one JSON-compatible numeric diagnostic to a float."""
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"unit-task {name} is not numeric")
    return float(value)


def _private_pool_reserved_bytes(device: torch.device) -> int:
    """Return bytes held by live CUDA Graph private pools on one H200."""
    return sum(
        value
        for key, value in torch.cuda.memory_stats(device).items()
        if key.startswith("reserved_bytes_by_private_pools.") and key.endswith(".all.current")
    )


def _configure_optimizer_runtime(
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    *,
    learning_rate: float | None = None,
) -> None:
    """Apply H200 fused-Adam options after loading portable optimizer state."""
    fused = device.type == "cuda"
    for group in optimizer.param_groups:
        if learning_rate is not None:
            group["lr"] = learning_rate
        group["fused"] = fused
    if not fused:
        return
    for state in optimizer.state.values():
        step = state.get("step")
        if isinstance(step, torch.Tensor) and step.device != device:
            state["step"] = step.to(device=device)


def resolve_task_settings(settings: TaskRlSettings, root: Path) -> TaskRlSettings:
    """Resolve artifact paths after Hydra validation kept them repository-relative."""

    def resolve(path: Path) -> Path:
        return path.resolve() if path.is_absolute() else (root / path).resolve()

    return settings.model_copy(
        update={
            "initial_actor": (
                resolve(settings.initial_actor) if settings.initial_actor is not None else None
            ),
            "initial_task_checkpoint": (
                resolve(settings.initial_task_checkpoint)
                if settings.initial_task_checkpoint is not None
                else None
            ),
            "resume_checkpoint": (
                resolve(settings.resume_checkpoint)
                if settings.resume_checkpoint is not None
                else None
            ),
            "public_agent_manifest": resolve(settings.public_agent_manifest),
            "output_dir": resolve(settings.output_dir),
            "incumbent": resolve_incumbent(settings.incumbent, root),
        }
    )


def _prepare_output(settings: TaskRlSettings, root: Path) -> None:
    output_root = (root / "outputs").resolve()
    if not settings.output_dir.is_relative_to(output_root):
        raise ValueError("unit-task training output must remain under outputs/")
    if settings.resume_checkpoint is None:
        if settings.output_dir.exists():
            raise FileExistsError(
                f"unit-task training output already exists: {settings.output_dir}"
            )
        settings.output_dir.mkdir(parents=True)
        return
    if not settings.output_dir.is_dir():
        raise FileNotFoundError("unit-task resume output directory does not exist")
    checkpoint_root = (settings.output_dir / "checkpoints").resolve()
    if not settings.resume_checkpoint.resolve().is_relative_to(checkpoint_root):
        raise ValueError("unit-task resume checkpoint must belong to its output run")


def _contract(backend: BackendApi, settings: TaskRlSettings) -> NativeTaskContract:
    raw = cast(
        Mapping[str, object],
        backend.unit_task_spec(
            settings.environment,
            settings.abi.unit_limit,
            settings.abi.maximum_quantity,
        ),
    )
    return NativeTaskContract.from_spec(raw)


def _contract_identity(contract: NativeTaskContract) -> dict[str, object]:
    return {
        "version": contract.version,
        "catalog_fingerprint": contract.catalog_fingerprint,
        "candidate_count": contract.candidate_count,
        "candidate_feature_count": contract.candidate_feature_count,
        "root_feature_count": contract.root_feature_count,
        "task_field_count": contract.task_field_count,
        "prefix_capacity": contract.prefix_capacity,
        "time_token_count": contract.time_token_count,
        "maximum_quantity": contract.maximum_quantity,
        "unit_limit": contract.unit_limit,
        "board_size": contract.board_size,
    }


def _initialization_identity(settings: TaskRlSettings) -> dict[str, object]:
    """Authenticate the optional task checkpoint and optimizer warm start."""
    checkpoint = settings.initial_task_checkpoint
    expected_sha256 = settings.initial_task_checkpoint_sha256
    if checkpoint is None:
        if expected_sha256 is not None:
            raise ValueError("unit-task initialization hash lacks a checkpoint")
        return {"kind": "random_task_head"}
    if expected_sha256 is None:
        raise ValueError("unit-task initialization checkpoint lacks its hash")
    if not checkpoint.is_file():
        raise FileNotFoundError(f"unit-task initialization checkpoint is absent: {checkpoint}")
    actual_sha256 = sha256_file(checkpoint)
    if actual_sha256 != expected_sha256:
        raise ValueError("unit-task initialization checkpoint hash changed")
    return {
        "kind": "unit_task_checkpoint",
        "checkpoint": {
            "path": str(checkpoint),
            "sha256": actual_sha256,
            "size_bytes": checkpoint.stat().st_size,
        },
        "optimizer_imported": settings.initial_optimizer == "import",
    }


def _validate_source_actor(
    source_actor: Mapping[str, object],
    settings: TaskRlSettings,
) -> dict[str, object]:
    """Authenticate actor provenance for actor-only and complete warm starts."""
    if settings.initial_actor is None:
        if settings.initial_task_checkpoint is None:
            raise ValueError("unit-task source actor lacks an initialization artifact")
        encoder_version = source_actor.get("actor_encoder_version")
        action_keys = source_actor.get("action_keys")
        if (
            not isinstance(encoder_version, str)
            or not encoder_version
            or not isinstance(action_keys, Sequence)
            or isinstance(action_keys, str | bytes)
            or not action_keys
            or not all(isinstance(value, str) and value for value in action_keys)
        ):
            raise ValueError("unit-task complete checkpoint lacks actor runtime provenance")
        return dict(source_actor)
    if (
        Path(str(source_actor.get("path"))).resolve() != settings.initial_actor.resolve()
        or not settings.initial_actor.is_file()
        or source_actor.get("sha256") != sha256_file(settings.initial_actor)
    ):
        raise ValueError("unit-task source actor differs from the configured artifact")
    return dict(source_actor)


def _validate_task_architecture(
    model: TaskTapeActorCritic,
    contract: NativeTaskContract,
    settings: TaskRlSettings,
) -> None:
    """Reject BC heads whose measured architecture differs from this profile."""
    expected = contract.architecture(
        architecture_version=settings.model.architecture_version,
        context_width=model.actor.architecture.model_width,
        model_width=settings.model.model_width,
        feedforward_width=settings.model.feedforward_width,
        attention_heads=settings.model.attention_heads,
        prefix_layers=settings.model.prefix_layers,
        history_window=settings.model.history_window,
    )
    if model.tasks.architecture != expected:
        raise ValueError(
            "unit-task initialization checkpoint architecture differs from the profile"
        )


def _record_bytes(record: TaskDecisionRecord) -> int:
    return sum(
        int(np.asarray(getattr(record, name)).nbytes)
        for name in (
            "root_features",
            "prefix_fields",
            "prefix_mask",
            "candidate_features",
            "candidate_mask",
            "candidate_arrivals",
            "mode_mask",
            "action",
            "quantity_mask",
            "earliest_mask",
            "deadline_mask",
            "factor_mask",
        )
    )


def _episode_bytes(episode: TaskTapeEpisode) -> int:
    total = int(episode.market_factor_mask.nbytes)
    turns = episode.trajectory.turns
    if isinstance(turns, TrajectoryTurns):
        total += sum(int(value.nbytes) for value in turns.arrays())
    else:
        for turn in turns:
            for field in fields(turn):
                value = getattr(turn, field.name)
                if isinstance(value, np.ndarray):
                    total += int(value.nbytes)
    compact_bytes = (
        episode.compact_task_turns.nbytes
        if isinstance(episode.compact_task_turns, CompactTaskEpisodeTurns)
        else sum(compact_task_bytes(record) for record in episode.compact_task_turns)
    )
    return (
        total + sum(_record_bytes(record) for record in episode.task_records) + int(compact_bytes)
    )


def _outcome_metrics(episodes: Sequence[TaskTapeEpisode]) -> dict[str, object]:
    rows = [
        (
            episode.trajectory.opponent_id,
            episode.trajectory.seed,
            episode.trajectory.seat,
            episode.trajectory.outcome,
            episode.trajectory.terminal_cash,
            episode.trajectory.opponent_cash,
        )
        for episode in episodes
    ]
    return _outcome_metrics_from_rows(rows)


def _outcome_metrics_from_rows(
    rows: Sequence[OutcomeRow],
) -> dict[str, object]:
    """Summarize small rank-gathered direct outcomes without tensor payloads."""
    result: dict[str, object] = {}
    groups = {
        opponent: [row for row in rows if row[0] == opponent]
        for opponent in sorted({row[0] for row in rows})
    }
    physical_rows: list[OutcomeRow] = []
    for opponent, group in groups.items():
        summarized = group
        if opponent == "self_play":
            by_seed: dict[int, dict[int, OutcomeRow]] = {}
            for row in group:
                seats = by_seed.setdefault(row[1], {})
                if row[2] in seats:
                    raise ValueError("unit-task self-play repeated a seat perspective")
                seats[row[2]] = row
            summarized = []
            for seats in by_seed.values():
                if set(seats) != {0, 1}:
                    raise ValueError("unit-task self-play outcome lacks one seat")
                first, second = seats[0], seats[1]
                if first[3] != -second[3] or first[4] != second[5] or first[5] != second[4]:
                    raise ValueError("unit-task self-play outcome perspectives differ")
                summarized.append(first)
        physical_rows.extend(summarized)
        outcomes = [row[3] for row in summarized]
        cash = [row[4] for row in summarized]
        differences = [row[4] - row[5] for row in summarized]
        result[opponent] = {
            "games": len(summarized),
            "training_episodes": len(group),
            "wins": sum(value > 0 for value in outcomes),
            "ties": sum(value == 0 for value in outcomes),
            "losses": sum(value < 0 for value in outcomes),
            "mean_terminal_cash": float(np.mean(cash)),
            "mean_cash_difference": float(np.mean(differences)),
        }
    all_outcomes = [row[3] for row in physical_rows]
    result["overall"] = {
        "games": len(physical_rows),
        "training_episodes": len(rows),
        "wins": sum(value > 0 for value in all_outcomes),
        "ties": sum(value == 0 for value in all_outcomes),
        "losses": sum(value < 0 for value in all_outcomes),
    }
    return result


def _append_json(path: Path, value: Mapping[str, object]) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, default=str))
        stream.write("\n")


_DISTRIBUTED_TASK_RNG_VERSION = "unit-task-tape-distributed-rng-v1"


def _capture_worker_rng_state(
    context: DistributedContext,
    randomizer: random.Random,
    device: torch.device,
) -> dict[str, object]:
    """Capture every rank's small stochastic state at one update boundary."""
    states = context.all_gather(capture_task_rng_state(randomizer, device))
    return {
        "version": _DISTRIBUTED_TASK_RNG_VERSION,
        "world_size": context.world_size,
        "ranks": states,
    }


def _restore_worker_rng_state(
    value: object,
    context: DistributedContext,
    randomizer: random.Random,
    device: torch.device,
) -> None:
    """Restore exactly the stochastic stream owned by this distributed rank."""
    if not context.enabled:
        if isinstance(value, Mapping) and value.get("version") == (_DISTRIBUTED_TASK_RNG_VERSION):
            ranks = value.get("ranks")
            if value.get("world_size") != 1 or not isinstance(ranks, Sequence) or len(ranks) != 1:
                raise ValueError("unit-task checkpoint RNG world differs from training")
            value = ranks[0]
        restore_task_rng_state(value, randomizer, device)
        return
    if (
        not isinstance(value, Mapping)
        or value.get("version") != _DISTRIBUTED_TASK_RNG_VERSION
        or value.get("world_size") != context.world_size
    ):
        raise ValueError("distributed unit-task checkpoint RNG topology changed")
    ranks = value.get("ranks")
    if not isinstance(ranks, Sequence) or len(ranks) != context.world_size:
        raise ValueError("distributed unit-task checkpoint RNG ranks are incomplete")
    restore_task_rng_state(ranks[context.rank], randomizer, device)


def _train_task_tape_worker(
    raw_settings: TaskRlSettings,
    repository_root: Path,
    context: DistributedContext,
    *,
    smoke: bool,
    output_prepared: bool,
) -> dict[str, object]:
    """Train one identity-bound unit-task challenger on complete matches."""
    root = repository_root.resolve()
    settings = resolve_task_settings(raw_settings, root)
    device = context.device
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA unit-task training was requested but is unavailable")
    if device.type == "cuda":
        torch.cuda.set_device(device)
    torch.set_num_threads(settings.cpu_threads)
    rank_seed = settings.seed + context.rank * 10_000_019
    randomizer = random.Random(rank_seed + 1)
    np.random.seed(rank_seed % (2**32))
    torch.manual_seed(rank_seed)
    if device.type == "cuda":
        torch.cuda.manual_seed(rank_seed)

    backend = load_backend(root)
    resolved_environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    official_environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration={}).configuration,
    )
    if not smoke and resolved_environment != official_environment:
        raise ValueError("long unit-task training must use the complete official environment")
    settings = settings.model_copy(update={"environment": resolved_environment})
    contract = _contract(backend, settings)
    source = source_identity(root)
    if not smoke and bool(source["worktree_dirty"]):
        raise RuntimeError("long unit-task training requires a clean source revision")
    initialization = _initialization_identity(settings)
    if context.primary and not output_prepared:
        _prepare_output(settings, root)
    context.barrier()

    start_update = 1
    checkpoint_metadata: dict[str, object] | None = None
    initialization_metadata: dict[str, object] | None = None
    if settings.resume_checkpoint is None:
        source_actor_raw: Mapping[str, object]
        if settings.initial_task_checkpoint is None:
            if settings.initial_actor is None:
                raise ValueError("unit-task actor-only initialization is absent")
            model, source_actor_raw = initialize_task_model(
                settings.initial_actor,
                contract,
                settings.model,
                device,
            )
        else:
            model, initialization_metadata = load_task_checkpoint(
                settings.initial_task_checkpoint,
                contract,
                device,
                include_optimizer=settings.initial_optimizer == "import",
            )
            source_actor_value = initialization_metadata.get("source_actor_identity")
            if not isinstance(source_actor_value, Mapping):
                raise ValueError(
                    "unit-task initialization checkpoint lacks its source actor identity"
                )
            source_actor_raw = source_actor_value
            _validate_task_architecture(model, contract, settings)
        source_actor = _validate_source_actor(source_actor_raw, settings)
    else:
        model, checkpoint_metadata = load_task_checkpoint(
            settings.resume_checkpoint,
            contract,
            device,
        )
        resumed_source_actor = checkpoint_metadata.get("source_actor_identity")
        if not isinstance(resumed_source_actor, Mapping):
            raise ValueError("unit-task checkpoint lacks its source actor identity")
        source_actor = _validate_source_actor(resumed_source_actor, settings)
        update = checkpoint_metadata.get("update")
        if not isinstance(update, int) or isinstance(update, bool) or update >= settings.updates:
            raise ValueError("unit-task checkpoint cannot resume this run")
        start_update = update + 1

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=settings.optimization.learning_rate,
        weight_decay=settings.optimization.weight_decay,
        fused=device.type == "cuda",
    )
    if settings.resume_checkpoint is None and settings.initial_optimizer == "import":
        if initialization_metadata is None:
            raise ValueError("unit-task optimizer import lacks checkpoint metadata")
        initialized_config = initialization_metadata.get("resolved_config")
        if not isinstance(initialized_config, Mapping):
            raise ValueError("unit-task optimizer checkpoint lacks its resolved profile")
        current_config = settings.model_dump(mode="json")
        for field in (
            "model",
            "objective",
            "opponents",
            "opponent_weights",
            "paired_seats",
        ):
            if initialized_config.get(field) != current_config[field]:
                raise ValueError(f"unit-task optimizer checkpoint changed the {field} profile")
        initialized_optimization = initialized_config.get("optimization")
        current_optimization = current_config["optimization"]
        if not isinstance(initialized_optimization, Mapping) or not isinstance(
            current_optimization, Mapping
        ):
            raise ValueError("unit-task optimizer checkpoint lacks optimization settings")
        initialized_optimizer_profile = dict(initialized_optimization)
        current_optimizer_profile = dict(current_optimization)
        for field in (
            "episodes_per_minibatch",
            "episodes_per_microbatch",
            "learning_rate",
        ):
            initialized_optimizer_profile.pop(field, None)
            current_optimizer_profile.pop(field, None)
        if initialized_optimizer_profile != current_optimizer_profile:
            raise ValueError("unit-task optimizer checkpoint changed optimizer semantics")
        optimizer_state = initialization_metadata.get("optimizer_state")
        if not isinstance(optimizer_state, Mapping):
            raise ValueError("unit-task initialization checkpoint lacks optimizer state")
        optimizer.load_state_dict(dict(optimizer_state))
        initialized_learning_rate = initialized_optimization.get("learning_rate")
        if not isinstance(initialized_learning_rate, int | float) or isinstance(
            initialized_learning_rate, bool
        ):
            raise ValueError("unit-task optimizer checkpoint lacks its learning rate")
        if float(initialized_learning_rate) != settings.optimization.learning_rate:
            initialization["optimizer_overrides"] = {
                "learning_rate": {
                    "from": float(initialized_learning_rate),
                    "to": settings.optimization.learning_rate,
                }
            }
        _configure_optimizer_runtime(
            optimizer,
            device,
            learning_rate=settings.optimization.learning_rate,
        )
    training_model: nn.Module = model
    if context.enabled:
        if device.type != "cuda" or device.index is None:
            raise ValueError("distributed unit-task CUDA device is invalid")
        training_model = DistributedDataParallel(
            model,
            device_ids=[device.index],
            output_device=device.index,
            broadcast_buffers=False,
            find_unused_parameters=False,
            gradient_as_bucket_view=True,
            static_graph=True,
        )
    local_batch_games = local_value(
        settings.rollout.batch_games,
        context.world_size,
        "task rollout batch_games",
    )
    local_cpu_workers = local_value(
        settings.rollout.cpu_workers,
        context.world_size,
        "task rollout cpu_workers",
    )
    local_actor_streams = local_value(
        settings.rollout.actor_streams,
        context.world_size,
        "task rollout actor_streams",
    )
    collector = TaskRolloutCollector(
        backend,
        model,
        contract,
        root,
        settings.public_agent_manifest,
        resolved_environment,
        settings.opponent_weights,
        device,
        batch_games=local_batch_games,
        cpu_workers=local_cpu_workers,
        actor_streams=local_actor_streams,
        sampling_seed=settings.seed + 4,
        act_timeout_seconds=settings.act_timeout_seconds,
        remaining_overage_seconds=settings.remaining_overage_seconds,
        initial_actor=settings.initial_actor,
        rank=context.rank,
        world_size=context.world_size,
    )
    native_module = cast(Mapping[str, object], backend.identity["native_module"])
    artifact_identities: dict[str, object] = {
        "public_agent_manifest": {
            "path": str(settings.public_agent_manifest),
            "sha256": sha256_file(settings.public_agent_manifest),
        },
        "native_module": dict(native_module),
        "native_task_contract": _contract_identity(contract),
        "opponents": collector.opponent_identities,
        "named_incumbent": incumbent_identity(settings.incumbent),
        "initialization": initialization,
    }
    profile_config = settings.model_dump(mode="json")
    checkpoint_config = dict(profile_config)
    checkpoint_config["resume_checkpoint"] = None
    if checkpoint_metadata is not None:
        if checkpoint_metadata.get("resolved_config") != checkpoint_config:
            raise ValueError("unit-task resume profile differs from its checkpoint")
        if checkpoint_metadata.get("opponent_identities") != artifact_identities:
            raise ValueError("unit-task resume artifacts differ from its checkpoint")
        if checkpoint_metadata.get("source_identity") != source:
            raise ValueError("unit-task resume source tree differs from its checkpoint")
        optimizer_state = checkpoint_metadata.get("optimizer_state")
        if not isinstance(optimizer_state, Mapping):
            raise ValueError("unit-task checkpoint lacks optimizer state")
        optimizer.load_state_dict(dict(optimizer_state))
        _configure_optimizer_runtime(optimizer, device)
        _restore_worker_rng_state(
            checkpoint_metadata.get("rng_state"),
            context,
            randomizer,
            device,
        )

    resolved_path = settings.output_dir / "resolved-settings.json"
    if settings.resume_checkpoint is None and context.primary:
        resolved_path.write_text(
            json.dumps(
                {
                    "schema_version": "unit-task-training-settings-v1",
                    "unit_task_rl": profile_config,
                    "resolved_environment": resolved_environment,
                    "official_environment": resolved_environment == official_environment,
                    "source": source,
                    "source_actor": source_actor,
                    "initialization": initialization,
                    "artifacts": artifact_identities,
                    "decision_surface": "complete official-rule terminal W/D/L",
                    "cash_role": "diagnostic only",
                },
                indent=2,
                sort_keys=True,
                default=str,
            ),
            encoding="utf-8",
        )
    elif settings.resume_checkpoint is not None and context.primary and not resolved_path.is_file():
        raise FileNotFoundError("unit-task resumed run lacks resolved settings")
    context.barrier()

    store = (
        TaskCheckpointStore(settings.output_dir, settings.checkpoint) if context.primary else None
    )
    if settings.resume_checkpoint is None:
        initial_rng_state = _capture_worker_rng_state(context, randomizer, device)
        if store is not None:
            store.publish(
                0,
                model,
                optimizer,
                final=False,
                contract=contract,
                source_actor_identity=source_actor,
                resolved_config=checkpoint_config,
                opponent_identities=artifact_identities,
                source_identity=source,
                rng_state=initial_rng_state,
            )
        context.barrier()

    codec = cast(Mapping[str, object], backend.action_codec_spec())
    has_quantity = torch.as_tensor(
        np.asarray(codec["has_quantity"], dtype=np.bool_),
        dtype=torch.bool,
        device=device,
    )
    seed_count = (
        min(2, settings.rollout.seeds_per_update) if smoke else settings.rollout.seeds_per_update
    )
    if seed_count % context.world_size:
        raise ValueError("smoke seed count must divide across training devices")
    local_episode_count = 2 * seed_count // context.world_size
    if local_episode_count % settings.optimization.episodes_per_minibatch:
        raise ValueError("smoke seed count does not divide into PPO minibatches")
    final_update = min(settings.updates, start_update if smoke else settings.updates)
    latest: dict[str, object] | None = None
    training_started = time.perf_counter()
    metrics_path = settings.output_dir / "metrics.jsonl"
    for update in range(start_update, final_update + 1):
        first_seed = settings.rollout_seed_start + (update - 1) * settings.rollout.seeds_per_update
        seeds = tuple(range(first_seed, first_seed + seed_count))
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        rollout_started = time.perf_counter()
        rollout = collector.collect(seeds, update=update, sample=True)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        rollout_seconds = time.perf_counter() - rollout_started
        episode_sizes = [_episode_bytes(episode) for episode in rollout.episodes]
        host_bytes = sum(episode_sizes)
        maximum_minibatch_bytes = sum(
            sorted(episode_sizes, reverse=True)[: settings.optimization.episodes_per_minibatch]
        )
        memory_error: str | None = None
        if host_bytes > int(settings.rollout.host_memory_limit_gib * 1024**3 / context.world_size):
            memory_error = "unit-task rollout exceeds configured host memory"
        if device.type == "cuda":
            free_gpu, total_gpu = torch.cuda.mem_get_info(device)
            if free_gpu < int(total_gpu * (1.0 - settings.rollout.gpu_memory_fraction)):
                memory_error = (
                    "unit-task persistent rollout graphs exceed the configured pre-PPO GPU fraction"
                )
            if 2 * maximum_minibatch_bytes > int(free_gpu * settings.rollout.gpu_memory_fraction):
                memory_error = "unit-task PPO batch exceeds configured free GPU fraction"
        memory_errors = context.all_gather(memory_error)
        if any(value is not None for value in memory_errors):
            raise MemoryError(next(value for value in memory_errors if value is not None))
        local_outcome_rows = [
            (
                episode.trajectory.opponent_id,
                episode.trajectory.seed,
                episode.trajectory.seat,
                episode.trajectory.outcome,
                episode.trajectory.terminal_cash,
                episode.trajectory.opponent_cash,
            )
            for episode in rollout.episodes
        ]
        rollout_payloads = context.all_gather(
            {
                "rank": context.rank,
                "device": str(device),
                "seconds": rollout_seconds,
                "maximum_actor_seconds": rollout.maximum_actor_seconds,
                "remaining_overage_seconds": rollout.remaining_overage_seconds,
                "task_decisions": rollout.task_decisions,
                "market_factors": rollout.market_factors,
                "host_bytes": host_bytes,
                "maximum_minibatch_bytes": maximum_minibatch_bytes,
                "phase_seconds": dict(rollout.phase_seconds),
                "outcomes": local_outcome_rows,
            }
        )
        pre_optimization_memory = {
            "pre_optimization_allocated_bytes": (
                torch.cuda.memory_allocated(device) if device.type == "cuda" else 0
            ),
            "pre_optimization_reserved_bytes": (
                torch.cuda.memory_reserved(device) if device.type == "cuda" else 0
            ),
            "pre_optimization_private_pool_reserved_bytes": (
                _private_pool_reserved_bytes(device) if device.type == "cuda" else 0
            ),
        }
        optimization_started = time.perf_counter()
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        optimized = optimize_task_rollout(
            rollout,
            model,
            training_model,
            optimizer,
            settings,
            has_quantity,
            device,
            randomizer,
            context,
            contract,
            smoke=smoke,
        )
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        local_optimization_seconds = time.perf_counter() - optimization_started
        optimization_seconds = context.maximum(local_optimization_seconds)
        worker_memory = context.all_gather(
            {
                "rank": context.rank,
                "device": str(device),
                "peak_gpu_allocated_bytes": (
                    torch.cuda.max_memory_allocated(device) if device.type == "cuda" else 0
                ),
                "peak_gpu_reserved_bytes": (
                    torch.cuda.max_memory_reserved(device) if device.type == "cuda" else 0
                ),
                "optimization_seconds": local_optimization_seconds,
                **pre_optimization_memory,
                "post_optimization_allocated_bytes": (
                    torch.cuda.memory_allocated(device) if device.type == "cuda" else 0
                ),
                "post_optimization_reserved_bytes": (
                    torch.cuda.memory_reserved(device) if device.type == "cuda" else 0
                ),
                "post_optimization_private_pool_reserved_bytes": (
                    _private_pool_reserved_bytes(device) if device.type == "cuda" else 0
                ),
                "cpu_affinity": list(context.cpu_affinity),
            }
        )
        if device.type == "cuda":
            optimized.update(
                peak_gpu_allocated_bytes=sum(
                    _as_int(value["peak_gpu_allocated_bytes"], "peak GPU allocation")
                    for value in worker_memory
                ),
                peak_gpu_reserved_bytes=sum(
                    _as_int(value["peak_gpu_reserved_bytes"], "peak GPU reservation")
                    for value in worker_memory
                ),
            )
        final = update == final_update
        checkpoint = None
        checkpoint_due = (
            final
            or update % settings.checkpoint.rolling_interval == 0
            or update % settings.checkpoint.permanent_interval == 0
        )
        checkpoint_rng = (
            _capture_worker_rng_state(context, randomizer, device) if checkpoint_due else None
        )
        if checkpoint_due and store is not None:
            if checkpoint_rng is None:
                raise RuntimeError("unit-task checkpoint RNG state disappeared")
            checkpoint = store.publish(
                update,
                model,
                optimizer,
                final=final,
                contract=contract,
                source_actor_identity=source_actor,
                resolved_config=checkpoint_config,
                opponent_identities=artifact_identities,
                source_identity=source,
                rng_state=checkpoint_rng,
            )
        context.barrier()
        elapsed_seconds = context.maximum(time.perf_counter() - training_started)
        if context.primary:
            outcome_rows = [
                row
                for payload in rollout_payloads
                for row in cast(list[OutcomeRow], payload["outcomes"])
            ]
            outcome_metrics = _outcome_metrics_from_rows(outcome_rows)
            overall_outcomes = cast(Mapping[str, object], outcome_metrics["overall"])
            physical_games = _as_int(overall_outcomes["games"], "rollout games")
            phase_names = {
                name
                for payload in rollout_payloads
                for name in cast(Mapping[str, float], payload["phase_seconds"])
            }
            phase_seconds = {
                name: sum(
                    float(cast(Mapping[str, float], payload["phase_seconds"]).get(name, 0.0))
                    for payload in rollout_payloads
                )
                for name in sorted(phase_names)
            }
            global_rollout_seconds = max(
                _as_float(payload["seconds"], "rollout seconds") for payload in rollout_payloads
            )
            global_task_decisions = sum(
                _as_int(payload["task_decisions"], "rollout task decisions")
                for payload in rollout_payloads
            )
            latest = {
                "update": update,
                "rollout_seeds": list(seeds),
                "source_commit": source["commit"],
                "outcomes": outcome_metrics,
                "rollout": {
                    "seconds": global_rollout_seconds,
                    "games_per_second": physical_games / max(global_rollout_seconds, 1e-9),
                    "training_episodes_per_second": len(outcome_rows)
                    / max(global_rollout_seconds, 1e-9),
                    "task_decisions_per_second": global_task_decisions
                    / max(global_rollout_seconds, 1e-9),
                    "maximum_actor_seconds": max(
                        _as_float(
                            payload["maximum_actor_seconds"],
                            "maximum actor seconds",
                        )
                        for payload in rollout_payloads
                    ),
                    "remaining_overage_seconds": min(
                        _as_float(
                            payload["remaining_overage_seconds"],
                            "remaining actor overage",
                        )
                        for payload in rollout_payloads
                    ),
                    "task_decisions": global_task_decisions,
                    "market_factors": sum(
                        _as_int(payload["market_factors"], "rollout market factors")
                        for payload in rollout_payloads
                    ),
                    "host_bytes": sum(
                        _as_int(payload["host_bytes"], "rollout host bytes")
                        for payload in rollout_payloads
                    ),
                    "maximum_minibatch_bytes": max(
                        _as_int(
                            payload["maximum_minibatch_bytes"],
                            "maximum minibatch bytes",
                        )
                        for payload in rollout_payloads
                    ),
                    "phase_work_seconds": phase_seconds,
                    "workers": rollout_payloads,
                },
                "optimization": optimized,
                "optimization_seconds": optimization_seconds,
                "system": {
                    "distributed_world_size": context.world_size,
                    "persistent_cuda_graphs": device.type == "cuda",
                    "training_devices": list(settings.training_devices),
                    "rollout_batch_games": settings.rollout.batch_games,
                    "rollout_cpu_workers": settings.rollout.cpu_workers,
                    "rollout_actor_streams": settings.rollout.actor_streams,
                    "workers": worker_memory,
                },
                "checkpoint": checkpoint,
                "elapsed_seconds": elapsed_seconds,
            }
            _append_json(metrics_path, latest)
        # The next collection is sequential, not pipelined.  Drop the complete
        # previous panel before evaluating the next collector call so NumPy can
        # reuse its pages instead of first-touching a second rollout generation.
        del rollout
        # PPO's transient autograd blocks are much larger than the persistent
        # rollout graphs.  Return those unused blocks to the H200 allocator once
        # per complete update so a long next AR panel is not charged against
        # stale PPO cache.  Doing this here avoids the per-microbatch synchronize
        # and allocation churn that previously dominated optimization time.
        if device.type == "cuda":
            torch.cuda.empty_cache()

    collector.release_cuda_graphs()
    context.barrier()
    if not context.primary:
        return {}
    report: dict[str, object] = {
        "schema_version": "unit-task-training-report-v1",
        "status": "smoke_complete" if smoke else "training_complete",
        "source": source,
        "resolved_settings": str(resolved_path),
        "native_task_contract": _contract_identity(contract),
        "initial_actor": source_actor,
        "initialization": initialization,
        "opponents": artifact_identities,
        "selection_seeds_reserved": list(settings.selection_seeds),
        "confirmation_seeds_reserved": list(settings.confirmation_seeds),
        "latest": latest,
        "elapsed_seconds": time.perf_counter() - training_started,
        "promotion_authority": False,
        "distributed": {
            "world_size": context.world_size,
            "training_devices": list(settings.training_devices),
        },
    }
    report_path = settings.output_dir / "training-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return report


def _distributed_worker_entry(
    rank: int,
    settings_payload: dict[str, object],
    repository_root_value: str,
    rendezvous_value: str,
    smoke: bool,
) -> None:
    """Run one synchronized unit-task worker on its assigned H200."""
    settings = TaskRlSettings.model_validate(settings_payload)
    context = initialize_context(
        rank,
        settings.training_devices,
        Path(rendezvous_value),
    )
    try:
        _train_task_tape_worker(
            settings,
            Path(repository_root_value),
            context,
            smoke=smoke,
            output_prepared=True,
        )
    finally:
        destroy_context(context)


def train_task_tape(
    raw_settings: TaskRlSettings,
    repository_root: Path,
    *,
    smoke: bool,
) -> dict[str, object]:
    """Run one single-device or synchronized multi-H200 task PPO lineage."""
    devices = raw_settings.training_devices
    if len(devices) == 1:
        return _train_task_tape_worker(
            raw_settings,
            repository_root,
            single_process_context(torch.device(devices[0])),
            smoke=smoke,
            output_prepared=False,
        )
    if not torch.cuda.is_available():
        raise RuntimeError("distributed unit-task training requested without CUDA")
    available = torch.cuda.device_count()
    for value in devices:
        device = torch.device(value)
        if device.index is None or device.index >= available:
            raise RuntimeError(f"distributed unit-task device is unavailable: {value}")
    resolved = resolve_task_settings(raw_settings, repository_root.resolve())
    _prepare_output(resolved, repository_root.resolve())
    rendezvous = resolved.output_dir / ".ddp-rendezvous"
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
    report_path = resolved.output_dir / "training-report.json"
    value = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("distributed unit-task report is not a mapping")
    return cast(dict[str, object], value)


__all__ = ["resolve_task_settings", "train_task_tape"]
