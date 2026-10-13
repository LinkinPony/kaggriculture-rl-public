"""Compact exact-mask shards for task-head behavior cloning."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import torch
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field
from torch import Tensor

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.tasks.replay import ReplaySequence
from kagg_revue.bc.tasks.translate import TranslatedSequence
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    FactorizedTaskMasks,
    TaskActions,
    TaskConditionalMasks,
    TaskDecisionInputs,
)
from kagg_revue.policy.tasks.schema import TaskTapeArchitecture

Partition = Literal["train", "validation", "test"]


class TaskBcShard(BaseModel):
    """Identity and dimensions of one seat-local compressed sequence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    shard_id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    episode_id: str = Field(min_length=1)
    source_date: str = Field(min_length=1)
    seat: int = Field(ge=0)
    partition: Partition
    turns: int = Field(gt=0)
    stream_decisions: int = Field(gt=0)
    sampled_decisions: int = Field(gt=0)
    market_decisions: int = Field(default=0, ge=0)
    outcome: int = Field(default=0, ge=-1, le=1)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    statistics: dict[str, object]


class TaskBcManifest(BaseModel):
    """Artifact identities needed to replay a task BC dataset safely."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[
        "unit-task-bc-dataset-v1",
        "unit-task-bc-dataset-v2",
        "unit-task-scratch-bc-dataset-v3",
    ]
    dataset_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    generated_at: str = Field(min_length=1)
    source: dict[str, object]
    source_actor_identity: dict[str, object] | None = None
    initialization_contract: dict[str, object] | None = None
    native_backend: dict[str, object]
    native_task_abi: str = Field(min_length=1)
    catalog_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    action_keys: tuple[str, ...] = ()
    actor_architecture: ActorArchitecture
    task_architecture: TaskTapeArchitecture
    environment: dict[str, object]
    translation: dict[str, object]
    selection: dict[str, object]
    partitions: dict[str, tuple[str, ...]]
    shards: tuple[TaskBcShard, ...]


@dataclass(frozen=True)
class TaskBcBatch:
    """One device batch of exact conditional task decisions."""

    inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs
    actions: TaskActions
    masks: TaskConditionalMasks | FactorizedTaskMasks


@dataclass(frozen=True)
class ScratchTaskBcBatch:
    """Whole causal sequences and their seat-local task supervision."""

    board: Tensor
    units: Tensor
    global_features: Tensor
    economic_state: Tensor
    actions: Tensor
    quantities: Tensor
    phases: Tensor
    turn_mask: Tensor
    decision_mask: Tensor
    market_factor_mask: Tensor
    skill_ids: Tensor
    outcomes: Tensor
    tasks: TaskBcBatch
    task_episode_index: Tensor
    task_turn_index: Tensor


_ARRAY_FIELDS = (
    "context",
    "stream_index",
    "turn_index",
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

_FACTORIZED_ARRAY_FIELDS = (
    "context",
    "economic_state",
    "stream_index",
    "turn_index",
    "root_features",
    "prefix_fields",
    "prefix_mask",
    "current_unit",
    "current_x",
    "current_y",
    "target_counts",
    "resource_counts",
    "mode_mask",
    "action",
    "operation_mask",
    "argument_mask",
    "target_mask",
    "quantity_mask",
    "earliest_mask",
    "deadline_mask",
    "factor_mask",
)

_SCRATCH_ACTOR_FIELDS = (
    "board",
    "units",
    "global_features",
    "economic_state",
    "actions",
    "quantities",
    "phases",
    "decision_mask",
    "market_factor_mask",
    "outcome",
)

_SCRATCH_FACTORIZED_ARRAY_FIELDS = (
    *_SCRATCH_ACTOR_FIELDS,
    *(name for name in _FACTORIZED_ARRAY_FIELDS if name not in {"context", "economic_state"}),
)


def save_sequence_shard(
    path: Path,
    sequence: TranslatedSequence,
    replay: ReplaySequence,
    seat: int,
) -> dict[str, object]:
    """Persist one full causal actor sequence plus sampled task decisions."""
    if path.suffix != ".npz" or not sequence.records:
        raise ValueError("task BC sequence shard must be a nonempty .npz")
    if seat != sequence.seat or not 0 <= seat < replay.board.shape[0]:
        raise ValueError("task BC shard seat differs from its replay sequence")
    records = [sample.record for sample in sequence.records]
    turns = replay.turns
    actions = np.asarray(replay.action_tokens[seat], dtype=np.int64)
    quantities = np.asarray(replay.action_quantities[seat], dtype=np.int64)
    decision_mask = np.asarray(replay.decision_mask[seat], dtype=np.bool_)
    phases = np.zeros_like(actions, dtype=np.int8)
    for turn, encoded in enumerate(replay.encoded_actions[seat]):
        phases[turn, encoded.unit_decisions : len(encoded.tokens)] = 1
    market_factor_mask = decision_mask & (phases == 1)
    opponent = 1 - seat
    outcome = int(
        np.sign(float(replay.rewards[seat]) - float(replay.rewards[opponent]))
    )
    arrays: dict[str, NDArray[np.generic]] = {
        "board": np.asarray(replay.board[seat], dtype=np.float16),
        "units": np.asarray(replay.units[seat], dtype=np.float16),
        "global_features": np.asarray(
            replay.global_features[seat], dtype=np.float16
        ),
        "economic_state": np.asarray(
            replay.economic_state[seat], dtype=np.int32
        ),
        "actions": actions,
        "quantities": quantities,
        "phases": phases,
        "decision_mask": decision_mask,
        "market_factor_mask": market_factor_mask,
        "outcome": np.asarray(outcome, dtype=np.int8),
        "stream_index": np.asarray(
            [sample.stream_index for sample in sequence.records], dtype=np.int32
        ),
        "turn_index": np.asarray(
            [record.turn_index for record in records], dtype=np.int16
        ),
        "available_at": np.asarray(
            [record.available_at for record in records], dtype=np.int16
        ),
        "day_end": np.asarray([record.day_end for record in records], dtype=np.int16),
    }
    if sequence.factorized:
        names: tuple[str, ...] = (
            "root_features",
            "prefix_fields",
            "prefix_mask",
            "current_unit",
            "current_x",
            "current_y",
            "target_counts",
            "resource_counts",
            "mode_mask",
            "action",
            "operation_mask",
            "argument_mask",
            "target_mask",
            "quantity_mask",
            "earliest_mask",
            "deadline_mask",
            "factor_mask",
        )
    else:
        names = (
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
    for name in names:
        arrays[name] = np.stack([getattr(record, name) for record in records])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, **cast(dict[str, Any], arrays))
    temporary.replace(path)
    return {
        "turns": turns,
        "stream_decisions": int(cast(int, sequence.statistics["stream_decisions"])),
        "sampled_decisions": len(records),
        "market_decisions": int(market_factor_mask.sum()),
        "outcome": outcome,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def load_sequence_arrays(path: Path) -> dict[str, NDArray[np.generic]]:
    """Load and minimally validate one bounded NPZ sequence."""
    with np.load(path, allow_pickle=False) as archive:
        legacy = {*_ARRAY_FIELDS, "available_at", "day_end"}
        factorized = {*_FACTORIZED_ARRAY_FIELDS, "available_at", "day_end"}
        scratch_fields = {
            *_SCRATCH_FACTORIZED_ARRAY_FIELDS,
            "available_at",
            "day_end",
        }
        fields = set(archive.files)
        if fields == legacy:
            expected = legacy
        elif fields == factorized:
            expected = factorized
        elif fields == scratch_fields:
            expected = scratch_fields
        else:
            raise ValueError(f"task BC shard fields differ: {path}")
        arrays = {name: np.asarray(archive[name]) for name in archive.files}
    records = int(arrays["turn_index"].shape[0])
    scratch = "board" in expected
    turn_fields = (
        set(_SCRATCH_ACTOR_FIELDS) if scratch else {"context", "economic_state"}
    ) & expected
    for name in expected - turn_fields:
        if arrays[name].shape[0] != records:
            raise ValueError(f"task BC shard field {name} has a different row count")
    if scratch:
        turns = arrays["board"].shape[0]
        for name in set(_SCRATCH_ACTOR_FIELDS) - {"outcome"}:
            if arrays[name].shape[0] != turns:
                raise ValueError(f"scratch actor field {name} has a different turn count")
        if arrays["outcome"].shape != () or int(arrays["outcome"]) not in {-1, 0, 1}:
            raise ValueError("scratch BC outcome must be a scalar W/D/L label")
        if not np.array_equal(
            arrays["market_factor_mask"],
            arrays["decision_mask"] & (arrays["phases"] == 1),
        ):
            raise ValueError("scratch BC market factors differ from action phases")
    else:
        if arrays["context"].ndim != 2:
            raise ValueError("task BC context must have shape [turn, width]")
        turns = arrays["context"].shape[0]
    turn_index = np.asarray(arrays["turn_index"], dtype=np.int64)
    if np.any((turn_index < 0) | (turn_index >= turns)):
        raise ValueError("task BC record refers outside its context sequence")
    finite = (
        all(
            np.isfinite(arrays[name]).all()
            for name in ("board", "units", "global_features")
        )
        if scratch
        else np.isfinite(arrays["context"]).all()
    )
    if "candidate_features" in arrays:
        finite = finite and np.isfinite(arrays["candidate_features"]).all()
    if not finite:
        raise ValueError("task BC shard contains NaN or Inf")
    return arrays


def collate_arrays(
    arrays: dict[str, NDArray[np.generic]],
    indices: NDArray[np.int64],
    device: torch.device,
) -> TaskBcBatch:
    """Move selected shard rows and their turn contexts to one device."""
    return collate_array_groups(((arrays, indices),), device)


def collate_array_groups(
    groups: Sequence[
        tuple[dict[str, NDArray[np.generic]], NDArray[np.int64]]
    ],
    device: torch.device,
) -> TaskBcBatch:
    """Combine bounded shard slices into one device batch."""
    if not groups:
        raise ValueError("task BC collation requires at least one shard slice")
    for arrays, indices in groups:
        if indices.ndim != 1 or not indices.size:
            raise ValueError("task BC shard slice must be a nonempty vector")
        records = int(arrays["turn_index"].shape[0])
        if int(indices.min()) < 0 or int(indices.max()) >= records:
            raise IndexError("task BC shard slice lies outside its records")
    factorized = "economic_state" in groups[0][0]
    if any(("economic_state" in arrays) != factorized for arrays, _ in groups):
        raise ValueError("task BC collation cannot mix task input contracts")

    def selected(name: str) -> NDArray[np.generic]:
        values = [arrays[name][indices] for arrays, indices in groups]
        return values[0] if len(values) == 1 else np.concatenate(values)

    contexts: list[NDArray[np.generic]] = []
    for arrays, indices in groups:
        turns = np.asarray(arrays["turn_index"], dtype=np.int64)[indices]
        contexts.append(
            arrays["context"][turns]
            if "context" in arrays
            else np.zeros((len(indices), 1), dtype=np.float32)
        )
    context = contexts[0] if len(contexts) == 1 else np.concatenate(contexts)
    economic_context: NDArray[np.generic] | None = None
    if factorized:
        economic_rows = []
        for arrays, indices in groups:
            turns = np.asarray(arrays["turn_index"], dtype=np.int64)[indices]
            economic_rows.append(arrays["economic_state"][turns])
        economic_context = (
            economic_rows[0]
            if len(economic_rows) == 1
            else np.concatenate(economic_rows)
        )
    input_names = (
        (
            "root_features",
            "prefix_fields",
            "prefix_mask",
            "current_unit",
            "current_x",
            "current_y",
            "target_counts",
            "resource_counts",
            "mode_mask",
            "available_at",
            "day_end",
            "action",
            "operation_mask",
            "argument_mask",
            "target_mask",
            "quantity_mask",
            "earliest_mask",
            "deadline_mask",
            "factor_mask",
        )
        if factorized
        else (
            "root_features",
            "prefix_fields",
            "prefix_mask",
            "candidate_features",
            "candidate_mask",
            "candidate_arrivals",
            "mode_mask",
            "available_at",
            "day_end",
            "action",
            "quantity_mask",
            "earliest_mask",
            "deadline_mask",
            "factor_mask",
        )
    )
    selected_arrays = {
        name: selected(name)
        for name in input_names
    }

    def tensor(name: str, dtype: torch.dtype) -> Tensor:
        return torch.as_tensor(selected_arrays[name], dtype=dtype, device=device)

    action = tensor("action", torch.long)
    prefix_length = int(
        np.count_nonzero(selected_arrays["prefix_mask"], axis=1).max()
    )
    if factorized:
        if economic_context is None:
            raise RuntimeError("factorized task collation lost economic state")
        inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs = (
            FactorizedTaskDecisionInputs(
                context=torch.as_tensor(context, dtype=torch.float32, device=device),
                root_features=tensor("root_features", torch.float32),
                prefix_fields=tensor("prefix_fields", torch.long),
                prefix_mask=tensor("prefix_mask", torch.bool),
                economic_state=torch.as_tensor(
                    economic_context, dtype=torch.int32, device=device
                ),
                current_unit=tensor("current_unit", torch.long),
                current_x=tensor("current_x", torch.long),
                current_y=tensor("current_y", torch.long),
                target_counts=tensor("target_counts", torch.int32),
                resource_counts=tensor("resource_counts", torch.int32),
                mode_mask=tensor("mode_mask", torch.bool),
                available_at=tensor("available_at", torch.long),
                day_end=tensor("day_end", torch.long),
                prefix_length=prefix_length,
            )
        )
        masks: TaskConditionalMasks | FactorizedTaskMasks = FactorizedTaskMasks(
            mode=inputs.mode_mask,
            operation=tensor("operation_mask", torch.bool),
            argument=tensor("argument_mask", torch.bool),
            target=tensor("target_mask", torch.bool),
            quantity=tensor("quantity_mask", torch.bool),
            earliest=tensor("earliest_mask", torch.bool),
            deadline=tensor("deadline_mask", torch.bool),
            factors=tensor("factor_mask", torch.bool),
        )
    else:
        inputs = TaskDecisionInputs(
            context=torch.as_tensor(context, dtype=torch.float32, device=device),
            root_features=tensor("root_features", torch.float32),
            prefix_fields=tensor("prefix_fields", torch.long),
            prefix_mask=tensor("prefix_mask", torch.bool),
            candidate_features=tensor("candidate_features", torch.float32),
            candidate_mask=tensor("candidate_mask", torch.bool),
            candidate_arrivals=tensor("candidate_arrivals", torch.long),
            mode_mask=tensor("mode_mask", torch.bool),
            available_at=tensor("available_at", torch.long),
            day_end=tensor("day_end", torch.long),
            prefix_length=prefix_length,
        )
        masks = TaskConditionalMasks(
            mode=inputs.mode_mask,
            candidate=inputs.candidate_mask,
            quantity=tensor("quantity_mask", torch.bool),
            earliest=tensor("earliest_mask", torch.bool),
            deadline=tensor("deadline_mask", torch.bool),
            factors=tensor("factor_mask", torch.bool),
        )
    return TaskBcBatch(
        inputs=inputs,
        actions=TaskActions(
            mode=action[:, 0],
            candidate=action[:, 1],
            quantity=action[:, 2],
            earliest=action[:, 3],
            deadline=action[:, 4],
        ),
        masks=masks,
    )


def collate_scratch_sequences(
    sequences: Sequence[dict[str, NDArray[np.generic]]],
    device: torch.device,
) -> ScratchTaskBcBatch:
    """Move complete episode-start sequences and every sampled task to a device."""
    if not sequences or any("board" not in arrays for arrays in sequences):
        raise ValueError("scratch BC collation requires causal actor arrays")
    turns = {int(arrays["board"].shape[0]) for arrays in sequences}
    if len(turns) != 1:
        raise ValueError("scratch BC sequences must share the official turn count")
    task_groups: list[
        tuple[dict[str, NDArray[np.generic]], NDArray[np.int64]]
    ] = []
    episode_rows: list[NDArray[np.int64]] = []
    task_turn_rows: list[NDArray[np.int64]] = []
    for episode_index, arrays in enumerate(sequences):
        records = int(arrays["turn_index"].shape[0])
        indices = np.arange(records, dtype=np.int64)
        task_groups.append((arrays, indices))
        episode_rows.append(np.full(records, episode_index, dtype=np.int64))
        task_turn_rows.append(
            np.asarray(arrays["turn_index"], dtype=np.int64)
        )

    def stacked(name: str, dtype: torch.dtype) -> Tensor:
        values = np.stack([arrays[name] for arrays in sequences])
        return torch.as_tensor(values, dtype=dtype, device=device)

    batch = len(sequences)
    turn_count = turns.pop()
    return ScratchTaskBcBatch(
        board=stacked("board", torch.float32),
        units=stacked("units", torch.float32),
        global_features=stacked("global_features", torch.float32),
        economic_state=stacked("economic_state", torch.int32),
        actions=stacked("actions", torch.long),
        quantities=stacked("quantities", torch.long),
        phases=stacked("phases", torch.long),
        turn_mask=torch.ones(
            (batch, turn_count), dtype=torch.bool, device=device
        ),
        decision_mask=stacked("decision_mask", torch.bool),
        market_factor_mask=stacked("market_factor_mask", torch.bool),
        skill_ids=torch.full(
            (batch, turn_count), -1, dtype=torch.long, device=device
        ),
        outcomes=torch.as_tensor(
            [int(arrays["outcome"]) for arrays in sequences],
            dtype=torch.long,
            device=device,
        ),
        tasks=collate_array_groups(task_groups, device),
        task_episode_index=torch.as_tensor(
            np.concatenate(episode_rows), dtype=torch.long, device=device
        ),
        task_turn_index=torch.as_tensor(
            np.concatenate(task_turn_rows), dtype=torch.long, device=device
        ),
    )


class TaskBcDataset:
    """Authenticated collection of independent, episode-grouped task shards."""

    def __init__(self, manifest_path: Path, *, verify_hashes: bool = True) -> None:
        """Load a manifest and reject partition or shard identity drift."""
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.manifest = TaskBcManifest.model_validate(raw)
        self.root = manifest_path.parent
        by_id = {shard.shard_id: shard for shard in self.manifest.shards}
        declared = [value for rows in self.manifest.partitions.values() for value in rows]
        if len(declared) != len(set(declared)) or set(declared) != set(by_id):
            raise ValueError("task BC partitions do not cover shards exactly once")
        self._by_id = by_id
        for shard in self.manifest.shards:
            path = self.root / shard.path
            if not path.is_file() or path.stat().st_size != shard.size_bytes:
                raise FileNotFoundError(f"task BC shard identity differs: {path}")
            if verify_hashes and sha256_file(path) != shard.sha256:
                raise ValueError(f"task BC shard hash differs: {path}")

    def shards(self, partition: Partition) -> tuple[TaskBcShard, ...]:
        """Return manifest-ordered shards in one disjoint split."""
        ids = self.manifest.partitions.get(partition)
        if ids is None or not ids:
            raise ValueError(f"task BC partition is empty: {partition}")
        return tuple(self._by_id[shard_id] for shard_id in ids)

    def arrays(self, shard: TaskBcShard) -> dict[str, NDArray[np.generic]]:
        """Load one authenticated sequence shard."""
        return load_sequence_arrays(self.root / shard.path)


__all__ = [
    "Partition",
    "TaskBcBatch",
    "TaskBcDataset",
    "TaskBcManifest",
    "TaskBcShard",
    "ScratchTaskBcBatch",
    "collate_array_groups",
    "collate_arrays",
    "collate_scratch_sequences",
    "load_sequence_arrays",
    "save_sequence_shard",
]
