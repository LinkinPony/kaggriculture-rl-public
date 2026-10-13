"""Device-side recording for fixed-batch task autoregression."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor

from kagg_revue.policy.tasks.grammar import TaskActions


@triton.jit
def _record_kernel(
    active,
    modes,
    candidates,
    quantities,
    earliest,
    deadlines,
    selections,
    counts,
    MAX_DECISIONS: tl.constexpr,
):
    row = tl.program_id(0)
    enabled = tl.load(active + row) != 0
    count = tl.load(counts + row)
    valid = enabled & (count < MAX_DECISIONS)
    base = (row * MAX_DECISIONS + count) * 5
    values = (
        tl.load(modes + row),
        tl.load(candidates + row),
        tl.load(quantities + row),
        tl.load(earliest + row),
        tl.load(deadlines + row),
    )
    for field in tl.static_range(0, 5):
        tl.store(selections + base + field, values[field], mask=valid)
    tl.store(counts + row, count + 1, mask=valid)


@triton.jit
def _rollout_record_kernel(
    active,
    modes,
    candidates,
    quantities,
    earliest,
    deadlines,
    joint_log_probability,
    values,
    selections,
    counts,
    stored_log_probability,
    stored_values,
    MAX_DECISIONS: tl.constexpr,
):
    row = tl.program_id(0)
    enabled = tl.load(active + row) != 0
    count = tl.load(counts + row)
    valid = enabled & (count < MAX_DECISIONS)
    base = (row * MAX_DECISIONS + count) * 5
    action_values = (
        tl.load(modes + row),
        tl.load(candidates + row),
        tl.load(quantities + row),
        tl.load(earliest + row),
        tl.load(deadlines + row),
    )
    for field in tl.static_range(0, 5):
        tl.store(selections + base + field, action_values[field], mask=valid)
    statistic = row * MAX_DECISIONS + count
    tl.store(
        stored_log_probability + statistic,
        tl.load(joint_log_probability + row),
        mask=valid,
    )
    tl.store(
        stored_values + statistic,
        tl.load(values + row),
        mask=valid,
    )
    tl.store(counts + row, count + 1, mask=valid)


@triton.jit
def _row_rollout_record_kernel(
    rows,
    active,
    modes,
    candidates,
    quantities,
    earliest,
    deadlines,
    joint_log_probability,
    values,
    selections,
    counts,
    stored_log_probability,
    stored_values,
    MAX_DECISIONS: tl.constexpr,
):
    local = tl.program_id(0)
    row = tl.load(rows + local)
    enabled = tl.load(active + row) != 0
    count = tl.load(counts + row)
    valid = enabled & (count < MAX_DECISIONS)
    base = (row * MAX_DECISIONS + count) * 5
    action_values = (
        tl.load(modes + local),
        tl.load(candidates + local),
        tl.load(quantities + local),
        tl.load(earliest + local),
        tl.load(deadlines + local),
    )
    for field in tl.static_range(0, 5):
        tl.store(selections + base + field, action_values[field], mask=valid)
    statistic = row * MAX_DECISIONS + count
    tl.store(
        stored_log_probability + statistic,
        tl.load(joint_log_probability + local),
        mask=valid,
    )
    tl.store(
        stored_values + statistic,
        tl.load(values + local),
        mask=valid,
    )
    tl.store(counts + row, count + 1, mask=valid)


def record_task_selections(
    active: Tensor,
    actions: TaskActions,
    selections: Tensor,
    counts: Tensor,
) -> None:
    """Append active full-batch actions without synchronizing with the host."""
    batch, maximum_decisions, fields = selections.shape
    action_values = tuple(
        getattr(actions, name) for name in actions.__dataclass_fields__
    )
    if (
        active.device.type != "cuda"
        or active.shape != (batch,)
        or active.dtype != torch.bool
        or not active.is_contiguous()
    ):
        raise ValueError("task selection activity must be a contiguous CUDA mask")
    if fields != 5 or selections.dtype != torch.int16 or not selections.is_contiguous():
        raise ValueError("task selection storage has the wrong fixed layout")
    if counts.shape != (batch,) or counts.dtype != torch.int16 or not counts.is_contiguous():
        raise ValueError("task selection counts have the wrong fixed layout")
    if any(
        value.shape != (batch,)
        or value.device != active.device
        or not value.is_contiguous()
        for value in action_values
    ):
        raise ValueError("task selection actions must be contiguous CUDA vectors")
    if selections.device != active.device or counts.device != active.device:
        raise ValueError("task selection storage must share one CUDA device")
    _record_kernel[(batch,)](
        active,
        actions.mode,
        actions.candidate,
        actions.quantity,
        actions.earliest,
        actions.deadline,
        selections,
        counts,
        MAX_DECISIONS=maximum_decisions,
        num_warps=1,
    )


def record_task_rollout(
    active: Tensor,
    actions: TaskActions,
    joint_log_probability: Tensor,
    values: Tensor,
    selections: Tensor,
    counts: Tensor,
    stored_log_probability: Tensor,
    stored_values: Tensor,
) -> None:
    """Append lightweight behavior values while all task state stays on CUDA."""
    batch, maximum_decisions, fields = selections.shape
    action_values = tuple(
        getattr(actions, name) for name in actions.__dataclass_fields__
    )
    vectors = action_values + (joint_log_probability, values)
    if (
        active.device.type != "cuda"
        or active.shape != (batch,)
        or active.dtype != torch.bool
        or not active.is_contiguous()
    ):
        raise ValueError("task rollout activity must be a contiguous CUDA mask")
    if fields != 5 or selections.dtype != torch.int16 or not selections.is_contiguous():
        raise ValueError("task rollout selections have the wrong fixed layout")
    if counts.shape != (batch,) or counts.dtype != torch.int16 or not counts.is_contiguous():
        raise ValueError("task rollout counts have the wrong fixed layout")
    if (
        stored_log_probability.shape != (batch, maximum_decisions)
        or stored_values.shape != (batch, maximum_decisions)
        or stored_log_probability.dtype != torch.float32
        or stored_values.dtype != torch.float32
        or not stored_log_probability.is_contiguous()
        or not stored_values.is_contiguous()
    ):
        raise ValueError("task rollout statistics have the wrong fixed layout")
    if any(
        value.shape != (batch,)
        or value.device != active.device
        or not value.is_contiguous()
        for value in vectors
    ):
        raise ValueError("task rollout values must be contiguous CUDA vectors")
    if any(
        value.device != active.device
        for value in (
            selections,
            counts,
            stored_log_probability,
            stored_values,
        )
    ):
        raise ValueError("task rollout storage must share one CUDA device")
    _rollout_record_kernel[(batch,)](
        active,
        actions.mode,
        actions.candidate,
        actions.quantity,
        actions.earliest,
        actions.deadline,
        joint_log_probability,
        values,
        selections,
        counts,
        stored_log_probability,
        stored_values,
        MAX_DECISIONS=maximum_decisions,
        num_warps=1,
    )


def record_task_rollout_rows(
    rows: Tensor,
    active: Tensor,
    actions: TaskActions,
    joint_log_probability: Tensor,
    values: Tensor,
    selections: Tensor,
    counts: Tensor,
    stored_log_probability: Tensor,
    stored_values: Tensor,
) -> None:
    """Append one compacted active-row policy batch into global storage."""
    batch, maximum_decisions, fields = selections.shape
    row_count = rows.numel()
    action_values = tuple(
        getattr(actions, name) for name in actions.__dataclass_fields__
    )
    vectors = action_values + (joint_log_probability, values)
    if (
        rows.device.type != "cuda"
        or rows.shape != (row_count,)
        or rows.dtype != torch.long
        or not rows.is_contiguous()
        or active.shape != (batch,)
        or active.dtype != torch.bool
        or not active.is_contiguous()
    ):
        raise ValueError("compacted task rollout rows have the wrong layout")
    if fields != 5 or selections.dtype != torch.int16 or not selections.is_contiguous():
        raise ValueError("task rollout selections have the wrong fixed layout")
    if counts.shape != (batch,) or counts.dtype != torch.int16 or not counts.is_contiguous():
        raise ValueError("task rollout counts have the wrong fixed layout")
    if (
        stored_log_probability.shape != (batch, maximum_decisions)
        or stored_values.shape != (batch, maximum_decisions)
        or stored_log_probability.dtype != torch.float32
        or stored_values.dtype != torch.float32
        or not stored_log_probability.is_contiguous()
        or not stored_values.is_contiguous()
    ):
        raise ValueError("task rollout statistics have the wrong fixed layout")
    if any(
        value.shape != (row_count,)
        or value.device != rows.device
        or not value.is_contiguous()
        for value in vectors
    ):
        raise ValueError("compacted task rollout values must be CUDA vectors")
    if any(
        value.device != rows.device
        for value in (
            active,
            selections,
            counts,
            stored_log_probability,
            stored_values,
        )
    ):
        raise ValueError("compacted task rollout storage must share one device")
    _row_rollout_record_kernel[(row_count,)](
        rows,
        active,
        actions.mode,
        actions.candidate,
        actions.quantity,
        actions.earliest,
        actions.deadline,
        joint_log_probability,
        values,
        selections,
        counts,
        stored_log_probability,
        stored_values,
        MAX_DECISIONS=maximum_decisions,
        num_warps=1,
    )


__all__ = [
    "record_task_rollout",
    "record_task_rollout_rows",
    "record_task_selections",
]
