"""Quadrant telemetry distinguishes ownership, transient production and empty facilities."""

from dataclasses import replace
from pathlib import Path

import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.quadrants import combine, measure
from kagg_revue.learning.config import Experiment
from kagg_revue.monitor.metrics import _step_and_metrics
from kagg_revue.policy.contracts import ContractLayout


def test_full_trajectory_and_terminal_settlement() -> None:
    """Count late land, vanished crops and unused purchases with raw-count aggregation."""
    config = Experiment(output_dir=Path("outputs/learning/test-quadrants"), decision_interval=1)
    layout = ContractLayout.resolve(runtime_settings(config))
    layout = replace(layout, observation=replace(layout.observation, turns=3))
    frames = torch.zeros(4, 3, layout.observation.features)
    board = frames[..., :2900].reshape(4, 3, 29, 10, 10)
    board[..., 1, 5:, 5:] = 1  # SE locked until explicitly purchased.
    board[1:, 0, 1, 5:, 5:] = 0
    board[1, 0, 3, 5, 5] = 1  # Transient crop: terminal-only monitoring would miss it.
    board[3, 1:, 1, 5:, 5:] = 0  # Both remaining seats buy after the last action.
    board[3, 1, 4, 5, 5] = 1  # Empty coop is developed, but not productive.
    board[3, 2, 5, 5, 5] = 1
    board[3, 2, 17, 5, 5] = 1  # Stocked pasture is productive.
    before = torch.get_rng_state().clone()
    one = measure(frames[:3, :1], frames[3, :1], layout)
    two = measure(frames[:3, 1:], frames[3, 1:], layout)
    result = combine([one, two])
    assert torch.equal(torch.get_rng_state(), before)
    assert result == combine([measure(frames[:3], frames[3], layout)])
    assert result["trajectories"] == 3
    se = result["quadrants"]["SE"]
    assert se["unlocked"] == 3 and se["productive"] == 2 and se["unused"] == 1
    assert se["developed_rate"] == 1 and se["productive_rate"] == 2 / 3
    assert se["mean_unlock_step"] == 7 / 3
    assert se["mean_peak_productive_tiles"] == 2 / 3
    assert measure(frames[:2], frames[3], layout) == {}
    assert combine([one, {}]) == {}
    _, metrics = _step_and_metrics({"update": 1, "land": result})
    assert metrics["rl/land/quadrants/SE/productive_rate"] == 2 / 3
    assert metrics["rl/land/trajectories"] == 3
