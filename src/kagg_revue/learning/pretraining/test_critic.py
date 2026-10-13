"""Verify independent critic ancestry, preserved tensors and donor-free recovery."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest
import torch

from kagg_revue.artifacts.io import digest
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.learning.pretraining.config import InitialWeights
from kagg_revue.learning.pretraining.critic import archive
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.contracts import ContractLayout


def test_independent_critic_transfer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the actor independent, preserve critic parameters and reject corrupted recovery."""
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
        output_dir=Path("outputs/learning/donor"),
        device="cpu",
        width=16,
        depth=1,
        critic_width=16,
        critic_depth=1,
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
    checkpoint = parent_config.output_dir / "initial.pt"
    payload = torch.load(checkpoint, weights_only=False)
    critic = PrefixCritic(ContractLayout.resolve(settings))
    payload.update(critic=critic.state_dict(), update=139, critic_optimizer={"sentinel": 1})
    torch.save(payload, checkpoint)
    parent["members"]["initial.pt"] = digest(checkpoint)
    artifacts.write_ledger(parent_config.output_dir, parent)
    child = parent_config.model_copy(
        update={
            "output_dir": Path("outputs/learning/child"),
            "seed": 999,
            "initial_critic": InitialWeights(
                run=parent_config.output_dir, checkpoint="initial.pt", sha256=digest(checkpoint)
            ),
        }
    )
    child = Experiment.model_validate(child.model_dump())
    state = artifacts.create(child, runtime_settings(child))
    root = torch.load(child.output_dir / "initial.pt", weights_only=False)
    assert all(torch.equal(value, root["critic"][key]) for key, value in payload["critic"].items())
    assert any(
        not torch.equal(value, root["model"][key]) for key, value in payload["model"].items()
    )
    assert "critic_optimizer" not in root
    assert state["critic_transfer"]["checkpoint_update"] == 139
    assert "initial_critic" not in artifacts.protocol(parent_config)
    parent_config.output_dir.rename(parent_config.output_dir.with_name("moved"))
    assert artifacts.restore(child)["run_id"] == state["run_id"]
    (child.output_dir / "critic-transfer/parent.pt").write_bytes(b"changed")
    with pytest.raises(ValueError, match="preserved initial critic"):
        artifacts.restore(child)


def test_missing_critic_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An actor-only source must never silently create a random critic."""
    monkeypatch.chdir(tmp_path)
    parent = Path("outputs/learning/donor")
    parent.mkdir(parents=True)
    checkpoint = parent / "initial.pt"
    config = Experiment(output_dir=Path("outputs/learning/child"))
    layout = ContractLayout.resolve(runtime_settings(config))
    torch.save({"layout": asdict(layout), "lineage": {"run_id": "donor"}}, checkpoint)
    sha256 = digest(checkpoint)
    (parent / "state.json").write_text(
        json.dumps(
            {
                "run_id": "donor",
                "members": {"initial.pt": sha256},
            }
        )
    )
    config = config.model_copy(
        update={
            "initial_critic": InitialWeights(
                run=parent,
                checkpoint="initial.pt",
                sha256=sha256,
            )
        }
    )
    with pytest.raises(ValueError, match="initial critic has incompatible"):
        archive(config, {}, layout)
