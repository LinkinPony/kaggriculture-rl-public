"""Typed compiler outputs and policy-visible decision traces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator
from torch import Tensor

from kagg_revue.policy.programs.contract import MarketDecision, UnitDecision

if TYPE_CHECKING:
    from kagg_revue.policy.programs.grammar import (
        ProgramActions,
        ProgramConditionalMasks,
        ProgramPrefixState,
    )
    from kagg_revue.policy.programs.legality import MarketMasks, UnitMasks


class ProgramArchitecture(BaseModel):
    """Checkpoint-bound conditional-program tensor and model dimensions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    architecture_version: Literal["conditional-program-v1", "conditional-program-v2"]
    context_width: int = Field(gt=0)
    model_width: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    board_size: int = Field(gt=1)
    unit_limit: int = Field(gt=0)
    maximum_market_orders: int = Field(gt=0)
    control_count: int = Field(gt=0)
    direction_count: int = Field(gt=0)
    task_count: int = Field(gt=0)
    raw_operation_count: int = Field(gt=0)
    market_order_count: int = Field(gt=0)
    quantity_mode_count: int = Field(gt=0)
    argument_count: int = Field(gt=0)
    item_count: int = Field(gt=0)
    root_feature_count: int = Field(gt=0)
    option_feature_count: int = Field(gt=0)
    exact_quantity_bits: int = Field(gt=0, le=62)
    native_abi_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_action_language(self) -> ProgramArchitecture:
        """Reject dimensions that cannot encode every compiler branch."""
        if self.argument_count < self.item_count + 3:
            raise ValueError("conditional-program argument vocabulary is incomplete")
        return self

    @property
    def tile_count(self) -> int:
        """Return the full pointer width."""
        return self.board_size * self.board_size

    @property
    def factor_count(self) -> int:
        """Return fixed diagnostic slots including every exact bit."""
        from kagg_revue.policy.programs.grammar import PROGRAM_BASE_FACTOR_COUNT

        return PROGRAM_BASE_FACTOR_COUNT + self.exact_quantity_bits


@dataclass(frozen=True)
class ProgramStepOutput:
    """One sampled or teacher-forced conditional program decision."""

    actions: ProgramActions
    masks: ProgramConditionalMasks
    joint_log_probability: Tensor
    factor_log_probability: Tensor
    entropy: Tensor
    factor_entropy: Tensor
    factors: Tensor
    outcome_logits: Tensor
    value: Tensor
    next_prefix: ProgramPrefixState

    @property
    def factor_counts(self) -> Tensor:
        """Count stochastic factors for entropy normalization."""
        return self.factors.sum(dim=-1)


@dataclass(frozen=True)
class ProgramSequenceOutput:
    """Full joint turn likelihood reconstructed from microdecisions."""

    joint_log_probability: Tensor
    normalized_entropy: Tensor
    factor_log_probability: Tensor
    factor_entropy: Tensor
    factors: Tensor
    outcome_logits: Tensor
    value: Tensor

    @property
    def factor_counts(self) -> Tensor:
        """Count active stochastic tokens across the complete turn."""
        return self.factors.sum(dim=(-1, -2))


@dataclass(frozen=True, slots=True)
class ProgramDecisionTrace:
    """Exact masks and selection for one conditional factor tree."""

    unit_decisions: tuple[UnitDecision, ...]
    unit_masks: tuple[UnitMasks, ...]
    market_decisions: tuple[MarketDecision, ...]
    market_masks: tuple[MarketMasks, ...]


@dataclass(frozen=True, slots=True)
class CompiledProgram:
    """One complete official action in numeric and dictionary form."""

    tokens: NDArray[np.int64]
    quantities: NDArray[np.int64]
    decision_count: int
    unit_count: int
    action: dict[str, object]
    trace: ProgramDecisionTrace

    def validate(self, maximum_decisions: int) -> None:
        """Reject malformed or incomplete compiler output."""
        if self.tokens.shape != (maximum_decisions,):
            raise ValueError("program token buffer has the wrong shape")
        if self.quantities.shape != self.tokens.shape:
            raise ValueError("program quantity buffer has the wrong shape")
        if not self.unit_count <= self.decision_count <= maximum_decisions:
            raise ValueError("program decision count is outside its buffer")
        if len(self.trace.unit_decisions) != self.unit_count:
            raise ValueError("program trace lacks a decision for every unit")


__all__ = [
    "CompiledProgram",
    "ProgramArchitecture",
    "ProgramDecisionTrace",
    "ProgramSequenceOutput",
    "ProgramStepOutput",
]
