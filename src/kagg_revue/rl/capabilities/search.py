"""High-throughput value-guided search over compiled capability bundles."""

from __future__ import annotations

import copy
from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.capability import CapabilityCandidates, CapabilitySelector


@dataclass(frozen=True)
class CandidateSearchResult:
    """Frozen evidence added to the exact rollout behavior distribution."""

    logits: Tensor
    target_values: Tensor
    replay_prior: Tensor


class FrozenTargetSearch:
    """Exhaustively rank every native candidate with a lagged W/D/L model.

    The native compiler has already searched the structured bundle language by
    constructing its bounded candidate panel.  This class evaluates the whole
    panel in one GPU operation.  It deliberately does not clone environments:
    the search budget is independent of primitive option duration and remains
    small relative to complete-match rollout.
    """

    def __init__(
        self,
        selector: CapabilitySelector,
        *,
        candidate_value_scale: float,
        replay_prior_logit: float,
        direct_mode: int = 0,
    ) -> None:
        """Freeze an independent target and the non-causal replay prior."""
        if candidate_value_scale < 0.0:
            raise ValueError("candidate value scale must be non-negative")
        if replay_prior_logit < 0.0:
            raise ValueError("replay prior logit must be non-negative")
        if direct_mode < 0:
            raise ValueError("direct capability mode must be non-negative")
        self._target = copy.deepcopy(selector).eval().requires_grad_(False)
        self._candidate_value_scale = candidate_value_scale
        self._replay_prior_logit = replay_prior_logit
        self._direct_mode = direct_mode

    @property
    def target(self) -> CapabilitySelector:
        """Expose the frozen module for checkpoint serialization only."""
        return self._target

    @torch.inference_mode()
    def score(
        self,
        state: Tensor,
        candidates: CapabilityCandidates,
    ) -> CandidateSearchResult:
        """Return exact frozen search evidence for one candidate panel."""
        replay_prior = (candidates.mode == self._direct_mode).to(torch.float32)
        replay_prior = replay_prior * self._replay_prior_logit
        if self._candidate_value_scale == 0.0:
            target_values = torch.zeros_like(replay_prior)
            candidate_mask = candidates.mask.bool()
        else:
            zeros = torch.zeros_like(candidates.mode, dtype=torch.float32)
            output = self._target(state, candidates, zeros)
            target_values = output.candidate_values
            candidate_mask = output.candidate_mask
        logits = target_values * self._candidate_value_scale + replay_prior
        logits = logits.masked_fill(~candidate_mask, 0.0)
        return CandidateSearchResult(
            logits=logits,
            target_values=target_values,
            replay_prior=replay_prior,
        )

    @torch.no_grad()
    def synchronize(self, selector: CapabilitySelector) -> None:
        """Atomically replace target parameters between rollout batches."""
        self._target.load_state_dict(selector.state_dict(), strict=True)
        self._target.eval().requires_grad_(False)


__all__ = ["CandidateSearchResult", "FrozenTargetSearch"]
