"""Guarded episode-minibatch optimization for atomic-effect PPO."""

from __future__ import annotations

import random
from collections import defaultdict
from contextlib import nullcontext
from copy import deepcopy

import numpy as np
import torch
from torch import Tensor, nn
from torch.optim import Optimizer

from kagg_revue.policy.effects.model import EffectActorCritic
from kagg_revue.rl.distributed import DistributedContext, single_process_context
from kagg_revue.rl.effects.chunked import backward_sharded_ppo
from kagg_revue.rl.effects.config import EffectOptimizationSettings
from kagg_revue.rl.effects.data import EffectRolloutBatch
from kagg_revue.rl.effects.initialization import effect_optimizer_parameters
from kagg_revue.rl.effects.objective import effect_ppo_loss
from kagg_revue.rl.effects.optimizers import IndependentAdamW
from kagg_revue.rl.effects.replay import (
    EffectSequenceEvaluator,
    _autocast,
    _clear_disabled_actor_gradients,
    _enable_trainable_recurrent_backends,
    _evaluate,
    _global_advantages,
    _global_maximum,
    _global_metric_row,
    _prefetched_subsets,
    _selected_log_probability,
    _synchronize_model_gradients,
    _zero_parameter_anchor,
    audit_effect_behavior,
)
from kagg_revue.rl.effects.trust_region import EffectPolicyGuard, guarded_optimizer_step


def optimize_effect_batch(
    model: EffectActorCritic,
    optimizer: Optimizer,
    batch: EffectRolloutBatch,
    settings: EffectOptimizationSettings,
    device: torch.device,
    randomizer: random.Random,
    *,
    training_model: nn.Module | None = None,
    reference_model: EffectActorCritic | None = None,
    context: DistributedContext | None = None,
    actor_requested: bool = True,
    critic_actor_gradient: bool = True,
    gae_lambda: float = 1.0,
) -> dict[str, object]:
    """Run behavior-corrected factor-wise PPO over complete episodes."""
    distributed = context or single_process_context(device)
    evaluator = training_model or EffectSequenceEvaluator(
        model,
        critic_actor_gradient=critic_actor_gradient,
    )
    if settings.episodes_per_minibatch % distributed.world_size:
        raise ValueError("effect logical minibatch must divide across learner ranks")
    local_minibatch = settings.episodes_per_minibatch // distributed.world_size
    if batch.episode_count % local_minibatch:
        raise ValueError("effect local episodes must fill learner minibatches")
    microbatch_size = settings.effective_episodes_per_microbatch
    if microbatch_size > local_minibatch or local_minibatch % microbatch_size:
        raise ValueError("effect microbatch must divide the local minibatch")
    advantages = _global_advantages(
        batch,
        distributed,
        normalize=settings.normalize_advantage,
        actor_requested=actor_requested,
        gae_lambda=gae_lambda,
    )
    advantage_mean = float(advantages.mean)
    advantage_scale = float(advantages.scale)
    actor_update = advantages.actor_update
    metrics: dict[str, list[float]] = defaultdict(list)
    optimizer_steps = 0
    optimizer_episodes = 0
    evaluated_minibatches = 0
    physical_microbatches = 0
    completed_epochs = 0
    input_materialization_seconds = 0.0
    input_wait_seconds = 0.0
    stopped_early = False
    trigger_kl: float | None = None
    maximum_behavior_log_ratio = 0.0
    reference_forward_microbatches = 0
    policy_episodes = {
        int(index) for index in torch.unique(batch.episode_index[batch.policy_mask]).tolist()
    }
    model.train()
    model.actor.eval()
    _enable_trainable_recurrent_backends(model)
    frozen_reference: EffectActorCritic | None = None
    reference_cache: Tensor | None = None
    rollout_reference = bool(batch.decision_shards) and all(
        shard.reference_candidate_log_probabilities is not None for shard in batch.decision_shards
    )
    if actor_update and not rollout_reference:
        if reference_model is model:
            raise ValueError("effect PPO reference cannot alias the trainable model")
        frozen_reference = reference_model or deepcopy(model).to(device)
        frozen_reference.load_state_dict(model.state_dict(), strict=True)
        frozen_reference.train()
        frozen_reference.actor.eval()
        frozen_reference.zero_grad(set_to_none=True)
        if settings.ppo_epochs > 1:
            reference_cache = torch.full(
                (batch.factor_count, int(batch.candidate_counts.max())),
                -torch.inf,
                dtype=torch.float32,
                device=device,
            )
    actor_parameters, critic_parameters = effect_optimizer_parameters(model)
    guard = (
        EffectPolicyGuard(
            model,
            batch,
            device,
            episode_count=microbatch_size,
            candidate_elements_per_chunk=settings.candidate_elements_per_chunk,
        )
        if actor_update
        else None
    )
    initial_guard_kl = 0.0 if guard is None else distributed.maximum(guard())
    if not np.isfinite(initial_guard_kl) or initial_guard_kl > settings.target_kl:
        raise RuntimeError(
            f"effect rollout/reference KL failed before learning: {initial_guard_kl}"
        )
    actor_steps = 0
    rejected_attempts = 0
    maximum_trial_kl = initial_guard_kl
    accepted_guard_kl = initial_guard_kl
    minimum_step_scale = 1.0

    def critic_only() -> bool:
        return not (actor_update and not stopped_early)

    for epoch in range(settings.ppo_epochs):
        order = list(range(batch.episode_count))
        randomizer.shuffle(order)
        logical_batches = tuple(
            order[start : start + local_minibatch]
            for start in range(0, len(order), local_minibatch)
        )
        microbatches = tuple(
            tuple(
                episodes[start : start + microbatch_size]
                for start in range(0, len(episodes), microbatch_size)
            )
            for episodes in logical_batches
        )
        prepared = _prefetched_subsets(
            batch,
            tuple(value for group in microbatches for value in group),
            device,
            critic_only=critic_only,
        )
        try:
            for episodes, logical_microbatches in zip(
                logical_batches,
                microbatches,
                strict=True,
            ):
                minibatch_actor = actor_update and not stopped_early
                optimizer.zero_grad(set_to_none=True)
                logical_metrics: dict[str, Tensor] = {}
                behavior_log_ratio_max = torch.zeros((), device=device)
                logical_policy_episodes = sum(episode in policy_episodes for episode in episodes)
                rank_scales = distributed.loss_scales(
                    torch.tensor(
                        [len(episodes), logical_policy_episodes],
                        dtype=torch.float32,
                        device=device,
                    )
                )
                for microbatch_index, micro_episodes in enumerate(logical_microbatches):
                    selected, materialization, wait = next(prepared)
                    input_materialization_seconds += materialization
                    input_wait_seconds += wait
                    raw_advantages = (
                        selected.outcomes.float()[selected.episode_index]
                        - selected.old_value.detach().float()
                    )
                    selected_advantages = raw_advantages
                    if (
                        settings.normalize_advantage
                        and minibatch_actor
                        and np.isfinite(advantage_scale)
                        and advantage_scale > 1e-6
                    ):
                        selected_advantages = (raw_advantages - advantage_mean) / advantage_scale
                    value_weight = len(micro_episodes) / len(episodes)
                    micro_policy_episodes = sum(
                        episode in policy_episodes for episode in micro_episodes
                    )
                    policy_weight = (
                        micro_policy_episodes / logical_policy_episodes
                        if logical_policy_episodes
                        else 0.0
                    )
                    chunked = (
                        minibatch_actor and rollout_reference and bool(selected.decision_shards)
                    )
                    if chunked:
                        loss, local_behavior_ratio_max = backward_sharded_ppo(
                            model,
                            selected,
                            selected_advantages,
                            settings,
                            value_scale=rank_scales[0] * value_weight,
                            policy_scale=rank_scales[1] * policy_weight,
                            critic_actor_gradient=critic_actor_gradient,
                            validate=optimizer_steps == 0,
                        )
                        behavior_log_ratio_max = torch.maximum(
                            behavior_log_ratio_max,
                            local_behavior_ratio_max,
                        )
                    else:
                        reference_candidates: Tensor | None = None
                        if not minibatch_actor:
                            reference_log_probability = selected.old_log_probability.detach()
                        elif selected.reference_candidate_log_probabilities is not None:
                            reference_candidates = (
                                selected.reference_candidate_log_probabilities.detach()
                            )
                            reference_log_probability = (
                                reference_candidates.gather(
                                    1,
                                    selected.selected.long()[:, None],
                                )
                                .squeeze(1)
                                .detach()
                            )
                        elif frozen_reference is None:
                            reference_log_probability = selected.old_log_probability.detach()
                        elif reference_cache is not None and epoch > 0:
                            width = selected.candidate_width
                            reference_candidates = reference_cache.index_select(
                                0,
                                selected.factor_index,
                            )[:, :width]
                            reference_log_probability = (
                                reference_candidates.gather(
                                    1,
                                    selected.selected.long()[:, None],
                                )
                                .squeeze(1)
                                .detach()
                            )
                        else:
                            with torch.no_grad(), _autocast(device):
                                reference_output = _evaluate(
                                    frozen_reference,
                                    selected,
                                    validate=optimizer_steps == 0,
                                )
                                reference_log_probability = _selected_log_probability(
                                    reference_output,
                                    selected.selected,
                                ).detach()
                                reference_candidates = torch.log_softmax(
                                    reference_output.candidate_logits.float(), dim=-1
                                ).detach()
                            reference_forward_microbatches += 1
                            if reference_cache is not None:
                                reference_cache[
                                    selected.factor_index,
                                    : reference_candidates.shape[1],
                                ] = reference_candidates
                        last = microbatch_index + 1 == len(logical_microbatches)
                        no_sync = getattr(evaluator, "no_sync", None)
                        synchronization = (
                            no_sync() if not last and callable(no_sync) else nullcontext()
                        )
                        with synchronization, _autocast(device):
                            output = _evaluate(
                                model,
                                selected,
                                training_model=evaluator,
                                value_only=not minibatch_actor,
                                validate=optimizer_steps == 0,
                            )
                            loss = effect_ppo_loss(
                                output,
                                selected.selected,
                                selected.old_log_probability,
                                reference_log_probability,
                                reference_candidates,
                                selected_advantages,
                                selected.outcomes,
                                selected.episode_index,
                                selected.turn_index,
                                selected.policy_mask,
                                selected.value_mask,
                                turn_horizon=selected.board.shape[1],
                                clip_epsilon=settings.clip_epsilon,
                                value_loss_weight=settings.value_loss_weight,
                                entropy_weight=settings.entropy_weight,
                                actor_update=minibatch_actor,
                                validate=optimizer_steps == 0,
                            )
                        weighted = (
                            rank_scales[0] * settings.value_loss_weight * value_weight * loss.value
                        )
                        if minibatch_actor and policy_weight:
                            weighted = weighted + rank_scales[0] * value_weight * loss.policy
                            weighted = weighted - (
                                rank_scales[1]
                                * policy_weight
                                * settings.entropy_weight
                                * loss.entropy
                            )
                        weighted = weighted + _zero_parameter_anchor(model)
                        weighted.backward()  # type: ignore[no-untyped-call]
                    physical_microbatches += 1
                    contributions = {
                        "policy_loss": rank_scales[0] * value_weight * loss.policy,
                        "value_loss": rank_scales[0] * value_weight * loss.value,
                        "entropy": rank_scales[1] * policy_weight * loss.entropy,
                        "approximate_kl": (rank_scales[1] * policy_weight * loss.approximate_kl),
                        "clip_fraction": (rank_scales[1] * policy_weight * loss.clip_fraction),
                        "behavior_approximate_kl": (
                            rank_scales[1] * policy_weight * loss.behavior_approximate_kl
                        ),
                        "behavior_clip_fraction": (
                            rank_scales[1] * policy_weight * loss.behavior_clip_fraction
                        ),
                    }
                    for name, contribution in contributions.items():
                        detached = contribution.detach()
                        logical_metrics[name] = (
                            detached
                            if name not in logical_metrics
                            else logical_metrics[name] + detached
                        )
                    if not chunked and minibatch_actor and bool(selected.policy_mask.any()):
                        behavior_ratio = (
                            reference_log_probability - selected.old_log_probability.detach()
                        )
                        behavior_log_ratio_max = torch.maximum(
                            behavior_log_ratio_max,
                            behavior_ratio[selected.policy_mask].abs().max(),
                        )
                global_metrics = _global_metric_row(logical_metrics, distributed)
                maximum_behavior_log_ratio = max(
                    maximum_behavior_log_ratio,
                    _global_maximum(behavior_log_ratio_max, distributed),
                )
                global_metrics["loss"] = global_metrics["policy_loss"] + (
                    settings.value_loss_weight * global_metrics["value_loss"]
                )
                if minibatch_actor:
                    global_metrics["loss"] -= settings.entropy_weight * global_metrics["entropy"]
                for name, metric_value in global_metrics.items():
                    metrics[name].append(metric_value)
                evaluated_minibatches += 1
                if minibatch_actor and global_metrics["approximate_kl"] > settings.target_kl:
                    stopped_early = True
                    trigger_kl = global_metrics["approximate_kl"]
                    minibatch_actor = False
                    _clear_disabled_actor_gradients(model, critic_actor_gradient=False)
                if chunked:
                    _synchronize_model_gradients(model, distributed)
                if isinstance(optimizer, IndependentAdamW):
                    actor_norm = torch.nn.utils.clip_grad_norm_(
                        actor_parameters, settings.gradient_clip
                    )
                    critic_norm = torch.nn.utils.clip_grad_norm_(
                        critic_parameters, settings.gradient_clip
                    )
                    gradient_norm = torch.maximum(actor_norm, critic_norm)
                else:
                    gradient_norm = torch.nn.utils.clip_grad_norm_(
                        (parameter for parameter in model.parameters() if parameter.requires_grad),
                        settings.gradient_clip,
                    )
                if not bool(torch.isfinite(gradient_norm)):
                    raise FloatingPointError("effect PPO produced a non-finite gradient")
                if not minibatch_actor:
                    _clear_disabled_actor_gradients(
                        model,
                        critic_actor_gradient=False if stopped_early else critic_actor_gradient,
                    )
                if minibatch_actor:
                    if guard is None:
                        raise RuntimeError("effect actor update lost its KL guard")
                    guarded_model: nn.Module = model
                    guarded_optimizer = optimizer
                    if isinstance(optimizer, IndependentAdamW):
                        optimizer.critic.step()
                        guarded_optimizer = optimizer.actor
                        guarded_model = nn.ModuleDict(
                            {"actor": model.actor, "effects": model.effects}
                        )
                    result = guarded_optimizer_step(
                        guarded_model,
                        guarded_optimizer,
                        actor_parameters,
                        lambda: distributed.maximum(guard()),
                        target_kl=settings.target_kl,
                        backoff_factor=settings.kl_backoff_factor,
                        maximum_retries=settings.kl_max_retries,
                    )
                    rejected_attempts += result.rejected_attempts
                    maximum_trial_kl = max(maximum_trial_kl, result.maximum_trial_kl)
                    if result.accepted:
                        actor_steps += 1
                        accepted_guard_kl = result.kl
                        minimum_step_scale = min(minimum_step_scale, result.learning_rate_scale)
                    else:
                        stopped_early = True
                        trigger_kl = result.kl
                        _clear_disabled_actor_gradients(model, critic_actor_gradient=False)
                        if not isinstance(optimizer, IndependentAdamW):
                            optimizer.step()
                else:
                    optimizer.step()
                optimizer_steps += 1
                optimizer_episodes += len(episodes) * distributed.world_size
                metrics["gradient_norm"].append(float(gradient_norm.detach()))
        finally:
            prepared.close()
        completed_epochs += 1
    model.eval()
    if not metrics["loss"]:
        raise RuntimeError("effect PPO produced no logical minibatch")
    planned_steps = settings.ppo_epochs * batch.episode_count // local_minibatch
    return {
        **{name: float(np.mean(values, dtype=np.float64)) for name, values in metrics.items()},
        "first_approximate_kl": metrics["approximate_kl"][0],
        "last_approximate_kl": metrics["approximate_kl"][-1],
        "maximum_approximate_kl": max(metrics["approximate_kl"]),
        "trigger_approximate_kl": trigger_kl,
        "target_kl": settings.target_kl,
        "optimizer_steps": optimizer_steps,
        "actor_optimizer_steps": actor_steps,
        "critic_optimizer_steps": optimizer_steps,
        "kl_rejected_attempts": rejected_attempts,
        "initial_guard_kl": initial_guard_kl,
        "accepted_guard_kl": accepted_guard_kl,
        "maximum_trial_kl": maximum_trial_kl,
        "guard_episodes": microbatch_size * distributed.world_size if guard else 0,
        "actor_learning_rate": float(optimizer.param_groups[0]["lr"]),
        "minimum_actor_step_scale": minimum_step_scale if actor_steps else 0.0,
        "planned_optimizer_steps": planned_steps,
        "optimizer_episodes": optimizer_episodes,
        "evaluated_minibatches": evaluated_minibatches,
        "completed_epochs": completed_epochs,
        "physical_microbatches": physical_microbatches * distributed.world_size,
        "physical_microbatches_per_rank": physical_microbatches,
        "reference_forward_microbatches_per_rank": reference_forward_microbatches,
        "reference_distribution_source": (
            "rollout" if actor_update and rollout_reference else "model"
        ),
        "chunked_candidate_backward": actor_update and rollout_reference,
        "candidate_elements_per_chunk": settings.candidate_elements_per_chunk,
        "reference_cache_bytes_per_rank": (
            0
            if reference_cache is None
            else reference_cache.numel() * reference_cache.element_size()
        ),
        "distributed_world_size": distributed.world_size,
        "logical_episodes_per_minibatch": settings.episodes_per_minibatch,
        "physical_episodes_per_microbatch": microbatch_size,
        "actor_update": actor_update,
        "actor_update_requested": actor_requested,
        "advantage_mean": advantage_mean,
        "advantage_scale": advantage_scale,
        "kl_early_stop": stopped_early,
        "maximum_absolute_behavior_log_ratio": maximum_behavior_log_ratio,
        "input_materialization_seconds": input_materialization_seconds,
        "input_wait_seconds": input_wait_seconds,
    }


__all__ = [
    "EffectSequenceEvaluator",
    "audit_effect_behavior",
    "optimize_effect_batch",
]
