"""Validated artifact identity and portable CPU build controls."""

from pathlib import Path

from pydantic import Field, model_validator

from kagg_revue.configuration import FrozenSettings
from kagg_revue.native.settings import NativeBuildSettings


class Deployment(FrozenSettings):
    """Export one registered member, never an arbitrary historical model path."""

    run: Path
    member: str
    output_dir: Path
    native: NativeBuildSettings
    cpu_threads: int = Field(default=1, gt=0)
    sampling_seed: int = Field(default=1210000000, ge=0)
    temperature: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    liquidation: bool = False

    @model_validator(mode="after")
    def validate_paths(self) -> "Deployment":
        """Keep new-run inputs and reviewable deployment artifacts under outputs."""
        for path, prefix in (
            (self.run, ("outputs", "learning")),
            (self.output_dir, ("outputs", "deployment")),
        ):
            if path.is_absolute() or ".." in path.parts or path.parts[:2] != prefix:
                raise ValueError("deployment requires a registered run and a deployment directory")
        return self
