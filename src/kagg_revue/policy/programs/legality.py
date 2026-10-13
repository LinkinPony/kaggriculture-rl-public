"""Typed legality masks emitted by the native shadow-state compiler."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

import numpy as np
from numpy.typing import NDArray

from kagg_revue.policy.programs.native import NativeProgramContract

BoolArray = NDArray[np.bool_]
IntArray = NDArray[np.int64]


def _flags(raw: Mapping[str, object], name: str, shape: tuple[int, ...]) -> BoolArray:
    value = np.asarray(raw[name])
    if value.shape != shape or value.dtype.kind not in "biu":
        raise ValueError(f"native conditional-program {name} differs from its declared shape")
    return cast(BoolArray, np.ascontiguousarray(value, dtype=np.bool_))


def _integers(raw: Mapping[str, object], name: str, shape: tuple[int, ...]) -> IntArray:
    value = np.asarray(raw[name])
    if value.shape != shape or value.dtype.kind not in "iu":
        raise ValueError(f"native conditional-program {name} differs from its declared shape")
    result = np.ascontiguousarray(value, dtype=np.int64)
    if np.any(result < 0):
        raise ValueError(f"native conditional-program {name} contains negatives")
    return result


@dataclass(frozen=True, slots=True)
class UnitMasks:
    """All active and conditional masks for one unit decision."""

    control: BoolArray
    direction: BoolArray
    task: BoolArray
    task_argument: BoolArray
    task_target: BoolArray
    task_quantity_mode: BoolArray
    task_quantity_max: IntArray
    raw_operation: BoolArray
    raw_argument: BoolArray
    raw_quantity_mode: BoolArray
    raw_quantity_max: IntArray

    @classmethod
    def from_raw(cls, raw: Mapping[str, object], contract: NativeProgramContract) -> UnitMasks:
        """Validate one native unit-mask surface."""
        task_args = (contract.task_count, contract.argument_count)
        raw_args = (contract.raw_operation_count, contract.argument_count)
        result = cls(
            control=_flags(raw, "control_mask", (contract.control_count,)),
            direction=_flags(raw, "direction_mask", (contract.direction_count,)),
            task=_flags(raw, "task_mask", (contract.task_count,)),
            task_argument=_flags(raw, "task_argument_mask", task_args),
            task_target=_flags(raw, "task_target_mask", (*task_args, contract.tile_count)),
            task_quantity_mode=_flags(
                raw,
                "task_quantity_mode_mask",
                (*task_args, contract.quantity_mode_count),
            ),
            task_quantity_max=_integers(raw, "task_quantity_max", task_args),
            raw_operation=_flags(raw, "raw_operation_mask", (contract.raw_operation_count,)),
            raw_argument=_flags(raw, "raw_argument_mask", raw_args),
            raw_quantity_mode=_flags(
                raw,
                "raw_quantity_mode_mask",
                (*raw_args, contract.quantity_mode_count),
            ),
            raw_quantity_max=_integers(raw, "raw_quantity_max", raw_args),
        )
        if not np.any(result.control):
            raise ValueError("native conditional-program unit has no legal control")
        return result


@dataclass(frozen=True, slots=True)
class MarketMasks:
    """All active and conditional masks for one ordered market slot."""

    order: BoolArray
    item: BoolArray
    quantity_mode: BoolArray
    quantity_max: IntArray

    @classmethod
    def from_raw(cls, raw: Mapping[str, object], contract: NativeProgramContract) -> MarketMasks:
        """Validate one native market-mask surface."""
        order_items = (contract.market_order_count, contract.item_count)
        result = cls(
            order=_flags(raw, "market_order_mask", (contract.market_order_count,)),
            item=_flags(raw, "market_item_mask", order_items),
            quantity_mode=_flags(
                raw,
                "market_quantity_mode_mask",
                (*order_items, contract.quantity_mode_count),
            ),
            quantity_max=_integers(raw, "market_quantity_max", order_items),
        )
        if not np.any(result.order):
            raise ValueError("native conditional-program market has no legal order")
        return result


__all__ = ["MarketMasks", "UnitMasks"]
