import numpy as np
import pytest
import torch

from kagg_revue.production.model import log_probabilities, sample_categorical
from kagg_revue.production.objectives import surrogate_rows, terminal_rewards


def test_outcome_rewards_ignore_cash_magnitude_and_reverse_with_seats() -> None:
    cash = np.array([[8.0, 9.0], [5.0, 3.0], [4.0, 4.0]])
    expected = np.array([[-1.0, 1.0], [1.0, -1.0], [0.0, 0.0]])
    for transformed in (cash, cash * 7 + 11):
        actual = terminal_rewards(transformed, cash_weight=0, cash_scale=2, win_weight=1)
        np.testing.assert_array_equal(actual, expected)
        np.testing.assert_array_equal(actual.sum(axis=1), np.zeros(len(cash)))
        swapped = terminal_rewards(transformed[:, ::-1], cash_weight=0, cash_scale=2, win_weight=1)
        np.testing.assert_array_equal(swapped, -actual)


def test_cash_shaping_remains_available_when_explicitly_weighted() -> None:
    cash = np.array([[8.0, 9.0], [5.0, 3.0]])
    actual = terminal_rewards(cash, cash_weight=1, cash_scale=2, win_weight=0.5)
    np.testing.assert_array_equal(actual, [[3.5, 5.0], [3.0, 1.0]])


@pytest.mark.parametrize("temperature", [1.0, 0.4])
def test_variable_length_score_gradient_matches_expected_return_and_ignores_baseline(
    temperature: float,
) -> None:
    # Enumerate STOP, CONTINUE/left and CONTINUE/right. The second choice exists
    # only after CONTINUE, so equal rewards must not favor either plan length.
    logits = torch.tensor([0.3, -0.4], dtype=torch.float64, requires_grad=True)
    root = torch.nn.functional.logsigmoid(torch.stack((-logits[0], logits[0])) / temperature)
    branch = torch.nn.functional.logsigmoid(torch.stack((-logits[1], logits[1])) / temperature)
    selected = torch.stack(
        (
            torch.stack((root[0], root[0] * 0)),
            torch.stack((root[1], branch[0])),
            torch.stack((root[1], branch[1])),
        )
    )
    fields = torch.tensor([[1.0, 0.0], [1.0, 1.0], [1.0, 1.0]], dtype=torch.float64)
    distribution = (selected * fields).sum(-1).exp()
    rewards = torch.tensor([0.7, -0.2, 1.3], dtype=torch.float64)
    expected = torch.autograd.grad((distribution * rewards).sum(), logits, retain_graph=True)[0]
    for baseline in (0.0, 2.0):
        gains, kl = surrogate_rows(
            selected - selected.detach(), fields, rewards - baseline, 0.2, joint=True
        )
        actual = torch.autograd.grad(
            (distribution.detach() * gains).sum(), logits, retain_graph=True
        )[0]
        torch.testing.assert_close(actual, expected)
        torch.testing.assert_close(kl, torch.zeros_like(kl))


def test_tempered_sampler_matches_its_reported_categorical_distribution() -> None:
    # Fourfold log-odds turn relative weights 1:3 into 1:81. This catches scaling
    # only the recorded likelihood while leaving the actual sampler unchanged.
    logits = torch.tensor([1.0, 3.0]).log().expand(16000, -1)
    temperature = 0.25
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(7)
        actions = sample_categorical(logits, temperature)
    expected = torch.tensor([1.0, 81.0]) / 82.0
    observed = torch.bincount(actions, minlength=2).float() / len(actions)
    torch.testing.assert_close(observed, expected, atol=0.01, rtol=0)
    torch.testing.assert_close(
        log_probabilities(logits, actions, temperature).exp(), expected[actions]
    )


def test_joint_clipping_uses_whole_plan_likelihood_and_ignores_padding() -> None:
    log_ratio = torch.tensor([[0.1, 0.1, 7.0], [-0.1, -0.1, -7.0]], requires_grad=True)
    fields = torch.tensor([[1.0, 1.0, 0.0], [1.0, 1.0, 0.0]])
    advantages = torch.tensor([1.0, -1.0])
    gain, kl = surrogate_rows(log_ratio, fields, advantages, 0.15, joint=True)
    torch.testing.assert_close(gain, torch.tensor([1.15, -0.85]))
    summed = torch.tensor([0.2, -0.2])
    torch.testing.assert_close(kl, summed.exp() - 1 - summed)
    gain.sum().backward()
    torch.testing.assert_close(log_ratio.grad, torch.zeros_like(log_ratio))


def test_frozen_field_surrogate_keeps_existing_values_and_gradients() -> None:
    log_ratio = torch.tensor([[0.03, -0.08], [-0.07, 0.05]], requires_grad=True)
    fields = torch.tensor([[1.0, 0.0], [1.0, 1.0]])
    advantages = torch.tensor([0.9, -0.3])
    actual, kl = surrogate_rows(log_ratio, fields, advantages, 0.1, joint=False)
    ratio = log_ratio.exp()
    reference = torch.minimum(
        ratio * advantages[:, None], ratio.clamp(0.9, 1.1) * advantages[:, None]
    )
    reference = (reference * fields).sum(-1) / fields.sum(-1)
    torch.testing.assert_close(actual, reference)
    torch.testing.assert_close(kl, ((ratio - 1 - log_ratio) * fields).sum(-1) / fields.sum(-1))
    torch.testing.assert_close(
        torch.autograd.grad(actual.sum(), log_ratio, retain_graph=True)[0],
        torch.autograd.grad(reference.sum(), log_ratio)[0],
    )
