"""Validated settings for the route-library complementarity screen."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator

from kagg_revue.rl.routes.config import RoutePpoSettings


class RouteScreenSettings(BaseModel):
    """Output identity for a fixed selection-panel route screen."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    output_dir: Path

    @model_validator(mode="after")
    def validate_output(self) -> RouteScreenSettings:
        """Keep generated evidence under repository outputs."""
        path = self.output_dir
        if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != "outputs":
            raise ValueError("route screen output must be repository-relative under outputs/")
        if ".." in path.parts:
            raise ValueError("route screen output cannot escape outputs/")
        return self


class RouteScreenAppSettings(BaseModel):
    """Hydra root joining training and screen contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    route_ppo: RoutePpoSettings
    screen: RouteScreenSettings


__all__ = ["RouteScreenAppSettings", "RouteScreenSettings"]
