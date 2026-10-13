"""Source-only recovery must preserve the authenticated optimizer and protocol ledger."""

import json
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.recovery import repair as module
from kagg_revue.learning.state import protocol
from kagg_revue.opponents import artifacts as script_artifacts


@pytest.mark.parametrize("mismatch", [False, True])
@pytest.mark.parametrize("script_change", [False, True])
@pytest.mark.parametrize("transferred", [False, True])
def test_source_repair_preserves_state_and_rejects_protocol_changes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mismatch: bool,
    script_change: bool,
    transferred: bool,
) -> None:
    """Only a matching qualification may change source identity and append provenance."""
    monkeypatch.chdir(tmp_path)
    directory = Path("outputs/learning/repair-test")
    directory.mkdir(parents=True)
    state: dict[str, Any] = {
        "schema": "random-root-league-v1",
        "initialization": "random",
        "input_weights": [],
        "run_id": "fixture",
        "protocol": protocol(Experiment(output_dir=directory, updates=8)),
        "completed_update": 4,
        "latest": "checkpoints/update-000004.pt",
        "pool": ["checkpoints/update-000004.pt"],
        "members": {"checkpoints/update-000004.pt": "checkpoint-hash"},
        "native": "native-hash",
        "source": "old-source",
        "records": [{"update": 4}],
        "pfsp": {"last_update": 4},
    }
    previous_scripts = {
        "backend": "native-cpp",
        "files": {"src/kagg_revue/native/_revue_native.so": "old-binary"},
    }
    scripts = {
        "backend": "native-cpp",
        "files": {"src/kagg_revue/native/_revue_native.so": "new-binary"},
    }
    if script_change:
        state["protocol"].update(architecture="grounded-v2", decision_interval=1)
        state["protocol"]["script_population"] = {
            "manifest": "data/external/scripts/manifest.json",
            "sha256": "a" * 64,
            "agents": ["ahmed_v45"],
            "fraction": 0.25,
        }
        state["script_runtime"] = {**previous_scripts, "directory": "script-runtime"}
        monkeypatch.setattr(script_artifacts, "identity", lambda *args: scripts)
        monkeypatch.setattr(
            script_artifacts,
            "archive",
            lambda *args: {**scripts, "directory": "script-runtime"},
        )
    if transferred:
        parent = directory / "weight-transfer/parent.pt"
        parent.parent.mkdir()
        parent.write_bytes(b"authenticated-parent")
        source = {
            "run": "outputs/learning/parent",
            "checkpoint": "initial.pt",
            "sha256": digest(parent),
        }
        state.update(schema="checkpoint-root-league-v1", initialization="checkpoint")
        state["protocol"]["initial_weights"] = source
        state["input_weights"] = [source]
        state["weight_transfer"] = {**source, "artifact": "weight-transfer/parent.pt"}
    write_json(directory / "state.json", state)
    write_json(directory / "run-status.json", {"status": "failed", "pid": 1073741824})
    qualified = {
        "passed": True,
        "run_id": "fixture",
        "completed_update": 4,
        "checkpoint_sha256": "checkpoint-hash",
        "previous_source": "old-source",
        "source_sha256": "new-source",
        "protocol": {
            **state["protocol"],
            **({"seed": 12345} if mismatch and not script_change else {}),
        },
    }
    if script_change:
        qualified.update(previous_script_runtime=previous_scripts, script_runtime=scripts)
        if mismatch:
            qualified["script_runtime"] = previous_scripts
    report = directory / "qualification.json"
    write_json(report, qualified)
    monkeypatch.setattr(module, "materialize", lambda *args: {})
    monkeypatch.setattr(artifacts, "member_path", lambda *args: directory)
    monkeypatch.setattr(
        artifacts,
        "source_identity",
        lambda: {"source_sha256": "new-source", "native_sha256": "native-hash"},
    )
    monkeypatch.setattr(module, "archive_source", lambda *args: None)
    config = module.Repair(run=directory, qualification=report, qualification_sha256=digest(report))
    before = (directory / "state.json").read_bytes()
    if mismatch:
        with pytest.raises(ValueError, match="does not bind"):
            module.repair(config)
        assert (directory / "state.json").read_bytes() == before
        assert not (directory / "source-revisions").exists()
    else:
        module.repair(config)
        after = json.loads((directory / "state.json").read_text())
        assert {key for key in after if after[key] != state.get(key)} == {
            "source",
            "source_directory",
            "repair_history",
        } | ({"script_runtime"} if script_change else set())
        if script_change:
            assert after["script_runtime"] == {
                **scripts,
                "directory": "source-revisions/0001/script-runtime",
            }
        previous = directory / after["source_directory"] / "previous-state.json"
        assert json.loads(previous.read_text()) == state
