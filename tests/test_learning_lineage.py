import subprocess
import sys
from pathlib import Path

import pytest
import torch
from pydantic import ValidationError

from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.production.contracts import ContractLayout


def test_fresh_roots_do_not_load_weights_and_restore_rejects_external_or_changed_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        artifacts,
        "source_identity",
        lambda: {
            "files": {},
            "source_sha256": "test-source",
            "native_sha256": artifacts.digest(Path(artifacts.native.__file__)),
        },
    )
    config = Experiment(
        output_dir=Path("outputs/learning/test"),
        device="cpu",
        games=4,
        width=16,
        depth=1,
        critic_depth=1,
        critic_width=16,
        unit_limit=2,
        decision_interval=2,
        environment={
            "boardSize": 4,
            "episodeSteps": 9,
            "turnsPerDay": 3,
            "maxMarketOrdersPerTurn": 2,
        },
    )
    settings = runtime_settings(config)
    assert settings.ppo.bc_weight == settings.ppo.cash_weight == 0
    assert settings.ppo.script_opponents == ()
    assert not {"bc", "checkpoint", "mode", "opponents"} & settings.model_dump().keys()
    assert not settings.model.time_prior
    layout = ContractLayout.resolve(settings)
    before = torch.get_rng_state().clone()
    first = random_policy(layout, config.seed, config.exploration)
    same = random_policy(layout, config.seed, config.exploration)
    different = random_policy(layout, config.seed + 1, config.exploration)
    assert torch.equal(before, torch.get_rng_state())
    assert all(torch.equal(v, same.state_dict()[k]) for k, v in first.state_dict().items())
    assert any(not torch.equal(v, different.state_dict()[k]) for k, v in first.state_dict().items())
    assert not torch.equal(first.market_heads[0][-1].weight, different.market_heads[0][-1].weight)
    original_load = torch.load

    def forbid_load(*args, **kwargs):
        raise AssertionError("random initialization must not deserialize any weights")

    monkeypatch.setattr(torch, "load", forbid_load)
    state = artifacts.create(config, settings)
    assert state["input_weights"] == []
    assert state["initialization"] == "random"
    assert artifacts.digest(config.output_dir / state["native_artifact"]) == state["native"]
    assert len(set(state["members"].values())) == 3
    assert not Path("data").exists()
    artifacts.restore(config.model_copy(update={"resume": True}))
    with pytest.raises(ValueError, match="authenticated"):
        artifacts.load_member(config, state, "../legacy.pt", torch.device("cpu"))
    monkeypatch.setattr(torch, "load", original_load)
    actor, payload = artifacts.load_member(config, state, "initial.pt", torch.device("cpu"))
    assert payload["lineage"]["kind"] == "random"
    assert "bc" not in payload["settings"]
    assert "prior" not in actor.state_dict()
    with pytest.raises(FileExistsError):
        artifacts.create(config, settings)
    changed = config.model_copy(update={"actor_learning_rate": config.actor_learning_rate * 2})
    with pytest.raises(ValueError, match="protocol"):
        artifacts.restore(changed)
    path = config.output_dir / "initial.pt"
    path.write_bytes(path.read_bytes() + b"modified")
    monkeypatch.setattr(torch, "load", forbid_load)
    with pytest.raises(ValueError, match="authenticated"):
        artifacts.load_member(config, state, "initial.pt", torch.device("cpu"))


def test_protocol_rejects_weight_inputs_and_cross_role_seed_leakage() -> None:
    base = {"output_dir": "outputs/learning/test"}
    for key in ("checkpoint", "teacher", "bc", "opponents"):
        with pytest.raises(ValidationError, match="Extra inputs"):
            Experiment.model_validate({**base, key: "legacy"})
    with pytest.raises(ValidationError, match="disjoint"):
        Experiment.model_validate({**base, "train_seed": 710000000})
    with pytest.raises(ValidationError, match="independent initialization"):
        Experiment.model_validate({**base, "seed": 91001})
    # Seed zero belongs to no fictitious BC dataset in a fresh RL experiment.
    settings = runtime_settings(Experiment.model_validate({**base, "train_seed": 0}))
    assert settings.ppo.seed_start == 0


def test_current_training_imports_no_legacy_workflow_or_versioned_teacher() -> None:
    source = Path(__file__).resolve().parents[1] / "src"
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, sys.argv[1])
import kagg_revue.learning.train
assert 'kagg_revue.native._revue_native' not in sys.modules
assert 'kagg_revue.native._revue_core' in sys.modules
for name in sys.modules:
    assert not name.startswith('kagg_revue.production'), name
    assert not name.startswith('kagg_revue.teacher'), name
    assert not any(part in name for part in (
        'opponents.kaito', 'opponents.boatlee', 'opponents.mugundh'
    )), name
""",
            str(source),
        ],
        check=True,
    )
