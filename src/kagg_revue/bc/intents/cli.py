"""Hydra command for causal canonical-intent teacher data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.bc.intents.config import IntentTeacherDataAppSettings
from kagg_revue.bc.intents.prepare import prepare_intent_teacher_dataset


def repository_root() -> Path:
    """Return the checkout containing this command."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> IntentTeacherDataAppSettings:
    """Compose and validate the tracked canonical-intent data profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="intent_teacher_data_config", overrides=overrides)
    payload = OmegaConf.to_container(composed, resolve=True)
    return IntentTeacherDataAppSettings.model_validate(cast(dict[str, Any], payload))


def main() -> None:
    """Generate exact causal teacher transactions and compact native labels."""
    parser = argparse.ArgumentParser(prog="kagg-revue-intent-teacher-data")
    parser.add_argument("command", nargs="?", default="prepare", choices=("prepare",))
    parser.add_argument("--smoke", action="store_true")
    arguments, overrides = parser.parse_known_args()
    del arguments.command
    settings = load_settings(overrides).intent_teacher_data
    result = prepare_intent_teacher_dataset(
        settings,
        repository_root(),
        smoke=arguments.smoke,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
