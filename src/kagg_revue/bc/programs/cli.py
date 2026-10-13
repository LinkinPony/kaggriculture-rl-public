"""Hydra command for conditional-program data preparation and training."""

from __future__ import annotations

import argparse
import importlib
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.bc.programs.config import ProgramBcAppSettings, ProgramBcSettings


class _Runner(Protocol):
    def __call__(self, settings: ProgramBcSettings, repository_root: Path) -> dict[str, object]: ...


def repository_root() -> Path:
    """Return the checkout containing this source package."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> ProgramBcSettings:
    """Compose and strongly validate one program-BC profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="conditional_program_bc_config", overrides=overrides)
    raw = OmegaConf.to_container(composed, resolve=True)
    return ProgramBcAppSettings.model_validate(cast(dict[str, Any], raw)).conditional_program_bc


def _runner(module_name: str, function_name: str) -> _Runner:
    module = importlib.import_module(module_name)
    value = getattr(module, function_name, None)
    if not callable(value):
        raise RuntimeError(f"program BC runner is absent: {function_name}")
    return cast(_Runner, cast(Callable[..., object], value))


def main() -> None:
    """Prepare compact data, train, or execute both stages."""
    parser = argparse.ArgumentParser(prog="kagg-revue-program-bc")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=("prepare", "train", "run"),
    )
    arguments, overrides = parser.parse_known_args()
    settings = load_settings(overrides)
    root = repository_root()
    if settings.aggregate_source is not None:
        preparation = _runner(
            "kagg_revue.bc.programs.aggregate",
            "prepare_program_aggregate",
        )
    elif settings.demonstration_source is not None:
        preparation = _runner(
            "kagg_revue.bc.programs.generation",
            "prepare_program_demonstrations",
        )
    elif settings.correction_source is not None:
        preparation = _runner(
            "kagg_revue.bc.programs.correction",
            "prepare_program_corrections",
        )
    else:
        preparation = _runner(
            "kagg_revue.bc.programs.prepare", "prepare_program_bc_dataset"
        )
    training = _runner("kagg_revue.bc.programs.train", "train_program_bc")
    if arguments.command == "prepare":
        result = preparation(settings, root)
    elif arguments.command == "train":
        result = training(settings, root)
    else:
        result = {
            "preparation": preparation(settings, root),
            "training": training(settings, root),
        }
    if int(os.environ.get("RANK", "0")) == 0:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
