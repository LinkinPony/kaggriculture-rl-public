"""Memory-bounded candidate evaluation for atomic-effect PPO."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any

import torch
from torch import Tensor
from torch.nn import functional

from kagg_revue.policy.effects.data import EffectTensorState
from kagg_revue.policy.effects.model import EffectActorCritic
from kagg_revue.policy.effects.schema import EffectSequenceContext
from kagg_revue.rl.effects.config import EffectOptimizationSettings
from kagg_revue.rl.effects.data import EffectRolloutBatch
from kagg_revue.rl.effects.objective import EffectPpoLoss, factor_score_mean
from kagg_revue.rl.effects.reuse import evaluate_reused_work


@dataclass(frozen=True)
class ShardedBehaviorErrors:
    """Sufficient statistics for one memory-bounded behavior audit."""

    maximum_log_error: float
    maximum_value_error: float
    total_log_error: float
    total_value_error: float
    factor_count: int
    value_count: int
    all_finite: bool


def _autocast(device: torch.device) -> Any:
    return (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )


def _state_rows(state: EffectTensorState, rows: slice) -> EffectTensorState:
    """Select contiguous factor rows without changing their candidate width."""
    return EffectTensorState(
        **{name: getattr(state, name)[rows] for name in EffectTensorState.__dataclass_fields__}
    )


def _detached_sequence(sequence: EffectSequenceContext) -> EffectSequenceContext:
    """Create leaf turn context for independent candidate-chunk backpropagation."""

    def leaf(value: Tensor) -> Tensor:
        return value.detach().requires_grad_(value.requires_grad)

    return EffectSequenceContext(
        context=leaf(sequence.context),
        tile_context=leaf(sequence.tile_context),
        strategy=None if sequence.strategy is None else leaf(sequence.strategy),
        outcome_logits=None if sequence.outcome_logits is None else leaf(sequence.outcome_logits),
    )


def _backward_sequence(
    sequence: EffectSequenceContext,
    leaves: EffectSequenceContext,
) -> None:
    """Propagate accumulated candidate-chunk gradients through the actor once."""
    outputs: list[Tensor] = []
    gradients: list[Tensor] = []
    for output, leaf in (
        (sequence.context, leaves.context),
        (sequence.tile_context, leaves.tile_context),
        (sequence.strategy, leaves.strategy),
        (sequence.outcome_logits, leaves.outcome_logits),
    ):
        if output is not None and leaf is not None and leaf.grad is not None:
            outputs.append(output)
            gradients.append(leaf.grad)
    if outputs:
        torch.autograd.backward(outputs, gradients)


def _balanced_weights(
    episode_index: Tensor,
    turn_index: Tensor,
    mask: Tensor,
    episode_count: int,
    turn_horizon: int,
) -> Tensor:
    """Return the exact mean-factor, mean-turn, mean-episode weights."""
    active = mask.bool()
    result = torch.zeros_like(episode_index, dtype=torch.float32)
    if not bool(active.any()):
        return result
    episodes = episode_index.long()
    keys = episodes * turn_horizon + turn_index.long()
    surface = episode_count * turn_horizon
    counts = torch.zeros(surface, dtype=torch.float32, device=episodes.device)
    counts.scatter_add_(
        0,
        keys[active],
        torch.ones_like(keys[active], dtype=torch.float32),
    )
    represented_turns = counts > 0
    turn_episodes = torch.arange(surface, device=episodes.device) // turn_horizon
    episode_turns = torch.zeros(
        episode_count,
        dtype=torch.float32,
        device=episodes.device,
    )
    episode_turns.scatter_add_(
        0,
        turn_episodes[represented_turns],
        torch.ones_like(turn_episodes[represented_turns], dtype=torch.float32),
    )
    represented_episodes = int(torch.count_nonzero(episode_turns))
    result[active] = (
        counts[keys[active]].reciprocal()
        * episode_turns[episodes[active]].reciprocal()
        / represented_episodes
    )
    return result


def _sequence_context(
    model: EffectActorCritic,
    batch: EffectRolloutBatch,
    *,
    compute_value: bool = True,
) -> EffectSequenceContext:
    economic_state = (
        batch.economic_state
        if model.actor.architecture.economic_feature_version is not None
        else None
    )
    with _autocast(batch.board.device):
        return model.encode_effect_sequences(
            batch.board,
            batch.units,
            batch.global_features,
            batch.actions,
            batch.quantities,
            batch.turn_mask,
            batch.decision_mask,
            economic_state,
            compute_value=compute_value,
        )


def evaluate_sharded_behavior(
    model: EffectActorCritic,
    batch: EffectRolloutBatch,
    *,
    candidate_elements_per_chunk: int,
) -> ShardedBehaviorErrors:
    """Compare rollout statistics without creating a rollout-wide logit tensor."""
    if candidate_elements_per_chunk < 1:
        raise ValueError("effect candidate chunk capacity must be positive")
    if batch.state is None or not batch.decision_shards:
        raise ValueError("sharded effect behavior audit requires compact candidate shards")
    sequence = _sequence_context(model, batch)
    maximum_log_error = 0.0
    maximum_value_error = 0.0
    total_log_error = 0.0
    total_value_error = 0.0
    factor_count = 0
    value_count = 0
    all_finite = True
    offset = 0
    first_chunk = True
    for decision_shard in batch.decision_shards:
        width = int(decision_shard.state.candidate_fields.shape[1])
        rows_per_chunk = max(1, candidate_elements_per_chunk // width)
        for local_start in range(0, decision_shard.row_count, rows_per_chunk):
            local_stop = min(decision_shard.row_count, local_start + rows_per_chunk)
            start = offset + local_start
            stop = offset + local_stop
            rows = slice(start, stop)
            local_rows = slice(local_start, local_stop)
            with _autocast(batch.board.device):
                output = model.evaluate_effect_sequence_context(
                    sequence,
                    _state_rows(batch.state, rows),
                    batch.episode_index[rows],
                    batch.turn_index[rows],
                    candidate_states=(_state_rows(decision_shard.state, local_rows),),
                    validate=first_chunk,
                )
            log_probability = (
                torch.log_softmax(output.candidate_logits.float(), dim=-1)
                .gather(1, batch.selected[rows].long()[:, None])
                .squeeze(1)
            )
            log_errors = (log_probability - batch.old_log_probability[rows]).abs()
            value_errors = (output.value - batch.old_value[rows]).abs()[batch.value_mask[rows]]
            finite = bool(torch.isfinite(log_errors).all()) and bool(
                torch.isfinite(value_errors).all()
            )
            all_finite = all_finite and finite
            maximum_log_error = max(maximum_log_error, float(log_errors.max()))
            if value_errors.numel():
                maximum_value_error = max(
                    maximum_value_error,
                    float(value_errors.max()),
                )
            total_log_error += float(log_errors.sum())
            total_value_error += float(value_errors.sum())
            factor_count += log_errors.numel()
            value_count += value_errors.numel()
            first_chunk = False
            del output, log_probability, log_errors, value_errors
        offset += decision_shard.row_count
    if offset != batch.factor_count or first_chunk:
        raise RuntimeError("sharded effect behavior audit lost factor rows")
    return ShardedBehaviorErrors(
        maximum_log_error=maximum_log_error,
        maximum_value_error=maximum_value_error,
        total_log_error=total_log_error,
        total_value_error=total_value_error,
        factor_count=factor_count,
        value_count=value_count,
        all_finite=all_finite,
    )


def backward_sharded_ppo(
    model: EffectActorCritic,
    batch: EffectRolloutBatch,
    advantages: Tensor,
    settings: EffectOptimizationSettings,
    *,
    value_scale: Tensor,
    policy_scale: Tensor,
    critic_actor_gradient: bool,
    validate: bool,
) -> tuple[EffectPpoLoss, Tensor]:
    """Backpropagate exact PPO statistics without a rollout-wide logit tensor."""
    if batch.state is None or not batch.decision_shards:
        raise ValueError("chunked effect PPO requires compact candidate shards")
    if not all(
        shard.reference_candidate_log_probabilities is not None for shard in batch.decision_shards
    ):
        raise ValueError("chunked effect PPO requires rollout behavior distributions")
    turn_horizon = int(batch.board.shape[1])
    policy_weights = _balanced_weights(
        batch.episode_index,
        batch.turn_index,
        batch.policy_mask,
        batch.episode_count,
        turn_horizon,
    )
    value_weights = _balanced_weights(
        batch.episode_index,
        batch.turn_index,
        batch.value_mask,
        batch.episode_count,
        turn_horizon,
    )
    sequence = _sequence_context(model, batch)
    leaves = _detached_sequence(sequence)
    zero = torch.zeros((), dtype=torch.float32, device=batch.board.device)
    policy = zero.clone()
    value = zero.clone()
    entropy = zero.clone()
    approximate_kl = zero.clone()
    clip_fraction = zero.clone()
    behavior_approximate_kl = zero.clone()
    behavior_clip_fraction = zero.clone()
    behavior_log_ratio_max = zero.clone()
    offset = 0
    first_chunk = True
    for decision_shard in batch.decision_shards:
        reference = decision_shard.reference_candidate_log_probabilities
        if reference is None:
            raise RuntimeError("chunked effect PPO lost a behavior distribution")
        width = int(decision_shard.state.candidate_fields.shape[1])
        rows_per_chunk = max(1, settings.candidate_elements_per_chunk // width)
        for local_start in range(0, decision_shard.row_count, rows_per_chunk):
            local_stop = min(decision_shard.row_count, local_start + rows_per_chunk)
            start = offset + local_start
            stop = offset + local_stop
            rows = slice(start, stop)
            local_rows = slice(local_start, local_stop)
            with _autocast(batch.board.device):
                output = evaluate_reused_work(
                    model,
                    leaves,
                    _state_rows(batch.state, rows),
                    batch.episode_index[rows],
                    batch.turn_index[rows],
                    _state_rows(decision_shard.state, local_rows),
                    critic_actor_gradient=critic_actor_gradient,
                    validate=validate and first_chunk,
                )
            logits = output.candidate_logits.float()
            log_probabilities = torch.log_softmax(logits, dim=-1)
            probabilities = torch.softmax(logits, dim=-1)
            selected = batch.selected[rows].long()
            new_log_probability = log_probabilities.gather(
                1,
                selected[:, None],
            ).squeeze(1)
            reference_logs = reference[local_rows].detach()
            reference_log_probability = reference_logs.gather(
                1,
                selected[:, None],
            ).squeeze(1)
            old_log_probability = batch.old_log_probability[rows].detach()
            policy_log_ratio = new_log_probability - reference_log_probability
            behavior_log_ratio = reference_log_probability - old_log_probability
            policy_ratio = torch.exp(policy_log_ratio)
            behavior_ratio = torch.exp(behavior_log_ratio)
            frozen_advantage = advantages[rows].detach()
            surrogate = behavior_ratio * torch.minimum(
                policy_ratio * frozen_advantage,
                policy_ratio.clamp(
                    1.0 - settings.clip_epsilon,
                    1.0 + settings.clip_epsilon,
                )
                * frozen_advantage,
            )
            policy_chunk = -factor_score_mean(
                surrogate, batch.policy_mask[rows], batch.episode_count, turn_horizon
            )
            finite_logs = log_probabilities.masked_fill(
                ~torch.isfinite(log_probabilities),
                0.0,
            )
            entropy_items = -(probabilities * finite_logs).sum(dim=-1)
            entropy_chunk = (entropy_items * policy_weights[rows]).sum()
            labels = batch.outcomes.long()[batch.episode_index[rows]] + 1
            value_items = functional.cross_entropy(
                output.outcome_logits.float(),
                labels,
                reduction="none",
            )
            value_chunk = (value_items * value_weights[rows]).sum()
            reference_probabilities = reference_logs.exp()
            categorical_kl = (
                reference_probabilities
                * (reference_logs - log_probabilities.detach()).masked_fill(
                    ~torch.isfinite(reference_logs),
                    0.0,
                )
            ).sum(dim=-1)
            approximate_kl_chunk = (categorical_kl * policy_weights[rows]).sum()
            detached_behavior_ratio = behavior_ratio.detach()
            detached_behavior_log_ratio = behavior_log_ratio.detach()
            clip_fraction_chunk = (
                detached_behavior_ratio
                * (torch.abs(policy_ratio.detach() - 1.0) > settings.clip_epsilon).to(
                    policy_ratio.dtype
                )
                * policy_weights[rows]
            ).sum()
            behavior_kl_chunk = (
                (torch.exp(detached_behavior_log_ratio) - 1.0 - detached_behavior_log_ratio)
                * policy_weights[rows]
            ).sum()
            behavior_clip_chunk = (
                (torch.abs(detached_behavior_ratio - 1.0) > settings.clip_epsilon).to(
                    detached_behavior_ratio.dtype
                )
                * policy_weights[rows]
            ).sum()
            checked = (
                new_log_probability,
                old_log_probability,
                reference_log_probability,
                advantages[rows],
                output.outcome_logits,
                policy_ratio,
                behavior_ratio,
                categorical_kl,
            )
            if validate and any(not bool(torch.isfinite(item).all()) for item in checked):
                raise ValueError("chunked effect PPO received a non-finite statistic")
            weighted = value_scale * settings.value_loss_weight * value_chunk
            weighted = weighted + value_scale * policy_chunk
            weighted = weighted - policy_scale * settings.entropy_weight * entropy_chunk
            weighted.backward()  # type: ignore[no-untyped-call]
            policy += policy_chunk.detach()
            value += value_chunk.detach()
            entropy += entropy_chunk.detach()
            approximate_kl += approximate_kl_chunk.detach()
            clip_fraction += clip_fraction_chunk.detach()
            behavior_approximate_kl += behavior_kl_chunk.detach()
            behavior_clip_fraction += behavior_clip_chunk.detach()
            active = batch.policy_mask[rows]
            if bool(active.any()):
                behavior_log_ratio_max = torch.maximum(
                    behavior_log_ratio_max,
                    behavior_log_ratio[active].abs().max().detach(),
                )
            first_chunk = False
            del output, logits, log_probabilities, probabilities
        offset += decision_shard.row_count
    if offset != batch.factor_count or first_chunk:
        raise RuntimeError("chunked effect PPO lost factor rows")
    _backward_sequence(sequence, leaves)
    total = policy + settings.value_loss_weight * value - settings.entropy_weight * entropy
    return (
        EffectPpoLoss(
            total=total,
            policy=policy,
            value=value,
            entropy=entropy,
            approximate_kl=approximate_kl,
            clip_fraction=clip_fraction,
            behavior_approximate_kl=behavior_approximate_kl,
            behavior_clip_fraction=behavior_clip_fraction,
            policy_factors=batch.policy_mask.sum(),
            value_turns=batch.value_mask.sum(),
        ),
        behavior_log_ratio_max,
    )


__all__ = [
    "ShardedBehaviorErrors",
    "backward_sharded_ppo",
    "evaluate_sharded_behavior",
]
