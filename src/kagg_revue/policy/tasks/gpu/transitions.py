"""Fused CUDA transition for one autoregressive task selection."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor

from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.tasks.grammar import TaskActions, TaskCatalog


def _resource_key(operation: int, argument: int, unit: int) -> int:
    """Return the compact reservation key used by the native task planner."""
    if operation == 6:
        return 100 + argument
    if operation == 3:
        return 200 + argument
    if operation == 5:
        return 300 + unit * 12 + argument
    if operation == 9:
        return 300 + unit * 12 + 8
    if operation == 13:
        return 300 + unit * 12
    return -1


def _apply_selection_cpu(
    rows: Tensor,
    actions: TaskActions,
    arrivals: Tensor,
    catalog: TaskCatalog,
    economic_state: Tensor,
    active: Tensor,
    hour: Tensor,
    history_counts: Tensor,
    forced_ends: Tensor,
    prefix_fields: Tensor,
    replan: Tensor,
    optional: Tensor,
    tape_sizes: Tensor,
    current_units: Tensor,
    x: Tensor,
    y: Tensor,
    available: Tensor,
    first: Tensor,
    planning_counts: Tensor,
    target_counts: Tensor,
    resource_counts: Tensor,
    layout: EconomicStateLayout,
    prefix_capacity: int,
    turns: int,
) -> None:
    """Reference transition for CPU rollout and compact PPO reconstruction."""
    for local in range(rows.numel()):
        row = int(rows[local])
        if not bool(active[row]):
            continue
        mode = int(actions.mode[local])
        candidate = int(actions.candidate[local])
        quantity = int(actions.quantity[local])
        selected_earliest = int(actions.earliest[local])
        selected_deadline = int(actions.deadline[local])
        arrival = int(arrivals[local])
        operation = int(catalog.operations[candidate])
        argument = int(catalog.arguments[candidate])
        target_x = int(catalog.targets[candidate, 0])
        target_y = int(catalog.targets[candidate, 1])
        operation_turns = int(catalog.operation_turns[candidate])
        unit = int(current_units[row])
        was_first = bool(first[row])
        rewrite = mode == 1
        is_end = operation == 0
        is_wait = operation == 2
        clear = rewrite and was_first
        task = rewrite and not is_end
        finish = not rewrite or is_end
        history_count = int(history_counts[row])

        remaining = replan[row].clone().bool()
        remaining[unit] = False
        still_active = bool(remaining.any())
        next_unit = int(remaining.to(torch.int8).argmax())

        records = prefix_fields[row, :history_count]
        record_active = records[:, 8] == 0
        owners = records[:, 0].long()
        reservation_delta = torch.zeros(
            history_count, dtype=torch.int32, device=rows.device
        )
        if finish and not rewrite and was_first:
            reservation_delta += (record_active & (owners == unit)).to(torch.int32)
        if finish and still_active:
            reservation_delta -= (record_active & (owners == next_unit)).to(
                torch.int32
            )
        changed = torch.nonzero(reservation_delta, as_tuple=False).flatten()
        for record_index in changed.tolist():
            delta = int(reservation_delta[record_index])
            record = records[record_index]
            record_operation = int(record[1])
            record_argument = int(record[2]) - 1
            record_x = int(record[3]) - 1
            record_y = int(record[4]) - 1
            if record_x >= 0 and record_y >= 0:
                target_counts[
                    row, record_y * layout.board_size + record_x
                ] += delta
            resource = _resource_key(
                record_operation, record_argument, int(record[0])
            )
            if resource >= 0:
                resource_counts[row, resource] += delta

        if task and target_x >= 0 and target_y >= 0:
            target_counts[row, target_y * layout.board_size + target_x] += 1
        selected_resource = _resource_key(operation, argument, unit)
        if task and selected_resource >= 0:
            resource_counts[row, selected_resource] += 1

        if clear and history_count:
            clear_records = (owners == unit) & record_active
            records[clear_records, 8] = 8
        if clear or task:
            if history_count >= prefix_capacity:
                inactive = prefix_fields[row, :, 8] != 0
                remove = int(inactive.to(torch.int8).argmax())
                source = torch.arange(prefix_capacity, device=rows.device)
                source += (source >= remove).long()
                source.clamp_(max=prefix_capacity - 1)
                prefix_fields[row] = prefix_fields[row].index_select(0, source)
                append_at = prefix_capacity - 1
            else:
                append_at = history_count
            if task:
                prefix_fields[row, append_at] = torch.tensor(
                    (
                        unit,
                        operation,
                        argument + 1,
                        target_x + 1,
                        target_y + 1,
                        quantity,
                        selected_earliest,
                        selected_deadline,
                        0,
                    ),
                    dtype=prefix_fields.dtype,
                    device=prefix_fields.device,
                )
                history_counts[row] = min(history_count + 1, prefix_capacity)

        if clear or task:
            tape_sizes[row, unit] = (0 if clear else int(tape_sizes[row, unit])) + int(
                task
            )
        old_available = int(available[row])
        if task:
            available[row] = max(arrival, selected_earliest) + operation_turns
            if not is_wait:
                x[row] = target_x
                y[row] = target_y
            planning_counts[row] += 1
            first[row] = False

        if finish:
            replan[row, unit] = False
            optional[row, unit] = False
            active[row] = still_active
            current_units[row] = next_unit
            position = layout.positions + next_unit * 2
            x[row] = economic_state[row, position]
            y[row] = economic_state[row, position + 1]
            available[row] = hour[row]
            first[row] = still_active
            planning_counts[row] = 0
            if rewrite and is_end and old_available >= turns:
                forced_ends[row] += 1


@triton.jit
def _selection_kernel(
    rows,
    modes,
    candidates,
    quantities,
    earliest,
    deadlines,
    arrivals,
    catalog_operations,
    catalog_arguments,
    catalog_targets,
    catalog_turns,
    economic_state,
    active,
    hour,
    history_counts,
    forced_ends,
    prefix_fields,
    replan,
    optional,
    tape_sizes,
    current_units,
    simulated_x,
    simulated_y,
    available_at,
    first,
    planning_counts,
    target_counts,
    resource_counts,
    STATE_WIDTH: tl.constexpr,
    POSITIONS: tl.constexpr,
    UNIT_LIMIT: tl.constexpr,
    BOARD_SIZE: tl.constexpr,
    PREFIX_CAPACITY: tl.constexpr,
    RESOURCE_WIDTH: tl.constexpr,
    TURNS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    active_row = tl.program_id(0)
    lane = tl.arange(0, BLOCK)
    row = tl.load(rows + active_row)
    mode = tl.load(modes + active_row)
    candidate = tl.load(candidates + active_row)
    quantity = tl.load(quantities + active_row)
    selected_earliest = tl.load(earliest + active_row)
    selected_deadline = tl.load(deadlines + active_row)
    arrival = tl.load(arrivals + active_row)
    operation = tl.load(catalog_operations + candidate)
    argument = tl.load(catalog_arguments + candidate)
    target_x = tl.load(catalog_targets + candidate * 2)
    target_y = tl.load(catalog_targets + candidate * 2 + 1)
    operation_turns = tl.load(catalog_turns + candidate)
    unit = tl.load(current_units + row)
    enabled = tl.load(active + row) != 0
    was_first = tl.load(first + row) != 0
    rewrite = mode == 1
    is_end = operation == 0
    is_wait = operation == 2
    clear = enabled & rewrite & was_first
    task = enabled & rewrite & ~is_end
    finish = enabled & (~rewrite | is_end)
    history_count = tl.load(history_counts + row)

    unit_lane = lane < UNIT_LIMIT
    remaining = tl.load(
        replan + row * UNIT_LIMIT + lane,
        mask=unit_lane,
        other=0,
    ) != 0
    remaining &= lane != unit
    still_active = tl.max(remaining.to(tl.int32), axis=0) != 0
    next_unit = tl.argmax(remaining.to(tl.int32), axis=0)

    prefix_lane = lane < PREFIX_CAPACITY
    prefix_base = prefix_fields + row * PREFIX_CAPACITY * 9
    owner = tl.load(
        prefix_base + lane * 9, mask=prefix_lane, other=0
    )
    status = tl.load(
        prefix_base + lane * 9 + 8, mask=prefix_lane, other=0
    )
    prefix_valid = prefix_lane & (lane < history_count)
    record_active = prefix_valid & (status == 0)
    restore_current = (
        finish
        & ~rewrite
        & was_first
        & record_active
        & (owner == unit)
    )
    exclude_next = (
        finish
        & still_active
        & record_active
        & (owner == next_unit)
    )
    reservation_delta = restore_current.to(tl.int32) - exclude_next.to(
        tl.int32
    )
    record_operation = tl.load(
        prefix_base + lane * 9 + 1, mask=prefix_valid, other=0
    )
    record_argument = (
        tl.load(prefix_base + lane * 9 + 2, mask=prefix_valid, other=0)
        - 1
    )
    record_x = (
        tl.load(prefix_base + lane * 9 + 3, mask=prefix_valid, other=0)
        - 1
    )
    record_y = (
        tl.load(prefix_base + lane * 9 + 4, mask=prefix_valid, other=0)
        - 1
    )
    record_targeted = (record_x >= 0) & (record_y >= 0)
    record_tile = (
        tl.maximum(record_y, 0) * BOARD_SIZE + tl.maximum(record_x, 0)
    )
    tl.atomic_add(
        target_counts + row * BOARD_SIZE * BOARD_SIZE + record_tile,
        reservation_delta,
        mask=(reservation_delta != 0) & record_targeted,
    )
    record_resource = -1
    record_resource = tl.where(
        record_operation == 6, 100 + record_argument, record_resource
    )
    record_resource = tl.where(
        record_operation == 3, 200 + record_argument, record_resource
    )
    record_resource = tl.where(
        record_operation == 5,
        300 + owner * 12 + record_argument,
        record_resource,
    )
    record_resource = tl.where(
        record_operation == 9, 300 + owner * 12 + 8, record_resource
    )
    record_resource = tl.where(
        record_operation == 13, 300 + owner * 12, record_resource
    )
    tl.atomic_add(
        resource_counts
        + row * RESOURCE_WIDTH
        + tl.maximum(record_resource, 0),
        reservation_delta,
        mask=(reservation_delta != 0) & (record_resource >= 0),
    )

    task_tile = (
        tl.maximum(target_y, 0) * BOARD_SIZE + tl.maximum(target_x, 0)
    )
    tl.atomic_add(
        target_counts + row * BOARD_SIZE * BOARD_SIZE + task_tile,
        1,
        mask=task & (target_x >= 0) & (target_y >= 0),
    )
    selected_resource = -1
    selected_resource = tl.where(
        operation == 6, 100 + argument, selected_resource
    )
    selected_resource = tl.where(
        operation == 3, 200 + argument, selected_resource
    )
    selected_resource = tl.where(
        operation == 5,
        300 + unit * 12 + argument,
        selected_resource,
    )
    selected_resource = tl.where(
        operation == 9, 300 + unit * 12 + 8, selected_resource
    )
    selected_resource = tl.where(
        operation == 13, 300 + unit * 12, selected_resource
    )
    tl.atomic_add(
        resource_counts
        + row * RESOURCE_WIDTH
        + tl.maximum(selected_resource, 0),
        1,
        mask=task & (selected_resource >= 0),
    )

    status = tl.where(
        clear & prefix_valid & (owner == unit) & (status == 0), 8, status
    )
    inactive = prefix_valid & (status != 0)
    remove = tl.argmax(inactive.to(tl.int32), axis=0)
    full = history_count >= PREFIX_CAPACITY
    source = tl.where(full & (lane >= remove), lane + 1, lane)
    source = tl.minimum(source, PREFIX_CAPACITY - 1)
    source_owner = tl.load(
        prefix_base + source * 9, mask=prefix_lane, other=0
    )
    append_at = tl.where(full, PREFIX_CAPACITY - 1, history_count)
    append = task & prefix_lane & (lane == append_at)
    appended = (
        unit,
        operation,
        argument + 1,
        target_x + 1,
        target_y + 1,
        quantity,
        selected_earliest,
        selected_deadline,
        0,
    )
    for field in tl.static_range(0, 9):
        value = tl.load(
            prefix_base + source * 9 + field,
            mask=prefix_lane,
            other=0,
        )
        if field == 8:
            value = tl.where(
                clear
                & (source < history_count)
                & (source_owner == unit)
                & (value == 0),
                8,
                value,
            )
        value = tl.where(append, appended[field], value)
        tl.store(
            prefix_base + lane * 9 + field,
            value,
            mask=prefix_lane & (clear | task),
        )
    tl.store(
        history_counts + row + lane,
        tl.minimum(history_count + 1, PREFIX_CAPACITY),
        mask=(lane == 0) & task,
    )

    old_tape_size = tl.load(tape_sizes + row * UNIT_LIMIT + unit)
    next_tape_size = tl.where(clear, 0, old_tape_size) + task.to(tl.int64)
    tl.store(
        tape_sizes + row * UNIT_LIMIT + unit + lane,
        next_tape_size,
        mask=(lane == 0) & (clear | task),
    )
    completion = tl.maximum(arrival, selected_earliest) + operation_turns
    old_available = tl.load(available_at + row)
    old_x = tl.load(simulated_x + row)
    old_y = tl.load(simulated_y + row)
    old_planning_count = tl.load(planning_counts + row)
    tl.store(available_at + row + lane, completion, mask=(lane == 0) & task)
    tl.store(
        simulated_x + row + lane,
        tl.where(is_wait, old_x, target_x),
        mask=(lane == 0) & task,
    )
    tl.store(
        simulated_y + row + lane,
        tl.where(is_wait, old_y, target_y),
        mask=(lane == 0) & task,
    )
    tl.store(
        planning_counts + row + lane,
        old_planning_count + 1,
        mask=(lane == 0) & task,
    )
    tl.store(first + row + lane, 0, mask=(lane == 0) & task)

    tl.store(
        replan + row * UNIT_LIMIT + unit + lane,
        0,
        mask=(lane == 0) & finish,
    )
    tl.store(
        optional + row * UNIT_LIMIT + unit + lane,
        0,
        mask=(lane == 0) & finish,
    )
    tl.store(active + row + lane, still_active, mask=(lane == 0) & finish)
    tl.store(current_units + row + lane, next_unit, mask=(lane == 0) & finish)
    state_base = economic_state + row * STATE_WIDTH
    next_x = tl.load(state_base + POSITIONS + next_unit * 2)
    next_y = tl.load(state_base + POSITIONS + next_unit * 2 + 1)
    tl.store(simulated_x + row + lane, next_x, mask=(lane == 0) & finish)
    tl.store(simulated_y + row + lane, next_y, mask=(lane == 0) & finish)
    tl.store(
        available_at + row + lane,
        tl.load(hour + row),
        mask=(lane == 0) & finish,
    )
    tl.store(first + row + lane, still_active, mask=(lane == 0) & finish)
    tl.store(planning_counts + row + lane, 0, mask=(lane == 0) & finish)
    forced = rewrite & is_end & (old_available >= TURNS)
    old_forced = tl.load(forced_ends + row)
    tl.store(
        forced_ends + row + lane,
        old_forced + forced.to(tl.int64),
        mask=(lane == 0) & finish,
    )


def apply_selection(
    rows: Tensor,
    actions: TaskActions,
    arrivals: Tensor,
    catalog: TaskCatalog,
    economic_state: Tensor,
    active: Tensor,
    hour: Tensor,
    history_counts: Tensor,
    forced_ends: Tensor,
    prefix_fields: Tensor,
    replan: Tensor,
    optional: Tensor,
    tape_sizes: Tensor,
    current_units: Tensor,
    x: Tensor,
    y: Tensor,
    available: Tensor,
    first: Tensor,
    planning_counts: Tensor,
    target_counts: Tensor,
    resource_counts: Tensor,
    layout: EconomicStateLayout,
    prefix_capacity: int,
    turns: int,
) -> None:
    """Apply active selections in place with one launch."""
    count = rows.numel()
    if count == 0:
        return
    action_values = tuple(getattr(actions, name) for name in actions.__dataclass_fields__)
    if any(value.shape != (count,) or not value.is_contiguous() for value in action_values):
        raise ValueError("unit-task CUDA actions must be contiguous vectors")
    if rows.shape != (count,) or not rows.is_contiguous() or arrivals.shape != (count,):
        raise ValueError("unit-task CUDA transition rows are malformed")
    if rows.device.type == "cpu":
        _apply_selection_cpu(
            rows,
            actions,
            arrivals,
            catalog,
            economic_state,
            active,
            hour,
            history_counts,
            forced_ends,
            prefix_fields,
            replan,
            optional,
            tape_sizes,
            current_units,
            x,
            y,
            available,
            first,
            planning_counts,
            target_counts,
            resource_counts,
            layout,
            prefix_capacity,
            turns,
        )
        return
    if rows.device.type != "cuda":
        raise ValueError("unit-task transition requires CPU or CUDA rows")
    resource_width = 300 + layout.unit_limit * 12
    _selection_kernel[(count,)](
        rows,
        actions.mode,
        actions.candidate,
        actions.quantity,
        actions.earliest,
        actions.deadline,
        arrivals,
        catalog.operations,
        catalog.arguments,
        catalog.targets,
        catalog.operation_turns,
        economic_state,
        active,
        hour,
        history_counts,
        forced_ends,
        prefix_fields,
        replan,
        optional,
        tape_sizes,
        current_units,
        x,
        y,
        available,
        first,
        planning_counts,
        target_counts,
        resource_counts,
        STATE_WIDTH=layout.width,
        POSITIONS=layout.positions,
        UNIT_LIMIT=layout.unit_limit,
        BOARD_SIZE=layout.board_size,
        PREFIX_CAPACITY=prefix_capacity,
        RESOURCE_WIDTH=resource_width,
        TURNS=turns,
        BLOCK=1024,
        num_warps=8,
    )


__all__ = ["apply_selection"]
