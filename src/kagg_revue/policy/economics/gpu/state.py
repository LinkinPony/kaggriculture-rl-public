"""Fused CUDA compilation of turn and action-prefix economic facts."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor

from kagg_revue.policy.economics.gpu.common import (
    _fibonacci,
    _signed_log,
    _validate_state,
)
from kagg_revue.policy.economics.layout import EconomicStateLayout


@triton.jit
def _turn_kernel(
    state,
    global_features,
    output,
    GLOBAL_STRIDE: tl.constexpr,
    STATE_WIDTH: tl.constexpr,
    UNIT_LIMIT: tl.constexpr,
    SHED: tl.constexpr,
    SEEDS: tl.constexpr,
    MARKET_INVENTORY: tl.constexpr,
    MARKET_PRICES: tl.constexpr,
    LAND_COSTS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    feature = tl.arange(0, BLOCK)
    valid = feature < 50
    base = state + row * STATE_WIDTH
    global_base = global_features + row * GLOBAL_STRIDE
    capacity = tl.maximum(tl.load(base + 5), 1).to(tl.float32)
    shed_total = tl.load(base + 8).to(tl.float32)
    money = tl.load(base + 9)
    hires = tl.maximum(tl.load(base + 10), 0)
    land_level = tl.load(base + 11)
    next_hire = tl.load(base + 12) * _fibonacci(tl.minimum(hires, 31))
    land_cost = tl.load(base + LAND_COSTS + tl.maximum(0, tl.minimum(land_level, 2)))
    next_land = tl.where(land_level < 3, land_cost, 0)
    value = tl.zeros((BLOCK,), tl.float32)
    value = tl.where(feature == 0, 1.0, value)
    value = tl.where(feature == 1, tl.load(global_base + 2), value)
    value = tl.where(feature == 2, tl.load(global_base + 3), value)
    value = tl.where(feature == 3, tl.load(global_base + 4), value)
    value = tl.where(feature == 4, _signed_log(money), value)
    value = tl.where(feature == 5, tl.load(global_base + 8), value)
    value = tl.where(feature == 6, tl.load(global_base + 9), value)
    value = tl.where(feature == 7, tl.minimum(tl.maximum(shed_total / capacity, 0.0), 2.0), value)
    free_ratio = tl.minimum(tl.maximum((capacity - shed_total) / capacity, 0.0), 1.0)
    value = tl.where(feature == 8, free_ratio, value)
    shed_item = tl.maximum(0, tl.minimum(feature - 9, 11))
    shed_value = tl.load(base + SHED + shed_item)
    value = tl.where((feature >= 9) & (feature < 21), _signed_log(shed_value), value)
    crop = tl.maximum(0, tl.minimum(feature - 21, 4))
    seed_value = tl.load(base + SEEDS + crop)
    value = tl.where((feature >= 21) & (feature < 26), _signed_log(seed_value), value)
    product = tl.maximum(0, tl.minimum(feature - 26, 8))
    inventory = tl.load(base + MARKET_INVENTORY + product)
    value = tl.where((feature >= 26) & (feature < 35), _signed_log(inventory), value)
    price_product = tl.maximum(0, tl.minimum(feature - 35, 8))
    price = tl.load(base + MARKET_PRICES + price_product)
    value = tl.where((feature >= 35) & (feature < 44), _signed_log(price), value)
    value = tl.where(
        feature == 44,
        tl.minimum(tl.maximum(tl.load(base + 1).to(tl.float32) / 16.0, 0.0), 2.0),
        value,
    )
    value = tl.where(feature == 45, _signed_log(hires), value)
    value = tl.where(
        feature == 46,
        tl.minimum(tl.maximum(land_level.to(tl.float32) / 3.0, 0.0), 1.0),
        value,
    )
    value = tl.where(feature == 47, _signed_log(next_hire), value)
    value = tl.where(feature == 48, _signed_log(next_land), value)
    value = tl.where(
        feature == 49,
        tl.minimum(tl.maximum(tl.load(base + 6).to(tl.float32) / 10.0, 0.0), 2.0),
        value,
    )
    tl.store(output + row * 50 + feature, value, mask=valid)


@triton.jit
def _prefix_kernel(
    state,
    phases,
    output,
    PHASE_STRIDE: tl.constexpr,
    STATE_WIDTH: tl.constexpr,
    UNIT_LIMIT: tl.constexpr,
    SHED: tl.constexpr,
    SEEDS: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    feature = tl.arange(0, BLOCK)
    valid = feature < 30
    base = state + row * STATE_WIDTH
    phase = tl.load(phases + row * PHASE_STRIDE)
    capacity = tl.maximum(tl.load(base + 5), 1).to(tl.float32)
    shed_total = tl.load(base + 8).to(tl.float32)
    unit_count = tl.maximum(tl.load(base + 1), 1).to(tl.float32)
    unit_slot = tl.load(base + 2).to(tl.float32)
    order_capacity = tl.maximum(tl.load(base + 6), 1).to(tl.float32)
    order_slot = tl.load(base + 3).to(tl.float32)
    value = tl.zeros((BLOCK,), tl.float32)
    value = tl.where(feature == 0, 1.0, value)
    value = tl.where(feature == 1, (phase == 0).to(tl.float32), value)
    value = tl.where(feature == 2, (phase == 1).to(tl.float32), value)
    value = tl.where(
        feature == 3,
        tl.minimum(tl.maximum(unit_slot / unit_count, 0.0), 1.0),
        value,
    )
    value = tl.where(
        feature == 4,
        tl.minimum(tl.maximum((unit_count - unit_slot) / unit_count, 0.0), 1.0),
        value,
    )
    value = tl.where(
        feature == 5,
        tl.minimum(tl.maximum(order_slot / order_capacity, 0.0), 1.0),
        value,
    )
    value = tl.where(
        feature == 6,
        tl.minimum(tl.maximum((order_capacity - order_slot) / order_capacity, 0.0), 1.0),
        value,
    )
    value = tl.where(feature == 7, _signed_log(tl.load(base + 9)), value)
    value = tl.where(
        feature == 8,
        tl.minimum(tl.maximum(shed_total / capacity, 0.0), 2.0),
        value,
    )
    value = tl.where(
        feature == 9,
        tl.minimum(tl.maximum((capacity - shed_total) / capacity, 0.0), 1.0),
        value,
    )
    item = tl.maximum(0, tl.minimum(feature - 10, 11))
    shed_value = tl.load(base + SHED + item)
    value = tl.where((feature >= 10) & (feature < 22), _signed_log(shed_value), value)
    crop = tl.maximum(0, tl.minimum(feature - 22, 4))
    seed_value = tl.load(base + SEEDS + crop)
    value = tl.where((feature >= 22) & (feature < 27), _signed_log(seed_value), value)
    committed = tl.load(base + 2) + tl.load(base + 3)
    value = tl.where(
        feature == 27,
        tl.minimum(tl.maximum(committed.to(tl.float32) / 26.0, 0.0), 1.0),
        value,
    )
    conditional = tl.load(base + 13) != 0
    value = tl.where(feature == 28, (~conditional).to(tl.float32), value)
    value = tl.where(feature == 29, conditional.to(tl.float32), value)
    tl.store(output + row * 30 + feature, value, mask=valid)


def turn_features(
    state: Tensor,
    global_features: Tensor,
    layout: EconomicStateLayout,
) -> Tensor:
    """Compile state-level economic facts with one fused launch."""
    _validate_state(state, layout)
    if global_features.shape != (state.shape[0], 82):
        raise ValueError("economic CUDA global observations have the wrong shape")
    output = torch.empty((state.shape[0], 50), dtype=torch.float32, device=state.device)
    _turn_kernel[(state.shape[0],)](
        state,
        global_features,
        output,
        GLOBAL_STRIDE=global_features.stride(0),
        STATE_WIDTH=layout.width,
        UNIT_LIMIT=layout.unit_limit,
        SHED=layout.shed,
        SEEDS=layout.seeds,
        MARKET_INVENTORY=layout.market_inventory,
        MARKET_PRICES=layout.market_prices,
        LAND_COSTS=layout.land_costs,
        BLOCK=64,
        num_warps=2,
    )
    return output


def prefix_features(state: Tensor, phases: Tensor, layout: EconomicStateLayout) -> Tensor:
    """Compile current-prefix economic facts with one fused launch."""
    _validate_state(state, layout)
    if phases.shape != (state.shape[0],) or phases.dtype != torch.int64:
        raise ValueError("economic CUDA phases must be one int64 value per row")
    output = torch.empty((state.shape[0], 30), dtype=torch.float32, device=state.device)
    _prefix_kernel[(state.shape[0],)](
        state,
        phases,
        output,
        PHASE_STRIDE=phases.stride(0),
        STATE_WIDTH=layout.width,
        UNIT_LIMIT=layout.unit_limit,
        SHED=layout.shed,
        SEEDS=layout.seeds,
        BLOCK=32,
        num_warps=1,
    )
    return output


__all__ = ["prefix_features", "turn_features"]
