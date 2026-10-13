"""Validated settings for the local monitoring service."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class MonitorSettings(BaseModel):
    """Runtime settings whose network surface is always loopback-only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outputs_dir: Path
    port: int = Field(ge=1024, le=65535)
    refresh_seconds: int = Field(ge=2, le=60)
    stale_after_seconds: int = Field(ge=30)
    max_points: int = Field(ge=50, le=2_000)
    recent_points: int = Field(default=2000, ge=500, le=5000)
    history_cache_runs: int = Field(default=2, ge=1, le=8)
    default_window: int = Field(default=500, ge=1, le=1000000)
    smoothing_window: int = Field(default=32, ge=1, le=2048)
    show_raw: bool = False
    tensorboard_port: int | None = Field(default=None, ge=1024, le=65535)


__all__ = ["MonitorSettings"]
