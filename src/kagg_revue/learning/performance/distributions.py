"""Conditional categorical distribution diagnostics for compiler experiments."""

from collections.abc import Callable
from typing import Any

import torch
from torch import Tensor


class Distributions:
    """Observe captured decoder outputs without altering sampling or probabilities."""

    def __init__(self, device: torch.device) -> None:
        """Allocate on-device reductions, avoiding per-turn host synchronization."""
        self.logits: dict[str, Tensor] = {}
        self.totals = torch.zeros(6, device=device, dtype=torch.float64)

    def watch(
        self, name: str, decode: Callable[..., tuple[Tensor, Tensor]]
    ) -> Callable[..., tuple[Tensor, Tensor]]:
        """Retain the graph's live logits buffer from its final capture invocation."""

        def operation(*args: Any, **kwargs: Any) -> tuple[Tensor, Tensor]:
            actions, logits = decode(*args, **kwargs)
            self.logits[name] = logits
            return actions, logits

        return operation

    def update(self, fields: Tensor) -> None:
        """Compare distributions with the same supplied autoregressive action prefix."""
        actual, expected = self.logits["actual"].float(), self.logits["expected"].float()
        log_p, log_q = expected.log_softmax(-1), actual.log_softmax(-1)
        p, q = log_p.exp(), log_q.exp()
        kl = (p * (log_p - log_q)).sum(-1).clamp_min(0)
        tv = (p - q).abs().sum(-1) * 0.5
        support = ((actual > -1e8) != (expected > -1e8)).any(-1)
        self.totals[:3] += torch.stack((fields.sum(), (kl * fields).sum(), (tv * fields).sum()))
        self.totals[3:5] = torch.maximum(
            self.totals[3:5], torch.stack(((kl * fields).max(), (tv * fields).max()))
        )
        self.totals[5] += (support * fields).sum()

    def reset(self) -> None:
        """Separate the full-episode and live-weight replacement measurements."""
        self.totals.zero_()

    def report(self) -> dict[str, float]:
        """Return field-weighted means and worst conditional distributions."""
        mass, kl, tv, maximum_kl, maximum_tv, changed = self.totals.tolist()
        return {
            "effective_fields": mass,
            "mean_kl": kl / max(1, mass),
            "mean_total_variation": tv / max(1, mass),
            "maximum_kl": maximum_kl,
            "maximum_total_variation": maximum_tv,
            "changed_legal_support_fields": changed,
        }
