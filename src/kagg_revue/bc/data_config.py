"""Validated Hydra settings for replay data preparation."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReplayContract(BaseModel):
    """Official replay and actor-shape invariants accepted by the converter."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    replay_schema_version: int = Field(gt=0)
    module_version: str = Field(min_length=1)
    agents: int = Field(gt=1)
    episode_steps: int = Field(gt=1)
    board_size: int = Field(gt=0)
    max_market_orders: int = Field(gt=0)
    unit_limit: int = Field(gt=0)


class OpeningDiversitySettings(BaseModel):
    """Deterministic selection of structurally distinct replay openings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    prefix_turns: int = Field(gt=0)
    training_turns: int = Field(gt=0)
    horizons: tuple[int, ...]
    maximum_episodes: int = Field(gt=0)
    maximum_identical_prefixes: int = Field(gt=0)
    seed: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_opening(self) -> OpeningDiversitySettings:
        """Require ordered multi-resolution fingerprints inside the prefix."""
        if self.training_turns < self.prefix_turns:
            raise ValueError("opening training turns must cover the fingerprint prefix")
        if not self.horizons:
            raise ValueError("opening selection needs at least one fingerprint horizon")
        if tuple(sorted(set(self.horizons))) != self.horizons:
            raise ValueError("opening fingerprint horizons must be unique and increasing")
        if self.horizons[-1] != self.prefix_turns:
            raise ValueError("the final opening fingerprint horizon must equal prefix turns")
        if self.horizons[0] < 1:
            raise ValueError("opening fingerprint horizons must be positive")
        return self


class BcDataSettings(BaseModel):
    """One immutable compact behavior-dataset build."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    index_archive: Path
    source_archives: tuple[Path, ...]
    output_dir: Path
    report_dir: Path
    days: int = Field(gt=0)
    episodes_per_shard: int = Field(gt=0)
    workers: int = Field(gt=0)
    maximum_rejection_fraction: float = Field(ge=0.0, lt=1.0)
    contract: ReplayContract
    opening_diversity: OpeningDiversitySettings | None = None

    @model_validator(mode="after")
    def validate_sources(self) -> BcDataSettings:
        """Require one archive for every requested complete UTC day."""
        if len(self.source_archives) != self.days:
            raise ValueError("source archive count must equal the requested day count")
        if len(set(self.source_archives)) != len(self.source_archives):
            raise ValueError("source archives must be unique")
        if (
            self.opening_diversity is not None
            and self.opening_diversity.training_turns >= self.contract.episode_steps
        ):
            raise ValueError("opening training prefix must end before the terminal step")
        return self


class BcDataAppSettings(BaseModel):
    """Hydra root for compact replay preparation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bc_data: BcDataSettings


__all__ = [
    "BcDataAppSettings",
    "BcDataSettings",
    "OpeningDiversitySettings",
    "ReplayContract",
]
