"""Hydra entry point for parallel-turn generation, BC, PPO and evaluation."""

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.production.config import Settings


@hydra.main(version_base=None, config_path="../../../configs", config_name="production_config")
def main(configuration: DictConfig) -> None:
    """Resolve once and execute the selected reproducible profile."""
    resolved = OmegaConf.to_container(configuration.production, resolve=True)
    settings = Settings.model_validate(resolved)
    if settings.mode == "generate":
        from kagg_revue.production.prepare import prepare

        prepare(settings)
    elif settings.mode == "audit":
        from kagg_revue.production.oracle import audit

        audit(settings)
    elif settings.mode == "bc":
        from kagg_revue.production.imitation import train

        train(settings)
    elif settings.mode == "evaluate":
        from kagg_revue.production.evaluation import evaluate

        evaluate(settings)
    elif settings.mode == "reference":
        from kagg_revue.production.reference import audit as reference_audit

        reference_audit(settings)
    elif settings.mode == "transfer":
        from kagg_revue.production.cadence import transfer

        transfer(settings)
    elif settings.mode == "preflight":
        from kagg_revue.production.recovery import preflight

        preflight(settings)
    else:
        from kagg_revue.production.train import launch

        launch(settings)


if __name__ == "__main__":
    main()
