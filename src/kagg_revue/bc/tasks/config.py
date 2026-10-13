"""Validated Hydra settings for unit-task behavior cloning."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.bc.config import ModelSettings
from kagg_revue.bc.data_config import ReplayContract
from kagg_revue.rl.tasks.config import TaskAbiSettings, TaskModelSettings


def _repository_path(path: Path, root: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != root:
        raise ValueError(f"{name} must be repository-relative under {root}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


class TaskBcSourceSettings(BaseModel):
    """Authenticated daily archives and whole-population partitioning."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    index_archive: Path
    source_archives: tuple[Path, ...]
    days: int = Field(gt=0)
    validation_fraction: float = Field(gt=0.0, lt=0.5, allow_inf_nan=False)
    test_fraction: float = Field(gt=0.0, lt=0.5, allow_inf_nan=False)
    workers: int = Field(gt=0)
    worker_cpu_threads: int = Field(gt=0)
    maximum_rejection_fraction: float = Field(ge=0.0, lt=1.0)
    contract: ReplayContract

    @model_validator(mode="after")
    def validate_selection(self) -> TaskBcSourceSettings:
        """Require complete archives and disjoint population partitions."""
        if len(self.source_archives) != self.days:
            raise ValueError("task BC needs one archive for every requested day")
        if len(set(self.source_archives)) != len(self.source_archives):
            raise ValueError("task BC source archives must be unique")
        if self.validation_fraction + self.test_fraction >= 0.5:
            raise ValueError("task BC held-out partitions consume too much data")
        return self


class TaskBcSamplingSettings(BaseModel):
    """Lossless rolling-tape translation and unbiased decision subsampling."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tasks_per_suffix: Literal[2]
    decisions_per_sequence: int = Field(gt=0)
    seed: int = Field(ge=0)


class TaskBcOptimizationSettings(BaseModel):
    """End-to-end policy BC followed by W/D/L-head calibration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    epochs: int = Field(gt=0)
    outcome_epochs: int = Field(gt=0)
    policy_early_stopping_patience: int = Field(gt=0)
    outcome_early_stopping_patience: int = Field(gt=0)
    early_stopping_minimum_relative_improvement: float = Field(
        gt=0.0,
        lt=1.0,
        allow_inf_nan=False,
    )
    batch_sequences: int = Field(gt=0)
    learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    outcome_learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    weight_decay: float = Field(ge=0.0, allow_inf_nan=False)
    task_loss_weight: float = Field(gt=0.0, allow_inf_nan=False)
    market_loss_weight: float = Field(gt=0.0, allow_inf_nan=False)
    quantity_loss_weight: float = Field(ge=0.0, allow_inf_nan=False)
    gradient_clip: float = Field(gt=0.0, allow_inf_nan=False)
    seed: int = Field(ge=0)
    device: str = Field(min_length=1)
    cpu_threads: int = Field(gt=0)
    loader_workers: int = Field(gt=0)
    prefetch_shards: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_loader(self) -> TaskBcOptimizationSettings:
        """Keep decompression parallelism bounded and fully occupied."""
        if self.prefetch_shards < self.loader_workers:
            raise ValueError("task BC prefetch depth must cover every loader worker")
        return self


class TaskBcEvaluationSettings(BaseModel):
    """Small direct-outcome panel used to diagnose the BC checkpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool
    public_agent_manifest: Path
    opponents: tuple[str, ...]
    seeds: tuple[int, ...]
    device: str = Field(min_length=1)
    cpu_threads: int = Field(gt=0)
    batch_games: int = Field(gt=0)
    actor_streams: int = Field(gt=0)
    smoke_transitions: int = Field(gt=0)
    act_timeout_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    remaining_overage_seconds: float = Field(ge=0.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_panel(self) -> TaskBcEvaluationSettings:
        """Keep the diagnostic panel deployable and nonempty when enabled."""
        if self.enabled and (not self.opponents or not self.seeds):
            raise ValueError("enabled task BC evaluation needs opponents and seeds")
        if len(set(self.opponents)) != len(self.opponents):
            raise ValueError("task BC evaluation opponents must be unique")
        if self.batch_games % 2:
            raise ValueError("task BC GPU evaluation batch must preserve seat pairs")
        if self.enabled and not self.device.startswith("cuda"):
            raise ValueError("task BC heavy evaluation must use the GPU batch path")
        if self.act_timeout_seconds != 1.0 or self.remaining_overage_seconds != 60.0:
            raise ValueError("task BC evaluation must use official action-time semantics")
        return self


class TaskBcSettings(BaseModel):
    """One provenance-bound unit-task BC data and training run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_dir: Path
    output_dir: Path
    resume_policy_checkpoint: Path | None = None
    source: TaskBcSourceSettings
    sampling: TaskBcSamplingSettings
    abi: TaskAbiSettings
    actor: ModelSettings
    model: TaskModelSettings
    optimization: TaskBcOptimizationSettings
    evaluation: TaskBcEvaluationSettings
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_paths(self) -> TaskBcSettings:
        """Keep reusable data and generated run artifacts in their namespaces."""
        _repository_path(self.dataset_dir, "data", "dataset_dir")
        if self.dataset_dir.parts[:2] != ("data", "external"):
            raise ValueError("task BC dataset must remain under data/external/")
        _repository_path(self.output_dir, "outputs", "output_dir")
        if self.resume_policy_checkpoint is not None:
            _repository_path(
                self.resume_policy_checkpoint,
                "outputs",
                "resume_policy_checkpoint",
            )
            if self.resume_policy_checkpoint.parent != self.output_dir / "checkpoints":
                raise ValueError(
                    "task BC policy continuation must use this run's checkpoint"
                )
        _repository_path(
            self.evaluation.public_agent_manifest,
            "data",
            "public_agent_manifest",
        )
        for path in (self.source.index_archive, *self.source.source_archives):
            _repository_path(path, "data", "source archive")
            if path.parts[:2] != ("data", "external"):
                raise ValueError("task BC sources must remain under data/external/")
        episode_steps = self.environment.get("episodeSteps")
        market_orders = self.environment.get("maxMarketOrdersPerTurn")
        if not isinstance(episode_steps, int) or isinstance(episode_steps, bool):
            raise ValueError("task BC environment lacks episodeSteps")
        if not isinstance(market_orders, int) or isinstance(market_orders, bool):
            raise ValueError("task BC environment lacks maxMarketOrdersPerTurn")
        if self.evaluation.smoke_transitions >= episode_steps:
            raise ValueError("task BC official smoke must stop before episode completion")
        if self.actor.max_history < episode_steps:
            raise ValueError("scratch actor history must cover the complete episode")
        if self.actor.max_decisions < self.abi.unit_limit + market_orders:
            raise ValueError("scratch actor cannot hold unit and market decisions")
        if self.actor.maximum_quantity != self.abi.maximum_quantity:
            raise ValueError("scratch actor and task policy quantities differ")
        if self.actor.skill_tokens:
            raise ValueError("scratch task BC requires deterministic shared context")
        return self


class TaskBcAppSettings(BaseModel):
    """Hydra root for unit-task behavior cloning."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    unit_task_bc: TaskBcSettings


__all__ = [
    "TaskBcAppSettings",
    "TaskBcEvaluationSettings",
    "TaskBcOptimizationSettings",
    "TaskBcSamplingSettings",
    "TaskBcSettings",
    "TaskBcSourceSettings",
]
