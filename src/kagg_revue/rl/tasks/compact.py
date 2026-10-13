"""Compact rollout records reconstructed on CUDA for task PPO."""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.tasks.gpu import TaskPlanningState
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    TaskActions,
    TaskCatalog,
    TaskDecisionInputs,
    conditional_masks,
    factorized_conditional_masks,
    selected_arrivals,
)
from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.policy.tasks.runtime import CompactTaskTrace

IntArray = NDArray[np.int64]
FloatArray = NDArray[np.float32]
ShortArray = NDArray[np.int16]
BoolArray = NDArray[np.bool_]

_SNAPSHOT_VECTORS = (
    "replan_mask",
    "optional_mask",
    "replan_reasons",
    "tape_sizes",
)


def _freeze(
    value: object,
    dtype: np.dtype[Any],
    *,
    copy: bool,
) -> NDArray[Any]:
    result = (
        np.array(value, dtype=dtype, order="C", copy=True)
        if copy
        else np.asarray(value, dtype=dtype, order="C")
    )
    result.flags.writeable = False
    return result


@dataclass(frozen=True)
class CompactTaskTurnRecord:
    """One turn boundary plus its lightweight sampled task suffix."""

    turn_index: int
    hour: int
    day: int
    days: int
    unit_count: int
    history_count: int
    successful_tasks: int
    failed_tasks: int
    forced_ends: int
    prefix_fields: ShortArray
    replan_mask: BoolArray
    optional_mask: BoolArray
    replan_reasons: ShortArray
    tape_sizes: ShortArray
    actions: ShortArray
    old_joint_log_probability: FloatArray
    old_values: FloatArray
    _copy_arrays: InitVar[bool] = True

    def __post_init__(self, _copy_arrays: bool) -> None:
        """Freeze exact native snapshot fields and sampled statistics."""
        if not _copy_arrays:
            return
        if self.turn_index < 0 or self.history_count < 0:
            raise ValueError("compact task turn indices must be non-negative")
        prefix = cast(
            ShortArray,
            _freeze(
                self.prefix_fields,
                np.dtype(np.int16),
                copy=_copy_arrays,
            ),
        )
        replan = cast(
            BoolArray,
            _freeze(
                self.replan_mask,
                np.dtype(np.bool_),
                copy=_copy_arrays,
            ),
        )
        optional = cast(
            BoolArray,
            _freeze(
                self.optional_mask,
                np.dtype(np.bool_),
                copy=_copy_arrays,
            ),
        )
        reasons = cast(
            ShortArray,
            _freeze(
                self.replan_reasons,
                np.dtype(np.int16),
                copy=_copy_arrays,
            ),
        )
        tape_sizes = cast(
            ShortArray,
            _freeze(
                self.tape_sizes,
                np.dtype(np.int16),
                copy=_copy_arrays,
            ),
        )
        actions = cast(
            ShortArray,
            _freeze(
                self.actions,
                np.dtype(np.int16),
                copy=_copy_arrays,
            ),
        )
        old_log = cast(
            FloatArray,
            _freeze(
                self.old_joint_log_probability,
                np.dtype(np.float32),
                copy=_copy_arrays,
            ),
        )
        old_values = cast(
            FloatArray,
            _freeze(
                self.old_values,
                np.dtype(np.float32),
                copy=_copy_arrays,
            ),
        )
        decisions = actions.shape[0] if actions.ndim == 2 else -1
        if (
            prefix.shape != (self.history_count, 9)
            or replan.ndim != 1
            or optional.shape != replan.shape
            or reasons.shape != replan.shape
            or tape_sizes.shape != replan.shape
            or actions.shape != (decisions, 5)
            or old_log.shape != (decisions,)
            or old_values.shape != (decisions,)
            or decisions < 1
        ):
            raise ValueError("compact task turn tensors do not follow the task ABI")
        if not replan.any():
            raise ValueError("compact task turn lacks an active replanning unit")
        if not np.isfinite(old_log).all() or not np.isfinite(old_values).all():
            raise ValueError("compact task turn contains non-finite behavior values")
        for name, value in (
            ("prefix_fields", prefix),
            ("replan_mask", replan),
            ("optional_mask", optional),
            ("replan_reasons", reasons),
            ("tape_sizes", tape_sizes),
            ("actions", actions),
            ("old_joint_log_probability", old_log),
            ("old_values", old_values),
        ):
            object.__setattr__(self, name, value)

    @property
    def decision_count(self) -> int:
        """Return the number of sampled AR decisions at this boundary."""
        return int(self.actions.shape[0])


def compact_turn_records(
    trace: CompactTaskTrace,
    turn_index: int,
) -> tuple[CompactTaskTurnRecord | None, ...]:
    """Split one fixed-batch device tape into per-episode compact records."""
    raw = trace.snapshot
    batch = trace.counts.shape[0]
    if trace.actions.shape[:1] != (batch,):
        raise ValueError("compact task actions and counts are misaligned")
    snapshot = {
        name: np.asarray(raw[name])
        for name in (
            "history_counts",
            "prefix_fields",
            "hour",
            "day",
            "days",
            "unit_counts",
            "successful_tasks",
            "failed_tasks",
            "forced_ends",
            "replan_mask",
            "optional_mask",
            "replan_reasons",
            "tape_sizes",
        )
    }
    for value in (
        *snapshot.values(),
        trace.actions,
        trace.old_joint_log_probability,
        trace.old_values,
    ):
        value.flags.writeable = False
    result: list[CompactTaskTurnRecord | None] = []
    for row in range(batch):
        count = int(trace.counts[row])
        if count == 0:
            result.append(None)
            continue
        history_count = int(snapshot["history_counts"][row])
        prefix = snapshot["prefix_fields"][row, :history_count]
        result.append(
            CompactTaskTurnRecord(
                turn_index=turn_index,
                hour=int(snapshot["hour"][row]),
                day=int(snapshot["day"][row]),
                days=int(snapshot["days"][row]),
                unit_count=int(snapshot["unit_counts"][row]),
                history_count=history_count,
                successful_tasks=int(snapshot["successful_tasks"][row]),
                failed_tasks=int(snapshot["failed_tasks"][row]),
                forced_ends=int(snapshot["forced_ends"][row]),
                prefix_fields=prefix,
                replan_mask=snapshot["replan_mask"][row],
                optional_mask=snapshot["optional_mask"][row],
                replan_reasons=snapshot["replan_reasons"][row],
                tape_sizes=snapshot["tape_sizes"][row],
                actions=trace.actions[row, :count],
                old_joint_log_probability=(trace.old_joint_log_probability[row, :count]),
                old_values=trace.old_values[row, :count],
                _copy_arrays=False,
            )
        )
    return tuple(result)


def _snapshot_batch(
    records: list[CompactTaskTurnRecord],
    contract: NativeTaskContract,
) -> dict[str, NDArray[Any]]:
    """Pad variable history prefixes into the fixed native snapshot ABI."""
    batch = len(records)
    raw: dict[str, NDArray[Any]] = {
        "requires_decision": np.ones(batch, dtype=np.uint8),
    }
    scalar_names = {
        "hour": "hour",
        "day": "day",
        "days": "days",
        "unit_counts": "unit_count",
        "history_counts": "history_count",
        "successful_tasks": "successful_tasks",
        "failed_tasks": "failed_tasks",
        "forced_ends": "forced_ends",
    }
    for target, source in scalar_names.items():
        dtype = np.int32 if target.endswith("tasks") or target == "forced_ends" else np.int16
        raw[target] = np.asarray([getattr(record, source) for record in records], dtype=dtype)
    prefix = np.zeros(
        (batch, contract.prefix_capacity, contract.task_field_count),
        dtype=np.int16,
    )
    for row, record in enumerate(records):
        if record.history_count > contract.prefix_capacity:
            raise ValueError("compact task history exceeds the native capacity")
        prefix[row, : record.history_count] = record.prefix_fields
    raw["prefix_fields"] = prefix
    for name in _SNAPSHOT_VECTORS:
        raw[name] = np.stack([getattr(record, name) for record in records])
    return raw


def collate_compact_task_records(
    records: list[CompactTaskTurnRecord],
    economic_states: list[NDArray[Any]],
    episode_indices: IntArray,
    *,
    context_width: int,
    contract: NativeTaskContract,
    device: torch.device,
    factorized: bool = False,
    history_window: int = 64,
    catalog: TaskCatalog | None = None,
) -> Any:
    """Replay compact AR tapes in parallel and rebuild exact PPO inputs."""
    if not records or len(economic_states) != len(records):
        raise ValueError("compact task collation requires aligned turn records")
    if episode_indices.shape != (len(records),):
        raise ValueError("compact task episode identities are misaligned")
    raw = _snapshot_batch(records, contract)
    economic = np.stack(economic_states).astype(np.int32, copy=False)
    state = TaskPlanningState.from_native(
        raw,
        torch.as_tensor(economic, dtype=torch.int32, device=device),
        contract,
    )
    task_catalog = contract.catalog.to(device) if catalog is None else catalog
    if any(
        value.device != device
        for value in (
            task_catalog.operations,
            task_catalog.arguments,
            task_catalog.targets,
            task_catalog.requires_quantity,
            task_catalog.operation_turns,
        )
    ):
        raise ValueError("compact task catalog must already reside on the PPO device")
    counts = np.asarray([record.decision_count for record in records], dtype=np.int64)
    maximum = int(counts.max(initial=0))
    context = torch.zeros((len(records), context_width), dtype=torch.float32, device=device)
    input_parts: list[TaskDecisionInputs | FactorizedTaskDecisionInputs] = []
    action_parts: list[Tensor] = []
    old_log_parts: list[Tensor] = []
    old_value_parts: list[Tensor] = []
    episode_parts: list[Tensor] = []
    turn_parts: list[Tensor] = []

    active_batches = [
        np.flatnonzero(counts > decision).astype(np.int64, copy=False)
        for decision in range(maximum)
    ]
    offsets = np.zeros(maximum + 1, dtype=np.int64)
    if maximum:
        offsets[1:] = np.cumsum([active.size for active in active_batches], dtype=np.int64)
    active_rows = np.concatenate(active_batches)
    action_tape = np.concatenate(
        [
            np.stack([records[int(row)].actions[decision] for row in active])
            for decision, active in enumerate(active_batches)
        ]
    )
    old_log_tape = np.concatenate(
        [
            np.asarray(
                [records[int(row)].old_joint_log_probability[decision] for row in active],
                dtype=np.float32,
            )
            for decision, active in enumerate(active_batches)
        ]
    )
    old_value_tape = np.concatenate(
        [
            np.asarray(
                [records[int(row)].old_values[decision] for row in active],
                dtype=np.float32,
            )
            for decision, active in enumerate(active_batches)
        ]
    )
    turn_indices = np.asarray([record.turn_index for record in records], dtype=np.int64)
    episode_tape = np.concatenate([episode_indices[active] for active in active_batches])
    turn_tape = np.concatenate([turn_indices[active] for active in active_batches])

    def upload(value: NDArray[Any], dtype: torch.dtype) -> Tensor:
        host = torch.from_numpy(np.ascontiguousarray(value)).to(dtype=dtype)
        if device.type == "cuda":
            host = host.pin_memory()
        return host.to(device, non_blocking=device.type == "cuda")

    device_rows = upload(active_rows, torch.long)
    device_actions = upload(action_tape, torch.long)
    device_old_log = upload(old_log_tape, torch.float32)
    device_old_values = upload(old_value_tape, torch.float32)
    device_episodes = upload(episode_tape, torch.long)
    device_turns = upload(turn_tape, torch.long)
    for decision in range(maximum):
        start = int(offsets[decision])
        stop = int(offsets[decision + 1])
        rows = device_rows[start:stop]
        inputs = state.inputs(
            rows,
            context,
            task_catalog,
            prefix_length=contract.prefix_capacity,
            factorized=factorized,
            history_window=(history_window if factorized else None),
        )
        action_values = device_actions[start:stop]
        actions = TaskActions(
            mode=action_values[:, 0].contiguous(),
            candidate=action_values[:, 1].contiguous(),
            quantity=action_values[:, 2].contiguous(),
            earliest=action_values[:, 3].contiguous(),
            deadline=action_values[:, 4].contiguous(),
        )
        arrivals = selected_arrivals(inputs, task_catalog, actions).contiguous()
        input_parts.append(inputs)
        action_parts.append(action_values)
        old_log_parts.append(device_old_log[start:stop])
        old_value_parts.append(device_old_values[start:stop])
        episode_parts.append(device_episodes[start:stop])
        turn_parts.append(device_turns[start:stop])
        state.apply(rows, actions, task_catalog, arrivals)

    def combine(name: str, dtype: torch.dtype) -> Tensor:
        return torch.cat([getattr(inputs, name) for inputs in input_parts], dim=0).to(dtype=dtype)

    combined_inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs
    if factorized:
        combined_inputs = FactorizedTaskDecisionInputs(
            context=combine("context", torch.float32),
            root_features=combine("root_features", torch.float32),
            prefix_fields=combine("prefix_fields", torch.long),
            prefix_mask=combine("prefix_mask", torch.bool),
            economic_state=combine("economic_state", torch.int32),
            current_unit=combine("current_unit", torch.long),
            current_x=combine("current_x", torch.long),
            current_y=combine("current_y", torch.long),
            target_counts=combine("target_counts", torch.int32),
            resource_counts=combine("resource_counts", torch.int32),
            mode_mask=combine("mode_mask", torch.bool),
            available_at=combine("available_at", torch.long),
            day_end=combine("day_end", torch.long),
            prefix_length=history_window,
        )
    else:
        combined_inputs = TaskDecisionInputs(
            context=combine("context", torch.float32),
            root_features=combine("root_features", torch.float32),
            prefix_fields=combine("prefix_fields", torch.long),
            prefix_mask=combine("prefix_mask", torch.bool),
            candidate_features=combine("candidate_features", torch.float32),
            candidate_mask=combine("candidate_mask", torch.bool),
            candidate_arrivals=combine("candidate_arrivals", torch.long),
            mode_mask=combine("mode_mask", torch.bool),
            available_at=combine("available_at", torch.long),
            day_end=combine("day_end", torch.long),
            prefix_length=contract.prefix_capacity,
        )
    action_values = torch.cat(action_parts, dim=0)
    actions = TaskActions(
        mode=action_values[:, 0],
        candidate=action_values[:, 1],
        quantity=action_values[:, 2],
        earliest=action_values[:, 3],
        deadline=action_values[:, 4],
    )
    masks = (
        factorized_conditional_masks(
            combined_inputs,
            task_catalog,
            actions,
            maximum_quantity=contract.maximum_quantity,
            time_tokens=contract.time_token_count,
        )
        if isinstance(combined_inputs, FactorizedTaskDecisionInputs)
        else conditional_masks(
            combined_inputs,
            task_catalog,
            actions,
            maximum_quantity=contract.maximum_quantity,
            time_tokens=contract.time_token_count,
        )
    )
    from kagg_revue.rl.tasks.data import TaskDecisionBatch

    return TaskDecisionBatch(
        inputs=combined_inputs,
        actions=actions,
        masks=masks,
        old_joint_log_probability=torch.cat(old_log_parts),
        old_values=torch.cat(old_value_parts),
        episode_index=torch.cat(episode_parts),
        turn_index=torch.cat(turn_parts),
    )


def compact_task_bytes(record: CompactTaskTurnRecord) -> int:
    """Return the exact durable array footprint of one compact turn."""
    return sum(
        int(np.asarray(getattr(record, name)).nbytes)
        for name in (
            "prefix_fields",
            "replan_mask",
            "optional_mask",
            "replan_reasons",
            "tape_sizes",
            "actions",
            "old_joint_log_probability",
            "old_values",
        )
    )


__all__ = [
    "CompactTaskTurnRecord",
    "collate_compact_task_records",
    "compact_task_bytes",
    "compact_turn_records",
]
