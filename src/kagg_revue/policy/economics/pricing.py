"""Vectorized official market quotes for actor-visible projections."""

from __future__ import annotations

import torch
from torch import Tensor

from kagg_revue.policy.economics.layout import EconomicStateLayout


def fibonacci(index: Tensor) -> Tensor:
    """Return the hire-cost Fibonacci multiplier without host constants."""
    safe = index.long().clamp(0, 31)
    left = torch.ones_like(safe, dtype=torch.float32)
    right = torch.ones_like(left)
    result = torch.ones_like(left)
    for position in range(32):
        result = torch.where(safe == position, left, result)
        left, right = right, left + right
    return result


def signed_log(value: Tensor) -> Tensor:
    """Return the stable signed-log transform used by economic facts."""
    value = value.float()
    return torch.sign(value) * torch.log1p(value.abs()) / 12.0


def _shape(value: Tensor, threshold: Tensor, kind: Tensor) -> Tensor:
    value = value.clamp_min(0.0)
    threshold = threshold.clamp_min(1e-6)
    scaled = value / threshold
    hinge = scaled + 8.0 * (scaled - 1.0).clamp_min(0.0).square()
    return torch.where(
        kind == 0,
        value,
        torch.where(
            kind == 1,
            value.square(),
            torch.where(
                kind == 2,
                value.sqrt(),
                torch.where(
                    kind == 3,
                    torch.log1p(value),
                    torch.where(kind == 4, torch.log10(1.0 + value), hinge),
                ),
            ),
        ),
    )


def _parameter(
    state: Tensor,
    offset: int,
    product: Tensor,
    *,
    scale: float = 1.0,
) -> Tensor:
    if product.ndim < 1 or product.shape[0] != state.shape[0]:
        raise ValueError("market product indices must retain the state batch")
    indices = offset + product.long().clamp(0, 8)
    value = state.gather(1, indices.reshape(state.shape[0], -1)).reshape(
        product.shape
    ).double()
    return value / scale


def market_price(
    state: Tensor,
    product: Tensor,
    inventory: Tensor,
    layout: EconomicStateLayout,
) -> Tensor:
    """Evaluate banker-rounded official prices at hypothetical inventories."""
    if inventory.shape[: product.ndim] != product.shape:
        raise ValueError("market inventory and product batches differ")
    trailing = (1,) * (inventory.ndim - product.ndim)

    def parameter(offset: int, scale: float = 1.0) -> Tensor:
        value = _parameter(state, offset, product, scale=scale)
        return value.view(*value.shape, *trailing)

    base = parameter(layout.market_base_milli, 1000.0)
    target_inventory = parameter(layout.market_i0)
    threshold = parameter(layout.market_t_milli, 1000.0)
    below_kind = parameter(layout.market_below_function).long()
    below_target = parameter(layout.market_below_target_milli, 1000.0)
    above_kind = parameter(layout.market_above_function).long()
    above_target = parameter(layout.market_above_target_milli, 1000.0)
    inventory = inventory.double()
    below_distance = (target_inventory - inventory).clamp_min(0.0)
    above_distance = (inventory - target_inventory).clamp_min(0.0)
    below_denominator = _shape(threshold, threshold, below_kind).clamp_min(1e-6)
    above_denominator = _shape(threshold, threshold, above_kind).clamp_min(1e-6)
    below_amplitude = below_target * base / below_denominator
    above_amplitude = above_target * base / above_denominator
    raw = torch.where(
        inventory < target_inventory,
        base + below_amplitude * _shape(below_distance, threshold, below_kind),
        base - above_amplitude * _shape(above_distance, threshold, above_kind),
    )
    return torch.round(raw).clamp_min(1.0).float()


def market_curves(
    state: Tensor,
    product: Tensor,
    quantities: int,
    layout: EconomicStateLayout,
) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    """Return per-unit and cumulative no-opponent sell/buy quote curves."""
    indices = layout.market_inventory + product.long().clamp(0, 8)
    inventory = state.gather(1, indices.reshape(state.shape[0], -1)).reshape(
        product.shape
    ).float()
    steps = torch.arange(quantities, device=state.device, dtype=torch.float32)
    sell_inventory = inventory[..., None] + steps
    buy_inventory = inventory[..., None] - steps - 1.0
    sell_prices = market_price(state, product, sell_inventory, layout)
    buy_prices = market_price(state, product, buy_inventory, layout)
    return (
        sell_prices,
        sell_prices.cumsum(dim=-1),
        buy_prices,
        buy_prices.cumsum(dim=-1),
    )


def gather_cumulative(curve: Tensor, count: Tensor) -> Tensor:
    """Select a cumulative total at count, returning zero for no commit."""
    index = (count.long() - 1).clamp(0, curve.shape[-1] - 1)
    selected = curve.gather(-1, index.unsqueeze(-1)).squeeze(-1)
    return torch.where(count > 0, selected, torch.zeros_like(selected))


__all__ = [
    "fibonacci",
    "gather_cumulative",
    "market_curves",
    "market_price",
    "signed_log",
]
