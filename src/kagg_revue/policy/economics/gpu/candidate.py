"""Fused CUDA compilation of per-action economic consequences."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor

from kagg_revue.policy.economics.gpu.common import (
    _fibonacci,
    _layout_arguments,
    _market_price,
    _signed_log,
    _validate_state,
)
from kagg_revue.policy.economics.layout import (
    ACTION_TOKENS,
    CANDIDATE_FEATURES,
    EconomicStateLayout,
)

_ACTION_TOKENS = tl.constexpr(67)
_CANDIDATE_FEATURES = tl.constexpr(20)
_MAXIMUM_QUANTITY = tl.constexpr(128)


@triton.jit
def _candidate_kernel(
    state,
    phases,
    output,
    PHASE_STRIDE: tl.constexpr,
    STATE_WIDTH: tl.constexpr,
    UNIT_LIMIT: tl.constexpr,
    BOARD_SIZE: tl.constexpr,
    POSITIONS: tl.constexpr,
    INVENTORIES: tl.constexpr,
    SHED: tl.constexpr,
    SEEDS: tl.constexpr,
    MARKET_INVENTORY: tl.constexpr,
    MARKET_BASE_MILLI: tl.constexpr,
    MARKET_I0: tl.constexpr,
    MARKET_T_MILLI: tl.constexpr,
    MARKET_BELOW_FUNCTION: tl.constexpr,
    MARKET_BELOW_TARGET_MILLI: tl.constexpr,
    MARKET_ABOVE_FUNCTION: tl.constexpr,
    MARKET_ABOVE_TARGET_MILLI: tl.constexpr,
    SEED_COSTS: tl.constexpr,
    ANIMAL_COSTS: tl.constexpr,
    LAND_COSTS: tl.constexpr,
    TILES: tl.constexpr,
    TILE_FIELDS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    token = tl.arange(0, BLOCK)
    valid = token < _ACTION_TOKENS
    base = state + row * STATE_WIDTH
    out = output + row * _ACTION_TOKENS * _CANDIDATE_FEATURES
    phase = tl.load(phases + row * PHASE_STRIDE)
    phase_valid = ((phase == 0) & (token < 44)) | ((phase == 1) & (token >= 44))
    capacity = tl.load(base + 5)
    shed_total = tl.load(base + 8)
    free = tl.maximum(capacity - shed_total, 0)
    money = tl.maximum(tl.load(base + 9), 0)
    inherited_conditional = tl.load(base + 13) != 0

    item = tl.where(
        token < 17,
        token - 5,
        token - 18,
    )
    item = tl.maximum(0, tl.minimum(item, 11))
    shed = tl.load(base + SHED + item)
    unit_index = tl.maximum(0, tl.minimum(tl.load(base + 2), UNIT_LIMIT - 1))
    carried = tl.load(base + INVENTORIES + unit_index * 12 + item)
    x = tl.load(base + POSITIONS + unit_index * 2)
    y = tl.load(base + POSITIONS + unit_index * 2 + 1)
    half = BOARD_SIZE // 2
    adjacent = ((x == half - 1) | (x == half)) & ((y == half - 1) | (y == half))
    tile = base + TILES + (y * BOARD_SIZE + x) * TILE_FIELDS
    tile_kind = tl.load(tile)
    tile_structure = tl.load(tile + 6)
    tile_animal = tl.load(tile + 7)
    animal_item = item >= 9
    expected_structure = item != 9
    animal_place = (
        animal_item & (tile_kind == 4) & (tile_animal == 0) & (tile_structure == expected_structure)
    )
    place_maximum = tl.where(
        animal_place,
        tl.minimum(carried, 1),
        tl.where(adjacent, tl.minimum(carried, free), 0),
    )

    maximum = tl.where(token < 44, 1, 0)
    pickup_quantity = (token >= 5) & (token < 17)
    place_quantity = (token >= 18) & (token < 30)
    maximum = tl.where(pickup_quantity, tl.maximum(shed, 0), maximum)
    maximum = tl.where(place_quantity, tl.maximum(place_maximum, 0), maximum)
    maximum = tl.maximum(0, tl.minimum(maximum, _MAXIMUM_QUANTITY))

    is_sell = (token >= 46) & (token <= 54)
    sell_product = tl.maximum(0, tl.minimum(token - 46, 8))
    sell_count = tl.load(base + SHED + sell_product)
    sell_inventory = tl.load(base + MARKET_INVENTORY + sell_product)
    sell_price = _market_price(
        base,
        sell_product,
        sell_inventory,
        MARKET_BASE_MILLI,
        MARKET_I0,
        MARKET_T_MILLI,
        MARKET_BELOW_FUNCTION,
        MARKET_BELOW_TARGET_MILLI,
        MARKET_ABOVE_FUNCTION,
        MARKET_ABOVE_TARGET_MILLI,
    )
    sell_next = _market_price(
        base,
        sell_product,
        sell_inventory + (sell_price > 1.0).to(tl.int32),
        MARKET_BASE_MILLI,
        MARKET_I0,
        MARKET_T_MILLI,
        MARKET_BELOW_FUNCTION,
        MARKET_BELOW_TARGET_MILLI,
        MARKET_ABOVE_FUNCTION,
        MARKET_ABOVE_TARGET_MILLI,
    )
    maximum = tl.where(is_sell, tl.minimum(tl.maximum(sell_count, 0), 128), maximum)

    is_seed = (token >= 55) & (token <= 59)
    seed = tl.maximum(0, tl.minimum(token - 55, 4))
    seed_cost = tl.maximum(tl.load(base + SEED_COSTS + seed), 1)
    seed_maximum = tl.minimum(money // seed_cost, 128)
    maximum = tl.where(is_seed, seed_maximum, maximum)

    is_product = (token == 60) | (token == 61)
    product = tl.where(token == 61, 8, 0)
    product_inventory = tl.load(base + MARKET_INVENTORY + product)
    buy_price = _market_price(
        base,
        product,
        product_inventory - 1,
        MARKET_BASE_MILLI,
        MARKET_I0,
        MARKET_T_MILLI,
        MARKET_BELOW_FUNCTION,
        MARKET_BELOW_TARGET_MILLI,
        MARKET_ABOVE_FUNCTION,
        MARKET_ABOVE_TARGET_MILLI,
    )
    buy_next = _market_price(
        base,
        product,
        product_inventory - 2,
        MARKET_BASE_MILLI,
        MARKET_I0,
        MARKET_T_MILLI,
        MARKET_BELOW_FUNCTION,
        MARKET_BELOW_TARGET_MILLI,
        MARKET_ABOVE_FUNCTION,
        MARKET_ABOVE_TARGET_MILLI,
    )

    is_animal = (token >= 62) & (token <= 64)
    animal = tl.maximum(0, tl.minimum(token - 62, 2))
    animal_cost = tl.maximum(tl.load(base + ANIMAL_COSTS + animal), 1)
    animal_maximum = tl.minimum(tl.minimum(free, money // animal_cost), 128)
    maximum = tl.where(is_animal, animal_maximum, maximum)
    hires = tl.maximum(0, tl.load(base + 10))
    hire_cost = tl.load(base + 12) * _fibonacci(tl.minimum(hires, 31))
    maximum = tl.where(
        token == 65,
        (money >= hire_cost) & (tl.load(base + 1) < UNIT_LIMIT),
        maximum,
    )
    land_level = tl.load(base + 11)
    land_cost = tl.load(base + LAND_COSTS + tl.maximum(0, tl.minimum(land_level, 2)))
    maximum = tl.where(token == 66, (land_level < 3) & (money >= land_cost), maximum)
    maximum = tl.where((token == 44) | (token == 45), 1, maximum)

    one = maximum > 0
    pickup_one = pickup_quantity & one
    placed_in_shed = place_quantity & one & ~animal_place
    shed_delta = tl.where(
        (is_sell & one) | pickup_one,
        -1,
        tl.where(((is_product | is_animal) & one) | placed_in_shed, 1, 0),
    )
    relevant_after = tl.where(
        pickup_quantity,
        shed - pickup_one.to(tl.int32),
        tl.where(place_quantity, shed + placed_in_shed.to(tl.int32), 0),
    )
    relevant_after = tl.where(is_sell, sell_count - one.to(tl.int32), relevant_after)
    seed_count = tl.load(base + SEEDS + seed)
    relevant_after = tl.where(is_seed, seed_count + one.to(tl.int32), relevant_after)
    product_count = tl.load(base + SHED + product)
    relevant_after = tl.where(is_product, product_count + one.to(tl.int32), relevant_after)
    animal_count = tl.load(base + SHED + 9 + animal)
    relevant_after = tl.where(is_animal, animal_count + one.to(tl.int32), relevant_after)
    fixed_cost = tl.where(is_seed, seed_cost, animal_cost)
    price = tl.where(
        is_sell,
        sell_price,
        tl.where(is_product, buy_price, tl.where(is_seed | is_animal, fixed_cost, 0.0)),
    )
    next_price = tl.where(
        is_sell,
        sell_next,
        tl.where(is_product, buy_next, tl.where(is_seed | is_animal, fixed_cost, 0.0)),
    )
    next_hire = tl.load(base + 12) * _fibonacci(tl.minimum(hires + 1, 31))
    price = tl.where(
        token == 65,
        hire_cost,
        tl.where(token == 66, tl.where(land_level < 3, land_cost, 0), price),
    )
    next_land_level = land_level + 1
    next_land_cost = tl.load(base + LAND_COSTS + tl.maximum(0, tl.minimum(next_land_level, 2)))
    next_price = tl.where(
        token == 65,
        next_hire,
        tl.where(token == 66, tl.where(next_land_level < 3, next_land_cost, 0), next_price),
    )
    cash_delta = tl.where(
        is_sell & one,
        sell_price,
        tl.where((is_product | is_seed | is_animal) & one, -price, 0.0),
    )
    cash_delta = tl.where(((token == 65) | (token == 66)) & one, -price, cash_delta)
    market_delta = tl.where(is_sell & one & (sell_price > 1.0), 1, 0)
    market_delta = tl.where(is_product & one, -1, market_delta)
    conditional = inherited_conditional | is_sell | is_product
    quantity_dependent = pickup_quantity | place_quantity | ((token >= 46) & (token <= 64))
    resulting_free = tl.maximum(capacity - shed_total - shed_delta, 0).to(tl.float32)
    resulting_free /= tl.maximum(capacity, 1).to(tl.float32)

    values = (
        phase_valid.to(tl.float32),
        phase_valid.to(tl.float32),
        (phase_valid & one).to(tl.float32),
        (~conditional).to(tl.float32),
        conditional.to(tl.float32),
        quantity_dependent.to(tl.float32),
        _signed_log(maximum),
        one.to(tl.float32),
        _signed_log(cash_delta),
        _signed_log(money + cash_delta),
        _signed_log(shed_delta),
        _signed_log(relevant_after),
        _signed_log(market_delta),
        _signed_log(price),
        _signed_log(next_price),
        tl.minimum(resulting_free, 1.0),
        ((token == 65) & one).to(tl.float32),
        ((token == 66) & one).to(tl.float32) * 0.25,
        (token < 44).to(tl.float32),
        (token >= 44).to(tl.float32),
    )
    for feature in tl.static_range(0, _CANDIDATE_FEATURES):
        tl.store(
            out + token * _CANDIDATE_FEATURES + feature,
            values[feature],
            mask=valid,
        )


@triton.jit
def _buy_candidate_kernel(
    state,
    phases,
    output,
    PHASE_STRIDE: tl.constexpr,
    STATE_WIDTH: tl.constexpr,
    SHED: tl.constexpr,
    MARKET_INVENTORY: tl.constexpr,
    MARKET_BASE_MILLI: tl.constexpr,
    MARKET_I0: tl.constexpr,
    MARKET_T_MILLI: tl.constexpr,
    MARKET_BELOW_FUNCTION: tl.constexpr,
    MARKET_BELOW_TARGET_MILLI: tl.constexpr,
    MARKET_ABOVE_FUNCTION: tl.constexpr,
    MARKET_ABOVE_TARGET_MILLI: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    choice = tl.program_id(1)
    lane = tl.arange(0, BLOCK)
    base = state + row * STATE_WIDTH
    token = 60 + choice
    product = tl.where(choice == 0, 0, 8)
    inventory = tl.load(base + MARKET_INVENTORY + product)
    price = _market_price(
        base,
        product,
        inventory - lane - 1,
        MARKET_BASE_MILLI,
        MARKET_I0,
        MARKET_T_MILLI,
        MARKET_BELOW_FUNCTION,
        MARKET_BELOW_TARGET_MILLI,
        MARKET_ABOVE_FUNCTION,
        MARKET_ABOVE_TARGET_MILLI,
    )
    cumulative = tl.cumsum(price, axis=0)
    money = tl.maximum(tl.load(base + 9), 0)
    capacity = tl.load(base + 5)
    shed_total = tl.load(base + 8)
    free = tl.maximum(capacity - shed_total, 0)
    affordable = tl.sum((cumulative <= money).to(tl.int32), axis=0)
    maximum = tl.minimum(tl.minimum(free, affordable), _MAXIMUM_QUANTITY)
    one = maximum > 0
    first = tl.sum(tl.where(lane == 0, price, 0.0), axis=0)
    second = tl.sum(tl.where(lane == 1, price, 0.0), axis=0)
    phase_valid = tl.load(phases + row * PHASE_STRIDE) == 1
    relevant = tl.load(base + SHED + product) + one.to(tl.int32)
    cash_delta = tl.where(one, -first, 0.0)
    resulting_free = tl.maximum(capacity - shed_total - one.to(tl.int32), 0).to(tl.float32)
    resulting_free /= tl.maximum(capacity, 1).to(tl.float32)
    out = output + (row * _ACTION_TOKENS + token) * _CANDIDATE_FEATURES
    values = (
        phase_valid.to(tl.float32),
        phase_valid.to(tl.float32),
        (phase_valid & one).to(tl.float32),
        0.0,
        1.0,
        1.0,
        _signed_log(maximum),
        one.to(tl.float32),
        _signed_log(cash_delta),
        _signed_log(money + cash_delta),
        _signed_log(one.to(tl.int32)),
        _signed_log(relevant),
        _signed_log(-one.to(tl.int32)),
        _signed_log(first),
        _signed_log(second),
        tl.minimum(resulting_free, 1.0),
        0.0,
        0.0,
        0.0,
        1.0,
    )
    for feature in tl.static_range(0, _CANDIDATE_FEATURES):
        tl.store(out + feature, values[feature])


def candidate_features(state: Tensor, phases: Tensor, layout: EconomicStateLayout) -> Tensor:
    """Compile all action consequences with two fused launches."""
    _validate_state(state, layout)
    if phases.shape != (state.shape[0],) or phases.dtype != torch.int64:
        raise ValueError("economic CUDA phases must be one int64 value per row")
    output = torch.empty(
        (state.shape[0], ACTION_TOKENS, CANDIDATE_FEATURES),
        dtype=torch.float32,
        device=state.device,
    )
    common = _layout_arguments(layout)
    _candidate_kernel[(state.shape[0],)](
        state,
        phases,
        output,
        PHASE_STRIDE=phases.stride(0),
        UNIT_LIMIT=layout.unit_limit,
        BOARD_SIZE=layout.board_size,
        POSITIONS=layout.positions,
        INVENTORIES=layout.inventories,
        SHED=layout.shed,
        SEEDS=layout.seeds,
        MARKET_INVENTORY=layout.market_inventory,
        SEED_COSTS=layout.seed_costs,
        ANIMAL_COSTS=layout.animal_costs,
        LAND_COSTS=layout.land_costs,
        TILES=layout.tiles,
        TILE_FIELDS=layout.tile_fields,
        BLOCK=128,
        num_warps=4,
        **common,
    )
    _buy_candidate_kernel[(state.shape[0], 2)](
        state,
        phases,
        output,
        PHASE_STRIDE=phases.stride(0),
        SHED=layout.shed,
        MARKET_INVENTORY=layout.market_inventory,
        BLOCK=128,
        num_warps=4,
        **common,
    )
    return output


__all__ = ["candidate_features"]
