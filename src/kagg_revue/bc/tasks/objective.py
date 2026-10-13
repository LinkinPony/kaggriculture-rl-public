"""Seat-balanced scratch-BC policy and direct terminal-W/D/L objectives."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor
from torch.nn import functional

from kagg_revue.bc.tasks.config import TaskBcOptimizationSettings
from kagg_revue.bc.tasks.dataset import ScratchTaskBcBatch
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.quantity import quantity_log_probability
from kagg_revue.rl.outcome import outcome_labels
from kagg_revue.rl.tasks.model import TaskTapeEvaluation


@dataclass(frozen=True)
class ScratchPolicyLoss:
    """Differentiable end-to-end policy objective and detached diagnostics."""

    total: Tensor
    task: Tensor
    market_action: Tensor
    market_quantity: Tensor
    task_decisions: int
    market_decisions: int
    quantity_decisions: int


@dataclass(frozen=True)
class ScratchOutcomeLoss:
    """Direct W/D/L calibration for the two critic-owned heads."""

    total: Tensor
    market: Tensor
    task: Tensor
    market_predictions: int
    task_predictions: int


def _sequence_means(
    values: Tensor,
    mask: Tensor,
    batch_size: int,
    episode_index: Tensor | None = None,
) -> Tensor:
    """Give every episode-seat equal weight regardless of decision count."""
    means: list[Tensor] = []
    for index in range(batch_size):
        selected = mask[index] if episode_index is None else mask & (episode_index == index)
        current = values[index][selected] if episode_index is None else values[selected]
        if current.numel():
            means.append(current.mean())
    if len(means) != batch_size:
        raise ValueError("scratch BC batch contains an episode without supervision")
    return torch.stack(means)


def scratch_policy_loss(
    output: TaskTapeEvaluation,
    batch: ScratchTaskBcBatch,
    architecture: ActorArchitecture,
    settings: TaskBcOptimizationSettings,
) -> ScratchPolicyLoss:
    """Train causal actor, market decoder, and task decoder in one forward pass."""
    task_active = output.tasks.masks.factors.bool().any(dim=1)
    task_nll = -output.tasks.joint_log_probability.float()
    task = _sequence_means(
        task_nll,
        task_active,
        batch.board.shape[0],
        batch.task_episode_index,
    ).mean()

    logits = output.market.policy.action_logits.float()
    vocabulary = logits.shape[-1]
    allowed = torch.arange(vocabulary, device=logits.device) >= (
        architecture.unit_action_tokens
    )
    market_logits = logits.masked_fill(~allowed, -torch.inf)
    safe_actions = torch.where(
        batch.market_factor_mask,
        batch.actions,
        torch.full_like(batch.actions, architecture.unit_action_tokens),
    )
    action_nll = functional.cross_entropy(
        market_logits.flatten(0, -2),
        safe_actions.flatten(),
        reduction="none",
    ).view_as(batch.actions)
    market = _sequence_means(
        action_nll,
        batch.market_factor_mask,
        batch.board.shape[0],
    ).mean()

    quantity_mask = batch.market_factor_mask & (batch.quantities > 0)
    safe_quantities = torch.where(
        quantity_mask,
        batch.quantities,
        torch.ones_like(batch.quantities),
    )
    quantity_logp = quantity_log_probability(
        output.market.policy.quantity_logits,
        safe_quantities,
    )
    invalid_quantity = quantity_mask & ~torch.isfinite(quantity_logp)
    if bool(invalid_quantity.any()):
        raise ValueError("scratch BC market quantity exceeds the actor vocabulary")
    quantity_values = torch.where(
        quantity_mask,
        -quantity_logp,
        torch.zeros_like(quantity_logp),
    )
    quantity_means: list[Tensor] = []
    for index in range(batch.board.shape[0]):
        selected = quantity_mask[index]
        quantity_means.append(
            quantity_values[index][selected].mean()
            if bool(selected.any())
            else quantity_values[index].sum() * 0.0
        )
    quantity = torch.stack(quantity_means).mean()
    total = (
        settings.task_loss_weight * task
        + settings.market_loss_weight
        * (market + settings.quantity_loss_weight * quantity)
    )
    return ScratchPolicyLoss(
        total=total,
        task=task.detach(),
        market_action=market.detach(),
        market_quantity=quantity.detach(),
        task_decisions=int(task_active.sum().detach().item()),
        market_decisions=int(batch.market_factor_mask.sum().detach().item()),
        quantity_decisions=int(quantity_mask.sum().detach().item()),
    )


def scratch_outcome_loss(
    output: TaskTapeEvaluation,
    batch: ScratchTaskBcBatch,
) -> ScratchOutcomeLoss:
    """Fit both random outcome heads to direct complete-match W/D/L labels."""
    labels = outcome_labels(batch.outcomes)
    market_nll = functional.cross_entropy(
        output.market.outcome_logits.flatten(0, -2),
        labels[:, None].expand_as(batch.turn_mask).flatten(),
        reduction="none",
    ).view_as(batch.turn_mask)
    market = _sequence_means(
        market_nll,
        batch.turn_mask,
        batch.board.shape[0],
    ).mean()

    task_labels = labels[batch.task_episode_index]
    task_nll = functional.cross_entropy(
        output.tasks.outcome_logits,
        task_labels,
        reduction="none",
    )
    task_mask = torch.ones_like(task_nll, dtype=torch.bool)
    task = _sequence_means(
        task_nll,
        task_mask,
        batch.board.shape[0],
        batch.task_episode_index,
    ).mean()
    return ScratchOutcomeLoss(
        total=market + task,
        market=market.detach(),
        task=task.detach(),
        market_predictions=int(batch.turn_mask.sum().detach().item()),
        task_predictions=int(task_nll.numel()),
    )


__all__ = [
    "ScratchOutcomeLoss",
    "ScratchPolicyLoss",
    "scratch_outcome_loss",
    "scratch_policy_loss",
]
