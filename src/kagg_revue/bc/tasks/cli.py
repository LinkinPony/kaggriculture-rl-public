"""Hydra command for unit-task behavior cloning and direct evaluation."""

from __future__ import annotations

import argparse
import importlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.bc.tasks.config import TaskBcAppSettings, TaskBcSettings


class _Runner(Protocol):
    def __call__(
        self,
        settings: TaskBcSettings,
        repository_root: Path,
    ) -> dict[str, object]: ...


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> TaskBcSettings:
    """Compose and strongly validate one task BC profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="unit_task_bc_config", overrides=overrides)
    raw = OmegaConf.to_container(composed, resolve=True)
    return TaskBcAppSettings.model_validate(cast(dict[str, Any], raw)).unit_task_bc


def _runner(module_name: str, function_name: str) -> _Runner:
    module = importlib.import_module(module_name)
    value = getattr(module, function_name, None)
    if not callable(value):
        raise RuntimeError(f"task BC runner is absent: {function_name}")
    return cast(_Runner, cast(Callable[..., object], value))


def main() -> None:
    """Prepare replay shards, train the task head, or run both stages."""
    parser = argparse.ArgumentParser(prog="kagg-revue-task-bc")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=("prepare", "train", "evaluate", "run"),
    )
    arguments, overrides = parser.parse_known_args()
    settings = load_settings(overrides)
    root = repository_root()
    result: dict[str, object]
    if arguments.command == "prepare":
        result = _runner(
            "kagg_revue.bc.tasks.prepare", "prepare_task_bc_dataset"
        )(settings, root)
    elif arguments.command == "train":
        result = _runner("kagg_revue.bc.tasks.train", "train_task_bc")(
            settings, root
        )
    elif arguments.command == "evaluate":
        result = _runner(
            "kagg_revue.bc.tasks.evaluate", "evaluate_task_bc"
        )(settings, root)
    else:
        result = {
            "preparation": _runner(
                "kagg_revue.bc.tasks.prepare", "prepare_task_bc_dataset"
            )(settings, root),
            "training": _runner(
                "kagg_revue.bc.tasks.train", "train_task_bc"
            )(settings, root),
            "evaluation": (
                _runner("kagg_revue.bc.tasks.evaluate", "evaluate_task_bc")(
                    settings, root
                )
                if settings.evaluation.enabled
                else {"status": "disabled"}
            ),
        }
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
