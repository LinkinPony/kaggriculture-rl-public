"""Immutable ranked-source catalog and fixed-quantity BC preparation settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field

from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.config import default_environment
from kagg_revue.policy.settings import GeometrySettings, ModelSettings


class Preparation(FrozenSettings):
    """Bind ranking evidence, public downloads and deterministic seed partitions."""

    output_dir: Path
    daily_manifest: Path
    public_manifest: Path
    leaderboard_snapshots: tuple[Path, ...]
    report_dir: Path
    frame_audit: Path | None = None
    maximum_rank: int = Field(default=10, gt=0)
    partition: Literal["episode-seed"] = "episode-seed"
    partition_seed: int = Field(default=62001, ge=0)
    workers: int = Field(default=12, gt=0)
    episodes_per_shard: int = Field(default=8, gt=0)
    quantity_max: int = Field(default=100, gt=0)
    module_version: Literal["1.32.7"] = "1.32.7"
    maximum_excluded_row_fraction: float = Field(default=0.05, ge=0, lt=1)
    environment: dict[str, int | float] = Field(default_factory=default_environment)

    def geometry(self) -> GeometrySettings:
        """Keep the mainline grounded-v2 feature interface and quantities 1..100."""
        return GeometrySettings(
            environment=self.environment,
            unit_limit=32,
            width=128,
            decision_interval=1,
            quantity_max=self.quantity_max,
            quantity_extra=(),
            model=ModelSettings(
                architecture="grounded-v2", time_prior=False, prior_scale=0, critic_depth=2
            ),
        )
