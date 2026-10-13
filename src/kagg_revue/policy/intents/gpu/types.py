"""Graph-static values shared by CUDA intent transaction modules."""

from __future__ import annotations

from dataclasses import dataclass

from torch import Tensor

from kagg_revue.policy.intents.data import IntentTensorState


@dataclass(frozen=True)
class IntentGpuDecision:
    """One graph-static policy state plus its live candidate counts."""

    state: IntentTensorState
    candidate_counts: Tensor


__all__ = ["IntentGpuDecision"]
