"""Hydra command for causal Rank8 atomic-effect teacher data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.bc.effects.config import EffectTeacherDataAppSettings
from kagg_revue.bc.effects.prepare import prepare_effect_teacher_dataset


def repository_root() -> Path:
    """Return the checkout containing this command."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> EffectTeacherDataAppSettings:
    """Compose and validate the tracked effect teacher-data profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="effect_teacher_data_config", overrides=overrides)
    payload = OmegaConf.to_container(composed, resolve=True)
    return EffectTeacherDataAppSettings.model_validate(cast(dict[str, Any], payload))


def main() -> None:
    """Generate exact causal effect transactions and compact native labels."""
    parser = argparse.ArgumentParser(prog="kagg-revue-effect-teacher-data")
    parser.add_argument("command", nargs="?", default="prepare", choices=("prepare",))
    parser.add_argument("--smoke", action="store_true")
    arguments, overrides = parser.parse_known_args()
    settings = load_settings(overrides).effect_teacher_data
    result = prepare_effect_teacher_dataset(
        settings,
        repository_root(),
        smoke=arguments.smoke,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
