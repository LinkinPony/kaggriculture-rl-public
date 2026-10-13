"""Artifact-defining portfolio model and output schemas."""

from __future__ import annotations

from dataclasses import dataclass

from torch import Tensor

from kagg_revue.policy.plans.grammar import (
    GLOBAL_FIELDS,
    LINE_FIELDS,
    PRODUCTION_LINES,
    PlanActions,
    PlanConditionalMasks,
    factor_width,
)
from kagg_revue.policy.plans.observation import (
    BOARD_SHAPE,
    ECONOMIC_STATE_FEATURES,
    GLOBAL_FEATURES,
    UNIT_SHAPE,
)


@dataclass(frozen=True)
class StructuredPlanArchitecture:
    """Artifact-defining dimensions for the portfolio actor-critic."""

    observation_features: int
    journal_features: int
    event_features: int
    production_lines: int
    line_fields: int
    global_fields: int
    model_width: int
    feedforward_width: int
    board_shape: tuple[int, int, int, int] = BOARD_SHAPE
    unit_shape: tuple[int, int, int] = UNIT_SHAPE
    rich_global_features: int = GLOBAL_FEATURES
    economic_state_features: int = ECONOMIC_STATE_FEATURES
    entity_width: int = 32
    attention_heads: int = 4
    latent_tokens: int = 8
    register_tokens: int = 0
    scene_layers: int = 1
    temporal_layers: int = 2
    action_layers: int = 1
    max_history: int = 64
    strategy_tokens: int = 0
    fact_dropout: float = 0.0

    def __post_init__(self) -> None:
        """Reject dimensions that cannot form the versioned model."""
        positive = (
            "observation_features",
            "journal_features",
            "event_features",
            "production_lines",
            "line_fields",
            "global_fields",
            "model_width",
            "feedforward_width",
            "rich_global_features",
            "economic_state_features",
            "entity_width",
            "attention_heads",
            "latent_tokens",
            "temporal_layers",
            "action_layers",
            "max_history",
        )
        for name in positive:
            if getattr(self, name) < 1:
                raise ValueError(f"structured-plan {name} must be positive")
        expected = {
            "production_lines": PRODUCTION_LINES,
            "line_fields": LINE_FIELDS,
            "global_fields": GLOBAL_FIELDS,
        }
        for name, value in expected.items():
            if getattr(self, name) != value:
                raise ValueError(f"structured-plan {name} must match ABI v3")
        if self.board_shape != BOARD_SHAPE or self.unit_shape != UNIT_SHAPE:
            raise ValueError("structured-plan rich entity tensors must match policy ABI")
        if self.rich_global_features != GLOBAL_FEATURES:
            raise ValueError("structured-plan rich globals must match policy ABI")
        if self.economic_state_features != ECONOMIC_STATE_FEATURES:
            raise ValueError("structured-plan economic state must match policy ABI")
        if self.model_width % self.attention_heads:
            raise ValueError("structured-plan model width must divide into attention heads")
        if (self.model_width // self.attention_heads) % 2:
            raise ValueError("structured-plan attention head width must be even")
        if self.register_tokens < 0 or self.scene_layers < 0 or self.strategy_tokens < 0:
            raise ValueError("structured-plan optional token/layer counts cannot be negative")
        if not 0.0 <= self.fact_dropout < 1.0:
            raise ValueError("structured-plan fact dropout must lie in [0, 1)")

    @property
    def factor_width(self) -> int:
        """Return the fixed conditional action-factor width."""
        return factor_width(
            self.production_lines,
            self.line_fields,
            self.global_fields,
        )

    def payload(self) -> dict[str, object]:
        """Return the stable architecture payload stored in checkpoints."""
        return dict(self.__dict__)


@dataclass(frozen=True)
class StructuredPlanBehaviorOutput:
    """Only the policy fields persisted by on-policy rollout collection."""

    actions: PlanActions
    masks: PlanConditionalMasks
    joint_log_probability: Tensor
    value: Tensor


@dataclass(frozen=True)
class StructuredPlanPolicyOutput:
    """One complete action with joint likelihood and group-balanced entropy."""

    actions: PlanActions
    masks: PlanConditionalMasks
    joint_log_probability: Tensor
    factor_log_probability: Tensor
    entropy: Tensor
    value_logits: Tensor
    value: Tensor

    @property
    def factor_counts(self) -> Tensor:
        """Return the exact number of active conditional factors."""
        return self.masks.factors.sum(dim=1)


__all__ = [
    "StructuredPlanArchitecture",
    "StructuredPlanBehaviorOutput",
    "StructuredPlanPolicyOutput",
]
