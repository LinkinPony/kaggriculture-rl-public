"""Fused CUDA projection of selected market orders."""

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
    _validate_state,
)
from kagg_revue.policy.economics.layout import EconomicStateLayout


@triton.jit
def _project_market_kernel(
    state,
    tokens,
    quantities,
    phases,
    active,
    TOKEN_STRIDE: tl.constexpr,
    QUANTITY_STRIDE: tl.constexpr,
    PHASE_STRIDE: tl.constexpr,
    ACTIVE_STRIDE: tl.constexpr,
    STATE_WIDTH: tl.constexpr,
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
    UNIT_LIMIT: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    lane = tl.arange(0, BLOCK)
    base = state + row * STATE_WIDTH
    token = tl.load(tokens + row * TOKEN_STRIDE)
    requested = tl.maximum(0, tl.load(quantities + row * QUANTITY_STRIDE))
    market = (tl.load(active + row * ACTIVE_STRIDE) != 0) & (
        tl.load(phases + row * PHASE_STRIDE) == 1
    )
    money = tl.maximum(tl.load(base + 9), 0)
    capacity = tl.load(base + 5)
    shed_total = tl.load(base + 8)
    free = tl.maximum(capacity - shed_total, 0)
    is_sell = (token >= 46) & (token <= 54)
    is_seed = (token >= 55) & (token <= 59)
    is_product = (token == 60) | (token == 61)
    is_animal = (token >= 62) & (token <= 64)
    is_hire = token == 65
    is_land = token == 66
    product = tl.where(token == 61, 8, token - 60)
    item = tl.where(
        is_sell,
        token - 46,
        tl.where(is_seed, token - 55, tl.where(is_product, product, token - 53)),
    )
    item = tl.maximum(0, tl.minimum(item, 11))
    shed_count = tl.maximum(tl.load(base + SHED + item), 0)
    seed = tl.maximum(0, tl.minimum(token - 55, 4))
    seed_cost = tl.maximum(tl.load(base + SEED_COSTS + seed), 1)
    animal = tl.maximum(0, tl.minimum(token - 62, 2))
    animal_cost = tl.maximum(tl.load(base + ANIMAL_COSTS + animal), 1)
    hires = tl.maximum(0, tl.load(base + 10))
    hire_cost = tl.load(base + 12) * _fibonacci(tl.minimum(hires, 31))
    land_level = tl.load(base + 11)
    land_cost = tl.load(base + LAND_COSTS + tl.maximum(0, tl.minimum(land_level, 2)))
    curve_product = tl.maximum(0, tl.minimum(tl.where(is_sell, item, product), 8))
    inventory = tl.load(base + MARKET_INVENTORY + curve_product)
    sell_price = _market_price(
        base,
        curve_product,
        inventory + lane,
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
        inventory - lane - 1,
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
    maximum = tl.where(
        is_sell,
        shed_count,
        tl.where(
            is_seed,
            money // seed_cost,
            tl.where(
                is_product,
                tl.minimum(free, affordable),
                tl.where(
                    is_animal,
                    tl.minimum(free, money // animal_cost),
                    tl.where(
                        is_hire,
                        (money >= hire_cost) & (tl.load(base + 1) < UNIT_LIMIT),
                        tl.where(is_land, (land_level < 3) & (money >= land_cost), 0),
                    ),
                ),
            ),
        ),
    )
    # Only seeds can exceed the 128-lane quote block.  Their price is fixed,
    # so keeping their full contract quantity does not require a wider curve.
    maximum = tl.maximum(0, tl.where(is_seed, maximum, tl.minimum(maximum, 128)))
    effective_request = tl.where(is_hire | is_land, 1, requested)
    committed = tl.minimum(effective_request, maximum)
    selected_lane = committed - 1
    sell_cash = tl.sum(tl.where(lane == selected_lane, sell_cumulative, 0.0), axis=0)
    buy_cash = tl.sum(tl.where(lane == selected_lane, buy_cumulative, 0.0), axis=0)
    fixed_cost = tl.where(
        is_seed,
        seed_cost,
        tl.where(is_animal, animal_cost, tl.where(is_hire, hire_cost, land_cost)),
    )
    cash_delta = tl.where(
        is_sell,
        sell_cash,
        tl.where(is_product, -buy_cash, -fixed_cost * committed),
    )
    shed_delta = tl.where(is_sell, -committed, tl.where(is_product | is_animal, committed, 0))
    seed_delta = tl.where(is_seed, committed, 0)
    sold_units = tl.cumsum((sell_price > 1.0).to(tl.int32), axis=0)
    sold_inventory = tl.sum(tl.where(lane == selected_lane, sold_units, 0), axis=0)
    market_delta = tl.where(is_sell, sold_inventory, tl.where(is_product, -committed, 0))
    consequence = is_sell | is_seed | is_product | is_animal | is_hire | is_land
    applied = market & consequence & (committed > 0)
    tl.store(base + 13, 1, mask=market & (is_sell | is_product))
    tl.store(base + 9, tl.load(base + 9) + cash_delta.to(tl.int32), mask=applied)
    old_shed = tl.load(base + SHED + item)
    tl.store(base + SHED + item, old_shed + shed_delta, mask=applied)
    tl.store(base + 8, shed_total + shed_delta, mask=applied)
    old_seed = tl.load(base + SEEDS + seed)
    tl.store(base + SEEDS + seed, old_seed + seed_delta, mask=applied & (seed_delta > 0))
    market_product = tl.maximum(0, tl.minimum(tl.where(token == 61, 8, item), 8))
    old_market = tl.load(base + MARKET_INVENTORY + market_product)
    tl.store(
        base + MARKET_INVENTORY + market_product,
        old_market + market_delta,
        mask=applied & (market_delta != 0),
    )
    tl.store(base + 10, hires + 1, mask=applied & is_hire)
    tl.store(base + 11, land_level + 1, mask=applied & is_land)


def project_market_selection(
    state: Tensor,
    tokens: Tensor,
    quantities: Tensor,
    phases: Tensor,
    active: Tensor,
    layout: EconomicStateLayout,
) -> None:
    """Apply the selected market projection in place with one fused launch."""
    _validate_state(state, layout)
    batch = state.shape[0]
    if tokens.shape != (batch,) or quantities.shape != (batch,):
        raise ValueError("economic CUDA selections must have one value per row")
    if tokens.dtype != torch.int64 or quantities.dtype != torch.int64:
        raise ValueError("economic CUDA selections must use int64")
    if phases.shape != (batch,) or phases.dtype != torch.int64:
        raise ValueError("economic CUDA phases must use one int64 value per row")
    if active.shape != (batch,) or active.dtype != torch.bool:
        raise ValueError("economic CUDA active mask must use one bool per row")
    _project_market_kernel[(batch,)](
        state,
        tokens,
        quantities,
        phases,
        active,
        TOKEN_STRIDE=tokens.stride(0),
        QUANTITY_STRIDE=quantities.stride(0),
        PHASE_STRIDE=phases.stride(0),
        ACTIVE_STRIDE=active.stride(0),
        SHED=layout.shed,
        SEEDS=layout.seeds,
        MARKET_INVENTORY=layout.market_inventory,
        SEED_COSTS=layout.seed_costs,
        ANIMAL_COSTS=layout.animal_costs,
        LAND_COSTS=layout.land_costs,
        UNIT_LIMIT=layout.unit_limit,
        BLOCK=128,
        num_warps=4,
        **_layout_arguments(layout),
    )


__all__ = ["project_market_selection"]
