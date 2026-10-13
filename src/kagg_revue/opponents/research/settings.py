"""Validated research variants and declared paired-seat evaluation panels."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Variant(BaseModel):
    """One reproducible modification of an authenticated public strategy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(pattern=r"^[a-z0-9_]+$")
    base: str = "ahmed_v43"
    globals: dict[str, bool | int | float] = Field(default_factory=dict)
    opening: tuple[int, int, int] | None = None
    market: Literal["parent", "liquid", "lead", "priority"] = "parent"
    priority: bool = False
    sale_start: int = Field(default=216, ge=0, le=718)
    sale_end: int = Field(default=695, ge=0, le=718)
    lead: int = Field(default=4, ge=1, le=72)
    minimum_price: int = Field(default=2, ge=1)


class Experiment(BaseModel):
    """A fixed candidate panel evaluated without updating production training."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    manifest: Path
    output: Path
    variants: tuple[Variant, ...]
    opponents: tuple[str, ...]
    seeds: tuple[int, ...]
    workers: int = Field(default=8, ge=1, le=32)
    engine: Literal["native", "official"] = "native"
    accounting: bool = False

    @model_validator(mode="after")
    def validate_panel(self) -> "Experiment":
        """Reject empty panels and accidental duplicated experimental units."""
        if not self.variants or not self.opponents or not self.seeds:
            raise ValueError("variants, opponents and seeds must be nonempty")
        if self.engine == "official" and self.accounting:
            raise ValueError("trace accounting is available only in the native diagnostic runner")
        names = [variant.name for variant in self.variants]
        for values in (names, self.opponents, self.seeds):
            if len(values) != len(set(values)):
                raise ValueError("panel identities and seeds must be unique")
        return self
