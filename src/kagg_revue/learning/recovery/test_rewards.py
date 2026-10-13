"""Reward revisions support authenticated transferred roots without losing PPO state."""

import json
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.optimization.settings import CashMargin
from kagg_revue.learning.recovery import rewards


@pytest.mark.parametrize("root", ["random", "checkpoint", "corrupt-parent"])
def test_reward_revision_preserves_authenticated_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, root: str
) -> None:
    """Continue valid roots unchanged and reject altered transferred parent bytes."""
    monkeypatch.chdir(tmp_path)
    directory = Path("outputs/learning/reward-test")
    (directory / "weight-transfer").mkdir(parents=True)
    parent = directory / "weight-transfer/parent.pt"
    parent.write_bytes(b"authenticated BC parent")
    transferred = root != "random"
    source = {
        "run": "outputs/learning/parent",
        "checkpoint": "pretraining/shard-000001.pt",
        "sha256": digest(parent),
    }
    config = Experiment.model_validate(
        {"output_dir": directory, "updates": 8, "initial_weights": source if transferred else None}
    )
    state: dict[str, Any] = {
        "schema": "checkpoint-root-league-v1" if transferred else "random-root-league-v1",
        "initialization": "checkpoint" if transferred else "random",
        "input_weights": [source] if transferred else [],
        "weight_transfer": {**source, "artifact": "weight-transfer/parent.pt"},
        "run_id": "fixture",
        "protocol": artifacts.protocol(config),
        "completed_update": 4,
        "latest": "checkpoints/update-000004.pt",
        "pool": ["initial.pt"],
        "members": {"initial.pt": "initial", "checkpoints/update-000004.pt": "checkpoint"},
        "native": "native-hash",
        "source": "old-source",
        "records": [{"update": 4}],
        "pfsp": {"last_update": 4},
        "external_opponents": {},
    }
    write_json(directory / "state.json", state)
    write_json(directory / "run-status.json", {"status": "stopped", "pid": 1073741824})
    updated = artifacts.protocol(rewards.margin_protocol(state, CashMargin()))
    report = directory / "qualification.json"
    write_json(
        report,
        {
            "passed": True,
            "run_id": "fixture",
            "completed_update": 4,
            "checkpoint_sha256": "checkpoint",
            "source_state_sha256": digest(directory / "state.json"),
            "source_sha256": "new-source",
            "native_sha256": "native-hash",
            "script_runtime": None,
            "protocol": updated,
            "cash_margin_returns_verified": True,
            "full_optimizer_rng_and_parent_chain": True,
            "archived_source_recovery": True,
            "source_run_unchanged": True,
        },
    )
    monkeypatch.setattr(rewards, "materialize", lambda *args: {})
    monkeypatch.setattr(artifacts, "member_path", lambda *args: parent)
    monkeypatch.setattr(
        artifacts,
        "source_identity",
        lambda: {"source_sha256": "new-source", "native_sha256": "native-hash"},
    )
    monkeypatch.setattr(rewards, "archive_source", lambda *args: None)
    change = rewards.RewardChange(
        run=directory,
        cash_margin=CashMargin(),
        qualification=report,
        qualification_sha256=digest(report),
    )
    if root == "corrupt-parent":
        parent.write_bytes(b"corrupted parent")
        with pytest.raises(ValueError, match="preserved initial checkpoint differs"):
            rewards.change(change)
        assert json.loads((directory / "state.json").read_text()) == state
        assert not (directory / "reward-revisions").exists()
        return
    rewards.change(change)
    after = json.loads((directory / "state.json").read_text())
    assert {key for key in after if after[key] != state.get(key)} == {
        "protocol",
        "source",
        "source_directory",
        "reward_history",
    }
    assert after["protocol"] == updated
    assert after["reward_history"][0]["effective_from_update"] == 5
    previous = directory / "reward-revisions/0001/previous-state.json"
    assert json.loads(previous.read_text()) == state
