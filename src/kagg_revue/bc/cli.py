"""Hydra command for behavior-cloning training and evaluation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.bc.config import AppSettings
from kagg_revue.bc.experiment import Command, run_experiment


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[3]


def _settings(overrides: list[str]) -> AppSettings:
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return AppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Run a complete experiment or one resumable phase."""
    parser = argparse.ArgumentParser(prog="kagg-revue")
    parser.add_argument("command", choices=("run", "train", "evaluate"))
    arguments, overrides = parser.parse_known_args()
    settings = _settings(overrides)
    result = run_experiment(
        settings.model,
        settings.experiment,
        repository_root(),
        cast(Command, arguments.command),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
