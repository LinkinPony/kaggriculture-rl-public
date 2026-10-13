"""Frozen data roles and balanced budgets for independent learners and native scripts."""

from itertools import combinations
from pathlib import Path
from typing import Any, Literal

import orjson
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest
from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.pretraining.config import Demonstrations

MEMBERS: tuple[Literal["a", "bc", "spataro"], ...] = ("a", "bc", "spataro")
PAIRS = ((0, 1), (0, 2), (1, 2))


class League(FrozenSettings):
    """Use independent weights, all unordered neural pairs and declared native scripts."""

    experiment: Experiment
    members: tuple[Literal["a", "bc", "spataro"], ...] = MEMBERS
    strata: Path
    strata_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bc_epochs: int = Field(default=6, gt=0)
    bc_batch_rows: int = Field(default=1024, gt=0)
    bc_learning_rate: float = Field(default=1e-4, gt=0)
    bc_checkpoint_shards: int = Field(default=8, gt=0)
    games_per_pair: int = Field(default=64, ge=0)
    selfplay_games_per_member: int = Field(default=0, ge=0)
    games_per_script_per_member: int = Field(default=0, ge=0)
    cudnn_attention: bool = False
    resume: bool = False
    stop_after_update: int | None = Field(default=None, ge=0)
    stop_after_bc_shards: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_league(self) -> "League":
        """Keep both seats balanced and avoid accidental external training opponents."""
        cfg = self.experiment
        world = len(cfg.execution.devices) if cfg.execution else 1
        if len(self.members) < 2 or len(set(self.members)) != len(self.members):
            raise ValueError("league requires distinct trainable members")
        if cfg.games != sum(count for _, _, count in self.matchups()) or any(
            count % (2 * world) for _, _, count in self.matchups()
        ):
            raise ValueError("every pair must balance both seats on every GPU")
        if cfg.population.fraction or cfg.demonstrations or cfg.curriculum:
            raise ValueError("league does not support historical policies or curriculum")
        scripts = cfg.script_population
        script_games = len(self.members) * len(self.script_names) * self.games_per_script_per_member
        if bool(scripts) != bool(self.games_per_script_per_member) or (
            scripts and abs(cfg.games * scripts.fraction - script_games) > 1e-8
        ):
            raise ValueError("script fraction must match the explicit per-member game budget")
        if cfg.architecture != "grounded-v2" or cfg.resume or self.bc_batch_rows % world:
            raise ValueError("league requires grounded-v2 and divisible distributed BC batches")
        if (
            self.strata.is_absolute()
            or ".." in self.strata.parts
            or self.strata.parts[:1] != ("outputs",)
        ):
            raise ValueError("league strata must be under outputs")
        return self

    def matchups(self) -> tuple[tuple[int, int, int], ...]:
        """Return physical games per unordered mutual pairing and per self-play model."""
        return tuple(
            (left, right, count)
            for left, right, count in (
                *(
                    (left, right, self.games_per_pair)
                    for left, right in combinations(range(len(self.members)), 2)
                ),
                *(
                    (index, index, self.selfplay_games_per_member)
                    for index in range(len(self.members))
                ),
                *(
                    (index, len(self.members) + script, self.games_per_script_per_member)
                    for index in range(len(self.members))
                    for script in range(len(self.script_names))
                ),
            )
            if count
        )

    @property
    def trajectories_per_member(self) -> int:
        """Count both learned seats in self-play and each member's mutual-play seats."""
        return (
            (len(self.members) - 1) * self.games_per_pair
            + 2 * self.selfplay_games_per_member
            + len(self.script_names) * self.games_per_script_per_member
        )

    @property
    def script_names(self) -> tuple[str, ...]:
        """Return frozen external opponents in their declared scheduling order."""
        return self.experiment.script_population.agents if self.experiment.script_population else ()

    @property
    def participants(self) -> tuple[str, ...]:
        """Map seat owners to learned policies followed by native scripts."""
        return (*self.members, *self.script_names)

    def sources(self) -> dict[str, Any]:
        """Verify the immutable role manifest before reading any member data."""
        if digest(self.strata) != self.strata_sha256:
            raise ValueError("league strata fingerprint changed")
        result: dict[str, Any] = orjson.loads(self.strata.read_bytes())
        if not set(self.members).issubset(result["views"]):
            raise ValueError("league requires a data view for each active member")
        return result

    def member(self, name: str, *, committed: Demonstrations | None = None) -> Experiment:
        """Share an initialization seed and ABI while isolating data and optimizer state."""
        if name not in self.members:
            raise ValueError("unknown league member")
        if committed is None:
            source = self.sources()["views"][name]
            manifest, fingerprint = Path(source["manifest"]), source["sha256"]
        else:
            # PPO uses the completed BC endpoint, never the original example
            # shards. Keep its archived input identity and all BC controls bound.
            manifest, fingerprint = committed.manifest, committed.sha256
            if manifest != self.strata.parent / name / "manifest.json":
                raise ValueError("committed BC input must retain its original specialist role")
        demonstrations = Demonstrations(
            manifest=manifest,
            sha256=fingerprint,
            epochs=self.bc_epochs,
            batch_rows=self.bc_batch_rows,
            learning_rate=self.bc_learning_rate,
            checkpoint_shards=self.bc_checkpoint_shards,
            distributed=bool(self.experiment.execution),
            behavior_games=0,
        )
        if committed is not None and demonstrations != committed:
            raise ValueError("committed BC controls differ from the frozen league protocol")
        return self.experiment.model_copy(
            update={
                "output_dir": self.experiment.output_dir / name,
                "demonstrations": demonstrations,
            }
        )

    def protocol(self) -> dict[str, Any]:
        """Exclude only stop and resume controls from the immutable experiment recipe."""
        result = self.model_copy(
            update={"resume": False, "stop_after_update": None, "stop_after_bc_shards": None}
        ).model_dump(mode="json")
        if not self.selfplay_games_per_member:
            result.pop("selfplay_games_per_member")  # Preserve historical mutual-only protocols.
        if self.members == MEMBERS:
            result.pop("members")
        if not self.games_per_script_per_member:
            result.pop("games_per_script_per_member")
        return result
