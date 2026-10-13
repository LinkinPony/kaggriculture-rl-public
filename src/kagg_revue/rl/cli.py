"""Hydra command for terminal-outcome experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.config import RlAppSettings
from kagg_revue.rl.experiment import RlCommand, run_rl_experiment


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[3]


def _settings(overrides: list[str]) -> RlAppSettings:
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="rl_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return RlAppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Train and/or evaluate one immutable actor-critic challenger."""
    parser = argparse.ArgumentParser(prog="kagg-revue-rl")
    parser.add_argument("command", nargs="?", default="run", choices=("run", "train", "evaluate"))
    arguments, overrides = parser.parse_known_args()
    settings = _settings(overrides)
    result = run_rl_experiment(settings.rl, repository_root(), cast(RlCommand, arguments.command))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
