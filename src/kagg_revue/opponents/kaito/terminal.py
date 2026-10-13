"""Hand alignment, clone distance, and terminal liquidation for Kaito v48."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

from kagg_revue.opponents.kaito.routes import MutableAction

_SELLABLE = (
    "STRAWBERRY",
    "MELON",
    "MILK",
    "WOOL",
    "EGG",
    "TOMATO",
    "CARROT",
    "WHEAT",
    "FERTILIZER",
)
_PRODUCT_BY_ANIMAL = {"COW": "MILK", "SHEEP": "WOOL", "GOOSE": "EGG"}
_GLUT_WEIGHT = {
    "STRAWBERRY": 2.0,
    "MELON": 3.6,
    "MILK": 2.0,
    "WOOL": 3.2,
    "EGG": 1.5,
    "TOMATO": 1.3,
    "CARROT": 1.0,
    "WHEAT": 1.0,
    "FERTILIZER": 1.0,
}
_MAX_ORDERS = 10
_SHED_CAPACITY = 100


def _number(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _shed_access(board_size: int) -> set[tuple[int, int]]:
    half = board_size // 2
    return {
        (half - 1, half - 1),
        (half, half - 1),
        (half - 1, half),
        (half, half),
    }


def align_hands(action: MutableAction, observation: Mapping[str, Any]) -> MutableAction:
    """Return a mutable action matching the live number of farm hands."""
    player = 1 if int(observation.get("player", 0) or 0) == 1 else 0
    farms = observation.get("farms", []) or []
    farm = farms[player] if player < len(farms) else {}
    expected = len((farm or {}).get("hands", []) or [])
    hands = [list(command or ["PASS"]) for command in action.get("hands", [])]
    if len(hands) < expected:
        hands.extend([["PASS"] for _ in range(expected - len(hands))])
    return {
        "farmer": list(action.get("farmer") or ["PASS"]),
        "hands": hands[:expected],
        "market": [list(order) for order in action.get("market", [])],
    }


def projected_shed(
    observation: Mapping[str, Any],
    action: MutableAction,
) -> dict[str, int]:
    """Project legal same-turn DROP/PLACE deposits before the market phase."""
    player = 1 if int(observation.get("player", 0) or 0) == 1 else 0
    farms = observation.get("farms", []) or []
    farm = farms[player] if player < len(farms) else {}
    private = observation.get("private", {}) or {}
    projected = {
        str(key): max(0, int(value or 0))
        for key, value in dict(private.get("shed", {}) or {}).items()
    }
    inventories = list(private.get("inventories", []) or [])
    positions = [farm.get("farmer", [0, 0]), *(farm.get("hands", []) or [])]
    actions = [action.get("farmer", ["PASS"]), *(action.get("hands", []) or [])]
    tiles = farm.get("tiles", []) or []
    access = _shed_access(len(tiles) or 10)
    for index, unit_action in enumerate(actions):
        if index >= len(positions) or index >= len(inventories):
            continue
        position = positions[index]
        if not isinstance(position, list | tuple) or len(position) < 2:
            continue
        x, y = int(position[0]), int(position[1])
        if (x, y) not in access or not (0 <= y < len(tiles) and 0 <= x < len(tiles[y])):
            continue
        if not isinstance(unit_action, list) or not unit_action:
            continue
        inventory = {
            str(key): max(0, int(value or 0))
            for key, value in dict(inventories[index] or {}).items()
        }
        deposits: Iterable[tuple[str, int]]
        if unit_action[0] == "DROP":
            deposits = inventory.items()
        elif unit_action[0] == "PLACE" and len(unit_action) >= 2:
            item = str(unit_action[1])
            tile = tiles[y][x]
            animal_structure = {
                "COW": "PASTURE",
                "SHEEP": "PASTURE",
                "GOOSE": "COOP",
            }.get(item)
            if (
                animal_structure is not None
                and isinstance(tile, dict)
                and tile.get("kind") == animal_structure
                and "animal" not in tile
            ):
                continue
            try:
                requested = int(unit_action[2]) if len(unit_action) >= 3 else 1
            except (TypeError, ValueError):
                continue
            deposits = ((item, min(max(0, requested), inventory.get(item, 0))),)
        else:
            continue
        for item, quantity in deposits:
            room = max(0, _SHED_CAPACITY - sum(projected.values()))
            deposited = min(max(0, int(quantity or 0)), room)
            if deposited:
                projected[item] = projected.get(item, 0) + deposited
    return projected


def _opponent_exposure(observation: Mapping[str, Any]) -> dict[str, float]:
    player = 1 if int(observation.get("player", 0) or 0) == 1 else 0
    farms = observation.get("farms", []) or []
    opponent = farms[1 - player] if len(farms) >= 2 else {}
    exposure = {item: 0.0 for item in _SELLABLE}
    for row in (opponent or {}).get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            crop = str(tile.get("crop", "")).upper()
            if crop in exposure:
                exposure[crop] += max(1.0, _number(tile.get("yield_units", 0)))
            animal = str(tile.get("animal", "")).upper()
            product = _PRODUCT_BY_ANIMAL.get(animal)
            if product:
                exposure[product] += 1.0 + max(0.0, _number(tile.get("yield_units", 0)))
            if tile.get("fertilizer_available", False):
                exposure["FERTILIZER"] += 1.0
    return exposure


def _public_signature(farm: Mapping[str, Any]) -> tuple[int, int, tuple[int, ...]]:
    counts = {
        key: 0
        for key in (
            "WHEAT",
            "CARROT",
            "TOMATO",
            "STRAWBERRY",
            "MELON",
            "COW",
            "SHEEP",
            "GOOSE",
            "PASTURE",
            "COOP",
            "WEED",
        )
    }
    for row in farm.get("tiles", []) or []:
        for tile in row if isinstance(row, list) else [row]:
            if not isinstance(tile, dict):
                continue
            for field in ("crop", "animal", "kind"):
                value = str(tile.get(field, "")).upper()
                if value in counts:
                    counts[value] += 1
                    break
    return (
        len(farm.get("hands", []) or []),
        len(farm.get("unlocked_quadrants", []) or []),
        tuple(counts[key] for key in sorted(counts)),
    )


def clone_distance(observation: Mapping[str, Any]) -> float:
    """Return the frozen public-farm distance used by clone preemption."""
    farms = observation.get("farms", []) or []
    if len(farms) < 2:
        return float("inf")
    left = _public_signature(farms[0])
    right = _public_signature(farms[1])
    return float(
        abs(left[0] - right[0])
        + 3 * abs(left[1] - right[1])
        + sum(abs(a - b) for a, b in zip(left[2], right[2], strict=True))
    )


def terminal_market(
    observation: Mapping[str, Any],
    action: MutableAction,
) -> MutableAction:
    """Replace the final market queue with collision-ranked liquidation."""
    result = align_hands(action, observation)
    shed = projected_shed(observation, result)
    prices = (observation.get("market", {}) or {}).get("prices", {}) or {}
    exposure = _opponent_exposure(observation)
    rows: list[tuple[float, int, str, int]] = []
    for item in _SELLABLE:
        quantity = max(0, int(shed.get(item, 0) or 0))
        if quantity <= 0:
            continue
        price = max(1.0, _number(prices.get(item, 1), 1.0))
        score = (
            (1.0 + exposure.get(item, 0.0))
            * _GLUT_WEIGHT.get(item, 1.0)
            * price
            * math.log1p(quantity)
        )
        rows.append((score, -_SELLABLE.index(item), item, quantity))
    rows.sort(reverse=True)
    result["market"] = [
        ["SELL", item, quantity] for _, _, item, quantity in rows[:_MAX_ORDERS]
    ]
    return result


__all__ = ["align_hands", "clone_distance", "projected_shed", "terminal_market"]
