import math
from typing import Any, cast

import pytest
import torch
from torch import nn

from kagg_revue.policy.model import PolicyOutput
from kagg_revue.policy.tasks.grammar import TaskActions, TaskConditionalMasks
from kagg_revue.policy.tasks.schema import TaskPolicyOutput
from kagg_revue.rl.tasks.learning import (
    TaskUpdateMetrics,
    _combine_microbatch_metrics,
    _EpisodeLossCounts,
    _global_step_metrics,
    _set_ppo_training_mode,
)
from kagg_revue.rl.tasks.objective import (
    AdvantageReference,
    market_ppo_loss,
    task_ppo_loss,
    task_terminal_advantages,
)


def test_ppo_mode_disables_dropout_but_keeps_recurrent_backward() -> None:
    class SyntheticActor(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.scene = nn.Sequential(nn.Dropout(p=1.0))
            self.action = nn.Sequential(nn.Dropout(p=1.0))
            self.strategy = nn.GRU(3, 3, batch_first=True)

    class SyntheticModel(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.actor = SyntheticActor()
            self.tasks = nn.Sequential(nn.Dropout(p=1.0))

    model = SyntheticModel()
    _set_ppo_training_mode(model)  # type: ignore[arg-type]
    assert model.training
    assert model.actor.strategy.training
    assert not model.actor.scene.training
    assert not model.actor.action.training
    assert not model.tasks.training
    inputs = torch.randn(2, 4, 3, requires_grad=True)
    output, _state = model.actor.strategy(inputs)
    output.sum().backward()
    assert inputs.grad is not None


def test_rollout_reference_keeps_homogeneous_minibatch_actor_active() -> None:
    advantages = task_terminal_advantages(
        torch.tensor([1, 1]),
        torch.tensor([0.25, -0.25]),
        torch.tensor([0, 1]),
        normalize=True,
        reference=AdvantageReference(mean=0.0, scale=0.5, actor_update=True),
    )
    assert advantages.actor_update
    torch.testing.assert_close(advantages.values, torch.tensor([1.5, 2.5]))


def test_task_ppo_uses_one_ratio_and_excludes_forced_rows() -> None:
    factors = torch.tensor([[True, True, False, False, False], [False, False, False, False, False]])
    masks = TaskConditionalMasks(
        mode=torch.ones(2, 2, dtype=torch.bool),
        candidate=torch.ones(2, 3, dtype=torch.bool),
        quantity=torch.ones(2, 2, dtype=torch.bool),
        earliest=torch.ones(2, 3, dtype=torch.bool),
        deadline=torch.ones(2, 3, dtype=torch.bool),
        factors=factors,
    )
    zeros = torch.zeros(2, dtype=torch.long)
    output = TaskPolicyOutput(
        actions=TaskActions(zeros, zeros, zeros, zeros, zeros),
        masks=masks,
        joint_log_probability=torch.tensor([0.1, 100.0], requires_grad=True),
        factor_log_probability=torch.zeros(2, 5),
        entropy=torch.tensor([0.5, 100.0]),
        factor_entropy=torch.zeros(2, 5),
        outcome_logits=torch.zeros(2, 3, requires_grad=True),
        value=torch.zeros(2),
    )
    outcomes = torch.tensor([-1, 1])
    episodes = torch.tensor([0, 1])
    advantages = task_terminal_advantages(outcomes, torch.zeros(2), episodes, normalize=False)
    loss = task_ppo_loss(
        output,
        old_joint_log_probability=torch.zeros(2),
        advantages=advantages.values,
        outcomes=outcomes,
        episode_index=episodes,
        clip_epsilon=0.2,
        value_loss_weight=1.0,
        entropy_weight=0.01,
        actor_update=advantages.actor_update,
    )
    assert int(loss.policy_factors) == 1
    assert torch.isfinite(loss.total)
    loss.total.backward()  # type: ignore[no-untyped-call]


def test_market_ppo_ignores_compiler_unit_tokens() -> None:
    action_logits = torch.zeros(2, 1, 2, 3)
    legal = torch.zeros_like(action_logits, dtype=torch.bool)
    legal[:, :, 0, 0] = True
    legal[:, :, 1, 1:] = True
    actions = torch.tensor([[[0, 1]], [[0, 1]]])
    quantities = torch.zeros_like(actions)
    factor_mask = torch.tensor([[[False, True]], [[False, True]]])
    output = PolicyOutput(
        action_logits=action_logits,
        quantity_logits=torch.zeros(2, 1, 2, 2),
    )
    loss = market_ppo_loss(
        output,
        outcome_logits=torch.zeros(2, 1, 3),
        actions=actions,
        quantities=quantities,
        legal_mask=legal,
        policy_factor_mask=factor_mask,
        old_log_probability=torch.tensor([[[0.0, -math.log(2.0)]], [[0.0, -math.log(2.0)]]]),
        advantages=torch.tensor([[1.0], [-1.0]]),
        outcomes=torch.tensor([1, -1]),
        turn_mask=torch.ones(2, 1, dtype=torch.bool),
        has_quantity=torch.zeros(3, dtype=torch.bool),
        clip_epsilon=0.2,
        value_loss_weight=1.0,
        entropy_weight=0.0,
        actor_update=True,
    )
    assert int(loss.policy_factors) == 2
    assert torch.isfinite(loss.total)


def test_microbatch_metrics_preserve_logical_reductions() -> None:
    first = TaskUpdateMetrics(
        total_loss=1.0,
        task_policy_loss=2.0,
        task_value_loss=3.0,
        task_entropy=4.0,
        task_kl=0.1,
        task_clip_fraction=0.25,
        market_policy_loss=4.0,
        market_value_loss=5.0,
        market_entropy=6.0,
        market_kl=0.2,
        market_clip_fraction=0.3,
        gradient_norm=0.0,
        actor_update=True,
        task_factors=7,
        market_factors=10,
    )
    second = TaskUpdateMetrics(
        total_loss=3.0,
        task_policy_loss=6.0,
        task_value_loss=7.0,
        task_entropy=8.0,
        task_kl=0.5,
        task_clip_fraction=0.75,
        market_policy_loss=10.0,
        market_value_loss=9.0,
        market_entropy=12.0,
        market_kl=0.8,
        market_clip_fraction=0.9,
        gradient_norm=0.0,
        actor_update=True,
        task_factors=11,
        market_factors=30,
    )

    combined = _combine_microbatch_metrics(
        (first, second),
        (
            _EpisodeLossCounts(task_episodes=1, market_episodes=1, market_turns=2),
            _EpisodeLossCounts(task_episodes=3, market_episodes=2, market_turns=6),
        ),
        _EpisodeLossCounts(task_episodes=4, market_episodes=3, market_turns=8),
        torch.tensor(13.0),
    )

    assert combined.total_loss == 4.0
    assert combined.task_policy_loss == 5.0
    assert combined.task_value_loss == 6.0
    assert combined.task_entropy == 7.0
    assert combined.task_kl == 0.4
    assert combined.task_clip_fraction == 0.625
    assert combined.market_policy_loss == 8.0
    assert combined.market_value_loss == 8.0
    assert combined.market_entropy == 10.0
    assert combined.market_kl == 0.65
    assert combined.market_clip_fraction == 0.75
    assert combined.gradient_norm == 13.0
    assert combined.task_factors == 18
    assert combined.market_factors == 40


def test_kl_gate_uses_global_weighted_means_not_rank_maximum() -> None:
    metrics = TaskUpdateMetrics(
        total_loss=1.0,
        task_policy_loss=2.0,
        task_value_loss=3.0,
        task_entropy=4.0,
        task_kl=0.1,
        task_clip_fraction=0.2,
        market_policy_loss=5.0,
        market_value_loss=6.0,
        market_entropy=7.0,
        market_kl=0.2,
        market_clip_fraction=0.3,
        gradient_norm=8.0,
        actor_update=True,
        task_factors=9,
        market_factors=10,
    )

    class SyntheticContext:
        def all_gather(self, value: dict[str, float | int]) -> list[dict[str, float | int]]:
            return [
                value,
                {
                    "task_kl": 0.3,
                    "task_clip_fraction": 0.4,
                    "task_episodes": 6,
                    "market_kl": 0.4,
                    "market_clip_fraction": 0.5,
                    "market_factors": 30,
                },
            ]

    combined, maximum_task, maximum_market = _global_step_metrics(
        metrics,
        _EpisodeLossCounts(task_episodes=2, market_episodes=2, market_turns=4),
        cast(Any, SyntheticContext()),
    )

    assert combined.task_kl == pytest.approx(0.25)
    assert combined.task_clip_fraction == pytest.approx(0.35)
    assert combined.market_kl == pytest.approx(0.35)
    assert combined.market_clip_fraction == pytest.approx(0.45)
    assert maximum_task == 0.3
    assert maximum_market == 0.4
