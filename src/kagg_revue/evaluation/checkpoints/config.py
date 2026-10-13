"""Frozen input identities and complete paired evaluation tasks."""

from pathlib import Path
from typing import Literal

from pydantic import Field

from kagg_revue.configuration import FrozenSettings


class Task(FrozenSettings):
    """One atomic batch with common environment and policy random seeds."""

    name: str
    phase: str
    candidate: str
    opponent: str
    group: str
    kind: Literal["neural", "script"]
    seed: int = Field(ge=0)
    sampling_seed: int = Field(ge=0)


class Options(FrozenSettings):
    """Bound one independent worker's memory and persist every completed batch."""

    manifest: Path
    schedule: Path
    output: Path
    device: str = "cuda:1"
    batch_games: int = Field(default=32, gt=0, multiple_of=2)
    workers: int = Field(default=4, gt=0)
    memory_fraction: float = Field(default=0.06, gt=0, le=0.08)
    precision: Literal["bf16", "fp32"] = "bf16"
    shard: int = Field(default=0, ge=0)
    shards: int = Field(default=1, gt=0)
