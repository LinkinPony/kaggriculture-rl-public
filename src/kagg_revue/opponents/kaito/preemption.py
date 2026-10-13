"""Frozen clone-aware SELL preemption with exact future quantity debt."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from kagg_revue.opponents.kaito.market import reorder_sell_slots
from kagg_revue.opponents.kaito.routes import ROUTE_LENGTH, ROUTES, MutableAction
from kagg_revue.opponents.kaito.terminal import align_hands, clone_distance, projected_shed

_CLONE_HORIZON = 2
_CLONE_DETECTION_START = 48
_CLONE_ACTIVE_START = 160
_CLONE_ACTIVE_STOP = 700
_CLONE_DISTANCE_THRESHOLD = 2.0
_CLONE_STREAK_REQUIRED = 24
_CLONE_MAXIMUM_BATCH = 10
_MAXIMUM_MARKET_ORDERS = 10


def _shops(observation: Mapping[str, Any]) -> list[str]:
    town = observation.get("town", {}) or {}
    return [str(value) for value in (town.get("unlocked_shops", []) or [])]


def public_asset_counts(farm: Mapping[str, Any]) -> dict[str, int]:
    """Count the public animal/crop signature used by the frozen gates."""
    counts = {
        "COW": 0,
        "SHEEP": 0,
        "GOOSE": 0,
        "MELON": 0,
        "WHEAT": 0,
        "STRAWBERRY": 0,
    }
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("animal", "crop"):
                value = str(tile.get(field, "") or "")
                if value in counts:
                    counts[value] += 1
    return counts


def _clone_veto_candidate(observation: Mapping[str, Any]) -> bool:
    step = int(observation.get("step", 0) or 0)
    shops = _shops(observation)
    if step != 120 or not shops or shops[0] != "BAKERY":
        return False
    seat = 1 if int(observation.get("player", 0) or 0) == 1 else 0
    farms = observation.get("farms", []) or []
    opponent = farms[1 - seat] if len(farms) >= 2 else {}
    counts = public_asset_counts(opponent)
    return (
        counts["SHEEP"] >= 4
        and counts["COW"] <= 1
        and counts["WHEAT"] >= 8
        and counts["MELON"] >= 7
        and counts["GOOSE"] <= 0
    )


def _sell_totals(rows: list[list[Any]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for order in rows:
        if len(order) < 3 or order[0] != "SELL":
            continue
        item = str(order[1])
        try:
            quantity = max(0, int(order[2]))
        except (TypeError, ValueError):
            continue
        totals[item] = totals.get(item, 0) + quantity
    return totals


class CloneSellPreemption:
    """Move only scheduled inventory across time and repay it exactly."""

    def __init__(self) -> None:
        """Create independent state for both possible seats."""
        self._states: dict[int, dict[str, Any]] = {0: {}, 1: {}}

    def _reset(self, seat: int, step: int) -> dict[str, Any]:
        state: dict[str, Any] = {
            "last_step": step,
            "near_streak": 0,
            "latched": False,
            "route": "default",
            "due": {},
            "clone_veto": False,
        }
        self._states[seat] = state
        return state

    def apply(
        self,
        observation: Mapping[str, Any],
        action: MutableAction,
        route_name: str,
        configuration: Mapping[str, Any],
    ) -> MutableAction:
        """Apply the active v48 clone gate and two-turn SELL shift."""
        result = align_hands(action, observation)
        seat = 1 if int(observation.get("player", 0) or 0) == 1 else 0
        step = int(observation.get("step", 0) or 0)
        state = self._states[seat]
        if step == 0 or step < int(state.get("last_step", -1)):
            state = self._reset(seat, step)
        state["last_step"] = step

        if _clone_veto_candidate(observation):
            state["clone_veto"] = True

        distance = clone_distance(observation)
        if distance <= _CLONE_DISTANCE_THRESHOLD:
            state["near_streak"] = int(state.get("near_streak", 0)) + 1
        else:
            state["near_streak"] = 0
        if (
            not bool(state.get("latched", False))
            and step >= _CLONE_DETECTION_START
            and int(state.get("near_streak", 0)) >= _CLONE_STREAK_REQUIRED
        ):
            state["latched"] = True

        if route_name != str(state.get("route", "default")):
            if state.get("due"):
                state["due"] = {}
            state["route"] = route_name

        market = [list(order) for order in result.get("market", [])]
        all_due = cast(dict[int, dict[str, int]], state.setdefault("due", {}))
        due_now = dict(all_due.pop(step, {}) or {})
        adjusted: list[list[Any]] = []
        for order in market:
            if len(order) >= 3 and order[0] == "SELL":
                item = str(order[1])
                debt = max(0, int(due_now.get(item, 0) or 0))
                if debt:
                    quantity = max(0, int(order[2] or 0))
                    reduction = min(quantity, debt)
                    quantity -= reduction
                    due_now[item] = debt - reduction
                    if quantity <= 0:
                        continue
                    order[2] = quantity
            adjusted.append(order)
        for item, quantity in due_now.items():
            if quantity > 0 and step < 718:
                row = all_due.setdefault(step + 1, {})
                row[item] = int(row.get(item, 0) or 0) + int(quantity)
        result["market"] = adjusted

        eligible = (
            bool(state.get("latched", False))
            and not bool(state.get("clone_veto", False))
            and _CLONE_ACTIVE_START <= step < _CLONE_ACTIVE_STOP
            and step + _CLONE_HORIZON < ROUTE_LENGTH
            and len(adjusted) < _MAXIMUM_MARKET_ORDERS
        )
        if not eligible:
            return result

        future = ROUTES.sell_totals(route_name, step + _CLONE_HORIZON)
        existing = _sell_totals(adjusted)
        available = projected_shed(observation, result)
        for item, quantity in existing.items():
            available[item] = max(0, int(available.get(item, 0) or 0) - quantity)

        prices = dict((observation.get("market", {}) or {}).get("prices", {}) or {})
        candidates: list[tuple[float, str, int]] = []
        for item, planned in future.items():
            quantity = min(
                max(0, int(planned) - int(existing.get(item, 0) or 0)),
                max(0, int(available.get(item, 0) or 0)),
                _CLONE_MAXIMUM_BATCH,
            )
            if quantity > 0:
                candidates.append((float(prices.get(item, 0) or 0) * quantity, item, quantity))
        candidates.sort(reverse=True)
        remaining = _CLONE_MAXIMUM_BATCH
        shifted = 0
        due_step = step + _CLONE_HORIZON
        for _value, item, requested in candidates:
            if len(result["market"]) >= _MAXIMUM_MARKET_ORDERS or remaining <= 0:
                break
            quantity = min(requested, remaining)
            if quantity <= 0:
                continue
            result["market"].append(["SELL", item, quantity])
            row = all_due.setdefault(due_step, {})
            row[item] = int(row.get(item, 0) or 0) + quantity
            remaining -= quantity
            shifted += quantity
        if not shifted:
            return result
        return reorder_sell_slots(
            observation,
            result,
            configuration,
            demand_alpha=0.25,
        )


__all__ = ["CloneSellPreemption", "public_asset_counts"]
