from __future__ import annotations

import torch

from kagg_revue.rl.plans.objective import plan_ppo_loss, terminal_wdl_advantages


def test_structured_plan_advantage_is_undiscounted_and_skips_homogeneous_actor() -> None:
    outcomes = torch.tensor([-1.0, 1.0])
    episode_index = torch.tensor([0, 0, 1])
    old_values = torch.zeros(3)
    durations = torch.tensor([1, 17, 400])
    advantages = terminal_wdl_advantages(
        outcomes,
        old_values,
        episode_index,
        durations,
        normalize=False,
    )
    assert advantages.actor_update
    assert torch.equal(advantages.values, torch.tensor([-1.0, -1.0, 1.0]))

    homogeneous = terminal_wdl_advantages(
        torch.tensor([-1.0, -1.0]),
        old_values,
        episode_index,
        durations,
        normalize=True,
    )
    assert not homogeneous.actor_update
    assert torch.equal(homogeneous.values, torch.full((3,), -1.0))


def test_structured_plan_ppo_uses_one_joint_ratio_and_duration_balanced_entropy() -> None:
    old_log_probability = torch.tensor([-2.0, -3.0, -4.0])
    outcomes = torch.tensor([-1.0, 1.0])
    episode_index = torch.tensor([0, 0, 1])
    durations = torch.tensor([3, 9, 2])
    loss = plan_ppo_loss(
        new_joint_log_probability=old_log_probability.clone().requires_grad_(),
        old_joint_log_probability=old_log_probability,
        decision_entropy=torch.tensor([0.0, 2.0, 4.0]),
        factor_counts=torch.tensor([2, 8, 4]),
        outcome_logits=torch.zeros(3, 3, requires_grad=True),
        advantages=torch.tensor([-1.0, -1.0, 1.0]),
        outcomes=outcomes,
        episode_index=episode_index,
        durations=durations,
        clip_epsilon=0.1,
        value_loss_weight=1.0,
        entropy_weight=0.01,
        actor_update=True,
    )
    assert torch.allclose(loss.entropy, torch.tensor(2.75))
    assert torch.allclose(loss.approximate_kl, torch.tensor(0.0))
    assert torch.allclose(loss.clip_fraction, torch.tensor(0.0))
    loss.total.backward()


def test_homogeneous_terminal_panel_keeps_entropy_exploration_gradient() -> None:
    decision_entropy = torch.tensor([2.0, 4.0], requires_grad=True)
    loss = plan_ppo_loss(
        new_joint_log_probability=torch.zeros(2, requires_grad=True),
        old_joint_log_probability=torch.zeros(2),
        decision_entropy=decision_entropy,
        factor_counts=torch.tensor([2, 2]),
        outcome_logits=torch.zeros(2, 3, requires_grad=True),
        advantages=torch.zeros(2),
        outcomes=torch.zeros(2),
        episode_index=torch.tensor([0, 1]),
        durations=torch.ones(2, dtype=torch.long),
        clip_epsilon=0.1,
        value_loss_weight=1.0,
        entropy_weight=0.01,
        actor_update=False,
    )
    assert torch.equal(loss.policy, torch.tensor(0.0))
    loss.total.backward()
    assert decision_entropy.grad is not None
    assert torch.all(decision_entropy.grad < 0)
