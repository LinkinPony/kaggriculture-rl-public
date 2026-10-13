from __future__ import annotations

import math

import torch

from kagg_revue.policy.programs.schema import ProgramSequenceOutput
from kagg_revue.rl.programs.objective import (
    program_ppo_loss,
    terminal_program_advantages,
)


def test_program_ppo_uses_one_episode_balanced_ratio_per_turn() -> None:
    episode_index = torch.tensor([0, 1, 1, 1])
    outcomes = torch.tensor([-1, 1], dtype=torch.int8)
    old_values = torch.zeros(4)
    advantages = terminal_program_advantages(
        outcomes,
        old_values,
        episode_index,
        normalize=False,
    )
    joint = torch.zeros(4, requires_grad=True)
    logits = torch.zeros((4, 3), requires_grad=True)
    factors = torch.ones((4, 1, 1), dtype=torch.bool)
    output = ProgramSequenceOutput(
        joint_log_probability=joint,
        normalized_entropy=torch.ones(4),
        factor_log_probability=torch.zeros((4, 1, 1)),
        factor_entropy=torch.ones((4, 1, 1)),
        factors=factors,
        outcome_logits=logits,
        value=torch.zeros(4),
    )
    loss = program_ppo_loss(
        output,
        torch.zeros(4),
        advantages.values,
        outcomes,
        episode_index,
        clip_epsilon=0.2,
        value_loss_weight=1.0,
        entropy_weight=0.0,
        actor_update=advantages.actor_update,
    )
    torch.testing.assert_close(loss.policy, torch.zeros(()))
    torch.testing.assert_close(loss.value, torch.tensor(math.log(3.0)))
    torch.testing.assert_close(loss.value_accuracy, torch.tensor(0.5))
    torch.testing.assert_close(loss.value_brier, torch.tensor(2.0 / 3.0))
    loss.total.backward()
    assert joint.grad is not None and torch.isfinite(joint.grad).all()
    assert logits.grad is not None and torch.isfinite(logits.grad).all()
