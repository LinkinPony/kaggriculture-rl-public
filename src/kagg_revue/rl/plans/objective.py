"""Undiscounted terminal-W/D/L SMDP objective for complete plan updates."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor
from torch.nn import functional


@dataclass(frozen=True)
class PlanAdvantages:
    """Frozen terminal advantages and actor-update eligibility."""

    values: Tensor
    actor_update: bool
    mean: Tensor
    scale: Tensor


@dataclass(frozen=True)
class PlanPpoLoss:
    """Episode-balanced joint-plan PPO and detached-encoder critic loss."""

    total: Tensor
    policy: Tensor
    value: Tensor
    entropy: Tensor
    approximate_kl: Tensor
    clip_fraction: Tensor


def _episode_indices(episode_index: Tensor, episode_count: int) -> Tensor:
    if episode_count < 1 or episode_index.ndim != 1 or episode_index.numel() < 1:
        raise ValueError("episode-balanced plan reduction needs decisions and episodes")
    if episode_index.is_floating_point() or episode_index.dtype == torch.bool:
        raise ValueError("structured-plan episode index must use an integer dtype")
    indices = episode_index.long()
    if bool(torch.any((indices < 0) | (indices >= episode_count))):
        raise ValueError("structured-plan decision refers outside the episode panel")
    if bool(torch.any(torch.bincount(indices, minlength=episode_count) == 0)):
        raise ValueError("every structured-plan episode needs at least one decision")
    return indices


def episode_balanced_mean(values: Tensor, episode_index: Tensor, episode_count: int) -> Tensor:
    """Average decisions per episode before averaging the complete games."""
    if values.ndim != 1 or values.shape != episode_index.shape:
        raise ValueError("episode-balanced plan values must align with decisions")
    indices = _episode_indices(episode_index, episode_count)
    sums = torch.zeros(episode_count, dtype=values.dtype, device=values.device)
    counts = torch.zeros_like(sums)
    sums.scatter_add_(0, indices, values)
    counts.scatter_add_(0, indices, torch.ones_like(values))
    return (sums / counts).mean()


def episode_duration_balanced_mean(
    values: Tensor,
    episode_index: Tensor,
    durations: Tensor,
    episode_count: int,
) -> Tensor:
    """Average by controlled primitive time within each complete episode."""
    if values.ndim != 1 or values.shape != episode_index.shape:
        raise ValueError("structured-plan duration values must align with decisions")
    if (
        durations.shape != values.shape
        or durations.is_floating_point()
        or durations.dtype == torch.bool
    ):
        raise ValueError("structured-plan entropy durations must be integer decisions")
    if bool(torch.any(durations < 1)):
        raise ValueError("structured-plan entropy durations must be positive")
    indices = _episode_indices(episode_index, episode_count)
    weights = durations.to(values.dtype)
    weighted = torch.zeros(episode_count, dtype=values.dtype, device=values.device)
    totals = torch.zeros_like(weighted)
    weighted.scatter_add_(0, indices, values * weights)
    totals.scatter_add_(0, indices, weights)
    return (weighted / totals).mean()


def terminal_wdl_advantages(
    outcomes: Tensor,
    old_values: Tensor,
    episode_index: Tensor,
    durations: Tensor,
    *,
    normalize: bool,
) -> PlanAdvantages:
    """Assign one undiscounted terminal result to each plan decision."""
    if outcomes.ndim != 1 or old_values.ndim != 1:
        raise ValueError("structured-plan outcomes and old values must be vectors")
    if old_values.shape != episode_index.shape or durations.shape != old_values.shape:
        raise ValueError("structured-plan SMDP statistics must align")
    if (
        durations.is_floating_point()
        or durations.dtype == torch.bool
        or bool(torch.any(durations < 1))
    ):
        raise ValueError("structured-plan SMDP durations must be positive integers")
    if not torch.isfinite(old_values).all() or bool(
        torch.any((old_values < -1) | (old_values > 1))
    ):
        raise ValueError("structured-plan old values must lie in [-1, 1]")
    if not torch.isfinite(outcomes).all() or bool(
        torch.any((outcomes < -1) | (outcomes > 1) | (outcomes != outcomes.round()))
    ):
        raise ValueError("structured-plan outcomes must be loss, tie, or win")
    indices = _episode_indices(episode_index, outcomes.numel())
    raw = outcomes.detach().float()[indices] - old_values.detach().float()
    mean = episode_balanced_mean(raw, indices, outcomes.numel())
    variance = episode_balanced_mean((raw - mean).square(), indices, outcomes.numel())
    scale = variance.clamp_min(0.0).sqrt()
    actor_update = torch.unique(outcomes.detach()).numel() >= 2
    values = raw
    if normalize and actor_update and bool(torch.isfinite(scale)) and float(scale) > 1e-6:
        values = (raw - mean) / scale
    return PlanAdvantages(values, actor_update, mean.detach(), scale.detach())


def plan_ppo_loss(
    new_joint_log_probability: Tensor,
    old_joint_log_probability: Tensor,
    decision_entropy: Tensor,
    factor_counts: Tensor,
    outcome_logits: Tensor,
    advantages: Tensor,
    outcomes: Tensor,
    episode_index: Tensor,
    durations: Tensor,
    *,
    clip_epsilon: float,
    value_loss_weight: float,
    entropy_weight: float,
    actor_update: bool,
    validate_inputs: bool = True,
) -> PlanPpoLoss:
    """Apply one clipped ratio to each complete autoregressive plan update."""
    if not 0.0 < clip_epsilon < 1.0:
        raise ValueError("structured-plan PPO clip epsilon must be in (0, 1)")
    if value_loss_weight < 0.0 or entropy_weight < 0.0:
        raise ValueError("structured-plan PPO loss weights must be non-negative")
    expected = old_joint_log_probability.shape
    vectors = (
        new_joint_log_probability,
        decision_entropy,
        factor_counts,
        advantages,
        episode_index,
        durations,
    )
    if old_joint_log_probability.ndim != 1 or any(value.shape != expected for value in vectors):
        raise ValueError("structured-plan PPO statistics must align by decision")
    if outcome_logits.shape != (*expected, 3) or outcomes.ndim != 1:
        raise ValueError("structured-plan critic logits must have shape [decisions, 3]")
    if bool(torch.any(factor_counts < 1)):
        raise ValueError("structured-plan entropy needs a positive factor count")
    if (
        durations.is_floating_point()
        or durations.dtype == torch.bool
        or bool(torch.any(durations < 1))
    ):
        raise ValueError("structured-plan durations must be positive integers")
    indices = _episode_indices(episode_index, outcomes.numel())
    if validate_inputs and any(
        bool(torch.any(~torch.isfinite(value)))
        for value in (
            new_joint_log_probability,
            old_joint_log_probability,
            decision_entropy,
            advantages,
            outcome_logits,
        )
    ):
        raise ValueError("structured-plan PPO received a non-finite statistic")

    log_ratio = new_joint_log_probability - old_joint_log_probability.detach()
    ratio = torch.exp(log_ratio)
    frozen_advantages = advantages.detach()
    surrogate = torch.minimum(
        ratio * frozen_advantages,
        ratio.clamp(1.0 - clip_epsilon, 1.0 + clip_epsilon) * frozen_advantages,
    )
    zero = torch.zeros((), dtype=ratio.dtype, device=ratio.device)
    policy = -episode_balanced_mean(surrogate, indices, outcomes.numel()) if actor_update else zero
    entropy = episode_duration_balanced_mean(
        decision_entropy,
        indices,
        durations,
        outcomes.numel(),
    )
    labels = outcomes.long()[indices] + 1
    value_items = functional.cross_entropy(outcome_logits.float(), labels, reduction="none")
    value = episode_balanced_mean(value_items, indices, outcomes.numel())
    # A homogeneous W/D/L panel has no reward-driven actor signal, but must still
    # retain the configured exploration pressure instead of freezing at collapse.
    entropy_objective = entropy_weight * entropy
    total = policy + value_loss_weight * value - entropy_objective
    detached_log_ratio = log_ratio.detach()
    approximate_kl = episode_balanced_mean(
        (torch.exp(detached_log_ratio) - 1.0) - detached_log_ratio,
        indices,
        outcomes.numel(),
    )
    clip_fraction = episode_balanced_mean(
        (torch.abs(ratio.detach() - 1.0) > clip_epsilon).to(ratio.dtype),
        indices,
        outcomes.numel(),
    )
    return PlanPpoLoss(
        total=total,
        policy=policy,
        value=value,
        entropy=entropy,
        approximate_kl=approximate_kl,
        clip_fraction=clip_fraction,
    )


__all__ = [
    "PlanAdvantages",
    "PlanPpoLoss",
    "episode_balanced_mean",
    "episode_duration_balanced_mean",
    "plan_ppo_loss",
    "terminal_wdl_advantages",
]
