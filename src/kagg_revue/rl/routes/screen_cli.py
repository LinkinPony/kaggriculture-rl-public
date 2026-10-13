"""Hydra command for the formal Kaito route-library screen."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.routes.screen import screen_route_library
from kagg_revue.rl.routes.screen_config import RouteScreenAppSettings


def repository_root() -> Path:
    """Return this source checkout."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> RouteScreenAppSettings:
    """Compose and validate the route screen profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="route_ppo_screen_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return RouteScreenAppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Run all six forced routes on the frozen selection panel."""
    settings = load_settings(sys.argv[1:])
    result = screen_route_library(
        settings.route_ppo,
        settings.screen,
        repository_root(),
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
