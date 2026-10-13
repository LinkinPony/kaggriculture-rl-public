"""Actor-safe semantic intent teacher for an authenticated route program."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from kagg_revue.policy.tasks.contract import (
    ANIMALS,
    ITEMS,
    TaskOperation,
    UnitTask,
    deterministic_path,
)
from kagg_revue.rl.intents.controller import (
    CanonicalIntentController,
    IntentTurnPlan,
    IntentTurnResult,
)
from kagg_revue.teacher.submission import SubmissionTeacher, SubmissionTeacherArtifact

_DIRECTIONS = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}
_OFFICIAL = {operation.name: operation for operation in TaskOperation if operation.is_official}
_MARKET_CHOICES = {
    "SELL": "MARKET_SELL",
    "BUY_SEED": "MARKET_BUY_SEED",
    "BUY_PRODUCT": "MARKET_BUY_PRODUCT",
    "BUY_ANIMAL": "MARKET_BUY_ANIMAL",
    "HIRE": "MARKET_HIRE",
    "BUY_LAND": "MARKET_BUY_LAND",
}


@dataclass(frozen=True, slots=True)
class ProgramIntentPlan:
    """One actor-safe semantic plan before canonical candidate selection."""

    intent: IntentTurnPlan
    tasks: tuple[UnitTask, ...]
    route_id: str
    first_event_day: int | None


@dataclass(frozen=True, slots=True)
class ProgramIntentTurn:
    """One teacher result with causal-program provenance."""

    result: IntentTurnResult
    plan: ProgramIntentPlan

    @property
    def tasks(self) -> tuple[UnitTask, ...]:
        """Return the semantic tasks selected for this turn."""
        return self.plan.tasks

    @property
    def route_id(self) -> str:
        """Return the actor-visible selected route identity."""
        return self.plan.route_id

    @property
    def first_event_day(self) -> int | None:
        """Return the observed event day used for route selection."""
        return self.plan.first_event_day


@dataclass(frozen=True, slots=True)
class NativeIntentTeacherBatch:
    """Dense semantic plans consumed by the GIL-released native compiler."""

    directive_operations: NDArray[np.int64]
    directive_targets: NDArray[np.int64]
    directive_items: NDArray[np.int64]
    directive_quantities: NDArray[np.int64]
    directive_counts: NDArray[np.int64]
    market_choices: NDArray[np.int64]
    market_items: NDArray[np.int64]
    market_quantities: NDArray[np.int64]
    market_counts: NDArray[np.int64]

    def arguments(self) -> tuple[NDArray[np.int64], ...]:
        """Return fields in the native method's stable ABI order."""
        return (
            self.directive_operations,
            self.directive_targets,
            self.directive_items,
            self.directive_quantities,
            self.directive_counts,
            self.market_choices,
            self.market_items,
            self.market_quantities,
            self.market_counts,
        )


def encode_native_intent_plans(
    plans: Sequence[ProgramIntentPlan],
    spec: Mapping[str, object],
    *,
    board_size: int,
    unit_limit: int,
    maximum_market_orders: int,
) -> NativeIntentTeacherBatch:
    """Encode causal semantic plans without enumerating dynamic candidates."""
    if not plans or board_size < 1 or unit_limit < 1 or maximum_market_orders < 1:
        raise ValueError("intent teacher batch dimensions must be positive")
    choices = cast(Mapping[str, int], spec["choice_kinds"])
    batch = len(plans)
    operations = np.zeros((batch, unit_limit), dtype=np.int64)
    targets = np.full((batch, unit_limit), -1, dtype=np.int64)
    items = np.full((batch, unit_limit), -1, dtype=np.int64)
    quantities = np.zeros((batch, unit_limit), dtype=np.int64)
    directive_counts = np.empty(batch, dtype=np.int64)
    market_choices = np.zeros((batch, maximum_market_orders), dtype=np.int64)
    market_items = np.zeros_like(market_choices)
    market_quantities = np.zeros_like(market_choices)
    market_counts = np.empty(batch, dtype=np.int64)
    for row, plan in enumerate(plans):
        if len(plan.tasks) > unit_limit:
            raise ValueError("intent teacher plan exceeds the configured unit limit")
        directive_counts[row] = len(plan.tasks)
        for unit, task in enumerate(plan.tasks):
            operations[row, unit] = int(task.operation)
            if task.target is not None:
                targets[row, unit] = task.target[1] * board_size + task.target[0]
            if task.argument is not None:
                items[row, unit] = ITEMS.index(task.argument)
            quantities[row, unit] = (
                task.earliest_start if task.operation is TaskOperation.WAIT else task.quantity
            )
        orders = cast(Sequence[Sequence[object]], plan.intent.action["market"])
        if len(orders) > maximum_market_orders:
            raise ValueError("intent teacher market plan exceeds the native limit")
        market_counts[row] = len(orders)
        for order_index, order in enumerate(orders):
            if not order:
                raise ValueError("intent teacher market order cannot be empty")
            kind = str(order[0])
            choice_name = _MARKET_CHOICES.get(kind)
            if choice_name is None:
                raise ValueError(f"unsupported intent teacher market order {kind!r}")
            market_choices[row, order_index] = choices[choice_name]
            if kind in {"HIRE", "BUY_LAND"}:
                continue
            if len(order) != 3 or not isinstance(order[1], str):
                raise ValueError("intent teacher quantity order is malformed")
            vocabulary = ANIMALS if kind == "BUY_ANIMAL" else ITEMS
            market_items[row, order_index] = vocabulary.index(order[1]) + 1
            quantity = order[2]
            if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
                raise ValueError("intent teacher market quantity must be positive")
            market_quantities[row, order_index] = quantity
    return NativeIntentTeacherBatch(
        directive_operations=operations,
        directive_targets=targets,
        directive_items=items,
        directive_quantities=quantities,
        directive_counts=directive_counts,
        market_choices=market_choices,
        market_items=market_items,
        market_quantities=market_quantities,
        market_counts=market_counts,
    )


def _advance(position: tuple[int, int], direction: str) -> tuple[int, int]:
    dx, dy = _DIRECTIONS[direction]
    return position[0] + dx, position[1] + dy


def _canonical_endpoints(
    start: tuple[int, int], directions: Sequence[str]
) -> tuple[tuple[int, int], ...]:
    positions = [start]
    for direction in directions:
        positions.append(_advance(positions[-1], direction))
    endpoints: list[tuple[int, int]] = []
    first = 0
    while first < len(directions):
        best = first + 1
        for end in range(first + 1, len(directions) + 1):
            if deterministic_path(positions[first], positions[end]) == tuple(directions[first:end]):
                best = end
        endpoints.append(positions[best])
        first = best
    return tuple(endpoints)


def _operation_task(
    action: Sequence[object],
    target: tuple[int, int],
    hour: int,
) -> UnitTask:
    operation = _OFFICIAL.get(str(action[0]))
    if operation is None:
        raise ValueError(f"route program contains unsupported operation {action[0]!r}")
    argument = str(action[1]) if operation.needs_argument and len(action) > 1 else None
    quantity = 0
    if operation.needs_quantity:
        quantity = 1 if len(action) == 2 else int(cast(int, action[2]))
    return UnitTask(
        operation=operation,
        target=target,
        argument=argument,
        quantity=quantity,
        earliest_start=hour,
        deadline=hour + 1,
    )


def active_program_task(
    program: Sequence[Sequence[object]],
    position: tuple[int, int],
    *,
    hour: int,
    board_size: int,
    day_end: int,
) -> UnitTask:
    """Summarize the current embedded-program prefix as one semantic task."""
    if not program:
        raise ValueError("route unit program cannot be empty")
    first = tuple(program[0])
    if not first:
        raise ValueError("route unit action cannot be empty")
    name = str(first[0])
    if name == "PASS":
        wait = 0
        for action in program:
            if not action or str(action[0]) != "PASS":
                break
            wait += 1
        boundary = min(day_end, hour + wait)
        task = UnitTask(
            operation=TaskOperation.WAIT,
            target=None,
            argument=None,
            quantity=0,
            earliest_start=boundary,
            deadline=boundary,
        )
        task.validate(board_size=board_size, day_end=day_end)
        return task
    if name in _OFFICIAL:
        task = _operation_task(first, position, hour)
        task.validate(board_size=board_size, day_end=day_end)
        return task
    if name not in _DIRECTIONS:
        raise ValueError(f"route program contains unsupported action {name!r}")

    directions: list[str] = []
    terminal: tuple[object, ...] | None = None
    for raw_action in program:
        action = tuple(raw_action)
        action_name = str(action[0]) if action else ""
        if action_name in _DIRECTIONS:
            directions.append(action_name)
            continue
        terminal = action
        break
    endpoints = _canonical_endpoints(position, directions)
    if not endpoints:
        raise RuntimeError("moving route prefix has no semantic endpoint")
    operation = None if not terminal else _OFFICIAL.get(str(terminal[0]))
    if len(endpoints) == 1 and operation is not None:
        assert terminal is not None
        task = _operation_task(terminal, endpoints[0], hour + len(directions))
    else:
        target = endpoints[0]
        completion = hour + len(deterministic_path(position, target))
        task = UnitTask(
            operation=TaskOperation.POSITION,
            target=target,
            argument=None,
            quantity=0,
            earliest_start=completion,
            deadline=completion,
        )
    task.validate(board_size=board_size, day_end=day_end)
    return task


class ProgramIntentPlanner:
    """Translate the Rank8 actor's visible program into semantic intent plans."""

    def __init__(
        self,
        configuration: Mapping[str, object],
        artifact: SubmissionTeacherArtifact,
    ) -> None:
        """Create episode-local causal route-program state."""
        self._configuration = dict(configuration)
        self._source = SubmissionTeacher(configuration, artifact)

    def _integer(self, name: str, default: int) -> int:
        value = self._configuration.get(name, default)
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"intent teacher environment {name} must be an integer")
        return value

    def plan(self, observation: Mapping[str, object]) -> ProgramIntentPlan:
        """Build semantic tasks without reading a future observation."""
        plan = self._source.plan(observation)
        programs = self._source.causal_unit_programs(observation)
        farms = cast(Sequence[Mapping[str, object]], observation["farms"])
        raw_player = observation.get("player", 0)
        if not isinstance(raw_player, int) or isinstance(raw_player, bool):
            raise TypeError("intent teacher observation player must be an integer")
        player = raw_player
        farm = farms[player]
        positions = [
            farm["farmer"],
            *cast(Sequence[Sequence[int]], farm["hands"]),
        ]
        step = cast(int, observation["step"])
        turns_per_day = self._integer("turnsPerDay", 24)
        hour = step % turns_per_day
        board_size = self._integer("boardSize", 10)
        tasks = tuple(
            active_program_task(
                program,
                (
                    int(cast(Sequence[int], position)[0]),
                    int(cast(Sequence[int], position)[1]),
                ),
                hour=hour,
                board_size=board_size,
                day_end=turns_per_day,
            )
            for program, position in zip(programs, positions, strict=True)
        )
        return ProgramIntentPlan(
            intent=IntentTurnPlan(
                action=cast(Mapping[str, object], plan["action"]),
                active_tasks=tasks,
            ),
            tasks=tasks,
            route_id=str(plan["route_id"]),
            first_event_day=cast(int | None, plan["first_event_day"]),
        )

    def reset(self) -> None:
        """Reset the source program state for a new episode."""
        self._source.reset()

    def metadata(self) -> dict[str, object]:
        """Return actor-visible route-selection metadata."""
        return self._source.metadata()


class ProgramIntentTeacher:
    """Select canonical intents from a causal Rank8 route program."""

    def __init__(
        self,
        backend: Any,
        configuration: Mapping[str, object],
        artifact: SubmissionTeacherArtifact,
    ) -> None:
        """Create independent program-planner and canonical-ledger state."""
        self._planner = ProgramIntentPlanner(configuration, artifact)
        self._controller = CanonicalIntentController(backend, configuration)

    def plan(self, observation: Mapping[str, object]) -> ProgramIntentPlan:
        """Build semantic tasks without reading a future observation."""
        return self._planner.plan(observation)

    def act(self, engine: Any, player: int) -> ProgramIntentTurn:
        """Select dynamic canonical IDs using only actor-visible program state."""
        observation = cast(Mapping[str, object], engine.observation(player))
        plan = self.plan(observation)
        result = self._controller.act(engine, player, plan.intent)
        return ProgramIntentTurn(result=result, plan=plan)

    def reset(self) -> None:
        """Reset both the source program and canonical ledger."""
        self._planner.reset()
        self._controller.reset()

    def metadata(self) -> dict[str, object]:
        """Return actor-visible route-selection metadata."""
        return self._planner.metadata()


__all__ = [
    "NativeIntentTeacherBatch",
    "ProgramIntentPlan",
    "ProgramIntentPlanner",
    "ProgramIntentTeacher",
    "ProgramIntentTurn",
    "active_program_task",
    "encode_native_intent_plans",
]
