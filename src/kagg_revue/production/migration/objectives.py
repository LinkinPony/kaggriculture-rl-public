"""Pure distillation loss and an outcome-independent coefficient schedule."""

from torch import Tensor
from torch.nn import functional as F


def distillation_rows(
    student: Tensor, teacher: Tensor, fields: Tensor, temperature: float
) -> Tensor:
    """Match conditional distributions without erasing the teacher's logit margins."""
    target = F.log_softmax(teacher.detach().float() / temperature, dim=-1)
    prediction = F.log_softmax(student.float() / temperature, dim=-1)
    divergence = (target.exp() * (target - prediction)).sum(-1)
    return (divergence * fields).sum(-1) / fields.sum(-1).clamp_min(1) * temperature**2


def scheduled_scale(initial: float, elapsed: int, interval: int, decrement: float) -> float:
    """Derive the coefficient from completed schedule intervals, including on resume."""
    if not 0 <= initial <= 1 or elapsed < 0 or interval <= 0 or not 0 < decrement <= 1:
        raise ValueError("invalid coefficient schedule")
    return max(0.0, round(initial - (elapsed // interval) * decrement, 12))
