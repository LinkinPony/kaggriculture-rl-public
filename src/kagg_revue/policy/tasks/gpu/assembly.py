"""Fused active-row assembly for GPU task-policy inputs."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor


@triton.jit
def _assembly_kernel(
    rows,
    current_units,
    hour,
    day,
    days,
    unit_counts,
    history_counts,
    successful,
    failed,
    forced,
    optional,
    reasons,
    tape_sizes,
    x,
    y,
    available,
    first,
    planning_counts,
    prefix_fields,
    output_root,
    output_prefix,
    output_prefix_mask,
    output_mode_mask,
    output_available,
    output_day_end,
    UNIT_LIMIT: tl.constexpr,
    BOARD_SIZE: tl.constexpr,
    SOURCE_PREFIX_CAPACITY: tl.constexpr,
    OUTPUT_PREFIX_CAPACITY: tl.constexpr,
    TURNS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    local_row = tl.program_id(0)
    block = tl.program_id(1)
    lane = tl.arange(0, BLOCK)
    source_row = tl.load(rows + local_row)
    unit = tl.load(current_units + source_row)
    history_count = tl.load(history_counts + source_row)

    flat = block * BLOCK + lane
    prefix_elements = OUTPUT_PREFIX_CAPACITY * 9
    prefix_valid = flat < prefix_elements
    record = flat // 9
    field = flat - record * 9
    active_records = tl.minimum(history_count, OUTPUT_PREFIX_CAPACITY)
    source_start = tl.maximum(history_count - OUTPUT_PREFIX_CAPACITY, 0)
    source_record = source_start + record
    prefix_value = tl.load(
        prefix_fields + source_row * SOURCE_PREFIX_CAPACITY * 9
        + source_record * 9 + field,
        mask=prefix_valid & (record < active_records),
        other=0,
    )
    tl.store(
        output_prefix + local_row * prefix_elements + flat,
        prefix_value,
        mask=prefix_valid,
    )
    tl.store(
        output_prefix_mask + local_row * OUTPUT_PREFIX_CAPACITY + record,
        record < active_records,
        mask=prefix_valid & (field == 0),
    )


    if block == 0:
        scalar_hour = tl.load(hour + source_row)
        scalar_day = tl.load(day + source_row)
        scalar_days = tl.load(days + source_row)
        scalar_units = tl.load(unit_counts + source_row)
        scalar_successful = tl.load(successful + source_row)
        scalar_failed = tl.load(failed + source_row)
        scalar_forced = tl.load(forced + source_row)
        scalar_x = tl.load(x + source_row)
        scalar_y = tl.load(y + source_row)
        scalar_available = tl.load(available + source_row)
        scalar_first = tl.load(first + source_row) != 0
        planning_count = tl.load(planning_counts + source_row)
        unit_offset = source_row * UNIT_LIMIT + unit
        tape_size = tl.load(tape_sizes + unit_offset)
        reason = tl.load(reasons + unit_offset)
        continue_legal = (
            scalar_first
            & (tl.load(optional + unit_offset) != 0)
            & (tape_size > 0)
        )
        completed = scalar_successful + scalar_failed
        denominator = float(TURNS)
        root = tl.full((BLOCK,), 0.0, tl.float32)
        root = tl.where(lane == 0, scalar_hour / denominator, root)
        root = tl.where(
            lane == 1,
            scalar_day / tl.maximum(scalar_days, 1).to(tl.float32),
            root,
        )
        root = tl.where(
            lane == 2,
            unit / float(max(1, UNIT_LIMIT - 1)),
            root,
        )
        root = tl.where(lane == 3, scalar_units / float(UNIT_LIMIT), root)
        root = tl.where(lane == 4, scalar_x / float(BOARD_SIZE - 1), root)
        root = tl.where(lane == 5, scalar_y / float(BOARD_SIZE - 1), root)
        root = tl.where(lane == 6, scalar_available / denominator, root)
        root = tl.where(
            lane == 7,
            tl.maximum(TURNS - scalar_available, 0) / denominator,
            root,
        )
        root = tl.where(lane == 8, planning_count / denominator, root)
        root = tl.where(lane == 9, tape_size / denominator, root)
        root = tl.where(
            lane == 10,
            history_count / float(SOURCE_PREFIX_CAPACITY),
            root,
        )
        completion_denominator = tl.maximum(completed, 1).to(tl.float32)
        root = tl.where(
            lane == 11,
            scalar_successful / completion_denominator,
            root,
        )
        root = tl.where(
            lane == 12,
            scalar_failed / completion_denominator,
            root,
        )
        root = tl.where(
            lane == 13,
            scalar_forced / completion_denominator,
            root,
        )
        for value in tl.static_range(0, 7):
            root = tl.where(lane == 14 + value, reason == value, root)
        root = tl.where(lane == 21, continue_legal, root)
        root = tl.where(lane == 22, 1.0, root)
        root = tl.where(lane == 23, scalar_first, root)
        tl.store(
            output_root + local_row * 24 + lane,
            root,
            mask=lane < 24,
        )
        tl.store(
            output_mode_mask + local_row * 2 + lane,
            tl.where(lane == 0, continue_legal, True),
            mask=lane < 2,
        )
        tl.store(
            output_available + local_row + lane,
            scalar_available,
            mask=lane == 0,
        )
        tl.store(
            output_day_end + local_row + lane,
            TURNS,
            mask=lane == 0,
        )


def _assemble_decision_inputs_cpu(
    rows: Tensor,
    current_units: Tensor,
    hour: Tensor,
    day: Tensor,
    days: Tensor,
    unit_counts: Tensor,
    history_counts: Tensor,
    successful: Tensor,
    failed: Tensor,
    forced: Tensor,
    optional: Tensor,
    reasons: Tensor,
    tape_sizes: Tensor,
    x: Tensor,
    y: Tensor,
    available: Tensor,
    first: Tensor,
    planning_counts: Tensor,
    prefix_fields: Tensor,
    *,
    unit_limit: int,
    board_size: int,
    prefix_capacity: int,
    source_prefix_capacity: int,
    turns: int,
) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor, Tensor]:
    """Reference assembly used by CPU rollout and compact PPO smoke tests."""
    batch = rows.numel()
    device = rows.device
    source_rows = rows.long()
    units = current_units[source_rows].long()
    counts = history_counts[source_rows].long()
    active_records = counts.clamp(max=prefix_capacity)
    source_start = (counts - prefix_capacity).clamp_min(0)
    offsets = torch.arange(prefix_capacity, device=device)[None]
    source_records = (source_start[:, None] + offsets).clamp(
        max=source_prefix_capacity - 1
    )
    prefix_mask = offsets < active_records[:, None]
    prefix = prefix_fields[source_rows[:, None], source_records]
    prefix = torch.where(prefix_mask[..., None], prefix, torch.zeros_like(prefix))

    scalar_hour = hour[source_rows].float()
    scalar_day = day[source_rows].float()
    scalar_days = days[source_rows].clamp_min(1).float()
    scalar_units = unit_counts[source_rows].float()
    scalar_successful = successful[source_rows].float()
    scalar_failed = failed[source_rows].float()
    scalar_forced = forced[source_rows].float()
    scalar_x = x[source_rows].float()
    scalar_y = y[source_rows].float()
    scalar_available = available[source_rows]
    scalar_first = first[source_rows].bool()
    unit_optional = optional[source_rows, units].bool()
    tape_size = tape_sizes[source_rows, units]
    reason = reasons[source_rows, units].long()
    continue_legal = scalar_first & unit_optional & (tape_size > 0)
    completed = scalar_successful + scalar_failed
    completion_denominator = completed.clamp_min(1.0)
    denominator = float(turns)

    root = torch.zeros((batch, 24), dtype=torch.float32, device=device)
    root[:, 0] = scalar_hour / denominator
    root[:, 1] = scalar_day / scalar_days
    root[:, 2] = units.float() / float(max(1, unit_limit - 1))
    root[:, 3] = scalar_units / float(unit_limit)
    root[:, 4] = scalar_x / float(board_size - 1)
    root[:, 5] = scalar_y / float(board_size - 1)
    root[:, 6] = scalar_available.float() / denominator
    root[:, 7] = (turns - scalar_available).clamp_min(0).float() / denominator
    root[:, 8] = planning_counts[source_rows].float() / denominator
    root[:, 9] = tape_size.float() / denominator
    root[:, 10] = counts.float() / float(source_prefix_capacity)
    root[:, 11] = scalar_successful / completion_denominator
    root[:, 12] = scalar_failed / completion_denominator
    root[:, 13] = scalar_forced / completion_denominator
    reason_values = torch.arange(7, device=device)
    root[:, 14:21] = (reason[:, None] == reason_values[None]).float()
    root[:, 21] = continue_legal.float()
    root[:, 22] = 1.0
    root[:, 23] = scalar_first.float()

    mode_mask = torch.ones((batch, 2), dtype=torch.bool, device=device)
    mode_mask[:, 0] = continue_legal
    output_available = scalar_available.to(torch.int16)
    day_end = torch.full((batch,), turns, dtype=torch.int16, device=device)
    return root, prefix, prefix_mask, mode_mask, output_available, day_end


def assemble_decision_inputs(
    rows: Tensor,
    current_units: Tensor,
    hour: Tensor,
    day: Tensor,
    days: Tensor,
    unit_counts: Tensor,
    history_counts: Tensor,
    successful: Tensor,
    failed: Tensor,
    forced: Tensor,
    optional: Tensor,
    reasons: Tensor,
    tape_sizes: Tensor,
    x: Tensor,
    y: Tensor,
    available: Tensor,
    first: Tensor,
    planning_counts: Tensor,
    prefix_fields: Tensor,
    *,
    unit_limit: int,
    board_size: int,
    prefix_capacity: int,
    source_prefix_capacity: int | None = None,
    turns: int,
) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor, Tensor]:
    """Gather active rows and construct scalar features with one launch."""
    batch = rows.numel()
    source_capacity = (
        prefix_capacity if source_prefix_capacity is None else source_prefix_capacity
    )
    if source_capacity < prefix_capacity:
        raise ValueError("unit-task source prefix is below its output window")
    if not rows.is_contiguous():
        raise ValueError("unit-task assembly requires contiguous rows")
    if rows.device.type == "cpu":
        return _assemble_decision_inputs_cpu(
            rows,
            current_units,
            hour,
            day,
            days,
            unit_counts,
            history_counts,
            successful,
            failed,
            forced,
            optional,
            reasons,
            tape_sizes,
            x,
            y,
            available,
            first,
            planning_counts,
            prefix_fields,
            unit_limit=unit_limit,
            board_size=board_size,
            prefix_capacity=prefix_capacity,
            source_prefix_capacity=source_capacity,
            turns=turns,
        )
    if rows.device.type != "cuda":
        raise ValueError("unit-task assembly requires CPU or CUDA rows")
    device = rows.device
    root = torch.empty((batch, 24), dtype=torch.float32, device=device)
    prefix = torch.empty(
        (batch, prefix_capacity, 9),
        dtype=prefix_fields.dtype,
        device=device,
    )
    prefix_mask = torch.empty(
        (batch, prefix_capacity), dtype=torch.bool, device=device
    )
    mode_mask = torch.empty((batch, 2), dtype=torch.bool, device=device)
    output_available = torch.empty(batch, dtype=torch.int16, device=device)
    day_end = torch.empty(batch, dtype=torch.int16, device=device)
    block = 256
    _assembly_kernel[
        (batch, triton.cdiv(prefix_capacity * 9, block))
    ](
        rows,
        current_units,
        hour,
        day,
        days,
        unit_counts,
        history_counts,
        successful,
        failed,
        forced,
        optional,
        reasons,
        tape_sizes,
        x,
        y,
        available,
        first,
        planning_counts,
        prefix_fields,
        root,
        prefix,
        prefix_mask,
        mode_mask,
        output_available,
        day_end,
        UNIT_LIMIT=unit_limit,
        BOARD_SIZE=board_size,
        SOURCE_PREFIX_CAPACITY=source_capacity,
        OUTPUT_PREFIX_CAPACITY=prefix_capacity,
        TURNS=turns,
        BLOCK=block,
        num_warps=4,
    )
    return root, prefix, prefix_mask, mode_mask, output_available, day_end


__all__ = ["assemble_decision_inputs"]
