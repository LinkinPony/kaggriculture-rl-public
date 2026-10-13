"""Pure terminal-W/D/L objectives for task and direct-market decisions."""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import Tensor
from torch.nn import functional

from kagg_revue.policy.model import PolicyOutput
from kagg_revue.policy.quantity import quantity_log_probability
from kagg_revue.policy.tasks.schema import TaskPolicyOutput
from kagg_revue.rl.outcome import outcome_labels


@dataclass(frozen=True)
class TerminalAdvantages:
    """Frozen Monte Carlo terminal-WDL advantages."""

    values: Tensor
    actor_update: bool
    mean: Tensor
    scale: Tensor


@dataclass(frozen=True)
class AdvantageReference:
    """Rollout-wide normalization shared by every episode minibatch."""

    mean: float
    scale: float
    actor_update: bool


@dataclass(frozen=True)
class TapePpoLoss:
    """One PPO surface with direct outcome critic diagnostics."""

    total: Tensor
    policy: Tensor
    value: Tensor
    entropy: Tensor
    approximate_kl: Tensor
    clip_fraction: Tensor
    policy_factors: Tensor
    value_factors: Tensor


def _validate_episode_index(
    episode_index: Tensor,
    episodes: int,
    *,
    validate_values: bool = True,
) -> Tensor:
    if episode_index.ndim != 1 or episode_index.numel() < 1:
        raise ValueError("task decisions need one nonempty episode-index vector")
    if episode_index.is_floating_point() or episode_index.dtype == torch.bool:
        raise ValueError("task episode indices must use an integer dtype")
    result = episode_index.long()
    if validate_values and bool(torch.any((result < 0) | (result >= episodes))):
        raise ValueError("task decision refers to an episode outside the batch")
    return result


def _episode_mean(values: Tensor, episode_index: Tensor, episodes: int) -> Tensor:
    if values.shape != episode_index.shape or values.ndim != 1:
        raise ValueError("episode-balanced values must align with decision indices")
    sums = torch.zeros(episodes, dtype=values.dtype, device=values.device)
    counts = torch.zeros_like(sums)
    sums.scatter_add_(0, episode_index, values)
    counts.scatter_add_(0, episode_index, torch.ones_like(values))
    represented = counts > 0
    means = sums / counts.clamp_min(1)
    weights = represented.to(values.dtype)
    return (means * weights).sum() / weights.sum().clamp_min(1)


def _masked_episode_mean(
    values: Tensor,
    episode_index: Tensor,
    episodes: int,
    mask: Tensor,
) -> Tensor:
    if mask.shape != values.shape:
        raise ValueError("episode-balanced mask must align with its values")
    weights = mask.to(values.dtype)
    sums = torch.zeros(episodes, dtype=values.dtype, device=values.device)
    counts = torch.zeros_like(sums)
    sums.scatter_add_(0, episode_index, values * weights)
    counts.scatter_add_(0, episode_index, weights)
    represented = counts > 0
    means = sums / counts.clamp_min(1)
    episode_weights = represented.to(values.dtype)
    return (means * episode_weights).sum() / episode_weights.sum().clamp_min(1)


def task_terminal_advantages(
    outcomes: Tensor,
    old_values: Tensor,
    episode_index: Tensor,
    *,
    normalize: bool,
    reference: AdvantageReference | None = None,
    validate_inputs: bool = True,
) -> TerminalAdvantages:
    """Assign the same undiscounted terminal W/D/L to every task boundary."""
    if outcomes.ndim != 1 or old_values.ndim != 1:
        raise ValueError("task outcomes and values must be vectors")
    indices = _validate_episode_index(
        episode_index,
        outcomes.shape[0],
        validate_values=validate_inputs,
    )
    if old_values.shape != indices.shape:
        raise ValueError("task behavior values must align with task decisions")
    if validate_inputs:
        outcome_labels(outcomes)
    raw = outcomes.float()[indices] - old_values.float()
    if reference is None:
        mean = _episode_mean(raw, indices, outcomes.shape[0])
        variance = _episode_mean((raw - mean).square(), indices, outcomes.shape[0])
        scale = variance.clamp_min(0.0).sqrt()
        actor_update = torch.unique(outcomes).numel() >= 2
    else:
        mean = raw.new_tensor(reference.mean)
        scale = raw.new_tensor(reference.scale)
        actor_update = reference.actor_update
    values = raw
    if normalize and actor_update:
        if reference is not None:
            if math.isfinite(reference.scale) and reference.scale > 1e-6:
                values = (raw - mean) / scale
        else:
            normalized = (raw - mean) / scale.clamp_min(1e-6)
            values = torch.where(torch.isfinite(scale) & (scale > 1e-6), normalized, raw)
    return TerminalAdvantages(values, actor_update, mean.detach(), scale.detach())


def market_terminal_advantages(
    outcomes: Tensor,
    old_values: Tensor,
    turn_mask: Tensor,
    *,
    normalize: bool,
    reference: AdvantageReference | None = None,
    validate_inputs: bool = True,
) -> TerminalAdvantages:
    """Assign terminal W/D/L to every actor-visible official turn."""
    if old_values.shape != turn_mask.shape or outcomes.shape != old_values.shape[:1]:
        raise ValueError("market values, outcomes, and turn mask do not align")
    if validate_inputs:
        outcome_labels(outcomes)
    valid = turn_mask.bool()
    raw = outcomes.float()[:, None] - old_values.float()
    valid_values = valid.to(raw.dtype)
    valid_count = valid_values.sum()
    if validate_inputs and bool(valid_count < 1):
        raise ValueError("market batch contains no valid turn")
    if reference is None:
        denominator = valid_count.clamp_min(1)
        mean = (raw * valid_values).sum() / denominator
        scale = (((raw - mean).square() * valid_values).sum() / denominator).sqrt()
        actor_update = torch.unique(outcomes).numel() >= 2
    else:
        mean = raw.new_tensor(reference.mean)
        scale = raw.new_tensor(reference.scale)
        actor_update = reference.actor_update
    values = raw
    if normalize and actor_update:
        if reference is not None:
            if math.isfinite(reference.scale) and reference.scale > 1e-6:
                values = (raw - mean) / scale
        else:
            normalized = (raw - mean) / scale.clamp_min(1e-6)
            values = torch.where(torch.isfinite(scale) & (scale > 1e-6), normalized, raw)
    return TerminalAdvantages(
        values.masked_fill(~valid, 0.0),
        actor_update,
        mean.detach(),
        scale.detach(),
    )


def task_ppo_loss(
    output: TaskPolicyOutput,
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
) -> TapePpoLoss:
    """Clip one combined conditional ratio per accepted task decision."""
    if not 0.0 < clip_epsilon < 1.0:
        raise ValueError("task PPO clip epsilon must lie in (0, 1)")
    decisions = output.joint_log_probability.shape[0]
    indices = _validate_episode_index(
        episode_index,
        outcomes.shape[0],
        validate_values=validate_inputs,
    )
    if (
        old_joint_log_probability.shape != (decisions,)
        or advantages.shape != (decisions,)
        or indices.shape != (decisions,)
        or output.outcome_logits.shape != (decisions, 3)
    ):
        raise ValueError("task PPO tensors do not align with task decisions")
    active = output.factor_counts > 0
    if validate_inputs and (
        bool(torch.any(active & ~torch.isfinite(old_joint_log_probability)))
        or bool(torch.any(active & ~torch.isfinite(output.joint_log_probability)))
    ):
        raise ValueError("task behavior probability is not finite")
    log_ratio = output.joint_log_probability - old_joint_log_probability
    ratio = torch.exp(log_ratio)
    surrogate = torch.minimum(
        ratio * advantages,
        ratio.clamp(1.0 - clip_epsilon, 1.0 + clip_epsilon) * advantages,
    )
    policy = (
        -_masked_episode_mean(surrogate, indices, outcomes.shape[0], active)
        if actor_update
        else ratio.new_zeros(())
    )
    entropy = _masked_episode_mean(output.entropy, indices, outcomes.shape[0], active)
    labels = outcome_labels(outcomes, validate=validate_inputs)[indices]
    value_items = functional.cross_entropy(output.outcome_logits.float(), labels, reduction="none")
    value = _episode_mean(value_items, indices, outcomes.shape[0])
    total = policy + value_loss_weight * value
    if actor_update:
        total = total - entropy_weight * entropy
    detached_ratio = ratio.detach()
    approximate_kl = _masked_episode_mean(
        (detached_ratio - 1.0) - log_ratio.detach(),
        indices,
        outcomes.shape[0],
        active,
    )
    clipped = (torch.abs(detached_ratio - 1.0) > clip_epsilon).float()
    clip_fraction = _masked_episode_mean(clipped, indices, outcomes.shape[0], active)
    return TapePpoLoss(
        total=total,
        policy=policy,
        value=value,
        entropy=entropy,
        approximate_kl=approximate_kl,
        clip_fraction=clip_fraction,
        policy_factors=active.sum(),
        value_factors=torch.tensor(decisions, device=active.device),
    )


def _market_statistics(
    output: PolicyOutput,
    actions: Tensor,
    quantities: Tensor,
    legal_mask: Tensor,
    factor_mask: Tensor,
    has_quantity: Tensor,
    *,
    validate: bool,
) -> tuple[Tensor, Tensor]:
    if legal_mask.shape != output.action_logits.shape:
        raise ValueError("market exact masks and action logits differ")
    if actions.shape != quantities.shape or actions.shape != factor_mask.shape:
        raise ValueError("market action tensors do not align")
    safe_actions = actions.clamp(0, output.action_logits.shape[-1] - 1)
    safe_legal = legal_mask.bool().clone()
    safe_legal[..., 0] |= ~factor_mask.bool()
    selected_legal = safe_legal.gather(-1, safe_actions[..., None]).squeeze(-1)
    if validate and bool(torch.any(factor_mask & ~selected_legal)):
        raise ValueError("stored market action is absent from its exact mask")
    logits = output.action_logits.float().masked_fill(~safe_legal, -torch.inf)
    log_probabilities = torch.log_softmax(logits, dim=-1)
    probabilities = log_probabilities.exp()
    action_log = log_probabilities.gather(-1, safe_actions[..., None]).squeeze(-1)
    action_entropy = -(probabilities * log_probabilities.masked_fill(~safe_legal, 0.0)).sum(dim=-1)
    quantity_factor = factor_mask & has_quantity[safe_actions]
    quantity_log = quantity_log_probability(output.quantity_logits, quantities.clamp_min(1))
    quantity_log_probabilities = torch.log_softmax(output.quantity_logits.float(), dim=-1)
    quantity_entropy = -(quantity_log_probabilities.exp() * quantity_log_probabilities).sum(dim=-1)
    joint = action_log + torch.where(quantity_factor, quantity_log, torch.zeros_like(quantity_log))
    entropy = action_entropy + torch.where(
        quantity_factor, quantity_entropy, torch.zeros_like(quantity_entropy)
    )
    return joint, entropy


def market_ppo_loss(
    output: PolicyOutput,
    outcome_logits: Tensor,
    actions: Tensor,
    quantities: Tensor,
    legal_mask: Tensor,
    policy_factor_mask: Tensor,
    old_log_probability: Tensor,
    advantages: Tensor,
    outcomes: Tensor,
    turn_mask: Tensor,
    has_quantity: Tensor,
    *,
    clip_epsilon: float,
    value_loss_weight: float,
    entropy_weight: float,
    actor_update: bool,
    validate_inputs: bool = True,
) -> TapePpoLoss:
    """Optimize only direct market samples while teacher-forcing compiler units."""
    if not 0.0 < clip_epsilon < 1.0:
        raise ValueError("market PPO clip epsilon must lie in (0, 1)")
    if advantages.shape != turn_mask.shape or outcome_logits.shape != (
        *turn_mask.shape,
        3,
    ):
        raise ValueError("market advantages or critic logits differ from turns")
    if old_log_probability.shape != actions.shape:
        raise ValueError("market behavior probabilities do not align with actions")
    active = policy_factor_mask.bool() & turn_mask.bool()[..., None]
    new_log_probability, entropy_values = _market_statistics(
        output,
        actions,
        quantities,
        legal_mask,
        active,
        has_quantity,
        validate=validate_inputs,
    )
    if validate_inputs and (
        bool(torch.any(active & ~torch.isfinite(old_log_probability)))
        or bool(torch.any(active & ~torch.isfinite(new_log_probability)))
    ):
        raise ValueError("market behavior probability is not finite")
    log_ratio = new_log_probability - old_log_probability
    ratio = torch.exp(log_ratio)
    surrogate = torch.minimum(
        ratio * advantages[..., None],
        ratio.clamp(1.0 - clip_epsilon, 1.0 + clip_epsilon) * advantages[..., None],
    )
    counts = active.sum(dim=(1, 2))
    represented = counts > 0
    policy_by_episode = (surrogate * active).sum(dim=(1, 2)) / counts.clamp_min(1)
    entropy_by_episode = (entropy_values * active).sum(dim=(1, 2)) / counts.clamp_min(1)
    episode_weights = represented.to(ratio.dtype)
    episode_denominator = episode_weights.sum().clamp_min(1)
    policy = -(policy_by_episode * episode_weights).sum() / episode_denominator
    if not actor_update:
        policy = ratio.new_zeros(())
    entropy = (entropy_by_episode * episode_weights).sum() / episode_denominator
    labels = outcome_labels(outcomes, validate=validate_inputs)[:, None].expand_as(turn_mask)
    value_items = functional.cross_entropy(
        outcome_logits.flatten(0, -2), labels.flatten(), reduction="none"
    ).view_as(turn_mask)
    value = (value_items * turn_mask).sum() / turn_mask.sum().clamp_min(1)
    total = policy + value_loss_weight * value
    if actor_update:
        total = total - entropy_weight * entropy
    detached_ratio = ratio.detach()
    denominator = active.sum().clamp_min(1)
    approximate_kl = (((detached_ratio - 1.0) - log_ratio.detach()) * active).sum() / denominator
    clip_fraction = ((torch.abs(detached_ratio - 1.0) > clip_epsilon) & active).sum() / denominator
    return TapePpoLoss(
        total=total,
        policy=policy,
        value=value,
        entropy=entropy,
        approximate_kl=approximate_kl,
        clip_fraction=clip_fraction,
        policy_factors=active.sum(),
        value_factors=turn_mask.sum(),
    )


__all__ = [
    "AdvantageReference",
    "TapePpoLoss",
    "TerminalAdvantages",
    "market_ppo_loss",
    "market_terminal_advantages",
    "task_ppo_loss",
    "task_terminal_advantages",
]
