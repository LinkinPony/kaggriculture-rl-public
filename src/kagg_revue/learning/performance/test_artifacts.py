"""Keep short qualification branches verifiable under production retention limits."""

import json
from pathlib import Path

import pytest

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as learning_state
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.performance import artifacts
from kagg_revue.learning.retention import retire
from kagg_revue.learning.state import protocol


@pytest.mark.parametrize("keep", [2, None])
def test_qualification_retains_starting_optimizer_and_checkpoint_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, keep: int | None
) -> None:
    """Four saves must not retire the starting checkpoint used for verification."""
    monkeypatch.chdir(tmp_path)
    source = Path("outputs/learning/source")
    destination = Path("outputs/learning/qualification")
    original = Experiment(output_dir=source, checkpoint_keep_recent=keep)
    first = "checkpoints/update-000004.pt"
    checkpoint = source / first
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"immutable optimizer checkpoint")
    (source / "native.so").write_bytes(b"native fixture")
    write_json(
        source / "state.json",
        {
            "protocol": protocol(original),
            "members": {first: digest(checkpoint)},
            "latest": first,
            "completed_update": 4,
            "native_artifact": "native.so",
            "pool": [],
        },
    )
    before = (source / "state.json").read_bytes()
    monkeypatch.setattr(learning_state, "source_identity", lambda: {"source_sha256": "test"})
    monkeypatch.setattr(artifacts, "archive_source", lambda directory, identity: None)
    config = artifacts.qualification_copy(
        source, destination, Execution(devices=("cuda:0", "cuda:1")), 4
    )
    state = json.loads((destination / "state.json").read_text())
    for update in range(5, 9):
        name = f"checkpoints/update-{update:06d}.pt"
        state["members"][name] = f"digest-{update}"
        state["latest"] = name
        assert retire(config, state) == []
    assert first in state["members"]
    assert (destination / first).read_bytes() == checkpoint.read_bytes()
    assert (source / "state.json").read_bytes() == before
