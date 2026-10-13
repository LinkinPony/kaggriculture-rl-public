"""Validated Hydra settings for terminal-outcome training."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.core.observability import ObservabilitySettings


class PfspSettings(BaseModel):
    """Bounded historical-policy sampling for the rollout hot path."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool
    self_play_probability: float = Field(ge=0.0, le=1.0)
    history_capacity: int = Field(gt=0)


class CheckpointSettings(BaseModel):
    """Bounded recovery checkpoints plus durable lineage milestones."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rolling_interval: int = Field(gt=0)
    rolling_keep: int = Field(gt=0)
    permanent_interval: int = Field(gt=0)


class TerminalRewardSettings(BaseModel):
    """One terminal actor-return definition with explicit margin bounds."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["wdl", "margin_augmented_wdl"]
    margin_beta: float = Field(ge=0.0, allow_inf_nan=False)
    margin_cash_scale: float = Field(gt=0.0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_mode(self) -> TerminalRewardSettings:
        """Keep inactive margin parameters from silently changing W/D/L runs."""
        if self.mode == "wdl" and self.margin_beta != 0.0:
            raise ValueError("pure W/D/L reward requires zero margin beta")
        if self.mode == "margin_augmented_wdl" and self.margin_beta <= 0.0:
            raise ValueError("margin-augmented W/D/L reward requires positive beta")
        return self


class OpponentSamplingSettings(BaseModel):
    """One balanced lineage draw per rollout seed."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["weighted_per_seed"]
    weights: dict[str, float]

    @model_validator(mode="after")
    def validate_weights(self) -> OpponentSamplingSettings:
        """Require one normalized, positive distribution."""
        if not self.weights:
            raise ValueError("RL opponent sampling weights cannot be empty")
        if any(not opponent_id for opponent_id in self.weights):
            raise ValueError("RL opponent sampling identities cannot be empty")
        if any(not math.isfinite(weight) or weight <= 0.0 for weight in self.weights.values()):
            raise ValueError("RL opponent sampling weights must be finite and positive")
        if not math.isclose(math.fsum(self.weights.values()), 1.0, abs_tol=1e-9):
            raise ValueError("RL opponent sampling weights must sum to one")
        return self


class FrozenActorOpponentSettings(BaseModel):
    """Authenticated actor checkpoint used as one immutable GPU opponent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    checkpoint: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ResumeTransitionSettings(BaseModel):
    """Explicit authorization for one optimizer-semantics branch."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    detach_critic_from_actor: bool = False
    actor_learning_rate_multiplier: float = Field(default=1.0, gt=0.0, allow_inf_nan=False)
    enable_opening_exploration: bool = False
    replace_opening_exploration: bool = False
    enable_margin_augmented_wdl: bool = False

    @model_validator(mode="after")
    def validate_transition(self) -> ResumeTransitionSettings:
        """Reject an authorization that changes no training semantics."""
        if self.enable_opening_exploration and self.replace_opening_exploration:
            raise ValueError(
                "RL resume transition cannot both enable and replace opening exploration"
            )
        if (
            not self.detach_critic_from_actor
            and self.actor_learning_rate_multiplier == 1.0
            and not self.enable_opening_exploration
            and not self.replace_opening_exploration
            and not self.enable_margin_augmented_wdl
        ):
            raise ValueError("RL resume transition must change a training semantic")
        return self


class OpeningExplorationSettings(BaseModel):
    """Episode-locked opening noise mixed into every ordinary PPO rollout."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = False
    prefix_turns: int = Field(default=8, gt=0)
    noisy_fraction: float = Field(default=0.5, gt=0.0, le=1.0, allow_inf_nan=False)
    probe_seeds: int = Field(default=16, gt=0)
    escape_target: float = Field(
        default=0.2,
        gt=0.0,
        lt=1.0,
        allow_inf_nan=False,
    )
    maximum_scale: float = Field(default=24.0, gt=0.0, allow_inf_nan=False)
    calibration_steps: int = Field(default=10, gt=0, le=32)


class RlSettings(BaseModel):
    """One reproducible undiscounted complete-match training run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    initial_actor: Path
    actor_initialization: Literal["artifact", "random"] = "artifact"
    resume_checkpoint: Path | None = None
    resume_transition: ResumeTransitionSettings | None = None
    public_agent_manifest: Path
    output_dir: Path
    seed: int = Field(ge=0)
    rollout_seed_start: int = Field(ge=0)
    updates: int = Field(gt=0)
    seeds_per_update: int = Field(gt=0)
    rollout_batch_games: int = Field(gt=0)
    rollout_cpu_workers: int = Field(gt=0)
    rollout_actor_streams: int = Field(gt=0, le=16)
    rollout_gpu_policy_session: bool
    rollout_host_memory_limit_gib: float = Field(gt=0.0)
    rollout_gpu_memory_fraction: float = Field(gt=0.0, le=0.9)
    opponents: tuple[str, ...]
    opponent_sampling: OpponentSamplingSettings | None = None
    frozen_actor_opponents: dict[str, FrozenActorOpponentSettings] = Field(default_factory=dict)
    opening_exploration: OpeningExplorationSettings = Field(
        default_factory=OpeningExplorationSettings
    )
    pfsp: PfspSettings
    checkpoint: CheckpointSettings
    terminal_reward: TerminalRewardSettings
    paired_seats: Literal[True]
    evaluation_opponents: tuple[str, ...]
    selection_seeds: tuple[int, ...]
    confirmation_seeds: tuple[int, ...]
    discount: float
    gae_lambda: float
    critic_warmup_updates: int = Field(ge=0)
    critic_actor_gradient: bool
    ppo_epochs: int = Field(gt=0)
    episodes_per_minibatch: int = Field(gt=0)
    actor_learning_rate: float = Field(gt=0.0)
    critic_learning_rate: float = Field(gt=0.0)
    weight_decay: float = Field(ge=0.0)
    clip_epsilon: float = Field(gt=0.0, lt=1.0)
    value_loss_weight: float = Field(gt=0.0)
    entropy_weight: float = Field(ge=0.0)
    target_kl: float = Field(gt=0.0)
    gradient_clip: float = Field(gt=0.0)
    normalize_advantage: bool
    device: str
    devices: tuple[str, ...] = ()
    cpu_threads: int = Field(gt=0)
    unit_limit: int = Field(gt=0)
    evaluation_device: str
    act_timeout_seconds: float = Field(gt=0.0)
    remaining_overage_seconds: float = Field(ge=0.0)
    observability: ObservabilitySettings
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_training(self) -> RlSettings:
        """Reject profiles that change the outcome objective or rollout identity."""
        if self.resume_transition is not None:
            if self.resume_checkpoint is None:
                raise ValueError("RL resume transition requires a checkpoint")
            if self.resume_transition.detach_critic_from_actor and self.critic_actor_gradient:
                raise ValueError(
                    "RL critic detach transition requires critic actor gradients disabled"
                )
        if not self.opponents:
            raise ValueError("RL training needs a nonempty frozen opponent population")
        if len(set(self.opponents)) != len(self.opponents):
            raise ValueError("RL opponent identities must be unique")
        if any(not opponent for opponent in self.opponents):
            raise ValueError("RL opponent identities cannot be empty")
        frozen_ids = set(self.frozen_actor_opponents)
        if frozen_ids & {"self_play", "deterministic_incumbent"}:
            raise ValueError("RL frozen actor opponents cannot use reserved identities")
        if not frozen_ids <= set(self.opponents):
            raise ValueError("RL frozen actor opponents must belong to the training population")
        if (
            self.opponent_sampling is not None
            and tuple(self.opponent_sampling.weights) != self.opponents
        ):
            raise ValueError(
                "RL opponent sampling weights must follow the configured opponent order"
            )
        if self.pfsp.enabled and self.opponents != ("self_play",):
            raise ValueError(
                "historical PFSP keeps notebook opponents outside the training hot path"
            )
        if self.pfsp.enabled and self.opponent_sampling is not None:
            raise ValueError("historical PFSP cannot use weighted notebook sampling")
        if not self.evaluation_opponents:
            raise ValueError("RL evaluation needs a nonempty frozen opponent population")
        if len(set(self.evaluation_opponents)) != len(self.evaluation_opponents):
            raise ValueError("RL evaluation opponent identities must be unique")
        if any(not opponent for opponent in self.evaluation_opponents):
            raise ValueError("RL evaluation opponent identities cannot be empty")
        if "self_play" in self.evaluation_opponents:
            raise ValueError("RL held-out evaluation requires frozen external opponents")
        if not self.selection_seeds or not self.confirmation_seeds:
            raise ValueError("RL selection and confirmation need nonempty seed panels")
        if len(set(self.selection_seeds)) != len(self.selection_seeds) or len(
            set(self.confirmation_seeds)
        ) != len(self.confirmation_seeds):
            raise ValueError("RL evaluation seeds must be unique within each panel")
        rollout_seeds = range(
            self.rollout_seed_start,
            self.rollout_seed_start + self.updates * self.seeds_per_update,
        )
        if set(self.selection_seeds) & set(self.confirmation_seeds):
            raise ValueError("RL selection and confirmation seeds must be disjoint")
        evaluation_seeds = (*self.selection_seeds, *self.confirmation_seeds)
        if any(seed in rollout_seeds for seed in evaluation_seeds):
            raise ValueError("RL rollout and evaluation seeds must be disjoint")
        if self.discount != 1.0 or self.gae_lambda != 1.0:
            raise ValueError("terminal-outcome training requires gamma=1 and lambda=1")
        if self.rollout_actor_streams > self.rollout_cpu_workers:
            raise ValueError("rollout actor streams cannot exceed CPU workers")
        training_devices = self.training_devices
        if len(set(training_devices)) != len(training_devices):
            raise ValueError("RL training devices must be unique")
        if self.device != training_devices[0]:
            raise ValueError("RL device must name the first training device")
        for name, value in (
            *((f"devices[{index}]", value) for index, value in enumerate(training_devices)),
            ("evaluation_device", self.evaluation_device),
        ):
            try:
                torch_device = torch.device(value)
            except (RuntimeError, ValueError) as error:
                raise ValueError(f"RL {name} is not a valid torch device") from error
            if torch_device.type not in {"cpu", "cuda"}:
                raise ValueError(f"RL {name} must be a CPU or CUDA device")
        world_size = len(training_devices)
        if self.opening_exploration.enabled and self.pfsp.enabled:
            raise ValueError("continuous opening noise does not support historical PFSP rollouts")
        if world_size > 1:
            parsed_devices = tuple(torch.device(value) for value in training_devices)
            if any(device.type != "cuda" or device.index is None for device in parsed_devices):
                raise ValueError("distributed RL training requires indexed CUDA devices")
            if self.pfsp.enabled or (
                self.opponents != ("self_play",) and self.opponent_sampling is None
            ):
                raise ValueError(
                    "distributed RL training requires pure self-play or weighted per-seed "
                    "opponent sampling"
                )
            if not self.rollout_gpu_policy_session:
                raise ValueError("distributed RL training requires GPU policy sessions")
            for name, numeric_value in (
                ("seeds_per_update", self.seeds_per_update),
                ("rollout_batch_games", self.rollout_batch_games),
                ("rollout_cpu_workers", self.rollout_cpu_workers),
                ("rollout_actor_streams", self.rollout_actor_streams),
                ("episodes_per_minibatch", self.episodes_per_minibatch),
            ):
                if numeric_value % world_size:
                    raise ValueError(f"RL {name} must be divisible by the distributed world size")
        episode_steps = self.environment.get("episodeSteps")
        market_orders = self.environment.get("maxMarketOrdersPerTurn")
        if not isinstance(episode_steps, int) or isinstance(episode_steps, bool):
            raise ValueError("environment episodeSteps must be an integer")
        if episode_steps < 2:
            raise ValueError("environment episodeSteps must allow a transition")
        if self.opening_exploration.enabled and self.opening_exploration.prefix_turns >= (
            episode_steps - 1
        ):
            raise ValueError("opening exploration prefix must end before the terminal turn")
        if not isinstance(market_orders, int) or isinstance(market_orders, bool):
            raise ValueError("environment maxMarketOrdersPerTurn must be an integer")
        if market_orders < 1:
            raise ValueError("environment maxMarketOrdersPerTurn must be positive")
        return self

    @property
    def training_devices(self) -> tuple[str, ...]:
        """Return the explicit distributed topology or the legacy primary device."""
        return self.devices or (self.device,)


class RlAppSettings(BaseModel):
    """Hydra root for the independent actor-critic command."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rl: RlSettings


class StrategyMigrationSettings(BaseModel):
    """One authenticated vocabulary/capacity/strategy migration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_checkpoint: Path
    source_initial_actor: Path
    destination_dir: Path
    unit_limit: Literal[32]
    strategy_tokens: int = Field(ge=2)
    seed: int = Field(ge=0)
    distillation_games: int = Field(ge=1)
    distillation_turns: int = Field(ge=1)
    distillation_learning_rate: float = Field(gt=0.0)


class StrategyMigrationAppSettings(BaseModel):
    """Hydra root for a strategy migration and its target RL profile."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    migration: StrategyMigrationSettings
    rl: RlSettings

    @model_validator(mode="after")
    def validate_target_run(self) -> StrategyMigrationAppSettings:
        """Bind the migration outputs to one fresh, actor-frozen-warmup branch."""
        destination = self.migration.destination_dir
        if self.rl.unit_limit != self.migration.unit_limit:
            raise ValueError("migration and target RL unit capacities differ")
        if self.rl.initial_actor != destination / "initial-actor.pt":
            raise ValueError("target RL initial actor is not the migration artifact")
        if self.rl.resume_checkpoint != destination / "checkpoint.pt":
            raise ValueError("target RL checkpoint is not the migration artifact")
        if self.rl.critic_warmup_updates < 1:
            raise ValueError("strategy migration requires actor-frozen critic warm-up")
        return self


class MemoryMigrationSettings(BaseModel):
    """Authenticated replacement of a serial strategy recurrence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_checkpoint: Path
    source_initial_actor: Path
    destination_dir: Path
    seed: int = Field(ge=0)


class MemoryMigrationAppSettings(BaseModel):
    """Hydra root for a persistent-memory architecture migration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    migration: MemoryMigrationSettings
    rl: RlSettings

    @model_validator(mode="after")
    def validate_target_run(self) -> MemoryMigrationAppSettings:
        """Bind the target run to the migrated actor and checkpoint."""
        destination = self.migration.destination_dir
        if self.rl.initial_actor != destination / "initial-actor.pt":
            raise ValueError("target RL initial actor is not the memory migration artifact")
        if self.rl.resume_checkpoint != destination / "checkpoint.pt":
            raise ValueError("target RL checkpoint is not the memory migration artifact")
        return self


__all__ = [
    "CheckpointSettings",
    "FrozenActorOpponentSettings",
    "MemoryMigrationAppSettings",
    "MemoryMigrationSettings",
    "OpponentSamplingSettings",
    "OpeningExplorationSettings",
    "PfspSettings",
    "ResumeTransitionSettings",
    "RlAppSettings",
    "RlSettings",
    "StrategyMigrationAppSettings",
    "StrategyMigrationSettings",
    "TerminalRewardSettings",
]
