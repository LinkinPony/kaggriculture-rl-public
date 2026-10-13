"""Hindsight-only adapter for the canonical intent language audit."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from kagg_revue.policy.tasks.contract import UnitTask
from kagg_revue.rl.intents.controller import (
    CanonicalIntentController,
    IntentTurnPlan,
    IntentTurnResult,
)
from kagg_revue.rl.intents.transaction import canonical_unit_action


@dataclass(frozen=True, slots=True)
class OracleTurnDirective:
    """One source turn plus its non-causal trace interpretation."""

    action: Mapping[str, object]
    active_tasks: tuple[UnitTask | None, ...]
    next_tasks: tuple[UnitTask | None, ...]
    animal_hints: Mapping[tuple[int, int], str]


OracleTurnResult = IntentTurnResult


class HindsightIntentController:
    """Feed hindsight trace tasks through the shared causal controller.

    Only the caller is non-causal. The ledger editor and deterministic
    compiler are exactly the same implementation used by the training teacher.
    """

    def __init__(self, backend: Any, configuration: Mapping[str, object]) -> None:
        """Create one persistent native intent session for an audit game."""
        self._controller = CanonicalIntentController(backend, configuration)

    def act(
        self,
        engine: Any,
        player: int,
        directive: OracleTurnDirective,
    ) -> OracleTurnResult:
        """Compile one hindsight directive through canonical candidate IDs."""
        return self._controller.act(
            engine,
            player,
            IntentTurnPlan(
                action=directive.action,
                active_tasks=directive.active_tasks,
            ),
        )


__all__ = [
    "HindsightIntentController",
    "OracleTurnDirective",
    "OracleTurnResult",
    "canonical_unit_action",
]
