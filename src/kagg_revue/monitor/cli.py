"""Hydra-configured entry point for the local monitoring Web UI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, cast

import uvicorn
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.monitor.app import create_app
from kagg_revue.monitor.config import MonitorSettings

LOCAL_BIND_HOST = "127.0.0.1"


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[3]


def _settings(overrides: list[str]) -> MonitorSettings:
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="monitor", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return MonitorSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Serve the experiment dashboard on IPv4 loopback only."""
    parser = argparse.ArgumentParser(prog="kagg-revue-monitor")
    _, overrides = parser.parse_known_args()
    settings = _settings(overrides)
    app = create_app(settings, repository_root())
    print(f"Revue monitor: http://{LOCAL_BIND_HOST}:{settings.port}", flush=True)
    uvicorn.run(
        app,
        host=LOCAL_BIND_HOST,
        port=settings.port,
        access_log=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
