"""Hydra entry point for isolated script-opponent research."""

import json
from typing import Any, cast

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.opponents.research.arena import run
from kagg_revue.opponents.research.settings import Experiment


@hydra.main(version_base=None, config_path="../../../../configs", config_name="script_research")
def main(configuration: DictConfig) -> None:
    """Run the declared experimental panel and retain its complete evidence."""
    config = Experiment.model_validate(
        cast(dict[str, Any], OmegaConf.to_container(configuration.research, resolve=True))
    )
    print(json.dumps(run(config), indent=2))


if __name__ == "__main__":
    main()
