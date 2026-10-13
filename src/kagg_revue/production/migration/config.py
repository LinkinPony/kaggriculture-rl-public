"""Validated controls for scheduled distillation followed by pure WDL PPO."""

from pathlib import Path

from pydantic import Field, model_validator

from kagg_revue.production.config import FrozenSettings, Settings


class MigrationSettings(FrozenSettings):
    """One frozen teacher, one student, and a finite path to zero table weight."""

    production: Settings
    resume_from: Path | None = None
    scale_step: float = Field(gt=0, le=1)
    scale_interval: int = Field(gt=0)
    learning_rate: float = Field(gt=0)
    distillation_temperature: float = Field(gt=0)
    evaluation_interval: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_migration(self) -> "MigrationSettings":
        """Require an explicit teacher and the unmodified full table as the origin."""
        settings = self.production
        if (
            settings.checkpoint is None
            or settings.model.architecture != "work-v1"
            or not settings.model.time_prior
            or settings.model.prior_scale != 1
        ):
            raise ValueError("migration requires an explicit full-prior work teacher")
        selection_end = settings.evaluation_seed + settings.evaluation_games // 2
        if settings.confirmation_seed < selection_end:
            raise ValueError("confirmation must follow the disjoint selection range")
        if (
            settings.ppo.cash_weight
            or settings.ppo.bc_weight
            or settings.ppo.entropy_weight
            or settings.ppo.win_weight <= 0
        ):
            raise ValueError("post-migration PPO requires only the terminal WDL objective")
        return self

    @property
    def teacher(self) -> Path:
        """Return the schema-validated source checkpoint."""
        assert self.production.checkpoint is not None
        return self.production.checkpoint
