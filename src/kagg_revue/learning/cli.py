"""Hydra entry point for new random-root reinforcement learning experiments."""

from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.learning.config import Experiment


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="learning_mainline",
)
def main(configuration: DictConfig) -> None:
    """Validate the teacher-free protocol before importing or initializing models."""
    from kagg_revue.learning.train import run

    run(Experiment.model_validate(OmegaConf.to_container(configuration.experiment, resolve=True)))


if __name__ == "__main__":
    main()
