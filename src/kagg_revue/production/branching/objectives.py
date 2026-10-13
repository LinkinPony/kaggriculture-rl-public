"""Terminal-WDL preferences over complete conditional programs; no cash or teacher logits."""

from torch import Tensor
from torch.nn import functional as F


def preference_weights(outcomes: Tensor) -> tuple[Tensor, Tensor]:
    """Give useful roots equal mass, retaining both successful and failed alternatives."""
    # [root, continuation, candidate], each entry is a direct -1/0/+1 terminal outcome.
    difference = (outcomes.float() - outcomes[..., :1].float()).mean(1)
    useful = difference.max(-1).values > 0
    mass = difference.abs() * useful[:, None]
    mass /= mass.sum(-1, keepdim=True).clamp_min(1e-12)
    return difference.sign(), mass


def preference_rows(
    current: Tensor, previous: Tensor, signs: Tensor, weights: Tensor, beta: float
) -> Tensor:
    """Compare changes in joint program log probability against the same root control."""
    ratios = current - previous
    relative = ratios - ratios[:, :1]
    return (F.softplus(-beta * signs * relative) * weights).sum(-1)
