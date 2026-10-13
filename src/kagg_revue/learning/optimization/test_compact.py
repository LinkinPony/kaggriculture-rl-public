"""Check padding-free PPO against the original complete native action tensors."""

import copy
from pathlib import Path

import numpy as np
import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.learning.optimization.kernels import PrefixLosses
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.native.batches import create_selfplay_batch
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.typed import TypedGroundedPolicy


def test_semantic_compression_preserves_values_objectives_and_all_gradients() -> None:
    """Exercise learned prefix deltas, entropy, unequal weights and absent-unit padding."""
    torch.set_num_threads(1)
    torch.manual_seed(411)
    config = Experiment(
        output_dir=Path("outputs/learning/compact-check"),
        architecture="grounded-v2",
        market_budget=True,
        agronomy=True,
        decision_interval=1,
        width=32,
        depth=1,
        critic_width=32,
        critic_depth=1,
        unit_limit=4,
        quantity_max=4,
        compile=False,
        precision="fp32",
        entropy_weight=0.01,
        environment={
            "boardSize": 4,
            "episodeSteps": 17,
            "turnsPerDay": 4,
            "maxMarketOrdersPerTurn": 3,
        },
    )
    settings = runtime_settings(config)
    actor = random_policy(ContractLayout.resolve(settings), 411, config.exploration)
    assert isinstance(actor, TypedGroundedPolicy)
    critic = PrefixCritic(actor.layout)
    readout = critic.delta[-1]
    assert isinstance(readout, torch.nn.Linear)
    torch.nn.init.normal_(readout.weight, std=0.1)
    packed = np.empty((8, actor.layout.observation.features), np.float16)
    create_selfplay_batch(settings, list(range(4))).observe_selfplay_into(packed)
    observations = torch.from_numpy(packed)
    steps = torch.zeros(8, dtype=torch.long)
    with torch.no_grad():
        actions, _ = actor.act(observations, steps, sample=True)
        actions[:, actor.layout.work_factors :] = torch.tensor([11, 1, 2, 1, 0, 0])
        logits = actor(observations, steps, actions)
        behavior = logits.log_softmax(-1).gather(-1, actions[..., None]).squeeze(-1)
        fields = actor.field_weights(actions, steps, observations)
        torch.testing.assert_close(
            actor.compact_logits(observations, actions), logits[:, actor.semantic_fields]
        )
        dense = critic.prefixes(observations, actions, fields)
        compact = critic.prefixes(observations, actions, fields, compact=True)
        for dense_value, compact_value in zip(dense, compact, strict=True):
            torch.testing.assert_close(dense_value, compact_value)
    other_actor, other_critic = copy.deepcopy(actor), copy.deepcopy(critic)
    reference = PrefixLosses(actor, critic, settings.ppo)
    reference.compact = False
    optimized = PrefixLosses(other_actor, other_critic, settings.ppo)
    credits = torch.randn_like(behavior)
    weights = torch.linspace(0.5, 1, 8)
    returns = torch.linspace(-1, 1, 8)
    expected = None
    for losses in (reference, optimized):
        gain, kl = losses.actor(
            observations, steps, actions, behavior, credits, weights, weights.sum(), 1.0
        )
        values = losses.value(observations, steps, actions, returns, weights, weights.sum())
        actual = torch.stack((gain, kl, *values))
        if expected is None:
            expected = actual.detach()
        else:
            torch.testing.assert_close(actual, expected)
        (gain + values[0]).backward()  # type: ignore[no-untyped-call]
    for before, after in ((actor, other_actor), (critic, other_critic)):
        assert before.state_dict().keys() == after.state_dict().keys()
        assert "semantic_fields" not in before.state_dict()
        for (name, left), (_, right) in zip(
            before.named_parameters(), after.named_parameters(), strict=True
        ):
            assert (left.grad is None) == (right.grad is None), name
            if left.grad is not None:
                torch.testing.assert_close(
                    left.grad,
                    right.grad,
                    atol=2e-6,
                    rtol=2e-5,
                    msg=name,
                )
