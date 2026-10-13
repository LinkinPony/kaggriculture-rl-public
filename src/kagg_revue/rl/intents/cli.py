"""Hydra entry point for intent-ledger PPO."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.intents.config import IntentRlAppSettings, IntentRlSettings


def repository_root() -> Path:
    """Return the checkout containing this command."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> IntentRlSettings:
    """Compose and validate one tracked training profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="intent_ledger_rl_config", overrides=overrides)
    payload = OmegaConf.to_container(composed, resolve=True)
    return IntentRlAppSettings.model_validate(
        cast(dict[str, Any], payload)
    ).intent_ledger_rl


def main() -> None:
    """Run a long training lineage or its bounded integration smoke."""
    parser = argparse.ArgumentParser(prog="kagg-revue-intent-rl")
    parser.add_argument(
        "command", nargs="?", default="train", choices=("train", "smoke")
    )
    arguments, overrides = parser.parse_known_args()
    settings = load_settings(overrides)
    if settings.device.startswith("cuda"):
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    from kagg_revue.rl.intents.train import train_intents

    result = train_intents(
        settings,
        repository_root(),
        smoke=arguments.command == "smoke",
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
