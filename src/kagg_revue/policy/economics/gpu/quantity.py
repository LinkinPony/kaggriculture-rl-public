"""Fused CUDA compilation of per-quantity economic consequences."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor

from kagg_revue.policy.economics.gpu.common import (
    _layout_arguments,
    _market_price,
    _signed_log,
    _validate_state,
)
from kagg_revue.policy.economics.layout import (
    MAXIMUM_QUANTITY,
    QUANTITY_FEATURES,
    EconomicStateLayout,
)

_MAXIMUM_QUANTITY = tl.constexpr(128)
_QUANTITY_FEATURES = tl.constexpr(12)


@triton.jit
def _quantity_kernel(
    state,
    tokens,
    output,
    TOKEN_STRIDE: tl.constexpr,
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
    TILES: tl.constexpr,
    TILE_FIELDS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    lane = tl.arange(0, BLOCK)
    q = lane + 1
    base = state + row * STATE_WIDTH
    token = tl.maximum(0, tl.minimum(tl.load(tokens + row * TOKEN_STRIDE), 66))
    money = tl.maximum(tl.load(base + 9), 0)
    capacity = tl.load(base + 5)
    shed_total = tl.load(base + 8)
    free = tl.maximum(capacity - shed_total, 0)
    is_sell = (token >= 46) & (token <= 54)
    is_seed = (token >= 55) & (token <= 59)
    is_product = (token == 60) | (token == 61)
    is_animal = (token >= 62) & (token <= 64)
    market_quantity = is_sell | is_seed | is_product | is_animal
    unit_quantity = ((token >= 5) & (token < 17)) | ((token >= 18) & (token < 30))
    product = tl.where(token == 61, 8, token - 60)
    relevant = tl.where(
        is_sell,
        token - 46,
        tl.where(
            is_seed,
            token - 55,
            tl.where(is_product, product, tl.where(is_animal, token - 53, 0)),
        ),
    )
    relevant = tl.maximum(0, tl.minimum(relevant, 11))
    curve_product = tl.maximum(0, tl.minimum(tl.where(is_sell, relevant, product), 8))
    market_inventory = tl.load(base + MARKET_INVENTORY + curve_product)
    sell_price = _market_price(
        base,
        curve_product,
        market_inventory + lane,
        MARKET_BASE_MILLI,
        MARKET_I0,
        MARKET_T_MILLI,
        MARKET_BELOW_FUNCTION,
        MARKET_BELOW_TARGET_MILLI,
        MARKET_ABOVE_FUNCTION,
        MARKET_ABOVE_TARGET_MILLI,
    )
    buy_price = _market_price(
        base,
        curve_product,
        market_inventory - lane - 1,
        MARKET_BASE_MILLI,
        MARKET_I0,
        MARKET_T_MILLI,
        MARKET_BELOW_FUNCTION,
        MARKET_BELOW_TARGET_MILLI,
        MARKET_ABOVE_FUNCTION,
        MARKET_ABOVE_TARGET_MILLI,
    )
    sell_cumulative = tl.cumsum(sell_price, axis=0)
    buy_cumulative = tl.cumsum(buy_price, axis=0)
    affordable = tl.sum((buy_cumulative <= money).to(tl.int32), axis=0)
    shed = tl.maximum(tl.load(base + SHED + relevant), 0)
    seed = tl.maximum(0, tl.minimum(token - 55, 4))
    seed_cost = tl.maximum(tl.load(base + SEED_COSTS + seed), 1)
    animal = tl.maximum(0, tl.minimum(token - 62, 2))
    animal_cost = tl.maximum(tl.load(base + ANIMAL_COSTS + animal), 1)
    market_maximum = tl.where(
        is_sell,
        shed,
        tl.where(
            is_seed,
            money // seed_cost,
            tl.where(
                is_product,
                tl.minimum(free, affordable),
                tl.minimum(free, money // animal_cost),
            ),
        ),
    )

    unit_index = tl.maximum(0, tl.minimum(tl.load(base + 2), UNIT_LIMIT - 1))
    unit_item = tl.where(token < 17, token - 5, token - 18)
    unit_item = tl.maximum(0, tl.minimum(unit_item, 11))
    unit_shed = tl.maximum(tl.load(base + SHED + unit_item), 0)
    carried = tl.maximum(tl.load(base + INVENTORIES + unit_index * 12 + unit_item), 0)
    x = tl.load(base + POSITIONS + unit_index * 2)
    y = tl.load(base + POSITIONS + unit_index * 2 + 1)
    half = BOARD_SIZE // 2
    adjacent = ((x == half - 1) | (x == half)) & ((y == half - 1) | (y == half))
    tile = base + TILES + (y * BOARD_SIZE + x) * TILE_FIELDS
    tile_kind = tl.load(tile)
    tile_structure = tl.load(tile + 6)
    tile_animal = tl.load(tile + 7)
    pickup = (token >= 5) & (token < 17)
    place = (token >= 18) & (token < 30)
    animal_place = (
        place
        & (unit_item >= 9)
        & (tile_kind == 4)
        & (tile_animal == 0)
        & (tile_structure == (unit_item != 9))
    )
    place_maximum = tl.where(
        animal_place,
        tl.minimum(carried, 1),
        tl.where(adjacent, tl.minimum(carried, free), 0),
    )
    unit_maximum = tl.where(
        pickup,
        tl.where(adjacent, unit_shed, 0),
        tl.where(place, place_maximum, 0),
    )
    maximum = tl.where(market_quantity, market_maximum, unit_maximum)
    maximum = tl.maximum(0, tl.minimum(maximum, _MAXIMUM_QUANTITY))
    committed = tl.minimum(q, maximum)
    cap_lane = maximum - 1
    sell_cap = tl.sum(tl.where(lane == cap_lane, sell_cumulative, 0.0), axis=0)
    buy_cap = tl.sum(tl.where(lane == cap_lane, buy_cumulative, 0.0), axis=0)
    sell_cash = tl.where(q <= maximum, sell_cumulative, sell_cap)
    buy_cash = tl.where(q <= maximum, buy_cumulative, buy_cap)
    sell_cash = tl.where(maximum > 0, sell_cash, 0.0)
    buy_cash = tl.where(maximum > 0, buy_cash, 0.0)
    fixed_cost = tl.where(is_seed, seed_cost, animal_cost).to(tl.float32)
    cash_delta = tl.where(
        is_sell,
        sell_cash,
        tl.where(
            is_product,
            -buy_cash,
            tl.where(is_seed | is_animal, -fixed_cost * committed, 0.0),
        ),
    )
    unit_place_to_shed = place & ~animal_place
    shed_delta = tl.where(
        is_sell | pickup,
        -committed,
        tl.where(is_product | is_animal | unit_place_to_shed, committed, 0),
    )
    resolved_relevant = tl.where(unit_quantity, unit_item, relevant)
    relevant_before = tl.where(
        is_seed,
        tl.load(base + SEEDS + tl.minimum(resolved_relevant, 4)),
        tl.load(base + SHED + resolved_relevant),
    )
    relevant_after = tl.where(
        is_seed,
        relevant_before + committed,
        relevant_before + shed_delta,
    )
    shed_after = shed_total + shed_delta
    sell_units = tl.cumsum((sell_price > 1.0).to(tl.int32), axis=0)
    sell_units_cap = tl.sum(tl.where(lane == cap_lane, sell_units, 0), axis=0)
    sell_market_delta = tl.where(q <= maximum, sell_units, sell_units_cap)
    sell_market_delta = tl.where(maximum > 0, sell_market_delta, 0)
    market_delta = tl.where(is_sell, sell_market_delta, tl.where(is_product, -committed, 0))
    marginal = tl.where(
        is_sell,
        sell_price,
        tl.where(is_product, buy_price, tl.where(is_seed | is_animal, fixed_cost, 0.0)),
    )
    present = market_quantity | unit_quantity
    conditional = (tl.load(base + 13) != 0) | is_sell | is_product
    free_ratio = tl.maximum(capacity - shed_after, 0).to(tl.float32)
    free_ratio /= tl.maximum(capacity, 1).to(tl.float32)
    out = output + row * _MAXIMUM_QUANTITY * _QUANTITY_FEATURES
    values = (
        present.to(tl.float32),
        tl.log(1.0 + q.to(tl.float32)) / 4.859812404361672,
        _signed_log(committed),
        (committed == q).to(tl.float32),
        (committed > 0).to(tl.float32),
        conditional.to(tl.float32),
        _signed_log(cash_delta),
        _signed_log(money + cash_delta),
        _signed_log(relevant_after),
        tl.minimum(free_ratio, 1.0),
        _signed_log(market_delta),
        _signed_log(marginal),
    )
    for feature in tl.static_range(0, _QUANTITY_FEATURES):
        tl.store(out + lane * _QUANTITY_FEATURES + feature, values[feature])


def quantity_features(state: Tensor, tokens: Tensor, layout: EconomicStateLayout) -> Tensor:
    """Compile every exact quantity consequence with one fused launch."""
    _validate_state(state, layout)
    if tokens.shape != (state.shape[0],) or tokens.dtype != torch.int64:
        raise ValueError("economic CUDA tokens must be one int64 value per row")
    output = torch.empty(
        (state.shape[0], MAXIMUM_QUANTITY, QUANTITY_FEATURES),
        dtype=torch.float32,
        device=state.device,
    )
    _quantity_kernel[(state.shape[0],)](
        state,
        tokens,
        output,
        TOKEN_STRIDE=tokens.stride(0),
        UNIT_LIMIT=layout.unit_limit,
        BOARD_SIZE=layout.board_size,
        POSITIONS=layout.positions,
        INVENTORIES=layout.inventories,
        SHED=layout.shed,
        SEEDS=layout.seeds,
        MARKET_INVENTORY=layout.market_inventory,
        SEED_COSTS=layout.seed_costs,
        ANIMAL_COSTS=layout.animal_costs,
        TILES=layout.tiles,
        TILE_FIELDS=layout.tile_fields,
        BLOCK=128,
        num_warps=4,
        **_layout_arguments(layout),
    )
    return output


__all__ = ["quantity_features"]
