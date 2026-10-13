"""Stable semantic contract for actor-owned unit task tapes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

TASK_TAPE_ABI_VERSION = "unit-task-tape-v1"

ITEMS = (
    "WHEAT",
    "CARROT",
    "TOMATO",
    "STRAWBERRY",
    "MELON",
    "EGG",
    "MILK",
    "WOOL",
    "FERTILIZER",
    "GOOSE",
    "COW",
    "SHEEP",
)
CROPS = ITEMS[:5]
ANIMALS = ITEMS[9:]


class TaskOperation(IntEnum):
    """Only semantic operations the unit-task actor may select."""

    END = 0
    POSITION = 1
    WAIT = 2
    PICKUP = 3
    DROP = 4
    PLACE = 5
    PLANT = 6
    WATER = 7
    HARVEST = 8
    FERTILIZE = 9
    DIG = 10
    BUILD_COOP = 11
    BUILD_PASTURE = 12
    FEED = 13
    COLLECT_FERTILIZER = 14
    CARE = 15

    @property
    def is_official(self) -> bool:
        """Return whether this task ends in one official non-movement action."""
        return self.value >= TaskOperation.PICKUP.value

    @property
    def needs_target(self) -> bool:
        """Return whether this task names one farm tile."""
        return self not in {TaskOperation.END, TaskOperation.WAIT}

    @property
    def needs_argument(self) -> bool:
        """Return whether this operation carries an item or crop identity."""
        return self in {
            TaskOperation.PICKUP,
            TaskOperation.PLACE,
            TaskOperation.PLANT,
        }

    @property
    def needs_quantity(self) -> bool:
        """Return whether this operation carries an exact positive quantity."""
        return self in {TaskOperation.PICKUP, TaskOperation.PLACE}


class TaskFeasibilityReason(IntEnum):
    """Exact hard-mask reason exposed as an actor-visible candidate fact."""

    FEASIBLE = 0
    END = 1
    OUT_OF_TIME = 2
    NO_PROGRESS = 3
    INVALID_GEOMETRY = 4
    INVALID_PARAMETER = 5


class TaskResultStatus(IntEnum):
    """Actor-visible result of one accepted task."""

    COMPLETED = 0
    TARGET_INVALID = 1
    RESOURCE_CONFLICT = 2
    NO_OP = 3
    MISSED_DEADLINE = 4
    DAY_ENDED = 5
    UNIT_REMOVED = 6
    REPLACED = 7


class ReplanReason(IntEnum):
    """Why the actor is being offered a task-tape decision."""

    DAY_START = 0
    NEW_UNIT = 1
    QUEUE_EMPTY = 2
    TASK_COMPLETED = 3
    TARGET_INVALID = 4
    OPERATION_FAILED = 5
    DEADLINE_MISSED = 6


class SuffixMode(IntEnum):
    """Permitted task-boundary treatment of an unexecuted suffix."""

    CONTINUE = 0
    REWRITE = 1


GridPosition = tuple[int, int]


@dataclass(frozen=True, slots=True)
class UnitTask:
    """One semantic task with at most one official unit operation."""

    operation: TaskOperation
    target: GridPosition | None
    argument: str | None
    quantity: int
    earliest_start: int
    deadline: int

    def validate(self, *, board_size: int, day_end: int) -> None:
        """Reject a task outside the authenticated environment contract."""
        if self.operation is TaskOperation.END:
            raise ValueError("END terminates decoding and cannot be stored on a task tape")
        if board_size < 1 or day_end < 1:
            raise ValueError("task environment dimensions must be positive")
        if self.operation.needs_target:
            if self.target is None:
                raise ValueError("targeted unit task lacks a target")
            x, y = self.target
            if not (0 <= x < board_size and 0 <= y < board_size):
                raise ValueError("unit task target is outside the farm board")
        elif self.target is not None:
            raise ValueError("untargeted unit task cannot carry a target")
        expected_arguments: tuple[str, ...]
        if self.operation is TaskOperation.PLANT:
            expected_arguments = CROPS
        elif self.operation in {TaskOperation.PICKUP, TaskOperation.PLACE}:
            expected_arguments = ITEMS
        else:
            expected_arguments = ()
        if expected_arguments:
            if self.argument not in expected_arguments:
                raise ValueError("unit task argument is outside its operation vocabulary")
        elif self.argument is not None:
            raise ValueError("argument-free unit task cannot carry an argument")
        if self.operation.needs_quantity:
            if self.quantity < 1:
                raise ValueError("quantity task requires a positive quantity")
        elif self.quantity != 0:
            raise ValueError("quantity-free unit task must use canonical zero")
        if not 0 <= self.earliest_start <= day_end:
            raise ValueError("unit task earliest start is outside the day")
        if not 0 <= self.deadline <= day_end:
            raise ValueError("unit task deadline is outside the day")
        if self.deadline < self.earliest_start:
            raise ValueError("unit task deadline precedes its earliest start")

    @property
    def operation_turns(self) -> int:
        """Return the official turns consumed after reaching the target."""
        return int(self.operation.is_official)

    def completion(self, position: GridPosition, available_at: int) -> int:
        """Return the deterministic earliest completion boundary."""
        distance = 0 if self.target is None else manhattan_distance(position, self.target)
        arrival = available_at + distance
        return max(arrival, self.earliest_start) + self.operation_turns

    def official_action(self) -> list[object]:
        """Compile the semantic effect without adding any movement choice."""
        if not self.operation.is_official:
            raise ValueError("position and wait tasks have no official operation")
        action: list[object] = [self.operation.name]
        if self.argument is not None:
            action.append(self.argument)
        if self.operation.needs_quantity:
            action.append(self.quantity)
        return action


@dataclass(frozen=True, slots=True)
class TaskPrefixState:
    """Exact simulated state before the next conditional task sample."""

    unit_index: int
    position: GridPosition
    available_at: int
    day_end: int
    tasks: tuple[UnitTask, ...] = ()

    @property
    def remaining(self) -> int:
        """Return independent time remaining for this unit."""
        return max(0, self.day_end - self.available_at)

    @property
    def capacity(self) -> int:
        """Return a derived upper bound on further progress-making tasks."""
        return self.remaining

    def append(self, task: UnitTask, *, board_size: int) -> TaskPrefixState:
        """Advance the simulated unit position and independent time line."""
        task.validate(board_size=board_size, day_end=self.day_end)
        completion = task.completion(self.position, self.available_at)
        if completion <= self.available_at:
            raise ValueError("accepted unit task must make temporal progress")
        if completion > task.deadline or completion > self.day_end:
            raise ValueError("accepted unit task cannot finish by its deadline")
        return TaskPrefixState(
            unit_index=self.unit_index,
            position=self.position if task.target is None else task.target,
            available_at=completion,
            day_end=self.day_end,
            tasks=(*self.tasks, task),
        )


@dataclass(frozen=True, slots=True)
class TaskDeclaration:
    """Actor-declared target and resource use visible to later unit prefixes."""

    unit_index: int
    task_index: int
    operation: TaskOperation
    target: GridPosition | None
    argument: str | None
    completion: int
    resource_key: str | None


@dataclass(frozen=True, slots=True)
class TaskFeedback:
    """Causal execution result retained for the next planning observation."""

    unit_index: int
    task: UnitTask
    status: TaskResultStatus
    step: int
    requested_action: tuple[object, ...] | None
    actual_action: tuple[object, ...] | None
    detail: str


def manhattan_distance(left: GridPosition, right: GridPosition) -> int:
    """Return obstacle-free official movement distance between two tiles."""
    return abs(left[0] - right[0]) + abs(left[1] - right[1])


def deterministic_path(start: GridPosition, target: GridPosition) -> tuple[str, ...]:
    """Return the canonical x-first shortest path used by the compiler."""
    x, y = start
    target_x, target_y = target
    actions: list[str] = []
    while x < target_x:
        actions.append("EAST")
        x += 1
    while x > target_x:
        actions.append("WEST")
        x -= 1
    while y < target_y:
        actions.append("SOUTH")
        y += 1
    while y > target_y:
        actions.append("NORTH")
        y -= 1
    return tuple(actions)


__all__ = [
    "ANIMALS",
    "CROPS",
    "ITEMS",
    "TASK_TAPE_ABI_VERSION",
    "GridPosition",
    "ReplanReason",
    "SuffixMode",
    "TaskDeclaration",
    "TaskFeasibilityReason",
    "TaskFeedback",
    "TaskOperation",
    "TaskPrefixState",
    "TaskResultStatus",
    "UnitTask",
    "deterministic_path",
    "manhattan_distance",
]
