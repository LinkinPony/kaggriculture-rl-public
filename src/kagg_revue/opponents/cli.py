"""Hydra command for frozen public-notebook opponent benchmarks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.opponents.benchmark import run_benchmark
from kagg_revue.opponents.config import OpponentBenchmarkAppSettings


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[3]


def _settings(overrides: list[str]) -> OpponentBenchmarkAppSettings:
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="opponent_benchmark", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return OpponentBenchmarkAppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Run one complete public-notebook opponent benchmark."""
    import sys

    settings = _settings(sys.argv[1:])
    result = run_benchmark(settings.benchmark, repository_root())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
