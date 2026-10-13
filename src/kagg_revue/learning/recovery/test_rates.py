"""Learning-rate revisions preserve prior evidence and reject stale ledger selections."""

import json
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.recovery import rates


@pytest.mark.parametrize("stale", [False, True])
def test_rate_revision_preserves_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stale: bool
) -> None:
    """Only a pinned stopped run can change its actor rate; old checkpoints remain intact."""
    monkeypatch.chdir(tmp_path)
    directory = Path("outputs/learning/rate-test")
    directory.mkdir(parents=True)
    checkpoint = directory / "checkpoint.pt"
    checkpoint.write_bytes(b"immutable optimizer and model fixture")
    config = Experiment(output_dir=directory, updates=8, actor_learning_rate=7.5e-6)
    state: dict[str, Any] = {
        "schema": "random-root-league-v1",
        "initialization": "random",
        "input_weights": [],
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
    monkeypatch.setattr(rates, "materialize", lambda *args: {})
    monkeypatch.setattr(artifacts, "member_path", lambda *args: checkpoint)
    monkeypatch.setattr(
        artifacts,
        "source_identity",
        lambda: {"source_sha256": "new-source", "native_sha256": "native-hash"},
    )
    monkeypatch.setattr(rates, "archive_source", lambda *args: None)
    change = rates.RateChange(
        run=directory,
        state_sha256="0" * 64 if stale else digest(directory / "state.json"),
        actor_learning_rate=2e-5,
    )
    before = (directory / "state.json").read_bytes()
    if stale:
        with pytest.raises(ValueError, match="pinned stopped ledger"):
            rates.change(change)
        assert (directory / "state.json").read_bytes() == before
        assert not (directory / "learning-rate-revisions").exists()
        return
    transition = rates.change(change)
    after = json.loads((directory / "state.json").read_text())
    assert {key for key in after if after[key] != state.get(key)} == {
        "protocol",
        "source",
        "source_directory",
        "learning_rate_history",
    }
    assert after["protocol"] == {**state["protocol"], "actor_learning_rate": 2e-5}
    assert transition["effective_from_update"] == 5
    previous = directory / transition["revision"] / "previous-state.json"
    assert previous.read_bytes() == before
    assert (directory / transition["preserved_checkpoint"]).read_bytes() == checkpoint.read_bytes()
