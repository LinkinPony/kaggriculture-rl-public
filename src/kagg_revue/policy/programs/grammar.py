"""Tensor grammar for conditional turn-program sampling and replay."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.programs.native import NativeProgramContract

PROGRAM_BASE_FACTOR_COUNT = 8


def _discrete(value: Tensor) -> bool:
    return not value.is_floating_point() and value.dtype != torch.bool


@dataclass(frozen=True)
class ProgramDecisionInputs:
    """Policy-visible state for one batched autoregressive decision."""

    context: Tensor
    tile_tokens: Tensor
    root_features: Tensor
    option_features: Tensor
    target_reservations: Tensor
    phase: Tensor
    unit_index: Tensor
    market_slot: Tensor
    unit_count: Tensor
    current_x: Tensor
    current_y: Tensor
    forced: Tensor

    @property
    def batch_size(self) -> int:
        """Return the number of independent live program rows."""
        return int(self.context.shape[0])

    def validate(self, contract: NativeProgramContract, context_width: int) -> None:
        """Validate exact shapes, devices, and discrete identities."""
        batch = self.batch_size
        tiles = contract.tile_count
        expected = {
            "context": (batch, context_width),
            "tile_tokens": (batch, tiles, context_width),
            "root_features": (batch, contract.root_feature_count),
            "option_features": (batch, contract.option_feature_count),
            "target_reservations": (batch, tiles),
            "phase": (batch,),
            "unit_index": (batch,),
            "market_slot": (batch,),
            "unit_count": (batch,),
            "current_x": (batch,),
            "current_y": (batch,),
            "forced": (batch,),
        }
        for name, shape in expected.items():
            if getattr(self, name).shape != shape:
                raise ValueError(f"conditional-program {name} has the wrong shape")
        values = tuple(getattr(self, name) for name in expected)
        if not all(value.device == self.context.device for value in values):
            raise ValueError("conditional-program inputs must share one device")
        if not self.context.is_floating_point() or not self.tile_tokens.is_floating_point():
            raise ValueError("conditional-program context and tiles must be floating point")
        if not self.root_features.is_floating_point():
            raise ValueError("conditional-program root features must be floating point")
        for name in expected.keys() - {"context", "tile_tokens", "root_features"}:
            if not _discrete(getattr(self, name)):
                raise ValueError(f"conditional-program {name} must be discrete")
        if bool(torch.any((self.phase < 0) | (self.phase > 1))):
            raise ValueError("conditional-program decision phase must be unit or market")
        if bool(
            torch.any(
                (self.unit_count < 1) | (self.unit_count > contract.unit_limit)
            )
        ):
            raise ValueError("conditional-program unit count is outside its ABI")


@dataclass(frozen=True)
class NativeProgramMasks:
    """Complete native conditional surface used only while sampling."""

    control: Tensor
    direction: Tensor
    task: Tensor
    task_argument: Tensor
    task_target: Tensor
    task_quantity_mode: Tensor
    task_quantity_max: Tensor
    raw_operation: Tensor
    raw_argument: Tensor
    raw_quantity_mode: Tensor
    raw_quantity_max: Tensor
    market_order: Tensor
    market_item: Tensor
    market_quantity_mode: Tensor
    market_quantity_max: Tensor

    def validate(self, batch: int, contract: NativeProgramContract) -> None:
        """Reject a native mask surface with any shape or device drift."""
        task_args = (batch, contract.task_count, contract.argument_count)
        raw_args = (batch, contract.raw_operation_count, contract.argument_count)
        market_items = (batch, contract.market_order_count, contract.item_count)
        expected = {
            "control": (batch, contract.control_count),
            "direction": (batch, contract.direction_count),
            "task": (batch, contract.task_count),
            "task_argument": task_args,
            "task_target": (*task_args, contract.tile_count),
            "task_quantity_mode": (*task_args, contract.quantity_mode_count),
            "task_quantity_max": task_args,
            "raw_operation": (batch, contract.raw_operation_count),
            "raw_argument": raw_args,
            "raw_quantity_mode": (*raw_args, contract.quantity_mode_count),
            "raw_quantity_max": raw_args,
            "market_order": (batch, contract.market_order_count),
            "market_item": market_items,
            "market_quantity_mode": (
                *market_items,
                contract.quantity_mode_count,
            ),
            "market_quantity_max": market_items,
        }
        device = self.control.device
        for name, shape in expected.items():
            value = getattr(self, name)
            if value.shape != shape:
                raise ValueError(
                    f"conditional-program native {name} has the wrong shape"
                )
            if value.device != device:
                raise ValueError("conditional-program native masks span devices")
            if name.endswith("max"):
                if not _discrete(value) or bool(torch.any(value < 0)):
                    raise ValueError(
                        "conditional-program quantity bounds must be nonnegative integers"
                    )
            elif value.is_floating_point():
                raise ValueError("conditional-program legality masks must be discrete")


@dataclass(frozen=True)
class ProgramActions:
    """One complete high-level choice with inactive fields canonicalized."""

    control: Tensor
    task: Tensor
    target: Tensor
    argument: Tensor
    direction: Tensor
    raw_operation: Tensor
    quantity_mode: Tensor
    exact_quantity: Tensor
    market_order: Tensor

    def validate(self, batch: int) -> None:
        """Require one integer vector per action field."""
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if value.shape != (batch,) or not _discrete(value):
                raise ValueError(
                    f"conditional-program action {name} must be an integer vector"
                )


@dataclass(frozen=True)
class ProgramConditionalMasks:
    """Selected conditional slices sufficient for exact PPO replay."""

    control: Tensor
    direction: Tensor
    task: Tensor
    argument: Tensor
    target: Tensor
    raw_operation: Tensor
    quantity_mode: Tensor
    market_order: Tensor
    market_item: Tensor
    quantity_max: Tensor

    def validate(self, batch: int, contract: NativeProgramContract) -> None:
        """Validate compact exact masks without inspecting repository config."""
        expected = {
            "control": (batch, contract.control_count),
            "direction": (batch, contract.direction_count),
            "task": (batch, contract.task_count),
            "argument": (batch, contract.argument_count),
            "target": (batch, contract.tile_count),
            "raw_operation": (batch, contract.raw_operation_count),
            "quantity_mode": (batch, contract.quantity_mode_count),
            "market_order": (batch, contract.market_order_count),
            "market_item": (batch, contract.item_count),
            "quantity_max": (batch,),
        }
        device = self.control.device
        for name, shape in expected.items():
            value = getattr(self, name)
            if value.shape != shape or value.device != device:
                raise ValueError(
                    f"conditional-program replay {name} has the wrong tensor ABI"
                )
            if name == "quantity_max":
                if not _discrete(value) or bool(torch.any(value < 0)):
                    raise ValueError("conditional-program replay quantity bound is invalid")
            elif value.is_floating_point():
                raise ValueError("conditional-program replay masks must be discrete")


@dataclass(frozen=True)
class ProgramPrefixState:
    """Policy-owned causal prefix state for one turn."""

    hidden: Tensor


@dataclass(frozen=True)
class ProgramSequenceInputs:
    """Padded decision states for teacher-forced full-turn replay."""

    context: Tensor
    tile_tokens: Tensor
    root_features: Tensor
    option_features: Tensor
    target_reservations: Tensor
    phase: Tensor
    unit_index: Tensor
    market_slot: Tensor
    unit_count: Tensor
    current_x: Tensor
    current_y: Tensor
    forced: Tensor
    decision_mask: Tensor

    @property
    def batch_size(self) -> int:
        """Return the number of complete turn programs."""
        return int(self.context.shape[0])

    @property
    def decision_capacity(self) -> int:
        """Return the padded number of autoregressive decisions."""
        return int(self.phase.shape[1])

    def decision(self, index: int) -> ProgramDecisionInputs:
        """Select one aligned microdecision without copying turn context."""
        if index < 0 or index >= self.decision_capacity:
            raise IndexError("conditional-program decision index is outside its sequence")
        return ProgramDecisionInputs(
            context=self.context,
            tile_tokens=self.tile_tokens,
            root_features=self.root_features[:, index],
            option_features=self.option_features[:, index],
            target_reservations=self.target_reservations[:, index],
            phase=self.phase[:, index],
            unit_index=self.unit_index[:, index],
            market_slot=self.market_slot[:, index],
            unit_count=self.unit_count[:, index],
            current_x=self.current_x[:, index],
            current_y=self.current_y[:, index],
            forced=self.forced[:, index],
        )

    def validate(self, contract: NativeProgramContract, context_width: int) -> None:
        """Validate the padded recurrent sequence contract."""
        batch = self.batch_size
        decisions = self.decision_capacity
        if decisions < 1:
            raise ValueError("conditional-program sequence must contain a decision")
        expected = {
            "context": (batch, context_width),
            "tile_tokens": (batch, contract.tile_count, context_width),
            "root_features": (
                batch,
                decisions,
                contract.root_feature_count,
            ),
            "option_features": (
                batch,
                decisions,
                contract.option_feature_count,
            ),
            "target_reservations": (batch, decisions, contract.tile_count),
            "phase": (batch, decisions),
            "unit_index": (batch, decisions),
            "market_slot": (batch, decisions),
            "unit_count": (batch, decisions),
            "current_x": (batch, decisions),
            "current_y": (batch, decisions),
            "forced": (batch, decisions),
            "decision_mask": (batch, decisions),
        }
        for name, shape in expected.items():
            value = getattr(self, name)
            if value.shape != shape or value.device != self.context.device:
                raise ValueError(
                    f"conditional-program sequence {name} has the wrong tensor ABI"
                )
        if self.decision_mask.is_floating_point():
            raise ValueError("conditional-program sequence mask must be discrete")
        mask = self.decision_mask.bool()
        if not bool(mask[:, 0].all()) or bool(
            torch.any(mask[:, 1:] & ~mask[:, :-1])
        ):
            raise ValueError("conditional-program sequence mask must be nonempty and contiguous")
        for index in range(decisions):
            self.decision(index).validate(contract, context_width)


@dataclass(frozen=True)
class ProgramActionSequence:
    """Padded structured choices aligned with complete turn programs."""

    control: Tensor
    task: Tensor
    target: Tensor
    argument: Tensor
    direction: Tensor
    raw_operation: Tensor
    quantity_mode: Tensor
    exact_quantity: Tensor
    market_order: Tensor

    def decision(self, index: int) -> ProgramActions:
        """Select one microdecision action vector."""
        return ProgramActions(
            **{
                name: getattr(self, name)[:, index]
                for name in self.__dataclass_fields__
            }
        )

    def validate(self, batch: int, decisions: int) -> None:
        """Validate all padded action fields."""
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if value.shape != (batch, decisions) or not _discrete(value):
                raise ValueError(
                    f"conditional-program action sequence {name} has the wrong ABI"
                )


@dataclass(frozen=True)
class ProgramMaskSequence:
    """Padded compact rollout masks for full-turn PPO replay."""

    control: Tensor
    direction: Tensor
    task: Tensor
    argument: Tensor
    target: Tensor
    raw_operation: Tensor
    quantity_mode: Tensor
    market_order: Tensor
    market_item: Tensor
    quantity_max: Tensor

    def decision(self, index: int) -> ProgramConditionalMasks:
        """Select one conditional mask slice."""
        return ProgramConditionalMasks(
            **{
                name: getattr(self, name)[:, index]
                for name in self.__dataclass_fields__
            }
        )

    def validate(
        self, batch: int, decisions: int, contract: NativeProgramContract
    ) -> None:
        """Validate every compact per-decision replay surface."""
        for index in range(decisions):
            self.decision(index).validate(batch, contract)


__all__ = [
    "PROGRAM_BASE_FACTOR_COUNT",
    "NativeProgramMasks",
    "ProgramActions",
    "ProgramActionSequence",
    "ProgramConditionalMasks",
    "ProgramDecisionInputs",
    "ProgramMaskSequence",
    "ProgramPrefixState",
    "ProgramSequenceInputs",
]
