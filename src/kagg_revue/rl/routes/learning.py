"""Terminal paired-control PPO update for route decisions."""

from __future__ import annotations

import math

import torch
from torch import Tensor

from kagg_revue.rl.routes.config import RouteOptimizationSettings
from kagg_revue.rl.routes.model import RouteActorCritic
from kagg_revue.rl.routes.rollout import RouteRolloutBatch


def _normalized(value: Tensor) -> Tensor:
    centered = value - value.mean()
    scale = centered.std(unbiased=False)
    if float(scale) < 1e-6:
        return centered
    return centered / scale


def optimize_route_batch(
    model: RouteActorCritic,
    optimizer: torch.optim.Optimizer,
    batch: RouteRolloutBatch,
    settings: RouteOptimizationSettings,
    *,
    device: torch.device,
    generator: torch.Generator,
) -> dict[str, float | int]:
    """Apply clipped PPO with the complete-match W/D/L residual return."""
    batch.validate()
    features = torch.as_tensor(batch.features, device=device)
    prior = torch.as_tensor(batch.prior_actions, device=device)
    actions = torch.as_tensor(batch.actions, device=device)
    actor_weights = torch.as_tensor(batch.actor_weights, device=device)
    old_log_probability = torch.as_tensor(batch.old_log_probabilities, device=device)
    old_values = torch.as_tensor(batch.old_values, device=device)
    episode_indices = torch.as_tensor(batch.episode_indices, device=device)
    game_rewards = torch.as_tensor(batch.game_rewards, device=device)
    returns = game_rewards[episode_indices]
    advantages = (returns - old_values) * actor_weights
    if settings.normalize_advantage:
        relevant = actor_weights > 0.0
        normalized = torch.zeros_like(advantages)
        if bool(relevant.any()):
            normalized[relevant] = _normalized(advantages[relevant])
        advantages = normalized

    decisions = features.shape[0]
    minibatch = min(settings.decisions_per_minibatch, decisions)
    policy_loss_sum = 0.0
    value_loss_sum = 0.0
    entropy_sum = 0.0
    kl_sum = 0.0
    clip_fraction_sum = 0.0
    gradient_norm_sum = 0.0
    samples = 0
    optimizer_steps = 0
    completed_epochs = 0
    model.train()
    for epoch in range(settings.ppo_epochs):
        order = torch.randperm(decisions, device=device, generator=generator)
        epoch_kl_sum = 0.0
        epoch_samples = 0
        for start in range(0, decisions, minibatch):
            indices = order[start : start + minibatch]
            logits, values = model(features[indices], prior[indices])
            log_probabilities = torch.log_softmax(logits, dim=-1)
            selected = log_probabilities.gather(1, actions[indices, None]).squeeze(1)
            log_ratio = selected - old_log_probability[indices]
            ratio = log_ratio.exp()
            current_advantage = advantages[indices]
            current_actor_weights = actor_weights[indices]
            unclipped = ratio * current_advantage
            clipped = ratio.clamp(
                1.0 - settings.clip_epsilon,
                1.0 + settings.clip_epsilon,
            ) * current_advantage
            actor_count = current_actor_weights.sum().clamp_min(1.0)
            policy_loss = -(
                torch.minimum(unclipped, clipped) * current_actor_weights
            ).sum() / actor_count
            value_loss = (values - returns[indices]).square().mean()
            probabilities = log_probabilities.exp()
            row_entropy = -(probabilities * log_probabilities).sum(dim=-1)
            entropy = (row_entropy * current_actor_weights).sum() / actor_count
            loss = (
                policy_loss
                + settings.value_loss_weight * value_loss
                - settings.entropy_weight * entropy
            )
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            gradient_norm = torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                settings.gradient_clip,
            )
            optimizer.step()

            count = int(indices.numel())
            approximate_kl = float(
                (
                    (old_log_probability[indices] - selected) * current_actor_weights
                ).sum().div(actor_count).detach()
            )
            clip_fraction = float(
                (
                    ((ratio - 1.0).abs() > settings.clip_epsilon).float()
                    * current_actor_weights
                ).sum().div(actor_count).detach()
            )
            policy_loss_sum += float(policy_loss.detach()) * count
            value_loss_sum += float(value_loss.detach()) * count
            entropy_sum += float(entropy.detach()) * count
            kl_sum += approximate_kl * count
            clip_fraction_sum += clip_fraction * count
            gradient_norm_sum += float(gradient_norm) * count
            epoch_kl_sum += approximate_kl * count
            samples += count
            epoch_samples += count
            optimizer_steps += 1
        completed_epochs = epoch + 1
        if epoch_samples and epoch_kl_sum / epoch_samples > settings.target_kl:
            break

    if samples < 1 or not math.isfinite(policy_loss_sum):
        raise RuntimeError("route PPO produced no finite optimizer samples")
    reward_variance = float(returns.var(unbiased=False))
    residual_variance = float((returns - old_values).var(unbiased=False))
    explained_variance = (
        0.0 if reward_variance < 1e-9 else 1.0 - residual_variance / reward_variance
    )
    return {
        "decisions": decisions,
        "actor_decisions": int((actor_weights > 0.0).sum()),
        "optimizer_steps": optimizer_steps,
        "completed_epochs": completed_epochs,
        "policy_loss": policy_loss_sum / samples,
        "value_loss": value_loss_sum / samples,
        "entropy": entropy_sum / samples,
        "approximate_kl": kl_sum / samples,
        "clip_fraction": clip_fraction_sum / samples,
        "gradient_norm": gradient_norm_sum / samples,
        "explained_variance_before_update": explained_variance,
    }


__all__ = ["optimize_route_batch"]
