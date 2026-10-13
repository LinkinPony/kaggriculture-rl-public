"""Immutable daily sources and model-independent demonstration preparation controls."""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.config import default_environment
from kagg_revue.policy.settings import GeometrySettings, ModelSettings


class Source(FrozenSettings):
    """An exact raw archive, assigned wholly to one date-based data partition."""

    archive: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    split: Literal["train", "selection", "confirmation"]


class Preparation(FrozenSettings):
    """Derive labels from raw frames without loading a model or a script teacher."""

    output_dir: Path
    sources: tuple[Source, ...]
    architecture: Literal["grounded-v1", "grounded-v2"] = "grounded-v1"
    partition: Literal["dates", "episode-seed"] = "dates"
    partition_seed: int = Field(default=62001, ge=0)
    unit_limit: int = Field(default=32, gt=0, le=32)
    workers: int = Field(default=12, gt=0)
    episodes_per_shard: int = Field(default=8, gt=0)
    maximum_episodes_per_source: int | None = Field(default=None, gt=0)
    module_version: str = "1.32.7"
    environment: dict[str, int | float] = Field(default_factory=default_environment)
    # Exact small quantities plus broad exploration symbols. Additional symbols
    # are learned only from the training partition's literal request vocabulary.
    quantity_max: int = Field(default=128, gt=0)
    quantity_extra: tuple[int, ...] = (256, 512, 1024, 4096, 10000, 1000000)
    quantity_encoding: Literal["exact", "clip"] = "exact"
    maximum_excluded_row_fraction: float = Field(default=0.05, ge=0, lt=1)

    @model_validator(mode="after")
    def validate_sources(self) -> "Preparation":
        """Keep date roles separate and reusable datasets under data/external."""
        if self.quantity_encoding == "clip" and self.quantity_extra:
            raise ValueError("clipped quantities require a contiguous vocabulary without extras")
        if not self.sources or len({s.date for s in self.sources}) != len(self.sources):
            raise ValueError("demonstrations require distinct source dates")
        if self.partition == "dates" and not {"train", "selection"} <= {
            s.split for s in self.sources
        }:
            raise ValueError("demonstrations require separate training and selection dates")
        roles = {"train": 0, "selection": 1, "confirmation": 2}
        ordered = sorted(self.sources, key=lambda s: s.date)
        if any(roles[a.split] > roles[b.split] for a, b in zip(ordered, ordered[1:], strict=False)):
            raise ValueError("selection and confirmation dates must follow the training dates")
        if (
            self.output_dir.is_absolute()
            or ".." in self.output_dir.parts
            or self.output_dir.parts[:1] not in {("data",), ("outputs",)}
        ):
            raise ValueError("encoded demonstrations require a repository artifact directory")
        for path in (source.archive for source in self.sources):
            if path.is_absolute() or ".." in path.parts or path.parts[:2] != ("data", "external"):
                raise ValueError("demonstration artifacts belong under data/external")
        return self

    def geometry(self) -> GeometrySettings:
        """Describe reusable tensors without constructing an actor or PPO profile."""
        return GeometrySettings(
            environment=self.environment,
            unit_limit=self.unit_limit,
            width=128,
            decision_interval=1,
            quantity_max=self.quantity_max,
            quantity_extra=self.quantity_extra,
            model=ModelSettings(
                architecture=self.architecture, time_prior=False, prior_scale=0, critic_depth=2
            ),
        )
