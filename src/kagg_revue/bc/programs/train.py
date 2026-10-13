"""End-to-end behavior cloning for the conditional-program mainline."""

from __future__ import annotations

import json
import math
import os
import random
import shutil
import time
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import numpy as np
import torch
from torch import Tensor, nn
from torch import distributed as dist
from torch.nn import functional
from torch.nn.parallel import DistributedDataParallel

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.programs.config import ProgramBcSettings
from kagg_revue.bc.programs.dataset import (
    Partition,
    ProgramBcDataset,
    ProgramBcShard,
)
from kagg_revue.bc.programs.prepare import resolve_program_bc_settings
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.model import parameter_count
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.rl.outcome import outcome_labels
from kagg_revue.rl.programs.checkpoint import (
    capture_program_rng_state,
    load_program_checkpoint,
    save_program_checkpoint,
)
from kagg_revue.rl.programs.data import ProgramEpisode, collate_program_episodes
from kagg_revue.rl.programs.initialization import initialize_program_model
from kagg_revue.rl.programs.model import ProgramActorCritic


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, default=str), encoding="utf-8")
    temporary.replace(path)


def _alias(source: Path, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    try:
        os.link(source, temporary)
    except OSError:
        shutil.copy2(source, temporary)
    temporary.replace(destination)


def _prefetched_episodes(
    dataset: ProgramBcDataset,
    shards: Sequence[ProgramBcShard],
    *,
    workers: int,
    depth: int,
) -> Iterator[ProgramEpisode]:
    """Load and decompress bounded episode shards ahead of the GPU."""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        pending: list[Future[ProgramEpisode]] = []
        iterator = iter(shards)
        for _ in range(min(depth, len(shards))):
            pending.append(executor.submit(dataset.episode, next(iterator)))
        while pending:
            future = pending.pop(0)
            yield future.result()
            try:
                shard = next(iterator)
            except StopIteration:
                continue
            pending.append(executor.submit(dataset.episode, shard))


def _episode_means(values: Tensor, episode_index: Tensor, episodes: int) -> Tensor:
    """Reduce turn-level values without weighting longer programs more heavily."""
    return torch.stack(
        [values[episode_index == index].mean() for index in range(episodes)]
    )


def _episode_sums(values: Tensor, episode_index: Tensor, episodes: int) -> Tensor:
    """Preserve exact factor totals for each episode."""
    return torch.stack(
        [values[episode_index == index].sum() for index in range(episodes)]
    )


def _run_partition(
    model: ProgramActorCritic,
    dataset: ProgramBcDataset,
    partition: Partition,
    settings: ProgramBcSettings,
    contract: NativeProgramContract,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    epoch: int,
    *,
    forward_model: nn.Module | None = None,
    rank: int = 0,
    world_size: int = 1,
) -> dict[str, object]:
    training = optimizer is not None
    evaluated_model = model if forward_model is None else forward_model
    evaluated_model.train(training)
    shards = list(dataset.shards(partition))
    if training:
        random.Random(settings.optimization.seed + epoch).shuffle(shards)
    global_sequences = len(shards)
    local_batch_sequences = settings.optimization.batch_sequences
    if world_size > 1:
        if settings.optimization.batch_sequences % world_size:
            raise ValueError("program BC global batch must divide across DDP ranks")
        local_batch_sequences //= world_size
        local_shards: list[ProgramBcShard] = []
        for offset in range(0, len(shards), settings.optimization.batch_sequences):
            global_batch = shards[
                offset : offset + settings.optimization.batch_sequences
            ]
            if len(global_batch) % world_size:
                raise ValueError(
                    f"program BC {partition} tail cannot divide across DDP ranks"
                )
            local_shards.extend(global_batch[rank::world_size])
        shards = local_shards
    started = time.perf_counter()
    metric_sums = torch.zeros(5, dtype=torch.float64, device=device)
    group_metric_sums: dict[str, Tensor] = {}
    group_counts: Counter[str] = Counter()
    group_turns: Counter[str] = Counter()
    group_program_decisions: Counter[str] = Counter()
    group_batches: Counter[str] = Counter()
    sequences = 0
    turns = 0
    program_decisions = 0
    stochastic_factors = 0
    batches = 0
    context = nullcontext() if training else torch.inference_mode()

    def run_batch(episodes: list[ProgramEpisode], *, validate: bool) -> None:
        nonlocal sequences, turns, program_decisions, stochastic_factors, batches
        if optimizer is not None:
            optimizer.zero_grad(set_to_none=True)
        batch = collate_program_episodes(
            episodes,
            contract,
            model.actor.architecture.model_width,
            device,
            validate=validate,
        )
        autocast = (
            torch.autocast(device_type="cuda", dtype=torch.bfloat16)
            if device.type == "cuda"
            else nullcontext()
        )
        with autocast:
            output = evaluated_model(
                batch.board,
                batch.units,
                batch.global_features,
                batch.actions,
                batch.quantities,
                batch.turn_mask,
                batch.decision_mask,
                batch.program_inputs,
                batch.program_actions,
                batch.program_masks,
                batch.program_episode_index,
                batch.program_turn_index,
                economic_state=batch.economic_state,
                validate_inputs=validate,
            ).programs
            policy_values = _episode_means(
                -output.joint_log_probability.float(),
                batch.program_episode_index,
                len(episodes),
            )
            policy = policy_values.mean()
            labels = outcome_labels(batch.outcomes)[batch.program_episode_index]
            outcome_values = functional.cross_entropy(
                output.outcome_logits.float(), labels, reduction="none"
            )
            outcome_episode_values = _episode_means(
                outcome_values,
                batch.program_episode_index,
                len(episodes),
            )
            outcome = outcome_episode_values.mean()
            entropy_values = _episode_means(
                output.normalized_entropy.float(),
                batch.program_episode_index,
                len(episodes),
            )
            factor_values = _episode_sums(
                output.factor_counts.float(),
                batch.program_episode_index,
                len(episodes),
            )
            total_values = (
                policy_values
                + settings.optimization.outcome_loss_weight * outcome_episode_values
            )
            total = policy + settings.optimization.outcome_loss_weight * outcome
        if not bool(torch.isfinite(total)):
            raise FloatingPointError("program BC loss is not finite")
        if optimizer is not None:
            total.backward()  # type: ignore[no-untyped-call]
            torch.nn.utils.clip_grad_norm_(model.parameters(), settings.optimization.gradient_clip)
            optimizer.step()
        count = len(episodes)
        metric_sums.add_(
            torch.stack(
                (
                    policy.detach(),
                    outcome.detach(),
                    total.detach(),
                    entropy_values.detach().mean(),
                    factor_values.detach().sum(),
                )
            ).double()
            * torch.tensor(
                [count, count, count, count, 1],
                dtype=torch.float64,
                device=device,
            )
        )
        for group in sorted(
            {episode.source_group for episode in episodes if episode.source_group is not None}
        ):
            indices = torch.tensor(
                [index for index, episode in enumerate(episodes) if episode.source_group == group],
                dtype=torch.long,
                device=device,
            )
            if group not in group_metric_sums:
                group_metric_sums[group] = torch.zeros(
                    5, dtype=torch.float64, device=device
                )
            group_metric_sums[group].add_(
                torch.stack(
                    (
                        policy_values[indices].detach().sum(),
                        outcome_episode_values[indices].detach().sum(),
                        total_values[indices].detach().sum(),
                        entropy_values[indices].detach().sum(),
                        factor_values[indices].detach().sum(),
                    )
                ).double()
            )
            group_count = int(indices.numel())
            group_counts[group] += group_count
            group_turns[group] += sum(
                episode.turn_count for episode in episodes if episode.source_group == group
            )
            group_program_decisions[group] += sum(
                int(np.asarray(episode.program_decision_counts).sum())
                for episode in episodes
                if episode.source_group == group
            )
            group_batches[group] += 1
        sequences += count
        turns += sum(episode.turn_count for episode in episodes)
        program_decisions += sum(
            int(np.asarray(episode.program_decision_counts).sum()) for episode in episodes
        )
        batches += 1

    with context:
        pending: list[ProgramEpisode] = []
        for completed, episode in enumerate(
            _prefetched_episodes(
                dataset,
                shards,
                workers=settings.optimization.loader_workers,
                depth=settings.optimization.prefetch_shards,
            ),
            start=1,
        ):
            pending.append(episode)
            if len(pending) == local_batch_sequences:
                run_batch(pending, validate=batches == 0)
                pending = []
            if rank == 0 and (completed % 100 == 0 or completed == len(shards)):
                print(
                    json.dumps(
                        {
                            "partition": partition,
                            "epoch": epoch,
                            "completed_sequences": min(
                                completed * world_size, global_sequences
                            ),
                            "sequences": global_sequences,
                            "elapsed_seconds": time.perf_counter() - started,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
        if pending:
            run_batch(pending, validate=batches == 0)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elapsed = time.perf_counter() - started
    if not sequences or not batches:
        raise RuntimeError(f"program BC {partition} partition produced no batches")
    if world_size > 1:
        dist.all_reduce(metric_sums)
        counts = torch.tensor(
            [sequences, turns, program_decisions],
            dtype=torch.int64,
            device=device,
        )
        dist.all_reduce(counts)
        sequences, turns, program_decisions = (
            int(value) for value in counts.cpu().tolist()
        )
        elapsed_value = torch.tensor(elapsed, dtype=torch.float64, device=device)
        dist.all_reduce(elapsed_value, op=dist.ReduceOp.MAX)
        elapsed = float(elapsed_value.item())

        gathered_names: list[object] = [None] * world_size
        dist.all_gather_object(gathered_names, tuple(sorted(group_metric_sums)))
        group_names = sorted(
            {
                str(group)
                for rank_names in gathered_names
                for group in cast(tuple[str, ...], rank_names)
            }
        )
        for group in group_names:
            group_metrics = group_metric_sums.get(
                group, torch.zeros(5, dtype=torch.float64, device=device)
            )
            dist.all_reduce(group_metrics)
            group_metric_sums[group] = group_metrics
            group_values = torch.tensor(
                [
                    group_counts[group],
                    group_turns[group],
                    group_program_decisions[group],
                    group_batches[group],
                ],
                dtype=torch.int64,
                device=device,
            )
            dist.all_reduce(group_values)
            (
                group_counts[group],
                group_turns[group],
                group_program_decisions[group],
                group_batches[group],
            ) = (int(value) for value in group_values.cpu().tolist())
    values = metric_sums.cpu().tolist()
    stochastic_factors = int(values[4])
    result: dict[str, object] = {
        "objective_nll": values[0] / sequences,
        "terminal_wdl_nll": values[1] / sequences,
        "total_loss": values[2] / sequences,
        "normalized_entropy": values[3] / sequences,
        "sequences": sequences,
        "turns": turns,
        "program_decisions": program_decisions,
        "stochastic_factors": stochastic_factors,
        "batches": batches,
        "elapsed_seconds": elapsed,
        "turns_per_second": turns / max(elapsed, 1e-9),
        "program_decisions_per_second": program_decisions / max(elapsed, 1e-9),
    }
    if group_metric_sums:
        result["source_groups"] = {
            group: {
                "objective_nll": group_metric_sums[group].cpu().tolist()[0]
                / group_counts[group],
                "terminal_wdl_nll": group_metric_sums[group].cpu().tolist()[1]
                / group_counts[group],
                "total_loss": group_metric_sums[group].cpu().tolist()[2]
                / group_counts[group],
                "normalized_entropy": group_metric_sums[group].cpu().tolist()[3]
                / group_counts[group],
                "sequences": group_counts[group],
                "turns": group_turns[group],
                "program_decisions": group_program_decisions[group],
                "stochastic_factors": int(
                    group_metric_sums[group].cpu().tolist()[4]
                ),
                "batches": group_batches[group],
            }
            for group in sorted(group_metric_sums)
        }
    return result


def _require_dataset_identity(
    model: ProgramActorCritic,
    dataset: ProgramBcDataset,
    contract: NativeProgramContract,
    actor_identity: Mapping[str, object],
) -> None:
    manifest = dataset.manifest
    if model.actor.architecture != manifest.actor_architecture:
        raise ValueError("program BC actor architecture differs from its dataset")
    if model.programs.architecture != manifest.program_architecture:
        raise ValueError("program BC language architecture differs from its dataset")
    if contract.version != manifest.native_program_abi:
        raise ValueError("program BC native ABI differs from its dataset")
    for name in ("sha256", "actor_encoder_version", "derived_fact_version"):
        if actor_identity.get(name) != manifest.source_actor_identity.get(name):
            raise ValueError(f"program BC source actor {name} differs from its dataset")
    actor_action_keys = actor_identity.get("action_keys")
    manifest_action_keys = manifest.source_actor_identity.get("action_keys")
    if (
        not isinstance(actor_action_keys, list | tuple)
        or not isinstance(manifest_action_keys, list | tuple)
        or tuple(actor_action_keys) != tuple(manifest_action_keys)
    ):
        raise ValueError("program BC source actor action_keys differs from its dataset")


def _initialize_model(
    settings: ProgramBcSettings,
    contract: NativeProgramContract,
    device: torch.device,
) -> tuple[ProgramActorCritic, dict[str, object]]:
    """Initialize from the actor or one identity-bound correction checkpoint."""
    if settings.initial_checkpoint is None:
        return initialize_program_model(
            settings.initial_actor,
            contract,
            settings.model,
            device,
            random_actor=settings.initialization == "random",
        )
    model, metadata = load_program_checkpoint(
        settings.initial_checkpoint,
        contract,
        device,
    )
    expected = contract.architecture(
        context_width=model.actor.architecture.model_width,
        model_width=settings.model.model_width,
        feedforward_width=settings.model.feedforward_width,
    )
    source_actor = metadata.get("source_actor_identity")
    if model.programs.architecture != expected or not isinstance(source_actor, Mapping):
        raise ValueError("program BC correction checkpoint differs from its profile")
    if (
        Path(str(source_actor.get("path"))).resolve() != settings.initial_actor.resolve()
        or not settings.initial_actor.is_file()
        or source_actor.get("sha256") != sha256_file(settings.initial_actor)
    ):
        raise ValueError("program BC correction checkpoint source actor changed")
    return model, dict(source_actor)


def train_program_bc(raw_settings: ProgramBcSettings, repository_root: Path) -> dict[str, object]:
    """Train every actor/program parameter for the full requested epoch budget."""
    root = repository_root.resolve()
    settings = resolve_program_bc_settings(raw_settings, root)
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    rank = int(os.environ.get("RANK", "0"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    if world_size < 1 or rank < 0 or rank >= world_size:
        raise ValueError("program BC distributed rank environment is invalid")
    requested_device = torch.device(settings.optimization.device)
    distributed = world_size > 1
    if distributed:
        if requested_device.type != "cuda" or not torch.cuda.is_available():
            raise RuntimeError("distributed program BC requires CUDA")
        if local_rank < 0 or local_rank >= torch.cuda.device_count():
            raise ValueError("program BC local rank has no CUDA device")
        device = torch.device("cuda", local_rank)
        torch.cuda.set_device(device)
        dist.init_process_group(backend="nccl")
    else:
        device = requested_device
    report_path = settings.output_dir / "training-report.json"
    resolved_path = settings.output_dir / "resolved-settings.json"
    metrics_path = settings.output_dir / "metrics.jsonl"
    checkpoints = settings.output_dir / "checkpoints"
    if rank == 0:
        if report_path.exists() or resolved_path.exists() or metrics_path.exists():
            raise FileExistsError("program BC training outputs already exist")
        if checkpoints.exists():
            raise FileExistsError("program BC checkpoint directory already exists")
        settings.output_dir.mkdir(parents=True, exist_ok=True)
    if distributed:
        dist.barrier()
    dataset_path = settings.dataset_dir / "manifest.json"
    dataset = ProgramBcDataset(dataset_path)
    backend = load_backend(root)
    environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    if environment != dataset.manifest.environment:
        raise ValueError("program BC training environment differs from its dataset")
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA program BC training was requested but unavailable")
    torch.set_num_threads(settings.optimization.cpu_threads)
    torch.set_float32_matmul_precision("high")
    random.seed(settings.optimization.seed)
    np.random.seed(settings.optimization.seed)
    torch.manual_seed(settings.optimization.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(settings.optimization.seed)
    randomizer = random.Random(settings.optimization.seed)
    contract = NativeProgramContract.from_spec(
        cast(
            Mapping[str, object],
            backend.conditional_program_spec(environment, settings.abi.unit_limit),
        )
    )
    model, actor_identity = _initialize_model(settings, contract, device)
    _require_dataset_identity(model, dataset, contract, actor_identity)
    training_model: nn.Module = model
    if distributed:
        training_model = DistributedDataParallel(
            model,
            device_ids=[device.index],
            output_device=device.index,
            broadcast_buffers=False,
            static_graph=True,
        )
        torch.manual_seed(settings.optimization.seed + rank)
        torch.cuda.manual_seed(settings.optimization.seed + rank)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=settings.optimization.learning_rate,
        weight_decay=settings.optimization.weight_decay,
        fused=device.type == "cuda",
    )
    source = source_identity(root)
    resolved = {
        "conditional_program_bc": settings.model_dump(mode="json"),
        "environment": environment,
        "dataset": {
            "path": str(dataset_path),
            "sha256": dataset.manifest_sha256,
            "dataset_id": dataset.manifest.dataset_id,
        },
        "source_actor_identity": actor_identity,
        "distributed": {
            "world_size": world_size,
            "backend": "nccl" if distributed else None,
        },
        "initial_program_checkpoint": (
            {
                "path": str(settings.initial_checkpoint),
                "sha256": sha256_file(settings.initial_checkpoint),
                "size_bytes": settings.initial_checkpoint.stat().st_size,
            }
            if settings.initial_checkpoint is not None
            else None
        ),
    }
    if rank == 0:
        _write_json(resolved_path, resolved)
        _write_json(
            settings.output_dir / "run-status.json",
            {
                "status": "running",
                "started_at": datetime.now(UTC).isoformat(),
                "epoch": 0,
                "world_size": world_size,
            },
        )
        checkpoints.mkdir()
    if distributed:
        dist.barrier()
    artifact_bindings = {
        "bc_dataset": cast(dict[str, object], resolved["dataset"]),
        "native_module": cast(dict[str, object], backend.identity["native_module"]),
    }
    best_epoch = 0
    best_objective = math.inf
    history: list[dict[str, object]] = []
    total_started = time.perf_counter()
    for epoch in range(1, settings.optimization.epochs + 1):
        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)
        epoch_started = time.perf_counter()
        training = _run_partition(
            model,
            dataset,
            "train",
            settings,
            contract,
            device,
            optimizer,
            epoch,
            forward_model=training_model,
            rank=rank,
            world_size=world_size,
        )
        validation = _run_partition(
            model,
            dataset,
            "validation",
            settings,
            contract,
            device,
            None,
            epoch,
            rank=rank,
            world_size=world_size,
        )
        checkpoint_path = checkpoints / f"epoch-{epoch:04d}.pt"
        objective = float(cast(float, validation["objective_nll"]))
        selected = objective < best_objective
        if selected:
            best_epoch = epoch
            best_objective = objective
        peak_allocated = (
            torch.cuda.max_memory_allocated(device) if device.type == "cuda" else 0
        )
        peak_reserved = (
            torch.cuda.max_memory_reserved(device) if device.type == "cuda" else 0
        )
        if distributed:
            peaks = torch.tensor(
                [peak_allocated, peak_reserved], dtype=torch.int64, device=device
            )
            dist.all_reduce(peaks, op=dist.ReduceOp.MAX)
            peak_allocated, peak_reserved = (
                int(value) for value in peaks.cpu().tolist()
            )
        system = {
            "elapsed_seconds": time.perf_counter() - epoch_started,
            "total_elapsed_seconds": time.perf_counter() - total_started,
            "cuda_peak_allocated_bytes": peak_allocated,
            "cuda_peak_reserved_bytes": peak_reserved,
        }
        if rank == 0:
            checkpoint = save_program_checkpoint(
                checkpoint_path,
                model,
                optimizer,
                update=epoch,
                contract=contract,
                source_actor_identity=actor_identity,
                resolved_config=resolved,
                opponent_identities=artifact_bindings,
                source_identity=source,
                rng_state=capture_program_rng_state(randomizer, device),
            )
            if selected:
                _alias(checkpoint_path, checkpoints / "best.pt")
            _alias(checkpoint_path, checkpoints / "latest.pt")
            row: dict[str, object] = {
                "epoch": epoch,
                "training": training,
                "validation": validation,
                "system": system,
                "checkpoint": checkpoint,
                "best": selected,
            }
            history.append(row)
            with metrics_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            _write_json(
                settings.output_dir / "run-status.json",
                {
                    "status": "running",
                    "updated_at": datetime.now(UTC).isoformat(),
                    "epoch": epoch,
                    "world_size": world_size,
                },
            )
            print(json.dumps(row, sort_keys=True, default=str), flush=True)
        if distributed:
            dist.barrier()
    if best_epoch < 1:
        raise RuntimeError("program BC training produced no selected checkpoint")
    del training_model
    del optimizer
    del model
    if device.type == "cuda":
        torch.cuda.empty_cache()
    best_model, best_metadata = load_program_checkpoint(
        checkpoints / "best.pt", contract, device
    )
    test = _run_partition(
        best_model,
        dataset,
        "test",
        settings,
        contract,
        device,
        None,
        best_epoch,
        rank=rank,
        world_size=world_size,
    )
    report: dict[str, object] = {
        "schema_version": "conditional-program-bc-training-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "training_complete",
        "purpose": "behavior warm start; no promotion authority",
        "objective": {
            "policy": "episode/seat-balanced exact-mask joint program NLL",
            "outcome": "direct terminal W/D/L cross-entropy",
            "checkpoint_selection": "minimum held-out program NLL",
        },
        "source": source,
        "execution": {
            "device": str(device),
            "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
            "world_size": world_size,
            "devices": (
                [torch.cuda.get_device_name(index) for index in range(world_size)]
                if distributed
                else [str(device)]
            ),
            "parameter_count": parameter_count(best_model),
        },
        "dataset": cast(dict[str, object], resolved["dataset"]),
        "source_actor_identity": actor_identity,
        "training_span": {"initial_epoch": 0, "target_epoch": settings.optimization.epochs},
        "epochs": history,
        "best": {
            "epoch": best_epoch,
            "validation_objective_nll": best_objective,
            "checkpoint": best_metadata["checkpoint_identity"],
        },
        "test": test,
        "metrics": {
            "path": str(metrics_path),
            "sha256": sha256_file(metrics_path),
        },
    }
    if rank == 0:
        _write_json(report_path, report)
        _write_json(
            settings.output_dir / "run-status.json",
            {
                "status": "complete",
                "completed_at": datetime.now(UTC).isoformat(),
                "epoch": settings.optimization.epochs,
                "best_epoch": best_epoch,
                "world_size": world_size,
            },
        )
    if distributed:
        dist.barrier()
        dist.destroy_process_group()
    return report if rank == 0 else {}


__all__ = ["train_program_bc"]
