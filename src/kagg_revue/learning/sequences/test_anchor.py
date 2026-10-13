"""Check the reference-policy KL anchor used by recurrent PPO."""

import torch

from kagg_revue.learning.optimization.settings import OptimizationSettings
from kagg_revue.learning.sequences.objectives import SequenceObjectives


def _objectives() -> SequenceObjectives:
    settings = OptimizationSettings.model_construct(clip=0.1, entropy_weight=0.0)
    return SequenceObjectives(settings, compile=False, device=torch.device("cpu"))


def test_anchor_is_zero_at_reference_and_positive_elsewhere() -> None:
    """Masked actions and inactive fields must not produce NaN or spurious divergence."""
    torch.manual_seed(0)
    logits = torch.randn(6, 5, 7)
    logits[..., -1] = -1e9
    fields = torch.tensor([[1.0, 1.0, 0.0, 1.0, 1.0]] * 6)
    weights, mass = torch.ones(6), torch.tensor(6.0)
    objectives = _objectives()
    same = objectives.anchor(logits, logits.clone(), fields, weights, mass, 1.0)
    moved = objectives.anchor(logits, logits + torch.randn(6, 5, 7), fields, weights, mass, 1.0)
    assert abs(float(same)) < 1e-6
    assert float(moved) > 0


def test_anchor_gradient_reaches_only_the_policy_logits() -> None:
    """The frozen reference contributes no gradient; the policy receives a finite one."""
    logits = torch.randn(4, 3, 5, requires_grad=True)
    reference = torch.randn(4, 3, 5)
    fields = torch.ones(4, 3)
    loss = _objectives().anchor(logits, reference, fields, torch.ones(4), torch.tensor(4.0), 1.0)
    loss.backward()  # type: ignore[no-untyped-call]
    assert logits.grad is not None and bool(torch.isfinite(logits.grad).all())
    assert float(logits.grad.abs().sum()) > 0
