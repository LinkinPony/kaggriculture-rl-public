"""Terminal rewards derived from official end-of-season cash."""

from __future__ import annotations

import math

import torch
from torch import Tensor


def margin_augmented_return(
    outcome: int,
    cash_difference: float,
    *,
    beta: float,
    cash_scale: float,
) -> float:
    """Return bounded cash-margin ordering within the official W/D/L classes."""
    if outcome not in {-1, 0, 1}:
        raise ValueError("terminal outcome must be loss, tie or win")
    if not math.isfinite(cash_difference):
        raise ValueError("terminal cash difference must be finite")
    if not math.isfinite(beta) or beta <= 0.0:
        raise ValueError("margin reward beta must be finite and positive")
    if not math.isfinite(cash_scale) or cash_scale <= 0.0:
        raise ValueError("margin reward cash scale must be finite and positive")
    derived_outcome = int(cash_difference > 0.0) - int(cash_difference < 0.0)
    if derived_outcome != outcome:
        raise ValueError("terminal outcome differs from the cash-difference sign")
    return float(outcome) + beta * cash_difference / (abs(cash_difference) + cash_scale)


def margin_augmented_returns(
    outcomes: Tensor,
    cash_differences: Tensor,
    *,
    beta: float,
    cash_scale: float,
    validate: bool = True,
) -> Tensor:
    """Vectorize :func:`margin_augmented_return` without leaving the device."""
    if outcomes.shape != cash_differences.shape:
        raise ValueError("terminal outcomes and cash differences must align")
    if not math.isfinite(beta) or beta <= 0.0:
        raise ValueError("margin reward beta must be finite and positive")
    if not math.isfinite(cash_scale) or cash_scale <= 0.0:
        raise ValueError("margin reward cash scale must be finite and positive")
    margins = cash_differences.float()
    if validate:
        if outcomes.is_floating_point() and bool(torch.any(outcomes != outcomes.round()).item()):
            raise ValueError("terminal outcomes must be integral")
        if bool(torch.any((outcomes < -1) | (outcomes > 1)).item()):
            raise ValueError("terminal outcomes must be loss, tie or win")
        if not bool(torch.isfinite(margins).all().item()):
            raise ValueError("terminal cash differences must be finite")
        derived_outcomes = torch.sign(margins).to(dtype=outcomes.dtype)
        if bool(torch.any(derived_outcomes != outcomes).item()):
            raise ValueError("terminal outcomes differ from the cash-difference signs")
    return outcomes.float() + beta * margins / (margins.abs() + cash_scale)


__all__ = ["margin_augmented_return", "margin_augmented_returns"]
