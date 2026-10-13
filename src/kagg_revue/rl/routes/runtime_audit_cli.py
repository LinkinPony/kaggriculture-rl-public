"""Hydra command for route-PPO reference-runtime audit."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.routes.runtime_audit import audit_route_runtime
from kagg_revue.rl.routes.runtime_audit_config import RouteRuntimeAuditAppSettings


def repository_root() -> Path:
    """Return this source checkout."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> RouteRuntimeAuditAppSettings:
    """Compose and validate one route runtime audit."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="route_ppo_runtime_audit_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return RouteRuntimeAuditAppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Run per-action parity and official-time accounting."""
    settings = load_settings(sys.argv[1:])
    result = audit_route_runtime(
        settings.route_ppo,
        settings.audit,
        repository_root(),
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
