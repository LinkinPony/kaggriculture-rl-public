"""Canonical numeric labels for official behavior-cloning actions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class ActionEncodingError(ValueError):
    """Raised when a replay action cannot be represented by the actor ABI."""


@dataclass(frozen=True)
class EncodedTurnAction:
    """One complete unit prefix and bounded ordered market suffix."""

    tokens: tuple[int, ...]
    quantities: tuple[int, ...]
    unit_decisions: int
    market_orders: int
    repairs: Mapping[str, int]


def _official_quantity(value: Any, field: str) -> tuple[int | None, bool]:
    try:
        quantity = int(value)
    except (TypeError, ValueError, OverflowError):
        return None, False
    if quantity <= 0:
        return None, not isinstance(value, int) or isinstance(value, bool)
    if quantity > 2**63 - 1:
        raise ActionEncodingError(f"{field} exceeds the numeric action ABI")
    coerced = not isinstance(value, int) or isinstance(value, bool)
    return quantity, coerced


def _merge_repairs(target: dict[str, int], update: Mapping[str, int]) -> None:
    for name, count in update.items():
        target[name] = target.get(name, 0) + count


class ReplayActionEncoder:
    """Map official request syntax to the native actor token vocabulary."""

    _SIMPLE_UNIT_OPS = frozenset(
        {
            "PASS",
            "NORTH",
            "SOUTH",
            "EAST",
            "WEST",
            "DROP",
            "WATER",
            "HARVEST",
            "FERTILIZE",
            "DIG",
            "BUILD_COOP",
            "BUILD_PASTURE",
            "FEED",
            "COLLECT_FERTILIZER",
            "CARE",
        }
    )
    _QUANTITY_MARKET_OPS = frozenset({"SELL", "BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL"})
    _SIMPLE_MARKET_OPS = frozenset({"HIRE", "BUY_LAND"})

    def __init__(self, codec_spec: Mapping[str, Any]) -> None:
        """Bind labels to one authenticated native action codec spec."""
        raw_keys = codec_spec.get("keys")
        if not isinstance(raw_keys, (list, tuple)) or not all(
            isinstance(key, str) for key in raw_keys
        ):
            raise ValueError("action codec keys must be a string sequence")
        self.keys = tuple(raw_keys)
        self._token = {key: index for index, key in enumerate(self.keys)}
        self.unit_tokens = int(codec_spec["unit_tokens"])
        self.market_stop_token = int(codec_spec["market_stop_token"])
        if self.market_stop_token != self.unit_tokens:
            raise ValueError("market STOP must immediately follow the unit vocabulary")
        if self._token.get("MARKET:STOP") != self.market_stop_token:
            raise ValueError("action codec STOP identity differs")

    def _lookup(self, key: str) -> int:
        try:
            return self._token[key]
        except KeyError as error:
            raise ActionEncodingError(f"action is outside the actor vocabulary: {key}") from error

    def _unit(self, value: Any, field: str) -> tuple[int, int, Mapping[str, int]]:
        if not isinstance(value, list) or not value or not isinstance(value[0], str):
            return self._lookup("UNIT:PASS"), 0, {"invalid_unit_requests_to_pass": 1}
        request = value
        operation = request[0]
        if operation in self._SIMPLE_UNIT_OPS:
            extra_repairs = (
                {"extra_unit_arguments_dropped": len(request) - 1} if len(request) > 1 else {}
            )
            return self._lookup(f"UNIT:{operation}"), 0, extra_repairs
        if operation in {"PICKUP", "PLACE"}:
            if len(request) < 2 or not isinstance(request[1], str):
                return self._lookup("UNIT:PASS"), 0, {"invalid_unit_requests_to_pass": 1}
            item = request[1]
            if len(request) == 2:
                token = self._token.get(f"UNIT:{operation}:{item}")
                if token is None:
                    return self._lookup("UNIT:PASS"), 0, {"invalid_unit_requests_to_pass": 1}
                return token, 1, {}
            quantity, coerced = _official_quantity(request[2], f"{field} quantity")
            token = self._token.get(f"UNIT:{operation}:{item}")
            if quantity is None or token is None:
                return self._lookup("UNIT:PASS"), 0, {"invalid_unit_requests_to_pass": 1}
            quantity_repairs: dict[str, int] = {}
            if coerced:
                quantity_repairs["quantity_values_coerced_to_integer"] = 1
            if len(request) > 3:
                quantity_repairs["extra_unit_arguments_dropped"] = len(request) - 3
            return token, quantity, quantity_repairs
        if operation == "PLANT":
            if len(request) < 2 or not isinstance(request[1], str):
                return self._lookup("UNIT:PASS"), 0, {"invalid_unit_requests_to_pass": 1}
            token = self._token.get(f"UNIT:PLANT:{request[1]}")
            if token is None:
                return self._lookup("UNIT:PASS"), 0, {"invalid_unit_requests_to_pass": 1}
            plant_repairs = (
                {"extra_unit_arguments_dropped": len(request) - 2} if len(request) > 2 else {}
            )
            return token, 0, plant_repairs
        return self._lookup("UNIT:PASS"), 0, {"invalid_unit_requests_to_pass": 1}

    def _market(self, value: Any, field: str) -> tuple[int, int, Mapping[str, int]]:
        skip = self._lookup("MARKET:SKIP_SLOT")
        if value is None or value == []:
            return skip, 0, {}
        if not isinstance(value, list) or not value or not isinstance(value[0], str):
            return skip, 0, {"invalid_market_requests_to_skip": 1}
        request = value
        operation = request[0]
        if operation in self._SIMPLE_MARKET_OPS:
            extra_repairs = (
                {"extra_market_arguments_dropped": len(request) - 1} if len(request) > 1 else {}
            )
            return self._lookup(f"MARKET:{operation}"), 0, extra_repairs
        if operation in self._QUANTITY_MARKET_OPS:
            if len(request) < 3 or not isinstance(request[1], str):
                return skip, 0, {"invalid_market_requests_to_skip": 1}
            quantity, coerced = _official_quantity(request[2], f"{field} quantity")
            token = self._token.get(f"MARKET:{operation}:{request[1]}")
            if quantity is None or token is None:
                return skip, 0, {"invalid_market_requests_to_skip": 1}
            quantity_repairs: dict[str, int] = {}
            if coerced:
                quantity_repairs["quantity_values_coerced_to_integer"] = 1
            if len(request) > 3:
                quantity_repairs["extra_market_arguments_dropped"] = len(request) - 3
            return token, quantity, quantity_repairs
        return skip, 0, {"invalid_market_requests_to_skip": 1}

    def encode(
        self,
        action: Any,
        unit_count: int,
        max_market_orders: int,
    ) -> EncodedTurnAction:
        """Encode one request, matching the official missing/extra action semantics."""
        if unit_count < 1:
            raise ValueError("a turn must contain the main farmer")
        if max_market_orders < 1:
            raise ValueError("max_market_orders must be positive")

        repairs: dict[str, int] = {}
        if not isinstance(action, Mapping):
            action = {}
            repairs["invalid_player_actions_to_noop"] = 1
        raw_farmer = action.get("farmer")
        if raw_farmer is None:
            raw_farmer = ["PASS"]
            repairs["missing_farmer_pass"] = 1
        raw_hands = action.get("hands", [])
        if raw_hands is None:
            raw_hands = []
        if not isinstance(raw_hands, list):
            raw_hands = []
            repairs["invalid_hands_to_pass"] = expected_hands = unit_count - 1
        else:
            expected_hands = unit_count - 1
        if len(raw_hands) < expected_hands:
            repairs["missing_hand_passes"] = expected_hands - len(raw_hands)
        elif len(raw_hands) > expected_hands:
            repairs["extra_hand_requests_dropped"] = len(raw_hands) - expected_hands
        raw_units = [raw_farmer, *raw_hands[:expected_hands]]
        raw_units.extend([["PASS"]] * (unit_count - len(raw_units)))

        tokens: list[int] = []
        quantities: list[int] = []
        for index, request in enumerate(raw_units):
            token, quantity, update = self._unit(request, f"unit[{index}]")
            tokens.append(token)
            quantities.append(quantity)
            _merge_repairs(repairs, update)

        raw_market = action.get("market", [])
        if raw_market is None:
            raw_market = []
        if not isinstance(raw_market, list):
            raw_market = []
            repairs["invalid_market_to_empty"] = 1
        if len(raw_market) > max_market_orders:
            repairs["extra_market_orders_dropped"] = len(raw_market) - max_market_orders
        market = raw_market[:max_market_orders]
        for index, request in enumerate(market):
            token, quantity, update = self._market(request, f"market[{index}]")
            tokens.append(token)
            quantities.append(quantity)
            _merge_repairs(repairs, update)
        if len(market) < max_market_orders:
            tokens.append(self.market_stop_token)
            quantities.append(0)

        return EncodedTurnAction(
            tokens=tuple(tokens),
            quantities=tuple(quantities),
            unit_decisions=unit_count,
            market_orders=len(market),
            repairs=repairs,
        )


__all__ = [
    "ActionEncodingError",
    "EncodedTurnAction",
    "ReplayActionEncoder",
]
