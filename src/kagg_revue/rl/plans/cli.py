"""Hydra command for pure event-driven structured-plan PPO."""

from __future__ import annotations

import argparse
import importlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.plans.config import (
    StructuredPlanRlAppSettings,
    StructuredPlanRlSettings,
)


class _Trainer(Protocol):
    def __call__(
        self,
        settings: StructuredPlanRlSettings,
        repository_root: Path,
        *,
        smoke: bool,
    ) -> dict[str, object]: ...


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> StructuredPlanRlSettings:
    """Compose and strongly validate one structured-plan Hydra profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="structured_plan_rl_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return StructuredPlanRlAppSettings.model_validate(
        cast(dict[str, Any], value)
    ).structured_plan_rl


def _run(
    settings: StructuredPlanRlSettings,
    root: Path,
    *,
    smoke: bool,
) -> dict[str, object]:
    module = importlib.import_module("kagg_revue.rl.plans.train")
    raw_runner = getattr(module, "train_structured_plan", None)
    if not callable(raw_runner):
        raise RuntimeError("structured-plan trainer does not expose train_structured_plan")
    runner = cast(_Trainer, cast(Callable[..., object], raw_runner))
    return runner(settings, root, smoke=smoke)


def main() -> None:
    """Run long structured-plan PPO or a bounded integration smoke."""
    parser = argparse.ArgumentParser(prog="kagg-revue-plan-rl")
    parser.add_argument(
        "command",
        nargs="?",
        default="train",
        choices=("train", "smoke"),
    )
    arguments, overrides = parser.parse_known_args()
    result = _run(
        load_settings(overrides),
        repository_root(),
        smoke=arguments.command == "smoke",
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
