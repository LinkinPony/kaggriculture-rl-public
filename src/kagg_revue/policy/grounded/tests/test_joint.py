"""Joint unit decoding: sampling and teacher forcing define the same distribution."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.migration import expand_units
from kagg_revue.policy.memory.policy import MemoryPolicy


def test_joint_units_expand_exactly_and_sample_consistently() -> None:
    """Zero-output expansion keeps the parent; sequential logits match teacher forcing."""
    torch.set_num_threads(1)
    config = Experiment(
        output_dir=Path("outputs/learning/joint-units-test"),
        architecture="grounded-v2",
        decision_interval=1,
        width=16,
        depth=2,
        heads=4,
        critic_width=16,
        critic_depth=2,
        memory_width=16,
        memory_turns=4,
        sequence_chunk_turns=2,
        joint_units=True,
        unit_limit=4,
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
    parent = random_policy(
        replace(layout, network=replace(layout.network, joint_units=False)), 17, config.exploration
    )
    actor, report = expand_units(parent, layout)
    assert isinstance(parent, MemoryPolicy) and isinstance(actor, MemoryPolicy)
    assert actor.joint is not None and report["added_tensors"] > 0
    session = native.ContractSession(config.environment, config.unit_limit)
    session.update(native.Engine(21, config.environment).observation(0))
    array = np.empty((1, layout.observation.features), np.float16)
    session.observe_into(array)
    base, width = layout.observation, layout.observation.unit_features
    farmer = array[0, base.board_features : base.board_features + width].copy()
    support = array[0, -base.support_features :].reshape(base.units, 44)
    for unit in range(1, base.units):
        clone = farmer.copy()
        clone[2:4] = (unit % 4 / 3, unit // 4 / 3)  # A distinct tile for every clone.
        start = base.board_features + unit * width
        array[0, start : start + width] = clone
        support[unit] = support[0]
    array[0, -base.support_features :] = support.reshape(-1)
    observations = torch.from_numpy(array)[None].expand(2, 3, -1).clone()
    steps = torch.arange(2)
    parent.eval()
    actor.eval()
    state = parent.memory.temporal.empty(3, torch.device("cpu"))
    with torch.no_grad():
        chosen, expected, _ = parent.sequence(observations, steps, state, sample=True)
        _, inherited, _ = actor.sequence(observations, steps, state, chosen)
        torch.testing.assert_close(inherited, expected, rtol=0, atol=0)
        torch.nn.init.normal_(actor.joint.output.weight, std=0.5)
        torch.manual_seed(5)
        sampled, logits, _ = actor.sequence(observations, steps, state, sample=True)
        _, forced, _ = actor.sequence(observations, steps, state, sampled)
    torch.testing.assert_close(forced, logits, rtol=1e-5, atol=1e-5)
    assert bool(actor._units(observations.flatten(0, 1))[2][:, 1:, 0].all())
    with torch.no_grad():
        changed = sampled.clone()
        changed[..., 0] = 0  # The farmer passes instead; later units must react.
        _, reacted, _ = actor.sequence(observations, steps, state, changed)
    shape = (2, 3, base.units, 2, 4, -1)
    before = forced[:, :, : layout.work_factors].reshape(shape)
    after = reacted[:, :, : layout.work_factors].reshape(shape)
    assert not torch.equal(after[:, :, 1:, 0, 0], before[:, :, 1:, 0, 0])
