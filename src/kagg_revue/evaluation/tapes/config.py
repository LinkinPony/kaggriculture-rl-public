"""Settings for replaying recorded strong-team actions against deployed packages."""

from pathlib import Path

from pydantic import Field

from kagg_revue.configuration import FrozenSettings


class Candidate(FrozenSettings):
    """One exact deployment package, loaded only inside its own interpreter."""

    label: str
    package: Path
    submission: int | None = None


class Tapes(FrozenSettings):
    """Recorded strong-team versions frozen from the watched collectors."""

    manifests: tuple[Path, ...]
    submissions: tuple[int, ...]
    games_per_submission: int = Field(ge=1)
    salt: str = "tapes-20260929"


class Study(FrozenSettings):
    """Every candidate replaces the opponent seat of the same recorded games."""

    output: Path
    engine: Path
    tapes: Tapes
    candidates: tuple[Candidate, ...]
    workers: int = Field(default=40, ge=1, le=48)
    chunk: int = Field(default=6, ge=1)
    task_timeout: int = Field(default=3600, ge=60)
    checkpoints: tuple[int, ...] = (120, 240, 360, 480, 600, 719)
    bootstrap: int = Field(default=4096, ge=100)
    baseline: str | None = None
