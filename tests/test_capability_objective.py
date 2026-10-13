from __future__ import annotations

import torch

from kagg_revue.rl.capabilities.objective import (
    episode_balanced_mean,
    macro_ppo_loss,
    paired_direct_residual_advantages,
    paired_direct_wdl_advantages,
    terminal_wdl_advantages,
)


def test_macro_ppo_uses_episode_balance_and_disables_flat_wdl_actor() -> None:
    episode_index = torch.tensor([0, 1, 1, 1])
    durations = torch.tensor([24, 24, 24, 23])
    outcomes = torch.tensor([-1.0, 1.0])
    old_values = torch.zeros(4)
    advantages = terminal_wdl_advantages(
        outcomes,
        old_values,
        episode_index,
        durations,
        normalize=False,
    )

    assert advantages.actor_update
    assert torch.equal(advantages.values, torch.tensor([-1.0, 1.0, 1.0, 1.0]))
    assert torch.equal(
        episode_balanced_mean(torch.tensor([2.0, 3.0, 3.0, 3.0]), episode_index, 2),
        torch.tensor(2.5),
    )

    new_log_probability = torch.zeros(4, requires_grad=True)
    loss = macro_ppo_loss(
        new_log_probability,
        torch.zeros(4),
        torch.ones(4),
        torch.zeros(4, 3, requires_grad=True),
        advantages.values,
        outcomes,
        episode_index,
        durations,
        clip_epsilon=0.1,
        value_loss_weight=1.0,
        entropy_weight=0.01,
        actor_update=advantages.actor_update,
    )
    loss.total.backward()
    assert torch.isfinite(loss.total)
    assert new_log_probability.grad is not None

    flat = terminal_wdl_advantages(
        torch.full((2,), -1.0),
        old_values,
        episode_index,
        durations,
        normalize=True,
    )
    assert not flat.actor_update


def test_paired_direct_advantage_removes_same_job_outcome_difficulty() -> None:
    episode_index = torch.tensor([0, 0, 1, 2, 2])
    durations = torch.ones(5, dtype=torch.long)
    advantages = paired_direct_wdl_advantages(
        outcomes=torch.tensor([1.0, -1.0, 0.0]),
        direct_outcomes=torch.tensor([1.0, 0.0, -1.0]),
        episode_index=episode_index,
        durations=durations,
        normalize=False,
    )

    assert advantages.actor_update
    assert torch.equal(
        advantages.values,
        torch.tensor([0.0, 0.0, -1.0, 1.0, 1.0]),
    )


def test_residual_advantage_and_ppo_only_credit_interventions() -> None:
    episode_index = torch.tensor([0, 0, 1, 1, 2])
    durations = torch.ones(5, dtype=torch.long)
    intervention_mask = torch.tensor([False, True, False, False, True])
    advantages = paired_direct_residual_advantages(
        outcomes=torch.tensor([-1.0, 1.0, 1.0]),
        direct_outcomes=torch.tensor([0.0, -1.0, 1.0]),
        episode_index=episode_index,
        durations=durations,
        intervention_mask=intervention_mask,
        normalize=False,
    )

    assert advantages.actor_update
    assert torch.equal(
        advantages.values,
        torch.tensor([0.0, -1.0, 0.0, 0.0, 0.0]),
    )
    new_log_probability = torch.zeros(5, requires_grad=True)
    loss = macro_ppo_loss(
        new_log_probability,
        torch.zeros(5),
        torch.ones(5),
        torch.zeros(5, 3, requires_grad=True),
        advantages.values,
        torch.tensor([-1.0, 1.0, 1.0]),
        episode_index,
        durations,
        clip_epsilon=0.1,
        value_loss_weight=0.0,
        entropy_weight=0.0,
        actor_update=advantages.actor_update,
        policy_mask=intervention_mask,
    )
    loss.total.backward()

    assert new_log_probability.grad is not None
    assert torch.count_nonzero(new_log_probability.grad[~intervention_mask]) == 0
    assert new_log_probability.grad[1] > 0
