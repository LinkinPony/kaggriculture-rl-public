"""Hydra command for compact behavior-cloning replay preparation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.bc.data_config import BcDataAppSettings
from kagg_revue.bc.prepare import prepare_dataset


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[3]


def _settings(overrides: list[str]) -> BcDataAppSettings:
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="bc_data", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return BcDataAppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Prepare an immutable compact dataset from authenticated replay ZIPs."""
    parser = argparse.ArgumentParser(prog="kagg-revue-bc-data")
    parser.add_argument("command", nargs="?", default="prepare", choices=("prepare",))
    _, overrides = parser.parse_known_args()
    settings = _settings(overrides)
    result = prepare_dataset(settings.bc_data, repository_root())
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
