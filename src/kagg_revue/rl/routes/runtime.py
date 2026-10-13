"""Official-observation reference runtime for a frozen route-PPO policy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch

from kagg_revue.native import _revue_native
from kagg_revue.opponents.kaito.preemption import CloneSellPreemption
from kagg_revue.opponents.kaito.replay import SparseRouteController
from kagg_revue.opponents.kaito.routes import ROUTE_NAMES, MutableAction
from kagg_revue.opponents.kaito.runtime import _bakery_capital_candidate, _route_event
from kagg_revue.opponents.kaito.terminal import terminal_market
from kagg_revue.rl.routes.contract import ROUTE_DECISION_BY_STEP, ROUTE_DECISIONS
from kagg_revue.rl.routes.features import pool_route_features
from kagg_revue.rl.routes.model import RouteActorArchitecture, RouteActorCritic


def load_route_model(
    checkpoint_path: Path,
    *,
    prior_logit: float | None = None,
) -> tuple[RouteActorCritic, dict[str, object]]:
    """Load one immutable route actor on CPU with an optional calibrated prior."""
    raw = cast(
        dict[str, Any],
        torch.load(checkpoint_path, map_location="cpu", weights_only=False),
    )
    architecture_value = raw.get("architecture")
    if not isinstance(architecture_value, Mapping):
        raise ValueError("route runtime checkpoint lacks an architecture")
    architecture = RouteActorArchitecture(
        feature_width=int(architecture_value["feature_width"]),
        hidden_width=int(architecture_value["hidden_width"]),
        feedforward_width=int(architecture_value["feedforward_width"]),
        prior_logit=float(architecture_value["prior_logit"]),
    )
    if prior_logit is not None:
        if not np.isfinite(prior_logit) or prior_logit <= 0.0:
            raise ValueError("route runtime prior logit must be finite and positive")
        architecture = replace(architecture, prior_logit=prior_logit)
    model = RouteActorCritic(architecture)
    model.load_state_dict(raw["model_state_dict"])
    model.eval()
    return model, cast(dict[str, object], raw)


class RoutePolicyRuntime:
    """PPO route actor with the readable frozen Kaito executor."""

    def __init__(
        self,
        configuration: Mapping[str, Any],
        model: RouteActorCritic,
        *,
        unit_limit: int,
    ) -> None:
        """Create episode-local executor state around one immutable CPU model."""
        if next(model.parameters()).device.type != "cpu":
            raise ValueError("reference route runtime requires a CPU actor")
        self._configuration = dict(configuration)
        self._model = model
        self._unit_limit = unit_limit
        self._children = {
            name: SparseRouteController(name) for name in ROUTE_NAMES
        }
        self._preemption = CloneSellPreemption()
        self._selected = {0: "default", 1: "default"}
        self._last_step = {0: -1, 1: -1}
        self._actor_decisions = {0: 0, 1: 0}
        self._actor_switches = {0: 0, 1: 0}
        self._errors = {0: 0, 1: 0}

    def _reset_seat(self, seat: int) -> None:
        self._selected[seat] = "default"
        self._actor_decisions[seat] = 0
        self._actor_switches[seat] = 0
        self._errors[seat] = 0

    def _prior_action(
        self,
        observation: Mapping[str, Any],
        candidate_name: str,
    ) -> int:
        proposal = _route_event(observation)
        if proposal is None and _bakery_capital_candidate(observation):
            proposal = "bakery_capital"
        return int(proposal == candidate_name)

    def _actor_action(
        self,
        observation: Mapping[str, Any],
        *,
        decision_index: int,
        candidate_route: int,
        prior_action: int,
    ) -> int:
        board, units, globals_ = _revue_native.encode_official_observation_numeric(
            dict(observation),
            self._configuration,
            self._unit_limit,
        )
        features = pool_route_features(
            np.asarray(board)[None, ...],
            np.asarray(units)[None, ...],
            np.asarray(globals_)[None, ...],
            decision_index=decision_index,
            candidate_route=candidate_route,
            prior_actions=np.asarray([prior_action], dtype=np.int64),
            unit_limit=self._unit_limit,
        )
        with torch.no_grad():
            logits, _values = self._model(
                torch.from_numpy(features),
                torch.tensor([prior_action], dtype=torch.int64),
            )
        return int(logits.argmax(dim=-1).item())

    def act(self, observation: Mapping[str, Any]) -> MutableAction:
        """Select a synchronized route and emit one legal official action."""
        try:
            seat = 1 if int(observation.get("player", 0) or 0) == 1 else 0
            step = int(observation.get("step", 0) or 0)
            if step == 0 or step < self._last_step[seat]:
                self._reset_seat(seat)
            self._last_step[seat] = step
            decision = ROUTE_DECISION_BY_STEP.get(step)
            if self._selected[seat] == "default" and decision is not None:
                decision_index = ROUTE_DECISIONS.index(decision)
                prior_action = self._prior_action(observation, decision.route_name)
                actor_action = self._actor_action(
                    observation,
                    decision_index=decision_index,
                    candidate_route=decision.route_index,
                    prior_action=prior_action,
                )
                self._actor_decisions[seat] += 1
                if actor_action == 1:
                    self._selected[seat] = decision.route_name
                    self._actor_switches[seat] += 1
            route_name = self._selected[seat]
            result = self._children[route_name].act(observation, self._configuration)
            result = self._preemption.apply(
                observation,
                result,
                route_name,
                self._configuration,
            )
            if step == 718:
                result = terminal_market(observation, result)
            return result
        except Exception:
            seat = 1 if int(observation.get("player", 0) or 0) == 1 else 0
            self._errors[seat] += 1
            farms = observation.get("farms", []) or []
            farm = farms[seat] if seat < len(farms) else {}
            return {
                "farmer": ["PASS"],
                "hands": [["PASS"] for _ in (farm.get("hands", []) or [])],
                "market": [],
            }

    def diagnostics(self, seat: int) -> dict[str, int | str]:
        """Return route decisions without exposing actor internals."""
        bounded = 1 if seat == 1 else 0
        return {
            "selected_route": self._selected[bounded],
            "actor_decisions": self._actor_decisions[bounded],
            "actor_switches": self._actor_switches[bounded],
            "errors": self._errors[bounded],
        }


__all__ = ["RoutePolicyRuntime", "load_route_model"]
