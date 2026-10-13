"""Causal semantic-task controller for the canonical intent ledger."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np

from kagg_revue.policy.tasks.contract import ITEMS, TaskOperation, UnitTask
from kagg_revue.rl.intents.transaction import Edit, Editor, append_market, apply_edit


@dataclass(frozen=True, slots=True)
class IntentTurnPlan:
    """Causal semantic unit directives and the current market request."""

    action: Mapping[str, object]
    active_tasks: tuple[UnitTask | None, ...]


@dataclass(frozen=True, slots=True)
class IntentTurnResult:
    """One compiled action and its exact dynamic-candidate labels."""

    action: Mapping[str, object]
    canonical_ids: tuple[int, ...]
    unavailable_intents: Mapping[str, int]
    market_adjustments: Mapping[str, int]


class CanonicalIntentController:
    """Edit persistent unit directives through the public candidate ABI."""

    def __init__(self, backend: Any, configuration: Mapping[str, object]) -> None:
        """Create one episode-local native ledger session."""
        self._configuration = dict(configuration)
        self._session = backend.intent_ledger_session(self._configuration)
        spec = cast(Mapping[str, object], backend.intent_ledger_spec())
        self._choices = cast(Mapping[str, int], spec["choice_kinds"])
        self._work = cast(Mapping[str, int], spec["work_kinds"])
        board_size = self._integer("boardSize", 10)
        self._cells = board_size * board_size

    def _integer(self, name: str, default: int) -> int:
        value = self._configuration.get(name, default)
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"intent teacher environment {name} must be an integer")
        return value

    def _target(self, position: tuple[int, int]) -> int:
        return position[1] * self._integer("boardSize", 10) + position[0]

    def _directive_key(self, unit: int) -> int:
        return self._cells * 16 + 2 + len(ITEMS) + 256 + unit

    def _desired_edits(
        self,
        plan: IntentTurnPlan,
        observation: Mapping[str, object],
        unavailable: Counter[str],
    ) -> dict[int, Edit]:
        hour = cast(int, observation["step"]) % self._integer("turnsPerDay", 24)
        day_end = self._integer("turnsPerDay", 24)
        source_actions = (
            tuple(cast(Sequence[object], plan.action["farmer"])),
            *(tuple(value) for value in cast(Sequence[Sequence[object]], plan.action["hands"])),
        )
        edits: dict[int, Edit] = {}
        for unit, source_action in enumerate(source_actions):
            task = plan.active_tasks[unit] if unit < len(plan.active_tasks) else None
            if task is None:
                if source_action and str(source_action[0]) != "PASS":
                    unavailable["source_task_missing"] += 1
                    continue
                operation = int(TaskOperation.WAIT)
                target = -1
                item = -1
                quantity = min(day_end, hour + 1)
            else:
                operation = int(task.operation)
                target = -1 if task.target is None else self._target(task.target)
                item = ITEMS.index(task.argument) if task.argument in ITEMS else -1
                quantity = (
                    task.earliest_start if task.operation is TaskOperation.WAIT else task.quantity
                )
            key = self._directive_key(unit)
            edits[key] = Edit(
                key=key,
                kind="directive",
                target=target,
                item=item,
                unit=unit,
                operation=operation,
                quantity=quantity,
                work_kind=self._work[f"DIRECTIVE_{TaskOperation(operation).name}"],
            )
        return edits

    def _pending_edits(
        self,
        desired: Mapping[int, Edit],
        observation: Mapping[str, object],
    ) -> list[Edit]:
        current: dict[int, tuple[int, ...]] = {}
        directive_start = self._work["DIRECTIVE_POSITION"]
        for raw_row in np.asarray(observation["work_orders"], dtype=np.int64):
            row = tuple(int(value) for value in raw_row)
            if row[0] < directive_start or row[8] < 1:
                continue
            current[self._directive_key(row[8] - 1)] = row
        pending: list[Edit] = []
        for key, edit in desired.items():
            existing = current.get(key)
            expected = (
                edit.work_kind,
                edit.target,
                edit.item + 1,
                edit.quantity,
                edit.priority,
            )
            if existing is None or existing[:5] != expected or existing[8] != edit.unit + 1:
                pending.append(edit)
        return sorted(pending, key=lambda edit: edit.key)

    def act(
        self,
        engine: Any,
        player: int,
        plan: IntentTurnPlan,
    ) -> IntentTurnResult:
        """Compile one causal plan and retain selected canonical IDs."""
        editor = Editor(self._session, engine, player)
        root = editor.observation()
        unavailable: Counter[str] = Counter()
        observation = cast(Mapping[str, object], engine.observation(player))
        desired = self._desired_edits(plan, observation, unavailable)
        for edit in self._pending_edits(desired, root):
            apply_edit(editor, edit, self._choices, unavailable)
        market = cast(Sequence[Sequence[object]], plan.action["market"])
        adjustments: Counter[str] = Counter()
        append_market(editor, self._choices, market, unavailable, adjustments)
        if not editor.select(**{"0": self._choices["COMMIT"]}):
            raise RuntimeError("intent teacher transaction cannot commit")
        action = cast(Mapping[str, object], self._session.action(engine, player))
        return IntentTurnResult(
            action=action,
            canonical_ids=tuple(editor.ids),
            unavailable_intents=dict(unavailable),
            market_adjustments=dict(adjustments),
        )

    def reset(self) -> None:
        """Reset the native ledger for a new episode."""
        self._session.reset()


__all__ = [
    "CanonicalIntentController",
    "IntentTurnPlan",
    "IntentTurnResult",
]
