"""Shared primitives for fused economic CUDA kernels."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor
from triton.language.extra import libdevice  # type: ignore[import-untyped]

from kagg_revue.policy.economics.layout import EconomicStateLayout


@triton.jit
def _signed_log(value):
    value = value.to(tl.float32)
    sign = tl.where(value > 0.0, 1.0, tl.where(value < 0.0, -1.0, 0.0))
    return sign * tl.log(1.0 + tl.abs(value)) / 12.0


@triton.jit
def _fibonacci(index):
    left = 1
    right = 1
    result = 1
    for position in tl.static_range(0, 32):
        result = tl.where(index == position, left, result)
        left, right = right, left + right
    return result


@triton.jit
def _market_shape(value, threshold, kind):
    value = tl.maximum(value, 0.0)
    threshold = tl.maximum(threshold, 1.0e-6)
    scaled = value / threshold
    excess = tl.maximum(scaled - 1.0, 0.0)
    hinge = scaled + 8.0 * excess * excess
    return tl.where(
        kind == 0,
        value,
        tl.where(
            kind == 1,
            value * value,
            tl.where(
                kind == 2,
                libdevice.sqrt(value),
                tl.where(
                    kind == 3,
                    libdevice.log(1.0 + value),
                    tl.where(kind == 4, libdevice.log10(1.0 + value), hinge),
                ),
            ),
        ),
    )


@triton.jit
def _market_price(
    base,
    product,
    inventory,
    MARKET_BASE_MILLI: tl.constexpr,
    MARKET_I0: tl.constexpr,
    MARKET_T_MILLI: tl.constexpr,
    MARKET_BELOW_FUNCTION: tl.constexpr,
    MARKET_BELOW_TARGET_MILLI: tl.constexpr,
    MARKET_ABOVE_FUNCTION: tl.constexpr,
    MARKET_ABOVE_TARGET_MILLI: tl.constexpr,
):
    product = tl.maximum(0, tl.minimum(product, 8))
    market_base = tl.load(base + MARKET_BASE_MILLI + product).to(tl.float64) / 1000.0
    target_inventory = tl.load(base + MARKET_I0 + product).to(tl.float64)
    threshold = tl.load(base + MARKET_T_MILLI + product).to(tl.float64) / 1000.0
    below_kind = tl.load(base + MARKET_BELOW_FUNCTION + product)
    below_target = tl.load(base + MARKET_BELOW_TARGET_MILLI + product).to(tl.float64) / 1000.0
    above_kind = tl.load(base + MARKET_ABOVE_FUNCTION + product)
    above_target = tl.load(base + MARKET_ABOVE_TARGET_MILLI + product).to(tl.float64) / 1000.0
    inventory = inventory.to(tl.float64)
    below_distance = tl.maximum(target_inventory - inventory, 0.0)
    above_distance = tl.maximum(inventory - target_inventory, 0.0)
    below_denominator = tl.maximum(
        _market_shape(threshold, threshold, below_kind),
        1.0e-6,
    )
    above_denominator = tl.maximum(
        _market_shape(threshold, threshold, above_kind),
        1.0e-6,
    )
    below_amplitude = below_target * market_base / below_denominator
    above_amplitude = above_target * market_base / above_denominator
    raw = tl.where(
        inventory < target_inventory,
        market_base + below_amplitude * _market_shape(below_distance, threshold, below_kind),
        market_base - above_amplitude * _market_shape(above_distance, threshold, above_kind),
    )
    return tl.maximum(libdevice.rint(raw), 1.0).to(tl.float32)


def _validate_state(state: Tensor, layout: EconomicStateLayout) -> None:
    if state.device.type != "cuda" or state.dtype not in {torch.int32, torch.int64}:
        raise ValueError("economic CUDA state must use int32 or int64")
    if state.shape != (state.shape[0], layout.width) or not state.is_contiguous():
        raise ValueError("economic CUDA state must use the contiguous compact ABI")


def _layout_arguments(layout: EconomicStateLayout) -> dict[str, int]:
    return {
        "STATE_WIDTH": layout.width,
        "MARKET_BASE_MILLI": layout.market_base_milli,
        "MARKET_I0": layout.market_i0,
        "MARKET_T_MILLI": layout.market_t_milli,
        "MARKET_BELOW_FUNCTION": layout.market_below_function,
        "MARKET_BELOW_TARGET_MILLI": layout.market_below_target_milli,
        "MARKET_ABOVE_FUNCTION": layout.market_above_function,
        "MARKET_ABOVE_TARGET_MILLI": layout.market_above_target_milli,
    }


__all__ = [
    "_fibonacci",
    "_layout_arguments",
    "_market_price",
    "_signed_log",
    "_validate_state",
]
