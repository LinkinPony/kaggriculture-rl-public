"""Validated Hydra configuration for pure structured-plan PPO."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.core.observability import ObservabilitySettings
from kagg_revue.rl.plans.contract import PlanVersionContract


def _repository_path(path: Path, directory: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != directory:
        raise ValueError(f"{name} must be a repository-relative path under {directory}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


class PlanAbiSettings(BaseModel):
    """Exact native observation and incremental-portfolio ABI."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: Literal[3]
    production_lines: Literal[8]
    line_fields: Literal[6]
    global_fields: Literal[10]
    mode_tokens: Literal[2]
    line_operation_tokens: Literal[3]
    line_value_tokens: Literal[16]
    global_operation_tokens: Literal[2]
    global_value_tokens: Literal[16]
    observation_features: Literal[90]
    journal_features: Literal[32]
    event_features: Literal[32]


class PlanModelSettings(BaseModel):
    """Checkpoint-bound rich scene, temporal, strategy, and decoder shape."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_width: int = Field(gt=0)
    entity_width: int = Field(gt=0)
    attention_heads: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    latent_tokens: int = Field(gt=0)
    register_tokens: int = Field(ge=0)
    scene_layers: int = Field(ge=0)
    temporal_layers: int = Field(gt=0)
    action_layers: int = Field(gt=0)
    max_history: int = Field(gt=0)
    strategy_tokens: int = Field(ge=0)
    fact_dropout: float = Field(ge=0.0, lt=1.0, allow_inf_nan=False)


class PlanVersions(BaseModel):
    """Opaque semantic identities frozen across rollout and optimization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    language: str
    observation: str
    grammar: str
    executor: str

    @model_validator(mode="after")
    def validate_identities(self) -> PlanVersions:
        """Require every semantic version to be explicit and canonical."""
        for name, value in self.model_dump().items():
            if not value or value != value.strip():
                raise ValueError(f"structured-plan {name} version must be canonical")
        return self

    def contract(self) -> PlanVersionContract:
        """Return the exact rollout/checkpoint version contract."""
        return PlanVersionContract(
            language_version=self.language,
            observation_version=self.observation,
            grammar_version=self.grammar,
            executor_version=self.executor,
        )


class PlanObjectiveSettings(BaseModel):
    """Direct terminal objective and undiscounted SMDP semantics."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reward: Literal["terminal_wdl"]
    discount: float = Field(allow_inf_nan=False)
    gae_lambda: float = Field(allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_terminal_objective(self) -> PlanObjectiveSettings:
        """Forbid discounted or shaped variants in the pure-plan mainline."""
        if self.discount != 1.0 or self.gae_lambda != 1.0:
            raise ValueError("structured-plan terminal W/D/L requires gamma=lambda=1")
        return self


class PlanOptimizationSettings(BaseModel):
    """Joint-plan PPO and detached-encoder W/D/L critic parameters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ppo_epochs: int = Field(gt=0)
    episodes_per_minibatch: int = Field(gt=0)
    actor_learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    critic_learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    weight_decay: float = Field(ge=0.0, allow_inf_nan=False)
    clip_epsilon: float = Field(gt=0.0, lt=1.0, allow_inf_nan=False)
    value_loss_weight: float = Field(gt=0.0, allow_inf_nan=False)
    entropy_weight: float = Field(ge=0.0, allow_inf_nan=False)
    target_kl: float = Field(gt=0.0, allow_inf_nan=False)
    gradient_clip: float = Field(gt=0.0, allow_inf_nan=False)
    normalize_advantage: bool


class PlanRolloutSettings(BaseModel):
    """Native complete-match rollout and event inference capacities."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seeds_per_update: int = Field(gt=0)
    cpu_workers: int = Field(gt=0, le=256)
    inference_batch_size: int = Field(gt=0)
    event_cuda_graph_max_batch_size: int = Field(ge=0)
    host_memory_limit_gib: float = Field(gt=0.0, allow_inf_nan=False)
    gpu_memory_fraction: float = Field(gt=0.0, le=0.9, allow_inf_nan=False)


class PlanSelfPlaySettings(BaseModel):
    """Bounded current/history mixture using only this actor lineage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    historical_fraction: float = Field(gt=0.0, lt=1.0, allow_inf_nan=False)
    snapshot_interval: int = Field(gt=0)
    history_capacity: int = Field(ge=1)


class PlanHealthSettings(BaseModel):
    """Conservative direct-match quarantine for a degenerate lineage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    warmup_updates: int = Field(ge=0)
    anchor_panels: int = Field(ge=2)
    stop_fraction_floor: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    plan_change_fraction_ceiling: float = Field(
        ge=0.0,
        le=1.0,
        allow_inf_nan=False,
    )
    anchor_loss_rate_floor: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)


class PlanCheckpointSettings(BaseModel):
    """Bounded rolling recovery and durable milestone cadence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rolling_interval: int = Field(gt=0)
    rolling_keep: int = Field(gt=0)
    permanent_interval: int = Field(gt=0)


class StructuredPlanRlSettings(BaseModel):
    """One reproducible pure structured-plan PPO training lineage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    actor_initialization: Literal["random", "bc_backbone"]
    initial_actor: Path | None = None
    resume_checkpoint: Path | None = None
    output_dir: Path
    seed: int = Field(ge=0)
    rollout_seed_start: int = Field(ge=0)
    updates: int = Field(gt=0)
    paired_seats: Literal[True]
    selection_seeds: tuple[int, ...]
    confirmation_seeds: tuple[int, ...]
    abi: PlanAbiSettings
    model: PlanModelSettings
    versions: PlanVersions
    objective: PlanObjectiveSettings
    optimization: PlanOptimizationSettings
    rollout: PlanRolloutSettings
    self_play: PlanSelfPlaySettings
    health: PlanHealthSettings
    checkpoint: PlanCheckpointSettings
    observability: ObservabilitySettings
    devices: tuple[str, ...]
    cpu_threads: int = Field(gt=0)
    act_timeout_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    remaining_overage_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_training(self) -> StructuredPlanRlSettings:
        """Bind paths, pure self-play, seeds, official budget, and CUDA execution."""
        _repository_path(self.output_dir, "outputs", "structured-plan output_dir")
        if self.initial_actor is not None:
            _repository_path(
                self.initial_actor,
                "outputs",
                "structured-plan initial_actor",
            )
        if (self.actor_initialization == "bc_backbone") != (
            self.initial_actor is not None
        ):
            raise ValueError(
                "structured-plan BC initialization requires exactly one initial actor"
            )
        if self.resume_checkpoint is not None:
            _repository_path(
                self.resume_checkpoint,
                "outputs",
                "structured-plan resume_checkpoint",
            )
        self._validate_devices()
        history_seeds = self.rollout.seeds_per_update * self.self_play.historical_fraction
        current_seeds = self.rollout.seeds_per_update - history_seeds
        rollout_shards = len(self.devices)
        if history_seeds < rollout_shards or current_seeds < rollout_shards:
            raise ValueError(
                "structured-plan rollout shards must each represent current and history"
            )
        if self.rollout.seeds_per_update % rollout_shards:
            raise ValueError("structured-plan rollout seeds must divide across devices")
        distributed_capacities = {
            "rollout cpu_workers": self.rollout.cpu_workers,
            "PPO episodes_per_minibatch": self.optimization.episodes_per_minibatch,
            "cpu_threads": self.cpu_threads,
        }
        for name, value in distributed_capacities.items():
            if value % rollout_shards:
                raise ValueError(f"structured-plan {name} must divide across devices")
        if self.act_timeout_seconds != 1.0 or self.remaining_overage_seconds != 60.0:
            raise ValueError("structured-plan deployment budget must be official 1s+60s")
        self._validate_seeds()
        episode_steps = self.environment.get("episodeSteps")
        market_orders = self.environment.get("maxMarketOrdersPerTurn")
        valid_steps = (
            isinstance(episode_steps, int)
            and not isinstance(episode_steps, bool)
            and episode_steps >= 2
        )
        if not valid_steps:
            raise ValueError("structured-plan episodeSteps must allow a transition")
        valid_market = (
            isinstance(market_orders, int)
            and not isinstance(market_orders, bool)
            and market_orders >= 1
        )
        if not valid_market:
            raise ValueError("structured-plan market capacity must be positive")
        return self

    def _validate_seeds(self) -> None:
        if not self.selection_seeds or not self.confirmation_seeds:
            raise ValueError("structured-plan evaluation panels cannot be empty")
        if len(set(self.selection_seeds)) != len(self.selection_seeds) or len(
            set(self.confirmation_seeds)
        ) != len(self.confirmation_seeds):
            raise ValueError("structured-plan evaluation seeds must be unique")
        if set(self.selection_seeds) & set(self.confirmation_seeds):
            raise ValueError("structured-plan selection and confirmation seeds must be disjoint")
        rollout_end = self.rollout_seed_start + self.updates * self.rollout.seeds_per_update
        if any(
            self.rollout_seed_start <= seed < rollout_end
            for seed in (*self.selection_seeds, *self.confirmation_seeds)
        ):
            raise ValueError("structured-plan rollout and evaluation seeds must be disjoint")

    def _validate_devices(self) -> None:
        if not 1 <= len(self.devices) <= 2 or len(set(self.devices)) != len(self.devices):
            raise ValueError(
                "structured-plan trainer requires one or two unique CUDA devices"
            )
        for value in self.devices:
            try:
                device = torch.device(value)
            except (RuntimeError, ValueError) as error:
                raise ValueError("structured-plan training device is invalid") from error
            if device.type != "cuda" or device.index is None:
                raise ValueError("structured-plan long training requires indexed CUDA")

    def checkpoint_contract(self) -> dict[str, object]:
        """Return exact resume semantics while permitting run extension."""
        payload = self.model_dump(mode="json")
        for key in ("resume_checkpoint", "output_dir", "updates", "checkpoint"):
            payload.pop(key)
        return payload


class StructuredPlanRlAppSettings(BaseModel):
    """Hydra root for the independent structured-plan training command."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    structured_plan_rl: StructuredPlanRlSettings


__all__ = [
    "PlanAbiSettings",
    "PlanCheckpointSettings",
    "PlanHealthSettings",
    "PlanModelSettings",
    "PlanObjectiveSettings",
    "PlanOptimizationSettings",
    "PlanRolloutSettings",
    "PlanSelfPlaySettings",
    "PlanVersions",
    "StructuredPlanRlAppSettings",
    "StructuredPlanRlSettings",
]
