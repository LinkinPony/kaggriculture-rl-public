"""Live recovery, atomic compaction and stable identities under bounded retention."""

import copy
import json
import os
from pathlib import Path
from typing import Any

import pytest
import torch

from kagg_revue.artifacts.io import write_json
from kagg_revue.artifacts.serialization import save
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.storage import cleanup
from kagg_revue.learning.storage.artifacts import compact, import_member, resolve
from kagg_revue.learning.storage.publication import publish
from kagg_revue.learning.storage.roles import full_members


def _fixture(
    directory: Path, updates: tuple[int, ...] = (1, 2, 3, 4)
) -> tuple[Experiment, dict[str, Any]]:
    config = Experiment(
        output_dir=Path("outputs/learning/storage-test"),
        checkpoint_keep_recent=2,
    ).model_copy(update={"output_dir": directory})
    names = [
        "initial.pt",
        *(f"checkpoints/update-{i:06d}.pt" for i in updates),
    ]
    state: dict[str, Any] = {
        "schema": "random-root-league-v1",
        "run_id": "test",
        "source": "test-source",
        "native": "test-native",
        "initialization": "random",
        "input_weights": [],
        "protocol": artifacts.protocol(config),
        "latest": names[-1],
        "completed_update": updates[-1],
        "pool": [names[0], names[1]],
        "members": {},
    }
    for update, name in zip((0, *updates), names, strict=True):
        payload = {
            "model": {"weight": torch.arange(8).reshape(2, 4)},
            "layout": {},
            "settings": {},
            "update": update,
            "lineage": {"run_id": "test"},
            "actor_optimizer": {"state": torch.ones(32)},
            "critic_optimizer": {"state": torch.zeros(32)},
            "critic": {"weight": torch.ones(4)},
            "rng": {"cpu": torch.get_rng_state()},
        }
        state["members"][name] = save(payload, directory / name)
    for seed in config.evaluation.anchor_seeds:
        name = f"anchors/seed-{seed}.pt"
        state["members"][name] = save({"model": {}}, directory / name)
    write_json(directory / "state.json", state)
    return config, state


def test_enabling_milestones_does_not_promote_compacted_history(tmp_path: Path) -> None:
    """A policy-only historical U200 stays usable without claiming to contain Adam."""
    config, state = _fixture(tmp_path, (200, 401, 402, 403))
    publish(config.model_copy(update={"checkpoint_keep_interval": None}), state)
    name = "checkpoints/update-000200.pt"
    path = resolve(tmp_path, state, name)
    assert path != tmp_path / name
    publish(config, state)
    assert name not in full_members(config, state)
    assert resolve(tmp_path, state, name) == path
    assert "actor_optimizer" not in torch.load(path, weights_only=False)
    assert full_members(config, state) == {
        "checkpoints/update-000402.pt",
        "checkpoints/update-000403.pt",
    }


def test_compaction_preserves_policy_identity_and_recent_optimizers(tmp_path: Path) -> None:
    """Only current recoveries retain Adam; opponent tensors and hashes remain identical."""
    config, state = _fixture(tmp_path)
    original = copy.deepcopy(state)
    rng = torch.get_rng_state().clone()
    publish(config, state)
    assert (
        state["members"]["checkpoints/update-000001.pt"]
        == original["members"]["checkpoints/update-000001.pt"]
    )
    assert not (tmp_path / "checkpoints/update-000001.pt").exists()
    assert not (tmp_path / "checkpoints/update-000002.pt").exists()
    assert "checkpoints/update-000002.pt" in state["retired_members"]
    for update in (3, 4):
        payload = torch.load(tmp_path / f"checkpoints/update-{update:06d}.pt", weights_only=False)
        assert {"actor_optimizer", "critic_optimizer", "rng"} <= payload.keys()
    path = resolve(tmp_path, state, "checkpoints/update-000001.pt")
    actor = torch.load(path, weights_only=False)
    assert not {"actor_optimizer", "critic_optimizer", "critic", "rng"} & actor.keys()
    assert torch.equal(actor["model"]["weight"], torch.arange(8).reshape(2, 4))
    assert torch.equal(rng, torch.get_rng_state())
    assert json.loads((tmp_path / "state.json").read_text()) == state
    publish(config, state)
    assert resolve(tmp_path, state, "checkpoints/update-000001.pt") == path


def test_publish_failure_keeps_original_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An interrupted ledger commit leaves the old checkpoint ledger fully recoverable."""
    config, state = _fixture(tmp_path)
    original = copy.deepcopy(state)

    def fail(directory: Path, ledger: dict[str, Any]) -> None:
        raise OSError("simulated ledger failure")

    monkeypatch.setattr(artifacts, "write_ledger", fail)
    with pytest.raises(RuntimeError, match="simulated ledger failure"):
        publish(config, state)
    assert json.loads((tmp_path / "state.json").read_text()) == original
    for name in original["members"]:
        resolve(tmp_path, original, name)


def test_restore_ignores_unused_history_but_authenticates_live_policies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing historical bytes are harmless; missing/corrupt PFSP bytes still fail."""
    config, state = _fixture(tmp_path)
    monkeypatch.setattr(
        artifacts,
        "source_identity",
        lambda: {"source_sha256": "test-source", "native_sha256": "test-native"},
    )
    (tmp_path / "checkpoints/update-000002.pt").unlink()
    restored = artifacts.restore(config)
    assert restored["latest"] == state["latest"]
    compact(tmp_path, state, {"checkpoints/update-000001.pt"})
    (tmp_path / "checkpoints/update-000001.pt").unlink()
    write_json(tmp_path / "state.json", state)
    artifacts.restore(config)
    path = resolve(tmp_path, state, "checkpoints/update-000001.pt")
    path.write_bytes(path.read_bytes() + b"corrupt")
    with pytest.raises(ValueError, match="authenticated"):
        artifacts.restore(config)


def test_compact_import_survives_source_removal(tmp_path: Path) -> None:
    """Imported history contains no optimizer and does not depend on source files."""
    source, destination = tmp_path / "source", tmp_path / "destination"
    _, state = _fixture(source)
    name = "checkpoints/update-000001.pt"
    compact(source, state, {name})
    target: dict[str, Any] = {"members": {}}
    path = resolve(source, state, name)
    import_member(destination, target, name, path, state["members"][name])
    path.unlink()
    payload = torch.load(resolve(destination, target, name), weights_only=False)
    assert target["members"][name] == state["members"][name]
    assert "actor_optimizer" not in payload


def test_cleanup_preserves_live_links_and_noncheckpoint_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An exact cleanup removes abandoned weight links while preserving live bytes and logs."""
    monkeypatch.chdir(tmp_path)
    run = Path("outputs/learning/live")
    config, state = _fixture(run)
    publish(config, state)
    state["storage_history"] = [{"revision": "storage-revisions/0001"}]
    write_json(run / "state.json", state)
    write_json(
        run / "storage-revisions/0001/verification.json",
        {"passed": True, "completed_update": 4, "source_sha256": state["source"]},
    )
    obsolete = Path("outputs/learning/obsolete")
    obsolete.mkdir(parents=True)
    os.link(run / state["latest"], obsolete / "shared.pt")
    (obsolete / "other.pt").write_bytes(b"obsolete optimizer")
    (obsolete / "metrics.json").write_text("{}")
    report = Path("outputs/analysis/cleanup")
    planned = cleanup.plan((run,), report)
    assert {row["path"] for row in planned["candidates"]} == {
        str(obsolete / "shared.pt"),
        str(obsolete / "other.pt"),
    }
    result = cleanup.apply(planned, report)
    assert result["deleted_files"] == 2
    resolve(run, state, state["latest"])
    assert (obsolete / "metrics.json").read_text() == "{}"
