"""Verify that the intervention removes history without changing learned weights."""

from pathlib import Path

import numpy as np
import torch

from kagg_revue.evaluation.memory.runtime import HistoryDuel, HistoryPolicy
from kagg_revue.evaluation.neural import PairedPolicy
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.memory.policy import MemoryPolicy, RecurrentExecution


def test_reset_matches_fresh_state_and_full_matches_normal_runtime() -> None:
    """Poisoned past cannot affect off mode; full mode agrees with normal inference."""
    torch.set_num_threads(1)
    config = Experiment(
        output_dir=Path("outputs/learning/memory-ablation-test"),
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
    actor = random_policy(ContractLayout.resolve(runtime_settings(config)), 17, config.exploration)
    assert isinstance(actor, MemoryPolicy)
    actor.eval()
    original = {key: value.clone() for key, value in actor.state_dict().items()}
    session = native.ContractSession(config.environment, config.unit_limit)
    session.update(native.Engine(21, config.environment).observation(0))
    values = np.empty((1, actor.layout.observation.features), np.float16)
    session.observe_into(values)
    observations = torch.from_numpy(values)
    wrapper = HistoryPolicy(actor, 1)
    normal = RecurrentExecution(actor, 1, torch.device("cpu"))
    with torch.no_grad():
        for turn in range(6):
            steps = torch.tensor([turn])
            actual = wrapper.act(observations, steps, sample=False)
            expected = normal.act(observations, steps, sample=False)
            for left, right in zip(actual, expected, strict=True):
                torch.testing.assert_close(left, right, rtol=0, atol=0)
        wrapper.history_enabled.fill_(False)
        for cached in (*wrapper.execution.state.keys, *wrapper.execution.state.values):
            cached.fill_(12345)
        normal.reset()
        actual = wrapper.act(observations, torch.tensor([6]), sample=False)
        expected = normal.act(observations, torch.tensor([6]), sample=False)
        for left, right in zip(actual, expected, strict=True):
            torch.testing.assert_close(left, right, rtol=0, atol=0)
        assert int((wrapper.execution.state.turns >= 0).sum()) == 4
        duel = HistoryDuel(actor, 2, torch.float32)
        assert isinstance(duel.learner, HistoryPolicy)
        assert isinstance(duel.opponent, HistoryPolicy)
        assert duel.learner.actor is duel.opponent.actor
        assert (
            duel.learner.execution.state.keys[0].data_ptr()
            != duel.opponent.execution.state.keys[0].data_ptr()
        )
        duel.learner.execution.state.turns.fill_(1)
        duel.opponent.execution.state.turns.fill_(1)
        duel.reset_memory()
        assert (duel.learner.execution.state.turns == -1).all()
        assert (duel.opponent.execution.state.turns == -1).all()
    for key, value in actor.state_dict().items():
        assert torch.equal(value, original[key])
    paired = PairedPolicy(actor, actor, 2, learner_temperature=0, opponent_temperature=1)
    greedy_memory = RecurrentExecution(actor, 2, torch.device("cpu"))
    sampled_memory = RecurrentExecution(actor, 2, torch.device("cpu"))
    with torch.no_grad():
        for turn in range(6):
            batch = observations.expand(4, -1)
            steps = torch.full((4,), turn, dtype=torch.long)
            torch.manual_seed(31 + turn)
            actions, _ = paired.act(batch, steps, sample=True)
            torch.manual_seed(31 + turn)
            expected_left, _ = greedy_memory.act(batch[:2], steps[:2], sample=False)
            expected_right, _ = sampled_memory.act(batch[:2], steps[:2], sample=True)
            torch.testing.assert_close(actions[paired.learner_rows], expected_left, rtol=0, atol=0)
            torch.testing.assert_close(
                actions[paired.opponent_rows], expected_right, rtol=0, atol=0
            )
        assert paired.left_memory is not None and paired.right_memory is not None
        assert torch.equal(paired.left_memory.state.turns, greedy_memory.state.turns)
        assert torch.equal(paired.right_memory.state.turns, sampled_memory.state.turns)
        paired.reset_memory()
        assert (paired.left_memory.state.turns == -1).all()
        assert (paired.right_memory.state.turns == -1).all()
