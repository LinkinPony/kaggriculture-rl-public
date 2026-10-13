"""Small, explicit PFSP controls independent of model and optimizer settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from kagg_revue.configuration import FrozenSettings


class HistoricalSource(FrozenSettings):
    """Explicit, immutable selection of another run's frozen training opponents."""

    run: Path
    state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    checkpoints: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_paths(self) -> "HistoricalSource":
        """Restrict imports to an authenticated root, PPO checkpoint or BC endpoint."""
        if (
            self.run.is_absolute()
            or ".." in self.run.parts
            or self.run.parts[:2] != ("outputs", "learning")
        ):
            raise ValueError("historical sources require an outputs/learning run")
        if len(set(self.checkpoints)) != len(self.checkpoints):
            raise ValueError("historical checkpoints must be unique")
        for name in self.checkpoints:
            if name == "initial.pt":
                continue
            path = Path(name)
            if (
                len(path.parts) != 2
                or not (
                    (
                        path.parts[0] == "checkpoints"
                        and path.stem.startswith("update-")
                        and path.stem.removeprefix("update-").isdigit()
                    )
                    or (
                        path.parts[0] == "pretraining"
                        and path.stem.startswith("shard-")
                        and path.stem.removeprefix("shard-").isdigit()
                    )
                )
                or path.suffix != ".pt"
            ):
                raise ValueError(
                    "historical sources must name retained roots or PPO/BC checkpoints"
                )
        return self


class Mastery(FrozenSettings):
    """Reserve a small shared review budget for reliably beaten opponents."""

    min_games: int = Field(default=64, gt=0)
    score_threshold: float = Field(default=0.95, gt=0.5, le=1)
    review_fraction: float = Field(default=0.05, gt=0, lt=1)


class Inheritance(FrozenSettings):
    """Seed a new learner's PFSP evidence from predecessor ledgers.

    The k-th predecessor's decayed evidence counts ``discount ** k`` games per
    observed game. Only opponents the learner has not met are seeded.
    """

    discount: float = Field(default=0.5, gt=0, le=1)


class Pfsp(FrozenSettings):
    """Mix loss-prioritized sampling with exploration and recent-policy coverage."""

    power: float = Field(default=2.0, gt=0, le=4)
    uniform_fraction: float = Field(default=0.2, gt=0, le=1)
    latest_fraction: float = Field(default=0.1, ge=0, lt=1)
    prior_games: float = Field(default=8.0, gt=0)
    half_life_updates: float = Field(default=128.0, gt=0)
    max_effective_games: float = Field(default=256.0, gt=0)
    script_min_pairs_per_rank: int = Field(default=1, ge=1)
    recent_snapshots: int = Field(default=4, ge=1)
    concurrent_inference: bool = True
    script_sampling: Literal["pfsp", "independent_pfsp"] = "pfsp"
    mastery: Mastery | None = None
    inheritance: Inheritance | None = None

    @model_validator(mode="after")
    def validate_mixture(self) -> "Pfsp":
        """Reserve nonnegative probability mass for loss-prioritized history."""
        if self.uniform_fraction + self.latest_fraction > 1:
            raise ValueError("PFSP exploration and latest fractions must sum to at most one")
        return self
