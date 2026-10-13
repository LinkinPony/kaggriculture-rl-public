"""Episode-local optimized runtime for the frozen Kaito v48 behavior."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from kagg_revue.opponents.kaito.native import create_native_session

if TYPE_CHECKING:
    from kagg_revue.opponents.kaito.routes import MutableAction
    from kagg_revue.policy.runtime import NumericAction

_YARN_THIRD_PREFIXES = {
    ("BRUNCH_SPOT", "PET_CAFE"),
    ("PET_CAFE", "FARMERS_MARKET"),
}


def _shops(observation: Mapping[str, Any]) -> list[str]:
    town = observation.get("town", {}) or {}
    return [str(value) for value in (town.get("unlocked_shops", []) or [])]


def _route_event(observation: Mapping[str, Any]) -> str | None:
    step = int(observation.get("step", 0) or 0)
    shops = _shops(observation)
    if shops and shops[0] == "YARN_STORE" and step >= 88:
        return "yarn_fast"
    if shops and shops[0] == "FARMERS_MARKET" and step >= 120:
        return "farm_fast"
    if (
        len(shops) >= 2
        and shops[0] not in {"YARN_STORE", "FARMERS_MARKET"}
        and shops[1] == "YARN_STORE"
        and step >= 153
    ):
        return "yarn_second"
    if (
        len(shops) >= 3
        and shops[0] not in {"YARN_STORE", "FARMERS_MARKET"}
        and shops[1] != "YARN_STORE"
        and shops[2] == "YARN_STORE"
        and (shops[0], shops[1]) in _YARN_THIRD_PREFIXES
        and step >= 216
    ):
        return "yarn_third"
    return None


def _bakery_capital_candidate(observation: Mapping[str, Any]) -> bool:
    from kagg_revue.opponents.kaito.preemption import public_asset_counts

    step = int(observation.get("step", 0) or 0)
    shops = _shops(observation)
    if (
        step != 160
        or len(shops) < 2
        or shops[0] != "BAKERY"
        or shops[1] != "PIZZA_SHOP"
    ):
        return False
    seat = 1 if int(observation.get("player", 0) or 0) == 1 else 0
    farms = observation.get("farms", []) or []
    opponent = farms[1 - seat] if len(farms) >= 2 else {}
    counts = public_asset_counts(opponent)
    return (
        counts["COW"] >= 3
        and counts["SHEEP"] >= 2
        and counts["MELON"] >= 10
        and counts["GOOSE"] <= 0
    )


class KaitoV48Runtime:
    """Thread-independent v48 state sharing only immutable route templates."""

    native_rollout_required = True
    native_batch_kind = "kaito_v48"

    def __init__(self, configuration: Mapping[str, Any]) -> None:
        """Create one fresh episode state without copying the route portfolio."""
        self._configuration = dict(configuration)
        self._children: dict[str, Any] | None = None
        self._preemption: Any | None = None
        self._selected = {0: "default", 1: "default"}
        self._last_step = {0: -1, 1: -1}
        self._encoder: Any | None = None
        self._maximum_market_orders = int(configuration.get("maxMarketOrdersPerTurn", 10) or 10)
        self._numeric_tokens: Any | None = None
        self._numeric_quantities: Any | None = None
        self._native_session = create_native_session(self._maximum_market_orders)

    @property
    def native_session(self) -> Any:
        """Return episode-local state for the direct native-engine hot path."""
        return self._native_session

    def _reference_controllers(self) -> tuple[dict[str, Any], Any]:
        """Construct the readable Python reference only for diagnostics."""
        if self._children is None or self._preemption is None:
            from kagg_revue.opponents.kaito.preemption import CloneSellPreemption
            from kagg_revue.opponents.kaito.replay import SparseRouteController
            from kagg_revue.opponents.kaito.routes import ROUTE_NAMES

            self._children = {
                name: SparseRouteController(name) for name in ROUTE_NAMES
            }
            self._preemption = CloneSellPreemption()
        return self._children, self._preemption

    def _act(self, observation: Mapping[str, Any]) -> MutableAction:
        from kagg_revue.opponents.kaito.terminal import terminal_market

        children, preemption = self._reference_controllers()
        seat = 1 if int(observation.get("player", 0) or 0) == 1 else 0
        step = int(observation.get("step", 0) or 0)
        if step == 0 or step < self._last_step[seat]:
            self._selected[seat] = "default"
        self._last_step[seat] = step

        if self._selected[seat] == "default":
            event = _route_event(observation)
            if event is None and _bakery_capital_candidate(observation):
                event = "bakery_capital"
            if event is not None:
                self._selected[seat] = event
        route_name = self._selected[seat]
        result: MutableAction = children[route_name].act(
            observation, self._configuration
        )
        result = preemption.apply(
            observation,
            result,
            route_name,
            self._configuration,
        )
        if step == 718:
            result = terminal_market(observation, result)
        return result

    def act(self, observation: Mapping[str, Any]) -> MutableAction:
        """Return the v48 action with the notebook's final PASS crash guard."""
        try:
            return self._act(observation)
        except Exception:
            seat = 1 if int(observation.get("player", 0) or 0) == 1 else 0
            farms = observation.get("farms", []) or []
            farm = farms[seat] if seat < len(farms) else {}
            return {
                "farmer": ["PASS"],
                "hands": [["PASS"] for _ in (farm.get("hands", []) or [])],
                "market": [],
            }

    def act_numeric(self, observation: Mapping[str, Any]) -> NumericAction:
        """Return the exact official action through the native numeric ABI."""
        import numpy as np

        from kagg_revue.bc.actions import ReplayActionEncoder
        from kagg_revue.native import _revue_native
        from kagg_revue.policy.runtime import NumericAction

        if self._encoder is None:
            self._encoder = ReplayActionEncoder(_revue_native.action_codec_spec())
            self._numeric_tokens = np.empty(32, dtype=np.int64)
            self._numeric_quantities = np.empty(32, dtype=np.int64)
        action = self.act(observation)
        seat = 1 if int(observation.get("player", 0) or 0) == 1 else 0
        farms = observation.get("farms", []) or []
        farm = farms[seat] if seat < len(farms) else {}
        unit_count = 1 + len(farm.get("hands", []) or [])
        encoded = self._encoder.encode(
            action,
            unit_count=unit_count,
            max_market_orders=self._maximum_market_orders,
        )
        count = len(encoded.tokens)
        if self._numeric_tokens is None or self._numeric_quantities is None:
            raise RuntimeError("v48 numeric buffers were not initialized")
        if count > self._numeric_tokens.size:
            self._numeric_tokens = np.empty(count, dtype=np.int64)
            self._numeric_quantities = np.empty(count, dtype=np.int64)
        self._numeric_tokens[:count] = encoded.tokens
        self._numeric_quantities[:count] = encoded.quantities
        return NumericAction(
            tokens=self._numeric_tokens[:count],
            quantities=self._numeric_quantities[:count],
            decision_count=count,
            unit_count=unit_count,
        )

    def close(self) -> None:
        """Release no-op episode state through the common agent protocol."""


__all__ = ["KaitoV48Runtime"]
