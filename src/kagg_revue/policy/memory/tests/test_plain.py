"""Preserve the old entity encoder while adding independent causal memory."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.learning.sequences.critic import MemoryCritic
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.encoder import ContextEncoder
from kagg_revue.policy.memory.blocks import Gate
from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.spatial.encoder import Block
from kagg_revue.policy.spatial.model import log_probabilities


def test_plain_encoder_is_identical_and_memory_remains_causal() -> None:
    """Encoder weights/outputs match the old policy and memory gets finite gradients."""
    torch.set_num_threads(1)
    config = Experiment(
        output_dir=Path("outputs/learning/plain-memory-test"),
        architecture="grounded-v2",
        decision_interval=1,
        width=16,
        depth=3,
        critic_width=16,
        critic_depth=2,
        memory_width=16,
        memory_turns=4,
        sequence_chunk_turns=2,
        gated=False,
        unit_limit=3,
        quantity_max=100,
        quantity_extra=(),
        environment={
            "boardSize": 4,
            "episodeSteps": 9,
            "turnsPerDay": 4,
            "maxMarketOrdersPerTurn": 2,
        },
    )
    layout = ContractLayout.resolve(runtime_settings(config))
    legacy = random_policy(
        replace(layout, network=replace(layout.network, memory_turns=0)), 17, config.exploration
    )
    actor = random_policy(layout, 17, config.exploration)
    assert isinstance(actor, MemoryPolicy)
    critic = MemoryCritic(layout)
    assert isinstance(critic.entity_encoder, ContextEncoder)
    assert all(isinstance(block, Block) for block in actor.encoder.blocks)
    assert all(isinstance(block, Block) for block in critic.entity_encoder.blocks)
    assert not any(isinstance(block, Gate) for block in actor.encoder.modules())
    for key, value in legacy.encoder.state_dict().items():
        torch.testing.assert_close(value, actor.encoder.state_dict()[key], rtol=0, atol=0)
    session = native.ContractSession(config.environment, config.unit_limit)
    session.update(native.Engine(21, config.environment).observation(0))
    array = np.empty((1, layout.observation.features), np.float16)
    session.observe_into(array)
    observation = torch.from_numpy(array)
    torch.testing.assert_close(legacy.encoder(observation), actor.encoder(observation))
    observations = observation[None].expand(8, -1, -1).clone()
    actions = torch.zeros(8, 1, layout.factors, dtype=torch.long)
    state = actor.memory.temporal.empty(1, torch.device("cpu"))
    _, complete, _ = actor.sequence(observations, torch.arange(8), state, actions)
    pieces = []
    for start in range(0, 8, 2):
        _, output, state = actor.sequence(
            observations[start : start + 2],
            torch.arange(start, start + 2),
            state,
            actions[start : start + 2],
        )
        pieces.append(output)
    torch.testing.assert_close(torch.cat(pieces), complete, atol=2e-5, rtol=2e-5)
    loss = -log_probabilities(complete.flatten(0, 1), actions.flatten(0, 1)).mean()
    loss.backward()  # type: ignore[no-untyped-call]
    assert all(torch.isfinite(p.grad).all() for p in actor.parameters() if p.grad is not None)
    for group in (actor.encoder, actor.memory.temporal, actor.memory.gate):
        assert any(p.grad is not None and p.grad.abs().sum() > 0 for p in group.parameters())
