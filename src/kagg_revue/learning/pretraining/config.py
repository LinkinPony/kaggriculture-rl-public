"""Explicit supervised budgets and authenticated optional starting weights."""

import math
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from kagg_revue.configuration import FrozenSettings


class LossWeights(FrozenSettings):
    """Relative weights of the five conditional action domains."""

    unit_target: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    unit_operation: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    unit_quantity: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    market_operation: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    market_quantity: float = Field(default=1.0, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_total(self) -> "LossWeights":
        """Reject disabled objectives and overflowing relative weights."""
        total = sum(self.model_dump().values())
        if not math.isfinite(total) or total <= 0:
            raise ValueError("BC loss weights require a finite, positive total")
        return self


class GroupedLoss(FrozenSettings):
    """Normalize supervised fields over the complete optimizer batch, across all ranks.

    ``domain_mean`` averages each domain and divides the weights by their sum. A
    domain absent from a batch contributes zero; its weight is not redistributed.
    ``field_mean`` treats the weights as per-field multipliers and divides by the
    weighted count of every supervised field, so a domain's share follows its
    frequency and no sparse domain is inflated.
    """

    normalization: Literal["domain_mean", "field_mean"] = "domain_mean"
    weights: LossWeights = Field(default_factory=LossWeights)


class InitialWeights(FrozenSettings):
    """Pin one registered parent checkpoint for a separate BC or PPO run."""

    run: Path
    checkpoint: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_paths(self) -> "InitialWeights":
        """Keep parent artifacts inside a named learning run."""
        member = Path(self.checkpoint)
        if (
            self.run.is_absolute()
            or ".." in self.run.parts
            or self.run.parts[:2] != ("outputs", "learning")
            or member.is_absolute()
            or ".." in member.parts
            or member.suffix != ".pt"
        ):
            raise ValueError("initial weights require a registered outputs/learning checkpoint")
        return self


class EarlyStopping(FrozenSettings):
    """Stop after consecutive epochs without a meaningful selection NLL decrease."""

    patience: int = Field(default=10, gt=0)
    min_delta: float = Field(default=0.001, ge=0, allow_inf_nan=False)


class Schedule(FrozenSettings):
    """Linear warmup, then cosine decay across the declared epochs of BC shards."""

    warmup_shards: int = Field(default=0, ge=0)
    final_fraction: float = Field(default=0.1, ge=0, le=1)

    def factor(self, cursor: int, total: int) -> float:
        """Return the rate multiplier for the shard at ``cursor`` out of ``total``."""
        if cursor < self.warmup_shards:
            return (cursor + 1) / self.warmup_shards
        progress = min(1.0, (cursor - self.warmup_shards) / max(1, total - self.warmup_shards))
        cosine = 0.5 * (1 + math.cos(math.pi * progress))
        return self.final_fraction + (1 - self.final_fraction) * cosine


class Demonstrations(FrozenSettings):
    """A fixed dataset and optimization budget before independent online RL."""

    manifest: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    epochs: int = Field(default=4, gt=0)
    batch_rows: int = Field(default=256, gt=0)
    learning_rate: float = Field(default=0.0003, gt=0)
    checkpoint_shards: int = Field(default=16, gt=0)
    epoch_checkpoint_interval: int = Field(default=1, gt=0)
    distributed: bool = False
    behavior_games: int = Field(default=0, ge=0)
    control_games: int = Field(default=0, ge=0, multiple_of=2)
    behavior_seed: int = Field(default=4200000000, ge=0)
    early_stopping: EarlyStopping | None = None
    loss: GroupedLoss | None = None
    schedule: Schedule | None = None
    # Rate for zero-started joint unit parameters; None shares ``learning_rate``.
    joint_learning_rate: float | None = Field(default=None, gt=0)

    def rates(self, cursor: int, total: int) -> tuple[float, float]:
        """Return the base and joint-unit rates for the shard at ``cursor``."""
        factor = 1.0 if self.schedule is None else self.schedule.factor(cursor, total)
        joint = self.learning_rate if self.joint_learning_rate is None else self.joint_learning_rate
        return self.learning_rate * factor, joint * factor

    @model_validator(mode="after")
    def validate_source(self) -> "Demonstrations":
        """Keep reusable datasets in the declared persistent source namespace."""
        if (
            self.manifest.is_absolute()
            or ".." in self.manifest.parts
            or not (
                self.manifest.parts[:2] == ("data", "external")
                or self.manifest.parts[:1] == ("outputs",)
            )
            or self.manifest.name != "manifest.json"
        ):
            raise ValueError("demonstration manifests belong under data/external or outputs")
        return self
