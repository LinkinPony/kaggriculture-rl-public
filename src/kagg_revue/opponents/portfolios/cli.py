"""Hydra entrypoint for extracting and qualifying the active native opponents."""

import json
import sys
from pathlib import Path
from typing import Any, Literal

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf
from pydantic import Field

from kagg_revue.configuration import FrozenSettings
from kagg_revue.opponents.compilation.generation import generate
from kagg_revue.opponents.portfolios.qualification import qualify


class Settings(FrozenSettings):
    """Source identity, independent evaluation seeds, and artifact destinations."""

    mode: Literal["extract", "qualify", "training", "throughput"] = "qualify"
    manifest: Path
    seeds: list[int] = Field(min_length=1)
    workers: int = Field(ge=1, le=32)
    output: Path
    perturb: bool = False
    agents: list[str] | None = None
    asset_destination: Path = Path("src/kagg_revue/opponents/portfolios")


def main() -> None:
    """Execute one reproducible asset extraction or conformance panel."""
    root = Path(__file__).resolve().parents[4]
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        configuration = compose(config_name="native_opponents", overrides=sys.argv[1:])
    settings = Settings.model_validate(OmegaConf.to_container(configuration, resolve=True))
    result: dict[str, Any]
    if settings.mode == "extract":
        result = generate(
            settings.manifest,
            Path("src/kagg_revue/native/csrc/opponents/compiled/generated"),
            settings.asset_destination,
        )
    elif settings.mode == "training":
        from kagg_revue.opponents.portfolios.training import training_parity

        result = training_parity(settings.manifest, settings.output)
    elif settings.mode == "throughput":
        from kagg_revue.opponents.portfolios.training import throughput

        result = throughput(settings.output)
    else:
        result = qualify(
            settings.manifest,
            settings.seeds,
            settings.workers,
            settings.output,
            settings.perturb,
            settings.agents,
        )
    print(json.dumps(result, indent=2))
    if result.get("passed") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
