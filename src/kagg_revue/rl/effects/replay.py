"""Sequence replay, distributed gradients, and prefetched effect minibatches."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable, Generator, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from typing import Any

import numpy as np
import torch
from torch import Tensor, nn
from torch import distributed as dist

from kagg_revue.policy.effects.model import EffectActorCritic
from kagg_revue.policy.effects.schema import EffectPolicyOutput
from kagg_revue.rl.distributed import DistributedContext
from kagg_revue.rl.effects.chunked import (
    evaluate_sharded_behavior,
)
from kagg_revue.rl.effects.data import EffectRolloutBatch
from kagg_revue.rl.effects.objective import (
    EffectAdvantages,
    terminal_effect_advantages,
)


class EffectSequenceEvaluator(nn.Module):
    """Expose effect sequence evaluation through DDP's forward hook."""

    def __init__(
        self,
        model: EffectActorCritic,
        *,
        critic_actor_gradient: bool = True,
    ) -> None:
        """Bind the single authoritative actor-critic implementation."""
        super().__init__()
        self.model = model
        self.critic_actor_gradient = critic_actor_gradient

    def forward(
        self,
        batch: EffectRolloutBatch,
        *,
        value_only: bool,
        validate: bool,
    ) -> EffectPolicyOutput:
        """Evaluate one already materialized learner microbatch."""
        economic_state = (
            batch.economic_state
            if self.model.actor.architecture.economic_feature_version is not None
            else None
        )
        if batch.state is not None and not batch.decision_shards:
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
                economic_state,
                candidate_counts=None if value_only else batch.candidate_counts,
                value_only=value_only,
                critic_actor_gradient=self.critic_actor_gradient,
                validate=validate,
            )
        if batch.state is None or not batch.decision_shards:
            raise ValueError("effect learner requires materialized factor state")
        sequence = self.model.encode_effect_sequences(
            batch.board,
            batch.units,
            batch.global_features,
            batch.actions,
            batch.quantities,
            batch.turn_mask,
            batch.decision_mask,
            economic_state,
            value_only=value_only,
        )
        return self.model.evaluate_effect_sequence_context(
            sequence,
            batch.state,
            batch.episode_index,
            batch.turn_index,
            candidate_states=tuple(shard.state for shard in batch.decision_shards),
            value_only=value_only,
            critic_actor_gradient=self.critic_actor_gradient,
            validate=validate,
        )


def _autocast(device: torch.device) -> Any:
    return (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )


def _evaluate(
    model: EffectActorCritic,
    batch: EffectRolloutBatch,
    *,
    training_model: nn.Module | None = None,
    value_only: bool = False,
    validate: bool,
) -> EffectPolicyOutput:
    if training_model is None:
        return EffectSequenceEvaluator(model).forward(
            batch,
            value_only=value_only,
            validate=validate,
        )
    result = training_model(batch, value_only=value_only, validate=validate)
    if not isinstance(result, EffectPolicyOutput):
        raise TypeError("effect DDP evaluator returned an invalid output")
    return result


def _global_advantages(
    batch: EffectRolloutBatch,
    context: DistributedContext,
    *,
    normalize: bool,
    actor_requested: bool,
    gae_lambda: float = 1.0,
) -> EffectAdvantages:
    """Build one globally normalized turn-level advantage reference."""
    local = terminal_effect_advantages(
        batch.outcomes,
        batch.old_value,
        batch.episode_index,
        batch.turn_index,
        batch.value_mask,
        turn_horizon=batch.board.shape[1],
        normalize=False,
        gae_lambda=gae_lambda,
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
    actor_update = actor_requested and (
        len({value for summary in summaries for value in summary[3]}) >= 2
    )
    values = local.values
    if normalize and actor_update and np.isfinite(scale) and scale > 1e-6:
        values = (values - mean) / scale
    return EffectAdvantages(
        values=values,
        mean=values.new_tensor(mean),
        scale=values.new_tensor(scale),
        actor_update=actor_update,
    )


def _global_metric_row(
    values: dict[str, Tensor],
    context: DistributedContext,
) -> dict[str, float]:
    names = tuple(values)
    packed = torch.stack(tuple(values[name] for name in names)).float()
    if context.enabled:
        dist.all_reduce(packed, op=dist.ReduceOp.SUM)
        packed /= context.world_size
    return dict(zip(names, packed.cpu().tolist(), strict=True))


def _global_maximum(value: Tensor, context: DistributedContext) -> float:
    packed = value.detach().float().clone()
    if context.enabled:
        dist.all_reduce(packed, op=dist.ReduceOp.MAX)
    return float(packed)


def _selected_log_probability(output: EffectPolicyOutput, selected: Tensor) -> Tensor:
    return (
        torch.log_softmax(output.candidate_logits.float(), dim=-1)
        .gather(1, selected.long()[:, None])
        .squeeze(1)
    )


def _zero_parameter_anchor(model: EffectActorCritic) -> Tensor:
    parameters = [
        parameter.reshape(-1)[0] for parameter in model.parameters() if parameter.requires_grad
    ]
    if not parameters:
        raise RuntimeError("effect learner has no trainable parameters")
    return torch.stack(parameters).sum() * 0.0


def _clear_disabled_actor_gradients(
    model: EffectActorCritic,
    *,
    critic_actor_gradient: bool,
) -> None:
    if critic_actor_gradient:
        modules = (
            model.effects.candidate_encoder,
            model.effects.query,
            model.effects.key,
            model.effects.residual,
        )
        for module in modules:
            for parameter in module.parameters():
                parameter.grad = None
        return
    critic_module = model.effects.value_head if model.critic is None else model.critic
    critic_ids = {id(parameter) for parameter in critic_module.parameters()}
    for parameter in model.parameters():
        if parameter.requires_grad and id(parameter) not in critic_ids:
            parameter.grad = None


def _enable_trainable_recurrent_backends(model: EffectActorCritic) -> None:
    """Permit cuDNN RNN backward while keeping actor dropout disabled."""
    for module in model.modules():
        if isinstance(module, nn.GRU | nn.LSTM | nn.RNN) and any(
            parameter.requires_grad for parameter in module.parameters()
        ):
            module.train()


def _synchronize_model_gradients(
    model: EffectActorCritic,
    context: DistributedContext,
) -> None:
    """Match DDP's averaged gradient after a manually chunked forward path."""
    if not context.enabled:
        return
    parameters = tuple(parameter for parameter in model.parameters() if parameter.requires_grad)
    if not parameters:
        raise RuntimeError("chunked effect PPO has no trainable parameters")
    participating = torch.tensor(
        [parameter.grad is not None for parameter in parameters],
        dtype=torch.int32,
        device=parameters[0].device,
    )
    dist.all_reduce(participating, op=dist.ReduceOp.SUM)
    participation_counts = tuple(int(value) for value in participating.cpu().tolist())
    groups: dict[tuple[torch.device, torch.dtype], list[tuple[nn.Parameter, Tensor]]] = defaultdict(
        list
    )
    for count, parameter in zip(participation_counts, parameters, strict=True):
        if not count:
            continue
        gradient = parameter.grad
        if gradient is None:
            gradient = torch.zeros_like(parameter)
            parameter.grad = gradient
        groups[(gradient.device, gradient.dtype)].append((parameter, gradient))
    for values in groups.values():
        flattened = torch.cat([gradient.reshape(-1) for _parameter, gradient in values])
        dist.all_reduce(flattened, op=dist.ReduceOp.SUM)
        flattened.div_(context.world_size)
        offset = 0
        for parameter, gradient in values:
            stop = offset + parameter.numel()
            gradient.copy_(flattened[offset:stop].view_as(parameter))
            offset = stop


def _prepare_subset(
    batch: EffectRolloutBatch,
    episodes: Sequence[int],
    device: torch.device,
    critic_only: bool,
    stream: torch.cuda.Stream | None,
) -> tuple[EffectRolloutBatch, float]:
    started = time.perf_counter()
    if stream is None:
        selected = batch.subset(episodes, device, critic_only=critic_only)
    else:
        with torch.cuda.device(device), torch.cuda.stream(stream):
            selected = batch.subset(episodes, device, critic_only=critic_only)
    return selected, time.perf_counter() - started


def _prefetched_subsets(
    batch: EffectRolloutBatch,
    episode_batches: Sequence[Sequence[int]],
    device: torch.device,
    *,
    critic_only: bool | Callable[[], bool],
) -> Generator[tuple[EffectRolloutBatch, float, float], None, None]:
    """Overlap indexed collation/upload with the current microbatch."""
    if not episode_batches:
        return
    prefetch_stream = (
        torch.cuda.Stream(device=device)  # type: ignore[no-untyped-call]
        if device.type == "cuda"
        else None
    )
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="effect-input") as executor:
        future = executor.submit(
            _prepare_subset,
            batch,
            episode_batches[0],
            device,
            critic_only() if callable(critic_only) else critic_only,
            prefetch_stream,
        )
        try:
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
                        critic_only() if callable(critic_only) else critic_only,
                        prefetch_stream,
                    )
                yield selected, materialization_seconds, wait_seconds
        finally:
            future.result()
            if prefetch_stream is not None:
                prefetch_stream.synchronize()


def audit_effect_behavior(
    model: EffectActorCritic,
    batch: EffectRolloutBatch,
    device: torch.device,
    *,
    episodes_per_batch: int,
    maximum_episodes: int | None = None,
    candidate_elements_per_chunk: int = 2_000_000,
    failure_batch_path: str | None = None,
) -> dict[str, float]:
    """Check incremental selections against causal sequence reconstruction."""
    if maximum_episodes is not None and maximum_episodes < 1:
        raise ValueError("effect behavior audit limit must be positive")
    model.eval()
    maximum_log_error = 0.0
    maximum_value_error = 0.0
    total_log_error = 0.0
    total_value_error = 0.0
    audited_factors = 0
    audited_values = 0
    all_finite = True
    # Batch-shape-dependent GEMM/attention kernels need not be bit exact.  This
    # remains narrow enough to catch a changed mask or semantic state, whose
    # categorical likelihood errors are orders of magnitude larger.
    tolerance = 0.1 if device.type == "cuda" else 1e-2
    audit_count = min(batch.episode_count, maximum_episodes or batch.episode_count)
    audited_episodes = tuple(
        index * batch.episode_count // audit_count for index in range(audit_count)
    )
    episode_batches = tuple(
        audited_episodes[start : start + episodes_per_batch]
        for start in range(0, audit_count, episodes_per_batch)
    )
    with torch.inference_mode():
        for selected, _materialization, _wait in _prefetched_subsets(
            batch,
            episode_batches,
            device,
            critic_only=False,
        ):
            if selected.decision_shards:
                errors = evaluate_sharded_behavior(
                    model,
                    selected,
                    candidate_elements_per_chunk=candidate_elements_per_chunk,
                )
                if failure_batch_path is not None and (
                    not errors.all_finite
                    or errors.maximum_log_error > tolerance
                    or errors.maximum_value_error > tolerance
                ):
                    torch.save(selected, failure_batch_path)
                    failure_batch_path = None
                all_finite = all_finite and errors.all_finite
                maximum_log_error = max(
                    maximum_log_error,
                    errors.maximum_log_error,
                )
                maximum_value_error = max(
                    maximum_value_error,
                    errors.maximum_value_error,
                )
                total_log_error += errors.total_log_error
                total_value_error += errors.total_value_error
                audited_factors += errors.factor_count
                audited_values += errors.value_count
            else:
                with _autocast(device):
                    output = _evaluate(model, selected, validate=True)
                log_probability = _selected_log_probability(output, selected.selected)
                log_errors = (log_probability - selected.old_log_probability).abs()
                value_errors = (output.value - selected.old_value).abs()[selected.value_mask]
                all_finite = all_finite and bool(torch.isfinite(log_errors).all())
                all_finite = all_finite and bool(torch.isfinite(value_errors).all())
                maximum_log_error = max(maximum_log_error, float(log_errors.max()))
                maximum_value_error = max(maximum_value_error, float(value_errors.max()))
                total_log_error += float(log_errors.sum())
                total_value_error += float(value_errors.sum())
                audited_factors += log_errors.numel()
                audited_values += value_errors.numel()
    mean_log_error = total_log_error / audited_factors
    mean_value_error = total_value_error / audited_values
    if not all_finite or maximum_log_error > tolerance or maximum_value_error > tolerance:
        raise RuntimeError(
            "effect behavior failed causal replay: "
            f"log_probability_error={maximum_log_error:.9g}, "
            f"value_error={maximum_value_error:.9g}, "
            f"audited_episodes={audit_count}"
        )
    return {
        "maximum_absolute_log_probability_error": maximum_log_error,
        "maximum_absolute_value_error": maximum_value_error,
        "mean_absolute_log_probability_error": mean_log_error,
        "mean_absolute_value_error": mean_value_error,
    }
