"""Tensor boundary for batches of native atomic-effect states."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import Tensor


@dataclass(frozen=True)
class EffectTensorState:
    """Actor-visible candidates, jobs, and semantic action prefixes."""

    candidate_fields: Tensor
    candidate_features: Tensor
    candidate_mask: Tensor
    jobs: Tensor
    job_mask: Tensor
    work_prefix: Tensor
    work_mask: Tensor
    market_prefix: Tensor
    market_mask: Tensor
    previous_action: Tensor
    previous_mask: Tensor
    phase: Tensor
    work_limit: Tensor

    @property
    def batch_size(self) -> int:
        """Return the independent state count."""
        return int(self.phase.shape[0])

    def validate(self) -> None:
        """Reject malformed padding before it changes a policy distribution."""
        batch = self.batch_size
        if self.phase.ndim != 1 or self.work_limit.shape != (batch,):
            raise ValueError("effect phase and work limit must be vectors")
        if self.candidate_fields.ndim != 3 or self.candidate_fields.shape[0] != batch:
            raise ValueError("effect candidate fields must have shape [B,C,F]")
        if self.candidate_features.shape[:2] != self.candidate_fields.shape[:2]:
            raise ValueError("effect candidate features do not align")
        if self.candidate_mask.shape != self.candidate_fields.shape[:2]:
            raise ValueError("effect candidate mask does not align")
        pairs = (
            (self.jobs, self.job_mask),
            (self.work_prefix, self.work_mask),
            (self.market_prefix, self.market_mask),
            (self.previous_action, self.previous_mask),
        )
        for values, mask in pairs:
            if values.ndim != 3 or values.shape[:2] != mask.shape:
                raise ValueError("effect entity fields and mask do not align")
            if values.shape[0] != batch:
                raise ValueError("effect state tensors use different batch sizes")
        for mask in (
            self.candidate_mask,
            self.job_mask,
            self.work_mask,
            self.market_mask,
            self.previous_mask,
        ):
            if mask.dtype != torch.bool:
                raise ValueError("effect masks must be boolean")
        if bool((self.candidate_mask.sum(dim=1) < 1).any()):
            raise ValueError("every effect state needs a legal candidate")


def tensor_state_from_native(
    payload: Mapping[str, Any],
    device: torch.device | str,
) -> EffectTensorState:
    """Upload a padded native batch and derive prefix masks from counts."""
    target = torch.device(device)

    def integer(name: str) -> Tensor:
        return torch.as_tensor(np.asarray(payload[name]), device=target)

    def mask_for(values: Tensor, counts: Tensor) -> Tensor:
        return torch.arange(values.shape[1], device=target)[None] < counts[:, None]

    jobs = integer("jobs")
    work = integer("work_prefix")
    market = integer("market_prefix")
    previous = integer("previous_action")
    state = EffectTensorState(
        candidate_fields=integer("candidate_fields"),
        candidate_features=torch.as_tensor(
            np.asarray(payload["candidate_features"]), device=target
        ),
        candidate_mask=torch.as_tensor(
            np.asarray(payload["candidate_mask"]), device=target, dtype=torch.bool
        ),
        jobs=jobs,
        job_mask=mask_for(jobs, integer("job_counts")),
        work_prefix=work,
        work_mask=mask_for(work, integer("work_counts")),
        market_prefix=market,
        market_mask=mask_for(market, integer("market_counts")),
        previous_action=previous,
        previous_mask=mask_for(previous, integer("previous_counts")),
        phase=integer("phase"),
        work_limit=integer("work_limit"),
    )
    state.validate()
    return state


__all__ = ["EffectTensorState", "tensor_state_from_native"]
