"""Validated Hydra settings for conditional-program PPO."""

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


class ProgramAbiSettings(BaseModel):
    """Capacity used to obtain the measured native compiler ABI."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    unit_limit: int = Field(gt=0)


class ProgramModelSettings(BaseModel):
    """Trainable conditional-language widths."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_width: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)


class ProgramObjectiveSettings(BaseModel):
    """Direct terminal competition objective."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reward: Literal["terminal_wdl"]
    discount: float = Field(allow_inf_nan=False)
    gae_lambda: float = Field(allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_terminal_wdl(self) -> ProgramObjectiveSettings:
        """Reject proxy rewards, shaping, and temporal discounting."""
        if self.discount != 1.0 or self.gae_lambda != 1.0:
            raise ValueError("conditional-program terminal W/D/L requires gamma=lambda=1")
        return self


class ProgramOptimizationSettings(BaseModel):
    """Joint-turn PPO and outcome-critic optimization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ppo_epochs: int = Field(gt=0)
    episodes_per_minibatch: int = Field(gt=0)
    episodes_per_microbatch: int | None = Field(default=None, gt=0)
    learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    weight_decay: float = Field(ge=0.0, allow_inf_nan=False)
    clip_epsilon: float = Field(gt=0.0, lt=1.0, allow_inf_nan=False)
    value_loss_weight: float = Field(ge=0.0, allow_inf_nan=False)
    entropy_weight: float = Field(ge=0.0, allow_inf_nan=False)
    gradient_clip: float = Field(gt=0.0, allow_inf_nan=False)
    target_kl: float = Field(gt=0.0, allow_inf_nan=False)
    normalize_advantage: bool

    @model_validator(mode="after")
    def validate_microbatch(self) -> ProgramOptimizationSettings:
        """Require execution shards to preserve the logical PPO batch."""
        microbatch = self.effective_episodes_per_microbatch
        if microbatch > self.episodes_per_minibatch:
            raise ValueError("PPO microbatch cannot exceed its logical minibatch")
        if self.episodes_per_minibatch % microbatch:
            raise ValueError("PPO logical minibatch must divide into microbatches")
        return self

    @property
    def effective_episodes_per_microbatch(self) -> int:
        """Return the physical episode count used for forward/backward."""
        return self.episodes_per_microbatch or self.episodes_per_minibatch


class ProgramRolloutSettings(BaseModel):
    """Bounded paired-seat native match collection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seeds_per_update: int = Field(gt=0)
    batch_games: int = Field(gt=1)
    devices: tuple[str, ...]
    cpu_workers: int = Field(gt=0)
    actor_streams: int = Field(gt=0)
    host_memory_limit_gib: float = Field(gt=0.0, allow_inf_nan=False)


class ProgramCheckpointSettings(BaseModel):
    """Recoverable and permanent checkpoint cadence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rolling_interval: int = Field(gt=0)
    rolling_keep: int = Field(gt=0)
    permanent_interval: int = Field(gt=0)


class ProgramRlSettings(BaseModel):
    """One isolated conditional-program PPO challenger."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    initial_actor: Path
    initial_checkpoint: Path | None = None
    resume_checkpoint: Path | None = None
    public_agent_manifest: Path | None = None
    output_dir: Path
    seed: int = Field(ge=0)
    rollout_seed_start: int = Field(ge=0)
    updates: int = Field(gt=0)
    opponents: tuple[str, ...]
    opponent_weights: dict[str, float]
    paired_seats: Literal[True]
    abi: ProgramAbiSettings
    model: ProgramModelSettings
    objective: ProgramObjectiveSettings
    optimization: ProgramOptimizationSettings
    rollout: ProgramRolloutSettings
    checkpoint: ProgramCheckpointSettings
    device: str
    cpu_threads: int = Field(gt=0)
    act_timeout_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    remaining_overage_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_experiment(self) -> ProgramRlSettings:
        """Bind artifact paths, paired panels, and official time semantics."""
        _repository_path(self.initial_actor, "outputs", "initial_actor")
        if self.initial_checkpoint is not None:
            _repository_path(self.initial_checkpoint, "outputs", "initial_checkpoint")
        if self.resume_checkpoint is not None:
            _repository_path(self.resume_checkpoint, "outputs", "resume_checkpoint")
        if self.initial_checkpoint is not None and self.resume_checkpoint is not None:
            raise ValueError(
                "conditional-program initial and resume checkpoints are mutually exclusive"
            )
        if self.public_agent_manifest is not None:
            _repository_path(self.public_agent_manifest, "data", "public_agent_manifest")
            if self.public_agent_manifest.parts[:2] != ("data", "external"):
                raise ValueError("public_agent_manifest must remain under data/external/")
        _repository_path(self.output_dir, "outputs", "output_dir")
        if not self.opponents or len(set(self.opponents)) != len(self.opponents):
            raise ValueError("conditional-program opponents must be nonempty and unique")
        if tuple(self.opponent_weights) != self.opponents:
            raise ValueError("conditional-program opponent weights must follow opponent order")
        if (
            any(
                opponent not in {"self_play", "deterministic_incumbent"}
                for opponent in self.opponents
            )
            and self.public_agent_manifest is None
        ):
            raise ValueError("public conditional-program opponents require a manifest")
        weights = tuple(self.opponent_weights.values())
        if any(not math.isfinite(value) or value <= 0.0 for value in weights):
            raise ValueError("conditional-program opponent weights must be finite and positive")
        if not math.isclose(math.fsum(weights), 1.0, abs_tol=1e-9):
            raise ValueError("conditional-program opponent weights must sum to one")
        episodes = 2 * self.rollout.seeds_per_update
        if episodes % self.optimization.episodes_per_minibatch:
            raise ValueError("paired episodes must divide into PPO minibatches")
        if self.act_timeout_seconds != 1.0 or self.remaining_overage_seconds != 60.0:
            raise ValueError("conditional-program deployment budget must match official semantics")
        parts = self.device.split(":", maxsplit=1)
        device_type = parts[0]
        if (
            device_type not in {"cpu", "cuda"}
            or (device_type == "cpu" and len(parts) != 1)
            or (len(parts) == 2 and not parts[1].isdigit())
        ):
            raise ValueError("conditional-program device must be CPU or CUDA")
        if (
            not self.rollout.devices
            or len(set(self.rollout.devices)) != len(self.rollout.devices)
            or self.rollout.devices[0] != self.device
        ):
            raise ValueError(
                "conditional-program rollout devices must be unique and start with device"
            )
        for rollout_device in self.rollout.devices:
            rollout_parts = rollout_device.split(":", maxsplit=1)
            if (
                rollout_parts[0] not in {"cpu", "cuda"}
                or (rollout_parts[0] == "cpu" and len(rollout_parts) != 1)
                or (len(rollout_parts) == 2 and not rollout_parts[1].isdigit())
            ):
                raise ValueError("conditional-program rollout device must be CPU or CUDA")
        if len(self.rollout.devices) > 1 and any(
            not value.startswith("cuda:") for value in self.rollout.devices
        ):
            raise ValueError(
                "multi-device conditional-program rollout requires indexed CUDA devices"
            )
        device_count = len(self.rollout.devices)
        if (
            self.rollout.seeds_per_update % device_count
            or self.rollout.batch_games % device_count
            or self.rollout.cpu_workers % device_count
            or self.rollout.actor_streams % device_count
            or self.cpu_threads % device_count
            or self.optimization.episodes_per_minibatch % device_count
        ):
            raise ValueError("conditional-program training shapes must divide across devices")
        local_minibatch = self.optimization.episodes_per_minibatch // device_count
        if local_minibatch % self.optimization.effective_episodes_per_microbatch:
            raise ValueError("conditional-program rank minibatch must divide into microbatches")
        if self.rollout.batch_games % self.rollout.actor_streams:
            raise ValueError("conditional-program rollout batch must divide across actor streams")
        if self.rollout.batch_games // self.rollout.actor_streams < 2:
            raise ValueError("conditional-program actor stream cannot hold self-play")
        episode_steps = self.environment.get("episodeSteps")
        market_orders = self.environment.get("maxMarketOrdersPerTurn")
        if (
            not isinstance(episode_steps, int)
            or isinstance(episode_steps, bool)
            or episode_steps < 2
        ):
            raise ValueError("conditional-program episodeSteps must allow a transition")
        if (
            not isinstance(market_orders, int)
            or isinstance(market_orders, bool)
            or market_orders < 1
        ):
            raise ValueError("conditional-program market order capacity must be positive")
        return self


class ProgramRlAppSettings(BaseModel):
    """Hydra root for one selected conditional-program profile."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    conditional_program_rl: ProgramRlSettings


__all__ = [
    "ProgramAbiSettings",
    "ProgramCheckpointSettings",
    "ProgramModelSettings",
    "ProgramObjectiveSettings",
    "ProgramOptimizationSettings",
    "ProgramRlAppSettings",
    "ProgramRlSettings",
    "ProgramRolloutSettings",
]
