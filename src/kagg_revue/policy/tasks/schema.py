"""Artifact architecture and policy outputs for unit-task tapes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from torch import Tensor

from kagg_revue.policy.tasks.grammar import (
    FACTORIZED_TASK_FACTOR_COUNT,
    TASK_FACTOR_COUNT,
    FactorizedTaskMasks,
    TaskActions,
    TaskConditionalMasks,
)


class TaskTapeArchitecture(BaseModel):
    """Validated checkpoint-bound shape of the task-level actor-critic."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    architecture_version: Literal[
        "attention-v1", "pooled-v2", "factorized-v3"
    ] = "attention-v1"
    context_width: int = Field(gt=0)
    model_width: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    attention_heads: int = Field(gt=0)
    prefix_layers: int = Field(gt=0)
    candidate_count: int = Field(gt=1)
    candidate_features: int = Field(gt=0)
    root_features: int = Field(gt=0)
    prefix_capacity: int = Field(gt=0)
    history_window: int = Field(default=64, gt=0)
    task_fields: int = Field(gt=0)
    operation_tokens: int = Field(gt=0)
    item_tokens: int = Field(gt=0)
    status_tokens: int = Field(gt=0)
    time_tokens: int = Field(gt=1)
    maximum_quantity: int = Field(gt=0)
    unit_limit: int = Field(gt=0)
    board_size: int = Field(gt=1)
    native_abi_version: str = Field(min_length=1)
    catalog_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_contract(self) -> TaskTapeArchitecture:
        """Reject shapes that cannot express the native task ABI."""
        if self.model_width % self.attention_heads:
            raise ValueError("unit-task model width must divide into attention heads")
        if self.task_fields != 9:
            raise ValueError("unit-task task-field width differs from ABI v1")
        if self.operation_tokens != 16 or self.item_tokens != 12:
            raise ValueError("unit-task operation or item vocabulary differs from ABI v1")
        if self.status_tokens != 9:
            raise ValueError("unit-task feedback vocabulary differs from ABI v1")
        if self.prefix_capacity < self.unit_limit * (self.time_tokens - 1):
            raise ValueError("unit-task prefix capacity is below one complete day")
        if (
            self.architecture_version == "factorized-v3"
            and self.history_window > self.prefix_capacity
        ):
            raise ValueError("factorized task history window exceeds native capacity")
        return self


@dataclass(frozen=True)
class TaskPolicyOutput:
    """One task-level policy factor with terminal W/D/L value."""

    actions: TaskActions
    masks: TaskConditionalMasks | FactorizedTaskMasks
    joint_log_probability: Tensor
    factor_log_probability: Tensor
    entropy: Tensor
    factor_entropy: Tensor
    outcome_logits: Tensor
    value: Tensor

    @property
    def factor_counts(self) -> Tensor:
        """Return the number of stochastic conditional factors per row."""
        expected = (
            FACTORIZED_TASK_FACTOR_COUNT
            if isinstance(self.masks, FactorizedTaskMasks)
            else TASK_FACTOR_COUNT
        )
        if self.masks.factors.shape[-1] != expected:
            raise ValueError("unit-task factor mask width differs from the ABI")
        return self.masks.factors.sum(dim=-1)


__all__ = ["TaskPolicyOutput", "TaskTapeArchitecture"]
