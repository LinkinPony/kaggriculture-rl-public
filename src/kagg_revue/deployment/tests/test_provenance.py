"""Deployment authenticates transferred roots without relabelling their lineage."""

import hashlib
import json
from pathlib import Path

import pytest

from kagg_revue.deployment.provenance import load_run
from kagg_revue.learning.config import Experiment


@pytest.mark.parametrize("mutation", [None, "parent", "declaration", "root_kind"])
def test_transferred_root_requires_bound_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str | None
) -> None:
    """Reject changed parent bytes, changed declarations and false random-root labels."""
    monkeypatch.chdir(tmp_path)
    directory = Path("outputs/learning/transfer")
    parent = directory / "weight-transfer/parent.pt"
    parent.parent.mkdir(parents=True)
    parent.write_bytes(b"preserved parent")
    declared = {
        "run": "outputs/learning/parent",
        "checkpoint": "checkpoints/update-000004.pt",
        "sha256": hashlib.sha256(parent.read_bytes()).hexdigest(),
    }
    protocol = Experiment(output_dir=directory).model_dump(mode="json")
    protocol["initial_weights"] = declared
    state = {
        "schema": "checkpoint-root-league-v1",
        "initialization": "checkpoint",
        "input_weights": [dict(declared)],
        "protocol": protocol,
        "weight_transfer": {**declared, "artifact": "weight-transfer/parent.pt"},
    }
    if mutation == "parent":
        parent.write_bytes(b"changed parent")
    elif mutation == "declaration":
        state["input_weights"] = [{**declared, "sha256": "0" * 64}]
    elif mutation == "root_kind":
        state["schema"] = "random-root-league-v1"
        state["initialization"] = "random"
    (directory / "state.json").write_text(json.dumps(state))
    if mutation is None:
        config, loaded = load_run(directory)
        assert config.initial_weights is not None
        assert loaded["initialization"] == "checkpoint"
        assert loaded["input_weights"] == [declared]
    else:
        with pytest.raises(ValueError):
            load_run(directory)
