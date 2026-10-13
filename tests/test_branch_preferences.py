import torch

from kagg_revue.production.branching.objectives import preference_rows, preference_weights


def test_preferences_use_wdl_and_reverse_gradient_for_bad_alternatives() -> None:
    outcomes = torch.tensor([[[0, 1, -1], [0, 1, 0]], [[1, 0, 1], [1, 1, 0]]])
    signs, weights = preference_weights(outcomes)
    current = torch.zeros(2, 3, requires_grad=True)
    previous = current.detach().clone()
    loss = preference_rows(current, previous, signs, weights, 0.7).sum()
    loss.backward()
    assert current.grad is not None
    assert current.grad[0, 1] < 0
    assert current.grad[0, 2] > 0
    assert not current.grad[1].any()
    torch.testing.assert_close(current.grad.sum(-1), torch.zeros(2))
    torch.testing.assert_close(weights.sum(-1), torch.tensor([1.0, 0.0]))


def test_tied_rollouts_do_not_invent_a_training_signal() -> None:
    outcomes = torch.ones(2, 3, 4)
    signs, weights = preference_weights(outcomes)
    current = torch.randn(2, 4, requires_grad=True)
    loss = preference_rows(current, current.detach(), signs, weights, 0.5).sum()
    loss.backward()
    assert not weights.any()
    assert current.grad is not None
    assert not current.grad.any()
