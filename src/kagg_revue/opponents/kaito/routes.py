"""Shared immutable route templates extracted from the frozen v48 artifact."""

from __future__ import annotations

import hashlib
import zlib
from dataclasses import dataclass
from importlib import resources
from typing import Any, TypeAlias, cast

import orjson

from kagg_revue.opponents.kaito.provenance import (
    ROUTE_ASSET_SHA256,
    ROUTE_JSON_SHA256,
)

ActionAtom: TypeAlias = str | int
Command: TypeAlias = tuple[ActionAtom, ...]
MutableAction: TypeAlias = dict[str, Any]

ROUTE_NAMES = (
    "default",
    "yarn_fast",
    "farm_fast",
    "yarn_second",
    "yarn_third",
    "bakery_capital",
)
ROUTE_LENGTH = 719


@dataclass(frozen=True, slots=True)
class _ActionTemplate:
    farmer: Command
    hands: tuple[Command, ...]
    market: tuple[Command, ...]

    def mutable(self) -> MutableAction:
        return {
            "farmer": list(self.farmer),
            "hands": [list(command) for command in self.hands],
            "market": [list(command) for command in self.market],
        }


def _command(value: object) -> Command:
    if not isinstance(value, list) or not all(isinstance(item, str | int) for item in value):
        raise ValueError("v48 route command is not a string/integer list")
    return tuple(cast(list[ActionAtom], value))


def _template(value: object) -> _ActionTemplate:
    if not isinstance(value, dict):
        raise ValueError("v48 route action is not a mapping")
    farmer = _command(value.get("farmer", ["PASS"]))
    raw_hands = value.get("hands", [])
    raw_market = value.get("market", [])
    if not isinstance(raw_hands, list) or not isinstance(raw_market, list):
        raise ValueError("v48 route hands/market are not lists")
    return _ActionTemplate(
        farmer=farmer,
        hands=tuple(_command(command) for command in raw_hands),
        market=tuple(_command(command) for command in raw_market),
    )


def _load_routes() -> dict[str, tuple[_ActionTemplate, ...]]:
    asset = resources.files(__package__).joinpath("routes.json.zlib").read_bytes()
    if hashlib.sha256(asset).hexdigest() != ROUTE_ASSET_SHA256:
        raise RuntimeError("optimized v48 route asset hash mismatch")
    raw_json = zlib.decompress(asset)
    if hashlib.sha256(raw_json).hexdigest() != ROUTE_JSON_SHA256:
        raise RuntimeError("optimized v48 route JSON hash mismatch")
    decoded = orjson.loads(raw_json)
    if not isinstance(decoded, dict) or set(decoded) != set(ROUTE_NAMES):
        raise ValueError("optimized v48 route set differs from the frozen artifact")
    result: dict[str, tuple[_ActionTemplate, ...]] = {}
    for name in ROUTE_NAMES:
        raw_route = decoded[name]
        if not isinstance(raw_route, list) or len(raw_route) != ROUTE_LENGTH:
            raise ValueError(f"optimized v48 route {name!r} must contain 719 turns")
        result[name] = tuple(_template(action) for action in raw_route)
    return result


class RouteLibrary:
    """Process-shared read-only v48 actions with per-call mutable views."""

    def __init__(self) -> None:
        """Load and authenticate the compact route asset once."""
        self._routes = _load_routes()

    def action(self, route_name: str, step: int) -> MutableAction:
        """Return one independently mutable action at a bounded turn."""
        bounded = min(max(0, int(step)), ROUTE_LENGTH - 1)
        return self._routes[route_name][bounded].mutable()

    def unit_action(self, route_name: str, step: int, actor: str | int) -> list[ActionAtom]:
        """Return one mutable farmer/hand command from an earlier route turn."""
        template = self._routes[route_name][min(max(0, int(step)), ROUTE_LENGTH - 1)]
        if actor == "farmer":
            return list(template.farmer or ("PASS",))
        index = int(actor)
        return list(template.hands[index] if index < len(template.hands) else ("PASS",))

    def sell_totals(self, route_name: str, step: int) -> dict[str, int]:
        """Return scheduled SELL quantities without exposing shared commands."""
        template = self._routes[route_name][min(max(0, int(step)), ROUTE_LENGTH - 1)]
        totals: dict[str, int] = {}
        for order in template.market:
            if len(order) < 3 or order[0] != "SELL":
                continue
            item = str(order[1])
            quantity = max(0, int(order[2]))
            totals[item] = totals.get(item, 0) + quantity
        return totals


ROUTES = RouteLibrary()

__all__ = ["ROUTE_LENGTH", "ROUTE_NAMES", "ROUTES", "MutableAction", "RouteLibrary"]
