"""Stable route-decision contract shared by rollout and deployment."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RouteDecision:
    """One synchronized route fork exposed to the PPO actor."""

    step: int
    route_index: int
    route_name: str


ROUTE_DECISIONS = (
    RouteDecision(step=88, route_index=1, route_name="yarn_fast"),
    RouteDecision(step=120, route_index=2, route_name="farm_fast"),
    RouteDecision(step=153, route_index=3, route_name="yarn_second"),
    RouteDecision(step=160, route_index=5, route_name="bakery_capital"),
    RouteDecision(step=216, route_index=4, route_name="yarn_third"),
)
ROUTE_DECISION_BY_STEP = {decision.step: decision for decision in ROUTE_DECISIONS}
ROUTE_FEATURE_VERSION = "kaito-route-pooled-observation-v1"
ROUTE_POLICY_VERSION = "kaito-event-route-ppo-v1"


__all__ = [
    "ROUTE_DECISION_BY_STEP",
    "ROUTE_DECISIONS",
    "ROUTE_FEATURE_VERSION",
    "ROUTE_POLICY_VERSION",
    "RouteDecision",
]
