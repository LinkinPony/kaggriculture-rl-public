"""Validated Python boundary for the native conditional-program ABI."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import torch
from torch import Tensor

from kagg_revue.policy.programs.contract import (
    ARGUMENT_COUNT,
    ITEM_NAMES,
    PROGRAM_ABI_VERSION,
    ControlType,
    Direction,
    MarketOrderType,
    QuantityMode,
    RawOperation,
    TaskType,
)

if TYPE_CHECKING:
    from kagg_revue.policy.programs.grammar import (
        NativeProgramMasks,
        ProgramDecisionInputs,
    )
    from kagg_revue.policy.programs.schema import ProgramArchitecture


def _positive(raw: Mapping[str, object], name: str) -> int:
    value = raw.get(name)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"native conditional-program {name} must be positive")
    return value


def _names(raw: Mapping[str, object], name: str, count: int) -> tuple[str, ...]:
    values = raw.get(name)
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise ValueError(f"native conditional-program {name} must be a name sequence")
    result = tuple(str(value) for value in values)
    if len(result) != count or len(set(result)) != count:
        raise ValueError(f"native conditional-program {name} must be unique and complete")
    return result


@dataclass(frozen=True, slots=True)
class NativeProgramContract:
    """Authenticated tensor dimensions exported by the C++ compiler."""

    version: str
    control_count: int
    direction_count: int
    task_count: int
    raw_operation_count: int
    market_order_count: int
    quantity_mode_count: int
    argument_count: int
    item_count: int
    board_size: int
    unit_limit: int
    maximum_market_orders: int
    maximum_decisions: int
    root_feature_count: int
    option_feature_count: int
    maximum_exact_quantity: int
    exact_quantity_bits: int
    root_feature_names: tuple[str, ...]
    option_feature_names: tuple[str, ...]

    @classmethod
    def from_spec(cls, raw: Mapping[str, object]) -> NativeProgramContract:
        """Validate native dimensions before they define a model artifact."""
        version = str(raw.get("version"))
        if version != PROGRAM_ABI_VERSION:
            raise ValueError("native conditional-program ABI version is unsupported")

        expected_counts = {
            "control_count": len(ControlType),
            "direction_count": len(Direction),
            "task_count": len(TaskType),
            "raw_operation_count": len(RawOperation),
            "market_order_count": len(MarketOrderType),
            "quantity_mode_count": len(QuantityMode),
            "argument_count": ARGUMENT_COUNT,
            "item_count": len(ITEM_NAMES),
        }
        measured = {name: _positive(raw, name) for name in expected_counts}
        for name, expected in expected_counts.items():
            if measured[name] != expected:
                raise ValueError(f"native conditional-program {name} differs from its ABI")

        unit_limit = _positive(raw, "unit_limit")
        maximum_market_orders = _positive(raw, "maximum_market_orders")
        maximum_decisions = _positive(raw, "maximum_decisions")
        if maximum_decisions != unit_limit + maximum_market_orders:
            raise ValueError("native conditional-program decision capacity is inconsistent")
        root_features = _positive(raw, "root_feature_count")
        option_features = _positive(raw, "option_feature_count")
        maximum_exact_quantity = _positive(raw, "maximum_exact_quantity")
        exact_quantity_bits = _positive(raw, "exact_quantity_bits")
        if maximum_exact_quantity.bit_length() != exact_quantity_bits:
            raise ValueError(
                "native conditional-program exact quantity width is inconsistent"
            )
        return cls(
            version=version,
            **measured,
            board_size=_positive(raw, "board_size"),
            unit_limit=unit_limit,
            maximum_market_orders=maximum_market_orders,
            maximum_decisions=maximum_decisions,
            root_feature_count=root_features,
            option_feature_count=option_features,
            maximum_exact_quantity=maximum_exact_quantity,
            exact_quantity_bits=exact_quantity_bits,
            root_feature_names=_names(raw, "root_features", root_features),
            option_feature_names=_names(raw, "option_features", option_features),
        )

    @property
    def tile_count(self) -> int:
        """Number of entries in the lossless board pointer."""
        return self.board_size * self.board_size

    def architecture(
        self,
        *,
        context_width: int,
        model_width: int,
        feedforward_width: int,
    ) -> ProgramArchitecture:
        """Build one checkpoint shape from measured native capacities."""
        from kagg_revue.policy.programs.schema import ProgramArchitecture

        return ProgramArchitecture(
            architecture_version="conditional-program-v2",
            context_width=context_width,
            model_width=model_width,
            feedforward_width=feedforward_width,
            board_size=self.board_size,
            unit_limit=self.unit_limit,
            maximum_market_orders=self.maximum_market_orders,
            control_count=self.control_count,
            direction_count=self.direction_count,
            task_count=self.task_count,
            raw_operation_count=self.raw_operation_count,
            market_order_count=self.market_order_count,
            quantity_mode_count=self.quantity_mode_count,
            argument_count=self.argument_count,
            item_count=self.item_count,
            root_feature_count=self.root_feature_count,
            option_feature_count=self.option_feature_count,
            exact_quantity_bits=self.exact_quantity_bits,
            native_abi_version=self.version,
        )


def decision_inputs(
    raw: Mapping[str, Any],
    context: Tensor,
    tile_tokens: Tensor,
    contract: NativeProgramContract,
    *,
    device: torch.device | str,
    validate: bool = False,
) -> tuple[ProgramDecisionInputs, NativeProgramMasks]:
    """Move one native decision batch into the typed tensor ABI."""
    from kagg_revue.policy.programs.grammar import (
        NativeProgramMasks,
        ProgramDecisionInputs,
    )

    def tensor(key: str, dtype: torch.dtype) -> Tensor:
        return torch.as_tensor(np.asarray(raw[key]), dtype=dtype, device=device)

    scalars = tensor("scalars", torch.long)
    if scalars.ndim != 2 or scalars.shape[1] != 7:
        raise ValueError("native conditional-program scalars must have shape [B,7]")
    inputs = ProgramDecisionInputs(
        context=context.to(device),
        tile_tokens=tile_tokens.to(device),
        root_features=tensor("root_features", torch.float32),
        option_features=tensor("option_features", torch.long),
        target_reservations=tensor("target_reservations", torch.int16),
        phase=scalars[:, 0],
        unit_index=scalars[:, 1],
        market_slot=scalars[:, 2],
        unit_count=scalars[:, 3],
        current_x=scalars[:, 4],
        current_y=scalars[:, 5],
        forced=scalars[:, 6],
    )
    masks = NativeProgramMasks(
        control=tensor("control_mask", torch.bool),
        direction=tensor("direction_mask", torch.bool),
        task=tensor("task_mask", torch.bool),
        task_argument=tensor("task_argument_mask", torch.bool),
        task_target=tensor("task_target_mask", torch.bool),
        task_quantity_mode=tensor("task_quantity_mode_mask", torch.bool),
        task_quantity_max=tensor("task_quantity_max", torch.long),
        raw_operation=tensor("raw_operation_mask", torch.bool),
        raw_argument=tensor("raw_argument_mask", torch.bool),
        raw_quantity_mode=tensor("raw_quantity_mode_mask", torch.bool),
        raw_quantity_max=tensor("raw_quantity_max", torch.long),
        market_order=tensor("market_order_mask", torch.bool),
        market_item=tensor("market_item_mask", torch.bool),
        market_quantity_mode=tensor("market_quantity_mode_mask", torch.bool),
        market_quantity_max=tensor("market_quantity_max", torch.long),
    )
    if validate:
        inputs.validate(contract, context.shape[-1])
        masks.validate(inputs.batch_size, contract)
    return inputs, masks


__all__ = ["NativeProgramContract", "decision_inputs"]
