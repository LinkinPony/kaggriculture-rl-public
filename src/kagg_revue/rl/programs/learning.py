"""Episode-minibatch optimization for conditional-program PPO."""

from __future__ import annotations

import random
from collections import defaultdict
from contextlib import nullcontext
from typing import cast

import numpy as np
import torch
from torch import Tensor, nn
from torch import distributed as dist

from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.rl.distributed import DistributedContext
from kagg_revue.rl.programs.config import ProgramOptimizationSettings
from kagg_revue.rl.programs.data import (
    ProgramBatch,
    ProgramEpisode,
    collate_program_episodes,
)
from kagg_revue.rl.programs.model import (
    ProgramActorCritic,
    ProgramEvaluation,
)
from kagg_revue.rl.programs.objective import (
    ProgramAdvantageReference,
    ProgramPpoLoss,
    program_ppo_loss,
    terminal_program_advantages,
)


def _autocast(device: torch.device) -> object:
    return (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )


def _episode_groups(
    count: int,
    size: int,
    randomizer: random.Random,
) -> tuple[tuple[int, ...], ...]:
    order = list(range(count))
    randomizer.shuffle(order)
    return tuple(tuple(order[start : start + size]) for start in range(0, count, size))


def _advantage_reference(
    episodes: tuple[ProgramEpisode, ...],
    *,
    normalize: bool,
    context: DistributedContext,
) -> ProgramAdvantageReference:
    if isinstance(episodes[0].old_values, torch.Tensor):
        device = episodes[0].old_values.device
        old_values = torch.cat(
            [
                cast(torch.Tensor, episode.old_values).to(device=device, non_blocking=True)
                for episode in episodes
            ]
        )
        episode_index = torch.cat(
            [
                torch.full(
                    (episode.turn_count,),
                    index,
                    dtype=torch.long,
                    device=device,
                )
                for index, episode in enumerate(episodes)
            ]
        )
        outcomes = torch.tensor(
            [episode.outcome for episode in episodes],
            dtype=torch.int8,
            device=device,
        )
    else:
        old_values = torch.from_numpy(
            np.concatenate([cast(np.ndarray, episode.old_values) for episode in episodes])
        )
        episode_index = torch.from_numpy(
            np.concatenate(
                [
                    np.full(episode.turn_count, index, dtype=np.int64)
                    for index, episode in enumerate(episodes)
                ]
            )
        )
        outcomes = torch.tensor([episode.outcome for episode in episodes], dtype=torch.int8)
    advantages = terminal_program_advantages(
        outcomes,
        old_values,
        episode_index,
        normalize=normalize,
    )
    if context.enabled:
        count = outcomes.new_tensor(float(len(episodes)), dtype=torch.float64)
        mean = advantages.mean.to(torch.float64)
        second_moment = advantages.scale.to(torch.float64).square() + mean.square()
        statistics = torch.stack(
            (
                mean * count,
                second_moment * count,
                count,
                torch.count_nonzero(outcomes < 0).to(torch.float64),
                torch.count_nonzero(outcomes == 0).to(torch.float64),
                torch.count_nonzero(outcomes > 0).to(torch.float64),
            )
        )
        dist.all_reduce(statistics, op=dist.ReduceOp.SUM)
        mean = statistics[0] / statistics[2]
        scale = (statistics[1] / statistics[2] - mean.square()).clamp_min(0).sqrt()
        actor_update = int(torch.count_nonzero(statistics[3:] > 0)) >= 2
    else:
        mean = advantages.mean
        scale = advantages.scale
        actor_update = advantages.actor_update
    return ProgramAdvantageReference(
        mean=float(mean),
        scale=float(scale),
        actor_update=actor_update,
    )


def _evaluate(
    model: ProgramActorCritic,
    training_model: nn.Module,
    episodes: list[ProgramEpisode],
    contract: NativeProgramContract,
    device: torch.device,
    *,
    validate: bool,
) -> tuple[ProgramBatch, ProgramEvaluation]:
    batch = collate_program_episodes(
        episodes,
        contract,
        model.actor.architecture.model_width,
        device,
        validate=validate,
    )
    raw_evaluated = training_model(
        batch.board,
        batch.units,
        batch.global_features,
        batch.actions,
        batch.quantities,
        batch.turn_mask,
        batch.decision_mask,
        batch.program_inputs,
        batch.program_actions,
        batch.program_masks,
        batch.program_episode_index,
        batch.program_turn_index,
        economic_state=(
            batch.economic_state
            if model.actor.architecture.economic_feature_version is not None
            else None
        ),
        validate_inputs=validate,
    )
    if not isinstance(raw_evaluated, ProgramEvaluation):
        raise TypeError("conditional-program DDP evaluator returned an invalid output")
    evaluated = raw_evaluated
    return batch, evaluated


def audit_program_behavior(
    model: ProgramActorCritic,
    episodes: tuple[ProgramEpisode, ...],
    contract: NativeProgramContract,
    device: torch.device,
    *,
    episodes_per_batch: int,
) -> dict[str, float]:
    """Compare incremental behavior with full causal teacher-forced replay."""
    model.eval()
    maximum_log_error = 0.0
    maximum_value_error = 0.0
    factor_mismatches = 0
    with torch.inference_mode():
        for start in range(0, len(episodes), episodes_per_batch):
            selected = list(episodes[start : start + episodes_per_batch])
            with _autocast(device):  # type: ignore[attr-defined]
                raw_batch, raw_evaluated = _evaluate(
                    model, model, selected, contract, device, validate=True
                )
            batch = raw_batch
            programs = raw_evaluated.programs
            log_error = (programs.joint_log_probability - batch.old_joint_log_probability).abs()
            value_error = (programs.value - batch.old_values).abs()
            maximum_log_error = max(maximum_log_error, float(log_error.max()))
            maximum_value_error = max(maximum_value_error, float(value_error.max()))
            factor_mismatches += int(
                torch.count_nonzero(programs.factor_counts != batch.stochastic_factor_counts)
            )
    tolerance = 0.1 if device.type == "cuda" else 1e-4
    if (
        not np.isfinite(maximum_log_error)
        or not np.isfinite(maximum_value_error)
        or maximum_log_error > tolerance
        or maximum_value_error > tolerance
        or factor_mismatches
    ):
        raise RuntimeError("conditional-program behavior likelihood failed replay")
    return {
        "maximum_absolute_log_probability_error": maximum_log_error,
        "maximum_absolute_value_error": maximum_value_error,
        "factor_count_mismatches": float(factor_mismatches),
    }


def _evaluate_loss(
    model: ProgramActorCritic,
    training_model: nn.Module,
    episodes: list[ProgramEpisode],
    contract: NativeProgramContract,
    settings: ProgramOptimizationSettings,
    device: torch.device,
    reference: ProgramAdvantageReference,
) -> ProgramPpoLoss:
    """Evaluate one physical shard without materializing host statistics."""
    with _autocast(device):  # type: ignore[attr-defined]
        batch, evaluated = _evaluate(
            model,
            training_model,
            episodes,
            contract,
            device,
            validate=False,
        )
        advantages = terminal_program_advantages(
            batch.outcomes,
            batch.old_values,
            batch.program_episode_index,
            normalize=settings.normalize_advantage,
            reference=reference,
        )
        return program_ppo_loss(
            evaluated.programs,
            batch.old_joint_log_probability,
            advantages.values,
            batch.outcomes,
            batch.program_episode_index,
            clip_epsilon=settings.clip_epsilon,
            value_loss_weight=settings.value_loss_weight,
            entropy_weight=settings.entropy_weight,
            actor_update=advantages.actor_update,
            validate_inputs=False,
        )


def _accumulate_metrics(
    accumulated: dict[str, Tensor],
    loss: ProgramPpoLoss,
    weight: float,
) -> None:
    """Accumulate GPU-resident logical-batch means."""
    tensors = {
        "loss": loss.total.detach(),
        "policy_loss": loss.policy.detach(),
        "value_loss": loss.value.detach(),
        "value_nll": loss.value.detach(),
        "value_accuracy": loss.value_accuracy.detach(),
        "value_brier": loss.value_brier.detach(),
        "conditional_entropy": loss.entropy.detach(),
        "approximate_kl": loss.approximate_kl.detach(),
        "clip_fraction": loss.clip_fraction.detach(),
    }
    for name, value in tensors.items():
        contribution = value * weight
        accumulated[name] = (
            contribution if name not in accumulated else accumulated[name] + contribution
        )


def _global_metrics(
    accumulated: dict[str, Tensor],
    context: DistributedContext,
) -> dict[str, float]:
    """Reduce one complete logical batch and synchronize its six scalars once."""
    names = tuple(accumulated)
    materialized = torch.stack(tuple(accumulated[name] for name in names)).float()
    if context.enabled:
        dist.all_reduce(materialized, op=dist.ReduceOp.SUM)
        materialized /= context.world_size
    values = materialized.cpu().tolist()
    return dict(zip(names, values, strict=True))


def optimize_program_rollout(
    model: ProgramActorCritic,
    training_model: nn.Module,
    optimizer: torch.optim.Optimizer,
    episodes: tuple[ProgramEpisode, ...],
    contract: NativeProgramContract,
    settings: ProgramOptimizationSettings,
    device: torch.device,
    randomizer: random.Random,
    context: DistributedContext,
) -> dict[str, object]:
    """Run representative PPO minibatches through bounded execution shards."""
    if settings.episodes_per_minibatch % context.world_size:
        raise ValueError("conditional-program PPO batch must divide across ranks")
    local_minibatch_size = settings.episodes_per_minibatch // context.world_size
    if not episodes or len(episodes) % local_minibatch_size:
        raise ValueError("conditional-program episodes must fill PPO minibatches")
    reference = _advantage_reference(
        episodes,
        normalize=settings.normalize_advantage,
        context=context,
    )
    metrics: dict[str, list[float]] = defaultdict(list)
    optimizer_steps = 0
    optimizer_episodes = 0
    evaluated_episodes = 0
    backward_microbatches = 0
    stopped_early = False
    training_model.train()
    for _epoch in range(settings.ppo_epochs):
        for episode_ids in _episode_groups(len(episodes), local_minibatch_size, randomizer):
            optimizer.zero_grad(set_to_none=True)
            accumulated: dict[str, Tensor] = {}
            microbatch_size = settings.effective_episodes_per_microbatch
            starts = range(0, len(episode_ids), microbatch_size)
            for microbatch_index, start in enumerate(starts):
                microbatch_ids = episode_ids[start : start + microbatch_size]
                selected = [episodes[index] for index in microbatch_ids]
                weight = len(selected) / len(episode_ids)
                last_microbatch = microbatch_index + 1 == len(starts)
                no_sync = getattr(training_model, "no_sync", None)
                synchronization = (
                    no_sync() if not last_microbatch and callable(no_sync) else nullcontext()
                )
                with synchronization:
                    loss = _evaluate_loss(
                        model,
                        training_model,
                        selected,
                        contract,
                        settings,
                        device,
                        reference,
                    )
                    objective = loss.total * weight
                    objective.backward()  # type: ignore[no-untyped-call]
                _accumulate_metrics(accumulated, loss, weight)
                backward_microbatches += 1
                del loss, objective
            values = _global_metrics(accumulated, context)
            for name, value in values.items():
                metrics[name].append(value)
            evaluated_episodes += len(episode_ids) * context.world_size
            if values["approximate_kl"] > settings.target_kl:
                optimizer.zero_grad(set_to_none=True)
                stopped_early = True
                break
            gradient_norm = torch.nn.utils.clip_grad_norm_(
                model.parameters(), settings.gradient_clip, foreach=True
            )
            if not bool(torch.isfinite(gradient_norm)):
                raise FloatingPointError("conditional-program PPO produced a non-finite gradient")
            optimizer.step()
            optimizer_steps += 1
            optimizer_episodes += len(episode_ids) * context.world_size
            metrics["gradient_norm"].append(float(gradient_norm.detach()))
        if stopped_early:
            break
    training_model.eval()
    if not metrics["loss"]:
        raise RuntimeError("conditional-program PPO produced no minibatch")
    return {
        **{name: float(np.mean(values, dtype=np.float64)) for name, values in metrics.items()},
        "last_approximate_kl": metrics["approximate_kl"][-1],
        "maximum_approximate_kl": max(metrics["approximate_kl"]),
        "optimizer_steps": optimizer_steps,
        "optimizer_episodes": optimizer_episodes,
        "evaluated_episodes": evaluated_episodes,
        "physical_microbatches": backward_microbatches * context.world_size,
        "physical_microbatches_per_rank": backward_microbatches,
        "backward_microbatches": backward_microbatches * context.world_size,
        "distributed_world_size": context.world_size,
        "logical_episodes_per_minibatch": settings.episodes_per_minibatch,
        "physical_episodes_per_microbatch": (settings.effective_episodes_per_microbatch),
        "actor_update": reference.actor_update,
        "advantage_mean": reference.mean,
        "advantage_scale": reference.scale,
        "kl_early_stop": stopped_early,
        "kl_stop_statistic": "optimizer_minibatch_episode_mean",
    }


__all__ = ["audit_program_behavior", "optimize_program_rollout"]
