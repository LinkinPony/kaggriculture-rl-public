"""Hydra command for atomic-effect behavior cloning."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.bc.effects.config import EffectBcAppSettings
from kagg_revue.bc.effects.train import train_effect_bc


def repository_root() -> Path:
    """Return the checkout containing this command."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> EffectBcAppSettings:
    """Compose and validate one tracked atomic-effect BC profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="effect_bc_config", overrides=overrides)
    payload = OmegaConf.to_container(composed, resolve=True)
    return EffectBcAppSettings.model_validate(cast(dict[str, Any], payload))


def main() -> None:
    """Train one provenance-bound atomic-effect warm start."""
    parser = argparse.ArgumentParser(prog="kagg-revue-effect-bc")
    parser.add_argument("command", nargs="?", default="train", choices=("train",))
    parser.add_argument("--smoke", action="store_true")
    arguments, overrides = parser.parse_known_args()
    result = train_effect_bc(
        load_settings(overrides).effect_bc,
        repository_root(),
        smoke=arguments.smoke,
    )
    if result:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
