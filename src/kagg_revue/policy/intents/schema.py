"""Checkpoint-bound schemas and outputs for intent policies."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator
from torch import Tensor

from kagg_revue.policy.intents.contract import NativeIntentContract


class IntentArchitecture(BaseModel):
    """Checkpoint-bound native and neural shape of an intent policy."""

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
    candidate_field_count: int = Field(gt=0)
    candidate_feature_count: int = Field(gt=0)
    ledger_field_count: int = Field(gt=0)
    status_field_count: int = Field(gt=0)
    work_field_count: int = Field(gt=0)
    choice_count: int = Field(gt=0)
    asset_kind_count: int = Field(gt=0)
    maintenance_count: int = Field(gt=0)
    product_collection_count: int = Field(gt=0)
    fertilizer_collection_count: int = Field(gt=0)
    priority_count: int = Field(gt=0)
    work_kind_count: int = Field(gt=0)
    position_role_count: int = Field(gt=0)
    directive_operation_count: int = Field(gt=0)
    market_order_count: int = Field(gt=0)
    phase_count: int = Field(gt=0)
    status_count: int = Field(gt=0)
    block_reason_count: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_native_widths(self) -> IntentArchitecture:
        """Bind the implementation to the native field layouts it consumes."""
        if (
            self.candidate_field_count != 10
            or self.ledger_field_count != 8
            or self.status_field_count != 4
            or self.work_field_count != 9
        ):
            raise ValueError("intent model does not support this native field layout")
        return self

    @classmethod
    def from_contract(
        cls,
        contract: NativeIntentContract,
        *,
        item_count: int,
        unit_limit: int,
        maximum_market_orders: int,
        context_width: int,
        model_width: int,
        feedforward_width: int,
    ) -> IntentArchitecture:
        """Construct a policy architecture from measured native dimensions."""
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
            candidate_field_count=len(contract.candidate_fields),
            candidate_feature_count=len(contract.candidate_features),
            ledger_field_count=len(contract.ledger_fields),
            status_field_count=len(contract.status_fields),
            work_field_count=len(contract.work_fields),
            choice_count=contract.choice_count,
            asset_kind_count=contract.asset_kind_count,
            maintenance_count=contract.maintenance_count,
            product_collection_count=contract.product_collection_count,
            fertilizer_collection_count=contract.fertilizer_collection_count,
            priority_count=contract.priority_count,
            work_kind_count=contract.work_kind_count,
            position_role_count=contract.position_role_count,
            directive_operation_count=contract.directive_operation_count,
            market_order_count=contract.market_order_count,
            phase_count=contract.phase_count,
            status_count=contract.status_count,
            block_reason_count=contract.block_reason_count,
        )

    @property
    def tile_count(self) -> int:
        """Return the flattened own-farm surface."""
        return self.board_size**2


@dataclass(frozen=True)
class IntentPolicyOutput:
    """Masked successor logits and direct terminal outcome logits."""

    candidate_logits: Tensor
    outcome_logits: Tensor

    @property
    def value(self) -> Tensor:
        """Return expected W/D/L in [-1, 1]."""
        probabilities = torch.softmax(self.outcome_logits.float(), dim=-1)
        return probabilities[:, 2] - probabilities[:, 0]


@dataclass(frozen=True)
class IntentSelection:
    """One sampled or greedy canonical successor per state."""

    indices: Tensor
    log_probability: Tensor
    entropy: Tensor
    value: Tensor


__all__ = ["IntentArchitecture", "IntentPolicyOutput", "IntentSelection"]
