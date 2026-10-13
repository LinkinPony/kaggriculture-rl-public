"""Hydra command for immutable effect BC dataset aggregation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.bc.effects.aggregate import prepare_effect_aggregate
from kagg_revue.bc.effects.config import EffectAggregateDataAppSettings


def repository_root() -> Path:
    """Return the checkout containing this command."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> EffectAggregateDataAppSettings:
    """Compose and validate one tracked effect aggregate profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(
            config_name="effect_aggregate_data_config",
            overrides=overrides,
        )
    payload = OmegaConf.to_container(composed, resolve=True)
    return EffectAggregateDataAppSettings.model_validate(cast(dict[str, Any], payload))


def main() -> None:
    """Link authenticated component shards into one partitioned dataset."""
    parser = argparse.ArgumentParser(prog="kagg-revue-effect-aggregate-data")
    parser.add_argument("command", nargs="?", default="prepare", choices=("prepare",))
    _arguments, overrides = parser.parse_known_args()
    result = prepare_effect_aggregate(
        load_settings(overrides).effect_aggregate_data,
        repository_root(),
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
