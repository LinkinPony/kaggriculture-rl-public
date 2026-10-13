"""SMDP terminal-WDL objectives for one joint macro selection at a time."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor
from torch.nn import functional


@dataclass(frozen=True)
class MacroAdvantages:
    """Frozen terminal-WDL advantages and balanced normalization diagnostics."""

    values: Tensor
    actor_update: bool
    mean: Tensor
    scale: Tensor


@dataclass(frozen=True)
class MacroPpoLoss:
    """Joint-selection PPO objective with episode-balanced reductions."""

    total: Tensor
    policy: Tensor
    value: Tensor
    entropy: Tensor
    approximate_kl: Tensor
    clip_fraction: Tensor
    macro_decisions: Tensor
    episodes: Tensor


def _validate_episode_index(episode_index: Tensor, episode_count: int) -> Tensor:
    if episode_count < 1:
        raise ValueError("episode-balanced reduction needs at least one episode")
    if episode_index.ndim != 1 or episode_index.numel() < 1:
        raise ValueError("episode index must contain at least one macro decision")
    if episode_index.is_floating_point() or episode_index.dtype == torch.bool:
        raise ValueError("episode index must use an integer dtype")
    indices = episode_index.long()
    if bool(torch.any((indices < 0) | (indices >= episode_count))):
        raise ValueError("macro decision refers to an episode outside the batch")
    counts = torch.bincount(indices, minlength=episode_count)
    if bool(torch.any(counts == 0)):
        raise ValueError("every episode needs at least one macro decision")
    return indices


def episode_balanced_mean(
    values: Tensor,
    episode_index: Tensor,
    episode_count: int,
) -> Tensor:
    """Average within each episode, then give every episode equal mass."""
    if values.ndim != 1 or values.shape != episode_index.shape:
        raise ValueError("episode-balanced values must have one item per macro decision")
    if not values.is_floating_point():
        raise ValueError("episode-balanced values must use a floating dtype")
    indices = _validate_episode_index(episode_index, episode_count)
    sums = torch.zeros(episode_count, dtype=values.dtype, device=values.device)
    counts = torch.zeros(episode_count, dtype=values.dtype, device=values.device)
    sums.scatter_add_(0, indices, values)
    counts.scatter_add_(0, indices, torch.ones_like(values))
    return (sums / counts).mean()


def _masked_episode_balanced_mean(
    values: Tensor,
    episode_index: Tensor,
    episode_count: int,
    mask: Tensor,
) -> Tensor:
    """Average active decisions within each represented active episode."""
    if mask.shape != values.shape or mask.dtype != torch.bool:
        raise ValueError("masked episode reduction needs one boolean per decision")
    indices = _validate_episode_index(episode_index, episode_count)
    active_rows = mask.nonzero(as_tuple=False).squeeze(-1)
    if active_rows.numel() == 0:
        return values.new_zeros(())
    active_indices = indices[active_rows]
    sums = torch.zeros(episode_count, dtype=values.dtype, device=values.device)
    counts = torch.zeros(episode_count, dtype=values.dtype, device=values.device)
    sums.scatter_add_(0, active_indices, values[active_rows])
    counts.scatter_add_(0, active_indices, torch.ones_like(values[active_rows]))
    represented = counts > 0
    return (sums[represented] / counts[represented]).mean()


def joint_macro_log_probability(
    factor_log_probability: Tensor,
    factor_mask: Tensor,
) -> Tensor:
    """Sum stochastic factors before PPO constructs one macro-level ratio.

    Clipping individual generator, selector, or parameter factors would define
    a different objective. The returned scalar per row is the only behavior
    statistic that should be persisted in ``MacroDecisionRecord``.
    """
    if factor_log_probability.ndim != 2 or factor_mask.shape != factor_log_probability.shape:
        raise ValueError("macro probability factors and mask must have shape [decisions, factors]")
    active = factor_mask.bool()
    if bool(torch.any(active.sum(dim=1) < 1)):
        raise ValueError("every macro selection needs at least one stochastic factor")
    if bool(torch.any(active & ~torch.isfinite(factor_log_probability))):
        raise ValueError("active macro probability factors must be finite")
    return factor_log_probability.masked_fill(~active, 0.0).sum(dim=1)


def terminal_wdl_advantages(
    outcomes: Tensor,
    old_values: Tensor,
    episode_index: Tensor,
    durations: Tensor,
    *,
    normalize: bool,
) -> MacroAdvantages:
    """Assign undiscounted terminal WDL once at every SMDP decision boundary.

    Durations are validated but do not repeat or reweight a macro choice. The
    competition objective is undiscounted, so a macro spanning many primitive
    turns still contributes exactly one policy likelihood term.
    """
    if outcomes.ndim != 1 or old_values.ndim != 1:
        raise ValueError("terminal outcomes and old values must be vectors")
    if old_values.shape != episode_index.shape or durations.shape != old_values.shape:
        raise ValueError("SMDP statistics must align with macro decisions")
    if durations.is_floating_point() or durations.dtype == torch.bool:
        raise ValueError("SMDP durations must use an integer dtype")
    if bool(torch.any(durations < 1)):
        raise ValueError("SMDP macro durations must be positive")
    if not torch.isfinite(old_values).all() or bool(
        torch.any((old_values < -1) | (old_values > 1))
    ):
        raise ValueError("old WDL values must be finite and lie in [-1, 1]")
    if not torch.isfinite(outcomes).all() or bool(
        torch.any((outcomes < -1) | (outcomes > 1) | (outcomes != outcomes.round()))
    ):
        raise ValueError("terminal outcomes must be loss, tie, or win")
    indices = _validate_episode_index(episode_index, outcomes.shape[0])
    raw = outcomes.detach().float()[indices] - old_values.detach().float()
    mean = episode_balanced_mean(raw, indices, outcomes.shape[0])
    variance = episode_balanced_mean((raw - mean).square(), indices, outcomes.shape[0])
    scale = variance.clamp_min(0.0).sqrt()
    actor_update = torch.unique(outcomes.detach()).numel() >= 2
    values = raw
    if normalize and actor_update and bool(torch.isfinite(scale)) and float(scale.item()) > 1e-6:
        values = (raw - mean) / scale
    return MacroAdvantages(
        values=values,
        actor_update=actor_update,
        mean=mean.detach(),
        scale=scale.detach(),
    )


def paired_direct_wdl_advantages(
    outcomes: Tensor,
    direct_outcomes: Tensor,
    episode_index: Tensor,
    durations: Tensor,
    *,
    normalize: bool,
) -> MacroAdvantages:
    """Use the same-job frozen DIRECT result as a policy-gradient baseline.

    The control match has the same seed, seat and opponent but never observes
    the sampled capability.  Subtracting its official terminal W/D/L therefore
    removes job difficulty without replacing the competition outcome.  The raw
    per-episode advantage lies in ``[-2, 2]`` and remains undiscounted.
    """
    if outcomes.ndim != 1 or direct_outcomes.shape != outcomes.shape:
        raise ValueError("paired DIRECT outcomes must be aligned vectors")
    if episode_index.ndim != 1 or durations.shape != episode_index.shape:
        raise ValueError("SMDP statistics must align with macro decisions")
    if durations.is_floating_point() or durations.dtype == torch.bool:
        raise ValueError("SMDP durations must use an integer dtype")
    if bool(torch.any(durations < 1)):
        raise ValueError("SMDP macro durations must be positive")
    for name, values in (
        ("terminal", outcomes),
        ("DIRECT control", direct_outcomes),
    ):
        if not torch.isfinite(values).all() or bool(
            torch.any((values < -1) | (values > 1) | (values != values.round()))
        ):
            raise ValueError(f"{name} outcomes must be loss, tie, or win")

    indices = _validate_episode_index(episode_index, outcomes.shape[0])
    episode_delta = outcomes.detach().float() - direct_outcomes.detach().float()
    raw = episode_delta[indices]
    mean = episode_balanced_mean(raw, indices, outcomes.shape[0])
    variance = episode_balanced_mean((raw - mean).square(), indices, outcomes.shape[0])
    scale = variance.clamp_min(0.0).sqrt()
    actor_update = bool(torch.any(episode_delta != 0))
    values = raw
    if normalize and actor_update and bool(torch.isfinite(scale)) and float(scale.item()) > 1e-6:
        values = (raw - mean) / scale
    return MacroAdvantages(
        values=values,
        actor_update=actor_update,
        mean=mean.detach(),
        scale=scale.detach(),
    )


def paired_direct_residual_advantages(
    outcomes: Tensor,
    direct_outcomes: Tensor,
    episode_index: Tensor,
    durations: Tensor,
    intervention_mask: Tensor,
    *,
    normalize: bool,
) -> MacroAdvantages:
    """Credit only actions that override the frozen DIRECT continuation.

    DIRECT is the non-trainable default. A sampled intervention receives its
    same-job terminal W/D/L difference; DIRECT decisions receive exactly zero
    actor weight and cannot be punished for another day's override.
    """
    if outcomes.ndim != 1 or direct_outcomes.shape != outcomes.shape:
        raise ValueError("paired DIRECT outcomes must be aligned vectors")
    if episode_index.ndim != 1 or durations.shape != episode_index.shape:
        raise ValueError("SMDP statistics must align with macro decisions")
    if intervention_mask.shape != episode_index.shape or intervention_mask.dtype != torch.bool:
        raise ValueError("residual intervention mask must be boolean and decision-aligned")
    if durations.is_floating_point() or durations.dtype == torch.bool:
        raise ValueError("SMDP durations must use an integer dtype")
    if bool(torch.any(durations < 1)):
        raise ValueError("SMDP macro durations must be positive")
    for name, outcome_values in (
        ("terminal", outcomes),
        ("DIRECT control", direct_outcomes),
    ):
        if not torch.isfinite(outcome_values).all() or bool(
            torch.any(
                (outcome_values < -1)
                | (outcome_values > 1)
                | (outcome_values != outcome_values.round())
            )
        ):
            raise ValueError(f"{name} outcomes must be loss, tie, or win")

    indices = _validate_episode_index(episode_index, outcomes.shape[0])
    episode_delta = outcomes.detach().float() - direct_outcomes.detach().float()
    active_episodes = torch.unique(indices[intervention_mask])
    active_delta = episode_delta[active_episodes]
    zero = episode_delta.new_zeros(())
    mean = active_delta.mean() if active_delta.numel() else zero
    scale = (
        (active_delta - mean).square().mean().clamp_min(0.0).sqrt()
        if active_delta.numel()
        else zero
    )
    values = torch.zeros_like(episode_index, dtype=torch.float32)
    values[intervention_mask] = episode_delta[indices[intervention_mask]]
    actor_update = bool(torch.any(values[intervention_mask] != 0))
    if normalize and actor_update and bool(torch.isfinite(scale)) and float(scale.item()) > 1e-6:
        values[intervention_mask] = values[intervention_mask] / scale
    return MacroAdvantages(
        values=values,
        actor_update=actor_update,
        mean=mean.detach(),
        scale=scale.detach(),
    )


def macro_ppo_loss(
    new_joint_log_probability: Tensor,
    old_joint_log_probability: Tensor,
    entropy_values: Tensor,
    outcome_logits: Tensor,
    advantages: Tensor,
    outcomes: Tensor,
    episode_index: Tensor,
    durations: Tensor,
    clip_epsilon: float,
    value_loss_weight: float,
    entropy_weight: float,
    *,
    actor_update: bool,
    policy_mask: Tensor | None = None,
    validate_inputs: bool = True,
) -> MacroPpoLoss:
    """Optimize one clipped joint ratio per macro choice and balanced WDL value.

    All inputs are flat over real macro decisions; padded candidates never
    enter the reduction. Decisions are first averaged within their episode and
    only then across episodes, preventing decision-heavy episodes from gaining
    more optimizer weight.
    """
    if not 0.0 < clip_epsilon < 1.0:
        raise ValueError("macro PPO clip epsilon must be between zero and one")
    if value_loss_weight < 0.0 or entropy_weight < 0.0:
        raise ValueError("macro PPO loss weights must be non-negative")
    expected = old_joint_log_probability.shape
    if (
        new_joint_log_probability.ndim != 1
        or expected != new_joint_log_probability.shape
        or entropy_values.shape != expected
        or advantages.shape != expected
        or episode_index.shape != expected
        or durations.shape != expected
    ):
        raise ValueError("macro PPO needs one scalar statistic per joint selection")
    if outcomes.ndim != 1 or outcome_logits.shape != (*expected, 3):
        raise ValueError("macro WDL logits must have shape [decisions, 3]")
    if (
        durations.is_floating_point()
        or durations.dtype == torch.bool
        or bool(torch.any(durations < 1))
    ):
        raise ValueError("macro PPO durations must be positive integers")
    indices = _validate_episode_index(episode_index, outcomes.shape[0])
    active_policy = (
        torch.ones_like(episode_index, dtype=torch.bool) if policy_mask is None else policy_mask
    )
    if active_policy.shape != expected or active_policy.dtype != torch.bool:
        raise ValueError("macro PPO policy mask must be boolean and decision-aligned")
    if validate_inputs:
        if bool(
            torch.any(~torch.isfinite(new_joint_log_probability))
            or torch.any(~torch.isfinite(old_joint_log_probability))
            or torch.any(~torch.isfinite(entropy_values))
            or torch.any(~torch.isfinite(advantages))
            or torch.any(~torch.isfinite(outcome_logits))
        ):
            raise ValueError("macro PPO received a non-finite statistic")
        if bool(torch.any((outcomes < -1) | (outcomes > 1) | (outcomes != outcomes.round()))):
            raise ValueError("macro PPO outcomes must be loss, tie, or win")

    log_ratio = new_joint_log_probability - old_joint_log_probability.detach()
    ratio = torch.exp(log_ratio)
    frozen_advantages = advantages.detach()
    surrogate = torch.minimum(
        ratio * frozen_advantages,
        ratio.clamp(1.0 - clip_epsilon, 1.0 + clip_epsilon) * frozen_advantages,
    )
    zero = torch.zeros((), dtype=ratio.dtype, device=ratio.device)
    local_actor_update = actor_update and bool(torch.any(active_policy))
    policy = (
        -_masked_episode_balanced_mean(
            surrogate,
            indices,
            outcomes.shape[0],
            active_policy,
        )
        if local_actor_update
        else zero
    )
    entropy = _masked_episode_balanced_mean(
        entropy_values,
        indices,
        outcomes.shape[0],
        active_policy,
    )

    labels = outcomes.long()[indices] + 1
    value_items = functional.cross_entropy(outcome_logits.float(), labels, reduction="none")
    value = episode_balanced_mean(value_items, indices, outcomes.shape[0])
    entropy_objective = entropy_weight * entropy if local_actor_update else entropy.detach() * 0.0
    total = policy + value_loss_weight * value - entropy_objective

    detached_log_ratio = log_ratio.detach()
    approximate_kl = _masked_episode_balanced_mean(
        (torch.exp(detached_log_ratio) - 1.0) - detached_log_ratio,
        indices,
        outcomes.shape[0],
        active_policy,
    )
    clip_fraction = _masked_episode_balanced_mean(
        (torch.abs(ratio.detach() - 1.0) > clip_epsilon).to(ratio.dtype),
        indices,
        outcomes.shape[0],
        active_policy,
    )
    return MacroPpoLoss(
        total=total,
        policy=policy,
        value=value,
        entropy=entropy,
        approximate_kl=approximate_kl,
        clip_fraction=clip_fraction,
        macro_decisions=torch.tensor(expected[0], dtype=torch.long, device=ratio.device),
        episodes=torch.tensor(outcomes.shape[0], dtype=torch.long, device=ratio.device),
    )


__all__ = [
    "MacroAdvantages",
    "MacroPpoLoss",
    "episode_balanced_mean",
    "joint_macro_log_probability",
    "macro_ppo_loss",
    "paired_direct_residual_advantages",
    "paired_direct_wdl_advantages",
    "terminal_wdl_advantages",
]
