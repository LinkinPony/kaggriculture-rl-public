"""Hydra command for Rank8 labels on frozen-student effect states."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.bc.effects.config import EffectCorrectionDataAppSettings
from kagg_revue.bc.effects.correction import prepare_effect_corrections


def repository_root() -> Path:
    """Return the checkout containing this command."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> EffectCorrectionDataAppSettings:
    """Compose and validate one tracked effect correction profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(
            config_name="effect_correction_data_config",
            overrides=overrides,
        )
    payload = OmegaConf.to_container(composed, resolve=True)
    return EffectCorrectionDataAppSettings.model_validate(
        cast(dict[str, Any], payload)
    )


def main() -> None:
    """Generate exact teacher corrections on student-driven trajectories."""
    parser = argparse.ArgumentParser(prog="kagg-revue-effect-correction-data")
    parser.add_argument("command", nargs="?", default="prepare", choices=("prepare",))
    parser.add_argument("--smoke", action="store_true")
    arguments, overrides = parser.parse_known_args()
    result = prepare_effect_corrections(
        load_settings(overrides).effect_correction_data,
        repository_root(),
        smoke=arguments.smoke,
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
