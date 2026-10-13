"""Hydra command for PPO-primary Kaito route training."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.routes.config import RoutePpoAppSettings, RoutePpoSettings
from kagg_revue.rl.routes.train import train_route_ppo


def repository_root() -> Path:
    """Return this source checkout."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> RoutePpoSettings:
    """Compose and validate one route-PPO profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="route_ppo_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return RoutePpoAppSettings.model_validate(cast(dict[str, Any], value)).route_ppo


def main() -> None:
    """Run a long route PPO experiment or a bounded integration smoke."""
    parser = argparse.ArgumentParser(prog="kagg-revue-route-ppo")
    parser.add_argument("command", nargs="?", default="train", choices=("train", "smoke"))
    arguments, overrides = parser.parse_known_args()
    result = train_route_ppo(
        load_settings(overrides),
        repository_root(),
        smoke=arguments.command == "smoke",
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
