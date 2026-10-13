from pathlib import Path

import numpy as np
import pytest
import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.rewards import margin_diagnostics
from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.optimization.objectives import terminal_rewards
from kagg_revue.learning.optimization.settings import CashMargin
from kagg_revue.learning.recovery.rewards import margin_protocol, wdl_protocol
from kagg_revue.learning.state import protocol


def test_bounded_margin_is_zero_sum_translation_invariant_and_scales_the_gap() -> None:
    cash = np.array([[15000.0, 5000.0], [5000.0, 15000.0], [15000.0, 15000.0]])
    for values in (cash, cash + 700000.0):
        actual = terminal_rewards(
            values, cash_weight=0, cash_scale=10000, win_weight=1, cash_margin=CashMargin()
        )
        np.testing.assert_array_equal(actual, [[1.5, -1.5], [-1.5, 1.5], [0, 0]])
        np.testing.assert_array_equal(actual.sum(axis=1), np.zeros(3))
    large = terminal_rewards(
        np.array([[1e12, 0.0]]),
        cash_weight=0,
        cash_scale=10000,
        win_weight=1,
        cash_margin=CashMargin(),
    )
    assert 1.5 < large[0, 0] < 2
    assert large[0, 0] == -large[0, 1]


def test_reward_transition_preserves_recurrent_protocol_and_legacy_identity() -> None:
    original = Experiment(
        output_dir=Path("outputs/learning/test"),
        architecture="grounded-v2",
        gated=True,
        memory_turns=384,
        decision_interval=1,
    )
    before = protocol(original)
    assert "cash_margin" not in before
    updated = margin_protocol({"protocol": before}, CashMargin())
    assert protocol(updated) == {**before, "cash_margin": {"beta": 1.0, "cash_scale": 10000.0}}
    assert runtime_settings(updated).ppo.cash_margin == CashMargin()
    assert protocol(wdl_protocol({"protocol": protocol(updated)})) == before
    assert before == protocol(original)


def test_margin_diagnostics_check_every_turn_and_only_the_learned_frozen_seats() -> None:
    settings = runtime_settings(
        Experiment(output_dir=Path("outputs/learning/test"), cash_margin=CashMargin())
    )
    empty = torch.empty(0)
    rollout = Rollout(
        observations=empty,
        actions=empty,
        log_probabilities=empty,
        steps=empty,
        returns=torch.tensor([1.5, -1.5, -1.5, 0.0]).repeat(3),
        cash=np.array([[15000.0, 5000.0], [5000.0, 15000.0], [15000.0, 15000.0]]),
        timing={},
        weights=empty,
        opponents=("self_play", "script", "historical_self_play"),
    )
    assert margin_diagnostics(rollout, settings)["terminal_reward_max_error"] == 0
    rollout.returns[-1] = 0.5
    with pytest.raises(ValueError, match="collected returns"):
        margin_diagnostics(rollout, settings)
