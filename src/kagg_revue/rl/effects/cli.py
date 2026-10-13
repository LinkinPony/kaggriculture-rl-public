"""Hydra entry point for atomic-effect PPO."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.effects.config import EffectRlAppSettings, EffectRlSettings


def repository_root() -> Path:
    """Return the checkout containing this command."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> EffectRlSettings:
    """Compose and strongly validate one tracked effect training profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="effect_policy_rl_config", overrides=overrides)
    payload = OmegaConf.to_container(composed, resolve=True)
    return EffectRlAppSettings.model_validate(cast(dict[str, Any], payload)).effect_policy_rl


def main() -> None:
    """Run a long effect lineage or a bounded integration smoke."""
    parser = argparse.ArgumentParser(prog="kagg-revue-effect-rl")
    parser.add_argument("command", nargs="?", default="train", choices=("train", "smoke"))
    arguments, overrides = parser.parse_known_args()
    settings = load_settings(overrides)
    if settings.device.startswith("cuda"):
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        os.environ.setdefault(
            "TORCHINDUCTOR_CACHE_DIR",
            str(repository_root() / "tmp" / "torchinductor"),
        )
    from kagg_revue.rl.effects.train import train_effects

    result = train_effects(
        settings,
        repository_root(),
        smoke=arguments.command == "smoke",
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
