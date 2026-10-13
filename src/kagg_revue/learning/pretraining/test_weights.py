"""Check transferred parameters, honest ancestry and self-contained BC recovery."""

import json
from pathlib import Path

import pytest
import torch

from kagg_revue.artifacts.io import digest
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.pretraining.config import Demonstrations, InitialWeights
from kagg_revue.learning.storage.artifacts import compact
from kagg_revue.native import _revue_core as native


@pytest.mark.parametrize("pretraining_only", [True, False])
@pytest.mark.parametrize("compacted", [True, False])
def test_weight_transfer_preserves_actor_and_recovers_without_parent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pretraining_only: bool, compacted: bool
) -> None:
    """A distinct child seed must still load every parent tensor and reject tampering."""
    monkeypatch.chdir(tmp_path)
    torch.set_num_threads(1)
    monkeypatch.setattr(
        artifacts,
        "source_identity",
        lambda: {
            "files": {},
            "source_sha256": "test-source",
            "native_sha256": digest(Path(native.__file__)),
        },
    )
    parent_config = Experiment(
        output_dir=Path("outputs/learning/parent"),
        device="cpu",
        width=16,
        depth=1,
        critic_depth=1,
        critic_width=16,
        unit_limit=3,
        architecture="grounded-v1",
        decision_interval=1,
        compile=False,
        precision="fp32",
        environment={
            "boardSize": 4,
            "episodeSteps": 13,
            "turnsPerDay": 6,
            "maxMarketOrdersPerTurn": 2,
        },
    )
    settings = runtime_settings(parent_config)
    parent = artifacts.create(parent_config, settings)
    checkpoint = "initial.pt"
    original = torch.load(parent_config.output_dir / checkpoint, weights_only=False)
    if compacted:
        checkpoint = "pretraining/shard-000004.pt"
        path = parent_config.output_dir / checkpoint
        path.parent.mkdir()
        torch.save({**original, "optimizer": {"state": {}}}, path)
        parent["members"][checkpoint] = digest(path)
        assert compact(parent_config.output_dir, parent, {checkpoint}) == [checkpoint]
        artifacts.write_ledger(parent_config.output_dir, parent)
        path.unlink()
    declared = InitialWeights(
        run=parent_config.output_dir,
        checkpoint=checkpoint,
        sha256=parent["members"][checkpoint],
    )
    child = parent_config.model_copy(
        update={
            "output_dir": Path("outputs/learning/child"),
            "seed": 999,
            "pretraining_only": pretraining_only,
            "initial_weights": declared,
            "demonstrations": Demonstrations(
                manifest=Path("outputs/datasets/example/manifest.json"), sha256="a" * 64
            )
            if pretraining_only
            else None,
        }
    )
    child = Experiment.model_validate(child.model_dump())
    state = artifacts.create(child, settings)
    root = torch.load(child.output_dir / "initial.pt", weights_only=False)
    assert state["run_id"] != parent["run_id"]
    assert state["initialization"] == "checkpoint"
    assert root["lineage"]["parent_sha256"] == declared.sha256
    assert state["weight_transfer"]["artifact_sha256"] == digest(
        child.output_dir / "weight-transfer/parent.pt"
    )
    assert (state["weight_transfer"]["parent_checkpoint_storage"] is not None) == compacted
    assert "optimizer" not in root and "rng" not in root
    assert all(torch.equal(value, original["model"][key]) for key, value in root["model"].items())
    parent_config.output_dir.rename(parent_config.output_dir.with_name("moved-parent"))
    assert artifacts.restore(child)["run_id"] == state["run_id"]
    (child.output_dir / "weight-transfer/parent.pt").write_bytes(b"changed")
    with pytest.raises(ValueError, match="preserved initial checkpoint"):
        artifacts.restore(child)
    ledger = json.loads((child.output_dir / "state.json").read_text())
    ledger["initialization"] = "random"
    (child.output_dir / "state.json").write_text(json.dumps(ledger))
    with pytest.raises(ValueError, match="policy root"):
        artifacts.restore(child)
