from pathlib import Path

import orjson
import pytest

from kagg_revue.artifacts.io import digest
from kagg_revue.learning.league import upgrade as implementation


@pytest.mark.parametrize("field", ["checkpoint_sha256", "source_sha256", "protocol"])
def test_execution_upgrade_rejects_evidence_for_another_checkpoint_or_recipe(
    tmp_path: Path, monkeypatch, field
):
    state = {
        "source": "old",
        "run_id": "league",
        "completed_update": 93,
        "latest": "checkpoint.pt",
        "checkpoints": {"checkpoint.pt": "checkpoint"},
        "protocol": {"games": 192},
    }
    ledger = tmp_path / "league.json"
    ledger.write_bytes(orjson.dumps(state))
    report = {
        "passed": True,
        "run_id": "league",
        "completed_update": 93,
        "checkpoint_sha256": "checkpoint",
        "source_state_sha256": digest(ledger),
        "source_sha256": "new",
        "native_sha256": "native",
        "protocol": state["protocol"],
    }
    report[field] = "different"
    qualification = tmp_path / "qualification.json"
    qualification.write_bytes(orjson.dumps(report))
    monkeypatch.setattr(implementation, "stopped_state", lambda _: state)
    monkeypatch.setattr(
        implementation.artifacts,
        "source_identity",
        lambda: {"source_sha256": "new", "native_sha256": "native"},
    )
    options = implementation.Upgrade.model_construct(
        run=tmp_path, qualification=qualification, qualification_sha256=digest(qualification)
    )
    with pytest.raises(ValueError, match="unchanged recipe"):
        implementation.upgrade(options)
    assert orjson.loads(ledger.read_bytes()) == state
    assert not (tmp_path / "runtime-revisions").exists()
