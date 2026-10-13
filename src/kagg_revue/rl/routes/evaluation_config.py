"""Validated Hydra settings for frozen route-PPO checkpoint evaluation."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.rl.routes.config import RoutePpoSettings


def _output_path(path: Path, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != "outputs":
        raise ValueError(f"{name} must be repository-relative under outputs/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape outputs/")


class RouteEvaluationSettings(BaseModel):
    """One immutable selection or confirmation panel."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_dir: Path
    output_dir: Path
    panel: Literal["selection", "confirmation"]
    checkpoint_set: Literal["permanent", "single"]
    checkpoint_update: int | None = None
    seed_start: int | None = Field(default=None, ge=0)
    seed_count: int | None = Field(default=None, gt=0)
    prior_logit_override: float | None = Field(default=None, gt=0.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_evaluation(self) -> RouteEvaluationSettings:
        """Keep selection grids and confirmation targets unambiguous."""
        _output_path(self.run_dir, "route evaluation run_dir")
        _output_path(self.output_dir, "route evaluation output_dir")
        if self.checkpoint_set == "single" and self.checkpoint_update is None:
            raise ValueError("single route evaluation requires checkpoint_update")
        if self.checkpoint_set == "permanent" and self.checkpoint_update is not None:
            raise ValueError("permanent route grid cannot name one checkpoint update")
        if self.panel == "confirmation" and self.checkpoint_set != "single":
            raise ValueError("confirmation must evaluate exactly one selected checkpoint")
        if (self.seed_start is None) != (self.seed_count is None):
            raise ValueError("route evaluation seed override requires both start and count")
        return self


class RouteEvaluationAppSettings(BaseModel):
    """Hydra root joining the training contract and evaluation panel."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    route_ppo: RoutePpoSettings
    evaluation: RouteEvaluationSettings


__all__ = ["RouteEvaluationAppSettings", "RouteEvaluationSettings"]
