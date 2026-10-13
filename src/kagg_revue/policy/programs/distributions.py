"""Masked categorical statistics shared by program rollout and replay."""

from __future__ import annotations

import torch
from torch import Tensor


def canonical_mask(batch: int, width: int, device: torch.device) -> Tensor:
    """Return a nonempty deterministic mask for an inactive branch."""
    result = torch.zeros((batch, width), dtype=torch.bool, device=device)
    result[:, 0] = True
    return result


def choose_masked(
    logits: Tensor,
    mask: Tensor,
    branch_active: Tensor,
    *,
    sample: bool,
    generator: torch.Generator | None,
    compute_entropy: bool,
) -> tuple[Tensor, Tensor, Tensor, Tensor]:
    """Sample one exact categorical and mark only stochastic branches."""
    legal = mask.bool()
    masked = logits.float().masked_fill(~legal, -torch.inf)
    log_probabilities = torch.log_softmax(masked, dim=1)
    if sample:
        selected = torch.multinomial(
            log_probabilities.exp(), 1, generator=generator
        ).squeeze(1)
    else:
        selected = masked.argmax(dim=1)
    selected_log = log_probabilities.gather(1, selected[:, None]).squeeze(1)
    factors = branch_active.bool() & (legal.sum(dim=1) > 1)
    zeros = torch.zeros_like(selected_log)
    if compute_entropy:
        probabilities = log_probabilities.exp()
        entropy = -(
            probabilities * log_probabilities.masked_fill(~legal, 0.0)
        ).sum(dim=1)
    else:
        entropy = zeros
    return (
        selected,
        torch.where(factors, selected_log, zeros),
        torch.where(factors, entropy, zeros),
        factors,
    )


def evaluate_masked(
    logits: Tensor,
    mask: Tensor,
    selected: Tensor,
    branch_active: Tensor,
    *,
    validate: bool,
) -> tuple[Tensor, Tensor, Tensor]:
    """Teacher-force one exact categorical under its stored rollout mask."""
    legal = mask.bool()
    safe = selected.clamp(0, logits.shape[1] - 1)
    if validate:
        if not bool(legal.any(dim=1).all()):
            raise ValueError("conditional-program factor has an empty legal set")
        chosen = legal.gather(1, safe[:, None]).squeeze(1)
        if bool(torch.any(branch_active & ~chosen)):
            raise ValueError(
                "conditional-program selected token is absent from its exact mask"
            )
    masked = logits.float().masked_fill(~legal, -torch.inf)
    log_probabilities = torch.log_softmax(masked, dim=1)
    probabilities = log_probabilities.exp()
    selected_log = log_probabilities.gather(1, safe[:, None]).squeeze(1)
    entropy = -(
        probabilities * log_probabilities.masked_fill(~legal, 0.0)
    ).sum(dim=1)
    factors = branch_active.bool() & (legal.sum(dim=1) > 1)
    zeros = torch.zeros_like(selected_log)
    return (
        torch.where(factors, selected_log, zeros),
        torch.where(factors, entropy, zeros),
        factors,
    )


__all__ = ["canonical_mask", "choose_masked", "evaluate_masked"]
