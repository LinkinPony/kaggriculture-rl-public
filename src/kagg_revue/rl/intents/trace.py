"""Lossless Rank8 trace interpretation for the intent language audit."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import cast

from kagg_revue.policy.tasks.contract import ANIMALS, TaskOperation, UnitTask
from kagg_revue.rl.intents.oracle import OracleTurnDirective
from kagg_revue.rl.intents.transaction import canonical_unit_action
from kagg_revue.rl.tasks.replay import UnitTraceStep, compress_unit_trace, expand_task_tape


@dataclass(frozen=True, slots=True)
class TraceTurn:
    """One source turn paired with pre-action unit positions."""

    positions: tuple[tuple[int, int], ...]
    action: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class TraceAudit:
    """Lossless task interpretation and language-pressure counts."""

    directives: tuple[OracleTurnDirective, ...]
    unit_actions: Mapping[str, int]
    market_actions: Mapping[str, int]
    semantic_tasks: Mapping[str, int]
    intent_pressure: Mapping[str, int]
    pickup_items: Mapping[str, int]
    pickup_quantities: Mapping[str, int]
    pickup_consumers: Mapping[str, int]
    pickup_actor_roles: Mapping[str, int]
    bulk_pickup_actor_roles: Mapping[str, int]
    sequences: int
    exact_sequences: int
    waypoint_tasks: int
    path_reversals: int
    multi_moving_hand_turns: int
    maximum_simultaneous_moves: int
    failure_examples: tuple[Mapping[str, object], ...]


def trace_turn(
    observation: Mapping[str, object], player: int, action: Mapping[str, object]
) -> TraceTurn:
    """Capture the positions needed to interpret one source action."""
    farm = cast(Sequence[Mapping[str, object]], observation["farms"])[player]
    raw_positions = [farm["farmer"], *cast(Sequence[object], farm["hands"])]
    positions = tuple(
        (int(cast(Sequence[int], value)[0]), int(cast(Sequence[int], value)[1]))
        for value in raw_positions
    )
    return TraceTurn(positions=positions, action=deepcopy(action))


def unit_actions(action: Mapping[str, object]) -> tuple[tuple[object, ...], ...]:
    """Return normalized farmer and hand actions in unit order."""
    farmer = cast(Sequence[object], action["farmer"])
    hands = cast(Sequence[Sequence[object]], action["hands"])
    return (canonical_unit_action(farmer),) + tuple(canonical_unit_action(value) for value in hands)


def _following_consumer(task: UnitTask, suffix: Sequence[UnitTask]) -> UnitTask | None:
    if task.operation is not TaskOperation.PICKUP:
        return suffix[0] if suffix else None
    for candidate in suffix:
        if candidate.operation is TaskOperation.PLACE and candidate.argument == task.argument:
            return candidate
        if task.argument == "WHEAT" and candidate.operation is TaskOperation.FEED:
            return candidate
        if task.argument == "FERTILIZER" and candidate.operation is TaskOperation.FERTILIZE:
            return candidate
    return None


def _task_timeline(
    steps: Sequence[UnitTraceStep], tasks: Sequence[UnitTask]
) -> tuple[dict[int, UnitTask], dict[int, UnitTask | None]]:
    if not steps:
        return {}, {}
    by_hour = {step.step: canonical_unit_action(step.action) for step in steps}
    active: dict[int, UnitTask] = {}
    following: dict[int, UnitTask | None] = {}
    position = steps[0].position
    hour = steps[0].step
    for index, task in enumerate(tasks):
        expanded = expand_task_tape((task,), position, start_time=hour)
        next_task = _following_consumer(task, tasks[index + 1 :])
        for action in expanded:
            if by_hour.get(hour) != canonical_unit_action(action):
                raise RuntimeError("lossless task tape lost its source-hour alignment")
            active[hour] = task
            following[hour] = next_task
            hour += 1
        if task.target is not None:
            position = task.target
    if set(active) != set(by_hour):
        raise RuntimeError("lossless task tape does not cover every source hour")
    return active, following


def compile_trace(
    turns: Sequence[TraceTurn],
    *,
    board_size: int,
    turns_per_day: int,
    identity: Mapping[str, object],
) -> TraceAudit:
    """Compress a complete source game and build hindsight directives."""
    sequences: dict[tuple[int, int], list[UnitTraceStep]] = defaultdict(list)
    unit_action_counts: Counter[str] = Counter()
    market_action_counts: Counter[str] = Counter()
    multi_moving = 0
    maximum_moving = 0
    for step, turn in enumerate(turns):
        actions = unit_actions(turn.action)
        moving = sum(str(action[0]) in {"NORTH", "SOUTH", "EAST", "WEST"} for action in actions)
        moving_hands = sum(
            unit > 0 and str(action[0]) in {"NORTH", "SOUTH", "EAST", "WEST"}
            for unit, action in enumerate(actions)
        )
        multi_moving += moving_hands > 1
        maximum_moving = max(maximum_moving, moving)
        day, hour = divmod(step, turns_per_day)
        for unit, (position, action) in enumerate(zip(turn.positions, actions, strict=True)):
            unit_action_counts[str(action[0])] += 1
            sequences[(day, unit)].append(
                UnitTraceStep(step=hour, position=position, action=action)
            )
        market = cast(Sequence[Sequence[object]], turn.action["market"])
        market_action_counts.update(str(order[0]) for order in market)

    active_by_step: dict[int, dict[int, UnitTask]] = defaultdict(dict)
    next_by_step: dict[int, dict[int, UnitTask | None]] = defaultdict(dict)
    task_records: list[tuple[int, UnitTask]] = []
    semantic_tasks: Counter[str] = Counter()
    pressure: Counter[str] = Counter()
    pickup_items: Counter[str] = Counter()
    pickup_quantities: Counter[str] = Counter()
    pickup_consumers: Counter[str] = Counter()
    pickup_actor_roles: Counter[str] = Counter()
    bulk_pickup_actor_roles: Counter[str] = Counter()
    failures: list[Mapping[str, object]] = []
    exact = 0
    waypoints = 0
    reversals = 0
    for (day, unit), steps in sequences.items():
        try:
            tape = compress_unit_trace(tuple(steps), board_size=board_size, day_end=turns_per_day)
            active, following = _task_timeline(steps, tape.tasks)
        except (RuntimeError, ValueError) as error:
            if len(failures) < 20:
                failures.append({**identity, "day": day, "unit": unit, "reason": str(error)})
            continue
        if not tape.exact_reconstruction:
            if len(failures) < 20:
                failures.append({**identity, "day": day, "unit": unit, "reason": "not_lossless"})
            continue
        exact += 1
        waypoints += tape.waypoint_tasks
        reversals += tape.reversals
        for index, task in enumerate(tape.tasks):
            semantic_tasks[task.operation.name] += 1
            if task.operation is TaskOperation.WAIT:
                pressure["temporal_guard_absent"] += 1
            elif task.operation is TaskOperation.DROP:
                pressure["store_all_absent"] += 1
            elif task.operation is TaskOperation.PICKUP:
                pickup_items[str(task.argument)] += 1
                pickup_quantities[str(task.quantity)] += 1
                actor_role = "FARMER" if unit == 0 else "HAND"
                pickup_actor_roles[actor_role] += 1
                consumer = _following_consumer(task, tape.tasks[index + 1 :])
                pickup_consumers["NONE" if consumer is None else consumer.operation.name] += 1
                if consumer is None:
                    pressure["standalone_fetch_absent"] += 1
                if task.quantity > 1:
                    pressure["bulk_fetch_absent"] += 1
                    bulk_pickup_actor_roles[actor_role] += 1
            elif task.operation is TaskOperation.POSITION and unit > 0:
                pressure["specific_hand_identity_absent"] += 1
        for hour, task in active.items():
            absolute = day * turns_per_day + hour
            active_by_step[absolute][unit] = task
            next_by_step[absolute][unit] = following[hour]
            task_records.append((absolute, task))

    directives: list[OracleTurnDirective] = []
    ordered_tasks = sorted(task_records, key=lambda value: value[0])
    for step, turn in enumerate(turns):
        unit_count = len(unit_actions(turn.action))
        animal_hints: dict[tuple[int, int], str] = {}
        for future_step, task in ordered_tasks:
            if future_step < step or task.target is None:
                continue
            if task.operation is TaskOperation.PLACE and task.argument in ANIMALS:
                animal_hints.setdefault(task.target, task.argument)
        directives.append(
            OracleTurnDirective(
                action=turn.action,
                active_tasks=tuple(active_by_step[step].get(unit) for unit in range(unit_count)),
                next_tasks=tuple(next_by_step[step].get(unit) for unit in range(unit_count)),
                animal_hints=animal_hints,
            )
        )
    return TraceAudit(
        directives=tuple(directives),
        unit_actions=dict(unit_action_counts),
        market_actions=dict(market_action_counts),
        semantic_tasks=dict(semantic_tasks),
        intent_pressure=dict(pressure),
        pickup_items=dict(pickup_items),
        pickup_quantities=dict(pickup_quantities),
        pickup_consumers=dict(pickup_consumers),
        pickup_actor_roles=dict(pickup_actor_roles),
        bulk_pickup_actor_roles=dict(bulk_pickup_actor_roles),
        sequences=len(sequences),
        exact_sequences=exact,
        waypoint_tasks=waypoints,
        path_reversals=reversals,
        multi_moving_hand_turns=multi_moving,
        maximum_simultaneous_moves=maximum_moving,
        failure_examples=tuple(failures),
    )


def adapt_source_units(
    action: Mapping[str, object], hand_count: int
) -> tuple[tuple[object, ...], ...]:
    """Align one source bundle to the oracle game's live hand count."""
    farmer = canonical_unit_action(cast(Sequence[object], action["farmer"]))
    hands = cast(Sequence[Sequence[object]], action["hands"])
    return (farmer,) + tuple(
        canonical_unit_action(hands[index]) if index < len(hands) else ("PASS",)
        for index in range(hand_count)
    )


__all__ = [
    "TraceAudit",
    "TraceTurn",
    "adapt_source_units",
    "compile_trace",
    "trace_turn",
    "unit_actions",
]
