"""H200 route features and target legality for factorized task rollout."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor

from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.tasks.grammar import FactorizedTaskDecisionInputs


@triton.jit
def _route_inputs_kernel(
    economic_state,
    current_unit,
    current_x,
    current_y,
    available_at,
    day_end,
    operation,
    argument,
    scaled_target_counts,
    scaled_resource,
    route,
    target_mask,
    STATE_WIDTH: tl.constexpr,
    INVENTORIES: tl.constexpr,
    SHED: tl.constexpr,
    SEEDS: tl.constexpr,
    TILES: tl.constexpr,
    TILE_FIELDS: tl.constexpr,
    BOARD_SIZE: tl.constexpr,
    TILE_COUNT: tl.constexpr,
    TIME_DENOMINATOR: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    tile = tl.arange(0, BLOCK)
    present = tile < TILE_COUNT
    target_x = tile % BOARD_SIZE
    target_y = tile // BOARD_SIZE
    x = tl.load(current_x + row)
    y = tl.load(current_y + row)
    distance = tl.abs(x - target_x) + tl.abs(y - target_y)
    selected_operation = tl.load(operation + row)
    selected_argument = tl.load(argument + row)
    available = tl.load(available_at + row)
    end = tl.load(day_end + row)
    official = selected_operation >= 3
    arrival = available + distance
    completion = arrival + official.to(tl.int32)
    remaining = tl.maximum(end - completion, 0)

    state_base = economic_state + row * STATE_WIDTH
    tile_base = state_base + TILES + tile * TILE_FIELDS
    kind = tl.load(tile_base, mask=present, other=0)
    crop = tl.load(tile_base + 1, mask=present, other=0)
    planted_day = tl.load(tile_base + 2, mask=present, other=0)
    watered = tl.load(tile_base + 3, mask=present, other=0)
    yield_units = tl.load(tile_base + 5, mask=present, other=0)
    structure = tl.load(tile_base + 6, mask=present, other=0)
    has_animal = tl.load(tile_base + 7, mask=present, other=0)
    fed = tl.load(tile_base + 9, mask=present, other=0)
    cared = tl.load(tile_base + 10, mask=present, other=0)
    fertilizer_available = tl.load(tile_base + 11, mask=present, other=0)
    half = BOARD_SIZE // 2
    adjacent = (
        ((target_x == half - 1) | (target_x == half))
        & ((target_y == half - 1) | (target_y == half))
    )
    safe_argument = tl.minimum(tl.maximum(selected_argument, 0), 11)
    inventory = (
        INVENTORIES + tl.load(current_unit + row) * 12
    )
    carried = tl.load(state_base + inventory + safe_argument)
    fertilizer = tl.load(state_base + inventory + 8)
    wheat = tl.load(state_base + inventory)
    shed = tl.load(state_base + SHED + safe_argument)
    seed = tl.load(
        state_base + SEEDS + tl.minimum(safe_argument, 4)
    )
    room = tl.maximum(
        tl.load(state_base + 5) - tl.load(state_base + 8), 0
    )
    animal_place = (
        (selected_argument >= 9)
        & (selected_argument < 12)
        & (kind == 4)
        & (has_animal == 0)
        & (structure == (selected_argument != 9))
    )
    unlocked = kind != 1
    first_yield = tl.where(crop <= 1, 2, tl.where(crop == 2, 8, 10))
    day = tl.load(state_base)
    legal = (
        (selected_operation == 0)
        | (selected_operation == 1)
        | (selected_operation == 2)
    )
    legal |= (
        (selected_operation == 3)
        & adjacent
        & (selected_argument >= 0)
        & (selected_argument < 12)
        & (shed > 0)
    )
    legal |= (selected_operation == 4) & adjacent
    legal |= (
        (selected_operation == 5)
        & (selected_argument >= 0)
        & (selected_argument < 12)
        & (carried > 0)
        & (animal_place | (adjacent & (room > 0)))
    )
    legal |= (
        (selected_operation == 6)
        & unlocked
        & (selected_argument >= 0)
        & (selected_argument < 5)
        & (kind == 0)
        & (seed > 0)
    )
    legal |= (
        (selected_operation == 7)
        & unlocked
        & (kind == 3)
        & (watered == 0)
    )
    legal |= (
        (selected_operation == 8)
        & unlocked
        & (yield_units > 0)
        & (
            ((kind == 3) & (day - planted_day >= first_yield))
            | ((kind == 4) & (has_animal != 0))
        )
    )
    legal |= (
        (selected_operation == 9)
        & unlocked
        & (kind == 3)
        & (fertilizer > 0)
    )
    legal |= (
        (selected_operation == 10)
        & unlocked
        & (kind != 0)
        & ~((kind == 4) & (has_animal != 0))
    )
    legal |= (
        ((selected_operation == 11) | (selected_operation == 12))
        & unlocked
        & (kind == 0)
    )
    legal |= (
        (selected_operation == 13)
        & unlocked
        & (kind == 4)
        & (has_animal != 0)
        & (fed == 0)
        & (wheat > 0)
    )
    legal |= (
        (selected_operation == 14)
        & unlocked
        & (kind == 4)
        & (has_animal != 0)
        & (fertilizer_available != 0)
    )
    legal |= (
        (selected_operation == 15)
        & unlocked
        & (kind == 4)
        & (has_animal != 0)
        & (cared == 0)
    )

    denominator = float(TIME_DENOMINATOR)
    route_base = route + (row * TILE_COUNT + tile) * 8
    tl.store(
        route_base,
        distance.to(tl.float32) / denominator,
        mask=present,
    )
    tl.store(
        route_base + 1,
        arrival.to(tl.float32) / denominator,
        mask=present,
    )
    tl.store(
        route_base + 2,
        completion.to(tl.float32) / denominator,
        mask=present,
    )
    tl.store(
        route_base + 3,
        remaining.to(tl.float32) / denominator,
        mask=present,
    )
    tl.store(route_base + 4, legal.to(tl.float32), mask=present)
    tl.store(
        route_base + 5,
        tl.load(
            scaled_target_counts + row * TILE_COUNT + tile,
            mask=present,
            other=0.0,
        ),
        mask=present,
    )
    tl.store(
        route_base + 6,
        tl.load(scaled_resource + row),
        mask=present,
    )
    tl.store(
        route_base + 7,
        official.to(tl.float32),
        mask=present,
    )

    targetless = (selected_operation == 0) | (selected_operation == 2)
    allowed = completion <= end
    allowed &= (selected_operation != 1) | (distance > 0)
    constrained = (
        (selected_operation == 3)
        | (selected_operation == 4)
        | ((selected_operation == 5) & (selected_argument < 9))
    )
    allowed &= ~constrained | adjacent
    allowed &= ~targetless
    tl.store(
        target_mask + row * (TILE_COUNT + 1) + tile,
        allowed,
        mask=present,
    )
    tl.store(
        target_mask + row * (TILE_COUNT + 1) + TILE_COUNT + tile,
        targetless,
        mask=tile == 0,
    )


def factorized_route_inputs(
    inputs: FactorizedTaskDecisionInputs,
    operation: Tensor,
    argument: Tensor,
    scaled_target_counts: Tensor,
    scaled_resource: Tensor,
    layout: EconomicStateLayout,
    time_tokens: int,
) -> tuple[Tensor, Tensor]:
    """Build route features and the exact target mask in one CUDA launch."""
    batch = inputs.batch_size
    tiles = layout.board_size * layout.board_size
    expected = {
        "economic_state": (batch, layout.width),
        "current_unit": (batch,),
        "current_x": (batch,),
        "current_y": (batch,),
        "available_at": (batch,),
        "day_end": (batch,),
        "operation": (batch,),
        "argument": (batch,),
        "scaled_target_counts": (batch, tiles),
        "scaled_resource": (batch,),
    }
    values = {
        "economic_state": inputs.economic_state,
        "current_unit": inputs.current_unit,
        "current_x": inputs.current_x,
        "current_y": inputs.current_y,
        "available_at": inputs.available_at,
        "day_end": inputs.day_end,
        "operation": operation,
        "argument": argument,
        "scaled_target_counts": scaled_target_counts,
        "scaled_resource": scaled_resource,
    }
    for name, shape in expected.items():
        value = values[name]
        if value.shape != shape:
            raise ValueError(f"factorized route {name} has the wrong shape")
        if value.device != inputs.economic_state.device:
            raise ValueError("factorized route tensors must share one device")
        if not value.is_contiguous():
            raise ValueError("factorized route tensors must be contiguous")
    if inputs.economic_state.device.type != "cuda" or time_tokens < 2:
        raise ValueError("factorized route fusion requires CUDA task inputs")
    route = torch.empty(
        (batch, tiles, 8),
        dtype=torch.float32,
        device=inputs.economic_state.device,
    )
    target_mask = torch.empty(
        (batch, tiles + 1),
        dtype=torch.bool,
        device=inputs.economic_state.device,
    )
    _route_inputs_kernel[(batch,)](
        inputs.economic_state,
        inputs.current_unit,
        inputs.current_x,
        inputs.current_y,
        inputs.available_at,
        inputs.day_end,
        operation,
        argument,
        scaled_target_counts,
        scaled_resource,
        route,
        target_mask,
        STATE_WIDTH=layout.width,
        INVENTORIES=layout.inventories,
        SHED=layout.shed,
        SEEDS=layout.seeds,
        TILES=layout.tiles,
        TILE_FIELDS=layout.tile_fields,
        BOARD_SIZE=layout.board_size,
        TILE_COUNT=tiles,
        TIME_DENOMINATOR=time_tokens - 1,
        BLOCK=triton.next_power_of_2(tiles),
        num_warps=4,
    )
    return route, target_mask

__all__ = ["factorized_route_inputs"]

