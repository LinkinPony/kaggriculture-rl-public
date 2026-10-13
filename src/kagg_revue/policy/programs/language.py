"""Static conditional-branch requirements for the program action language."""

from kagg_revue.policy.programs.contract import (
    MarketOrderType,
    RawOperation,
    TaskType,
)

TASK_ARGUMENT_REQUIRED = tuple(
    task
    in {
        TaskType.SAFE_PLANT,
        TaskType.BUILD,
        TaskType.DEPLOY_ANIMAL,
        TaskType.FETCH,
        TaskType.STORE,
        TaskType.PLANT,
    }
    for task in TaskType
)
TASK_TARGET_REQUIRED = tuple(task is not TaskType.WAIT for task in TaskType)
TASK_QUANTITY_REQUIRED = tuple(
    task in {TaskType.FETCH, TaskType.STORE} for task in TaskType
)
RAW_ARGUMENT_REQUIRED = tuple(
    operation in {RawOperation.PICKUP, RawOperation.PLACE, RawOperation.PLANT}
    for operation in RawOperation
)
RAW_QUANTITY_REQUIRED = tuple(
    operation in {RawOperation.PICKUP, RawOperation.PLACE}
    for operation in RawOperation
)
MARKET_ITEM_REQUIRED = tuple(
    order
    in {
        MarketOrderType.SELL,
        MarketOrderType.BUY_SEED,
        MarketOrderType.BUY_PRODUCT,
        MarketOrderType.BUY_ANIMAL,
    }
    for order in MarketOrderType
)

__all__ = [
    "MARKET_ITEM_REQUIRED",
    "RAW_ARGUMENT_REQUIRED",
    "RAW_QUANTITY_REQUIRED",
    "TASK_ARGUMENT_REQUIRED",
    "TASK_QUANTITY_REQUIRED",
    "TASK_TARGET_REQUIRED",
]
