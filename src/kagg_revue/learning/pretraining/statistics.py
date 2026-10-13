"""Detached conditional action diagnostics shared by stateless and recurrent BC."""

import torch
from torch import Tensor

DOMAINS = ("unit_target", "unit_operation", "unit_quantity", "market_operation", "market_quantity")


def domain_slices(units: int, *, compact: bool = True) -> tuple[slice, ...]:
    """Locate semantic domains in the single-turn typed actor's compact or full ABI."""
    stride = 3 if compact else 8
    unit_end = units * stride
    return (
        slice(0, unit_end, stride),
        slice(1, unit_end, stride),
        slice(2, unit_end, stride),
        slice(unit_end, None, 2),
        slice(unit_end + 1, None, 2),
    )


def field_totals(
    logits: Tensor, targets: Tensor, likelihood: Tensor, active: Tensor, units: int
) -> Tensor:
    """Sum NLL, teacher-prefix correctness and valid mass for semantic action fields."""
    correct = (logits.detach().argmax(-1) == targets).float()
    selectors = domain_slices(units)
    return torch.stack(
        [
            value
            for selected in selectors
            for value in (
                -(likelihood.detach()[:, selected] * active[:, selected]).sum(),
                (correct[:, selected] * active[:, selected]).sum(),
                active[:, selected].sum(),
            )
        ]
    )
