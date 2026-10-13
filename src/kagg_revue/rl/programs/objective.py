"""Terminal-W/D/L joint-turn objective for conditional programs."""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import Tensor
from torch.nn import functional

from kagg_revue.policy.programs.schema import ProgramSequenceOutput


@dataclass(frozen=True)
class ProgramAdvantageReference:
    """Rollout-wide frozen normalization shared by all minibatches."""

    mean: float
    scale: float
    actor_update: bool


@dataclass(frozen=True)
class ProgramAdvantages:
    """Undiscounted terminal advantages for complete turn programs."""

    values: Tensor
    actor_update: bool
    mean: Tensor
    scale: Tensor


@dataclass(frozen=True)
class ProgramPpoLoss:
    """Episode-balanced joint-ratio PPO diagnostics."""

    total: Tensor
    policy: Tensor
    value: Tensor
    value_accuracy: Tensor
    value_brier: Tensor
    entropy: Tensor
    approximate_kl: Tensor
    clip_fraction: Tensor
    policy_turns: Tensor
    value_turns: Tensor


def _indices(episode_index: Tensor, episodes: int) -> Tensor:
    if episode_index.ndim != 1 or episode_index.numel() < 1:
        raise ValueError("conditional-program PPO requires complete turn indices")
    if episode_index.is_floating_point() or episode_index.dtype == torch.bool:
        raise ValueError("conditional-program episode indices must be integers")
    values = episode_index.long()
    if bool(torch.any((values < 0) | (values >= episodes))):
        raise ValueError("conditional-program turn refers outside its episode batch")
    if bool(torch.any(torch.bincount(values, minlength=episodes) == 0)):
        raise ValueError("every conditional-program episode needs an official turn")
    return values


def _episode_mean(values: Tensor, indices: Tensor, episodes: int) -> Tensor:
    if values.shape != indices.shape or values.ndim != 1:
        raise ValueError("episode-balanced program values must align with turns")
    sums = torch.zeros(episodes, dtype=values.dtype, device=values.device)
    counts = torch.zeros_like(sums)
    sums.scatter_add_(0, indices, values)
    counts.scatter_add_(0, indices, torch.ones_like(values))
    return (sums / counts.clamp_min(1)).mean()


def _masked_episode_mean(
    values: Tensor,
    indices: Tensor,
    episodes: int,
    mask: Tensor,
) -> Tensor:
    if mask.shape != values.shape:
        raise ValueError("conditional-program policy mask must align with turns")
    weights = mask.to(values.dtype)
    sums = torch.zeros(episodes, dtype=values.dtype, device=values.device)
    counts = torch.zeros_like(sums)
    sums.scatter_add_(0, indices, values * weights)
    counts.scatter_add_(0, indices, weights)
    represented = counts > 0
    episode_weights = represented.to(values.dtype)
    numerator = ((sums / counts.clamp_min(1)) * episode_weights).sum()
    return numerator / episode_weights.sum().clamp_min(1)


def terminal_program_advantages(
    outcomes: Tensor,
    old_values: Tensor,
    episode_index: Tensor,
    *,
    normalize: bool,
    reference: ProgramAdvantageReference | None = None,
) -> ProgramAdvantages:
    """Assign one direct terminal result to every official turn."""
    if outcomes.ndim != 1 or old_values.ndim != 1:
        raise ValueError("conditional-program outcomes and old values must be vectors")
    indices = _indices(episode_index, outcomes.numel())
    if old_values.shape != indices.shape:
        raise ValueError("conditional-program values must align with official turns")
    if not torch.isfinite(outcomes).all() or bool(
        torch.any((outcomes < -1) | (outcomes > 1) | (outcomes != outcomes.round()))
    ):
        raise ValueError("conditional-program outcomes must be loss, tie, or win")
    if not torch.isfinite(old_values).all() or bool(torch.any(old_values.abs() > 1)):
        raise ValueError("conditional-program behavior values must lie in [-1, 1]")
    raw = outcomes.detach().float()[indices] - old_values.detach().float()
    if reference is None:
        mean = _episode_mean(raw, indices, outcomes.numel())
        variance = _episode_mean((raw - mean).square(), indices, outcomes.numel())
        scale = variance.clamp_min(0).sqrt()
        actor_update = torch.unique(outcomes.detach()).numel() >= 2
    else:
        mean = raw.new_tensor(reference.mean)
        scale = raw.new_tensor(reference.scale)
        actor_update = reference.actor_update
    values = raw
    if normalize and actor_update and math.isfinite(float(scale)) and float(scale) > 1e-6:
        values = (raw - mean) / scale
    return ProgramAdvantages(values, actor_update, mean.detach(), scale.detach())


def program_ppo_loss(
    output: ProgramSequenceOutput,
    old_joint_log_probability: Tensor,
    advantages: Tensor,
    outcomes: Tensor,
    episode_index: Tensor,
    *,
    clip_epsilon: float,
    value_loss_weight: float,
    entropy_weight: float,
    actor_update: bool,
    validate_inputs: bool = True,
) -> ProgramPpoLoss:
    """Apply one clipped ratio to each complete autoregressive turn program."""
    if not 0.0 < clip_epsilon < 1.0:
        raise ValueError("conditional-program PPO clip epsilon must be in (0, 1)")
    if value_loss_weight < 0.0 or entropy_weight < 0.0:
        raise ValueError("conditional-program PPO weights must be non-negative")
    turns = old_joint_log_probability.shape
    vectors = (
        output.joint_log_probability,
        output.normalized_entropy,
        output.factor_counts,
        advantages,
        episode_index,
    )
    if old_joint_log_probability.ndim != 1 or any(value.shape != turns for value in vectors):
        raise ValueError("conditional-program PPO statistics must align by turn")
    if output.outcome_logits.shape != (*turns, 3) or outcomes.ndim != 1:
        raise ValueError("conditional-program critic logits must have shape [turns,3]")
    indices = _indices(episode_index, outcomes.numel())
    active = output.factor_counts > 0
    if validate_inputs and any(
        bool(torch.any(~torch.isfinite(value)))
        for value in (
            output.joint_log_probability,
            output.normalized_entropy,
            output.outcome_logits,
            old_joint_log_probability,
            advantages,
        )
    ):
        raise ValueError("conditional-program PPO received a non-finite statistic")
    log_ratio = output.joint_log_probability - old_joint_log_probability.detach()
    ratio = torch.exp(log_ratio)
    frozen_advantages = advantages.detach()
    surrogate = torch.minimum(
        ratio * frozen_advantages,
        ratio.clamp(1.0 - clip_epsilon, 1.0 + clip_epsilon) * frozen_advantages,
    )
    zero = ratio.new_zeros(())
    policy = (
        -_masked_episode_mean(surrogate, indices, outcomes.numel(), active)
        if actor_update
        else zero
    )
    entropy = _masked_episode_mean(
        output.normalized_entropy,
        indices,
        outcomes.numel(),
        active,
    )
    labels = outcomes.long()[indices] + 1
    value_items = functional.cross_entropy(output.outcome_logits.float(), labels, reduction="none")
    value = _episode_mean(value_items, indices, outcomes.numel())
    probabilities = torch.softmax(output.outcome_logits.float(), dim=-1)
    value_accuracy = _episode_mean(
        (probabilities.argmax(dim=-1) == labels).to(probabilities.dtype),
        indices,
        outcomes.numel(),
    )
    targets = functional.one_hot(labels, num_classes=3).to(probabilities.dtype)
    value_brier = _episode_mean(
        (probabilities - targets).square().sum(dim=-1),
        indices,
        outcomes.numel(),
    )
    total = policy + value_loss_weight * value - entropy_weight * entropy
    detached_log_ratio = log_ratio.detach()
    approximate_kl = _masked_episode_mean(
        (torch.exp(detached_log_ratio) - 1.0) - detached_log_ratio,
        indices,
        outcomes.numel(),
        active,
    )
    clip_fraction = _masked_episode_mean(
        (torch.abs(ratio.detach() - 1.0) > clip_epsilon).to(ratio.dtype),
        indices,
        outcomes.numel(),
        active,
    )
    return ProgramPpoLoss(
        total=total,
        policy=policy,
        value=value,
        value_accuracy=value_accuracy,
        value_brier=value_brier,
        entropy=entropy,
        approximate_kl=approximate_kl,
        clip_fraction=clip_fraction,
        policy_turns=active.sum(),
        value_turns=active.new_tensor(active.numel(), dtype=torch.long),
    )


__all__ = [
    "ProgramAdvantageReference",
    "ProgramAdvantages",
    "ProgramPpoLoss",
    "program_ppo_loss",
    "terminal_program_advantages",
]
