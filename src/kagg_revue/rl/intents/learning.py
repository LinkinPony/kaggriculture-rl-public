"""Episode-minibatch optimization for independent intent pseudo-steps."""

from __future__ import annotations

import random
import time
from collections import defaultdict
from collections.abc import Generator, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from copy import deepcopy
from typing import Any

import numpy as np
import torch
from torch import distributed as dist
from torch import nn
from torch.optim import Optimizer

from kagg_revue.policy.intents.model import IntentActorCritic
from kagg_revue.policy.intents.schema import IntentPolicyOutput
from kagg_revue.rl.distributed import DistributedContext, single_process_context
from kagg_revue.rl.intents.config import IntentOptimizationSettings
from kagg_revue.rl.intents.data import IntentRolloutBatch
from kagg_revue.rl.intents.objective import (
    IntentAdvantages,
    intent_ppo_loss,
    terminal_intent_advantages,
)


class IntentSequenceEvaluator(nn.Module):
    """Expose causal intent sequence evaluation through DDP's forward hook."""

    def __init__(self, model: IntentActorCritic) -> None:
        """Bind the one authoritative actor-critic implementation."""
        super().__init__()
        self.model = model

    def forward(
        self,
        batch: IntentRolloutBatch,
        *,
        value_only: bool,
        validate: bool,
    ) -> IntentPolicyOutput:
        """Evaluate one already materialized learner microbatch."""
        if batch.state is None:
            raise ValueError("intent learner requires a materialized decision minibatch")
        return self.model.evaluate_sequences(
            batch.board,
            batch.units,
            batch.global_features,
            batch.actions,
            batch.quantities,
            batch.turn_mask,
            batch.decision_mask,
            batch.state,
            batch.episode_index,
            batch.turn_index,
            (
                batch.economic_state
                if self.model.actor.architecture.economic_feature_version is not None
                else None
            ),
            candidate_counts=batch.candidate_counts,
            value_only=value_only,
            validate=validate,
        )


def _autocast(device: torch.device) -> Any:
    return (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )


def _release_cuda_cache_if_pressured(device: torch.device) -> None:
    """Release inactive learner blocks before allocator pressure forces an OOM retry."""
    if device.type != "cuda":
        return
    total_memory = torch.cuda.get_device_properties(device).total_memory
    if torch.cuda.memory_reserved(device) * 5 >= total_memory * 4:
        torch.cuda.empty_cache()


def _evaluate(
    model: IntentActorCritic,
    batch: IntentRolloutBatch,
    *,
    training_model: nn.Module | None = None,
    value_only: bool = False,
    validate: bool,
) -> IntentPolicyOutput:
    if batch.state is None:
        raise ValueError("intent learner requires a materialized decision minibatch")
    if training_model is None:
        return IntentSequenceEvaluator(model).forward(
            batch, value_only=value_only, validate=validate
        )
    result = training_model(batch, value_only=value_only, validate=validate)
    if not isinstance(result, IntentPolicyOutput):
        raise TypeError("intent DDP evaluator returned an invalid output")
    return result


def _global_advantages(
    batch: IntentRolloutBatch,
    context: DistributedContext,
    *,
    normalize: bool,
) -> IntentAdvantages:
    """Build one globally normalized advantage reference on local rows."""
    local = terminal_intent_advantages(
        batch.outcomes,
        batch.old_value,
        batch.episode_index,
        normalize=False,
    )
    summaries = context.all_gather(
        (
            batch.episode_count,
            float(local.mean),
            float(local.scale.square()),
            tuple(int(value) for value in torch.unique(batch.outcomes).tolist()),
        )
    )
    count = sum(summary[0] for summary in summaries)
    mean = sum(summary[0] * summary[1] for summary in summaries) / count
    second_moment = (
        sum(summary[0] * (summary[2] + summary[1] ** 2) for summary in summaries) / count
    )
    scale = max(0.0, second_moment - mean**2) ** 0.5
    actor_update = len({value for summary in summaries for value in summary[3]}) >= 2
    values = local.values
    if normalize and actor_update and np.isfinite(scale) and scale > 1e-6:
        values = (values - mean) / scale
    return IntentAdvantages(
        values=values,
        mean=values.new_tensor(mean),
        scale=values.new_tensor(scale),
        actor_update=actor_update,
    )


def _global_metric_row(
    values: dict[str, torch.Tensor],
    context: DistributedContext,
) -> dict[str, float]:
    """Average one logical minibatch's detached diagnostics across ranks."""
    names = tuple(values)
    packed = torch.stack(tuple(values[name] for name in names)).float()
    if context.enabled:
        dist.all_reduce(packed, op=dist.ReduceOp.SUM)
        packed /= context.world_size
    return dict(zip(names, packed.cpu().tolist(), strict=True))


def _global_maximum(value: torch.Tensor, context: DistributedContext) -> float:
    """Return one detached maximum over every learner rank."""
    packed = value.detach().float().clone()
    if context.enabled:
        dist.all_reduce(packed, op=dist.ReduceOp.MAX)
    return float(packed)


def _selected_log_probability(output: IntentPolicyOutput, selected: torch.Tensor) -> torch.Tensor:
    """Gather selected-action likelihoods with the learner's PPO numerics."""
    return (
        torch.log_softmax(output.candidate_logits.float(), dim=-1)
        .gather(1, selected.long()[:, None])
        .squeeze(1)
    )


def _zero_parameter_anchor(model: IntentActorCritic) -> torch.Tensor:
    """Keep DDP hooks complete without evaluating disabled policy heads."""
    parameters = [
        parameter.reshape(-1)[0] for parameter in model.parameters() if parameter.requires_grad
    ]
    if not parameters:
        raise RuntimeError("intent learner has no trainable parameters")
    return torch.stack(parameters).sum() * 0.0


def _clear_disabled_actor_gradients(model: IntentActorCritic) -> None:
    """Keep AdamW participation unchanged for a critic-only update."""
    modules = (
        model.intents.candidate_encoder,
        model.intents.query,
        model.intents.key,
        model.intents.residual,
    )
    for module in modules:
        for parameter in module.parameters():
            parameter.grad = None


def _prepare_subset(
    batch: IntentRolloutBatch,
    episodes: Sequence[int],
    device: torch.device,
    critic_only: bool,
    stream: torch.cuda.Stream | None,
) -> tuple[IntentRolloutBatch, float]:
    """Materialize one episode batch outside the learner's launch thread."""
    started = time.perf_counter()
    if stream is None:
        selected = batch.subset(episodes, device, critic_only=critic_only)
    else:
        with torch.cuda.device(device), torch.cuda.stream(stream):
            selected = batch.subset(episodes, device, critic_only=critic_only)
    return selected, time.perf_counter() - started


def _prefetched_subsets(
    batch: IntentRolloutBatch,
    episode_batches: Sequence[Sequence[int]],
    device: torch.device,
    *,
    critic_only: bool,
) -> Generator[tuple[IntentRolloutBatch, float, float], None, None]:
    """Overlap the next CPU collation and device upload with model work."""
    if not episode_batches:
        return
    prefetch_stream = (
        torch.cuda.Stream(device=device)  # type: ignore[no-untyped-call]
        if device.type == "cuda"
        else None
    )
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="intent-input") as executor:
        future = executor.submit(
            _prepare_subset,
            batch,
            episode_batches[0],
            device,
            critic_only,
            prefetch_stream,
        )
        for index in range(len(episode_batches)):
            wait_started = time.perf_counter()
            selected, materialization_seconds = future.result()
            wait_seconds = time.perf_counter() - wait_started
            if prefetch_stream is not None:
                consumer = torch.cuda.current_stream(device)
                consumer.wait_stream(prefetch_stream)
                selected.record_stream(consumer)
            if index + 1 < len(episode_batches):
                future = executor.submit(
                    _prepare_subset,
                    batch,
                    episode_batches[index + 1],
                    device,
                    critic_only,
                    prefetch_stream,
                )
            yield selected, materialization_seconds, wait_seconds


def audit_intent_behavior(
    model: IntentActorCritic,
    batch: IntentRolloutBatch,
    device: torch.device,
    *,
    episodes_per_batch: int,
    maximum_episodes: int | None = None,
) -> dict[str, float]:
    """Verify incremental behavior against causal sequence reconstruction."""
    if maximum_episodes is not None and maximum_episodes < 1:
        raise ValueError("intent behavior audit episode limit must be positive")
    model.eval()
    maximum_log_error = 0.0
    maximum_value_error = 0.0
    total_log_error = 0.0
    total_value_error = 0.0
    excessive_log_errors = 0
    excessive_value_errors = 0
    audited_rows = 0
    all_finite = True
    tolerance = 0.1 if device.type == "cuda" else 1e-4
    audit_count = min(batch.episode_count, maximum_episodes or batch.episode_count)
    audited_episodes = tuple(
        index * batch.episode_count // audit_count for index in range(audit_count)
    )
    episode_batches = tuple(
        audited_episodes[start : start + episodes_per_batch]
        for start in range(0, audit_count, episodes_per_batch)
    )
    with torch.inference_mode():
        for selected, _materialization_seconds, _wait_seconds in _prefetched_subsets(
            batch,
            episode_batches,
            device,
            critic_only=False,
        ):
            with _autocast(device):
                output = _evaluate(model, selected, validate=True)
            log_probability = (
                torch.log_softmax(output.candidate_logits.float(), dim=-1)
                .gather(1, selected.selected[:, None])
                .squeeze(1)
            )
            log_errors = (log_probability - selected.old_log_probability).abs()
            value_errors = (output.value - selected.old_value).abs()
            all_finite = all_finite and bool(
                torch.isfinite(log_errors).all() & torch.isfinite(value_errors).all()
            )
            maximum_log_error = max(maximum_log_error, float(log_errors.max()))
            maximum_value_error = max(maximum_value_error, float(value_errors.max()))
            total_log_error += float(log_errors.sum())
            total_value_error += float(value_errors.sum())
            excessive_log_errors += int((log_errors > tolerance).sum())
            excessive_value_errors += int((value_errors > tolerance).sum())
            audited_rows += log_errors.numel()
    mean_log_error = total_log_error / audited_rows
    mean_value_error = total_value_error / audited_rows
    excessive_log_fraction = excessive_log_errors / audited_rows
    excessive_value_fraction = excessive_value_errors / audited_rows
    # CUDA rollout and learner attention use mathematically equivalent kernels,
    # but their BF16 rounding diverges over long causal histories. Keep the
    # sampled replay as a finite-value diagnostic; exact CPU replay remains a
    # strict implementation check.
    strict_error = device.type != "cuda" and (
        maximum_log_error > tolerance or maximum_value_error > tolerance
    )
    if not all_finite or strict_error:
        raise RuntimeError(
            "intent behavior likelihood failed causal replay: "
            f"log_probability_error={maximum_log_error:.9g}, "
            f"value_error={maximum_value_error:.9g}, "
            f"mean_log_probability_error={mean_log_error:.9g}, "
            f"mean_value_error={mean_value_error:.9g}, "
            f"excessive_log_probability_fraction={excessive_log_fraction:.9g}, "
            f"excessive_value_fraction={excessive_value_fraction:.9g}, "
            f"audited_episodes={audit_count}"
        )
    return {
        "maximum_absolute_log_probability_error": maximum_log_error,
        "maximum_absolute_value_error": maximum_value_error,
        "mean_absolute_log_probability_error": mean_log_error,
        "mean_absolute_value_error": mean_value_error,
        "excessive_log_probability_fraction": excessive_log_fraction,
        "excessive_value_fraction": excessive_value_fraction,
    }


def optimize_intent_batch(
    model: IntentActorCritic,
    optimizer: Optimizer,
    batch: IntentRolloutBatch,
    settings: IntentOptimizationSettings,
    device: torch.device,
    randomizer: random.Random,
    *,
    training_model: nn.Module | None = None,
    reference_model: IntentActorCritic | None = None,
    context: DistributedContext | None = None,
) -> dict[str, object]:
    """Run behavior-corrected PPO with complete-episode minibatches."""
    distributed = context or single_process_context(device)
    evaluator = training_model or IntentSequenceEvaluator(model)
    if settings.episodes_per_minibatch % distributed.world_size:
        raise ValueError("intent logical minibatch must divide across learner ranks")
    local_minibatch_size = settings.episodes_per_minibatch // distributed.world_size
    if batch.episode_count % local_minibatch_size:
        raise ValueError("intent local episodes must fill distributed minibatches")
    microbatch_size = settings.effective_episodes_per_microbatch
    if microbatch_size > local_minibatch_size or local_minibatch_size % microbatch_size:
        raise ValueError("intent microbatch must divide the local learner minibatch")
    global_advantages = _global_advantages(
        batch,
        distributed,
        normalize=settings.normalize_advantage,
    )
    mean = float(global_advantages.mean)
    scale = float(global_advantages.scale)
    actor_update = global_advantages.actor_update
    metrics: dict[str, list[float]] = defaultdict(list)
    optimizer_steps = 0
    optimizer_episodes = 0
    evaluated_minibatches = 0
    evaluated_episodes = 0
    physical_microbatches_per_rank = 0
    completed_epochs = 0
    input_materialization_seconds = 0.0
    input_wait_seconds = 0.0
    stopped_early = False
    trigger_approximate_kl: float | None = None
    maximum_absolute_behavior_log_ratio = 0.0
    policy_episodes = {
        int(index) for index in torch.unique(batch.episode_index[batch.policy_mask]).tolist()
    }
    model.train()
    # PPO likelihoods must not acquire training-only encoder dropout.
    model.actor.eval()
    frozen_reference: IntentActorCritic | None = None
    if actor_update:
        if reference_model is model:
            raise ValueError("intent PPO reference must not alias the trainable model")
        frozen_reference = reference_model or deepcopy(model).to(device)
        reference_device = next(frozen_reference.parameters()).device
        expected_index = (
            torch.cuda.current_device()
            if device.type == "cuda" and device.index is None
            else device.index
        )
        reference_index = (
            torch.cuda.current_device()
            if reference_device.type == "cuda" and reference_device.index is None
            else reference_device.index
        )
        if reference_device.type != device.type or reference_index != expected_index:
            raise ValueError("intent PPO reference is on the wrong learner device")
        frozen_reference.load_state_dict(model.state_dict(), strict=True)
        frozen_reference.train()
        frozen_reference.actor.eval()
        frozen_reference.zero_grad(set_to_none=True)
    for _epoch in range(settings.ppo_epochs):
        order = list(range(batch.episode_count))
        randomizer.shuffle(order)
        logical_batches = tuple(
            order[start : start + local_minibatch_size]
            for start in range(0, len(order), local_minibatch_size)
        )
        microbatches = tuple(
            tuple(
                episodes[start : start + microbatch_size]
                for start in range(0, len(episodes), microbatch_size)
            )
            for episodes in logical_batches
        )
        flattened = tuple(
            microbatch
            for logical_microbatches in microbatches
            for microbatch in logical_microbatches
        )
        prepared = _prefetched_subsets(
            batch,
            flattened,
            device,
            critic_only=not actor_update,
        )
        try:
            for episodes, logical_microbatches in zip(logical_batches, microbatches, strict=True):
                optimizer.zero_grad(set_to_none=True)
                logical_metrics: dict[str, torch.Tensor] = {}
                logical_behavior_log_ratio_max = torch.zeros((), device=device)
                logical_policy_episodes = sum(episode in policy_episodes for episode in episodes)
                rank_scales = distributed.loss_scales(
                    torch.tensor(
                        [len(episodes), logical_policy_episodes],
                        dtype=torch.float32,
                        device=device,
                    )
                )
                for microbatch_index, micro_episodes in enumerate(logical_microbatches):
                    selected, materialization_seconds, wait_seconds = next(prepared)
                    input_materialization_seconds += materialization_seconds
                    input_wait_seconds += wait_seconds
                    raw_advantages = (
                        selected.outcomes.float()[selected.episode_index]
                        - selected.old_value.detach().float()
                    )
                    advantages = raw_advantages
                    if (
                        settings.normalize_advantage
                        and actor_update
                        and np.isfinite(scale)
                        and scale > 1e-6
                    ):
                        advantages = (raw_advantages - mean) / scale
                    reference_candidate_log_probabilities: torch.Tensor | None = None
                    if frozen_reference is None:
                        reference_log_probability = selected.old_log_probability.detach()
                    else:
                        with torch.no_grad(), _autocast(device):
                            reference_output = _evaluate(
                                frozen_reference,
                                selected,
                                value_only=False,
                                validate=optimizer_steps == 0,
                            )
                            reference_log_probability = _selected_log_probability(
                                reference_output,
                                selected.selected,
                            ).detach()
                            reference_candidate_log_probabilities = torch.log_softmax(
                                reference_output.candidate_logits.float(), dim=-1
                            ).detach()
                            del reference_output
                    last_microbatch = microbatch_index + 1 == len(logical_microbatches)
                    no_sync = getattr(evaluator, "no_sync", None)
                    synchronization = (
                        no_sync()
                        if not last_microbatch and callable(no_sync)
                        else nullcontext()
                    )
                    with synchronization, _autocast(device):
                        output = _evaluate(
                            model,
                            selected,
                            training_model=evaluator,
                            value_only=not actor_update,
                            validate=optimizer_steps == 0,
                        )
                        loss = intent_ppo_loss(
                            output,
                            selected.selected,
                            selected.old_log_probability,
                            reference_log_probability,
                            reference_candidate_log_probabilities,
                            advantages,
                            selected.outcomes,
                            selected.episode_index,
                            selected.policy_mask,
                            clip_epsilon=settings.clip_epsilon,
                            value_loss_weight=settings.value_loss_weight,
                            entropy_weight=settings.entropy_weight,
                            actor_update=actor_update,
                            validate=optimizer_steps == 0,
                        )
                        value_weight = len(micro_episodes) / len(episodes)
                        micro_policy_episodes = sum(
                            episode in policy_episodes for episode in micro_episodes
                        )
                        policy_weight = (
                            micro_policy_episodes / logical_policy_episodes
                            if logical_policy_episodes
                            else 0.0
                        )
                        weighted_loss = (
                            rank_scales[0] * settings.value_loss_weight * value_weight * loss.value
                        )
                        if actor_update and policy_weight:
                            weighted_loss = weighted_loss + rank_scales[1] * policy_weight * (
                                loss.policy - settings.entropy_weight * loss.entropy
                            )
                        weighted_loss = weighted_loss + _zero_parameter_anchor(model)
                        weighted_loss.backward()  # type: ignore[no-untyped-call]
                    physical_microbatches_per_rank += 1

                    contributions = {
                        "policy_loss": rank_scales[1] * policy_weight * loss.policy,
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
                    for name, contribution_value in contributions.items():
                        detached = contribution_value.detach()
                        logical_metrics[name] = (
                            detached
                            if name not in logical_metrics
                            else logical_metrics[name] + detached
                        )
                    if actor_update and bool(selected.policy_mask.any()):
                        behavior_log_ratio = (
                            reference_log_probability - selected.old_log_probability.detach()
                        )
                        logical_behavior_log_ratio_max = torch.maximum(
                            logical_behavior_log_ratio_max,
                            behavior_log_ratio[selected.policy_mask].abs().max(),
                        )
                    del (
                        advantages,
                        loss,
                        output,
                        raw_advantages,
                        reference_log_probability,
                        reference_candidate_log_probabilities,
                        selected,
                        weighted_loss,
                    )
                global_metrics = _global_metric_row(logical_metrics, distributed)
                maximum_absolute_behavior_log_ratio = max(
                    maximum_absolute_behavior_log_ratio,
                    _global_maximum(logical_behavior_log_ratio_max, distributed),
                )
                global_metrics["loss"] = global_metrics["policy_loss"] + (
                    settings.value_loss_weight * global_metrics["value_loss"]
                )
                if actor_update:
                    global_metrics["loss"] -= settings.entropy_weight * global_metrics["entropy"]
                for name, metric_value in global_metrics.items():
                    metrics[name].append(metric_value)
                evaluated_minibatches += 1
                evaluated_episodes += len(episodes) * distributed.world_size
                if global_metrics["approximate_kl"] > settings.target_kl:
                    optimizer.zero_grad(set_to_none=True)
                    stopped_early = True
                    trigger_approximate_kl = global_metrics["approximate_kl"]
                    break
                gradient_norm = torch.nn.utils.clip_grad_norm_(
                    (parameter for parameter in model.parameters() if parameter.requires_grad),
                    settings.gradient_clip,
                )
                if not bool(torch.isfinite(gradient_norm)):
                    raise FloatingPointError("intent PPO produced a non-finite gradient")
                if not actor_update:
                    _clear_disabled_actor_gradients(model)
                optimizer.step()
                optimizer_steps += 1
                optimizer_episodes += len(episodes) * distributed.world_size
                metrics["gradient_norm"].append(float(gradient_norm.detach()))
                _release_cuda_cache_if_pressured(device)
        finally:
            prepared.close()
        if stopped_early:
            break
        completed_epochs += 1
    model.eval()
    if frozen_reference is not None:
        frozen_reference.eval()
    if not metrics["loss"]:
        raise RuntimeError("intent PPO produced no logical minibatch")
    planned_optimizer_steps = settings.ppo_epochs * batch.episode_count // local_minibatch_size
    return {
        **{name: float(np.mean(values, dtype=np.float64)) for name, values in metrics.items()},
        "first_approximate_kl": metrics["approximate_kl"][0],
        "last_approximate_kl": metrics["approximate_kl"][-1],
        "maximum_approximate_kl": max(metrics["approximate_kl"]),
        "trigger_approximate_kl": trigger_approximate_kl,
        "target_kl": settings.target_kl,
        "optimizer_steps": optimizer_steps,
        "planned_optimizer_steps": planned_optimizer_steps,
        "optimizer_episodes": optimizer_episodes,
        "evaluated_minibatches": evaluated_minibatches,
        "evaluated_episodes": evaluated_episodes,
        "completed_epochs": completed_epochs,
        "physical_microbatches": physical_microbatches_per_rank * distributed.world_size,
        "physical_microbatches_per_rank": physical_microbatches_per_rank,
        "distributed_world_size": distributed.world_size,
        "logical_episodes_per_minibatch": settings.episodes_per_minibatch,
        "physical_episodes_per_microbatch": microbatch_size,
        "actor_update": actor_update,
        "advantage_mean": mean,
        "advantage_scale": scale,
        "kl_early_stop": stopped_early,
        "kl_stop_statistic": (
            "exact_frozen_preupdate_categorical_logical_minibatch_episode_mean"
        ),
        "behavior_likelihood_statistic": "rollout_to_frozen_learner_reference",
        "maximum_absolute_behavior_log_ratio": maximum_absolute_behavior_log_ratio,
        "input_materialization_seconds": input_materialization_seconds,
        "input_wait_seconds": input_wait_seconds,
    }


__all__ = [
    "IntentSequenceEvaluator",
    "audit_intent_behavior",
    "optimize_intent_batch",
]
