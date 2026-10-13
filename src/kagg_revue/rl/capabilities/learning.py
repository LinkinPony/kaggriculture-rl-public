"""GPU minibatching and optimization for capability-space PPO."""

from __future__ import annotations

import random
from collections import defaultdict

import numpy as np
import torch
from torch import Tensor
from torch.nn import functional

from kagg_revue.policy.capability import CapabilityCandidates, CapabilitySelector
from kagg_revue.rl.capabilities.config import CapabilityRlSettings
from kagg_revue.rl.capabilities.data import TensorCapabilityRolloutBatch
from kagg_revue.rl.capabilities.objective import (
    episode_balanced_mean,
    macro_ppo_loss,
    paired_direct_residual_advantages,
    paired_direct_wdl_advantages,
    terminal_wdl_advantages,
)


def _candidate_inputs(
    batch: TensorCapabilityRolloutBatch,
    rows: Tensor,
) -> CapabilityCandidates:
    return CapabilityCandidates(
        mode=batch.mode[rows],
        int_fields=batch.int_fields[rows],
        edit_values=batch.edit_values[rows],
        edit_counts=batch.edit_counts[rows],
        candidate_features=batch.candidate_features[rows],
        mask=batch.candidate_mask[rows],
    )


def _episode_minibatches(
    episode_count: int,
    minibatch_size: int,
    randomizer: random.Random,
) -> tuple[tuple[int, ...], ...]:
    order = list(range(episode_count))
    randomizer.shuffle(order)
    return tuple(
        tuple(order[start : start + minibatch_size])
        for start in range(0, episode_count, minibatch_size)
    )


def optimize_capability_batch(
    model: CapabilitySelector,
    optimizer: torch.optim.Optimizer,
    batch: TensorCapabilityRolloutBatch,
    settings: CapabilityRlSettings,
    randomizer: random.Random,
) -> dict[str, float | int | bool]:
    """Run episode-balanced PPO and selected-candidate W/D/L learning."""
    optimization = settings.optimization
    policy_mask: Tensor | None = None
    if settings.objective.reward == "paired_direct_residual_wdl":
        if batch.direct_outcomes is None:
            raise ValueError("paired DIRECT PPO requires control-match outcomes")
        selected_modes = batch.mode.gather(
            1,
            batch.selected_indices[:, None],
        ).squeeze(1)
        policy_mask = selected_modes != 0
        advantages = paired_direct_residual_advantages(
            batch.outcomes,
            batch.direct_outcomes,
            batch.episode_index,
            batch.durations,
            policy_mask,
            normalize=optimization.normalize_advantage,
        )
    elif settings.objective.reward == "paired_direct_terminal_wdl":
        if batch.direct_outcomes is None:
            raise ValueError("paired DIRECT PPO requires control-match outcomes")
        advantages = paired_direct_wdl_advantages(
            batch.outcomes,
            batch.direct_outcomes,
            batch.episode_index,
            batch.durations,
            normalize=optimization.normalize_advantage,
        )
    else:
        advantages = terminal_wdl_advantages(
            batch.outcomes,
            batch.old_values,
            batch.episode_index,
            batch.durations,
            normalize=optimization.normalize_advantage,
        )
    metrics: dict[str, list[float]] = defaultdict(list)
    optimizer_steps = 0
    stopped_early = False
    model.train()
    for _epoch in range(optimization.ppo_epochs):
        for episode_ids in _episode_minibatches(
            batch.episodes,
            optimization.episodes_per_minibatch,
            randomizer,
        ):
            selected_episodes = torch.tensor(
                episode_ids,
                dtype=torch.long,
                device=batch.episode_index.device,
            )
            membership = batch.episode_index[:, None] == selected_episodes[None]
            rows = membership.any(dim=1).nonzero(as_tuple=False).squeeze(-1)
            local_episode_index = membership[rows].to(torch.int64).argmax(dim=1)
            candidates = _candidate_inputs(batch, rows)
            search_features = (
                batch.search_features[rows] if settings.abi.search_features > 0 else None
            )
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                evaluated = model.evaluate_actions(
                    batch.root_features[rows],
                    candidates,
                    batch.search_logits[rows],
                    batch.selected_indices[rows],
                    search_features,
                    exploration_epsilon=(settings.search.behavior_exploration_epsilon),
                )
                loss = macro_ppo_loss(
                    evaluated.log_probability,
                    batch.old_joint_log_probability[rows],
                    evaluated.entropy,
                    evaluated.policy.value_logits,
                    advantages.values[rows],
                    batch.outcomes[selected_episodes],
                    local_episode_index,
                    batch.durations[rows],
                    optimization.clip_epsilon,
                    optimization.value_loss_weight,
                    optimization.entropy_weight,
                    actor_update=advantages.actor_update,
                    policy_mask=(None if policy_mask is None else policy_mask[rows]),
                    validate_inputs=False,
                )
                candidate_value = loss.total.new_zeros(())
                if optimization.candidate_value_loss_weight > 0.0:
                    row_index = torch.arange(rows.numel(), device=rows.device)
                    candidate_logits = evaluated.policy.candidate_value_logits[
                        row_index,
                        batch.selected_indices[rows],
                    ]
                    labels = batch.outcomes[selected_episodes][local_episode_index].long() + 1
                    candidate_items = functional.cross_entropy(
                        candidate_logits.float(),
                        labels,
                        reduction="none",
                    )
                    candidate_value = episode_balanced_mean(
                        candidate_items,
                        local_episode_index,
                        len(episode_ids),
                    )
                total: Tensor = loss.total + (
                    optimization.candidate_value_loss_weight * candidate_value
                )
            optimizer.zero_grad(set_to_none=True)
            total.backward()  # type: ignore[no-untyped-call]
            gradient_norm = torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                optimization.gradient_clip,
            )
            if not bool(torch.isfinite(gradient_norm)):
                raise FloatingPointError("capability PPO produced a non-finite gradient")
            optimizer.step()
            optimizer_steps += 1
            metrics["loss"].append(float(total.detach()))
            metrics["policy_loss"].append(float(loss.policy.detach()))
            metrics["root_value_loss"].append(float(loss.value.detach()))
            if optimization.candidate_value_loss_weight > 0.0:
                metrics["candidate_value_loss"].append(float(candidate_value.detach()))
            metrics["entropy"].append(float(loss.entropy.detach()))
            metrics["approximate_kl"].append(float(loss.approximate_kl.detach()))
            metrics["clip_fraction"].append(float(loss.clip_fraction.detach()))
            metrics["gradient_norm"].append(float(gradient_norm.detach()))
            if float(loss.approximate_kl.detach()) > optimization.target_kl:
                stopped_early = True
                break
        if stopped_early:
            break
    model.eval()
    return {
        **{name: float(np.mean(values, dtype=np.float64)) for name, values in metrics.items()},
        "optimizer_steps": optimizer_steps,
        "actor_update": advantages.actor_update,
        "advantage_mean": float(advantages.mean),
        "advantage_scale": float(advantages.scale),
        "kl_early_stop": stopped_early,
    }


__all__ = ["optimize_capability_batch"]
