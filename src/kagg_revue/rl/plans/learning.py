"""GPU episode-minibatch optimization for structured-plan PPO."""

from __future__ import annotations

import random
from collections import defaultdict

import numpy as np
import torch
from torch import Tensor, nn
from torch import distributed as dist

from kagg_revue.policy.plans import PlanActions, PlanConditionalMasks, PlanInputs
from kagg_revue.policy.plans.model import StructuredPlanPolicy
from kagg_revue.rl.distributed import DistributedContext
from kagg_revue.rl.plans.config import StructuredPlanRlSettings
from kagg_revue.rl.plans.data import TensorPlanRolloutBatch
from kagg_revue.rl.plans.objective import (
    PlanAdvantages,
    plan_ppo_loss,
    terminal_wdl_advantages,
)


class PlanPolicyEvaluator(nn.Module):
    """Expose teacher-forced plan likelihood through the DDP forward path."""

    def __init__(self, policy: StructuredPlanPolicy) -> None:
        """Register the production policy as this module's only parameter tree."""
        super().__init__()
        self.policy = policy

    def forward(
        self,
        inputs: PlanInputs,
        actions: PlanActions,
        masks: PlanConditionalMasks,
        episode_index: torch.Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        """Evaluate one rank-local episode minibatch."""
        evaluated = self.policy.evaluate_actions(
            inputs,
            actions,
            masks,
            episode_index=episode_index,
            validate_inputs=False,
        )
        return (
            evaluated.joint_log_probability,
            evaluated.entropy,
            evaluated.value_logits,
        )


def audit_plan_behavior_likelihood(
    model: StructuredPlanPolicy,
    batch: TensorPlanRolloutBatch,
) -> dict[str, float]:
    """Check stateful rollout against full causal teacher-forced replay."""
    model.eval()
    with torch.inference_mode(), torch.autocast(
        device_type="cuda",
        dtype=torch.bfloat16,
    ):
        evaluated = model.evaluate_actions(
            batch.inputs,
            batch.actions,
            batch.masks,
            episode_index=batch.episode_index,
            validate=True,
            validate_inputs=False,
        )
    difference = (evaluated.joint_log_probability - batch.old_joint_log_probability).abs()
    maximum = float(difference.max())
    if not torch.isfinite(difference).all() or maximum > 0.1:
        raise RuntimeError("structured-plan stateful behavior likelihood failed replay")
    return {
        "maximum_absolute_log_probability_error": maximum,
        "mean_absolute_log_probability_error": float(difference.mean()),
    }


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


def _rows(
    batch: TensorPlanRolloutBatch, rows: torch.Tensor
) -> tuple[
    PlanInputs,
    PlanActions,
    PlanConditionalMasks,
]:
    inputs = PlanInputs(
        board=batch.inputs.board[rows],
        units=batch.inputs.units[rows],
        global_features=batch.inputs.global_features[rows],
        economic_state=batch.inputs.economic_state[rows],
        features=batch.inputs.features[rows],
        journal=batch.inputs.journal[rows],
        events=batch.inputs.events[rows],
        active_lines=batch.inputs.active_lines[rows],
        active_line_mask=batch.inputs.active_line_mask[rows],
        global_plan=batch.inputs.global_plan[rows],
    )
    actions = PlanActions(
        mode=batch.actions.mode[rows],
        line_operations=batch.actions.line_operations[rows],
        line_values=batch.actions.line_values[rows],
        global_operation=batch.actions.global_operation[rows],
        global_values=batch.actions.global_values[rows],
    )
    masks = PlanConditionalMasks(
        mode=batch.masks.mode[rows],
        line_operations=batch.masks.line_operations[rows],
        line_values=batch.masks.line_values[rows],
        global_operation=batch.masks.global_operation[rows],
        global_values=batch.masks.global_values[rows],
        factors=batch.masks.factors[rows],
    )
    return inputs, actions, masks


def _distributed_advantages(
    batch: TensorPlanRolloutBatch,
    settings: StructuredPlanRlSettings,
    context: DistributedContext,
) -> PlanAdvantages:
    """Normalize terminal advantages over the complete distributed panel."""
    normalize = settings.optimization.normalize_advantage
    if not context.enabled:
        return terminal_wdl_advantages(
            batch.outcomes,
            batch.old_values,
            batch.episode_index,
            batch.durations,
            normalize=normalize,
        )
    local = terminal_wdl_advantages(
        batch.outcomes,
        batch.old_values,
        batch.episode_index,
        batch.durations,
        normalize=False,
    )
    indices = batch.episode_index.long()
    counts = torch.zeros(
        batch.episodes,
        dtype=local.values.dtype,
        device=local.values.device,
    )
    sums = torch.zeros_like(counts)
    squared_sums = torch.zeros_like(counts)
    counts.scatter_add_(0, indices, torch.ones_like(local.values))
    sums.scatter_add_(0, indices, local.values)
    squared_sums.scatter_add_(0, indices, local.values.square())
    class_presence = torch.stack(
        tuple((batch.outcomes == outcome).any() for outcome in (-1, 0, 1))
    ).to(dtype=torch.float64)
    statistics = torch.cat(
        (
            torch.stack(
                (
                    (sums / counts).sum(),
                    (squared_sums / counts).sum(),
                    counts.new_tensor(float(batch.episodes)),
                )
            ).to(dtype=torch.float64),
            class_presence,
        )
    )
    dist.all_reduce(statistics, op=dist.ReduceOp.SUM)
    episode_count = statistics[2]
    mean = statistics[0] / episode_count
    variance = (statistics[1] / episode_count - mean.square()).clamp_min(0.0)
    scale = variance.sqrt()
    actor_update = int(torch.count_nonzero(statistics[3:] > 0)) >= 2
    values = local.values
    if normalize and actor_update and bool(torch.isfinite(scale)) and float(scale) > 1e-6:
        values = (values - mean.to(values.dtype)) / scale.to(values.dtype)
    return PlanAdvantages(
        values=values,
        actor_update=actor_update,
        mean=mean.to(values.dtype).detach(),
        scale=scale.to(values.dtype).detach(),
    )


def _global_loss_metrics(
    loss_values: tuple[torch.Tensor, ...],
    context: DistributedContext,
) -> tuple[float, ...]:
    values = torch.stack(tuple(value.detach().to(torch.float64) for value in loss_values))
    if context.enabled:
        dist.all_reduce(values, op=dist.ReduceOp.SUM)
        values /= context.world_size
    return tuple(float(value) for value in values)


def optimize_plan_batch(
    model: StructuredPlanPolicy,
    training_model: nn.Module,
    optimizer: torch.optim.Optimizer,
    batch: TensorPlanRolloutBatch,
    settings: StructuredPlanRlSettings,
    randomizer: random.Random,
    context: DistributedContext,
) -> dict[str, float | int | bool]:
    """Optimize exact joint plan ratios and a detached-encoder W/D/L head."""
    optimization = settings.optimization
    advantages = _distributed_advantages(batch, settings, context)
    metrics: dict[str, list[float]] = defaultdict(list)
    optimizer_steps = 0
    stopped_early = False
    critic_parameters = tuple(model.outcome_head.parameters())
    critic_ids = {id(parameter) for parameter in critic_parameters}
    actor_parameters = tuple(
        parameter for parameter in model.parameters() if id(parameter) not in critic_ids
    )
    training_model.train()
    local_minibatch_size = optimization.episodes_per_minibatch // context.world_size
    for _epoch in range(optimization.ppo_epochs):
        for episode_ids in _episode_minibatches(
            batch.episodes,
            local_minibatch_size,
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
            inputs, actions, masks = _rows(batch, rows)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                raw_evaluated = training_model(
                    inputs,
                    actions,
                    masks,
                    local_episode_index,
                )
                if (
                    not isinstance(raw_evaluated, tuple)
                    or len(raw_evaluated) != 3
                    or any(not isinstance(value, Tensor) for value in raw_evaluated)
                ):
                    raise TypeError("structured-plan DDP evaluator returned an invalid output")
                joint_log_probability, entropy, value_logits = raw_evaluated
                loss = plan_ppo_loss(
                    new_joint_log_probability=joint_log_probability,
                    old_joint_log_probability=batch.old_joint_log_probability[rows],
                    decision_entropy=entropy,
                    factor_counts=masks.factors.sum(dim=1),
                    outcome_logits=value_logits,
                    advantages=advantages.values[rows],
                    outcomes=batch.outcomes[selected_episodes],
                    episode_index=local_episode_index,
                    durations=batch.durations[rows],
                    clip_epsilon=optimization.clip_epsilon,
                    value_loss_weight=optimization.value_loss_weight,
                    entropy_weight=optimization.entropy_weight,
                    actor_update=advantages.actor_update,
                    validate_inputs=False,
                )
            (
                total_loss,
                policy_loss,
                value_loss,
                conditional_entropy,
                approximate_kl,
                clip_fraction,
            ) = _global_loss_metrics(
                (
                    loss.total,
                    loss.policy,
                    loss.value,
                    loss.entropy,
                    loss.approximate_kl,
                    loss.clip_fraction,
                ),
                context,
            )
            metrics["loss"].append(total_loss)
            metrics["policy_loss"].append(policy_loss)
            metrics["value_loss"].append(value_loss)
            metrics["conditional_entropy"].append(conditional_entropy)
            metrics["approximate_kl"].append(approximate_kl)
            metrics["clip_fraction"].append(clip_fraction)
            if approximate_kl > optimization.target_kl:
                stopped_early = True
                break
            loss.total.backward()  # type: ignore[no-untyped-call]
            actor_gradient_norm = torch.nn.utils.clip_grad_norm_(
                actor_parameters,
                optimization.gradient_clip,
            )
            critic_gradient_norm = torch.nn.utils.clip_grad_norm_(
                critic_parameters,
                optimization.gradient_clip,
            )
            if not bool(
                torch.isfinite(actor_gradient_norm)
                & torch.isfinite(critic_gradient_norm)
            ):
                raise FloatingPointError("structured-plan PPO produced a non-finite gradient")
            optimizer.step()
            optimizer_steps += 1
            actor_norm = float(actor_gradient_norm.detach())
            critic_norm = float(critic_gradient_norm.detach())
            metrics["actor_gradient_norm"].append(actor_norm)
            metrics["critic_gradient_norm"].append(critic_norm)
            metrics["gradient_norm"].append(max(actor_norm, critic_norm))
        if stopped_early:
            break
    training_model.eval()
    return {
        **{name: float(np.mean(values, dtype=np.float64)) for name, values in metrics.items()},
        "last_approximate_kl": metrics["approximate_kl"][-1],
        "maximum_approximate_kl": max(metrics["approximate_kl"]),
        "optimizer_steps": optimizer_steps,
        "actor_update": advantages.actor_update,
        "advantage_mean": float(advantages.mean),
        "advantage_scale": float(advantages.scale),
        "kl_early_stop": stopped_early,
    }


__all__ = [
    "PlanPolicyEvaluator",
    "audit_plan_behavior_likelihood",
    "optimize_plan_batch",
]
