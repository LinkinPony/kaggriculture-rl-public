"""Hydra command for authenticated teacher rollouts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.teacher.config import TeacherDataAppSettings
from kagg_revue.teacher.prepare import prepare_teacher_dataset


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[3]


def _settings(overrides: list[str]) -> TeacherDataAppSettings:
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="teacher_data", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return TeacherDataAppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Generate compact native rollouts from the exact submitted teacher."""
    parser = argparse.ArgumentParser(prog="kagg-revue-teacher-data")
    parser.add_argument("command", nargs="?", default="prepare", choices=("prepare",))
    _, overrides = parser.parse_known_args()
    settings = _settings(overrides)
    result = prepare_teacher_dataset(settings.teacher_data, repository_root())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
