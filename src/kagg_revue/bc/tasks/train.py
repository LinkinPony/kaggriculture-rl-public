"""End-to-end scratch behavior cloning for the unit-task policy."""

from __future__ import annotations

import json
import os
import random
import shutil
import time
from collections import deque
from collections.abc import Iterator, Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor, nn

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.tasks.config import TaskBcSettings
from kagg_revue.bc.tasks.dataset import (
    Partition,
    ScratchTaskBcBatch,
    TaskBcDataset,
    TaskBcShard,
    collate_scratch_sequences,
)
from kagg_revue.bc.tasks.model import (
    build_actor_architecture,
    initialize_scratch_model,
    scratch_initialization_identity,
)
from kagg_revue.bc.tasks.objective import (
    ScratchOutcomeLoss,
    ScratchPolicyLoss,
    scratch_outcome_loss,
    scratch_policy_loss,
)
from kagg_revue.bc.tasks.prepare import resolve_task_bc_settings
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.rl.tasks.checkpoint import (
    capture_task_rng_state,
    load_task_checkpoint,
    restore_task_rng_state,
    save_task_checkpoint,
)
from kagg_revue.rl.tasks.model import TaskTapeActorCritic, TaskTapeEvaluation

_Stage = Literal["policy", "outcome"]


@dataclass
class _Totals:
    """Mergeable legacy task-head likelihood diagnostics."""

    joint_nll_sum: Tensor | None = None
    entropy_sum: Tensor | None = None
    active_decisions: Tensor | None = None
    stored_decisions: int = 0
    batches: int = 0
    factor_nll_sum: Tensor | None = None
    factor_count: Tensor | None = None

    def update(self, output: Any) -> None:
        """Accumulate one detached task policy output."""
        factor_mask = output.masks.factors.bool()
        active = factor_mask.any(dim=1)
        losses = -output.factor_log_probability.detach()
        joint_nll_sum = losses.sum(dim=1)[active].sum().double()
        entropy_sum = output.entropy.detach()[active].sum().double()
        active_decisions = active.sum()
        factor_nll_sum = losses.masked_fill(~factor_mask, 0.0).sum(dim=0).double()
        factor_count = factor_mask.sum(dim=0)
        if self.factor_nll_sum is None:
            self.joint_nll_sum = joint_nll_sum
            self.entropy_sum = entropy_sum
            self.active_decisions = active_decisions
            self.factor_nll_sum = factor_nll_sum
            self.factor_count = factor_count
        elif self.factor_nll_sum.shape != factor_nll_sum.shape:
            raise ValueError("task BC factor width changed within one partition")
        else:
            if (
                self.joint_nll_sum is None
                or self.entropy_sum is None
                or self.active_decisions is None
                or self.factor_count is None
            ):
                raise RuntimeError("task BC diagnostic accumulators are incomplete")
            self.joint_nll_sum.add_(joint_nll_sum)
            self.entropy_sum.add_(entropy_sum)
            self.active_decisions.add_(active_decisions)
            self.factor_nll_sum.add_(factor_nll_sum)
            self.factor_count.add_(factor_count)
        self.stored_decisions += int(active.numel())
        self.batches += 1

    def summary(self, elapsed: float) -> dict[str, object]:
        """Return conditional NLL without treating it as promotion evidence."""
        if (
            self.joint_nll_sum is None
            or self.entropy_sum is None
            or self.active_decisions is None
            or self.factor_nll_sum is None
            or self.factor_count is None
        ):
            raise RuntimeError("task BC partition produced no diagnostic batches")
        factors = int(self.factor_nll_sum.numel())
        packed = torch.cat(
            (
                self.joint_nll_sum.reshape(1),
                self.entropy_sum.reshape(1),
                self.active_decisions.double().reshape(1),
                self.factor_nll_sum,
                self.factor_count.double(),
            )
        ).cpu()
        joint_nll_sum = float(packed[0])
        entropy_sum = float(packed[1])
        active_decisions = int(packed[2])
        factor_nll_sum = packed[3 : 3 + factors].tolist()
        factor_count = [int(value) for value in packed[3 + factors :].tolist()]
        denominator = max(1, active_decisions)
        return {
            "objective_joint_nll": joint_nll_sum / denominator,
            "mean_entropy": entropy_sum / denominator,
            "active_decisions": active_decisions,
            "stored_decisions": self.stored_decisions,
            "forced_decisions": self.stored_decisions - active_decisions,
            "batches": self.batches,
            "factor_nll": [
                value / max(1, count)
                for value, count in zip(factor_nll_sum, factor_count, strict=True)
            ],
            "factor_counts": factor_count,
            "elapsed_seconds": elapsed,
            "active_decisions_per_second": active_decisions / max(elapsed, 1e-9),
        }


@dataclass
class _StageTotals:
    """Sequence-balanced metrics for one scratch-BC partition."""

    stage: _Stage
    loss_sum: float = 0.0
    first_sum: float = 0.0
    second_sum: float = 0.0
    third_sum: float = 0.0
    sequences: int = 0
    turns: int = 0
    first_count: int = 0
    second_count: int = 0
    third_count: int = 0
    batches: int = 0

    def update(
        self,
        loss: ScratchPolicyLoss | ScratchOutcomeLoss,
        *,
        sequences: int,
        turns: int,
    ) -> None:
        """Accumulate already sequence-balanced batch means."""
        if sequences < 1 or turns < 1:
            raise ValueError("scratch BC metrics need nonempty sequences")
        self.loss_sum += float(loss.total.detach().item()) * sequences
        if self.stage == "policy":
            if not isinstance(loss, ScratchPolicyLoss):
                raise TypeError("policy metrics received an outcome loss")
            self.first_sum += float(loss.task.item()) * sequences
            self.second_sum += float(loss.market_action.item()) * sequences
            self.third_sum += float(loss.market_quantity.item()) * sequences
            self.first_count += loss.task_decisions
            self.second_count += loss.market_decisions
            self.third_count += loss.quantity_decisions
        else:
            if not isinstance(loss, ScratchOutcomeLoss):
                raise TypeError("outcome metrics received a policy loss")
            self.first_sum += float(loss.market.item()) * sequences
            self.second_sum += float(loss.task.item()) * sequences
            self.first_count += loss.market_predictions
            self.second_count += loss.task_predictions
        self.sequences += sequences
        self.turns += turns
        self.batches += 1

    def summary(self, elapsed: float) -> dict[str, object]:
        """Return offline diagnostics on their direct training surfaces."""
        if not self.sequences or not self.batches:
            raise RuntimeError("scratch BC partition produced no batches")
        result: dict[str, object] = {
            "objective_loss": self.loss_sum / self.sequences,
            "sequences": self.sequences,
            "turns": self.turns,
            "batches": self.batches,
            "elapsed_seconds": elapsed,
            "turns_per_second": self.turns / max(elapsed, 1e-9),
        }
        if self.stage == "policy":
            result.update(
                {
                    "task_joint_nll": self.first_sum / self.sequences,
                    "market_action_nll": self.second_sum / self.sequences,
                    "market_quantity_nll": self.third_sum / self.sequences,
                    "task_decisions": self.first_count,
                    "market_decisions": self.second_count,
                    "market_quantity_decisions": self.third_count,
                }
            )
        else:
            result.update(
                {
                    "market_wdl_nll": self.first_sum / self.sequences,
                    "task_wdl_nll": self.second_sum / self.sequences,
                    "market_predictions": self.first_count,
                    "task_predictions": self.second_count,
                }
            )
        return result


def _autocast(device: torch.device) -> Any:
    return (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )


def _prefetched_arrays(
    dataset: TaskBcDataset,
    shards: Sequence[TaskBcShard],
    *,
    workers: int,
    depth: int,
) -> Iterator[tuple[TaskBcShard, dict[str, NDArray[np.generic]]]]:
    """Load a bounded window of compressed shards concurrently in order."""
    if workers < 1 or depth < workers:
        raise ValueError("task BC prefetch requires depth >= workers >= 1")
    if workers == 1:
        for shard in shards:
            yield shard, dataset.arrays(shard)
        return

    shard_iterator = iter(shards)
    pending: deque[
        tuple[TaskBcShard, Future[dict[str, NDArray[np.generic]]]]
    ] = deque()
    with ThreadPoolExecutor(
        max_workers=workers,
        thread_name_prefix="scratch-task-bc-loader",
    ) as executor:
        for _ in range(min(depth, len(shards))):
            shard = next(shard_iterator)
            pending.append((shard, executor.submit(dataset.arrays, shard)))
        while pending:
            shard, future = pending.popleft()
            arrays = future.result()
            next_shard = next(shard_iterator, None)
            if next_shard is not None:
                pending.append(
                    (next_shard, executor.submit(dataset.arrays, next_shard))
                )
            yield shard, arrays


def _task_outcome_head(model: TaskTapeActorCritic) -> nn.Module:
    """Return the active task policy's critic-owned outcome head."""
    if model.tasks.factorized is not None:
        return model.tasks.factorized.outcome_head
    return model.tasks.outcome_head


def _set_policy_trainable(model: TaskTapeActorCritic) -> list[nn.Parameter]:
    """Open every action-affecting parameter and freeze both outcome heads."""
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    for parameter in model.actor.parameters():
        parameter.requires_grad_(True)
    for parameter in model.tasks.parameters():
        parameter.requires_grad_(True)
    for parameter in model.market.outcome.parameters():
        parameter.requires_grad_(False)
    for parameter in _task_outcome_head(model).parameters():
        parameter.requires_grad_(False)
    return [parameter for parameter in model.parameters() if parameter.requires_grad]


def _set_outcomes_trainable(model: TaskTapeActorCritic) -> list[nn.Parameter]:
    """Freeze the learned policy and open only the two new W/D/L heads."""
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    for parameter in model.market.outcome.parameters():
        parameter.requires_grad_(True)
    for parameter in _task_outcome_head(model).parameters():
        parameter.requires_grad_(True)
    return [parameter for parameter in model.parameters() if parameter.requires_grad]


def _forward(
    model: TaskTapeActorCritic,
    batch: ScratchTaskBcBatch,
    *,
    validate_inputs: bool,
    policy_grad: bool,
) -> TaskTapeEvaluation:
    """Evaluate one complete causal sequence batch under current weights."""
    return cast(
        TaskTapeEvaluation,
        model(
            batch.board,
            batch.units,
            batch.global_features,
            batch.actions,
            batch.quantities,
            batch.phases,
            batch.turn_mask,
            batch.decision_mask,
            batch.skill_ids,
            batch.tasks.inputs,
            batch.tasks.actions,
            batch.tasks.masks,
            batch.task_episode_index,
            batch.task_turn_index,
            economic_state=batch.economic_state,
            validate_inputs=validate_inputs,
            policy_grad=policy_grad,
            compute_market_outcome=not policy_grad,
            checkpoint_task_evaluation=False,
        ),
    )


def _run_partition(
    model: TaskTapeActorCritic,
    dataset: TaskBcDataset,
    partition: Partition,
    settings: TaskBcSettings,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None,
    epoch: int,
    *,
    stage: _Stage,
    validate_batches: bool,
) -> dict[str, object]:
    """Run one full episode/seat partition without truncating actor history."""
    training = optimizer is not None
    if training and stage == "policy":
        model.train()
        model.market.outcome.eval()
        _task_outcome_head(model).eval()
    elif training:
        model.eval()
        model.market.outcome.train()
        _task_outcome_head(model).train()
    else:
        model.eval()
    shards = list(dataset.shards(partition))
    if training:
        stage_offset = 0 if stage == "policy" else 1_000_003
        random.Random(
            settings.optimization.seed + stage_offset + epoch * 1009
        ).shuffle(shards)
    totals = _StageTotals(stage)
    started = time.perf_counter()
    context = nullcontext() if training else torch.inference_mode()
    trainable = (
        [
            parameter
            for group in optimizer.param_groups
            for parameter in group["params"]
        ]
        if optimizer is not None
        else []
    )

    def run_batch(
        arrays: Sequence[dict[str, NDArray[np.generic]]],
    ) -> None:
        batch = collate_scratch_sequences(arrays, device)
        if optimizer is not None:
            optimizer.zero_grad(set_to_none=True)
        with _autocast(device):
            output = _forward(
                model,
                batch,
                validate_inputs=validate_batches and totals.batches == 0,
                policy_grad=stage == "policy",
            )
            loss: ScratchPolicyLoss | ScratchOutcomeLoss = (
                scratch_policy_loss(
                    output,
                    batch,
                    model.actor.architecture,
                    settings.optimization,
                )
                if stage == "policy"
                else scratch_outcome_loss(output, batch)
            )
        if not bool(torch.isfinite(loss.total)):
            raise FloatingPointError(f"scratch BC {stage} loss is not finite")
        if optimizer is not None:
            loss.total.backward()  # type: ignore[no-untyped-call]
            torch.nn.utils.clip_grad_norm_(
                trainable,
                settings.optimization.gradient_clip,
            )
            optimizer.step()
        totals.update(
            loss,
            sequences=len(arrays),
            turns=sum(int(value["board"].shape[0]) for value in arrays),
        )

    with context:
        pending: list[dict[str, NDArray[np.generic]]] = []
        prefetched = _prefetched_arrays(
            dataset,
            shards,
            workers=settings.optimization.loader_workers,
            depth=settings.optimization.prefetch_shards,
        )
        for shard_index, (_shard, arrays) in enumerate(prefetched, start=1):
            pending.append(arrays)
            if len(pending) == settings.optimization.batch_sequences:
                run_batch(pending)
                pending = []
            if shard_index % 50 == 0 or shard_index == len(shards):
                print(
                    json.dumps(
                        {
                            "stage": stage,
                            "partition": partition,
                            "epoch": epoch,
                            "completed_sequences": shard_index,
                            "sequences": len(shards),
                            "elapsed_seconds": time.perf_counter() - started,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
        if pending:
            run_batch(pending)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    return totals.summary(time.perf_counter() - started)


def _alias(source: Path, destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    try:
        os.link(source, temporary)
    except OSError:
        shutil.copy2(source, temporary)
    temporary.replace(destination)


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def _require_manifest_identity(
    model: TaskTapeActorCritic,
    contract: NativeTaskContract,
    dataset: TaskBcDataset,
    action_keys: tuple[str, ...],
    expected_agents: int,
) -> None:
    """Reject stale contexts, architecture drift, and episode split leakage."""
    manifest = dataset.manifest
    if manifest.schema_version != "unit-task-scratch-bc-dataset-v3":
        raise ValueError("scratch BC training requires the raw causal v3 dataset")
    if manifest.source_actor_identity is not None:
        raise ValueError("scratch BC dataset unexpectedly imports an actor artifact")
    initialization = manifest.initialization_contract
    if not isinstance(initialization, Mapping) or (
        initialization.get("kind") != "random"
        or initialization.get("weight_artifact_imported") is not False
        or initialization.get("optimizer_imported") is not False
        or initialization.get("rng_imported") is not False
    ):
        raise ValueError("scratch BC random-initialization contract differs")
    if model.actor.architecture != manifest.actor_architecture:
        raise ValueError("scratch BC actor architecture differs from dataset")
    if model.tasks.architecture != manifest.task_architecture:
        raise ValueError("scratch BC task architecture differs from dataset")
    if action_keys != manifest.action_keys:
        raise ValueError("scratch BC action vocabulary differs from dataset")
    if (
        contract.version != manifest.native_task_abi
        or contract.catalog_fingerprint != manifest.catalog_fingerprint
    ):
        raise ValueError("scratch BC native task ABI differs from dataset")

    episodes: dict[str, list[TaskBcShard]] = {}
    for shard in manifest.shards:
        episodes.setdefault(shard.episode_id, []).append(shard)
    expected_seats = set(range(expected_agents))
    for episode_id, shards in episodes.items():
        if {shard.seat for shard in shards} != expected_seats:
            raise ValueError(f"scratch BC episode lacks every seat: {episode_id}")
        if len({shard.partition for shard in shards}) != 1:
            raise ValueError(f"scratch BC episode crosses partitions: {episode_id}")
        if sum(shard.outcome for shard in shards) != 0:
            raise ValueError(f"scratch BC seat-relative outcomes disagree: {episode_id}")


def _checkpoint(
    path: Path,
    model: TaskTapeActorCritic,
    optimizer: torch.optim.Optimizer,
    *,
    update: int,
    contract: NativeTaskContract,
    initialization: Mapping[str, object],
    resolved_environment: Mapping[str, object],
    settings: TaskBcSettings,
    dataset: TaskBcDataset,
    artifact_bindings: Mapping[str, object],
    source: Mapping[str, object],
    randomizer: random.Random,
    device: torch.device,
) -> dict[str, object]:
    """Persist one provenance-bound scratch model state."""
    return save_task_checkpoint(
        path,
        model,
        optimizer,
        update=update,
        contract=contract,
        source_actor_identity=initialization,
        resolved_config={
            "environment": dict(resolved_environment),
            "unit_task_bc": settings.model_dump(mode="json"),
            "dataset_id": dataset.manifest.dataset_id,
            "initialization": dict(initialization),
        },
        opponent_identities=artifact_bindings,
        source_identity=source,
        rng_state=capture_task_rng_state(randomizer, device),
    )


def train_task_bc(
    raw_settings: TaskBcSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Initialize all weights randomly, fit policy, then calibrate W/D/L heads."""
    root = repository_root.resolve()
    settings = resolve_task_bc_settings(raw_settings, root)
    report_path = settings.output_dir / "training-report.json"
    resolved_path = settings.output_dir / "resolved-settings.json"
    checkpoints = settings.output_dir / "checkpoints"
    resume_path = settings.resume_policy_checkpoint
    if report_path.exists() or resolved_path.exists():
        raise FileExistsError("scratch BC training outputs already exist")
    if resume_path is None and checkpoints.exists():
        raise FileExistsError("scratch BC checkpoint directory already exists")
    if resume_path is not None and (
        not checkpoints.is_dir() or not resume_path.is_file()
    ):
        raise FileNotFoundError("scratch BC policy continuation checkpoint is absent")
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    dataset_manifest_path = settings.dataset_dir / "manifest.json"
    dataset = TaskBcDataset(dataset_manifest_path)
    backend = load_backend(root)
    resolved_environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    if resolved_environment != dataset.manifest.environment:
        raise ValueError("scratch BC training environment differs from dataset")
    device = torch.device(settings.optimization.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA scratch BC training was requested but is unavailable")
    torch.set_num_threads(settings.optimization.cpu_threads)
    torch.set_float32_matmul_precision("high")
    random.seed(settings.optimization.seed)
    np.random.seed(settings.optimization.seed)
    torch.manual_seed(settings.optimization.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(settings.optimization.seed)
    contract = NativeTaskContract.from_spec(
        cast(
            Mapping[str, object],
            backend.unit_task_spec(
                resolved_environment,
                settings.abi.unit_limit,
                settings.abi.maximum_quantity,
            ),
        )
    )
    actor_architecture, action_keys = build_actor_architecture(
        backend,
        resolved_environment,
        settings.abi.unit_limit,
        settings.actor,
    )
    resume_metadata: dict[str, object] | None = None
    if resume_path is None:
        model = initialize_scratch_model(
            actor_architecture,
            contract,
            settings.model,
            device,
        )
        initialization = scratch_initialization_identity(
            backend,
            actor_architecture,
            action_keys,
            settings.optimization.seed,
            model,
        )
        start_policy_epoch = 0
    else:
        model, resume_metadata = load_task_checkpoint(
            resume_path,
            contract,
            device,
            include_optimizer=True,
        )
        raw_initialization = resume_metadata.get("source_actor_identity")
        if not isinstance(raw_initialization, Mapping):
            raise ValueError("scratch BC continuation lacks initialization identity")
        initialization = dict(raw_initialization)
        if (
            initialization.get("kind") != "random_from_seed"
            or initialization.get("seed") != settings.optimization.seed
            or initialization.get("weight_artifact_imported") is not False
        ):
            raise ValueError("scratch BC continuation was not initialized from scratch")
        update = resume_metadata.get("update")
        if not isinstance(update, int) or isinstance(update, bool):
            raise ValueError("scratch BC continuation lacks a policy epoch")
        start_policy_epoch = update
        if not 1 <= start_policy_epoch < settings.optimization.epochs:
            raise ValueError("scratch BC continuation lies outside the epoch budget")
        prior_config = resume_metadata.get("resolved_config")
        if (
            not isinstance(prior_config, Mapping)
            or prior_config.get("dataset_id") != dataset.manifest.dataset_id
        ):
            raise ValueError("scratch BC continuation uses a different dataset")
    _require_manifest_identity(
        model,
        contract,
        dataset,
        action_keys,
        settings.source.contract.agents,
    )
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    checkpoints.mkdir(parents=True, exist_ok=resume_path is not None)
    resolved: dict[str, object] = {
        "unit_task_bc": settings.model_dump(mode="json"),
        "environment": resolved_environment,
        "initialization": initialization,
        "dataset": {
            "path": str(dataset_manifest_path),
            "sha256": sha256_file(dataset_manifest_path),
            "dataset_id": dataset.manifest.dataset_id,
        },
    }
    _write_json(resolved_path, resolved)
    source = source_identity(root)
    randomizer = random.Random(settings.optimization.seed)
    continuation: dict[str, object] | None = None
    if resume_path is not None and resume_metadata is not None:
        restore_task_rng_state(
            resume_metadata.get("rng_state"),
            randomizer,
            device,
        )
        continuation = {
            "checkpoint": {
                "path": str(resume_path),
                "sha256": sha256_file(resume_path),
                "size_bytes": resume_path.stat().st_size,
            },
            "completed_policy_epochs": start_policy_epoch,
            "optimizer_restored": True,
            "rng_restored": True,
        }
    artifact_bindings: dict[str, object] = {
        "native_module": cast(dict[str, object], backend.identity["native_module"]),
        "bc_dataset": cast(dict[str, object], resolved["dataset"]),
    }

    policy_parameters = _set_policy_trainable(model)
    if not policy_parameters:
        raise RuntimeError("scratch BC policy phase has no trainable parameters")
    policy_optimizer = torch.optim.AdamW(
        policy_parameters,
        lr=settings.optimization.learning_rate,
        weight_decay=settings.optimization.weight_decay,
    )
    if resume_metadata is not None:
        optimizer_state = resume_metadata.get("optimizer_state")
        if not isinstance(optimizer_state, Mapping):
            raise ValueError("scratch BC continuation lacks optimizer state")
        policy_optimizer.load_state_dict(cast(dict[str, Any], optimizer_state))
    initial_policy_validation = _run_partition(
        model,
        dataset,
        "validation",
        settings,
        device,
        None,
        start_policy_epoch,
        stage="policy",
        validate_batches=True,
    )
    policy_history: list[dict[str, object]] = []
    best_policy_loss = (
        float(cast(float, initial_policy_validation["objective_loss"]))
        if resume_path is not None
        else float("inf")
    )
    best_policy_epoch = start_policy_epoch
    if resume_path is not None:
        _alias(resume_path, checkpoints / "policy-best.pt")
    policy_stale_epochs = 0
    policy_stop_reason = "maximum_epochs"
    for epoch in range(start_policy_epoch + 1, settings.optimization.epochs + 1):
        training = _run_partition(
            model,
            dataset,
            "train",
            settings,
            device,
            policy_optimizer,
            epoch,
            stage="policy",
            validate_batches=start_policy_epoch == 0 and epoch == 1,
        )
        validation = _run_partition(
            model,
            dataset,
            "validation",
            settings,
            device,
            None,
            epoch,
            stage="policy",
            validate_batches=False,
        )
        checkpoint_path = checkpoints / f"policy-epoch-{epoch:04d}.pt"
        checkpoint = _checkpoint(
            checkpoint_path,
            model,
            policy_optimizer,
            update=epoch,
            contract=contract,
            initialization=initialization,
            resolved_environment=resolved_environment,
            settings=settings,
            dataset=dataset,
            artifact_bindings=artifact_bindings,
            source=source,
            randomizer=randomizer,
            device=device,
        )
        validation_loss = float(cast(float, validation["objective_loss"]))
        previous_best = best_policy_loss
        improved = validation_loss < previous_best
        relative_improvement = (
            (previous_best - validation_loss) / max(abs(previous_best), 1e-12)
            if np.isfinite(previous_best)
            else float("inf")
        )
        if improved:
            best_policy_loss = validation_loss
            best_policy_epoch = epoch
            _alias(checkpoint_path, checkpoints / "policy-best.pt")
        meaningful = (
            relative_improvement
            >= settings.optimization.early_stopping_minimum_relative_improvement
        )
        policy_stale_epochs = 0 if meaningful else policy_stale_epochs + 1
        _alias(checkpoint_path, checkpoints / "latest.pt")
        row = {
            "epoch": epoch,
            "training": training,
            "validation": validation,
            "checkpoint": checkpoint,
            "best": improved,
            "relative_improvement": relative_improvement,
            "early_stopping_stale_epochs": policy_stale_epochs,
        }
        policy_history.append(row)
        print(json.dumps({"policy": row}, sort_keys=True, default=str), flush=True)
        if (
            policy_stale_epochs
            >= settings.optimization.policy_early_stopping_patience
        ):
            policy_stop_reason = "validation_plateau"
            break
    if not best_policy_epoch:
        raise RuntimeError("scratch BC policy phase produced no checkpoint")

    model, _policy_metadata = load_task_checkpoint(
        checkpoints / "policy-best.pt",
        contract,
        device,
        include_optimizer=False,
    )
    outcome_parameters = _set_outcomes_trainable(model)
    if not outcome_parameters:
        raise RuntimeError("scratch BC outcome phase has no trainable parameters")
    outcome_optimizer = torch.optim.AdamW(
        outcome_parameters,
        lr=settings.optimization.outcome_learning_rate,
        weight_decay=settings.optimization.weight_decay,
    )
    initial_outcome_validation = _run_partition(
        model,
        dataset,
        "validation",
        settings,
        device,
        None,
        0,
        stage="outcome",
        validate_batches=False,
    )
    initial_outcome_path = checkpoints / "outcome-epoch-0000.pt"
    _checkpoint(
        initial_outcome_path,
        model,
        outcome_optimizer,
        update=settings.optimization.epochs,
        contract=contract,
        initialization=initialization,
        resolved_environment=resolved_environment,
        settings=settings,
        dataset=dataset,
        artifact_bindings=artifact_bindings,
        source=source,
        randomizer=randomizer,
        device=device,
    )
    _alias(initial_outcome_path, checkpoints / "best.pt")
    _alias(initial_outcome_path, checkpoints / "latest.pt")
    best_outcome_loss = float(
        cast(float, initial_outcome_validation["objective_loss"])
    )
    best_outcome_epoch = 0
    outcome_history: list[dict[str, object]] = []
    outcome_stale_epochs = 0
    outcome_stop_reason = "maximum_epochs"
    for epoch in range(1, settings.optimization.outcome_epochs + 1):
        training = _run_partition(
            model,
            dataset,
            "train",
            settings,
            device,
            outcome_optimizer,
            epoch,
            stage="outcome",
            validate_batches=False,
        )
        validation = _run_partition(
            model,
            dataset,
            "validation",
            settings,
            device,
            None,
            epoch,
            stage="outcome",
            validate_batches=False,
        )
        checkpoint_path = checkpoints / f"outcome-epoch-{epoch:04d}.pt"
        checkpoint = _checkpoint(
            checkpoint_path,
            model,
            outcome_optimizer,
            update=settings.optimization.epochs + epoch,
            contract=contract,
            initialization=initialization,
            resolved_environment=resolved_environment,
            settings=settings,
            dataset=dataset,
            artifact_bindings=artifact_bindings,
            source=source,
            randomizer=randomizer,
            device=device,
        )
        validation_loss = float(cast(float, validation["objective_loss"]))
        previous_best = best_outcome_loss
        improved = validation_loss < previous_best
        relative_improvement = (
            (previous_best - validation_loss) / max(abs(previous_best), 1e-12)
        )
        if improved:
            best_outcome_loss = validation_loss
            best_outcome_epoch = epoch
            _alias(checkpoint_path, checkpoints / "best.pt")
        meaningful = (
            relative_improvement
            >= settings.optimization.early_stopping_minimum_relative_improvement
        )
        outcome_stale_epochs = 0 if meaningful else outcome_stale_epochs + 1
        _alias(checkpoint_path, checkpoints / "latest.pt")
        row = {
            "epoch": epoch,
            "training": training,
            "validation": validation,
            "checkpoint": checkpoint,
            "best": improved,
            "relative_improvement": relative_improvement,
            "early_stopping_stale_epochs": outcome_stale_epochs,
        }
        outcome_history.append(row)
        print(json.dumps({"outcome": row}, sort_keys=True, default=str), flush=True)
        if (
            outcome_stale_epochs
            >= settings.optimization.outcome_early_stopping_patience
        ):
            outcome_stop_reason = "validation_plateau"
            break

    best_model, _best_metadata = load_task_checkpoint(
        checkpoints / "best.pt",
        contract,
        device,
        include_optimizer=False,
    )
    for parameter in best_model.parameters():
        parameter.requires_grad_(False)
    test_policy = _run_partition(
        best_model,
        dataset,
        "test",
        settings,
        device,
        None,
        best_policy_epoch,
        stage="policy",
        validate_batches=True,
    )
    test_outcome = _run_partition(
        best_model,
        dataset,
        "test",
        settings,
        device,
        None,
        best_outcome_epoch,
        stage="outcome",
        validate_batches=False,
    )
    best_checkpoint = checkpoints / "best.pt"
    policy_best_checkpoint = checkpoints / "policy-best.pt"
    report: dict[str, object] = {
        "schema_version": "unit-task-scratch-bc-training-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "training_complete",
        "promotion_authority": False,
        "reason": (
            "offline likelihood selects only a BC artifact; deployment requires "
            "complete official-rule paired matches"
        ),
        "objective": {
            "policy": (
                "episode/seat-balanced task exact-mask joint NLL plus direct market "
                "action and exact-quantity NLL"
            ),
            "outcome": (
                "episode/seat-balanced terminal W/D/L cross-entropy with the learned "
                "policy frozen"
            ),
        },
        "actor_update": True,
        "scheduled_sampling": False,
        "initialization": initialization,
        "continuation": continuation,
        "source": source,
        "dataset": resolved["dataset"],
        "native_task_abi": contract.version,
        "catalog_fingerprint": contract.catalog_fingerprint,
        "initial_validation": {
            "policy": initial_policy_validation,
            "outcome_after_policy_selection": initial_outcome_validation,
        },
        "stopping": {
            "minimum_relative_improvement": (
                settings.optimization.early_stopping_minimum_relative_improvement
            ),
            "policy": {
                "reason": policy_stop_reason,
                "patience": settings.optimization.policy_early_stopping_patience,
                "start_epoch": start_policy_epoch,
                "completed_epoch": (
                    cast(int, policy_history[-1]["epoch"])
                    if policy_history
                    else start_policy_epoch
                ),
            },
            "outcome": {
                "reason": outcome_stop_reason,
                "patience": settings.optimization.outcome_early_stopping_patience,
                "completed_epoch": (
                    cast(int, outcome_history[-1]["epoch"])
                    if outcome_history
                    else 0
                ),
            },
        },
        "policy_epochs": policy_history,
        "outcome_epochs": outcome_history,
        "best": {
            "policy_epoch": best_policy_epoch,
            "policy_validation_loss": best_policy_loss,
            "outcome_epoch": best_outcome_epoch,
            "outcome_validation_loss": best_outcome_loss,
            "policy_checkpoint": {
                "path": str(policy_best_checkpoint),
                "sha256": sha256_file(policy_best_checkpoint),
                "size_bytes": policy_best_checkpoint.stat().st_size,
            },
            "checkpoint": {
                "path": str(best_checkpoint),
                "sha256": sha256_file(best_checkpoint),
                "size_bytes": best_checkpoint.stat().st_size,
            },
        },
        "test": {"policy": test_policy, "outcome": test_outcome},
        "peak_gpu_memory_bytes": (
            torch.cuda.max_memory_allocated(device) if device.type == "cuda" else 0
        ),
        "resolved_settings": {
            "path": str(resolved_path),
            "sha256": sha256_file(resolved_path),
        },
    }
    _write_json(report_path, report)
    return report


__all__ = ["train_task_bc"]
