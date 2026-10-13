"""Launch-efficient factorized task features for CUDA rollout."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor

from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.tasks.gpu.route import factorized_route_inputs
from kagg_revue.policy.tasks.grammar import FactorizedTaskDecisionInputs


@triton.jit
def _operation_mask_kernel(
    current_x,
    current_y,
    available_at,
    day_end,
    output,
    BOARD_SIZE: tl.constexpr,
    OPERATION_COUNT: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    operation = tl.arange(0, BLOCK)
    present = operation < OPERATION_COUNT
    remaining = tl.load(day_end + row) - tl.load(available_at + row)
    half = BOARD_SIZE // 2
    x = tl.load(current_x + row)
    y = tl.load(current_y + row)
    warehouse_distance = tl.minimum(
        tl.abs(x - (half - 1)), tl.abs(x - half)
    ) + tl.minimum(tl.abs(y - (half - 1)), tl.abs(y - half))
    warehouse_reachable = warehouse_distance + 1 <= remaining
    allowed = operation == 0
    allowed |= ((operation == 1) | (operation == 2)) & (remaining >= 1)
    allowed |= ((operation == 3) | (operation == 4)) & warehouse_reachable
    allowed |= (operation >= 5) & (remaining >= 1)
    tl.store(
        output + row * OPERATION_COUNT + operation,
        allowed,
        mask=present,
    )


@triton.jit
def _argument_inputs_kernel(
    economic_state,
    current_unit,
    current_x,
    current_y,
    available_at,
    day_end,
    resource_counts,
    operation,
    counts,
    argument_mask,
    STATE_WIDTH: tl.constexpr,
    INVENTORIES: tl.constexpr,
    SHED: tl.constexpr,
    SEEDS: tl.constexpr,
    BOARD_SIZE: tl.constexpr,
    ARGUMENT_COUNT: tl.constexpr,
    RESOURCE_COUNT: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    argument = tl.arange(0, BLOCK)
    present = argument < ARGUMENT_COUNT
    safe = tl.minimum(argument, 11)
    state_base = economic_state + row * STATE_WIDTH
    inventory = INVENTORIES + tl.load(current_unit + row) * 12
    carried = tl.load(
        state_base + inventory + safe, mask=present, other=0
    )
    shed = tl.load(state_base + SHED + safe, mask=present, other=0)
    seed = tl.load(
        state_base + SEEDS + tl.minimum(safe, 4),
        mask=present,
        other=0,
    )
    seed = tl.where(argument < 5, seed, 0)
    selected_operation = tl.load(operation + row)
    resource = tl.full((BLOCK,), -1, tl.int32)
    resource = tl.where(selected_operation == 6, argument, resource)
    resource = tl.where(selected_operation == 3, 5 + argument, resource)
    resource = tl.where(selected_operation == 5, 17 + argument, resource)
    resource = tl.where(selected_operation == 9, 25, resource)
    resource = tl.where(selected_operation == 13, 17, resource)
    valid_resource = (resource >= 0) & (resource < RESOURCE_COUNT)
    conflict = tl.load(
        resource_counts + row * RESOURCE_COUNT + resource,
        mask=present & valid_resource,
        other=0,
    )
    output_base = counts + (row * ARGUMENT_COUNT + argument) * 4
    tl.store(output_base, shed, mask=present)
    tl.store(output_base + 1, carried, mask=present)
    tl.store(output_base + 2, seed, mask=present)
    tl.store(output_base + 3, conflict, mask=present)

    no_argument = (
        (selected_operation != 3)
        & (selected_operation != 5)
        & (selected_operation != 6)
    )
    remaining = tl.load(day_end + row) - tl.load(available_at + row)
    half = BOARD_SIZE // 2
    x = tl.load(current_x + row)
    y = tl.load(current_y + row)
    warehouse_distance = tl.minimum(
        tl.abs(x - (half - 1)), tl.abs(x - half)
    ) + tl.minimum(tl.abs(y - (half - 1)), tl.abs(y - half))
    warehouse_reachable = warehouse_distance + 1 <= remaining
    allowed = no_argument & (argument == 12)
    allowed |= (selected_operation == 3) & (argument < 12)
    allowed |= (selected_operation == 6) & (argument < 5)
    allowed |= (
        (selected_operation == 5)
        & (
            ((argument < 9) & warehouse_reachable)
            | ((argument >= 9) & (argument < 12))
        )
    )
    tl.store(
        argument_mask + row * ARGUMENT_COUNT + argument,
        allowed,
        mask=present,
    )


@triton.jit
def _temporal_inputs_kernel(
    current_x,
    current_y,
    available_at,
    day_end,
    operation,
    target,
    rewrite,
    quantity_mask,
    earliest_mask,
    arrival_output,
    active_task_output,
    requires_quantity_output,
    BOARD_SIZE: tl.constexpr,
    TILE_COUNT: tl.constexpr,
    MAXIMUM_QUANTITY: tl.constexpr,
    TIME_TOKENS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    lane = tl.arange(0, BLOCK)
    selected_operation = tl.load(operation + row)
    selected_target = tl.minimum(tl.maximum(tl.load(target + row), 0), TILE_COUNT - 1)
    target_x = selected_target % BOARD_SIZE
    target_y = selected_target // BOARD_SIZE
    current_x_value = tl.load(current_x + row)
    current_y_value = tl.load(current_y + row)
    distance = (
        tl.abs(current_x_value - target_x)
        + tl.abs(current_y_value - target_y)
    )
    available = tl.load(available_at + row)
    end = tl.load(day_end + row)
    targetless = (selected_operation == 0) | (selected_operation == 2)
    arrival = tl.where(targetless, available, available + distance)
    rewrites = tl.load(rewrite + row)
    active_task = rewrites & (selected_operation != 0)
    requires_quantity = rewrites & (
        (selected_operation == 3) | (selected_operation == 5)
    )
    official = selected_operation >= 3
    quantity_allowed = requires_quantity | (lane == 0)
    tl.store(
        quantity_mask + row * MAXIMUM_QUANTITY + lane,
        quantity_allowed,
        mask=lane < MAXIMUM_QUANTITY,
    )
    earliest_allowed = (
        active_task
        & (lane >= available)
        & (lane <= end)
        & ((selected_operation != 2) | (lane > available))
        & (tl.maximum(arrival, lane) + official.to(tl.int32) <= end)
    )
    earliest_allowed |= ~active_task & (lane == 0)
    tl.store(
        earliest_mask + row * TIME_TOKENS + lane,
        earliest_allowed,
        mask=lane < TIME_TOKENS,
    )
    tl.store(arrival_output + row + lane, arrival, mask=lane == 0)
    tl.store(
        active_task_output + row + lane,
        active_task,
        mask=lane == 0,
    )
    tl.store(
        requires_quantity_output + row + lane,
        requires_quantity,
        mask=lane == 0,
    )


@triton.jit
def _deadline_mask_kernel(
    available_at,
    day_end,
    operation,
    earliest,
    arrival,
    active_task,
    output,
    TIME_TOKENS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    time = tl.arange(0, BLOCK)
    active = tl.load(active_task + row)
    operation_turns = tl.load(operation + row) >= 3
    completion = tl.maximum(
        tl.load(arrival + row), tl.load(earliest + row)
    ) + operation_turns.to(tl.int32)
    allowed = (
        active
        & (time >= completion)
        & (time <= tl.load(day_end + row))
    )
    allowed |= ~active & (time == 0)
    tl.store(
        output + row * TIME_TOKENS + time,
        allowed,
        mask=time < TIME_TOKENS,
    )




def factorized_operation_inputs(
    inputs: FactorizedTaskDecisionInputs,
    operation_count: int,
) -> Tensor:
    """Build factorized operation lookahead in one CUDA launch."""
    batch = inputs.batch_size
    values = (
        inputs.current_x,
        inputs.current_y,
        inputs.available_at,
        inputs.day_end,
    )
    if (
        inputs.context.device.type != "cuda"
        or operation_count < 1
        or any(value.shape != (batch,) for value in values)
        or any(value.device != inputs.context.device for value in values)
        or any(not value.is_contiguous() for value in values)
    ):
        raise ValueError("factorized operation fusion has invalid inputs")
    output = torch.empty(
        (batch, operation_count),
        dtype=torch.bool,
        device=inputs.context.device,
    )
    _operation_mask_kernel[(batch,)](
        *values,
        output,
        BOARD_SIZE=int(round(inputs.target_counts.shape[1] ** 0.5)),
        OPERATION_COUNT=operation_count,
        BLOCK=triton.next_power_of_2(operation_count),
        num_warps=4,
    )
    return output


def factorized_temporal_inputs(
    inputs: FactorizedTaskDecisionInputs,
    operation: Tensor,
    target: Tensor,
    rewrite: Tensor,
    maximum_quantity: int,
    time_tokens: int,
) -> tuple[Tensor, Tensor, Tensor, Tensor, Tensor]:
    """Build quantity and earliest masks plus shared temporal scalars."""
    batch = inputs.batch_size
    values = (
        inputs.current_x,
        inputs.current_y,
        inputs.available_at,
        inputs.day_end,
        operation,
        target,
        rewrite,
    )
    if (
        inputs.context.device.type != "cuda"
        or maximum_quantity < 1
        or time_tokens < 1
        or any(value.shape != (batch,) for value in values)
        or any(value.device != inputs.context.device for value in values)
        or any(not value.is_contiguous() for value in values)
    ):
        raise ValueError("factorized temporal fusion has invalid inputs")
    quantity_mask = torch.empty(
        (batch, maximum_quantity),
        dtype=torch.bool,
        device=inputs.context.device,
    )
    earliest_mask = torch.empty(
        (batch, time_tokens),
        dtype=torch.bool,
        device=inputs.context.device,
    )
    arrival = torch.empty(
        batch, dtype=torch.int64, device=inputs.context.device
    )
    active_task = torch.empty(
        batch, dtype=torch.bool, device=inputs.context.device
    )
    requires_quantity = torch.empty_like(active_task)
    block = triton.next_power_of_2(max(maximum_quantity, time_tokens))
    _temporal_inputs_kernel[(batch,)](
        *values,
        quantity_mask,
        earliest_mask,
        arrival,
        active_task,
        requires_quantity,
        BOARD_SIZE=int(round(inputs.target_counts.shape[1] ** 0.5)),
        TILE_COUNT=inputs.target_counts.shape[1],
        MAXIMUM_QUANTITY=maximum_quantity,
        TIME_TOKENS=time_tokens,
        BLOCK=block,
        num_warps=4,
    )
    return (
        quantity_mask,
        earliest_mask,
        arrival,
        active_task,
        requires_quantity,
    )


def factorized_deadline_mask(
    inputs: FactorizedTaskDecisionInputs,
    operation: Tensor,
    earliest: Tensor,
    arrival: Tensor,
    active_task: Tensor,
    time_tokens: int,
) -> Tensor:
    """Build factorized deadline legality in one CUDA launch."""
    batch = inputs.batch_size
    values = (
        inputs.available_at,
        inputs.day_end,
        operation,
        earliest,
        arrival,
        active_task,
    )
    if (
        inputs.context.device.type != "cuda"
        or time_tokens < 1
        or any(value.shape != (batch,) for value in values)
        or any(value.device != inputs.context.device for value in values)
        or any(not value.is_contiguous() for value in values)
    ):
        raise ValueError("factorized deadline fusion has invalid inputs")
    output = torch.empty(
        (batch, time_tokens),
        dtype=torch.bool,
        device=inputs.context.device,
    )
    _deadline_mask_kernel[(batch,)](
        *values,
        output,
        TIME_TOKENS=time_tokens,
        BLOCK=triton.next_power_of_2(time_tokens),
        num_warps=4,
    )
    return output


def factorized_argument_inputs(
    inputs: FactorizedTaskDecisionInputs,
    operation: Tensor,
    layout: EconomicStateLayout,
) -> tuple[Tensor, Tensor]:
    """Gather argument counts and the exact argument mask in one launch."""
    batch = inputs.batch_size
    argument_count = 13
    resource_count = inputs.resource_counts.shape[1]
    expected = {
        "economic_state": (batch, layout.width),
        "current_unit": (batch,),
        "current_x": (batch,),
        "current_y": (batch,),
        "available_at": (batch,),
        "day_end": (batch,),
        "resource_counts": (batch, resource_count),
        "operation": (batch,),
    }
    values = {
        "economic_state": inputs.economic_state,
        "current_unit": inputs.current_unit,
        "current_x": inputs.current_x,
        "current_y": inputs.current_y,
        "available_at": inputs.available_at,
        "day_end": inputs.day_end,
        "resource_counts": inputs.resource_counts,
        "operation": operation,
    }
    for name, shape in expected.items():
        value = values[name]
        if value.shape != shape:
            raise ValueError(f"factorized argument {name} has the wrong shape")
        if value.device != inputs.economic_state.device:
            raise ValueError("factorized argument tensors must share one device")
        if not value.is_contiguous():
            raise ValueError("factorized argument tensors must be contiguous")
    if inputs.economic_state.device.type != "cuda":
        raise ValueError("factorized argument fusion requires CUDA inputs")
    counts = torch.empty(
        (batch, argument_count, 4),
        dtype=inputs.economic_state.dtype,
        device=inputs.economic_state.device,
    )
    argument_mask = torch.empty(
        (batch, argument_count),
        dtype=torch.bool,
        device=inputs.economic_state.device,
    )
    _argument_inputs_kernel[(batch,)](
        inputs.economic_state,
        inputs.current_unit,
        inputs.current_x,
        inputs.current_y,
        inputs.available_at,
        inputs.day_end,
        inputs.resource_counts,
        operation,
        counts,
        argument_mask,
        STATE_WIDTH=layout.width,
        INVENTORIES=layout.inventories,
        SHED=layout.shed,
        SEEDS=layout.seeds,
        BOARD_SIZE=layout.board_size,
        ARGUMENT_COUNT=argument_count,
        RESOURCE_COUNT=resource_count,
        BLOCK=16,
        num_warps=4,
    )
    return counts, argument_mask


__all__ = [
    "factorized_argument_inputs",
    "factorized_deadline_mask",
    "factorized_operation_inputs",
    "factorized_route_inputs",
    "factorized_temporal_inputs",
]
