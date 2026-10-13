"""Validated Hydra settings for the unit-task-tape challenger."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _repository_path(path: Path, root: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != root:
        raise ValueError(f"{name} must be repository-relative under {root}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


class TaskAbiSettings(BaseModel):
    """Runtime capacities used to ask native C++ for the measured ABI."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    unit_limit: int = Field(gt=0)
    maximum_quantity: int = Field(gt=0)


class TaskModelSettings(BaseModel):
    """Trainable task-prefix and pointer widths."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    architecture_version: Literal[
        "attention-v1", "pooled-v2", "factorized-v3"
    ] = "attention-v1"
    model_width: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    attention_heads: int = Field(gt=0)
    prefix_layers: int = Field(gt=0)
    history_window: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_attention(self) -> TaskModelSettings:
        """Require an integral task attention head width."""
        if self.model_width % self.attention_heads:
            raise ValueError("task model width must divide into attention heads")
        return self


class TaskObjectiveSettings(BaseModel):
    """Direct competition reward and undiscounted credit semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reward: Literal["terminal_wdl"]
    discount: float = Field(allow_inf_nan=False)
    gae_lambda: float = Field(allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_terminal_wdl(self) -> TaskObjectiveSettings:
        """Disallow proxy rewards, discounting, and bootstrapped shaping."""
        if self.discount != 1.0 or self.gae_lambda != 1.0:
            raise ValueError("unit-task terminal W/D/L requires gamma=lambda=1")
        return self


class TaskOptimizationSettings(BaseModel):
    """PPO optimization for task and market factors."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ppo_epochs: int = Field(gt=0)
    episodes_per_minibatch: int = Field(gt=0)
    episodes_per_microbatch: int | None = Field(default=None, gt=0)
    learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    weight_decay: float = Field(ge=0.0, allow_inf_nan=False)
    clip_epsilon: float = Field(gt=0.0, lt=1.0, allow_inf_nan=False)
    task_value_loss_weight: float = Field(ge=0.0, allow_inf_nan=False)
    market_value_loss_weight: float = Field(ge=0.0, allow_inf_nan=False)
    task_entropy_weight: float = Field(ge=0.0, allow_inf_nan=False)
    market_entropy_weight: float = Field(ge=0.0, allow_inf_nan=False)
    gradient_clip: float = Field(gt=0.0, allow_inf_nan=False)
    target_kl: float = Field(gt=0.0, allow_inf_nan=False)
    normalize_advantage: bool

    @model_validator(mode="after")
    def validate_microbatch(self) -> TaskOptimizationSettings:
        """Require physical microbatches to preserve each logical PPO batch."""
        microbatch = self.episodes_per_microbatch or self.episodes_per_minibatch
        if microbatch > self.episodes_per_minibatch:
            raise ValueError("PPO microbatch cannot exceed its logical minibatch")
        if self.episodes_per_minibatch % microbatch:
            raise ValueError("PPO logical minibatch must divide into microbatches")
        return self

    @property
    def effective_episodes_per_microbatch(self) -> int:
        """Return the physical episode count used for one forward/backward."""
        return self.episodes_per_microbatch or self.episodes_per_minibatch


class TaskRolloutSettings(BaseModel):
    """Bounded paired-seat official-match collection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seeds_per_update: int = Field(gt=0)
    batch_games: int = Field(gt=0)
    cpu_workers: int = Field(gt=0)
    actor_streams: int = Field(gt=0)
    host_memory_limit_gib: float = Field(gt=0.0, allow_inf_nan=False)
    gpu_memory_fraction: float = Field(gt=0.0, le=0.9, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_pairs(self) -> TaskRolloutSettings:
        """Keep every rollout shard divisible into paired seats."""
        if self.batch_games % 2:
            raise ValueError("unit-task rollout batch_games must be even")
        return self


class TaskCheckpointSettings(BaseModel):
    """Recoverable and permanent checkpoint cadence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rolling_interval: int = Field(gt=0)
    rolling_keep: int = Field(gt=0)
    permanent_interval: int = Field(gt=0)


class TaskIncumbentSettings(BaseModel):
    """Identity of the named policy that a challenger must defeat."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["event_route_ppo"]
    checkpoint: Path
    checkpoint_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prior_logit: float = Field(gt=0.0, allow_inf_nan=False)
    unit_limit: int = Field(gt=0)
    confirmation_report: Path
    confirmation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    runtime_audit_report: Path
    runtime_audit_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class TaskRlSettings(BaseModel):
    """One reproducible closed-loop unit-task PPO challenger."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    initial_actor: Path | None = None
    initial_task_checkpoint: Path | None = None
    initial_task_checkpoint_sha256: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{64}$",
    )
    initial_optimizer: Literal["reset", "import"] = "reset"
    resume_checkpoint: Path | None = None
    public_agent_manifest: Path
    output_dir: Path
    seed: int = Field(ge=0)
    rollout_seed_start: int = Field(ge=0)
    updates: int = Field(gt=0)
    opponents: tuple[str, ...]
    opponent_weights: dict[str, float]
    paired_seats: Literal[True]
    evaluation_opponents: tuple[str, ...]
    selection_seeds: tuple[int, ...]
    confirmation_seeds: tuple[int, ...]
    abi: TaskAbiSettings
    model: TaskModelSettings
    objective: TaskObjectiveSettings
    optimization: TaskOptimizationSettings
    rollout: TaskRolloutSettings
    checkpoint: TaskCheckpointSettings
    incumbent: TaskIncumbentSettings
    device: str
    training_devices: tuple[str, ...]
    cuda_allocator_expandable_segments: bool
    cpu_threads: int = Field(gt=0)
    act_timeout_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    remaining_overage_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_experiment(self) -> TaskRlSettings:
        """Bind artifacts, opponent ladder, seeds, and official time semantics."""
        if self.initial_actor is not None:
            _repository_path(self.initial_actor, "outputs", "initial_actor")
        if self.initial_actor is None and self.initial_task_checkpoint is None:
            raise ValueError(
                "unit-task initialization needs an actor or a complete task checkpoint"
            )
        if (self.initial_task_checkpoint is None) != (self.initial_task_checkpoint_sha256 is None):
            raise ValueError("initial_task_checkpoint and its sha256 must be configured together")
        if self.initial_optimizer == "import" and self.initial_task_checkpoint is None:
            raise ValueError("initial optimizer import requires a task checkpoint")
        if self.initial_task_checkpoint is not None:
            _repository_path(
                self.initial_task_checkpoint,
                "outputs",
                "initial_task_checkpoint",
            )
        _repository_path(self.public_agent_manifest, "data", "public_agent_manifest")
        if self.public_agent_manifest.parts[:2] != ("data", "external"):
            raise ValueError("public_agent_manifest must remain under data/external/")
        _repository_path(self.output_dir, "outputs", "output_dir")
        if self.resume_checkpoint is not None:
            _repository_path(self.resume_checkpoint, "outputs", "resume_checkpoint")
        for path, name in (
            (self.incumbent.checkpoint, "incumbent checkpoint"),
            (self.incumbent.confirmation_report, "incumbent confirmation report"),
            (self.incumbent.runtime_audit_report, "incumbent runtime audit report"),
        ):
            _repository_path(path, "outputs", name)
        if not self.opponents or len(set(self.opponents)) != len(self.opponents):
            raise ValueError("unit-task opponent ladder must be nonempty and unique")
        if "frozen_initial_actor" in self.opponents and self.initial_actor is None:
            raise ValueError(
                "frozen initial actor rollout requires an actor-only artifact"
            )
        if tuple(self.opponent_weights) != self.opponents:
            raise ValueError("unit-task opponent weights must follow opponent order")
        weights = tuple(self.opponent_weights.values())
        if any(not math.isfinite(weight) or weight <= 0.0 for weight in weights):
            raise ValueError("unit-task opponent weights must be finite and positive")
        if not math.isclose(math.fsum(weights), 1.0, abs_tol=1e-9):
            raise ValueError("unit-task opponent weights must sum to one")
        if (
            not self.evaluation_opponents
            or len(set(self.evaluation_opponents)) != len(self.evaluation_opponents)
        ):
            raise ValueError(
                "unit-task evaluation opponent population must be nonempty and unique"
            )
        if any(not opponent for opponent in self.evaluation_opponents):
            raise ValueError("unit-task evaluation opponent identities cannot be empty")
        if "self_play" in self.evaluation_opponents:
            raise ValueError(
                "unit-task held-out evaluation requires frozen external opponents"
            )
        if not self.selection_seeds or not self.confirmation_seeds:
            raise ValueError("unit-task evaluation seed panels cannot be empty")
        if set(self.selection_seeds) & set(self.confirmation_seeds):
            raise ValueError("unit-task selection and confirmation seeds must be disjoint")
        if self.act_timeout_seconds != 1.0 or self.remaining_overage_seconds != 60.0:
            raise ValueError("unit-task deployment budget must match official semantics")
        if (
            not self.training_devices
            or len(set(self.training_devices)) != len(self.training_devices)
            or self.device != self.training_devices[0]
        ):
            raise ValueError("unit-task training devices must be unique and start with device")
        if len(self.training_devices) > 1:
            for device_value in self.training_devices:
                parsed = device_value.split(":", maxsplit=1)
                if len(parsed) != 2 or parsed[0] != "cuda" or not parsed[1].isdigit():
                    raise ValueError("distributed unit-task training requires indexed CUDA devices")
        world_size = len(self.training_devices)
        for capacity, name in (
            (self.rollout.seeds_per_update, "rollout seeds"),
            (self.rollout.batch_games, "rollout batch games"),
            (self.rollout.cpu_workers, "rollout CPU workers"),
            (self.rollout.actor_streams, "rollout actor streams"),
        ):
            if capacity % world_size:
                raise ValueError(f"unit-task {name} must divide across devices")
        training_episodes = 2 * self.rollout.seeds_per_update
        distributed_minibatch = self.optimization.episodes_per_minibatch * world_size
        if training_episodes % distributed_minibatch:
            raise ValueError(
                "unit-task paired rollout episodes must divide into distributed PPO minibatches"
            )
        local_episodes = training_episodes // world_size
        local_batch_games = self.rollout.batch_games // world_size
        local_streams = self.rollout.actor_streams // world_size
        if local_episodes % local_batch_games:
            raise ValueError("unit-task rank-local episodes must divide into rollout batches")
        if local_episodes // local_batch_games < local_streams:
            raise ValueError("unit-task rollout needs at least one resident batch per actor stream")
        episode_steps = self.environment.get("episodeSteps")
        market_orders = self.environment.get("maxMarketOrdersPerTurn")
        if (
            not isinstance(episode_steps, int)
            or isinstance(episode_steps, bool)
            or episode_steps < 2
        ):
            raise ValueError("unit-task environment episodeSteps must allow a transition")
        if (
            not isinstance(market_orders, int)
            or isinstance(market_orders, bool)
            or market_orders < 1
        ):
            raise ValueError("unit-task environment market order capacity must be positive")
        return self


class TaskRlAppSettings(BaseModel):
    """Hydra root object for one selected unit-task profile."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    unit_task_rl: TaskRlSettings


__all__ = [
    "TaskAbiSettings",
    "TaskCheckpointSettings",
    "TaskIncumbentSettings",
    "TaskModelSettings",
    "TaskObjectiveSettings",
    "TaskOptimizationSettings",
    "TaskRlAppSettings",
    "TaskRlSettings",
    "TaskRolloutSettings",
]
