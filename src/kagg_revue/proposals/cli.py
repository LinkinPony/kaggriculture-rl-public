"""Hydra command for replay-route complete-match evaluation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.proposals.config import ReplayRouteEvaluationAppSettings
from kagg_revue.proposals.evaluate import evaluate_replay_routes


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[3]


def load_settings(overrides: list[str]) -> ReplayRouteEvaluationAppSettings:
    """Compose and validate one replay-route Hydra profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="replay_route_evaluation", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return ReplayRouteEvaluationAppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Run an authenticated common-seed replay-route panel."""
    settings = load_settings(sys.argv[1:]).replay_route
    report = evaluate_replay_routes(settings, repository_root())
    print(
        json.dumps(
            {
                "output_dir": str(settings.output_dir),
                "routes": len(cast(list[object], report["routes"])),
                "promotion_authority": report["promotion_authority"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
