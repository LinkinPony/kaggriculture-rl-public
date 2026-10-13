"""Stable conditional-action language for persistent turn programs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

PROGRAM_ABI_VERSION = "conditional-turn-program-v2"

ITEM_NAMES = (
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
CROP_COUNT = 5
PRODUCT_COUNT = 9
ANIMAL_FIRST = 9
ANIMAL_COUNT = 3
COOP_ARGUMENT = len(ITEM_NAMES)
PASTURE_ARGUMENT = COOP_ARGUMENT + 1
NONE_ARGUMENT = PASTURE_ARGUMENT + 1
ARGUMENT_COUNT = NONE_ARGUMENT + 1


class ControlType(IntEnum):
    """Root branch sampled once for every visible unit."""

    KEEP = 0
    ASSIGN = 1
    STEP = 2
    RAW_LOCAL = 3
    CANCEL_PASS = 4


class Direction(IntEnum):
    """Exact one-cell movement escape branch."""

    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3


class TaskType(IntEnum):
    """Persistent semantic options selected by the actor."""

    SAFE_PLANT = 0
    WATER = 1
    HARVEST = 2
    FERTILIZE = 3
    DIG = 4
    BUILD = 5
    DEPLOY_ANIMAL = 6
    FEED = 7
    CARE = 8
    COLLECT = 9
    FETCH = 10
    STORE = 11
    GO_TO = 12
    PLANT = 13
    STORE_ALL = 14
    WAIT = 15


class RawOperation(IntEnum):
    """Official non-movement operations available at the current tile."""

    PICKUP = 0
    DROP = 1
    PLACE = 2
    PLANT = 3
    WATER = 4
    HARVEST = 5
    FERTILIZE = 6
    DIG = 7
    BUILD_COOP = 8
    BUILD_PASTURE = 9
    FEED = 10
    COLLECT_FERTILIZER = 11
    CARE = 12


class MarketOrderType(IntEnum):
    """Conditional root of one ordered market slot."""

    END = 0
    SELL = 1
    BUY_SEED = 2
    BUY_PRODUCT = 3
    BUY_ANIMAL = 4
    HIRE = 5
    BUY_LAND = 6


class QuantityMode(IntEnum):
    """Semantic quantities with an exact, lossless integer fallback."""

    ONE = 0
    ALL_AVAILABLE = 1
    PLAN_DEFICIT = 2
    MAX_AFFORDABLE = 3
    EXACT = 4


class OptionPhase(IntEnum):
    """Compiler-owned progress within a persistent semantic task."""

    APPROACH = 0
    OPERATE = 1
    FETCH = 2
    BUILD = 3
    PLACE = 4
    WATER = 5


class ProgramPhase(IntEnum):
    """Current autoregressive branch exposed by the native compiler."""

    UNIT = 0
    MARKET = 1
    DONE = 2


@dataclass(frozen=True, slots=True)
class UnitDecision:
    """One actor-owned conditional unit choice."""

    control: ControlType
    task: TaskType = TaskType.GO_TO
    target: int = -1
    argument: int = NONE_ARGUMENT
    direction: Direction = Direction.NORTH
    raw_operation: RawOperation = RawOperation.DROP
    quantity_mode: QuantityMode = QuantityMode.ONE
    exact_quantity: int = 1


@dataclass(frozen=True, slots=True)
class MarketDecision:
    """One actor-owned conditional market order."""

    order_type: MarketOrderType
    item: int = 0
    quantity_mode: QuantityMode = QuantityMode.ONE
    exact_quantity: int = 1


@dataclass(slots=True)
class OptionState:
    """Interruptible compiler state retained across environment turns."""

    task: TaskType
    target: int
    argument: int
    quantity_mode: QuantityMode
    exact_quantity: int
    phase: OptionPhase
    created_step: int


TASKS_REQUIRING_TARGET = frozenset(
    {
        TaskType.SAFE_PLANT,
        TaskType.WATER,
        TaskType.HARVEST,
        TaskType.FERTILIZE,
        TaskType.DIG,
        TaskType.BUILD,
        TaskType.DEPLOY_ANIMAL,
        TaskType.FEED,
        TaskType.CARE,
        TaskType.COLLECT,
        TaskType.FETCH,
        TaskType.STORE,
        TaskType.GO_TO,
        TaskType.PLANT,
        TaskType.STORE_ALL,
    }
)
TASKS_REQUIRING_ARGUMENT = frozenset(
    {
        TaskType.SAFE_PLANT,
        TaskType.BUILD,
        TaskType.DEPLOY_ANIMAL,
        TaskType.FETCH,
        TaskType.STORE,
        TaskType.PLANT,
    }
)
TASKS_REQUIRING_QUANTITY = frozenset({TaskType.FETCH, TaskType.STORE})
RAW_REQUIRING_ARGUMENT = frozenset({RawOperation.PICKUP, RawOperation.PLACE, RawOperation.PLANT})
RAW_REQUIRING_QUANTITY = frozenset({RawOperation.PICKUP, RawOperation.PLACE})
MARKET_REQUIRING_ITEM = frozenset(
    {
        MarketOrderType.SELL,
        MarketOrderType.BUY_SEED,
        MarketOrderType.BUY_PRODUCT,
        MarketOrderType.BUY_ANIMAL,
    }
)
MARKET_REQUIRING_QUANTITY = MARKET_REQUIRING_ITEM


__all__ = [
    "ANIMAL_COUNT",
    "ANIMAL_FIRST",
    "ARGUMENT_COUNT",
    "COOP_ARGUMENT",
    "CROP_COUNT",
    "ControlType",
    "Direction",
    "ITEM_NAMES",
    "MARKET_REQUIRING_ITEM",
    "MARKET_REQUIRING_QUANTITY",
    "MarketDecision",
    "MarketOrderType",
    "NONE_ARGUMENT",
    "OptionPhase",
    "OptionState",
    "PASTURE_ARGUMENT",
    "PRODUCT_COUNT",
    "PROGRAM_ABI_VERSION",
    "ProgramPhase",
    "QuantityMode",
    "RAW_REQUIRING_ARGUMENT",
    "RAW_REQUIRING_QUANTITY",
    "RawOperation",
    "TASKS_REQUIRING_ARGUMENT",
    "TASKS_REQUIRING_QUANTITY",
    "TASKS_REQUIRING_TARGET",
    "TaskType",
    "UnitDecision",
]
