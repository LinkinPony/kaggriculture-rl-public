"""Periodic persistence retains pool boundaries and flushes graceful stops."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment


def test_periodic_commit_preserves_pending_metrics_and_graceful_stop(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = Experiment(output_dir=Path("outputs/learning/test"), checkpoint_interval=4)
    config.output_dir.mkdir(parents=True)
    settings = runtime_settings(config)
    state = {
        "completed_update": 0,
        "records": [],
        "members": {"initial.pt": "root"},
        "latest": "initial.pt",
        "pool": ["initial.pt"],
        "run_id": "test",
    }
    saved = []

    def save(path, *args, **kwargs):
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(str(kwargs["update"]).encode())
        saved.append(kwargs)

    monkeypatch.setattr(artifacts, "save_policy", save)
    monkeypatch.setattr(torch.cuda, "get_rng_state", lambda device: torch.get_rng_state())
    part = SimpleNamespace(state_dict=lambda: {})
    learner = SimpleNamespace(
        policy=None, critic=part, actor_optimizer=part, critic_optimizer=part, device="cpu"
    )
    for update in range(1, 4):
        artifacts.checkpoint(config, settings, state, learner, update, {"update": update})
    assert not saved and state["completed_update"] == 0
    artifacts.checkpoint(config, settings, state, learner, 4, {"update": 4})
    assert [p["update"] for p in saved] == [4]
    assert state["pool"] == ["initial.pt", "checkpoints/update-000004.pt"]
    artifacts.checkpoint(config, settings, state, learner, 5, {"update": 5})
    assert json.loads((config.output_dir / "state.json").read_text())["completed_update"] == 4
    artifacts.commit_pending(config, settings, state, learner)
    artifacts.commit_pending(config, settings, state, learner)
    assert [p["update"] for p in saved] == [4, 5]
    assert saved[-1]["lineage"]["parent_sha256"] == state["members"]["checkpoints/update-000004.pt"]
    log = config.output_dir / "metrics.jsonl"
    assert [json.loads(line)["update"] for line in log.read_text().splitlines()] == [1, 2, 3, 4, 5]
    log.write_text(log.read_text() + '{"update": 6')
    artifacts.publish_metrics(config, state)
    assert [json.loads(line)["update"] for line in log.read_text().splitlines()] == [1, 2, 3, 4, 5]
    with pytest.raises(ValueError, match="must divide"):
        Experiment(output_dir=config.output_dir, checkpoint_interval=3)
