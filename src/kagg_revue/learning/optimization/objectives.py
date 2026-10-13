"""Terminal rewards and PPO surrogates for conditional plans."""

import numpy as np
import numpy.typing as npt
import torch
from torch import Tensor

from kagg_revue.learning.optimization.settings import CashMargin


def terminal_rewards(
    cash: npt.NDArray[np.float64],
    *,
    cash_weight: float,
    cash_scale: float,
    win_weight: float,
    cash_margin: CashMargin | None = None,
) -> npt.NDArray[np.float64]:
    """Return terminal WDL with only the explicitly configured cash reward terms."""
    difference = cash - cash[:, ::-1]
    rewards = win_weight * np.sign(difference)
    if cash_weight:
        rewards = rewards + cash_weight * (cash / cash_scale)
    if cash_margin is not None:
        rewards = rewards + cash_margin.beta * difference / (
            np.abs(difference) + cash_margin.cash_scale
        )
    return rewards


def surrogate_rows(
    log_ratio: Tensor, fields: Tensor, advantages: Tensor, clip: float, *, joint: bool
) -> tuple[Tensor, Tensor]:
    """Return per-plan clipped gains and behavior-to-current KL estimates.

    Joint mode sums conditional log probabilities before constructing the ratio.
    STOP and other causal masks affect the likelihood, never its normalization.
    Dividing by a sampled plan length would introduce a policy-dependent reward
    weight and make even an action-independent baseline produce a policy gradient.
    Field mode retains the frozen historical surrogate for controlled comparisons.
    """
    if joint:
        log_ratio = (log_ratio * fields).sum(-1, keepdim=True)
        fields = torch.ones_like(log_ratio)
    ratio = log_ratio.exp()
    gain = torch.minimum(
        ratio * advantages[:, None],
        ratio.clamp(1 - clip, 1 + clip) * advantages[:, None],
    )
    mass = fields.sum(-1).clamp_min(1)
    return (
        (gain * fields).sum(-1) / mass,
        ((ratio - 1 - log_ratio) * fields).sum(-1) / mass,
    )
