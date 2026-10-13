import copy
from typing import Any

import pytest
import torch

from kagg_revue.production.protection import guarded_step, has_return_variation


def _primed_optimizer() -> tuple[torch.nn.Parameter, torch.optim.AdamW]:
    parameter = torch.nn.Parameter(torch.tensor([0.4, -0.6]))
    optimizer = torch.optim.AdamW([parameter], lr=0.4, weight_decay=0)
    parameter.square().sum().backward()
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    (parameter - 2).square().sum().backward()
    return parameter, optimizer


def test_backtracking_restores_adam_moments_before_retrying() -> None:
    parameter, optimizer = _primed_optimizer()
    before = parameter.detach().clone()
    expected = torch.nn.Parameter(before.clone())
    expected.grad = parameter.grad.clone()
    reference = torch.optim.AdamW([expected])
    reference.load_state_dict(copy.deepcopy(optimizer.state_dict()))
    reference.param_groups[0]["lr"] *= 0.25
    reference.step()
    limit = float((expected - before).square().sum().detach()) * 1.1
    result = guarded_step(
        optimizer,
        lambda: float((parameter - before).square().sum().detach()),
        maximum=limit,
        attempts=4,
        decay=0.5,
    )
    assert result.accepted and result.rejections == 2
    torch.testing.assert_close(parameter, expected)
    for name, value in reference.state[expected].items():
        torch.testing.assert_close(optimizer.state[parameter][name], value)
    # Resume must preserve the accepted moment state and reduced learning rate.
    resumed = torch.optim.AdamW([torch.nn.Parameter(parameter.detach().clone())])
    resumed.load_state_dict(copy.deepcopy(optimizer.state_dict()))
    assert resumed.param_groups[0]["lr"] == reference.param_groups[0]["lr"]
    assert resumed.param_groups[0]["guard_lr_scale"] < 1


def test_rejected_nonfinite_steps_restore_parameters_and_optimizer() -> None:
    parameter, optimizer = _primed_optimizer()
    before = parameter.detach().clone()
    state = copy.deepcopy(optimizer.state[parameter])
    result = guarded_step(optimizer, lambda: float("nan"), maximum=0.3, attempts=2, decay=0.4)
    assert not result.accepted and result.rejections == result.attempts
    torch.testing.assert_close(parameter, before)
    for name, value in state.items():
        torch.testing.assert_close(optimizer.state[parameter][name], value)


@pytest.mark.parametrize("divergence", [0.1, 0.4, float("nan")])
def test_constant_rate_guard_attempts_once_and_preserves_adam_on_rejection(divergence):
    parameter, optimizer = _primed_optimizer()
    before = parameter.detach().clone()
    state = copy.deepcopy(optimizer.state_dict())
    calls = []

    def measure():
        calls.append(float(parameter.detach().sum()))
        return divergence

    result = guarded_step(optimizer, measure, maximum=0.3, attempts=3, decay=1)
    assert result.attempts == len(calls) == 1
    assert optimizer.param_groups[0]["lr"] == state["param_groups"][0]["lr"]
    assert "guard_lr_scale" not in optimizer.param_groups[0]
    assert result.accepted == (divergence <= 0.3)
    if result.accepted:
        assert not torch.equal(parameter, before)
        assert optimizer.state[parameter]["step"] == state["state"][0]["step"] + 1
    else:
        assert result.rejections == 1
        torch.testing.assert_close(parameter, before)
        for name, value in state["state"][0].items():
            torch.testing.assert_close(optimizer.state[parameter][name], value)


def test_constant_return_check_uses_global_extrema(monkeypatch: pytest.MonkeyPatch) -> None:
    assert not has_return_variation(torch.full((3,), 4.0))
    assert has_return_variation(torch.tensor([4.0, -7.0]))
    monkeypatch.setattr("torch.distributed.is_initialized", lambda: True)

    def include_peer(bounds: torch.Tensor, **_: Any) -> None:
        bounds.copy_(torch.minimum(bounds, torch.tensor([-7.0, 7.0])))

    monkeypatch.setattr("torch.distributed.all_reduce", include_peer)
    # Each rank can have constant returns while the global rollout has signal.
    assert has_return_variation(torch.full((3,), 4.0))
