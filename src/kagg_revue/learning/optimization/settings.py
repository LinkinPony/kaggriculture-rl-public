"""Optimization and historical-opponent controls without a data pipeline."""

from pathlib import Path
from typing import Literal

from pydantic import Field

from kagg_revue.configuration import FrozenSettings


class TemperatureSchedule(FrozenSettings):
    """Fixed log-cosine ramp after the existing critic-only greedy warmup."""

    end_update: int = Field(gt=1)
    start_temperature: float = Field(gt=0)
    scale_actor_learning_rate: bool = False


class UpdateProtection(FrozenSettings):
    """Actor rollback; decay 1 keeps the configured learning rates constant."""

    backtrack_attempts: int = Field(gt=0)
    learning_rate_decay: float = Field(gt=0, le=1)
    skip_constant_returns: bool = True


class HistoricalPopulation(FrozenSettings):
    """One frozen learned opponent alongside current-policy mirror games."""

    checkpoint: Path
    fraction: float = Field(gt=0, le=1)


class CashMargin(FrozenSettings):
    """Bound the terminal cash-difference bonus while preserving seat antisymmetry."""

    beta: float = Field(default=1.0, gt=0, allow_inf_nan=False)
    cash_scale: float = Field(default=10000.0, gt=0, allow_inf_nan=False)


class OptimizationSettings(FrozenSettings):
    """Direct terminal-outcome PPO with supervised retention."""

    population: Literal["self_play", "script_mix"]
    history: HistoricalPopulation | None = None
    ratio_scope: Literal["field", "plan", "prefix"] = "field"
    prefix_value_weight: float = Field(default=1.0, gt=0)
    prefix_trace_lambda: float = Field(default=0.0, ge=0, le=1)
    prefix_warmup_updates: int = Field(default=0, ge=0)
    temperature: float = Field(default=1.0, gt=0)
    temperature_schedule: TemperatureSchedule | None = None
    script_fraction: float = Field(default=0.0, ge=0, le=1)
    script_opponents: tuple[str, ...] = ()
    script_allocation: tuple[tuple[str, int], ...] = ()
    concurrent_history_inference: bool = False
    updates: int = Field(gt=0)
    games_per_update: int = Field(gt=0)
    batch_rows: int = Field(gt=0)
    epochs: int = Field(gt=0)
    actor_learning_rate: float = Field(gt=0)
    critic_learning_rate: float = Field(gt=0)
    learning_rate_warmup_updates: int = Field(default=0, ge=0)
    gamma: float = Field(default=1.0, gt=0, le=1)
    gae_lambda: float = Field(default=1.0, ge=0, le=1)
    clip: float = Field(gt=0, lt=1)
    target_kl: float = Field(gt=0)
    protection: UpdateProtection | None = None
    bc_weight: float = Field(ge=0)
    bc_rows: int = Field(gt=0)
    entropy_weight: float = Field(ge=0)
    reference_kl_weight: float = Field(default=0.0, ge=0, allow_inf_nan=False)
    cash_weight: float = Field(default=0.0, ge=0)
    cash_scale: float = Field(gt=0)
    cash_margin: CashMargin | None = None
    win_weight: float = Field(default=1.0, ge=0)
    seed_start: int = Field(ge=0)
    checkpoint_interval: int = Field(gt=0)
    microbatch_rows: int = Field(default=512, gt=0)
    evaluation_interval: int = Field(default=0, ge=0)
    retain_checkpoints: int = Field(default=0, ge=0)

    def temperature_at(self, update: int) -> float:
        """Resolve the sampling temperature from the absolute collection update."""
        from kagg_revue.learning.optimization.temperature import log_cosine_temperature

        schedule = self.temperature_schedule
        if schedule is None:
            return self.temperature
        return log_cosine_temperature(
            update,
            greedy_updates=self.prefix_warmup_updates,
            end_update=schedule.end_update,
            start=schedule.start_temperature,
            stop=self.temperature,
        )

    def actor_rate_at(self, update: int) -> float:
        """Optionally scale the actor step with the fixed relative temperature."""
        schedule = self.temperature_schedule
        rate = self.actor_learning_rate * self.warmup_scale(update)
        if schedule is not None and schedule.scale_actor_learning_rate:
            return rate * self.temperature_at(update) / self.temperature
        return rate

    def warmup_scale(self, update: int) -> float:
        """Use the absolute one-based PPO update so recovery never restarts warmup."""
        if update < 1:
            raise ValueError("learning-rate schedules require a positive PPO update")
        return (
            min(update / self.learning_rate_warmup_updates, 1.0)
            if (self.learning_rate_warmup_updates)
            else 1.0
        )

    def critic_rate_at(self, update: int) -> float:
        """Apply the same update-based linear warmup to the independent critic."""
        return self.critic_learning_rate * self.warmup_scale(update)
