"""Validated Hydra settings for event-driven Kaito route PPO."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

import torch
from pydantic import BaseModel, ConfigDict, Field, model_validator


def _relative_under(path: Path, directory: str, name: str) -> None:
    if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != directory:
        raise ValueError(f"{name} must be repository-relative under {directory}/")
    if ".." in path.parts:
        raise ValueError(f"{name} cannot escape its repository directory")


class RouteModelSettings(BaseModel):
    """Compact actor-critic widths and the frozen Kaito behavior prior."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hidden_width: int = Field(gt=0)
    feedforward_width: int = Field(gt=0)
    prior_logit: float = Field(gt=0.0, allow_inf_nan=False)


class RouteOptimizationSettings(BaseModel):
    """PPO optimization over terminal paired-control W/D/L residuals."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ppo_epochs: int = Field(gt=0)
    decisions_per_minibatch: int = Field(gt=0)
    learning_rate: float = Field(gt=0.0, allow_inf_nan=False)
    weight_decay: float = Field(ge=0.0, allow_inf_nan=False)
    clip_epsilon: float = Field(gt=0.0, lt=1.0, allow_inf_nan=False)
    value_loss_weight: float = Field(ge=0.0, allow_inf_nan=False)
    entropy_weight: float = Field(ge=0.0, allow_inf_nan=False)
    target_kl: float = Field(gt=0.0, allow_inf_nan=False)
    gradient_clip: float = Field(gt=0.0, allow_inf_nan=False)
    normalize_advantage: bool
    discount: float = Field(allow_inf_nan=False)
    gae_lambda: float = Field(allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_terminal_objective(self) -> RouteOptimizationSettings:
        """Forbid discounted or bootstrapped proxy returns."""
        if self.discount != 1.0 or self.gae_lambda != 1.0:
            raise ValueError("route terminal W/D/L PPO requires gamma=1 and lambda=1")
        return self


class RouteRolloutSettings(BaseModel):
    """Paired-seat complete-match rollout shape."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seeds_per_update: int = Field(gt=0)
    cpu_workers: int = Field(gt=0, le=256)
    unit_limit: int = Field(gt=0)


class RouteCheckpointSettings(BaseModel):
    """Recovery and permanent checkpoint intervals."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rolling_interval: int = Field(gt=0)
    permanent_interval: int = Field(gt=0)


class RoutePpoSettings(BaseModel):
    """One reproducible PPO-primary route-selection experiment."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    output_dir: Path
    public_agent_manifest: Path
    seed: int = Field(ge=0)
    rollout_seed_start: int = Field(ge=0)
    updates: int = Field(gt=0)
    opponents: tuple[str, ...]
    opponent_weights: dict[str, float]
    paired_seats: Literal[True]
    selection_seed_start: int = Field(ge=0)
    confirmation_seed_start: int = Field(ge=0)
    evaluation_seed_count: int = Field(gt=0)
    model: RouteModelSettings
    optimization: RouteOptimizationSettings
    rollout: RouteRolloutSettings
    checkpoint: RouteCheckpointSettings
    device: str
    cpu_threads: int = Field(gt=0)
    act_timeout_seconds: float = Field(gt=0.0, allow_inf_nan=False)
    remaining_overage_seconds: float = Field(ge=0.0, allow_inf_nan=False)
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_experiment(self) -> RoutePpoSettings:
        """Bind direct outcome semantics, artifacts, seeds, and runtime."""
        _relative_under(self.output_dir, "outputs", "route PPO output_dir")
        _relative_under(
            self.public_agent_manifest,
            "data",
            "route PPO public_agent_manifest",
        )
        if self.public_agent_manifest.parts[:2] != ("data", "external"):
            raise ValueError("route PPO manifest must remain under data/external/")
        if not self.opponents or len(set(self.opponents)) != len(self.opponents):
            raise ValueError("route PPO opponents must be nonempty and unique")
        if tuple(self.opponent_weights) != self.opponents:
            raise ValueError("route PPO opponent weights must follow opponent order")
        weights = tuple(self.opponent_weights.values())
        if any(not math.isfinite(value) or value <= 0.0 for value in weights):
            raise ValueError("route PPO opponent weights must be finite and positive")
        if not math.isclose(math.fsum(weights), 1.0, abs_tol=1e-9):
            raise ValueError("route PPO opponent weights must sum to one")
        try:
            device = torch.device(self.device)
        except (RuntimeError, ValueError) as error:
            raise ValueError("route PPO device is invalid") from error
        if device.type != "cuda" or device.index is None:
            raise ValueError("route PPO long training requires an indexed CUDA device")
        if self.environment.get("episodeSteps") != 720:
            raise ValueError("Kaito route PPO requires the official 720-step episode")
        market_orders = self.environment.get("maxMarketOrdersPerTurn")
        if not isinstance(market_orders, int) or isinstance(market_orders, bool):
            raise ValueError("route PPO market order capacity must be an integer")
        if market_orders < 1:
            raise ValueError("route PPO market order capacity must be positive")
        if self.act_timeout_seconds != 1.0 or self.remaining_overage_seconds != 60.0:
            raise ValueError("route PPO deployment budget must match official semantics")
        self._validate_seed_ranges()
        return self

    def _validate_seed_ranges(self) -> None:
        rollout_stop = self.rollout_seed_start + self.updates * self.rollout.seeds_per_update
        ranges = (
            range(self.rollout_seed_start, rollout_stop),
            range(
                self.selection_seed_start,
                self.selection_seed_start + self.evaluation_seed_count,
            ),
            range(
                self.confirmation_seed_start,
                self.confirmation_seed_start + self.evaluation_seed_count,
            ),
        )
        bounds = tuple((value.start, value.stop) for value in ranges)
        for index, (left_start, left_stop) in enumerate(bounds):
            for right_start, right_stop in bounds[index + 1 :]:
                if max(left_start, right_start) < min(left_stop, right_stop):
                    raise ValueError("route PPO rollout/selection/confirmation seeds overlap")

    def checkpoint_contract(self) -> dict[str, object]:
        """Return immutable resume/evaluation semantics."""
        payload = self.model_dump(mode="json")
        for key in ("output_dir", "updates", "checkpoint"):
            payload.pop(key)
        return payload


class RoutePpoAppSettings(BaseModel):
    """Hydra root for route PPO."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    route_ppo: RoutePpoSettings


__all__ = [
    "RouteCheckpointSettings",
    "RouteModelSettings",
    "RouteOptimizationSettings",
    "RoutePpoAppSettings",
    "RoutePpoSettings",
    "RouteRolloutSettings",
]
