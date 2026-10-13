"""Portable CPU extension build settings shared by deployment workflows."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NativeBuildSettings(BaseModel):
    """Python interpreters and bounded parallelism for native ABI builds."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    interpreters: tuple[Path, ...]
    compiler: Path
    patchelf: Path
    max_glibc: str = Field(pattern=r"^[0-9]+(?:\.[0-9]+)+$")
    jobs: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_interpreters(self) -> NativeBuildSettings:
        """Require at least one unique Python interpreter."""
        if not self.interpreters:
            raise ValueError("native submission build needs at least one Python interpreter")
        if len(set(self.interpreters)) != len(self.interpreters):
            raise ValueError("native submission build interpreters must be unique")
        return self
