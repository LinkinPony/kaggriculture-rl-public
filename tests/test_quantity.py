import torch

from kagg_revue.policy.quantity import (
    quantity_log_probability,
    quantity_mode,
    sample_quantity,
)


def test_quantity_mode_and_likelihood_use_the_same_exact_integer_logits() -> None:
    logits = torch.tensor([[-2.0, 1.0, 0.0]])

    prediction = quantity_mode(logits)
    log_probability = quantity_log_probability(logits, torch.tensor([2]))

    assert prediction.item() == 2
    assert torch.allclose(log_probability, torch.log_softmax(logits, dim=-1)[:, 1])


def test_sampled_quantity_stays_inside_the_exact_policy_vocabulary() -> None:
    torch.manual_seed(5)
    logits = torch.randn(2048, 7)
    quantities = sample_quantity(logits)

    log_probability = quantity_log_probability(logits, quantities)

    assert torch.all((quantities >= 1) & (quantities <= logits.shape[-1]))
    assert torch.isfinite(log_probability).all()
