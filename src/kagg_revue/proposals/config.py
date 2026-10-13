"""Validated settings for replay-route proposal evaluation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_ROUTE_ID = re.compile(r"^[1-9][0-9]*:[01]$")


def _relative_under(path: Path, directory: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != directory:
        raise ValueError(f"{name} must be a repository-relative path under {directory}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


class ReplayRouteEvaluationSettings(BaseModel):
    """One immutable complete-match panel for empirical replay routes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_manifest: Path
    source_agent_name: str
    prefix_turns: int = Field(gt=0)
    route_ids: tuple[str, ...] | None = None
    output_dir: Path
    baseline_report: Path
    seed_start: int = Field(ge=0)
    seed_count: int = Field(gt=0)
    opponents: tuple[str, ...]
    paired_seats: Literal[True]
    cpu_workers: int = Field(gt=0, le=64)
    act_timeout_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    remaining_overage_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_evaluation(self) -> ReplayRouteEvaluationSettings:
        """Reject ambiguous artifacts, panels, and non-official time contracts."""
        _relative_under(self.source_manifest, "data", "replay source manifest")
        if self.source_manifest.parts[:2] != ("data", "external"):
            raise ValueError("replay source manifest must remain under data/external/")
        _relative_under(self.output_dir, "outputs", "replay evaluation output")
        if self.output_dir.parts[:2] != ("outputs", "evaluation"):
            raise ValueError("replay evaluation output must remain under outputs/evaluation/")
        _relative_under(self.baseline_report, "outputs", "replay baseline report")
        if self.baseline_report.parts[:2] != ("outputs", "evaluation"):
            raise ValueError("replay baseline must remain under outputs/evaluation/")
        if not self.source_agent_name or self.source_agent_name != self.source_agent_name.strip():
            raise ValueError("replay source agent name must be canonical")
        if not self.opponents or len(set(self.opponents)) != len(self.opponents):
            raise ValueError("replay opponents must be nonempty and unique")
        if any(not value or value != value.strip() for value in self.opponents):
            raise ValueError("replay opponent identities must be canonical")
        if "kaito_v48" not in self.opponents:
            raise ValueError("replay panel must include the frozen Kaito incumbent")
        if self.route_ids is not None:
            if not self.route_ids or len(set(self.route_ids)) != len(self.route_ids):
                raise ValueError("explicit replay routes must be nonempty and unique")
            if any(_ROUTE_ID.fullmatch(value) is None for value in self.route_ids):
                raise ValueError("replay route ids must use the canonical episode:seat form")
        if self.act_timeout_seconds != 1.0 or self.remaining_overage_seconds != 60.0:
            raise ValueError("replay evaluation must bind the official time-budget contract")
        episode_steps = self.environment.get("episodeSteps")
        market_orders = self.environment.get("maxMarketOrdersPerTurn")
        if (
            not isinstance(episode_steps, int)
            or isinstance(episode_steps, bool)
            or episode_steps < 2
        ):
            raise ValueError("replay environment episodeSteps must allow a transition")
        if (
            not isinstance(market_orders, int)
            or isinstance(market_orders, bool)
            or market_orders < 1
        ):
            raise ValueError("replay environment market order capacity must be positive")
        if self.prefix_turns >= episode_steps:
            raise ValueError("replay prefix horizon must fit within the episode")
        return self

    @property
    def seeds(self) -> tuple[int, ...]:
        """Expand the contiguous common-seed panel."""
        return tuple(range(self.seed_start, self.seed_start + self.seed_count))


class ReplayRouteEvaluationAppSettings(BaseModel):
    """Hydra root for replay-route evaluation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    replay_route: ReplayRouteEvaluationSettings


__all__ = ["ReplayRouteEvaluationAppSettings", "ReplayRouteEvaluationSettings"]
