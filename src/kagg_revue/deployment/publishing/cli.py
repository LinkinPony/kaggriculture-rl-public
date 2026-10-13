"""Launch the half-hour submission publisher with Hydra configuration."""

from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.deployment.publishing.config import Publishing
from kagg_revue.deployment.publishing.service import run


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="deployment_publish",
)
def main(configuration: DictConfig) -> None:
    """Resolve the private upload destination and persist all generated outputs locally."""
    run(Publishing.model_validate(OmegaConf.to_container(configuration.publishing, resolve=True)))


if __name__ == "__main__":
    main()
