"""Bounded exact-integer distributions for parameterized policy actions."""

from __future__ import annotations

import torch
from torch import Tensor
from torch.nn import functional


def _validate_logits(logits: Tensor) -> None:
    if logits.ndim < 1 or logits.shape[-1] < 1:
        raise ValueError("quantity logits need a nonempty integer vocabulary")


def quantity_log_probability(logits: Tensor, quantity: Tensor) -> Tensor:
    """Return the categorical log probability of an exact positive integer.

    Quantity zero is the padding/no-quantity sentinel and values above the
    model vocabulary are outside the policy language. Both receive ``-inf``;
    callers must mask no-quantity decisions and reject selected out-of-range
    targets.
    """
    _validate_logits(logits)
    if quantity.shape != logits.shape[:-1]:
        raise ValueError("quantity targets must align with quantity logits")
    if quantity.is_floating_point():
        rounded = quantity.round()
        if torch.any(quantity != rounded):
            raise ValueError("quantity targets must be integral")
        quantity = rounded
    target = quantity.long() - 1
    valid = (target >= 0) & (target < logits.shape[-1])
    safe_target = target.clamp(min=0, max=logits.shape[-1] - 1)
    selected = functional.log_softmax(logits.float(), dim=-1).gather(-1, safe_target[..., None])[
        ..., 0
    ]
    return selected.masked_fill(~valid, -torch.inf)


def quantity_mode(logits: Tensor) -> Tensor:
    """Return the exact most-probable positive integer."""
    _validate_logits(logits)
    return logits.argmax(dim=-1) + 1


def sample_quantity(
    logits: Tensor,
    generator: torch.Generator | None = None,
) -> Tensor:
    """Sample one exact positive integer from categorical logits."""
    _validate_logits(logits)
    probabilities = torch.softmax(logits.float(), dim=-1)
    selected = torch.multinomial(
        probabilities.flatten(0, -2),
        1,
        replacement=True,
        generator=generator,
    ).view(*probabilities.shape[:-1])
    return selected + 1


__all__ = ["quantity_log_probability", "quantity_mode", "sample_quantity"]
