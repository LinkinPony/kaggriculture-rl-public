"""Validated Hydra settings for canonical intent-ledger PPO."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _repository_path(path: Path, root: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != root:
        raise ValueError(f"{name} must be repository-relative under {root}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


class IntentModelSettings(BaseModel):
    """Trainable intent head widths and encoder policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_width: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    train_turn_encoder: bool


class IntentOptimizationSettings(BaseModel):
    """Independent-step PPO optimization settings."""

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
    def validate_microbatch(self) -> IntentOptimizationSettings:
        """Keep gradient accumulation equivalent to one logical minibatch."""
        microbatch = self.effective_episodes_per_microbatch
        if microbatch > self.episodes_per_minibatch or self.episodes_per_minibatch % microbatch:
            raise ValueError("intent microbatch must divide the logical minibatch")
        return self

    @property
    def effective_episodes_per_microbatch(self) -> int:
        """Return the physical batch size used for gradient accumulation."""
        return self.episodes_per_microbatch or self.episodes_per_minibatch


class IntentRolloutSettings(BaseModel):
    """Bounded native self-play collection settings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seeds_per_update: int = Field(gt=0)
    cpu_workers: int = Field(gt=0)
    max_transaction_steps: int = Field(gt=1)
    actor_streams_per_device: int = Field(default=1, gt=0)
    devices: tuple[str, ...] | None = None


class IntentCheckpointSettings(BaseModel):
    """Recoverable checkpoint cadence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    interval: int = Field(gt=0)
    keep: int = Field(gt=0)


class IntentRlSettings(BaseModel):
    """One isolated intent-ledger self-play lineage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    initial_actor: Path
    initial_checkpoint: Path | None = None
    resume_checkpoint: Path | None = None
    output_dir: Path
    seed: int = Field(ge=0)
    rollout_seed_start: int = Field(ge=0)
    updates: int = Field(gt=0)
    opponent: Literal["self_play"]
    objective: Literal["terminal_wdl"]
    discount: float = Field(allow_inf_nan=False)
    gae_lambda: float = Field(allow_inf_nan=False)
    unit_limit: int = Field(gt=0)
    model: IntentModelSettings
    optimization: IntentOptimizationSettings
    rollout: IntentRolloutSettings
    checkpoint: IntentCheckpointSettings
    device: str
    cpu_threads: int = Field(gt=0)
    act_timeout_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    remaining_overage_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_experiment(self) -> IntentRlSettings:
        """Reject proxy objectives, unsafe paths, and incomplete rules."""
        _repository_path(self.initial_actor, "outputs", "intent initial_actor")
        if self.initial_checkpoint is not None:
            _repository_path(
                self.initial_checkpoint,
                "outputs",
                "intent initial_checkpoint",
            )
        if self.resume_checkpoint is not None:
            _repository_path(self.resume_checkpoint, "outputs", "intent resume_checkpoint")
        if self.initial_checkpoint is not None and self.resume_checkpoint is not None:
            raise ValueError("intent RL cannot initialize and resume at the same time")
        _repository_path(self.output_dir, "outputs", "intent output_dir")
        if self.discount != 1.0 or self.gae_lambda != 1.0:
            raise ValueError("intent terminal W/D/L requires gamma=lambda=1")
        if self.act_timeout_seconds != 1.0 or self.remaining_overage_seconds != 60.0:
            raise ValueError("intent deployment budget must match official semantics")
        try:
            device = __import__("torch").device(self.device)
        except (RuntimeError, ValueError) as error:
            raise ValueError("intent training device is invalid") from error
        if device.type not in {"cpu", "cuda"}:
            raise ValueError("intent training device must be CPU or CUDA")
        if device.type == "cuda" and device.index is None:
            raise ValueError("intent CUDA training requires an indexed device")
        rollout_devices = self.rollout.devices or (self.device,)
        parsed_rollout_devices: list[object] = []
        for raw_device in rollout_devices:
            try:
                rollout_device = __import__("torch").device(raw_device)
            except (RuntimeError, ValueError) as error:
                raise ValueError("intent rollout device is invalid") from error
            if rollout_device.type != device.type:
                raise ValueError("intent rollout and learner device types must match")
            if rollout_device.type == "cuda" and rollout_device.index is None:
                raise ValueError("intent CUDA rollout requires indexed devices")
            parsed_rollout_devices.append(rollout_device)
        if len(set(rollout_devices)) != len(rollout_devices):
            raise ValueError("intent rollout devices must be unique")
        if rollout_devices[0] != self.device:
            raise ValueError("intent learner device must be the first rollout device")
        if len(rollout_devices) > self.rollout.seeds_per_update:
            raise ValueError("intent rollout needs at least one seed per device")
        if self.rollout.seeds_per_update % len(rollout_devices):
            raise ValueError("intent rollout seeds must divide across learner ranks")
        local_seeds = self.rollout.seeds_per_update // len(rollout_devices)
        if self.rollout.actor_streams_per_device > local_seeds:
            raise ValueError("intent rollout needs at least one seed per actor stream")
        if self.optimization.episodes_per_minibatch % len(rollout_devices):
            raise ValueError("intent minibatch must divide across learner ranks")
        local_minibatch = self.optimization.episodes_per_minibatch // len(rollout_devices)
        microbatch = self.optimization.effective_episodes_per_microbatch
        if microbatch > local_minibatch or local_minibatch % microbatch:
            raise ValueError("intent microbatch must divide the local learner minibatch")
        episodes = 2 * self.rollout.seeds_per_update
        if episodes % self.optimization.episodes_per_minibatch:
            raise ValueError("intent self-play episodes must divide into minibatches")
        required_environment = {
            "boardSize": 1,
            "episodeSteps": 2,
            "turnsPerDay": 1,
            "maxMarketOrdersPerTurn": 1,
        }
        for name, lower in required_environment.items():
            value = self.environment.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value < lower:
                raise ValueError(f"intent environment {name} must be at least {lower}")
        return self

    @property
    def rollout_devices(self) -> tuple[str, ...]:
        """Return the explicit rollout fleet, defaulting to the learner device."""
        return self.rollout.devices or (self.device,)

    def checkpoint_contract(self) -> dict[str, object]:
        """Return resume-critical settings without checkpoint source paths."""
        payload = self.model_dump(mode="json")
        for name in (
            "initial_checkpoint",
            "resume_checkpoint",
            "output_dir",
            "updates",
            "checkpoint",
        ):
            payload.pop(name)
        return payload


class IntentRlAppSettings(BaseModel):
    """Hydra root for intent-ledger PPO."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_ledger_rl: IntentRlSettings


__all__ = [
    "IntentCheckpointSettings",
    "IntentModelSettings",
    "IntentOptimizationSettings",
    "IntentRlAppSettings",
    "IntentRlSettings",
    "IntentRolloutSettings",
]
