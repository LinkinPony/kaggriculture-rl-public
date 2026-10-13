"""Replay action-language audit and lossless unit-trace compression."""

from __future__ import annotations

from dataclasses import dataclass

from kagg_revue.policy.tasks.contract import (
    TaskOperation,
    UnitTask,
    deterministic_path,
)

_DIRECTIONS = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}
_OPPOSITE = {
    "NORTH": "SOUTH",
    "SOUTH": "NORTH",
    "EAST": "WEST",
    "WEST": "EAST",
}
_OPERATIONS = {operation.name: operation for operation in TaskOperation if operation.is_official}


@dataclass(frozen=True, slots=True)
class UnitTraceStep:
    """One official unit request and its position before execution."""

    step: int
    position: tuple[int, int]
    action: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class TapeAudit:
    """Lossless task tape plus language-pressure diagnostics."""

    tasks: tuple[UnitTask, ...]
    raw_actions: int
    compressed_tasks: int
    waypoint_tasks: int
    reversals: int
    waited_turns: int
    day_end_truncated: bool
    exact_reconstruction: bool


def _advance(position: tuple[int, int], direction: str) -> tuple[int, int]:
    dx, dy = _DIRECTIONS[direction]
    return position[0] + dx, position[1] + dy


def _canonical_endpoints(
    start: tuple[int, int], directions: list[str]
) -> tuple[tuple[int, int], ...]:
    """Split an observed path into longest canonical x-first subpaths."""
    positions = [start]
    for direction in directions:
        positions.append(_advance(positions[-1], direction))
    endpoints: list[tuple[int, int]] = []
    first = 0
    while first < len(directions):
        best = first + 1
        for end in range(first + 1, len(directions) + 1):
            expected = deterministic_path(positions[first], positions[end])
            if expected == tuple(directions[first:end]):
                best = end
        endpoints.append(positions[best])
        first = best
    return tuple(endpoints)


def _operation_task(
    action: tuple[object, ...],
    target: tuple[int, int],
    earliest: int,
    deadline: int,
) -> UnitTask:
    name = str(action[0])
    operation = _OPERATIONS.get(name)
    if operation is None:
        raise ValueError(f"unit trace contains unsupported operation {name!r}")
    argument = str(action[1]) if operation.needs_argument and len(action) > 1 else None
    quantity = 1 if operation.needs_quantity else 0
    if operation.needs_quantity and len(action) > 2:
        raw_quantity = action[2]
        if not isinstance(raw_quantity, int) or isinstance(raw_quantity, bool):
            raise ValueError("unit trace operation quantity must be an integer")
        quantity = raw_quantity
    return UnitTask(
        operation=operation,
        target=target,
        argument=argument,
        quantity=quantity,
        earliest_start=earliest,
        deadline=deadline,
    )


def expand_task_tape(
    tasks: tuple[UnitTask, ...],
    start: tuple[int, int],
    *,
    start_time: int,
) -> tuple[tuple[object, ...], ...]:
    """Expand an audited tape with the production compiler's x-first semantics."""
    position = start
    hour = start_time
    actions: list[tuple[object, ...]] = []
    for task in tasks:
        if task.operation is TaskOperation.WAIT:
            while hour < task.earliest_start:
                actions.append(("PASS",))
                hour += 1
            continue
        if task.target is None:
            raise ValueError("expanded targeted task lacks a target")
        for direction in deterministic_path(position, task.target):
            actions.append((direction,))
            position = _advance(position, direction)
            hour += 1
        while hour < task.earliest_start:
            actions.append(("PASS",))
            hour += 1
        if task.operation.is_official:
            actions.append(tuple(task.official_action()))
            hour += 1
    return tuple(actions)


def compress_unit_trace(
    steps: tuple[UnitTraceStep, ...],
    *,
    board_size: int,
    day_end: int,
) -> TapeAudit:
    """Compress one day-local unit trace without inventing strategic behavior."""
    if not steps:
        raise ValueError("unit trace cannot be empty")
    if board_size < 1 or day_end < 1:
        raise ValueError("unit trace environment dimensions must be positive")
    for previous, current in zip(steps, steps[1:], strict=False):
        if current.step != previous.step + 1:
            raise ValueError("unit trace steps must be contiguous")
    if steps[0].step < 0 or steps[-1].step >= day_end:
        raise ValueError("unit trace lies outside its day-local time line")

    initial = steps[0].position
    position = initial
    segment_start = initial
    available = steps[0].step
    directions: list[str] = []
    pass_count = 0
    tasks: list[UnitTask] = []
    waypoint_tasks = 0
    reversals = 0
    waited = 0

    def emit_path(*, retain_final: bool) -> tuple[tuple[int, int], ...]:
        nonlocal available, segment_start, waypoint_tasks
        endpoints = _canonical_endpoints(segment_start, directions)
        selected = endpoints[:-1] if retain_final and endpoints else endpoints
        for endpoint in selected:
            distance = len(deterministic_path(segment_start, endpoint))
            available += distance
            task = UnitTask(
                operation=TaskOperation.POSITION,
                target=endpoint,
                argument=None,
                quantity=0,
                earliest_start=available,
                deadline=available,
            )
            task.validate(board_size=board_size, day_end=day_end)
            tasks.append(task)
            waypoint_tasks += 1
            segment_start = endpoint
        return endpoints

    for trace in steps:
        if trace.position != position:
            raise ValueError("unit trace position does not match the preceding action")
        if not trace.action:
            raise ValueError("unit trace action cannot be empty")
        name = str(trace.action[0])
        if name in _DIRECTIONS:
            if pass_count:
                emit_path(retain_final=False)
                directions.clear()
                wait_until = trace.step
                wait = UnitTask(
                    operation=TaskOperation.WAIT,
                    target=None,
                    argument=None,
                    quantity=0,
                    earliest_start=wait_until,
                    deadline=wait_until,
                )
                wait.validate(board_size=board_size, day_end=day_end)
                tasks.append(wait)
                available = wait_until
                waited += pass_count
                pass_count = 0
                segment_start = position
            if directions and _OPPOSITE[directions[-1]] == name:
                reversals += 1
            directions.append(name)
            position = _advance(position, name)
            if not (0 <= position[0] < board_size and 0 <= position[1] < board_size):
                raise ValueError("unit trace moves outside the board")
            continue
        if name == "PASS":
            pass_count += 1
            continue
        if name not in _OPERATIONS:
            raise ValueError(f"unit trace contains unsupported action {name!r}")
        endpoints = emit_path(retain_final=True)
        if endpoints:
            segment_start = endpoints[-2] if len(endpoints) > 1 else segment_start
        operation = _operation_task(
            trace.action,
            position,
            trace.step,
            trace.step + 1,
        )
        operation.validate(board_size=board_size, day_end=day_end)
        tasks.append(operation)
        available = trace.step + 1
        waited += pass_count
        pass_count = 0
        directions.clear()
        segment_start = position

    trailing = bool(directions or pass_count)
    if directions:
        emit_path(retain_final=False)
        directions.clear()
    if pass_count:
        wait_until = steps[-1].step + 1
        wait = UnitTask(
            operation=TaskOperation.WAIT,
            target=None,
            argument=None,
            quantity=0,
            earliest_start=wait_until,
            deadline=wait_until,
        )
        wait.validate(board_size=board_size, day_end=day_end)
        tasks.append(wait)
        waited += pass_count
    raw = tuple(_canonical_action(step.action) for step in steps)
    reconstructed = expand_task_tape(tuple(tasks), initial, start_time=steps[0].step)
    return TapeAudit(
        tasks=tuple(tasks),
        raw_actions=len(steps),
        compressed_tasks=len(tasks),
        waypoint_tasks=waypoint_tasks,
        reversals=reversals,
        waited_turns=waited,
        day_end_truncated=trailing and steps[-1].step + 1 == day_end,
        exact_reconstruction=reconstructed == raw,
    )


def _canonical_action(action: tuple[object, ...]) -> tuple[object, ...]:
    """Normalize optional official quantities before semantic comparison."""
    if action and str(action[0]) in {"PICKUP", "PLACE"} and len(action) == 2:
        return (*action, 1)
    return action


__all__ = [
    "TapeAudit",
    "UnitTraceStep",
    "compress_unit_trace",
    "expand_task_tape",
]
