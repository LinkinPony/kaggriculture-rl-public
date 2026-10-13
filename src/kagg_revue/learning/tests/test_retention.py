"""Recovery metadata must remain valid when bulky old optimizer files are retired."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.learning.config import Evaluation, Experiment
from kagg_revue.learning.retention import remove_retired, retire


def test_retirement_preserves_dependencies_without_accumulating_milestones(tmp_path: Path) -> None:
    """Epoch actors remain selectable; superseded optimizer checkpoints are retired."""
    config = Experiment(
        output_dir=Path("outputs/learning/retention-test"),
        checkpoint_keep_recent=2,
        evaluation=Evaluation(interval=8),
        updates=20,
    )
    names = [
        "initial.pt",
        "anchors/seed-91001.pt",
        *(f"pretraining/shard-{i:06d}.pt" for i in range(1, 5)),
        *(f"checkpoints/update-{i:06d}.pt" for i in (4, 8, 12, 16, 17, 18, 19)),
    ]
    members = {}
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        members[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    original = members.copy()
    state: dict[str, Any] = {
        "members": members,
        "latest": "checkpoints/update-000019.pt",
        "pool": ["pretraining/shard-000004.pt", "checkpoints/update-000012.pt"],
        "rl_initial": "pretraining/shard-000004.pt",
        "pretraining_epoch_members": ["pretraining/shard-000001.pt", "pretraining/shard-000004.pt"],
        "sampling_history": [{"checkpoint_sha256": members["checkpoints/update-000004.pt"]}],
    }
    retired = retire(config, state)
    assert set(retired) == {
        "pretraining/shard-000002.pt",
        "pretraining/shard-000003.pt",
        "checkpoints/update-000004.pt",
        "checkpoints/update-000008.pt",
        "checkpoints/update-000016.pt",
        "checkpoints/update-000017.pt",
    }
    assert all((tmp_path / name).exists() for name in names)
    assert state["retired_members"] == {name: original[name] for name in retired}
    ledger = tmp_path / "state.json"
    ledger.write_text(json.dumps(state))
    remove_retired(tmp_path, retired)
    restored = json.loads(ledger.read_text())
    assert not any((tmp_path / name).exists() for name in retired)
    for name, expected in restored["members"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == expected
    assert retire(config, state) == []
    assert set(state["pretraining_epoch_members"]) <= state["members"].keys()


def test_retirement_rejects_paths_outside_the_run(tmp_path: Path) -> None:
    """A malformed checkpoint name must not remove a neighboring artifact."""
    run = tmp_path / "run"
    run.mkdir()
    sentinel = tmp_path / "neighbor.pt"
    sentinel.write_bytes(b"preserve")
    with pytest.raises(ValueError, match="escapes"):
        remove_retired(run, ["../neighbor.pt"])
    assert sentinel.read_bytes() == b"preserve"
