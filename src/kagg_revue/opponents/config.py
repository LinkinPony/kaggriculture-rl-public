"""Validated settings for public-notebook opponent benchmarks."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OpponentBenchmarkSettings(BaseModel):
    """One immutable paired-seat benchmark of frozen notebook artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    public_agent_manifest: Path
    output_dir: Path
    agent_ids: tuple[str, ...]
    anchor_id: str | None = None
    seeds: tuple[int, ...]
    workers: int = Field(gt=0, le=64)
    engine: Literal["native", "official"]
    paired_seats: Literal[True]
    act_timeout_seconds: float = Field(gt=0.0)
    remaining_overage_seconds: float = Field(ge=0.0)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_benchmark(self) -> OpponentBenchmarkSettings:
        """Reject ambiguous panels and non-complete match configurations."""
        if len(self.agent_ids) < 2:
            raise ValueError("opponent benchmark needs at least two agents")
        if len(set(self.agent_ids)) != len(self.agent_ids):
            raise ValueError("opponent benchmark agent identities must be unique")
        if any(not agent_id for agent_id in self.agent_ids):
            raise ValueError("opponent benchmark agent identities cannot be empty")
        if self.anchor_id is not None and self.anchor_id not in self.agent_ids:
            raise ValueError("opponent benchmark anchor must be in agent_ids")
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("opponent benchmark seeds must be nonempty and unique")
        if any(seed < 0 for seed in self.seeds):
            raise ValueError("opponent benchmark seeds must be nonnegative")
        episode_steps = self.environment.get("episodeSteps")
        market_orders = self.environment.get("maxMarketOrdersPerTurn")
        if not isinstance(episode_steps, int) or isinstance(episode_steps, bool):
            raise ValueError("environment episodeSteps must be an integer")
        if episode_steps < 2:
            raise ValueError("environment episodeSteps must allow a transition")
        if not isinstance(market_orders, int) or isinstance(market_orders, bool):
            raise ValueError("environment maxMarketOrdersPerTurn must be an integer")
        if market_orders < 1:
            raise ValueError("environment maxMarketOrdersPerTurn must be positive")
        return self


class OpponentBenchmarkAppSettings(BaseModel):
    """Hydra root for the notebook-opponent benchmark command."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    benchmark: OpponentBenchmarkSettings


__all__ = ["OpponentBenchmarkAppSettings", "OpponentBenchmarkSettings"]
