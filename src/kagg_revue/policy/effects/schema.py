"""Checkpoint-bound schemas and policy outputs for atomic effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator
from torch import Tensor

from kagg_revue.policy.effects.contract import NativeEffectContract


class EffectArchitecture(BaseModel):
    """Native ABI and neural shape frozen into an effect checkpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    native_abi_version: str
    native_spec_version: int = Field(gt=0)
    board_size: int = Field(gt=0)
    item_count: int = Field(gt=0)
    unit_limit: int = Field(gt=0)
    maximum_market_orders: int = Field(gt=0)
    context_width: int = Field(gt=0)
    model_width: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    attention_heads: int = Field(gt=0)
    state_layers: int = Field(gt=0)
    candidate_field_count: int = Field(gt=0)
    candidate_feature_count: int = Field(gt=0)
    job_field_count: int = Field(gt=0)
    action_field_count: int = Field(gt=0)
    request_count: int = Field(gt=0)
    resource_count: int = Field(gt=0)
    phase_count: int = Field(gt=0)
    critic_representation: str = "flattened_recurrent_v1"
    independent_critic: bool = False
    task_conditioning: bool = False
    destination_tasks: bool | None = None
    prefix_encoding: Literal["field_sum_v1", "joint_action_v2"] = "field_sum_v1"
    state_position_encoding: Literal[
        "packed_relative_v1",
        "canonical_group_v2",
    ] = "packed_relative_v1"

    @model_validator(mode="after")
    def validate_shape(self) -> EffectArchitecture:
        """Bind supported field layouts and attention dimensions."""
        if (
            self.candidate_field_count != 11
            or self.job_field_count != 8
            or self.action_field_count != 6
        ):
            raise ValueError("effect model does not support this native field layout")
        if self.model_width % self.attention_heads:
            raise ValueError("effect model width must divide by its attention heads")
        if (self.model_width // self.attention_heads) % 2:
            raise ValueError("effect attention head width must be even")
        return self

    @classmethod
    def from_contract(
        cls,
        contract: NativeEffectContract,
        *,
        item_count: int,
        unit_limit: int,
        maximum_market_orders: int,
        context_width: int,
        model_width: int,
        feedforward_width: int,
        attention_heads: int,
        state_layers: int,
    ) -> EffectArchitecture:
        """Construct a checkpoint schema from the measured native contract."""
        return cls(
            native_abi_version=contract.version,
            native_spec_version=contract.spec_version,
            board_size=contract.board_size,
            item_count=item_count,
            unit_limit=unit_limit,
            maximum_market_orders=maximum_market_orders,
            context_width=context_width,
            model_width=model_width,
            feedforward_width=feedforward_width,
            attention_heads=attention_heads,
            state_layers=state_layers,
            candidate_field_count=len(contract.candidate_fields),
            candidate_feature_count=len(contract.candidate_features),
            job_field_count=len(contract.job_fields),
            action_field_count=len(contract.action_fields),
            request_count=contract.request_count,
            resource_count=contract.resource_count,
            phase_count=contract.phase_count,
            state_position_encoding="canonical_group_v2",
            critic_representation="entity_recurrent_v2",
            prefix_encoding="joint_action_v2",
        )

    @property
    def destination_tasks_enabled(self) -> bool:
        """Preserve the initial conditional checkpoint's recorded action support."""
        return self.task_conditioning if self.destination_tasks is None else self.destination_tasks

    @property
    def tile_count(self) -> int:
        """Return the own-farm tile count."""
        return self.board_size**2

    @property
    def maximum_state_entities(self) -> int:
        """Bound root, jobs, current prefixes, and previous semantic action."""
        return 1 + 3 * self.unit_limit + 2 * self.maximum_market_orders


@dataclass(frozen=True)
class EffectPolicyOutput:
    """Masked pointer scores and a direct terminal W/D/L prediction."""

    candidate_logits: Tensor
    outcome_logits: Tensor

    @property
    def value(self) -> Tensor:
        """Return the expected W/D/L value in [-1, 1]."""
        probabilities = torch.softmax(self.outcome_logits.float(), dim=-1)
        return probabilities[:, 2] - probabilities[:, 0]


@dataclass(frozen=True)
class EffectSequenceContext:
    """Turn-level actor features shared by all flattened effect factors."""

    context: Tensor
    tile_context: Tensor
    strategy: Tensor | None
    outcome_logits: Tensor | None = None


@dataclass(frozen=True)
class EffectSelection:
    """One sampled complete effect or market-order tuple."""

    indices: Tensor
    log_probability: Tensor
    candidate_log_probabilities: Tensor
    entropy: Tensor
    value: Tensor


__all__ = [
    "EffectArchitecture",
    "EffectPolicyOutput",
    "EffectSelection",
    "EffectSequenceContext",
]
