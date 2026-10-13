"""Validated Hydra configuration for recurrent behavior cloning."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.core.observability import ObservabilitySettings


class ModelSettings(BaseModel):
    """Actor dimensions independent of a particular dataset tensor shape."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_width: int = Field(gt=0)
    entity_width: int = Field(gt=0)
    attention_heads: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    latent_tokens: int = Field(gt=0)
    register_tokens: int = Field(default=0, ge=0)
    scene_layers: int = Field(ge=0)
    temporal_layers: int = Field(gt=0)
    action_layers: int = Field(gt=0)
    max_history: int = Field(gt=0)
    max_decisions: int = Field(gt=0)
    maximum_quantity: int = Field(gt=0)
    fact_dropout: float = Field(ge=0.0, lt=1.0)
    skill_tokens: int = Field(default=0, ge=0)
    strategy_tokens: int = Field(default=0, ge=0)
    strategy_version: Literal["attention-v1", "gru-v1"] | None = None
    economic_feature_version: str | None = None

    @model_validator(mode="after")
    def validate_model(self) -> ModelSettings:
        """Reject attention shapes unsupported by rotary positions."""
        if self.model_width % self.attention_heads:
            raise ValueError("model width must be divisible by attention heads")
        if (self.model_width // self.attention_heads) % 2:
            raise ValueError("attention head width must be even")
        if self.skill_tokens == 1:
            raise ValueError("enabled latent skills need at least two tokens")
        if self.strategy_tokens == 1:
            raise ValueError("enabled strategy workspace needs at least two tokens")
        if self.skill_tokens and self.strategy_tokens:
            raise ValueError("latent skills and recurrent strategy cannot coexist")
        if bool(self.strategy_tokens) != (self.strategy_version is not None):
            raise ValueError("strategy tokens and implementation version must coexist")
        return self


class ExperimentSettings(BaseModel):
    """One reproducible sequential behavior and closed-loop experiment."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_dir: Path
    public_agent_manifest: Path
    output_dir: Path
    resume_checkpoint: Path | None = None
    initial_actor: Path | None = None
    seed: int
    split_seed: int
    train_fraction: float = Field(gt=0.0, lt=1.0)
    validation_fraction: float = Field(gt=0.0, lt=1.0)
    epochs: int = Field(gt=0)
    checkpoint_selection: Literal["minimum_validation_nll", "final_epoch"] = (
        "minimum_validation_nll"
    )
    batch_sequences: int = Field(gt=0)
    loader_workers: int = Field(gt=0)
    prefetch_batches: int = Field(ge=0)
    unroll_length: int = Field(gt=0)
    burn_in: int = Field(ge=0)
    learning_rate: float = Field(gt=0.0)
    weight_decay: float = Field(ge=0.0)
    quantity_loss_weight: float = Field(ge=0.0)
    gradient_clip: float = Field(gt=0.0)
    device: str
    unit_limit: int = Field(gt=0)
    selection_seeds: tuple[int, ...]
    confirmation_seeds: tuple[int, ...]
    confirmation_opponents: tuple[str, ...]
    evaluation_device: Literal["cpu", "cuda"]
    cpu_threads: int = Field(gt=0)
    act_timeout_seconds: float = Field(gt=0.0)
    remaining_overage_seconds: float = Field(ge=0.0)
    observability: ObservabilitySettings
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_experiment(self) -> ExperimentSettings:
        """Reject overlapping evidence and invalid sequence/environment shapes."""
        if self.train_fraction + self.validation_fraction >= 1.0:
            raise ValueError("train and validation fractions must leave a test partition")
        if self.burn_in >= self.unroll_length:
            raise ValueError("burn-in must be shorter than the optimized unroll")
        if self.resume_checkpoint is not None and self.initial_actor is not None:
            raise ValueError("BC cannot resume optimizer state and import an initial actor")
        if not self.selection_seeds or not self.confirmation_seeds:
            raise ValueError("selection and confirmation need nonempty seed panels")
        if set(self.selection_seeds) & set(self.confirmation_seeds):
            raise ValueError("selection and confirmation seeds must be disjoint")
        if not self.confirmation_opponents:
            raise ValueError("confirmation needs at least one named notebook opponent")
        episode_steps = self.environment.get("episodeSteps")
        market_orders = self.environment.get("maxMarketOrdersPerTurn")
        if not isinstance(episode_steps, int) or isinstance(episode_steps, bool):
            raise ValueError("environment episodeSteps must be an integer")
        if episode_steps < 2:
            raise ValueError("environment episodeSteps must allow a transition")
        if not isinstance(market_orders, int) or isinstance(market_orders, bool):
            raise ValueError("environment maxMarketOrdersPerTurn must be an integer")
        if market_orders < 1:
            raise ValueError("environment maxMarketOrdersPerTurn must be positive")
        return self


class AppSettings(BaseModel):
    """Hydra root with cross-validated model and experiment settings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model: ModelSettings
    experiment: ExperimentSettings

    @model_validator(mode="after")
    def validate_contract(self) -> AppSettings:
        """Ensure the actor can represent one complete official turn and season."""
        market_value = self.experiment.environment["maxMarketOrdersPerTurn"]
        episode_value = self.experiment.environment["episodeSteps"]
        if not isinstance(market_value, int) or not isinstance(episode_value, int):
            raise ValueError("validated environment integers changed type")
        market_orders = market_value
        episode_steps = episode_value
        if self.model.max_decisions < self.experiment.unit_limit + market_orders:
            raise ValueError("model max_decisions cannot hold units and market slots")
        if self.model.max_history < episode_steps:
            raise ValueError("model max_history must cover the configured season")
        if self.model.strategy_tokens and self.experiment.burn_in:
            raise ValueError(
                "persistent-strategy BC must start every sequence at the episode boundary"
            )
        return self


__all__ = ["AppSettings", "ExperimentSettings", "ModelSettings"]
