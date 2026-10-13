"""Market-order feedback retained by the frozen Kaito v48 policy."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from kagg_revue.opponents.kaito.routes import MutableAction

_PRICE_FLOOR = 1
_MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
    "CARROT": (35, 10000, 450, "hinge", 1.0, "sqrt", 0.7),
    "TOMATO": (60, 10000, 200, "hinge", 0.4, "sqrt", 0.6),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
    "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
    "EGG": (50, 10000, 332, "hinge", 0.4, "log", 0.2),
    "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
    "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
    "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
}
_PRODUCTS = tuple(_MARKET_PARAMS)
_SHOP_PRODUCTS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _shape(name: str, value: float, scale: float | None = None) -> float:
    value = max(0.0, float(value))
    if name == "linear":
        return value
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    if name == "log10":
        return math.log10(1.0 + value)
    if name == "hinge":
        if scale is None or scale <= 0:
            return value
        normalized = value / scale
        return normalized + 8.0 * max(0.0, normalized - 1.0) ** 2
    raise ValueError(f"unknown market shape {name!r}")


def _market_price(item: str, inventory: int) -> int:
    base, equilibrium, scale, below_func, below_target, above_func, above_target = (
        _MARKET_PARAMS[item]
    )
    if inventory < equilibrium:
        amplitude = below_target * base / _shape(below_func, scale, scale)
        price = base + amplitude * _shape(below_func, equilibrium - inventory, scale)
    else:
        amplitude = above_target * base / _shape(above_func, scale, scale)
        price = base - amplitude * _shape(above_func, inventory - equilibrium, scale)
    return max(_PRICE_FLOOR, int(round(price)))


def _is_sell(order: object) -> bool:
    return (
        isinstance(order, list | tuple)
        and len(order) >= 3
        and order[0] == "SELL"
        and order[1] in _MARKET_PARAMS
    )


def _impact_score(observation: Mapping[str, Any], order: list[Any]) -> float:
    if not _is_sell(order):
        return float("-inf")
    item = str(order[1])
    try:
        quantity = max(0, int(order[2]))
    except (TypeError, ValueError):
        return 0.0
    market = _get(observation, "market", {}) or {}
    inventory = _get(market, "inventory", {}) or {}
    prices = _get(market, "prices", {}) or {}
    current_inventory = int(_get(inventory, item, 10000) or 0)
    current_quote = float(
        _get(prices, item, _market_price(item, current_inventory)) or 0
    )
    later_quote = float(_market_price(item, current_inventory + quantity))
    return float(quantity) * max(0.0, current_quote - later_quote)


def is_rebalance(configuration: Mapping[str, Any]) -> bool:
    """Return the frozen planner's official-rule market regime."""
    return int(_get(configuration, "townCenterSellInterval", 12) or 12) >= 24


def _demand_per_day(
    observation: Mapping[str, Any],
    configuration: Mapping[str, Any],
) -> dict[str, float]:
    town = _get(observation, "town", {}) or {}
    shops = list(_get(town, "unlocked_shops", []) or [])
    step = int(_get(observation, "step", 0) or 0)
    day = int(_get(observation, "day", step // 24) or 0)
    rebalance = is_rebalance(configuration)
    shop_interval = int(_get(configuration, "townShopSellInterval", 4) or 4)
    turns_per_day = int(_get(configuration, "turnsPerDay", 24) or 24)
    center_default = 24 if rebalance else 12
    center_interval = int(
        _get(configuration, "townCenterSellInterval", center_default) or center_default
    )
    demand = {product: 0.0 for product in _PRODUCTS}
    ticks = turns_per_day / max(1, shop_interval)
    for shop in shops:
        products = _SHOP_PRODUCTS.get(str(shop), ())
        multiplier = 2 if len(products) == 1 else 1
        for product in products:
            demand[product] += ticks * multiplier
    center_ticks = turns_per_day / max(1, center_interval)
    center_multiplier = 1 if rebalance else (4 if day >= 20 else 2 if day >= 10 else 1)
    for product in _PRODUCTS:
        if product != "FERTILIZER":
            demand[product] += center_ticks * center_multiplier
    return demand


def _demand_adjusted_score(
    observation: Mapping[str, Any],
    order: list[Any],
    alpha: float,
    demand: Mapping[str, float],
) -> float:
    score = _impact_score(observation, order)
    if score <= 0 or not _is_sell(order):
        return score
    item = str(order[1])
    quantity = max(0, int(order[2]))
    market = _get(observation, "market", {}) or {}
    inventory = int(_get(_get(market, "inventory", {}) or {}, item, 10000))
    recovery = max(0.0, inventory + quantity - 10000) / max(
        0.25, float(demand.get(item, 0.0))
    )
    urgency = min(1.0, recovery / 10.0)
    return score * (1.0 + max(0.0, float(alpha)) * urgency)


def reorder_sell_slots(
    observation: Mapping[str, Any],
    action: MutableAction,
    configuration: Mapping[str, Any],
    *,
    demand_alpha: float = 0.0,
) -> MutableAction:
    """Sort existing SELL slots while preserving all other positions."""
    market = [list(order) for order in action.get("market", [])]
    demand = _demand_per_day(observation, configuration) if demand_alpha > 0 else {}
    sells: list[tuple[float, int, list[Any]]] = []
    for index, order in enumerate(market):
        if not _is_sell(order):
            continue
        score = (
            _demand_adjusted_score(observation, order, demand_alpha, demand)
            if demand_alpha > 0
            else _impact_score(observation, order)
        )
        sells.append((score, -index, list(order)))
    if len(sells) < 2:
        action["market"] = market
        return action
    sells.sort(reverse=True)
    ranked = iter(row[2] for row in sells)
    action["market"] = [next(ranked) if _is_sell(order) else order for order in market]
    return action


__all__ = ["is_rebalance", "reorder_sell_slots"]
