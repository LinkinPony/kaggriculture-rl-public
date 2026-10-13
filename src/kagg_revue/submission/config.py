"""Validated settings for one immutable Kaggle submission candidate."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from kagg_revue.native.settings import NativeBuildSettings as NativeBuildSettings


class SmokeSettings(BaseModel):
    """Official runtime contract used for exact-archive smoke checks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seed: int = Field(ge=0)
    act_timeout_seconds: float = Field(gt=0.0)
    remaining_overage_seconds: float = Field(ge=0.0)
    run_timeout_seconds: float = Field(gt=0.0)


class SubmissionSettings(BaseModel):
    """Inputs and output identity for one actor snapshot and package."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    training_run: Path
    source_snapshot: Path | None = None
    output_dir: Path
    unit_limit: int = Field(gt=0)
    cpu_threads: int = Field(gt=0)
    native: NativeBuildSettings
    smoke: SmokeSettings


class SubmissionAppSettings(BaseModel):
    """Hydra root for submission commands."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    submission: SubmissionSettings


__all__ = [
    "NativeBuildSettings",
    "SmokeSettings",
    "SubmissionAppSettings",
    "SubmissionSettings",
]
