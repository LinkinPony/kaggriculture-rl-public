"""Numerical checks for turn-based GAE and recoverable learning-rate warmup."""

import copy
from pathlib import Path

import pytest
import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.optimization.prefix import prefix_credit
from kagg_revue.learning.optimization.returns import generalized_returns
from kagg_revue.learning.state import protocol


@pytest.mark.parametrize("gamma,trace", [(0.999, 0.95), (0.999, 0.0), (0.999, 1.0), (1.0, 1.0)])
def test_turn_gae_matches_scalar_recursion_and_terminal_boundaries(
    gamma: float, trace: float
) -> None:
    """Compare independent win/draw/loss seats, a long horizon and the terminal step."""
    turns, seats = 719, 3
    values = torch.linspace(-0.6, 0.8, turns * seats, dtype=torch.float64).reshape(turns, seats)
    outcomes = torch.tensor([1.0, 0.0, -1.0], dtype=torch.float64).expand(turns, seats)
    steps = torch.arange(turns).repeat_interleave(seats)
    expected = torch.empty_like(values)
    credit = torch.zeros(seats, dtype=torch.float64)
    for turn in reversed(range(turns)):
        next_value = values[turn + 1] if turn + 1 < turns else torch.zeros_like(credit)
        reward = outcomes[turn] if turn == turns - 1 else torch.zeros_like(credit)
        credit = reward + gamma * next_value - values[turn] + gamma * trace * credit
        expected[turn] = credit + values[turn]
    actual = generalized_returns(values.flatten(), outcomes.flatten(), steps, turns, gamma, trace)
    torch.testing.assert_close(actual.view_as(values), expected)
    torch.testing.assert_close(actual[-seats:], outcomes[-1])
    if trace == 1:
        discounted = gamma ** torch.arange(turns - 1, -1, -1, dtype=torch.float64)
        torch.testing.assert_close(actual.view_as(values), outcomes * discounted[:, None])
    with pytest.raises(ValueError, match="clocks"):
        generalized_returns(
            values.flatten(), outcomes.flatten(), steps.flip(0), turns, gamma, trace
        )


def test_temporal_target_replaces_prefix_outcome_without_discounting_padding() -> None:
    """Every active conditional field receives the same future-turn target adjustment."""
    prefixes = torch.tensor([[0.2, 0.4, -0.1, 0.7], [-0.3, 0.1, 0.5, 0.6]])
    fields = torch.tensor([[1.0, 0.0, 1.0, 0.0], [1.0, 1.0, 0.0, 1.0]])
    terminal = torch.tensor([1.0, -1.0])
    targets = torch.tensor([0.17, -0.08])
    actual = prefix_credit(prefixes, fields, terminal, 1.0)
    actual += (targets - terminal)[:, None] * fields
    torch.testing.assert_close(actual, prefix_credit(prefixes, fields, targets, 1.0))
    assert not actual[~fields.bool()].any()


def test_warmup_uses_absolute_updates_after_optimizer_restore() -> None:
    """A saved optimizer rate never restarts or bypasses the 500-update ramp."""
    config = Experiment(
        output_dir=Path("outputs/learning/warmup-test"),
        device="cpu",
        compile=False,
        architecture="grounded-v2",
        decision_interval=1,
        actor_learning_rate=1e-4,
        critic_learning_rate=1e-4,
        learning_rate_warmup_updates=500,
        gamma=0.999,
        gae_lambda=0.95,
    )
    settings = runtime_settings(config)
    learner = Learner.__new__(Learner)
    learner.settings = settings
    learner.actor_optimizer = torch.optim.AdamW([torch.nn.Parameter(torch.ones(1))], lr=1e-4)
    learner.critic_optimizer = torch.optim.AdamW([torch.nn.Parameter(torch.ones(1))], lr=1e-4)
    for update, expected in [(1, 2e-7), (250, 5e-5), (500, 1e-4), (501, 1e-4)]:
        learner.schedule(update)
        for optimizer in (learner.actor_optimizer, learner.critic_optimizer):
            assert optimizer.param_groups[0]["lr"] == pytest.approx(expected)
    learner.schedule(123)
    saved = copy.deepcopy(learner.actor_optimizer.state_dict())
    learner.actor_optimizer.load_state_dict(saved)
    learner.schedule(124)
    assert learner.actor_optimizer.param_groups[0]["lr"] == pytest.approx(1e-4 * 124 / 500)
    assert settings.ppo.gamma == 0.999 and settings.ppo.gae_lambda == 0.95
    old = config.model_copy(
        update={"gamma": 1.0, "gae_lambda": 1.0, "learning_rate_warmup_updates": 0}
    )
    assert not {"gamma", "gae_lambda", "learning_rate_warmup_updates"} & protocol(old).keys()


@pytest.mark.parametrize("mode", ["early_stop", "rollback", "decayed"])
def test_rate_change_restores_adam_moments_and_honors_constant_rate(mode: str) -> None:
    """A recurrent PPO resume changes LR without resetting Adam or adaptive guard rates."""
    config = Experiment(
        output_dir=Path("outputs/learning/rate-test"),
        actor_learning_rate=2e-5,
        critic_learning_rate=1e-4,
        kl_control="early_stop" if mode == "early_stop" else "rollback",
    )
    learner = Learner.__new__(Learner)
    learner.settings = runtime_settings(config)
    if mode == "decayed":
        options = learner.settings.ppo
        assert options.protection is not None
        learner.settings = learner.settings.model_copy(
            update={
                "ppo": options.model_copy(
                    update={
                        "protection": options.protection.model_copy(
                            update={"learning_rate_decay": 0.5}
                        )
                    }
                )
            }
        )
    saved = []
    for name, rate in (("actor_optimizer", 7.5e-6), ("critic_optimizer", 1e-4)):
        parameter = torch.nn.Parameter(torch.ones(2))
        optimizer = torch.optim.AdamW([parameter], lr=rate)
        parameter.grad = torch.tensor([0.5, -0.25])
        optimizer.step()
        saved.append(copy.deepcopy(optimizer.state_dict()))
        setattr(learner, name, optimizer)
    learner.restore_optimizers(*saved)
    for optimizer, previous in zip(
        (learner.actor_optimizer, learner.critic_optimizer), saved, strict=True
    ):
        restored = optimizer.state_dict()
        for parameter, values in previous["state"].items():
            for key, value in values.items():
                assert torch.equal(restored["state"][parameter][key], value)
    expected = 7.5e-6 if mode == "decayed" else 2e-5
    assert learner.actor_optimizer.param_groups[0]["lr"] == expected
    assert learner.critic_optimizer.param_groups[0]["lr"] == 1e-4
