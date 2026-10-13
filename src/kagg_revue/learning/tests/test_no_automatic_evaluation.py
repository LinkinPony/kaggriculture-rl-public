"""Training must never invoke legacy baseline matches at any budget boundary."""

from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import numpy as np
import pytest
import torch

from kagg_revue.learning import state as artifacts
from kagg_revue.learning import train
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Evaluation, Experiment, Population


@pytest.mark.parametrize("completed", [0, 1, 2])
def test_training_skips_initial_periodic_and_final_evaluation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, completed: int
) -> None:
    """Exercise fresh, resumed and final boundaries without spending evaluation games."""
    monkeypatch.chdir(tmp_path)
    directory = Path("outputs/learning/no-evaluation")
    directory.mkdir(parents=True)
    config = Experiment(
        output_dir=directory,
        device="cpu",
        updates=2,
        games=2,
        checkpoint_interval=1,
        evaluation=Evaluation(interval=1),
        population=Population(fraction=0.0),
        compile=False,
    )
    settings = runtime_settings(config)
    state: dict[str, Any] = {
        "completed_update": completed,
        "latest": "initial.pt",
        "members": {"initial.pt": "identity"},
        "pool": ["initial.pt"],
        "records": [{"update": i, "physical_games": 2} for i in range(1, completed + 1)],
    }
    payload = {"update": completed, "critic": {}, "actor_optimizer": {}, "critic_optimizer": {}}
    actor = SimpleNamespace(layout=None)
    monkeypatch.setattr(artifacts, "load_member", lambda *args: (actor, payload))
    monkeypatch.setattr(train, "create_bank", lambda *args: None)
    critic = Mock()
    critic.to.return_value = critic
    monkeypatch.setattr(train, "PrefixCritic", lambda *args: critic)
    learner = Mock()
    learner.update.return_value = {}
    monkeypatch.setattr(train, "Learner", lambda *args: learner)
    monkeypatch.setattr(train, "restore_rng", lambda *args, **kwargs: None)
    collection = Mock()
    collection.runtimes = {}
    collection.resolve.return_value = (settings, None, None, None, 0)
    monkeypatch.setattr(train, "MatchedCollection", lambda *args: collection)
    rollout = SimpleNamespace(
        cash=np.array([[3.0, 1.0], [1.0, 3.0]]),
        returns=torch.tensor([1.0, -1.0]),
        opponents=["self_play", "self_play"],
        timing={},
        land={},
    )
    monkeypatch.setattr(train, "collect_update", lambda *args: (rollout, {}))
    monkeypatch.setattr(train, "combine", lambda *args: {})
    monkeypatch.setattr(train, "publish", lambda *args, **kwargs: None)
    monkeypatch.setattr(torch.cuda, "reset_peak_memory_stats", lambda *args: None)
    monkeypatch.setattr(torch.cuda, "max_memory_allocated", lambda *args: 0)
    forbidden = Mock(side_effect=AssertionError("automatic evaluation must not run"))
    monkeypatch.setattr(train, "evaluate", forbidden, raising=False)
    monkeypatch.setattr(train, "confirm", forbidden, raising=False)
    writer = Mock()
    writer.asynchronous = False

    def record(update: int, metrics: dict[str, Any]) -> None:
        state["records"].append(metrics)
        state["completed_update"] = update

    writer.record.side_effect = record
    monkeypatch.setattr(train, "CheckpointWriter", lambda *args: nullcontext(writer))
    train._train(config, settings, state, train.StopRequest())
    assert state["completed_update"] == 2
    assert learner.update.call_count == 2 - completed
    writer.flush.assert_called_once()
    forbidden.assert_not_called()
