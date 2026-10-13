"""Hydra command for capability-search PPO training and smoke runs."""

from __future__ import annotations

import argparse
import importlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.capabilities.config import (
    CapabilityRlAppSettings,
    CapabilityRlSettings,
)


class _CapabilityTrainer(Protocol):
    def __call__(
        self,
        settings: CapabilityRlSettings,
        repository_root: Path,
        *,
        smoke: bool,
    ) -> dict[str, object]: ...


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> CapabilityRlSettings:
    """Compose and strongly validate one capability-RL Hydra profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="capability_rl_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return CapabilityRlAppSettings.model_validate(cast(dict[str, Any], value)).capability_rl


def _run(
    settings: CapabilityRlSettings,
    root: Path,
    *,
    smoke: bool,
) -> dict[str, object]:
    """Load the trainer lazily so configuration/checkpoint tools stay standalone."""
    module = importlib.import_module("kagg_revue.rl.capabilities.train")
    raw_runner = getattr(module, "train_capability", None)
    if not callable(raw_runner):
        raise RuntimeError("capability trainer does not expose train_capability")
    runner = cast(_CapabilityTrainer, cast(Callable[..., object], raw_runner))
    return runner(settings, root, smoke=smoke)


def main() -> None:
    """Run a long capability-PPO train or a bounded integration smoke."""
    parser = argparse.ArgumentParser(prog="kagg-revue-capability-rl")
    parser.add_argument(
        "command",
        nargs="?",
        default="train",
        choices=("train", "smoke"),
    )
    arguments, overrides = parser.parse_known_args()
    settings = load_settings(overrides)
    result = _run(
        settings,
        repository_root(),
        smoke=arguments.command == "smoke",
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
