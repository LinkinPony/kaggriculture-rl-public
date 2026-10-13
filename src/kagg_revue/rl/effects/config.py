"""Validated Hydra settings for atomic-effect PPO training."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator


def _repository_path(path: Path, root: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != root:
        raise ValueError(f"{name} must be repository-relative under {root}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


class EffectModelSettings(BaseModel):
    """Trainable effect-head widths and inherited encoder policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_width: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    attention_heads: int = Field(gt=0)
    state_layers: int = Field(gt=0)
    train_turn_encoder: bool
    independent_critic: bool = False
    task_conditioning: bool = False
    prefix_encoding: Literal["field_sum_v1", "joint_action_v2"] = "joint_action_v2"
    destination_tasks: bool = False

    @model_validator(mode="after")
    def validate_attention(self) -> EffectModelSettings:
        """Reject head widths unsupported by rotary attention."""
        if self.model_width % self.attention_heads:
            raise ValueError("effect model width must divide by attention heads")
        if (self.model_width // self.attention_heads) % 2:
            raise ValueError("effect attention head width must be even")
        return self


class EffectOptimizationSettings(BaseModel):
    """Official-turn-balanced factor-wise PPO settings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ppo_epochs: int = Field(gt=0)
    episodes_per_minibatch: int = Field(gt=0)
    episodes_per_microbatch: int | None = Field(default=None, gt=0)
    actor_learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    critic_learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    critic_warmup_updates: int = Field(ge=0)
    critic_actor_gradient: bool
    weight_decay: float = Field(ge=0.0, allow_inf_nan=False)
    clip_epsilon: float = Field(gt=0.0, lt=1.0, allow_inf_nan=False)
    value_loss_weight: float = Field(ge=0.0, allow_inf_nan=False)
    entropy_weight: float = Field(ge=0.0, allow_inf_nan=False)
    gradient_clip: float = Field(gt=0.0, allow_inf_nan=False)
    target_kl: float = Field(gt=0.0, allow_inf_nan=False)
    kl_backoff_factor: float = Field(default=0.5, gt=0.0, lt=1.0, allow_inf_nan=False)
    kl_max_retries: int = Field(default=3, ge=0)
    normalize_advantage: bool
    candidate_elements_per_chunk: int = Field(default=2_000_000, gt=0)

    @model_validator(mode="after")
    def validate_microbatch(self) -> EffectOptimizationSettings:
        """Keep accumulation equivalent to one logical minibatch."""
        microbatch = self.effective_episodes_per_microbatch
        if microbatch > self.episodes_per_minibatch or self.episodes_per_minibatch % microbatch:
            raise ValueError("effect microbatch must divide the logical minibatch")
        return self

    @property
    def effective_episodes_per_microbatch(self) -> int:
        """Return the physical episode batch used by one forward pass."""
        return self.episodes_per_microbatch or self.episodes_per_minibatch


class EffectPopulationSettings(BaseModel):
    """Exact rollout allocation over current policy and named opponents."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    weights: dict[str, float]

    @model_validator(mode="after")
    def validate_weights(self) -> EffectPopulationSettings:
        """Require stable positive identities and one normalized distribution."""
        if not self.weights or any(not name or name != name.strip() for name in self.weights):
            raise ValueError("effect opponent identities must be nonempty")
        if any(not math.isfinite(weight) or weight <= 0.0 for weight in self.weights.values()):
            raise ValueError("effect opponent weights must be finite and positive")
        if not math.isclose(math.fsum(self.weights.values()), 1.0, abs_tol=1e-9):
            raise ValueError("effect opponent weights must sum to one")
        return self


class EffectRolloutSettings(BaseModel):
    """Bounded native batch and CUDA Graph collection settings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seeds_per_update: int = Field(gt=0)
    cpu_workers: int = Field(gt=0)
    actor_streams_per_device: int = Field(default=1, gt=0)
    maximum_graph_variants: int = Field(default=48, gt=0)
    devices: tuple[str, ...] | None = None


class EffectCheckpointSettings(BaseModel):
    """Recoverable rolling-checkpoint cadence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    interval: int = Field(gt=0)
    keep: int = Field(gt=0)


class EffectRlSettings(BaseModel):
    """One isolated atomic-effect terminal-W/D/L lineage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    initial_actor: Path
    initial_checkpoint: Path | None = None
    resume_checkpoint: Path | None = None
    public_agent_manifest: Path | None = None
    output_dir: Path
    seed: int = Field(ge=0)
    rollout_seed_start: int = Field(ge=0)
    updates: int = Field(gt=0)
    objective: Literal["terminal_wdl"]
    discount: float = Field(allow_inf_nan=False)
    gae_lambda: float = Field(allow_inf_nan=False)
    unit_limit: int = Field(gt=0)
    model: EffectModelSettings
    optimization: EffectOptimizationSettings
    population: EffectPopulationSettings
    rollout: EffectRolloutSettings
    checkpoint: EffectCheckpointSettings
    device: str
    cpu_threads: int = Field(gt=0)
    act_timeout_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    remaining_overage_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_experiment(self) -> EffectRlSettings:
        """Reject proxy objectives, unsafe paths, and inconsistent batch shapes."""
        _repository_path(self.initial_actor, "outputs", "effect initial_actor")
        if self.initial_checkpoint is not None:
            _repository_path(
                self.initial_checkpoint,
                "outputs",
                "effect initial_checkpoint",
            )
        if self.resume_checkpoint is not None:
            _repository_path(
                self.resume_checkpoint,
                "outputs",
                "effect resume_checkpoint",
            )
        if self.initial_checkpoint is not None and self.resume_checkpoint is not None:
            raise ValueError("effect RL cannot initialize and resume simultaneously")
        if self.public_agent_manifest is not None:
            _repository_path(
                self.public_agent_manifest,
                "data",
                "effect public_agent_manifest",
            )
            if self.public_agent_manifest.parts[:2] != ("data", "external"):
                raise ValueError("effect public_agent_manifest must be under data/external/")
        if any(name != "self_play" for name in self.population.weights) and (
            self.public_agent_manifest is None
        ):
            raise ValueError("effect native opponents require a public agent manifest")
        _repository_path(self.output_dir, "outputs", "effect output_dir")
        if self.discount != 1.0 or not 0.0 <= self.gae_lambda <= 1.0:
            raise ValueError("effect terminal W/D/L requires gamma=1 and lambda in [0, 1]")
        if self.gae_lambda != 1.0 and not self.model.independent_critic:
            raise ValueError("bootstrap advantages require an independent critic")
        if self.model.independent_critic and self.optimization.critic_actor_gradient:
            raise ValueError("independent critic cannot send value gradients to the actor")
        if self.act_timeout_seconds != 1.0 or self.remaining_overage_seconds != 60.0:
            raise ValueError("effect deployment budget must match official semantics")
        try:
            learner = torch.device(self.device)
        except (RuntimeError, ValueError) as error:
            raise ValueError("effect training device is invalid") from error
        if learner.type not in {"cpu", "cuda"}:
            raise ValueError("effect training device must be CPU or CUDA")
        if learner.type == "cuda" and learner.index is None:
            raise ValueError("effect CUDA training requires an indexed device")
        rollout_devices = self.rollout_devices
        parsed_devices: list[torch.device] = []
        for raw_device in rollout_devices:
            try:
                rollout_device = torch.device(raw_device)
            except (RuntimeError, ValueError) as error:
                raise ValueError("effect rollout device is invalid") from error
            if rollout_device.type != learner.type:
                raise ValueError("effect rollout and learner device types must match")
            if rollout_device.type == "cuda" and rollout_device.index is None:
                raise ValueError("effect CUDA rollout requires indexed devices")
            parsed_devices.append(rollout_device)
        if len(set(parsed_devices)) != len(parsed_devices):
            raise ValueError("effect rollout devices must be unique")
        if parsed_devices[0] != learner:
            raise ValueError("effect learner device must be the first rollout device")
        world_size = len(parsed_devices)
        if world_size > self.rollout.seeds_per_update:
            raise ValueError("effect rollout needs at least one seed per device")
        if self.rollout.seeds_per_update % world_size:
            raise ValueError("effect rollout seeds must divide across learner ranks")
        local_seeds = self.rollout.seeds_per_update // world_size
        if self.rollout.actor_streams_per_device > local_seeds:
            raise ValueError("effect rollout needs at least one seed per actor stream")
        if self.optimization.episodes_per_minibatch % world_size:
            raise ValueError("effect minibatch must divide across learner ranks")
        local_minibatch = self.optimization.episodes_per_minibatch // world_size
        microbatch = self.optimization.effective_episodes_per_microbatch
        if microbatch > local_minibatch or local_minibatch % microbatch:
            raise ValueError("effect microbatch must divide the local learner minibatch")
        episodes = 2 * self.rollout.seeds_per_update
        if episodes % self.optimization.episodes_per_minibatch:
            raise ValueError("effect rollout episodes must divide into minibatches")
        required_environment = {
            "boardSize": 1,
            "episodeSteps": 2,
            "turnsPerDay": 1,
            "maxMarketOrdersPerTurn": 1,
        }
        for name, lower in required_environment.items():
            value = self.environment.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value < lower:
                raise ValueError(f"effect environment {name} must be at least {lower}")
        return self

    @property
    def rollout_devices(self) -> tuple[str, ...]:
        """Return explicit rollout devices, defaulting to the learner."""
        return self.rollout.devices or (self.device,)

    def checkpoint_contract(self) -> dict[str, object]:
        """Return resume-critical settings without output/cadence overrides."""
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


class EffectRlAppSettings(BaseModel):
    """Hydra root for atomic-effect PPO."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    effect_policy_rl: EffectRlSettings


__all__ = [
    "EffectCheckpointSettings",
    "EffectModelSettings",
    "EffectOptimizationSettings",
    "EffectPopulationSettings",
    "EffectRlAppSettings",
    "EffectRlSettings",
    "EffectRolloutSettings",
]
