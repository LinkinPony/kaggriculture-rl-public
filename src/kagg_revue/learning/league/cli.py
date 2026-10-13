"""Hydra launch for the specialist league with frozen native script opponents."""

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.learning.league.config import League
from kagg_revue.learning.league.launch import run


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="learning_league_native"
)
def main(configuration: DictConfig) -> None:
    """Resolve the shared policy recipe and immutable specialist source manifest."""
    values = OmegaConf.to_container(configuration.league, resolve=True)
    assert isinstance(values, dict)
    values["experiment"] = OmegaConf.to_container(configuration.experiment, resolve=True)
    run(League.model_validate(values))


if __name__ == "__main__":
    main()
