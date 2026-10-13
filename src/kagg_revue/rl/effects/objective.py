"""Official-turn-balanced objectives for atomic-effect PPO."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor
from torch.nn import functional

from kagg_revue.policy.effects.schema import EffectPolicyOutput


@dataclass(frozen=True)
class EffectAdvantages:
    """One terminal W/D/L residual shared by every factor in a turn."""

    values: Tensor
    mean: Tensor
    scale: Tensor
    actor_update: bool


@dataclass(frozen=True)
class EffectPpoLoss:
    """Factor-wise PPO loss reduced on the official-turn surface."""

    total: Tensor
    policy: Tensor
    value: Tensor
    entropy: Tensor
    approximate_kl: Tensor
    clip_fraction: Tensor
    behavior_approximate_kl: Tensor
    behavior_clip_fraction: Tensor
    policy_factors: Tensor
    value_turns: Tensor


def _indices(episode_index: Tensor, episode_count: int) -> Tensor:
    if episode_count < 1 or episode_index.ndim != 1 or episode_index.numel() < 1:
        raise ValueError("effect objective requires represented episodes")
    if episode_index.is_floating_point() or episode_index.dtype == torch.bool:
        raise ValueError("effect episode indices must be integers")
    indices = episode_index.long()
    if bool(((indices < 0) | (indices >= episode_count)).any()):
        raise ValueError("effect factor refers outside the outcome batch")
    return indices


def official_turn_mean(
    values: Tensor,
    episode_index: Tensor,
    turn_index: Tensor,
    episode_count: int,
    turn_horizon: int,
    mask: Tensor | None = None,
) -> Tensor:
    """Mean factors within turns, turns within episodes, then episodes."""
    if values.ndim != 1 or values.shape != episode_index.shape:
        raise ValueError("effect reduction values must align with factors")
    episodes = _indices(episode_index, episode_count)
    if turn_horizon < 1 or turn_index.shape != values.shape:
        raise ValueError("effect reduction turn indices do not align")
    if turn_index.is_floating_point() or turn_index.dtype == torch.bool:
        raise ValueError("effect turn indices must be integers")
    turns = turn_index.long()
    if bool(((turns < 0) | (turns >= turn_horizon)).any()):
        raise ValueError("effect factor refers outside its episode horizon")
    active = torch.ones_like(episodes, dtype=torch.bool) if mask is None else mask
    if active.shape != values.shape or active.dtype != torch.bool:
        raise ValueError("effect reduction mask must be boolean and factor-aligned")
    weights = active.to(values.dtype)
    keys = episodes * turn_horizon + turns
    surface = episode_count * turn_horizon
    sums = torch.zeros(surface, dtype=values.dtype, device=values.device)
    counts = torch.zeros_like(sums)
    sums.scatter_add_(0, keys, values * weights)
    counts.scatter_add_(0, keys, weights)
    represented_turns = counts > 0
    if not bool(represented_turns.any()):
        return values.new_zeros(())
    turn_values = sums[represented_turns] / counts[represented_turns]
    turn_episodes = torch.arange(surface, device=values.device)[represented_turns] // turn_horizon
    episode_sums = torch.zeros(
        episode_count,
        dtype=values.dtype,
        device=values.device,
    )
    episode_counts = torch.zeros_like(episode_sums)
    episode_sums.scatter_add_(0, turn_episodes, turn_values)
    episode_counts.scatter_add_(0, turn_episodes, torch.ones_like(turn_values))
    represented_episodes = episode_counts > 0
    return (episode_sums[represented_episodes] / episode_counts[represented_episodes]).mean()


def factor_score_mean(
    values: Tensor,
    mask: Tensor,
    episode_count: int,
    turn_horizon: int,
) -> Tensor:
    """Sum causal scores with an action-independent episode/horizon denominator."""
    if episode_count < 1 or turn_horizon < 1:
        raise ValueError("effect score reduction requires a positive fixed horizon")
    if values.ndim != 1 or values.shape != mask.shape or mask.dtype != torch.bool:
        raise ValueError("effect score mask must align with factor values")
    return values.masked_fill(~mask, 0.0).sum() / (episode_count * turn_horizon)


def terminal_effect_advantages(
    outcomes: Tensor,
    old_values: Tensor,
    episode_index: Tensor,
    turn_index: Tensor,
    value_mask: Tensor,
    *,
    turn_horizon: int,
    normalize: bool,
    gae_lambda: float = 1.0,
) -> EffectAdvantages:
    """Broadcast one undiscounted terminal residual to every turn factor."""
    if outcomes.ndim != 1 or old_values.shape != episode_index.shape:
        raise ValueError("effect outcomes and behavior values do not align")
    if value_mask.shape != old_values.shape or value_mask.dtype != torch.bool:
        raise ValueError("effect value mask must align with factors")
    episodes = _indices(episode_index, outcomes.numel())
    if not bool(torch.isfinite(outcomes).all()) or bool(
        ((outcomes < -1) | (outcomes > 1) | (outcomes != outcomes.round())).any()
    ):
        raise ValueError("effect outcomes must be loss, tie, or win")
    if not bool(torch.isfinite(old_values).all()) or bool((old_values.abs() > 1).any()):
        raise ValueError("effect behavior values must lie in [-1, 1]")
    raw = outcomes.detach().float()[episodes] - old_values.detach().float()
    if not 0.0 <= gae_lambda <= 1.0:
        raise ValueError("effect GAE lambda must lie in [0, 1]")
    if gae_lambda != 1.0:
        # Only official turns consume time. Native pseudo-steps share one value.
        values = raw.new_zeros((outcomes.numel(), turn_horizon))
        present = torch.zeros_like(values, dtype=torch.bool)
        root_episodes = episodes[value_mask]
        root_turns = turn_index[value_mask].long()
        values[root_episodes, root_turns] = old_values[value_mask].float()
        present[root_episodes, root_turns] = True
        if int(present.sum()) != int(value_mask.sum()) or not bool(present[:, 0].all()):
            raise ValueError("effect GAE needs exactly one value per represented turn")
        if bool((present[:, 1:] & ~present[:, :-1]).any()):
            raise ValueError("effect GAE cannot bootstrap across missing official turns")
        advantage = torch.zeros_like(values)
        following_value = raw.new_zeros(outcomes.numel())
        following_advantage = torch.zeros_like(following_value)
        following_present = torch.zeros_like(following_value, dtype=torch.bool)
        for turn in range(turn_horizon - 1, -1, -1):
            terminal = present[:, turn] & ~following_present
            reward = outcomes.float() * terminal
            delta = reward + following_value - values[:, turn]
            following_advantage = (delta + gae_lambda * following_advantage) * present[:, turn]
            advantage[:, turn] = following_advantage
            following_value = values[:, turn]
            following_present = present[:, turn]
        raw = advantage[episodes, turn_index.long()]
    mean = official_turn_mean(
        raw,
        episodes,
        turn_index,
        outcomes.numel(),
        turn_horizon,
        value_mask,
    )
    variance = official_turn_mean(
        (raw - mean).square(),
        episodes,
        turn_index,
        outcomes.numel(),
        turn_horizon,
        value_mask,
    )
    scale = variance.clamp_min(0.0).sqrt()
    actor_update = torch.unique(outcomes.detach()).numel() >= 2
    values = raw
    if normalize and actor_update and bool(torch.isfinite(scale)) and float(scale) > 1e-6:
        values = (raw - mean) / scale
    return EffectAdvantages(values, mean.detach(), scale.detach(), actor_update)


def effect_behavior_cloning_loss(
    output: EffectPolicyOutput,
    selected: Tensor,
    policy_mask: Tensor,
    episode_index: Tensor,
    turn_index: Tensor,
    episode_count: int,
    turn_horizon: int,
) -> Tensor:
    """Return teacher-choice NLL balanced by official turn and episode."""
    if output.candidate_logits.shape[0] != selected.numel():
        raise ValueError("effect BC output does not align with teacher choices")
    log_probability = (
        torch.log_softmax(output.candidate_logits.float(), dim=-1)
        .gather(1, selected.long()[:, None])
        .squeeze(1)
    )
    return -official_turn_mean(
        log_probability,
        episode_index,
        turn_index,
        episode_count,
        turn_horizon,
        policy_mask,
    )


def effect_ppo_loss(
    output: EffectPolicyOutput,
    selected: Tensor,
    old_log_probability: Tensor,
    reference_log_probability: Tensor,
    reference_candidate_log_probabilities: Tensor | None,
    advantages: Tensor,
    outcomes: Tensor,
    episode_index: Tensor,
    turn_index: Tensor,
    policy_mask: Tensor,
    value_mask: Tensor,
    *,
    turn_horizon: int,
    clip_epsilon: float,
    value_loss_weight: float,
    entropy_weight: float,
    actor_update: bool,
    validate: bool = True,
) -> EffectPpoLoss:
    """Apply factor-wise clipping while retaining one value per turn."""
    if not 0.0 < clip_epsilon < 1.0:
        raise ValueError("effect PPO clip epsilon must be in (0, 1)")
    if value_loss_weight < 0.0 or entropy_weight < 0.0:
        raise ValueError("effect PPO loss weights must be non-negative")
    shape = selected.shape
    if selected.ndim != 1 or any(
        value.shape != shape
        for value in (
            old_log_probability,
            reference_log_probability,
            advantages,
            episode_index,
            turn_index,
            policy_mask,
            value_mask,
        )
    ):
        raise ValueError("effect PPO vectors must align by factor")
    if policy_mask.dtype != torch.bool or value_mask.dtype != torch.bool:
        raise ValueError("effect PPO masks must be boolean")
    if output.candidate_logits.shape[0] != selected.numel() or (
        output.outcome_logits.shape != (selected.numel(), 3)
    ):
        raise ValueError("effect PPO output does not align with factors")
    if actor_update and (
        reference_candidate_log_probabilities is None
        or reference_candidate_log_probabilities.shape != output.candidate_logits.shape
    ):
        raise ValueError("effect PPO reference distribution does not align")
    episodes = _indices(episode_index, outcomes.numel())
    labels = outcomes.long()[episodes] + 1
    value_items = functional.cross_entropy(output.outcome_logits.float(), labels, reduction="none")
    value = official_turn_mean(
        value_items,
        episodes,
        turn_index,
        outcomes.numel(),
        turn_horizon,
        value_mask,
    )
    if not actor_update:
        zero = value.detach().new_zeros(())
        return EffectPpoLoss(
            total=value_loss_weight * value,
            policy=zero,
            value=value,
            entropy=zero,
            approximate_kl=zero,
            clip_fraction=zero,
            behavior_approximate_kl=zero,
            behavior_clip_fraction=zero,
            policy_factors=policy_mask.sum(),
            value_turns=value_mask.sum(),
        )
    log_probabilities = torch.log_softmax(output.candidate_logits.float(), dim=-1)
    new_log_probability = log_probabilities.gather(1, selected.long()[:, None]).squeeze(1)
    probabilities = torch.softmax(output.candidate_logits.float(), dim=-1)
    finite_logs = log_probabilities.masked_fill(~torch.isfinite(log_probabilities), 0.0)
    entropy = -(probabilities * finite_logs).sum(dim=-1)
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
        raise ValueError("effect PPO received a non-finite statistic")

    policy_log_ratio = new_log_probability - reference_log_probability.detach()
    behavior_log_ratio = reference_log_probability.detach() - old_log_probability.detach()
    policy_ratio = torch.exp(policy_log_ratio)
    behavior_ratio = torch.exp(behavior_log_ratio)
    if validate and (
        not bool(torch.isfinite(policy_ratio).all())
        or not bool(torch.isfinite(behavior_ratio).all())
    ):
        raise ValueError("effect PPO received a non-finite likelihood ratio")
    frozen_advantage = advantages.detach()
    surrogate = behavior_ratio * torch.minimum(
        policy_ratio * frozen_advantage,
        policy_ratio.clamp(1.0 - clip_epsilon, 1.0 + clip_epsilon) * frozen_advantage,
    )
    local_actor = bool(policy_mask.any())
    policy = (
        -factor_score_mean(surrogate, policy_mask, outcomes.numel(), turn_horizon)
        if local_actor
        else policy_ratio.new_zeros(())
    )
    entropy_mean = official_turn_mean(
        entropy,
        episodes,
        turn_index,
        outcomes.numel(),
        turn_horizon,
        policy_mask,
    )
    total = policy + value_loss_weight * value
    if local_actor:
        total = total - entropy_weight * entropy_mean

    if reference_candidate_log_probabilities is None:
        raise RuntimeError("effect actor update lost its reference distribution")
    reference_logs = reference_candidate_log_probabilities.detach()
    reference_probabilities = reference_logs.exp()
    categorical_kl = (
        reference_probabilities
        * (reference_logs - log_probabilities.detach()).masked_fill(
            ~torch.isfinite(reference_logs), 0.0
        )
    ).sum(dim=-1)
    if validate and not bool(torch.isfinite(categorical_kl).all()):
        raise ValueError("effect PPO produced a non-finite categorical KL")

    def policy_mean(values: Tensor) -> Tensor:
        return official_turn_mean(
            values,
            episodes,
            turn_index,
            outcomes.numel(),
            turn_horizon,
            policy_mask,
        )

    detached_behavior_log_ratio = behavior_log_ratio.detach()
    detached_behavior_ratio = behavior_ratio.detach()
    return EffectPpoLoss(
        total=total,
        policy=policy,
        value=value,
        entropy=entropy_mean,
        approximate_kl=policy_mean(categorical_kl),
        clip_fraction=policy_mean(
            detached_behavior_ratio
            * (torch.abs(policy_ratio.detach() - 1.0) > clip_epsilon).to(policy_ratio.dtype)
        ),
        behavior_approximate_kl=policy_mean(
            torch.exp(detached_behavior_log_ratio) - 1.0 - detached_behavior_log_ratio
        ),
        behavior_clip_fraction=policy_mean(
            (torch.abs(detached_behavior_ratio - 1.0) > clip_epsilon).to(
                detached_behavior_ratio.dtype
            )
        ),
        policy_factors=policy_mask.sum(),
        value_turns=value_mask.sum(),
    )


__all__ = [
    "EffectAdvantages",
    "EffectPpoLoss",
    "effect_behavior_cloning_loss",
    "effect_ppo_loss",
    "factor_score_mean",
    "official_turn_mean",
    "terminal_effect_advantages",
]
