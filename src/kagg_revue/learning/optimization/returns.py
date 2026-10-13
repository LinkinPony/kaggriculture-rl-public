"""Turn-based GAE on complete games, independent of within-turn action fields."""

import torch
from torch import Tensor
from torch.nn import functional as F


@torch.no_grad()
def generalized_returns(
    values: Tensor,
    terminal_returns: Tensor,
    steps: Tensor,
    turns: int,
    gamma: float,
    gae_lambda: float,
) -> Tensor:
    """Return V + GAE for time-major tapes with terminal WDL and no intermediate rewards.

    Each column is one learned seat in one complete game. The terminal successor
    has zero value. Gamma and lambda advance once per game turn; action fields
    inside the same turn do not consume additional time or discount.
    """
    if not 0 < gamma <= 1 or not 0 <= gae_lambda <= 1 or turns < 1:
        raise ValueError("invalid GAE discount, trace or complete-game length")
    if values.ndim != 1 or values.shape != terminal_returns.shape or values.shape != steps.shape:
        raise ValueError("GAE requires equally sized flat values, outcomes and clocks")
    if not len(values) or len(values) % turns:
        raise ValueError("GAE requires complete equal-length trajectories")
    count = len(values) // turns
    expected = torch.arange(turns, device=steps.device)[:, None].expand(turns, count)
    if not torch.equal(steps.reshape(turns, count), expected):
        raise ValueError("GAE requires time-major complete-game clocks")
    if gamma == 1 and gae_lambda == 1:
        return terminal_returns.detach()
    baseline = values.reshape(turns, count)
    rewards = terminal_returns.reshape(turns, count)[-1:]
    credit = torch.cat((gamma * baseline[1:] - baseline[:-1], rewards - baseline[-1:]), dim=0)
    # Compose the reverse affine scan in log2(turns) GPU operations.
    stride, discount = 1, gamma * gae_lambda
    while stride < turns:
        credit = credit + discount * F.pad(credit[stride:], (0, 0, 0, stride))
        discount *= discount
        stride *= 2
    return (baseline + credit).flatten()
