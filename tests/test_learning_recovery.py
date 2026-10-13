import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest
import torch

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.rewards import wdl_protocol


def test_archived_source_rejects_tampering_and_symlinks_before_import(tmp_path: Path) -> None:
    payload = b'"""Archived source fixture."""\n'
    member = "src/kagg_revue/native/fixture.py"
    files = {member: hashlib.sha256(payload).hexdigest()}
    source_hash = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    state = {"source": source_hash, "native": "test-native"}
    write_json(
        tmp_path / "source.json",
        {
            "files": files,
            "source_sha256": source_hash,
            "native_sha256": "test-native",
            "torch_version": torch.__version__,
        },
    )
    for symlink in (False, True):
        with tarfile.open(tmp_path / "source.tar.gz", "w:gz") as archive:
            info = tarfile.TarInfo(member)
            if symlink:
                info.type, info.linkname = tarfile.SYMTYPE, "../../outside.py"
                archive.addfile(info)
            else:
                altered = payload + b"changed"
                info.size = len(altered)
                archive.addfile(info, io.BytesIO(altered))
        with pytest.raises(ValueError, match="path or file kind|implementation changed"):
            materialize(tmp_path, state, tmp_path / "isolated")
        assert not (tmp_path / "isolated" / member).exists()


def test_wdl_transition_preserves_all_other_protocol_controls() -> None:
    from kagg_revue.learning.adapter import runtime_settings
    from kagg_revue.learning.config import Experiment
    from kagg_revue.learning.state import protocol

    original = Experiment(output_dir=Path("outputs/learning/test"), cash_weight=1.0)
    before = protocol(original)
    updated = wdl_protocol({"protocol": before})
    assert protocol(updated) == {**before, "cash_weight": 0.0}
    assert before["cash_weight"] == 1.0
    settings = runtime_settings(updated)
    assert settings.ppo.cash_weight == 0.0
    assert settings.ppo.win_weight == 1.0


def test_training_recipes_and_shared_optimizer_default_to_wdl() -> None:
    from hydra import compose, initialize_config_dir
    from omegaconf import OmegaConf

    from kagg_revue.learning.adapter import runtime_settings
    from kagg_revue.learning.config import Experiment
    from kagg_revue.learning.optimization.settings import OptimizationSettings

    directory = Path(__file__).resolve().parents[1] / "configs"
    with initialize_config_dir(version_base=None, config_dir=str(directory)):
        for name in (
            "learning",
            "learning_demonstrations",
            "learning_curriculum",
            "learning_context",
            "learning_budget",
            "learning_top10_2d",
        ):
            config = compose(config_name=name)
            assert OmegaConf.select(config, "experiment.cash_weight") == 0.0, name
    settings = runtime_settings(Experiment(output_dir=Path("outputs/learning/test")))
    values = settings.ppo.model_dump(exclude={"cash_weight", "win_weight"})
    defaults = OptimizationSettings.model_validate(values)
    assert defaults.cash_weight == 0.0
    assert defaults.win_weight == 1.0
