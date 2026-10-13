"""Sparse route replay with the frozen weed repair transaction."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from kagg_revue.opponents.kaito.market import is_rebalance, reorder_sell_slots
from kagg_revue.opponents.kaito.routes import ROUTES, MutableAction
from kagg_revue.opponents.kaito.terminal import align_hands

_REPLAY_STEPS = 8


def _tile(farm: Mapping[str, Any], position: object) -> object:
    try:
        if not isinstance(position, list | tuple):
            return "LOCKED"
        x, y = int(position[0]), int(position[1])
        return (farm.get("tiles", []) or [])[y][x]
    except (IndexError, TypeError, ValueError):
        return "LOCKED"


class SparseRouteController:
    """One episode-local route replay controller with bounded weed recovery."""

    def __init__(self, route_name: str) -> None:
        """Bind one immutable route while retaining only repair state."""
        self._route_name = route_name
        self._states: dict[int, dict[str, Any]] = {0: {}, 1: {}}

    def act(
        self,
        observation: Mapping[str, Any],
        configuration: Mapping[str, Any],
    ) -> MutableAction:
        """Replay the current route turn and apply sparse promoted feedback."""
        step = max(0, int(observation.get("step", 0) or 0))
        seat = 1 if int(observation.get("player", 0) or 0) == 1 else 0
        game = self._states[seat]
        if step == 0 or "active" not in game or step < int(game.get("last_step", -1)):
            game = {"last_step": step, "active": {}}
            self._states[seat] = game
        game["last_step"] = step

        action = align_hands(ROUTES.action(self._route_name, step), observation)
        farms = observation.get("farms", []) or []
        farm = farms[seat] if seat < len(farms) else {}
        positions = [farm.get("farmer"), *(farm.get("hands", []) or [])]
        unit_actions = [action.get("farmer", ["PASS"]), *(action.get("hands", []) or [])]
        active = game["active"]
        if not isinstance(active, dict):
            raise TypeError("v48 weed transaction state is not a mapping")

        for actor_key, raw_transaction in list(active.items()):
            if not isinstance(raw_transaction, dict):
                raise TypeError("v48 weed transaction is not a mapping")
            index = 0 if actor_key == "farmer" else int(actor_key) + 1
            if index >= len(unit_actions):
                active.pop(actor_key, None)
                continue
            age = step - int(raw_transaction["start"])
            if age == 1:
                unit_actions[index] = list(raw_transaction["intended"])
                continue
            if 2 <= age <= 1 + _REPLAY_STEPS:
                unit_actions[index] = ROUTES.unit_action(
                    self._route_name,
                    step - 1,
                    actor_key,
                )
                continue
            active.pop(actor_key, None)

        for index, (position, intended) in enumerate(zip(positions, unit_actions, strict=False)):
            actor: str | int = "farmer" if index == 0 else index - 1
            if actor in active or not isinstance(intended, list) or not intended:
                continue
            operation = intended[0]
            if operation not in ("BUILD_PASTURE", "PLANT"):
                continue
            tile = _tile(farm, position)
            if not isinstance(tile, dict) or tile.get("kind") != "WEED":
                continue
            active[actor] = {"start": step, "intended": list(intended)}
            unit_actions[index] = ["DIG"]

        action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
        action["hands"] = unit_actions[1:]
        result = align_hands(action, observation)
        return reorder_sell_slots(
            observation,
            result,
            configuration,
            demand_alpha=0.25 if is_rebalance(configuration) else 0.0,
        )


__all__ = ["SparseRouteController"]
