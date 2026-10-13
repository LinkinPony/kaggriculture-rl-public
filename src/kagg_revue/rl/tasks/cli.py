"""Hydra command for compiler-in-the-loop unit-task PPO."""

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

from kagg_revue.rl.tasks.config import TaskRlAppSettings, TaskRlSettings


class _Trainer(Protocol):
    def __call__(
        self,
        settings: TaskRlSettings,
        repository_root: Path,
        *,
        smoke: bool,
    ) -> dict[str, object]: ...


class _Evaluator(Protocol):
    def __call__(
        self,
        settings: TaskRlSettings,
        repository_root: Path,
    ) -> dict[str, object]: ...


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> TaskRlSettings:
    """Compose and strongly validate one unit-task Hydra profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="unit_task_rl_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return TaskRlAppSettings.model_validate(cast(dict[str, Any], value)).unit_task_rl


def _train(
    settings: TaskRlSettings,
    root: Path,
    *,
    smoke: bool,
) -> dict[str, object]:
    if (
        any(value.startswith("cuda") for value in settings.training_devices)
        and settings.cuda_allocator_expandable_segments
    ):
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    module = importlib.import_module("kagg_revue.rl.tasks.train")
    raw_runner = getattr(module, "train_task_tape", None)
    if not callable(raw_runner):
        raise RuntimeError("unit-task trainer does not expose train_task_tape")
    runner = cast(_Trainer, cast(Callable[..., object], raw_runner))
    return runner(settings, root, smoke=smoke)


def _evaluate(settings: TaskRlSettings, root: Path) -> dict[str, object]:
    module = importlib.import_module("kagg_revue.rl.tasks.evaluate")
    raw_runner = getattr(module, "evaluate_task_tape", None)
    if not callable(raw_runner):
        raise RuntimeError("unit-task evaluator does not expose evaluate_task_tape")
    runner = cast(_Evaluator, cast(Callable[..., object], raw_runner))
    return runner(settings, root)


def main() -> None:
    """Run long unit-task PPO or one bounded integration smoke."""
    parser = argparse.ArgumentParser(prog="kagg-revue-task-rl")
    parser.add_argument(
        "command",
        nargs="?",
        default="train",
        choices=("run", "train", "evaluate", "smoke"),
    )
    arguments, overrides = parser.parse_known_args()
    settings = load_settings(overrides)
    root = repository_root()
    if arguments.command == "evaluate":
        result = _evaluate(settings, root)
    elif arguments.command == "run":
        result = {
            "training": _train(settings, root, smoke=False),
            "evaluation": _evaluate(settings, root),
        }
    else:
        result = _train(settings, root, smoke=arguments.command == "smoke")
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
