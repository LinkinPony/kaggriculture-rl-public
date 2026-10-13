from dataclasses import replace

import pytest
import torch

from kagg_revue.production.prefix import (
    PrefixCritic,
    prefix_credit,
    prefix_surrogate,
    prefix_value_rows,
)
from test_production_work import _layout


def test_masked_credit_skips_inactive_fields_and_telescopes_through_stop() -> None:
    values = torch.tensor([[0.2, float("nan"), 0.5, -0.1], [-0.4, 0.9, 0.8, 0.7]])
    fields = torch.tensor([[1.0, 0.0, 1.0, 1.0], [1.0, 0.0, 0.0, 0.0]])
    returns = torch.tensor([1.0, -1.0])
    credit = prefix_credit(values, fields, returns)
    torch.testing.assert_close(credit.sum(1), returns - values[:, 0])
    torch.testing.assert_close(credit[0, [0, 2, 3]], torch.tensor([0.3, -0.6, 1.1]))
    assert not credit[~fields.bool()].any()
    assert not credit.requires_grad


@pytest.mark.parametrize("trace_lambda", [0.0, 0.37, 0.95, 1.0])
def test_prefix_trace_matches_scalar_recursion_with_padding(trace_lambda: float) -> None:
    values = torch.tensor([[0.2, float("nan"), 0.5, -0.1], [-0.4, 0.9, 0.8, 0.7]])
    fields = torch.tensor([[1.0, 0.0, 1.0, 1.0], [0.0, 1.0, 0.0, 0.0]])
    returns = torch.tensor([1.0, -1.0])
    expected = torch.zeros_like(values)
    for row in range(len(values)):
        downstream = returns[row]
        advantage = torch.tensor(0.0)
        for index in reversed(range(values.shape[1])):
            if fields[row, index]:
                advantage = downstream - values[row, index] + trace_lambda * advantage
                expected[row, index] = advantage
                downstream = values[row, index]
    torch.testing.assert_close(prefix_credit(values, fields, returns, trace_lambda), expected)


def test_monte_carlo_credit_is_unbiased_with_an_inaccurate_prefix_critic() -> None:
    # STOP earns 0.7; CONTINUE then chooses between -0.2 and 1.3. Deliberately
    # inaccurate but causal baselines must not bias the on-policy gradient.
    logits = torch.tensor([0.3, -0.4], dtype=torch.float64, requires_grad=True)
    root = torch.nn.functional.logsigmoid(torch.stack((-logits[0], logits[0])))
    branch = torch.nn.functional.logsigmoid(torch.stack((-logits[1], logits[1])))
    selected = torch.stack(
        (
            torch.stack((root[0], root[0] * 0)),
            torch.stack((root[1], branch[0])),
            torch.stack((root[1], branch[1])),
        )
    )
    fields = torch.tensor([[1.0, 0.0], [1.0, 1.0], [1.0, 1.0]], dtype=torch.float64)
    rewards = torch.tensor([0.7, -0.2, 1.3], dtype=torch.float64)
    distribution = (selected * fields).sum(1).exp()
    expected = torch.autograd.grad((distribution * rewards).sum(), logits, retain_graph=True)[0]
    prefixes = torch.tensor([[-0.4, 0.0], [-0.4, 0.9], [-0.4, 0.9]], dtype=torch.float64)
    gradients = []
    for trace_lambda in (0.0, 1.0):
        credit = prefix_credit(prefixes, fields, rewards, trace_lambda)
        gain, _ = prefix_surrogate(selected - selected.detach(), fields, credit, 0.2)
        gradients.append(
            torch.autograd.grad((distribution.detach() * gain).sum(), logits, retain_graph=True)[0]
        )
    torch.testing.assert_close(gradients[1], expected)
    assert torch.sign(gradients[0][0]) != torch.sign(expected[0])


def test_prefix_policy_gradient_matches_exact_variable_length_return() -> None:
    # Enumerate STOP and the two choices after CONTINUE. Exact prefix values
    # must give the same expected policy gradient for short and long plans.
    logits = torch.tensor([0.3, -0.4], dtype=torch.float64, requires_grad=True)
    root = torch.nn.functional.logsigmoid(torch.stack((-logits[0], logits[0])))
    branch = torch.nn.functional.logsigmoid(torch.stack((-logits[1], logits[1])))
    selected = torch.stack(
        (
            torch.stack((root[0], root[0] * 0)),
            torch.stack((root[1], branch[0])),
            torch.stack((root[1], branch[1])),
        )
    )
    fields = torch.tensor([[1.0, 0.0], [1.0, 1.0], [1.0, 1.0]], dtype=torch.float64)
    rewards = torch.tensor([0.7, -0.2, 1.3], dtype=torch.float64)
    distribution = (selected * fields).sum(1).exp()
    expected_return = (distribution * rewards).sum()
    expected = torch.autograd.grad(expected_return, logits, retain_graph=True)[0]
    continuation = (branch.exp() * rewards[1:]).sum().detach()
    prefixes = torch.stack(
        (
            expected_return.detach().expand(3),
            continuation.expand(3),
        ),
        1,
    )
    credit = prefix_credit(prefixes, fields, rewards)
    gains, kl = prefix_surrogate(selected - selected.detach(), fields, credit, 0.2)
    actual = torch.autograd.grad((distribution.detach() * gains).sum(), logits)[0]
    torch.testing.assert_close(actual, expected)
    torch.testing.assert_close(kl, torch.zeros_like(kl))


def test_prefix_values_are_exclusive_causal_and_ignore_inactive_actions() -> None:
    layout = _layout()
    layout = replace(layout, network=replace(layout.network, time_prior=False))
    critic = PrefixCritic(layout)
    # Exercise learned deltas, not just their zero initializer.
    torch.nn.init.normal_(critic.delta[-1].weight, std=0.2)
    observations = torch.randn(2, layout.observation.features)
    actions = torch.zeros((2, layout.factors), dtype=torch.long)
    fields = torch.ones_like(actions, dtype=torch.float32)
    fields[:, 2] = 0
    state, values = critic.prefixes(observations, actions, fields)
    torch.testing.assert_close(state, critic(observations))
    torch.testing.assert_close(values[:, 0], state)
    changed = actions.clone()
    changed[:, 2] = 1
    torch.testing.assert_close(critic.prefixes(observations, changed, fields)[1], values)
    for boundary in (0, layout.work_factors - 1, layout.work_factors, layout.factors - 1):
        changed = actions.clone()
        changed[:, boundary:] = 1
        changed_state, changed_values = critic.prefixes(observations, changed, fields)
        torch.testing.assert_close(changed_state, state)
        torch.testing.assert_close(changed_values[:, : boundary + 1], values[:, : boundary + 1])
        if boundary + 1 < layout.factors:
            assert not torch.allclose(changed_values[:, boundary + 1 :], values[:, boundary + 1 :])
    losses, _, _ = prefix_value_rows(state, values, torch.tensor([1.0, -1.0]), fields, 0.7)
    losses.mean().backward()
    for module in (critic.entity_encoder, critic.network, critic.symbols, critic.delta):
        assert module is not None
        assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in module.parameters())


def test_prefix_clipping_masks_padding_and_value_targets_are_terminal() -> None:
    ratios = torch.tensor([[2.0, 0.5, 1.0], [1.0, 1.0, 1.0]], requires_grad=True)
    fields = torch.tensor([[1.0, 1.0, 0.0], [1.0, 0.0, 0.0]])
    advantages = torch.tensor([[1.0, -1.0, 0.0], [2.0, 0.0, 0.0]])
    gains, _ = prefix_surrogate(ratios.log(), fields, advantages, 0.1)
    torch.testing.assert_close(gains, torch.tensor([0.2, 2.0]))
    gains.sum().backward()
    assert not ratios.grad[0].any()
    state = torch.tensor([0.2, -0.4])
    prefixes = torch.tensor([[0.2, 0.5, 99.0], [-0.4, 99.0, 99.0]])
    returns = torch.tensor([1.0, -1.0])
    total, state_loss, prefix_loss = prefix_value_rows(state, prefixes, returns, fields, 0.3)
    torch.testing.assert_close(state_loss, (state - returns).square())
    torch.testing.assert_close(prefix_loss, torch.tensor([0.125, 0.0]))
    torch.testing.assert_close(total, state_loss + 0.3 * prefix_loss)
    # Adding a correctly predicted continuation must not reweight earlier errors.
    longer_fields = fields.clone()
    longer_fields[0, -1] = 1
    longer_values = prefixes.clone()
    longer_values[0, -1] = returns[0]
    longer = prefix_value_rows(state, longer_values, returns, longer_fields, 0.3)[0]
    torch.testing.assert_close(longer, total)
