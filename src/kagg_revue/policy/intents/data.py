"""Tensor boundary for one batch of augmented intent states."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor


@dataclass(frozen=True)
class IntentTensorState:
    """All actor-visible native fields at independent pseudo-steps."""

    candidate_fields: Tensor
    candidate_features: Tensor
    candidate_mask: Tensor
    ledger: Tensor
    status: Tensor
    work_priorities: Tensor
    work_orders: Tensor
    work_mask: Tensor
    positions: Tensor
    market_prefix: Tensor
    market_mask: Tensor
    phase: Tensor

    @property
    def batch_size(self) -> int:
        """Return the number of independent pseudo-steps."""
        return int(self.phase.shape[0])

    def validate(self) -> None:
        """Reject malformed padding before it can affect a distribution."""
        batch = self.batch_size
        if self.phase.ndim != 1:
            raise ValueError("intent phase must be a vector")
        if self.candidate_fields.ndim != 3 or self.candidate_fields.shape[0] != batch:
            raise ValueError("intent candidate fields must have shape [B,C,F]")
        if self.candidate_features.shape[:2] != self.candidate_fields.shape[:2]:
            raise ValueError("intent candidate features do not align")
        if self.candidate_mask.shape != self.candidate_fields.shape[:2]:
            raise ValueError("intent candidate mask does not align")
        if self.candidate_mask.dtype != torch.bool:
            raise ValueError("intent candidate mask must be boolean")
        if bool((self.candidate_mask.sum(dim=1) < 1).any()):
            raise ValueError("every intent state needs a legal candidate")
        if self.ledger.shape[:2] != self.status.shape[:2]:
            raise ValueError("intent ledger and status surfaces differ")
        if self.work_priorities.shape[:2] != self.ledger.shape[:2]:
            raise ValueError("intent work priorities lost their tile surface")
        if self.work_orders.shape[:2] != self.work_mask.shape:
            raise ValueError("intent work-order mask does not align")
        if self.market_prefix.shape[:2] != self.market_mask.shape:
            raise ValueError("intent market mask does not align")
        for value in (
            self.ledger,
            self.status,
            self.work_priorities,
            self.work_orders,
            self.positions,
            self.market_prefix,
        ):
            if value.shape[0] != batch:
                raise ValueError("intent state tensors use different batch sizes")


__all__ = ["IntentTensorState"]
