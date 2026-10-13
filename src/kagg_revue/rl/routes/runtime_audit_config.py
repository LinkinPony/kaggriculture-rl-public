"""Validated Hydra settings for route-policy runtime parity and timing."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.rl.routes.config import RoutePpoSettings


def _output_path(path: Path, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != "outputs":
        raise ValueError(f"{name} must be repository-relative under outputs/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape outputs/")


class RouteRuntimeAuditSettings(BaseModel):
    """One frozen CPU reference-runtime audit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    checkpoint_path: Path
    confirmation_report: Path
    output_dir: Path
    prior_logit: float = Field(gt=0.0, allow_inf_nan=False)
    seed_start: int = Field(ge=0)
    seed_count: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_paths(self) -> RouteRuntimeAuditSettings:
        """Keep inputs and generated evidence under outputs."""
        _output_path(self.checkpoint_path, "route audit checkpoint_path")
        _output_path(self.confirmation_report, "route audit confirmation_report")
        _output_path(self.output_dir, "route audit output_dir")
        return self


class RouteRuntimeAuditAppSettings(BaseModel):
    """Hydra root joining the PPO and runtime-audit contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    route_ppo: RoutePpoSettings
    audit: RouteRuntimeAuditSettings


__all__ = ["RouteRuntimeAuditAppSettings", "RouteRuntimeAuditSettings"]
