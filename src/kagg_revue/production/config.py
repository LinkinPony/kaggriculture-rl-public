"""Legacy BC and production workflows layered over shared runtime settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from kagg_revue.configuration import FrozenSettings as FrozenSettings
from kagg_revue.learning.optimization.settings import (
    HistoricalPopulation as HistoricalPopulation,
)
from kagg_revue.learning.optimization.settings import (
    OptimizationSettings as OptimizationSettings,
)
from kagg_revue.learning.optimization.settings import (
    TemperatureSchedule as TemperatureSchedule,
)
from kagg_revue.learning.optimization.settings import (
    UpdateProtection as UpdateProtection,
)
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.settings import ModelSettings as ModelSettings


class ImitationSettings(FrozenSettings):
    """Streaming demonstration generation and BC optimization."""

    directory: Path
    source: Path
    games: int = Field(gt=0)
    shard_games: int = Field(gt=0)
    seed_start: int = Field(ge=0)
    epochs: int = Field(ge=0)
    batch_rows: int = Field(gt=0)
    learning_rate: float = Field(gt=0)
    prior_pseudocount: float = Field(gt=0)
    greedy_prior_bias: float = Field(default=0.0, ge=0)
    source_kind: Literal["teacher", "daily"] = "teacher"
    replay_module_version: str = ""
    validation_fraction: float = Field(default=0.1, gt=0, lt=0.5)
    test_fraction: float = Field(default=0.1, gt=0, lt=0.5)
    maximum_rejection_fraction: float = Field(default=0.05, ge=0, lt=1)


class RecoveryEvaluation(FrozenSettings):
    """Stop a recovery challenger on direct paired notebook regression."""

    control_checkpoint: Path
    maximum_net_regressions: int = Field(ge=0)


class Settings(RuntimeSettings):
    """One reproducible pipeline profile; benchmarks use this exact object."""

    mode: Literal[
        "generate",
        "audit",
        "bc",
        "train",
        "evaluate",
        "qualify",
        "reference",
        "transfer",
        "preflight",
    ]
    output_dir: Path
    checkpoint: Path | None = None
    checkpoint_mode: Literal["resume", "fork"] = "resume"
    recovery_evaluation: RecoveryEvaluation | None = None
    seed: int = Field(ge=0)
    cpu_threads: int = Field(gt=0)
    opponents: tuple[str, ...]
    evaluation_policies: tuple[Path, ...] = ()
    evaluation_sample: bool = False
    evaluation_seed: int = Field(ge=0)
    confirmation_seed: int = Field(ge=0)
    bc: ImitationSettings

    @model_validator(mode="after")
    def validate_profile(self) -> "Settings":
        """Validate capacity, output ownership, and disjoint seed ranges."""
        for path, prefix in (
            (self.output_dir, ("outputs",)),
            (self.bc.directory, ("data", "external")),
            (self.bc.source, ("data", "external")),
        ):
            if path.is_absolute() or ".." in path.parts or path.parts[: len(prefix)] != prefix:
                raise ValueError("pipeline artifacts must stay in their repository directories")
        if self.checkpoint_mode == "fork" and self.checkpoint is None:
            raise ValueError("a training fork requires an explicit full checkpoint")
        if self.recovery_evaluation is not None and (
            self.checkpoint is None or not self.ppo.evaluation_interval
        ):
            raise ValueError("recovery evaluation requires a checkpoint and periodic panels")
        supported = {"kaito_v48", "kaito_v39", "boatlee_v21", "mugundh_v21"}
        if not set(self.ppo.script_opponents) <= supported:
            raise ValueError("script opponent lacks an authenticated native implementation")
        if self.bc.games % 2 or self.bc.shard_games % 2:
            raise ValueError("BC shards must contain complete seat pairs")
        if self.bc.source_kind == "daily" and (
            not self.bc.replay_module_version
            or self.model.architecture != "work-v1"
            or self.model.time_prior
        ):
            raise ValueError(
                "daily BC requires a replay version and a work actor without time prior"
            )
        panel_size = len(self.opponents) + len(self.evaluation_policies)
        if not panel_size or self.evaluation_games % (2 * panel_size):
            raise ValueError("evaluation must balance every opponent and both seats")
        if len(set(self.evaluation_policies)) != len(self.evaluation_policies):
            raise ValueError("evaluation policy paths must be unique")
        spans = [
            (self.bc.seed_start, self.bc.seed_start + (self.bc.games + 1) // 2),
            (
                self.ppo.seed_start,
                self.ppo.seed_start + self.ppo.games_per_update * self.ppo.updates,
            ),
            (self.evaluation_seed, self.evaluation_seed + self.evaluation_games // 2),
            (self.confirmation_seed, self.confirmation_seed + self.evaluation_games // 2),
        ]
        ordered = sorted(spans)
        if any(left[1] > right[0] for left, right in zip(ordered, ordered[1:], strict=False)):
            raise ValueError("BC, training, selection and confirmation seeds must be disjoint")
        return self
