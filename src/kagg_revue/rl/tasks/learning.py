"""One-pass shared-encoder optimization for task and market PPO."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from contextlib import nullcontext
from dataclasses import asdict, dataclass, replace
from typing import Any, cast

import numpy as np
import torch
from torch import Tensor, nn
from torch.nn.utils import clip_grad_norm_
from torch.optim import Optimizer

from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.rl.data import trajectory_old_values
from kagg_revue.rl.distributed import DistributedContext
from kagg_revue.rl.tasks.config import TaskOptimizationSettings, TaskRlSettings
from kagg_revue.rl.tasks.data import (
    TaskTapeBatch,
    TaskTapeEpisode,
    collate_task_episodes,
)
from kagg_revue.rl.tasks.model import TaskTapeActorCritic, TaskTapeEvaluation
from kagg_revue.rl.tasks.objective import (
    AdvantageReference,
    TapePpoLoss,
    market_ppo_loss,
    market_terminal_advantages,
    task_ppo_loss,
    task_terminal_advantages,
)
from kagg_revue.rl.tasks.rollout import TaskRolloutReport
from kagg_revue.rl.tasks.storage import CompactTaskEpisodeTurns, TaskValueMoments

_H200_RETAINED_TASK_ROWS = 12_288


@dataclass(frozen=True)
class TaskUpdateMetrics:
    """Detached direct-objective diagnostics from one optimizer step."""

    total_loss: float
    task_policy_loss: float
    task_value_loss: float
    task_entropy: float
    task_kl: float
    task_clip_fraction: float
    market_policy_loss: float
    market_value_loss: float
    market_entropy: float
    market_kl: float
    market_clip_fraction: float
    gradient_norm: float
    actor_update: bool
    task_factors: int
    market_factors: int


@dataclass(frozen=True)
class _TaskUpdateTensors:
    """Device-resident diagnostics accumulated without microbatch syncs."""

    total_loss: Tensor
    task_policy_loss: Tensor
    task_value_loss: Tensor
    task_entropy: Tensor
    task_kl: Tensor
    task_clip_fraction: Tensor
    market_policy_loss: Tensor
    market_value_loss: Tensor
    market_entropy: Tensor
    market_kl: Tensor
    market_clip_fraction: Tensor
    gradient_norm: Tensor
    actor_update: bool
    task_factors: Tensor
    market_factors: Tensor


@dataclass(frozen=True)
class _TaskBatchEvaluation:
    """Differentiable losses for one physical PPO microbatch."""

    objective: Tensor
    task_loss: TapePpoLoss
    market_loss: TapePpoLoss
    actor_update: bool


def _number(value: Tensor) -> float:
    return float(value.detach().cpu())


def _autocast(value: Tensor) -> Any:
    if value.device.type == "cuda":
        return torch.autocast(
            device_type="cuda",
            dtype=torch.bfloat16,
        )
    return nullcontext()


def _set_ppo_training_mode(model: TaskTapeActorCritic) -> None:
    """Keep recurrent backward enabled while disabling policy-time dropout."""
    model.train()
    model.actor.scene.eval()
    model.actor.action.eval()
    model.tasks.eval()


def _evaluate_task_batch(
    model: TaskTapeActorCritic,
    batch: TaskTapeBatch,
    settings: TaskOptimizationSettings,
    has_quantity: Tensor,
    *,
    task_reference: AdvantageReference | None = None,
    market_reference: AdvantageReference | None = None,
    validate_inputs: bool = True,
    training_model: nn.Module | None = None,
    task_loss_scale: float | Tensor = 1.0,
    market_actor_loss_scale: float | Tensor = 1.0,
    market_value_scale: Tensor | None = None,
) -> _TaskBatchEvaluation:
    """Evaluate a scaled contribution to one logical PPO minibatch."""
    market_batch = batch.market
    task_batch = batch.tasks
    market_advantages = market_terminal_advantages(
        market_batch.outcomes,
        market_batch.old_values,
        market_batch.turn_mask,
        normalize=settings.normalize_advantage,
        reference=market_reference,
        validate_inputs=validate_inputs,
    )
    task_advantages = task_terminal_advantages(
        market_batch.outcomes,
        task_batch.old_values,
        task_batch.episode_index,
        normalize=settings.normalize_advantage,
        reference=task_reference,
        validate_inputs=validate_inputs,
    )
    actor_update = market_advantages.actor_update and task_advantages.actor_update
    # PPO must exactly replay the frozen behavior distribution before an update.
    _set_ppo_training_mode(model)
    forward_model = model if training_model is None else training_model
    with _autocast(market_batch.board):
        evaluation = forward_model(
            market_batch.board,
            market_batch.units,
            market_batch.global_features,
            market_batch.actions,
            market_batch.quantities,
            market_batch.phases,
            market_batch.turn_mask,
            market_batch.decision_mask,
            market_batch.skill_ids,
            task_batch.inputs,
            task_batch.actions,
            task_batch.masks,
            task_batch.episode_index,
            task_batch.turn_index,
            market_batch.turn_facts,
            market_batch.turn_fact_mask,
            market_batch.prefix_facts,
            market_batch.candidate_facts,
            market_batch.economic_state,
            validate_inputs=validate_inputs,
            policy_grad=actor_update,
            checkpoint_task_evaluation=True,
            retained_task_rows=(
                _H200_RETAINED_TASK_ROWS
                if market_batch.board.device.type == "cuda"
                and "H200" in torch.cuda.get_device_name(market_batch.board.device)
                else 0
            ),
        )
        if not isinstance(evaluation, TaskTapeEvaluation):
            raise TypeError("unit-task training model returned an invalid evaluation")
        task_loss = task_ppo_loss(
            evaluation.tasks,
            task_batch.old_joint_log_probability,
            task_advantages.values,
            market_batch.outcomes,
            task_batch.episode_index,
            clip_epsilon=settings.clip_epsilon,
            value_loss_weight=settings.task_value_loss_weight,
            entropy_weight=settings.task_entropy_weight,
            actor_update=actor_update,
            validate_inputs=validate_inputs,
        )
        market_loss = market_ppo_loss(
            evaluation.market.policy,
            evaluation.market.outcome_logits,
            market_batch.actions,
            market_batch.quantities,
            market_batch.legal_mask,
            batch.market_factor_mask,
            market_batch.old_log_probability,
            market_advantages.values,
            market_batch.outcomes,
            market_batch.turn_mask,
            has_quantity,
            clip_epsilon=settings.clip_epsilon,
            value_loss_weight=settings.market_value_loss_weight,
            entropy_weight=settings.market_entropy_weight,
            actor_update=actor_update,
            validate_inputs=validate_inputs,
        )
        market_actor_loss = (
            market_loss.total - settings.market_value_loss_weight * market_loss.value
        )
        value_scale = 1.0 if market_value_scale is None else market_value_scale
        total = (
            task_loss_scale * task_loss.total
            + market_actor_loss_scale * market_actor_loss
            + value_scale * settings.market_value_loss_weight * market_loss.value
        )
    return _TaskBatchEvaluation(total, task_loss, market_loss, actor_update)


def _task_update_metrics(
    evaluation: _TaskBatchEvaluation,
    gradient_norm: Tensor,
) -> TaskUpdateMetrics:
    """Detach one physical-batch evaluation into optimization diagnostics."""
    return _materialize_update_metrics(_task_update_tensors(evaluation, gradient_norm))


def _task_update_tensors(
    evaluation: _TaskBatchEvaluation,
    gradient_norm: Tensor,
) -> _TaskUpdateTensors:
    """Keep physical-batch diagnostics on device until the logical step ends."""
    task_loss = evaluation.task_loss
    market_loss = evaluation.market_loss
    return _TaskUpdateTensors(
        total_loss=evaluation.objective.detach(),
        task_policy_loss=task_loss.policy.detach(),
        task_value_loss=task_loss.value.detach(),
        task_entropy=task_loss.entropy.detach(),
        task_kl=task_loss.approximate_kl.detach(),
        task_clip_fraction=task_loss.clip_fraction.detach(),
        market_policy_loss=market_loss.policy.detach(),
        market_value_loss=market_loss.value.detach(),
        market_entropy=market_loss.entropy.detach(),
        market_kl=market_loss.approximate_kl.detach(),
        market_clip_fraction=market_loss.clip_fraction.detach(),
        gradient_norm=gradient_norm.detach(),
        actor_update=evaluation.actor_update,
        task_factors=task_loss.policy_factors.detach(),
        market_factors=market_loss.policy_factors.detach(),
    )


def _materialize_update_metrics(row: _TaskUpdateTensors) -> TaskUpdateMetrics:
    """Transfer all logical-step diagnostics with one device synchronization."""
    names = (
        "total_loss",
        "task_policy_loss",
        "task_value_loss",
        "task_entropy",
        "task_kl",
        "task_clip_fraction",
        "market_policy_loss",
        "market_value_loss",
        "market_entropy",
        "market_kl",
        "market_clip_fraction",
        "gradient_norm",
        "task_factors",
        "market_factors",
    )
    values = torch.stack([getattr(row, name).float() for name in names]).cpu().tolist()
    numbers = dict(zip(names, values, strict=True))
    return TaskUpdateMetrics(
        total_loss=numbers["total_loss"],
        task_policy_loss=numbers["task_policy_loss"],
        task_value_loss=numbers["task_value_loss"],
        task_entropy=numbers["task_entropy"],
        task_kl=numbers["task_kl"],
        task_clip_fraction=numbers["task_clip_fraction"],
        market_policy_loss=numbers["market_policy_loss"],
        market_value_loss=numbers["market_value_loss"],
        market_entropy=numbers["market_entropy"],
        market_kl=numbers["market_kl"],
        market_clip_fraction=numbers["market_clip_fraction"],
        gradient_norm=numbers["gradient_norm"],
        actor_update=row.actor_update,
        task_factors=int(numbers["task_factors"]),
        market_factors=int(numbers["market_factors"]),
    )


def optimize_task_batch(
    model: TaskTapeActorCritic,
    batch: TaskTapeBatch,
    optimizer: Optimizer,
    settings: TaskOptimizationSettings,
    has_quantity: Tensor,
    *,
    task_reference: AdvantageReference | None = None,
    market_reference: AdvantageReference | None = None,
    validate_inputs: bool = True,
    training_model: nn.Module | None = None,
    market_value_scale: Tensor | None = None,
) -> tuple[TaskUpdateMetrics, TapePpoLoss, TapePpoLoss]:
    """Update all task-level and direct-market factors from complete matches."""
    evaluation = _evaluate_task_batch(
        model,
        batch,
        settings,
        has_quantity,
        task_reference=task_reference,
        market_reference=market_reference,
        validate_inputs=validate_inputs,
        training_model=training_model,
        market_value_scale=market_value_scale,
    )
    optimizer.zero_grad(set_to_none=True)
    evaluation.objective.backward()  # type: ignore[no-untyped-call]
    gradient_norm = clip_grad_norm_(model.parameters(), settings.gradient_clip)
    optimizer.step()
    metrics = _task_update_metrics(evaluation, gradient_norm)
    return metrics, evaluation.task_loss, evaluation.market_loss


def _as_int(value: object, name: str) -> int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"unit-task {name} is not numeric")
    return int(value)


def _as_float(value: object, name: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"unit-task {name} is not numeric")
    return float(value)


def _advantage_references(
    episodes: Sequence[TaskTapeEpisode],
    context: DistributedContext,
) -> tuple[AdvantageReference, AdvantageReference]:
    """Compute exact rollout-global task and market normalization."""
    outcomes = {episode.trajectory.outcome for episode in episodes}
    market_sum = 0.0
    market_count = 0
    task_episode_moments: list[tuple[float, float]] = []
    for episode in episodes:
        outcome = float(episode.trajectory.outcome)
        market_values = trajectory_old_values(episode.trajectory)
        market_sum += float(np.sum(outcome - market_values))
        market_count += int(market_values.size)
        moments: TaskValueMoments | None = None
        if episode.task_records:
            old_values = np.asarray(
                [record.old_value for record in episode.task_records],
                dtype=np.float64,
            )
            moments = TaskValueMoments(
                int(old_values.size),
                float(old_values.sum()),
                float(np.square(old_values).sum()),
            )
        elif episode.compact_task_turns:
            if isinstance(episode.compact_task_turns, CompactTaskEpisodeTurns):
                moments = episode.compact_task_turns.old_value_moments
            else:
                old_values = np.concatenate(
                    [record.old_values for record in episode.compact_task_turns]
                ).astype(np.float64, copy=False)
                moments = TaskValueMoments(
                    int(old_values.size),
                    float(old_values.sum()),
                    float(np.square(old_values).sum()),
                )
        if moments is not None:
            if moments.count < 1:
                raise ValueError("unit-task episode has no task value factors")
            old_mean = moments.total / moments.count
            old_square_mean = moments.square_total / moments.count
            task_episode_moments.append(
                (
                    outcome - old_mean,
                    outcome * outcome - 2.0 * outcome * old_mean + old_square_mean,
                )
            )
    if market_count < 1 or not task_episode_moments:
        raise ValueError("unit-task rollout lacks market turns or task decisions")
    local = {
        "outcomes": tuple(sorted(outcomes)),
        "market_sum": market_sum,
        "market_count": market_count,
        "task_episode_sum": float(sum(value[0] for value in task_episode_moments)),
        "task_episode_count": len(task_episode_moments),
    }
    summaries = context.all_gather(local)
    global_outcomes = {
        int(outcome)
        for summary in summaries
        for outcome in cast(tuple[int, ...], summary["outcomes"])
    }
    actor_update = len(global_outcomes) >= 2
    global_market_count = sum(
        _as_int(summary["market_count"], "market advantage count") for summary in summaries
    )
    global_task_count = sum(
        _as_int(summary["task_episode_count"], "task advantage count") for summary in summaries
    )
    if global_market_count < 1 or global_task_count < 1:
        raise ValueError("distributed unit-task rollout lacks policy factors")
    market_mean = (
        sum(_as_float(summary["market_sum"], "market advantage sum") for summary in summaries)
        / global_market_count
    )
    market_square = 0.0
    for episode in episodes:
        raw = float(episode.trajectory.outcome) - trajectory_old_values(episode.trajectory)
        market_square += float(np.sum(np.square(raw - market_mean)))
    task_mean = (
        sum(_as_float(summary["task_episode_sum"], "task advantage sum") for summary in summaries)
        / global_task_count
    )
    task_square = float(
        sum(
            square_mean - 2.0 * task_mean * mean + task_mean * task_mean
            for mean, square_mean in task_episode_moments
        )
    )
    squares = context.all_gather((market_square, task_square))
    market_scale = math.sqrt(
        max(
            0.0,
            sum(value[0] for value in squares) / global_market_count,
        )
    )
    task_variance = sum(value[1] for value in squares) / global_task_count
    return (
        AdvantageReference(
            task_mean,
            math.sqrt(max(0.0, task_variance)),
            actor_update,
        ),
        AdvantageReference(market_mean, market_scale, actor_update),
    )


def _optimization_metrics(rows: Sequence[TaskUpdateMetrics]) -> dict[str, object]:
    if not rows:
        raise RuntimeError("unit-task update produced no optimizer steps")
    numeric = (
        "total_loss",
        "task_policy_loss",
        "task_value_loss",
        "task_entropy",
        "task_clip_fraction",
        "market_policy_loss",
        "market_value_loss",
        "market_entropy",
        "market_clip_fraction",
        "gradient_norm",
    )
    return {
        **{name: float(np.mean([getattr(row, name) for row in rows])) for name in numeric},
        "maximum_task_kl": max(row.task_kl for row in rows),
        "maximum_market_kl": max(row.market_kl for row in rows),
        "actor_steps": sum(row.actor_update for row in rows),
        "optimizer_steps": len(rows),
        "task_factors": sum(row.task_factors for row in rows),
        "market_factors": sum(row.market_factors for row in rows),
    }


@dataclass(frozen=True)
class _EpisodeLossCounts:
    """Reduction denominators for one episode group."""

    task_episodes: int
    market_episodes: int
    market_turns: int


def _episode_loss_counts(episodes: Sequence[TaskTapeEpisode]) -> _EpisodeLossCounts:
    """Measure objective denominators without materializing device tensors."""
    return _EpisodeLossCounts(
        task_episodes=sum(
            bool(episode.task_records or episode.compact_task_turns) for episode in episodes
        ),
        market_episodes=sum(
            bool(np.asarray(episode.market_factor_mask).any()) for episode in episodes
        ),
        market_turns=sum(len(episode.trajectory.turns) for episode in episodes),
    )


def _combine_microbatch_metrics(
    rows: Sequence[TaskUpdateMetrics],
    microbatch_counts: Sequence[_EpisodeLossCounts],
    logical_counts: _EpisodeLossCounts,
    gradient_norm: Tensor,
) -> TaskUpdateMetrics:
    """Recover one logical-minibatch metric row from physical microbatches."""
    if not rows or len(rows) != len(microbatch_counts):
        raise RuntimeError("unit-task PPO microbatch metrics are incomplete")
    if any(row.actor_update != rows[0].actor_update for row in rows[1:]):
        raise RuntimeError("unit-task PPO microbatches disagree on actor updates")

    def weighted(name: str, weights: Sequence[int], denominator: int) -> float:
        if denominator < 1:
            return 0.0
        return (
            sum(
                float(getattr(row, name)) * weight
                for row, weight in zip(rows, weights, strict=True)
            )
            / denominator
        )

    task_weights = [counts.task_episodes for counts in microbatch_counts]
    market_weights = [counts.market_episodes for counts in microbatch_counts]
    turn_weights = [counts.market_turns for counts in microbatch_counts]
    factor_weights = [row.market_factors for row in rows]
    market_factors = sum(factor_weights)
    return TaskUpdateMetrics(
        total_loss=sum(row.total_loss for row in rows),
        task_policy_loss=weighted("task_policy_loss", task_weights, logical_counts.task_episodes),
        task_value_loss=weighted("task_value_loss", task_weights, logical_counts.task_episodes),
        task_entropy=weighted("task_entropy", task_weights, logical_counts.task_episodes),
        task_kl=weighted("task_kl", task_weights, logical_counts.task_episodes),
        task_clip_fraction=weighted(
            "task_clip_fraction", task_weights, logical_counts.task_episodes
        ),
        market_policy_loss=weighted(
            "market_policy_loss", market_weights, logical_counts.market_episodes
        ),
        market_value_loss=weighted("market_value_loss", turn_weights, logical_counts.market_turns),
        market_entropy=weighted("market_entropy", market_weights, logical_counts.market_episodes),
        market_kl=weighted("market_kl", factor_weights, market_factors),
        market_clip_fraction=weighted("market_clip_fraction", factor_weights, market_factors),
        gradient_norm=_number(gradient_norm),
        actor_update=rows[0].actor_update,
        task_factors=sum(row.task_factors for row in rows),
        market_factors=market_factors,
    )


def _combine_microbatch_tensors(
    rows: Sequence[_TaskUpdateTensors],
    microbatch_counts: Sequence[_EpisodeLossCounts],
    logical_counts: _EpisodeLossCounts,
    gradient_norm: Tensor,
) -> _TaskUpdateTensors:
    """Recover one logical metric row while all values remain on device."""
    if not rows or len(rows) != len(microbatch_counts):
        raise RuntimeError("unit-task PPO microbatch metrics are incomplete")
    if any(row.actor_update != rows[0].actor_update for row in rows[1:]):
        raise RuntimeError("unit-task PPO microbatches disagree on actor updates")

    exemplar = rows[0].total_loss

    def weighted(name: str, weights: Sequence[int], denominator: int) -> Tensor:
        if denominator < 1:
            return exemplar.new_zeros(())
        return (
            sum(
                (getattr(row, name) * weight for row, weight in zip(rows, weights, strict=True)),
                start=exemplar.new_zeros(()),
            )
            / denominator
        )

    task_weights = [counts.task_episodes for counts in microbatch_counts]
    market_weights = [counts.market_episodes for counts in microbatch_counts]
    turn_weights = [counts.market_turns for counts in microbatch_counts]
    market_factors = sum(
        (row.market_factors for row in rows),
        start=rows[0].market_factors.new_zeros(()),
    )
    # Market KL is factor-weighted. Avoid reading the device factor counts by
    # weighting with the tensors directly rather than using the generic helper.
    market_kl = sum(
        (row.market_kl * row.market_factors for row in rows),
        start=exemplar.new_zeros(()),
    ) / market_factors.clamp_min(1)
    market_clip_fraction = sum(
        (row.market_clip_fraction * row.market_factors for row in rows),
        start=exemplar.new_zeros(()),
    ) / market_factors.clamp_min(1)
    return _TaskUpdateTensors(
        total_loss=sum(
            (row.total_loss for row in rows),
            start=exemplar.new_zeros(()),
        ),
        task_policy_loss=weighted("task_policy_loss", task_weights, logical_counts.task_episodes),
        task_value_loss=weighted("task_value_loss", task_weights, logical_counts.task_episodes),
        task_entropy=weighted("task_entropy", task_weights, logical_counts.task_episodes),
        task_kl=weighted("task_kl", task_weights, logical_counts.task_episodes),
        task_clip_fraction=weighted(
            "task_clip_fraction", task_weights, logical_counts.task_episodes
        ),
        market_policy_loss=weighted(
            "market_policy_loss", market_weights, logical_counts.market_episodes
        ),
        market_value_loss=weighted("market_value_loss", turn_weights, logical_counts.market_turns),
        market_entropy=weighted("market_entropy", market_weights, logical_counts.market_episodes),
        market_kl=market_kl,
        market_clip_fraction=market_clip_fraction,
        gradient_norm=gradient_norm.detach(),
        actor_update=rows[0].actor_update,
        task_factors=sum(
            (row.task_factors for row in rows),
            start=rows[0].task_factors.new_zeros(()),
        ),
        market_factors=market_factors,
    )


def _global_step_metrics(
    metrics: TaskUpdateMetrics,
    logical_counts: _EpisodeLossCounts,
    context: DistributedContext,
) -> tuple[TaskUpdateMetrics, float, float]:
    """Use globally weighted KL/clip means while retaining rank maxima."""
    workers = context.all_gather(
        {
            "task_kl": metrics.task_kl,
            "task_clip_fraction": metrics.task_clip_fraction,
            "task_episodes": logical_counts.task_episodes,
            "market_kl": metrics.market_kl,
            "market_clip_fraction": metrics.market_clip_fraction,
            "market_factors": metrics.market_factors,
        }
    )

    def weighted(name: str, weight: str) -> float:
        denominator = sum(int(row[weight]) for row in workers)
        if denominator < 1:
            return 0.0
        return sum(float(row[name]) * int(row[weight]) for row in workers) / denominator

    task_kl = weighted("task_kl", "task_episodes")
    market_kl = weighted("market_kl", "market_factors")
    return (
        replace(
            metrics,
            task_kl=task_kl,
            task_clip_fraction=weighted("task_clip_fraction", "task_episodes"),
            market_kl=market_kl,
            market_clip_fraction=weighted("market_clip_fraction", "market_factors"),
        ),
        max(float(row["task_kl"]) for row in workers),
        max(float(row["market_kl"]) for row in workers),
    )


def _optimize_logical_minibatch(
    episodes: Sequence[TaskTapeEpisode],
    model: TaskTapeActorCritic,
    training_model: nn.Module,
    optimizer: Optimizer,
    settings: TaskRlSettings,
    has_quantity: Tensor,
    device: torch.device,
    context: DistributedContext,
    contract: NativeTaskContract,
    task_reference: AdvantageReference,
    market_reference: AdvantageReference,
    *,
    validate_inputs: bool,
) -> TaskUpdateMetrics:
    """Accumulate bounded physical batches into one unchanged PPO update."""
    logical_counts = _episode_loss_counts(episodes)
    if logical_counts.task_episodes != len(episodes):
        raise ValueError("unit-task PPO episode lacks a task decision tape")
    if logical_counts.market_turns < 1:
        raise ValueError("unit-task PPO minibatch lacks official turns")
    microbatch_size = settings.optimization.effective_episodes_per_microbatch
    groups = [
        episodes[start : start + microbatch_size]
        for start in range(0, len(episodes), microbatch_size)
    ]
    microbatch_counts = [_episode_loss_counts(group) for group in groups]
    local_market_value_scale = context.loss_scales(
        torch.tensor(
            [float(logical_counts.market_turns)],
            dtype=torch.float32,
            device=device,
        )
    )[0]
    optimizer.zero_grad(set_to_none=True)
    rows: list[_TaskUpdateTensors] = []
    task_catalog = model.tasks.catalog()
    for microbatch_index, (group, counts) in enumerate(zip(groups, microbatch_counts, strict=True)):
        batch = collate_task_episodes(
            list(group),
            context_width=model.actor.architecture.model_width,
            device=device,
            contract=contract,
            factorized=model.tasks.factorized is not None,
            history_window=model.tasks.architecture.history_window,
            task_catalog=task_catalog,
        )
        task_scale = counts.task_episodes / logical_counts.task_episodes
        market_actor_scale = (
            counts.market_episodes / logical_counts.market_episodes
            if logical_counts.market_episodes
            else 0.0
        )
        market_value_scale = (
            local_market_value_scale * counts.market_turns / logical_counts.market_turns
        )
        last_microbatch = microbatch_index + 1 == len(groups)
        no_sync = getattr(training_model, "no_sync", None)
        synchronization: Any = (
            no_sync() if not last_microbatch and callable(no_sync) else nullcontext()
        )
        with synchronization:
            evaluation = _evaluate_task_batch(
                model,
                batch,
                settings.optimization,
                has_quantity,
                task_reference=task_reference,
                market_reference=market_reference,
                validate_inputs=validate_inputs and microbatch_index == 0,
                training_model=training_model,
                task_loss_scale=task_scale,
                market_actor_loss_scale=market_actor_scale,
                market_value_scale=market_value_scale,
            )
            evaluation.objective.backward()  # type: ignore[no-untyped-call]
        rows.append(
            _task_update_tensors(
                evaluation,
                evaluation.objective.new_zeros(()),
            )
        )
        del batch, evaluation
    gradient_norm = clip_grad_norm_(
        model.parameters(),
        settings.optimization.gradient_clip,
        foreach=True,
    )
    optimizer.step()
    return _materialize_update_metrics(
        _combine_microbatch_tensors(
            rows,
            microbatch_counts,
            logical_counts,
            gradient_norm,
        )
    )


def optimize_task_rollout(
    report: TaskRolloutReport,
    model: TaskTapeActorCritic,
    training_model: nn.Module,
    optimizer: Optimizer,
    settings: TaskRlSettings,
    has_quantity: Tensor,
    device: torch.device,
    randomizer: random.Random,
    context: DistributedContext,
    contract: NativeTaskContract,
    *,
    smoke: bool,
) -> dict[str, object]:
    """Run synchronized PPO over one rank-sharded complete-match panel."""
    episodes = list(report.episodes)
    task_reference, market_reference = _advantage_references(episodes, context)
    rows: list[TaskUpdateMetrics] = []
    kl_trace: list[dict[str, float | int]] = []
    maximum_rank_task_kl = 0.0
    maximum_rank_market_kl = 0.0
    stopped_early = False
    validate = True
    epochs = 1 if smoke else settings.optimization.ppo_epochs
    for _epoch in range(epochs):
        order = list(range(len(episodes)))
        randomizer.shuffle(order)
        for start in range(
            0,
            len(order),
            settings.optimization.episodes_per_minibatch,
        ):
            indices = order[start : start + settings.optimization.episodes_per_minibatch]
            metrics = _optimize_logical_minibatch(
                [episodes[index] for index in indices],
                model,
                training_model,
                optimizer,
                settings,
                has_quantity,
                device,
                context,
                contract,
                task_reference=task_reference,
                market_reference=market_reference,
                validate_inputs=validate,
            )
            validate = False
            logical_counts = _episode_loss_counts([episodes[index] for index in indices])
            metrics, rank_task_kl, rank_market_kl = _global_step_metrics(
                metrics,
                logical_counts,
                context,
            )
            rows.append(metrics)
            maximum_rank_task_kl = max(maximum_rank_task_kl, rank_task_kl)
            maximum_rank_market_kl = max(maximum_rank_market_kl, rank_market_kl)
            kl_trace.append(
                {
                    "step": len(rows),
                    "task_kl": metrics.task_kl,
                    "market_kl": metrics.market_kl,
                    "task_clip_fraction": metrics.task_clip_fraction,
                    "market_clip_fraction": metrics.market_clip_fraction,
                    "maximum_rank_task_kl": rank_task_kl,
                    "maximum_rank_market_kl": rank_market_kl,
                }
            )
            global_kl = max(metrics.task_kl, metrics.market_kl)
            if global_kl > settings.optimization.target_kl:
                stopped_early = True
                break
        if stopped_early:
            break
    local_result = _optimization_metrics(rows)
    worker_results = context.all_gather(local_result)
    numeric = (
        "total_loss",
        "task_policy_loss",
        "task_value_loss",
        "task_entropy",
        "task_clip_fraction",
        "market_policy_loss",
        "market_value_loss",
        "market_entropy",
        "market_clip_fraction",
        "gradient_norm",
    )
    result: dict[str, object] = {
        **{
            name: float(
                np.mean(
                    [_as_float(worker[name], f"optimization {name}") for worker in worker_results]
                )
            )
            for name in numeric
        },
        "maximum_task_kl": max(
            _as_float(worker["maximum_task_kl"], "maximum task KL") for worker in worker_results
        ),
        "maximum_market_kl": max(
            _as_float(worker["maximum_market_kl"], "maximum market KL") for worker in worker_results
        ),
        "actor_steps": _as_int(worker_results[0]["actor_steps"], "actor steps"),
        "optimizer_steps": _as_int(worker_results[0]["optimizer_steps"], "optimizer steps"),
        "task_factors": sum(
            _as_int(worker["task_factors"], "task factors") for worker in worker_results
        ),
        "market_factors": sum(
            _as_int(worker["market_factors"], "market factors") for worker in worker_results
        ),
    }
    result.update(
        stopped_for_target_kl=stopped_early,
        kl_stop_statistic="global_weighted_mean",
        kl_stop_threshold=settings.optimization.target_kl,
        last_task_kl=rows[-1].task_kl,
        last_market_kl=rows[-1].market_kl,
        maximum_rank_task_kl=maximum_rank_task_kl,
        maximum_rank_market_kl=maximum_rank_market_kl,
        kl_trace=kl_trace,
        task_advantage=asdict(task_reference),
        market_advantage=asdict(market_reference),
    )
    return result


__all__ = [
    "TaskUpdateMetrics",
    "optimize_task_batch",
    "optimize_task_rollout",
]
