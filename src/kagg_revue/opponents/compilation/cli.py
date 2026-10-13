"""Hydra entry point for reproducible native policy generation."""

import json
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.configuration import FrozenSettings
from kagg_revue.opponents.compilation.generation import generate
from kagg_revue.opponents.compilation.sources import ExtraSource


class Generation(FrozenSettings):
    """Explicit source, native destination, and immutable runtime assets."""

    manifest: Path
    destination: Path
    assets: Path
    report: Path
    additions: dict[str, ExtraSource] = Field(default_factory=dict)


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="native_public_20260921"
)
def main(config: DictConfig) -> None:
    """Reject changed sources before producing any native implementation."""
    settings = Generation.model_validate(OmegaConf.to_container(config.generation, resolve=True))
    report = generate(settings.manifest, settings.destination, settings.assets, settings.additions)
    settings.report.parent.mkdir(parents=True, exist_ok=True)
    settings.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
