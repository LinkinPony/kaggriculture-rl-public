"""Cross-rank update metrics for structured-plan PPO."""

from __future__ import annotations

from dataclasses import dataclass

from kagg_revue.rl.plans.distributed import (
    AggregatedPlanRollout,
    PlanRolloutSummary,
    aggregate_plan_rollouts,
)


@dataclass(frozen=True)
class PlanLocalUpdate:
    """Small rank-local measurements safe for an object collective."""

    rollout: PlanRolloutSummary
    behavior_replay: dict[str, float] | None
    decisions: int
    continues: int
    stops: int
    patches: int
    active_lines: float
    episodes: int
    host_bytes: int
    rollout_seconds: float
    memory_reclaim_seconds: float
    transfer_seconds: float
    optimization_seconds: float
    cuda_peak_allocated_bytes: int
    cuda_peak_reserved_bytes: int


@dataclass(frozen=True)
class PlanAggregatedUpdate:
    """Global metrics derived without gathering rollout tensors."""

    rollout: AggregatedPlanRollout
    behavior_replay: dict[str, float] | None
    continue_fraction: float
    stop_fraction: float
    patch_fraction: float
    active_lines: float
    episodes: int
    decisions: int
    host_bytes: int
    rollout_seconds: float
    memory_reclaim_seconds: float
    transfer_seconds: float
    optimization_seconds: float
    cuda_peak_allocated_bytes: int
    cuda_peak_reserved_bytes: int


def aggregate_plan_updates(
    updates: list[PlanLocalUpdate],
) -> PlanAggregatedUpdate:
    """Aggregate direct counts, timings, and behavior replay across ranks."""
    if not updates:
        raise ValueError("structured-plan distributed update cannot be empty")
    rollout = aggregate_plan_rollouts([update.rollout for update in updates])
    decisions = sum(update.decisions for update in updates)
    episodes = sum(update.episodes for update in updates)
    if decisions < 1 or episodes < 1:
        raise RuntimeError("structured-plan distributed update lost training data")
    behavior_rows = [
        update for update in updates if update.behavior_replay is not None
    ]
    if behavior_rows and len(behavior_rows) != len(updates):
        raise RuntimeError("structured-plan ranks disagree on behavior replay")
    behavior_replay = (
        None
        if not behavior_rows
        else {
            "maximum_absolute_log_probability_error": max(
                update.behavior_replay[
                    "maximum_absolute_log_probability_error"
                ]
                for update in behavior_rows
                if update.behavior_replay is not None
            ),
            "mean_absolute_log_probability_error": sum(
                update.behavior_replay["mean_absolute_log_probability_error"]
                * update.decisions
                for update in behavior_rows
                if update.behavior_replay is not None
            )
            / decisions,
        }
    )
    return PlanAggregatedUpdate(
        rollout=rollout,
        behavior_replay=behavior_replay,
        continue_fraction=sum(update.continues for update in updates) / decisions,
        stop_fraction=sum(update.stops for update in updates) / decisions,
        patch_fraction=sum(update.patches for update in updates) / decisions,
        active_lines=sum(update.active_lines for update in updates) / decisions,
        episodes=episodes,
        decisions=decisions,
        host_bytes=sum(update.host_bytes for update in updates),
        rollout_seconds=max(update.rollout_seconds for update in updates),
        memory_reclaim_seconds=max(
            update.memory_reclaim_seconds for update in updates
        ),
        transfer_seconds=max(update.transfer_seconds for update in updates),
        optimization_seconds=max(
            update.optimization_seconds for update in updates
        ),
        cuda_peak_allocated_bytes=sum(
            update.cuda_peak_allocated_bytes for update in updates
        ),
        cuda_peak_reserved_bytes=sum(
            update.cuda_peak_reserved_bytes for update in updates
        ),
    )


__all__ = [
    "PlanAggregatedUpdate",
    "PlanLocalUpdate",
    "aggregate_plan_updates",
]
