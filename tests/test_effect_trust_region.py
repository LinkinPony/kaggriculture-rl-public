import copy

import pytest
import torch
from torch import nn
from torch.optim import AdamW

from kagg_revue.rl.effects.objective import factor_score_mean
from kagg_revue.rl.effects.trust_region import OptimizerTransaction, guarded_optimizer_step


def test_variable_length_scores_preserve_expected_outcome_gradient() -> None:
    stop_logit = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    stop_probability = stop_logit.sigmoid()
    win_probability = 0.55
    expected = (1 - stop_probability) * (2 * win_probability - 1)
    exact_gradient = torch.autograd.grad(expected, stop_logit, retain_graph=True)[0]
    baseline = expected.detach()
    surrogate = stop_logit * 0
    for mass, reward, length, stop in (
        (0.5, 0, 1, True),
        (0.5 * win_probability, 1, 3, False),
        (0.5 * (1 - win_probability), -1, 2, False),
    ):
        score = torch.nn.functional.logsigmoid(stop_logit if stop else -stop_logit)
        values = torch.cat(((score * (reward - baseline))[None], stop_logit.new_zeros(length - 1)))
        surrogate = surrogate + mass * factor_score_mean(
            values, torch.ones(length, dtype=torch.bool), 1, 1
        )
    actual = torch.autograd.grad(surrogate, stop_logit)[0]
    torch.testing.assert_close(actual, exact_gradient)


@pytest.mark.parametrize("initialized", [False, True])
def test_transaction_restores_weights_moments_and_lazy_state(initialized: bool) -> None:
    model = nn.Linear(2, 1)
    optimizer = AdamW(model.parameters(), lr=0.03)
    for parameter in model.parameters():
        parameter.grad = torch.ones_like(parameter)
    if initialized:
        optimizer.step()
    before = copy.deepcopy(model.state_dict())
    state_before = copy.deepcopy(optimizer.state_dict())
    pointers = [parameter.data_ptr() for parameter in model.parameters()]
    transaction = OptimizerTransaction(model, optimizer)
    for _ in range(2):
        optimizer.step()
        transaction.restore()
        for name, value in model.state_dict().items():
            torch.testing.assert_close(value, before[name], rtol=0, atol=0)
        actual = optimizer.state_dict()
        assert actual["param_groups"] == state_before["param_groups"]
        assert actual["state"].keys() == state_before["state"].keys()
        for key, values in state_before["state"].items():
            for field, value in values.items():
                torch.testing.assert_close(actual["state"][key][field], value, rtol=0, atol=0)
        assert [parameter.data_ptr() for parameter in model.parameters()] == pointers


def test_guard_retries_a_step_and_rejects_the_last_attempt() -> None:
    model = nn.Linear(1, 1, bias=False)
    optimizer = AdamW(model.parameters(), lr=0.1, weight_decay=0.0)
    parameters = tuple(model.parameters())
    before = model.weight.detach().clone()
    model.weight.grad = torch.ones_like(model.weight)

    def displacement() -> float:
        return float((model.weight.detach() - before).square().sum())

    result = guarded_optimizer_step(
        model,
        optimizer,
        parameters,
        displacement,
        target_kl=0.004,
        backoff_factor=0.5,
        maximum_retries=2,
    )
    assert result.accepted
    assert result.rejected_attempts > 0
    assert displacement() <= 0.004
    accepted = model.weight.detach().clone()
    clock = optimizer.state[model.weight]["step"].clone()
    result = guarded_optimizer_step(
        model,
        optimizer,
        parameters,
        lambda: float("inf"),
        target_kl=0.004,
        backoff_factor=0.5,
        maximum_retries=1,
    )
    assert not result.accepted
    torch.testing.assert_close(model.weight, accepted, rtol=0, atol=0)
    torch.testing.assert_close(optimizer.state[model.weight]["step"], clock, rtol=0, atol=0)
