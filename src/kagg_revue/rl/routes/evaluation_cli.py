"""Hydra command for route-PPO checkpoint selection and confirmation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.routes.evaluate import evaluate_route_checkpoints
from kagg_revue.rl.routes.evaluation_config import RouteEvaluationAppSettings


def repository_root() -> Path:
    """Return this source checkout."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> RouteEvaluationAppSettings:
    """Compose and validate a route checkpoint evaluation."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="route_ppo_evaluation_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return RouteEvaluationAppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Evaluate a permanent selection grid or one confirmation checkpoint."""
    import sys

    settings = load_settings(sys.argv[1:])
    result = evaluate_route_checkpoints(
        settings.route_ppo,
        settings.evaluation,
        repository_root(),
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
