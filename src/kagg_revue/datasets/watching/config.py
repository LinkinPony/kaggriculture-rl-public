"""Validated controls for a persistent public replay collector."""

from pathlib import Path

from pydantic import AwareDatetime, Field, field_validator, model_validator

from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.exclusions import EXCLUDED_SUBMISSIONS


class WatchSettings(FrozenSettings):
    """Track a stable team identity and keep every discovered public episode."""

    raw: Path
    team_id: int = Field(gt=0)
    team_name: str
    seed_submissions: tuple[int, ...] = ()
    seed_episodes: tuple[int, ...] = ()
    excluded_submissions: tuple[int, ...] = tuple(sorted(EXCLUDED_SUBMISSIONS))
    submitted_since: AwareDatetime | None = None
    daily_archive_root: Path | None = None
    scan_own_history: bool = True
    history_sources: tuple[Path, ...] = ()
    own_history_interval_seconds: float = Field(default=3600, gt=0)
    poll_seconds: float = Field(default=600, gt=0)
    cycle_timeout_seconds: float = Field(default=1800, gt=0)
    workers: int = Field(default=2, gt=0)
    request_interval: float = Field(default=1.5, gt=0)
    maximum_backoffs: int = Field(default=2, ge=0)
    downloads_per_cycle: int = Field(default=200, gt=0)
    once: bool = False

    @field_validator("excluded_submissions")
    @classmethod
    def include_retirements(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        """Old configuration overrides cannot reactivate retired submissions."""
        return tuple(sorted(set(value) | EXCLUDED_SUBMISSIONS))

    @model_validator(mode="after")
    def validate_exclusions(self) -> "WatchSettings":
        """Reject invalid IDs and contradictory explicit seed selections."""
        if any(key <= 0 for key in self.excluded_submissions):
            raise ValueError("excluded submission IDs must be positive")
        if set(self.seed_submissions) & set(self.excluded_submissions):
            raise ValueError("a seed submission cannot also be excluded")
        return self
