"""Independent pseudo-step objectives for intent-ledger learning."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor
from torch.nn import functional

from kagg_revue.policy.intents.schema import IntentPolicyOutput


@dataclass(frozen=True)
class IntentAdvantages:
    """Frozen terminal-W/D/L residuals for every pseudo-step."""

    values: Tensor
    mean: Tensor
    scale: Tensor
    actor_update: bool


@dataclass(frozen=True)
class IntentPpoLoss:
    """Episode-balanced PPO loss and direct diagnostics."""

    total: Tensor
    policy: Tensor
    value: Tensor
    entropy: Tensor
    approximate_kl: Tensor
    clip_fraction: Tensor
    behavior_approximate_kl: Tensor
    behavior_clip_fraction: Tensor
    policy_steps: Tensor
    value_steps: Tensor


def _indices(episode_index: Tensor, episode_count: int) -> Tensor:
    if episode_count < 1 or episode_index.ndim != 1 or episode_index.numel() < 1:
        raise ValueError("intent objective requires represented episodes")
    if episode_index.is_floating_point() or episode_index.dtype == torch.bool:
        raise ValueError("intent episode indices must be integers")
    indices = episode_index.long()
    if bool(((indices < 0) | (indices >= episode_count)).any()):
        raise ValueError("intent pseudo-step refers outside the outcome batch")
    if bool((torch.bincount(indices, minlength=episode_count) == 0).any()):
        raise ValueError("every intent episode needs at least one pseudo-step")
    return indices


def episode_balanced_mean(
    values: Tensor,
    episode_index: Tensor,
    episode_count: int,
    mask: Tensor | None = None,
) -> Tensor:
    """Average steps within each represented episode, then across episodes."""
    if values.ndim != 1 or values.shape != episode_index.shape:
        raise ValueError("episode-balanced intent values must align with steps")
    indices = _indices(episode_index, episode_count)
    active = torch.ones_like(indices, dtype=torch.bool) if mask is None else mask
    if active.shape != values.shape or active.dtype != torch.bool:
        raise ValueError("intent reduction mask must be boolean and step-aligned")
    weights = active.to(values.dtype)
    sums = torch.zeros(episode_count, dtype=values.dtype, device=values.device)
    counts = torch.zeros_like(sums)
    sums.scatter_add_(0, indices, values * weights)
    counts.scatter_add_(0, indices, weights)
    represented = counts > 0
    if not bool(represented.any()):
        return values.new_zeros(())
    return (sums[represented] / counts[represented]).mean()


def terminal_intent_advantages(
    outcomes: Tensor,
    old_values: Tensor,
    episode_index: Tensor,
    *,
    normalize: bool,
) -> IntentAdvantages:
    """Assign the undiscounted terminal result at every augmented state."""
    if outcomes.ndim != 1 or old_values.shape != episode_index.shape:
        raise ValueError("intent outcomes and behavior values do not align")
    indices = _indices(episode_index, outcomes.numel())
    if not bool(torch.isfinite(outcomes).all()) or bool(
        ((outcomes < -1) | (outcomes > 1) | (outcomes != outcomes.round())).any()
    ):
        raise ValueError("intent outcomes must be loss, tie, or win")
    if not bool(torch.isfinite(old_values).all()) or bool((old_values.abs() > 1).any()):
        raise ValueError("intent behavior values must lie in [-1, 1]")
    raw = outcomes.detach().float()[indices] - old_values.detach().float()
    mean = episode_balanced_mean(raw, indices, outcomes.numel())
    variance = episode_balanced_mean((raw - mean).square(), indices, outcomes.numel())
    scale = variance.clamp_min(0.0).sqrt()
    actor_update = torch.unique(outcomes.detach()).numel() >= 2
    values = raw
    if normalize and actor_update and bool(torch.isfinite(scale)) and float(scale) > 1e-6:
        values = (raw - mean) / scale
    return IntentAdvantages(values, mean.detach(), scale.detach(), actor_update)


def intent_behavior_cloning_loss(
    output: IntentPolicyOutput,
    selected: Tensor,
    policy_mask: Tensor,
    episode_index: Tensor,
    turn_index: Tensor,
    episode_count: int,
    turn_horizon: int,
) -> Tensor:
    """Fit the joint canonical transaction likelihood on a fixed turn scale."""
    steps = selected.shape
    if (
        selected.ndim != 1
        or output.candidate_logits.shape[0] != selected.numel()
        or any(value.shape != steps for value in (policy_mask, episode_index, turn_index))
    ):
        raise ValueError("intent BC choices and indices do not align")
    if policy_mask.dtype != torch.bool:
        raise ValueError("intent BC forced-transition mask must be boolean")
    indices = _indices(episode_index, episode_count)
    if turn_horizon < 1 or turn_index.is_floating_point() or turn_index.dtype == torch.bool:
        raise ValueError("intent BC turn horizon and indices must be positive integers")
    turns = turn_index.long()
    if bool(((turns < 0) | (turns >= turn_horizon)).any()):
        raise ValueError("intent BC pseudo-step refers outside the fixed turn horizon")
    items = functional.cross_entropy(
        output.candidate_logits.float(), selected.long(), reduction="none"
    )
    # The choices within a transaction form one joint action. Summing their
    # NLL preserves that likelihood; dividing only by the fixed episode/turn
    # surface prevents a verbose teacher or policy from changing its weight.
    turn_rows = indices * turn_horizon + turns
    turn_sums = torch.zeros(
        episode_count * turn_horizon,
        dtype=items.dtype,
        device=items.device,
    )
    turn_sums.scatter_add_(0, turn_rows, items * policy_mask)
    return turn_sums.view(episode_count, turn_horizon).mean()


def intent_ppo_loss(
    output: IntentPolicyOutput,
    selected: Tensor,
    old_log_probability: Tensor,
    reference_log_probability: Tensor,
    reference_candidate_log_probabilities: Tensor | None,
    advantages: Tensor,
    outcomes: Tensor,
    episode_index: Tensor,
    policy_mask: Tensor,
    *,
    clip_epsilon: float,
    value_loss_weight: float,
    entropy_weight: float,
    actor_update: bool,
    validate: bool = True,
) -> IntentPpoLoss:
    """Apply PPO around a frozen learner-path reference policy.

    Rollout kernels retain the probability that actually sampled each action.
    A frozen pre-update policy evaluated through the learner's numerical path
    anchors PPO clipping and KL.  Their likelihood ratio corrects samples from
    the rollout implementation to that reference distribution without making
    fixed cross-kernel rounding look like a policy update.  The complete frozen
    categorical distribution provides an exact policy KL rather than a noisy
    selected-action estimate.
    """
    if not 0.0 < clip_epsilon < 1.0:
        raise ValueError("intent PPO clip epsilon must be in (0, 1)")
    if value_loss_weight < 0.0 or entropy_weight < 0.0:
        raise ValueError("intent PPO loss weights must be non-negative")
    steps = selected.shape
    if selected.ndim != 1 or any(
        value.shape != steps
        for value in (
            old_log_probability,
            reference_log_probability,
            advantages,
            episode_index,
            policy_mask,
        )
    ):
        raise ValueError("intent PPO vectors must align by pseudo-step")
    if output.candidate_logits.shape[0] != selected.numel() or output.outcome_logits.shape != (
        selected.numel(),
        3,
    ):
        raise ValueError("intent PPO model output does not align with pseudo-steps")
    if actor_update and (
        reference_candidate_log_probabilities is None
        or reference_candidate_log_probabilities.shape != output.candidate_logits.shape
    ):
        raise ValueError("intent PPO reference distribution does not align with candidates")
    if policy_mask.dtype != torch.bool:
        raise ValueError("intent forced-transition mask must be boolean")
    indices = _indices(episode_index, outcomes.numel())
    labels = outcomes.long()[indices] + 1
    value_items = functional.cross_entropy(output.outcome_logits.float(), labels, reduction="none")
    value = episode_balanced_mean(value_items, indices, outcomes.numel())
    if not actor_update:
        zero = value.detach().new_zeros(())
        return IntentPpoLoss(
            total=value_loss_weight * value,
            policy=zero,
            value=value,
            entropy=zero,
            approximate_kl=zero,
            clip_fraction=zero,
            behavior_approximate_kl=zero,
            behavior_clip_fraction=zero,
            policy_steps=policy_mask.sum(),
            value_steps=selected.new_tensor(selected.numel()),
        )
    log_probabilities = torch.log_softmax(output.candidate_logits.float(), dim=-1)
    new_log_probability = log_probabilities.gather(1, selected.long()[:, None]).squeeze(1)
    probabilities = torch.softmax(output.candidate_logits.float(), dim=-1)
    finite_log_probability = log_probabilities.masked_fill(~torch.isfinite(log_probabilities), 0.0)
    entropy = -(probabilities * finite_log_probability).sum(dim=-1)
    if validate and any(
        not bool(torch.isfinite(value).all())
        for value in (
            new_log_probability,
            old_log_probability,
            reference_log_probability,
            advantages,
            output.outcome_logits,
        )
    ):
        raise ValueError("intent PPO received a non-finite statistic")

    policy_log_ratio = new_log_probability - reference_log_probability.detach()
    behavior_log_ratio = reference_log_probability.detach() - old_log_probability.detach()
    policy_ratio = torch.exp(policy_log_ratio)
    behavior_ratio = torch.exp(behavior_log_ratio)
    if validate and (
        not bool(torch.isfinite(policy_ratio).all())
        or not bool(torch.isfinite(behavior_ratio).all())
    ):
        raise ValueError("intent PPO received a non-finite likelihood ratio")
    frozen = advantages.detach()
    surrogate = behavior_ratio * torch.minimum(
        policy_ratio * frozen,
        policy_ratio.clamp(1.0 - clip_epsilon, 1.0 + clip_epsilon) * frozen,
    )
    local_actor = actor_update and bool(policy_mask.any())
    policy = (
        -episode_balanced_mean(surrogate, indices, outcomes.numel(), policy_mask)
        if local_actor
        else policy_ratio.new_zeros(())
    )
    entropy_mean = episode_balanced_mean(entropy, indices, outcomes.numel(), policy_mask)
    total = policy + value_loss_weight * value
    if local_actor:
        total = total - entropy_weight * entropy_mean

    detached_behavior_log_ratio = behavior_log_ratio.detach()
    detached_behavior_ratio = behavior_ratio.detach()
    if reference_candidate_log_probabilities is None:
        raise RuntimeError("intent actor update lost its reference distribution")
    detached_reference_log_probabilities = reference_candidate_log_probabilities.detach()
    reference_probabilities = detached_reference_log_probabilities.exp()
    categorical_kl = (
        reference_probabilities
        * (
            detached_reference_log_probabilities
            - log_probabilities.detach()
        ).masked_fill(~torch.isfinite(detached_reference_log_probabilities), 0.0)
    ).sum(dim=-1)
    if validate and not bool(torch.isfinite(categorical_kl).all()):
        raise ValueError("intent PPO produced a non-finite categorical KL")
    approximate_kl = episode_balanced_mean(
        categorical_kl,
        indices,
        outcomes.numel(),
        policy_mask,
    )
    clip_fraction = episode_balanced_mean(
        detached_behavior_ratio
        * (torch.abs(policy_ratio.detach() - 1.0) > clip_epsilon).to(policy_ratio.dtype),
        indices,
        outcomes.numel(),
        policy_mask,
    )
    behavior_approximate_kl = episode_balanced_mean(
        torch.exp(detached_behavior_log_ratio) - 1.0 - detached_behavior_log_ratio,
        indices,
        outcomes.numel(),
        policy_mask,
    )
    behavior_clip_fraction = episode_balanced_mean(
        (torch.abs(detached_behavior_ratio - 1.0) > clip_epsilon).to(detached_behavior_ratio.dtype),
        indices,
        outcomes.numel(),
        policy_mask,
    )
    return IntentPpoLoss(
        total=total,
        policy=policy,
        value=value,
        entropy=entropy_mean,
        approximate_kl=approximate_kl,
        clip_fraction=clip_fraction,
        behavior_approximate_kl=behavior_approximate_kl,
        behavior_clip_fraction=behavior_clip_fraction,
        policy_steps=policy_mask.sum(),
        value_steps=selected.new_tensor(selected.numel()),
    )


__all__ = [
    "IntentAdvantages",
    "IntentPpoLoss",
    "episode_balanced_mean",
    "intent_behavior_cloning_loss",
    "intent_ppo_loss",
    "terminal_intent_advantages",
]
