"""Hydra command for random-initialized canonical-intent BC."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.bc.intents.config import IntentBcAppSettings
from kagg_revue.bc.intents.train import train_intent_bc


def repository_root() -> Path:
    """Return the checkout containing this command."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> IntentBcAppSettings:
    """Compose and validate one tracked canonical-intent BC profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="intent_bc_config", overrides=overrides)
    payload = OmegaConf.to_container(composed, resolve=True)
    return IntentBcAppSettings.model_validate(cast(dict[str, Any], payload))


def main() -> None:
    """Train one provenance-bound intent policy from fresh random weights."""
    parser = argparse.ArgumentParser(prog="kagg-revue-intent-bc")
    parser.add_argument("command", nargs="?", default="train", choices=("train",))
    _arguments, overrides = parser.parse_known_args()
    settings = load_settings(overrides).intent_bc
    result = train_intent_bc(settings, repository_root())
    if result:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
