"""Undiscounted complete-match PPO training and artifact reports."""

from __future__ import annotations

import copy
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import Tensor, nn
from torch import multiprocessing as torch_multiprocessing
from torch.nn import functional
from torch.nn.parallel import DistributedDataParallel

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.observability import (
    ScalarLogger,
    observability_report,
    synchronize,
    throughput,
)
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.economics import EconomicStateLayout
from kagg_revue.policy.runtime import load_actor
from kagg_revue.policy.vocabulary import CURRENT_ACTIONS
from kagg_revue.rl.behavior import freeze_behavior_statistics
from kagg_revue.rl.checkpoint import (
    CheckpointStore,
    build_checkpoint_payload,
    capture_training_state,
    deserialize_training_state,
    restore_checkpoint,
    serialize_training_state,
)
from kagg_revue.rl.config import RlSettings
from kagg_revue.rl.data import (
    RolloutMatch,
    TensorRolloutBatch,
    Trajectory,
    TrajectoryTurns,
    opening_residual_inputs,
    trajectory_decisions,
    trajectory_old_values,
)
from kagg_revue.rl.distributed import (
    DistributedContext,
    aggregate_optimization_summaries,
    aggregate_rollout_shards,
    destroy_context,
    even_shard,
    initialize_context,
    local_value,
    single_process_context,
)
from kagg_revue.rl.initialization import initialize_training_actor
from kagg_revue.rl.minibatch import RolloutBatchPipeline
from kagg_revue.rl.opening.noise import (
    OpeningNoisePlan,
    build_opening_noise_plan,
    probe_official_openings,
)
from kagg_revue.rl.opponents import load_frozen_actor_opponent
from kagg_revue.rl.outcome import (
    ActorCriticOutput,
    OutcomeActorCritic,
    outcome_labels,
    ppo_loss,
)
from kagg_revue.rl.pfsp import HistoricalPfsp, HistoricalPolicy, actor_fingerprint
from kagg_revue.rl.reward import margin_augmented_return, margin_augmented_returns
from kagg_revue.rl.rollout.collector import RolloutCollector
from kagg_revue.rl.rollout.population import (
    opponent_outcome_metrics,
    weighted_rollout_jobs,
)
from kagg_revue.rl.rollout.scheduler import rollout_jobs

SUBMISSION_LIMIT_BYTES = 100_000_000


def _resolve(root: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _as_int(value: object, name: str) -> int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"resolved environment {name} is not numeric")
    return int(value)


def _as_float(value: object, name: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"{name} is not numeric")
    return float(value)


def _historical_model(
    current: OutcomeActorCritic,
    policy: HistoricalPolicy,
    reusable: OutcomeActorCritic | None = None,
) -> OutcomeActorCritic:
    """Install a selected actor into one stable graph-safe model allocation."""
    frozen = copy.deepcopy(current) if reusable is None else reusable
    parameter_pointers = tuple(parameter.data_ptr() for parameter in frozen.actor.parameters())
    frozen.actor.load_state_dict(policy.actor_state, strict=True)
    if tuple(parameter.data_ptr() for parameter in frozen.actor.parameters()) != (
        parameter_pointers
    ):
        raise RuntimeError("historical actor loading replaced captured parameter storage")
    frozen.eval()
    frozen.requires_grad_(False)
    return frozen


def resolve_rl_paths(settings: RlSettings, root: Path) -> RlSettings:
    """Resolve actor, manifest and output paths against the repository."""
    return settings.model_copy(
        update={
            "initial_actor": _resolve(root, settings.initial_actor),
            "resume_checkpoint": (
                _resolve(root, settings.resume_checkpoint)
                if settings.resume_checkpoint is not None
                else None
            ),
            "public_agent_manifest": _resolve(root, settings.public_agent_manifest),
            "output_dir": _resolve(root, settings.output_dir),
            "frozen_actor_opponents": {
                opponent_id: opponent.model_copy(
                    update={"checkpoint": _resolve(root, opponent.checkpoint)}
                )
                for opponent_id, opponent in settings.frozen_actor_opponents.items()
            },
        }
    )


def _prepare_output(settings: RlSettings, root: Path) -> None:
    output_root = (root / "outputs").resolve()
    if not settings.output_dir.is_relative_to(output_root):
        raise ValueError(f"RL output must be under {output_root}")
    if settings.output_dir.exists():
        raise FileExistsError(f"RL output already exists: {settings.output_dir}")
    settings.output_dir.mkdir(parents=True)


def _validate_actor(
    model: OutcomeActorCritic,
    keys: tuple[str, ...],
    encoder_version: str,
    fact_version: str | None,
    backend: BackendApi,
    settings: RlSettings,
) -> tuple[Tensor, dict[str, object]]:
    architecture = model.actor.architecture
    codec = cast(dict[str, Any], backend.action_codec_spec())
    native_keys = tuple(str(key) for key in cast(list[object], codec["keys"]))
    if keys != native_keys:
        raise ValueError("initial actor and native action vocabularies differ")
    encoder = cast(dict[str, Any], backend.actor_encoder_spec())
    if encoder_version != str(encoder["version"]):
        raise ValueError("initial actor and native observation encoders differ")
    if (
        architecture.board_shape[1] != int(encoder["board_channels"])
        or architecture.unit_shape[2] != int(encoder["unit_feat"])
        or architecture.global_features != int(encoder["global_feat"])
        or architecture.unit_shape[1] != settings.unit_limit
    ):
        raise ValueError("initial actor architecture differs from the native tensor ABI")
    fact_spec = cast(dict[str, Any], backend.derived_fact_spec())
    expected_fact = (
        str(fact_spec["version"]),
        int(fact_spec["turn_features"]),
        int(fact_spec["prefix_features"]),
        int(fact_spec["candidate_features"]),
    )
    actual_fact = (
        architecture.derived_fact_version,
        architecture.turn_fact_features,
        architecture.prefix_fact_features,
        architecture.candidate_fact_features,
    )
    if any(actual_fact[1:]) and actual_fact != expected_fact:
        raise ValueError("initial actor and native derived-fact contracts differ")
    if fact_version != architecture.derived_fact_version:
        raise ValueError("initial actor artifact carries a different fact identity")
    if architecture.economic_feature_version is not None:
        EconomicStateLayout.from_spec(
            cast(
                dict[str, int],
                backend.gpu_policy_state_spec(
                    architecture.board_shape[-1],
                    settings.unit_limit,
                ),
            ),
            board_size=architecture.board_shape[-1],
            unit_limit=settings.unit_limit,
        )
    resolved = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=dict(settings.environment)).configuration,
    )
    board_size = _as_int(resolved["boardSize"], "boardSize")
    if architecture.board_shape[2:] != (board_size, board_size):
        raise ValueError("initial actor board shape differs from the environment")
    if architecture.max_history < _as_int(resolved["episodeSteps"], "episodeSteps"):
        raise ValueError("initial actor history cannot cover the resolved season")
    if architecture.max_decisions < settings.unit_limit + _as_int(
        resolved["maxMarketOrdersPerTurn"], "maxMarketOrdersPerTurn"
    ):
        raise ValueError("initial actor cannot represent one complete official turn")
    has_quantity = torch.as_tensor(codec["has_quantity"], dtype=torch.bool)
    if has_quantity.shape != (architecture.action_tokens,):
        raise ValueError("native quantity mask differs from the actor vocabulary")
    return has_quantity, resolved


def _trajectory_terminal_return(trajectory: Trajectory, settings: RlSettings) -> float:
    """Return the configured complete-match actor target for one perspective."""
    if settings.terminal_reward.mode == "wdl":
        return float(trajectory.outcome)
    return margin_augmented_return(
        trajectory.outcome,
        trajectory.terminal_cash - trajectory.opponent_cash,
        beta=settings.terminal_reward.margin_beta,
        cash_scale=settings.terminal_reward.margin_cash_scale,
    )


def _batch_terminal_returns(batch: TensorRolloutBatch, settings: RlSettings) -> Tensor:
    """Return configured actor targets for one already validated minibatch."""
    if settings.terminal_reward.mode == "wdl":
        return batch.outcomes.float()
    return margin_augmented_returns(
        batch.outcomes,
        batch.cash_differences,
        beta=settings.terminal_reward.margin_beta,
        cash_scale=settings.terminal_reward.margin_cash_scale,
        validate=False,
    )


def _advantage_statistics(
    trajectories: list[Trajectory],
    settings: RlSettings,
    context: DistributedContext,
) -> tuple[float, float, bool]:
    """Return globally normalized advantage moments on every rank."""
    if not trajectories:
        raise ValueError("local rollout shard contains no trajectories")
    terminal_returns = [
        _trajectory_terminal_return(trajectory, settings) for trajectory in trajectories
    ]
    values = np.concatenate(
        [
            terminal_return - trajectory_old_values(trajectory)
            for terminal_return, trajectory in zip(
                terminal_returns,
                trajectories,
                strict=True,
            )
        ]
    )
    if values.size == 0:
        raise ValueError("local rollout shard contains no valid turns")
    local = (
        min(terminal_returns),
        max(terminal_returns),
        int(values.size),
        float(values.sum(dtype=np.float64)),
        float(np.square(values, dtype=np.float64).sum(dtype=np.float64)),
        float(np.max(np.abs(values))),
    )
    gathered = context.all_gather(local)
    return_minimum = min(row[0] for row in gathered)
    return_maximum = max(row[1] for row in gathered)
    actor_update = return_maximum - return_minimum > 1e-6
    count = sum(row[2] for row in gathered)
    total = sum(row[3] for row in gathered)
    squared_total = sum(row[4] for row in gathered)
    maximum = max(row[5] for row in gathered)
    if count < 1:
        raise ValueError("distributed rollout panel contains no valid turns")
    if actor_update and maximum <= 1e-6:
        return 0.0, 1.0, False
    if not settings.normalize_advantage or not actor_update:
        return 0.0, 1.0, actor_update
    mean = total / count
    variance = max(0.0, squared_total / count - mean * mean)
    scale = float(np.sqrt(variance))
    if not np.isfinite(scale) or scale <= 1e-6:
        return 0.0, 1.0, False
    return mean, scale, True


def _dense_reward_diagnostics(
    trajectories: list[Trajectory], terminal_returns: list[float]
) -> dict[str, float]:
    absolute: list[float] = []
    residuals: list[float] = []
    for trajectory, terminal_return in zip(trajectories, terminal_returns, strict=True):
        values = trajectory_old_values(trajectory)
        following = np.concatenate((values[1:], np.zeros(1, dtype=np.float64)))
        rewards = following - values
        rewards[-1] += terminal_return
        absolute.extend(np.abs(rewards).tolist())
        residuals.append(float(rewards.sum() - (terminal_return - values[0])))
    return {
        "mean_absolute_potential_reward": float(np.mean(absolute)),
        "maximum_telescoping_residual": float(np.max(np.abs(residuals))),
    }


def _autocast(device: torch.device) -> Any:
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.bfloat16)
    return nullcontext()


def _optimization_step(
    training_model: nn.Module,
    model: OutcomeActorCritic,
    batch: TensorRolloutBatch,
    settings: RlSettings,
    device: torch.device,
    has_quantity: Tensor,
    advantage_mean: float,
    advantage_scale: float,
    actor_update: bool,
    optimizer: torch.optim.Optimizer,
    context: DistributedContext,
) -> dict[str, Tensor]:
    terminal_returns = _batch_terminal_returns(batch, settings)
    advantages = terminal_returns[:, None] - batch.old_values.float()
    if settings.normalize_advantage and actor_update:
        advantages = (advantages - advantage_mean) / advantage_scale
    advantages = advantages.masked_fill(~batch.turn_mask, 0.0)
    optimizer.zero_grad(set_to_none=True)
    model.actor.eval()
    if model.actor.strategy is not None:
        model.actor.strategy.train(actor_update)
    model.outcome.train()
    board = batch.board.float() if device.type == "cpu" else batch.board
    units = batch.units.float() if device.type == "cpu" else batch.units
    globals_ = batch.global_features.float() if device.type == "cpu" else batch.global_features
    turn_facts = batch.turn_facts.float() if device.type == "cpu" else batch.turn_facts
    prefix_facts = batch.prefix_facts.float() if device.type == "cpu" else batch.prefix_facts
    candidate_facts = (
        batch.candidate_facts.float() if device.type == "cpu" else batch.candidate_facts
    )
    opening_residual, opening_turn_mask = opening_residual_inputs(batch)
    with _autocast(device):
        output = cast(
            ActorCriticOutput,
            training_model(
                board,
                units,
                globals_,
                turn_facts,
                batch.turn_fact_mask,
                prefix_facts,
                candidate_facts,
                batch.actions,
                batch.quantities,
                batch.phases,
                batch.turn_mask,
                batch.decision_mask,
                batch.skill_ids,
                batch.economic_state,
                actor_grad=actor_update,
                critic_actor_gradient=settings.critic_actor_gradient,
                validate_inputs=False,
                action_head_noise=opening_residual,
                action_head_noise_turn_mask=opening_turn_mask,
            ),
        )
        loss = ppo_loss(
            output,
            batch.actions,
            batch.quantities,
            batch.legal_mask,
            batch.old_log_probability,
            batch.skill_ids,
            batch.old_skill_log_probability,
            advantages,
            batch.outcomes,
            batch.turn_mask,
            batch.decision_mask,
            has_quantity,
            settings.clip_epsilon,
            settings.value_loss_weight,
            settings.entropy_weight,
            actor_update=actor_update,
            validate_inputs=False,
        )
        loss_scales = context.loss_scales(
            torch.stack(
                (
                    loss.policy_factors.float(),
                    loss.value_factors.float(),
                )
            )
        )
        policy_scale, value_scale = loss_scales.unbind()
        optimized_total = settings.value_loss_weight * loss.value * value_scale
        if actor_update:
            optimized_total = (
                optimized_total
                + loss.policy * policy_scale
                - settings.entropy_weight * loss.entropy * policy_scale
            )
    optimized_total.backward()  # type: ignore[no-untyped-call]
    gradient_norm = torch.nn.utils.clip_grad_norm_(
        model.parameters(), settings.gradient_clip, error_if_nonfinite=True
    )
    optimizer.step()

    with torch.no_grad():
        labels = outcome_labels(batch.outcomes, validate=False)[:, None].expand_as(batch.turn_mask)
        probabilities = torch.softmax(output.outcome_logits.float(), dim=-1)
        predictions = probabilities.argmax(dim=-1)
        valid = batch.turn_mask
        turns = valid.sum()
        safe_turns = turns.clamp_min(1)
        decisions = batch.decision_mask.sum()
        accuracy = ((predictions == labels) & valid).sum() / safe_turns
        targets = functional.one_hot(labels, num_classes=3).float()
        brier_items = (probabilities - targets).square().sum(dim=-1)
        brier = (brier_items * valid).sum() / safe_turns
    return {
        "total_loss": optimized_total.detach(),
        "policy_loss": loss.policy.detach(),
        "value_nll": loss.value.detach(),
        "entropy": loss.entropy.detach(),
        "approximate_kl": loss.approximate_kl.detach(),
        "clip_fraction": loss.clip_fraction.detach(),
        "value_accuracy": accuracy.detach(),
        "value_brier": brier.detach(),
        "gradient_norm": gradient_norm.detach(),
        "turns": turns.detach().float(),
        "decisions": decisions.detach().float(),
        "policy_factors": loss.policy_factors.detach().float(),
    }


def _summarize_optimization(
    rows: list[dict[str, Tensor]], epochs_completed: int
) -> dict[str, float]:
    if not rows:
        raise ValueError("optimization produced no minibatches")
    stacked = {name: torch.stack([row[name] for row in rows]) for name in rows[0]}
    decision_total = stacked["decisions"].sum()
    turn_total = stacked["turns"].sum()
    policy_factor_total = stacked["policy_factors"].sum()

    def weighted(name: str, weight: str, total: Tensor) -> Tensor:
        return (stacked[name] * stacked[weight]).sum() / total.clamp_min(1.0)

    tensors = {
        "total_loss": stacked["total_loss"].mean(),
        "policy_loss": weighted("policy_loss", "policy_factors", policy_factor_total),
        "value_nll": weighted("value_nll", "turns", turn_total),
        "entropy": weighted("entropy", "policy_factors", policy_factor_total),
        "approximate_kl": weighted("approximate_kl", "policy_factors", policy_factor_total),
        "clip_fraction": weighted("clip_fraction", "policy_factors", policy_factor_total),
        "value_accuracy": weighted("value_accuracy", "turns", turn_total),
        "value_brier": weighted("value_brier", "turns", turn_total),
        "maximum_gradient_norm": stacked["gradient_norm"].max(),
        "optimized_turns": turn_total,
        "optimized_decisions": decision_total,
        "optimized_policy_factors": policy_factor_total,
    }
    values = torch.stack(list(tensors.values())).cpu().tolist()
    summary = {name: float(value) for name, value in zip(tensors, values, strict=True)}
    summary.update(
        {
            "epochs_completed": float(epochs_completed),
            "minibatches": float(len(rows)),
        }
    )
    return summary


def _optimize(
    training_model: nn.Module,
    model: OutcomeActorCritic,
    trajectories: list[Trajectory],
    settings: RlSettings,
    device: torch.device,
    has_quantity: Tensor,
    actor_update: bool,
    optimizer: torch.optim.Optimizer,
    randomizer: random.Random,
    context: DistributedContext,
) -> dict[str, float]:
    advantage_mean, advantage_scale, diverse = _advantage_statistics(
        trajectories,
        settings,
        context,
    )
    actor_update = actor_update and diverse
    rows: list[dict[str, Tensor]] = []
    epochs_completed = 0
    local_minibatch = local_value(
        settings.episodes_per_minibatch,
        context.world_size,
        "episodes_per_minibatch",
    )
    pipeline = RolloutBatchPipeline(
        trajectories,
        local_minibatch,
        device,
    )
    next_slot = 0
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="rollout-collation") as collator:
        for _ in range(settings.ppo_epochs):
            indices = list(range(len(trajectories)))
            randomizer.shuffle(indices)
            minibatches = [
                [trajectories[index] for index in indices[start : start + local_minibatch]]
                for start in range(0, len(indices), local_minibatch)
            ]
            epoch_rows: list[dict[str, Tensor]] = []
            slot = next_slot % pipeline.slots
            pipeline.wait_host_reusable(slot)
            pending = collator.submit(
                pipeline.prepare,
                slot,
                minibatches[0],
            )
            next_slot += 1
            for minibatch_index, _ in enumerate(minibatches):
                prepared = pending.result()
                if minibatch_index + 1 < len(minibatches):
                    slot = next_slot % pipeline.slots
                    pipeline.wait_host_reusable(slot)
                    pending = collator.submit(
                        pipeline.prepare,
                        slot,
                        minibatches[minibatch_index + 1],
                    )
                    next_slot += 1
                batch = pipeline.upload(prepared)
                try:
                    row = _optimization_step(
                        training_model,
                        model,
                        batch,
                        settings,
                        device,
                        has_quantity,
                        advantage_mean,
                        advantage_scale,
                        actor_update,
                        optimizer,
                        context,
                    )
                finally:
                    pipeline.finish(prepared)
                rows.append(row)
                epoch_rows.append(row)
            epochs_completed += 1
            local_epoch = _summarize_optimization(epoch_rows, 1)
            epoch_summary = aggregate_optimization_summaries(context.all_gather(local_epoch))
            epoch_kl = epoch_summary["approximate_kl"]
            if actor_update and epoch_kl > settings.target_kl:
                break
    local_summary = _summarize_optimization(rows, epochs_completed)
    summary = aggregate_optimization_summaries(context.all_gather(local_summary))
    summary.update(
        {
            "actor_update": float(actor_update),
            "advantage_mean": advantage_mean,
            "advantage_scale": advantage_scale,
        }
    )
    return summary


def _migration_coverage(trajectories: list[Trajectory]) -> dict[str, object]:
    """Measure exposure of fields and capacities introduced by the migration."""
    legacy_unit_capacity = 16
    legacy_decision_capacity = 26
    inventory_order_start = 48
    inventory_order_stop = 60
    own_slots: np.ndarray[Any, np.dtype[np.int64]] | None = None
    opponent_slots: np.ndarray[Any, np.dtype[np.int64]] | None = None
    decision_positions: np.ndarray[Any, np.dtype[np.int64]] | None = None
    inventory_order: np.ndarray[Any, np.dtype[np.int64]] | None = None
    maximum_own_units = 0
    maximum_opponent_units = 0

    def accumulate(units: np.ndarray[Any, Any], decisions: np.ndarray[Any, Any]) -> None:
        nonlocal own_slots
        nonlocal opponent_slots
        nonlocal decision_positions
        nonlocal inventory_order
        nonlocal maximum_own_units
        nonlocal maximum_opponent_units
        if units.ndim == 3:
            units = units[None]
        if decisions.ndim == 1:
            decisions = decisions[None]
        present = units[..., 0] > 0.5
        if own_slots is None:
            own_slots = np.zeros(units.shape[-2], dtype=np.int64)
            opponent_slots = np.zeros_like(own_slots)
            decision_positions = np.zeros(decisions.shape[-1], dtype=np.int64)
            inventory_order = np.zeros(
                max(0, min(units.shape[-1], inventory_order_stop) - inventory_order_start),
                dtype=np.int64,
            )
        if (
            own_slots.shape[0] != units.shape[-2]
            or decision_positions is None
            or decision_positions.shape[0] != decisions.shape[-1]
        ):
            raise ValueError("rollout migration coverage mixed actor capacities")
        own_slots += present[:, 0].sum(axis=0, dtype=np.int64)
        assert opponent_slots is not None
        opponent_slots += present[:, 1].sum(axis=0, dtype=np.int64)
        decision_positions += decisions.sum(axis=0, dtype=np.int64)
        maximum_own_units = max(
            maximum_own_units,
            int(present[:, 0].sum(axis=-1).max(initial=0)),
        )
        maximum_opponent_units = max(
            maximum_opponent_units,
            int(present[:, 1].sum(axis=-1).max(initial=0)),
        )
        if inventory_order is not None and inventory_order.size:
            inventory_order += np.count_nonzero(
                units[:, 0, :, inventory_order_start:inventory_order_stop],
                axis=(0, 1),
            )

    for trajectory in trajectories:
        if isinstance(trajectory.turns, TrajectoryTurns):
            accumulate(trajectory.turns.units, trajectory.turns.decision_mask)
        else:
            for turn in trajectory.turns:
                accumulate(turn.units, turn.decision_mask)
    if own_slots is None or opponent_slots is None or decision_positions is None:
        return {
            "unit_slot_indices": [],
            "own_unit_slot_turns": [],
            "opponent_unit_slot_turns": [],
            "decision_position_indices": [],
            "decision_position_turns": [],
            "inventory_order_nonzero_by_item": [],
            "maximum_own_units": 0,
            "maximum_opponent_units": 0,
        }
    unit_start = min(legacy_unit_capacity, own_slots.shape[0])
    decision_start = min(legacy_decision_capacity, decision_positions.shape[0])
    return {
        "unit_slot_indices": list(range(unit_start, own_slots.shape[0])),
        "own_unit_slot_turns": own_slots[unit_start:].tolist(),
        "opponent_unit_slot_turns": opponent_slots[unit_start:].tolist(),
        "decision_position_indices": list(range(decision_start, decision_positions.shape[0])),
        "decision_position_turns": decision_positions[decision_start:].tolist(),
        "inventory_order_nonzero_by_item": (
            inventory_order.tolist() if inventory_order is not None else []
        ),
        "maximum_own_units": maximum_own_units,
        "maximum_opponent_units": maximum_opponent_units,
    }


def _rollout_summary(
    trajectories: list[Trajectory],
    matches: tuple[RolloutMatch, ...],
    elapsed_seconds: float,
    settings: RlSettings | None = None,
) -> dict[str, object]:
    outcomes = [match.outcome for match in matches]
    trajectory_outcomes = [trajectory.outcome for trajectory in trajectories]
    terminal_returns = (
        [float(trajectory.outcome) for trajectory in trajectories]
        if settings is None
        else [_trajectory_terminal_return(trajectory, settings) for trajectory in trajectories]
    )
    turns = sum(len(trajectory.turns) for trajectory in trajectories)
    decisions = sum(trajectory_decisions(trajectory) for trajectory in trajectories)
    return {
        "games": len(matches),
        "training_trajectories": len(trajectories),
        "wins": sum(outcome > 0 for outcome in outcomes),
        "ties": sum(outcome == 0 for outcome in outcomes),
        "losses": sum(outcome < 0 for outcome in outcomes),
        "outcome_classes": len(set(outcomes)),
        "training_outcome_classes": len(set(trajectory_outcomes)),
        "training_return_minimum": min(terminal_returns),
        "training_return_maximum": max(terminal_returns),
        "mean_training_return": float(np.mean(terminal_returns)),
        "turns": turns,
        "decisions": decisions,
        "elapsed_seconds": elapsed_seconds,
        "games_per_second": throughput(len(matches), elapsed_seconds),
        "training_trajectories_per_second": throughput(len(trajectories), elapsed_seconds),
        "turns_per_second": throughput(turns, elapsed_seconds),
        "decisions_per_second": throughput(decisions, elapsed_seconds),
        "mean_terminal_cash": float(np.mean([match.terminal_cash for match in matches])),
        "mean_cash_difference": float(
            np.mean([match.terminal_cash - match.opponent_cash for match in matches])
        ),
        "opponents": opponent_outcome_metrics(
            matches,
            [trajectory.opponent_id for trajectory in trajectories],
        ),
        "migration_coverage": _migration_coverage(trajectories),
        **_dense_reward_diagnostics(trajectories, terminal_returns),
    }


def _write_games(path: Path, update: int, matches: tuple[RolloutMatch, ...]) -> None:
    with path.open("a", encoding="utf-8") as stream:
        for match in matches:
            row = {
                "update": update,
                "match_id": match.match_id,
                "opponent_id": match.opponent_id,
                "seed": match.seed,
                "candidate_seat": match.candidate_seat,
                "outcome": match.outcome,
                "terminal_cash": match.terminal_cash,
                "opponent_cash": match.opponent_cash,
                "cash_difference": match.terminal_cash - match.opponent_cash,
            }
            stream.write(json.dumps(row, sort_keys=True) + "\n")


def _export_actor(
    path: Path,
    model: OutcomeActorCritic,
    keys: tuple[str, ...],
    encoder_version: str,
    fact_version: str | None,
) -> dict[str, object]:
    state: dict[str, Tensor] = {}
    for key, value in model.actor.state_dict().items():
        tensor = value.detach().cpu()
        state[key] = tensor.half() if tensor.is_floating_point() else tensor
    payload = {
        "artifact_version": "turn-policy-actor-v6",
        "architecture": model.actor.architecture_json(),
        "actor_encoder_version": encoder_version,
        "derived_fact_version": fact_version,
        "economic_feature_version": model.actor.architecture.economic_feature_version,
        "action_codec_version": CURRENT_ACTIONS.version,
        "action_keys": list(keys),
        "model_state": state,
    }
    temporary = path.with_suffix(".pt.tmp")
    torch.save(payload, temporary)
    temporary.replace(path)
    size = path.stat().st_size
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": size,
        "submission_limit_bytes": SUBMISSION_LIMIT_BYTES,
        "weight_artifact_within_limit": size < SUBMISSION_LIMIT_BYTES,
        "critic_excluded": True,
        "dtype": "float16",
    }


def _train_actor_critic_worker(
    raw_settings: RlSettings,
    repository_root: Path,
    context: DistributedContext,
    *,
    output_prepared: bool,
) -> dict[str, object]:
    """Run one rank of a synchronized rollout/update loop."""
    settings = resolve_rl_paths(raw_settings, repository_root)
    training_source = source_identity(repository_root)
    device = context.device
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA RL training was requested but no GPU is available")
    if device.type == "cpu":
        torch.set_num_threads(settings.cpu_threads)
    rank_seed = (settings.seed + context.rank * 10_000_019) % (2**63 - 1)
    random.seed(rank_seed)
    np.random.seed(rank_seed % (2**32 - 1))
    torch.manual_seed(rank_seed)
    if device.type == "cuda":
        torch.cuda.manual_seed(rank_seed)
    torch.set_float32_matmul_precision("high")

    backend = load_backend(repository_root)
    architecture_source, keys, encoder_version, fact_version = load_actor(
        settings.initial_actor, device
    )
    if settings.actor_initialization == "random":
        # Loading the architecture artifact constructs a temporary model. Reset
        # the generator so its discarded weights cannot shift the declared seed.
        torch.manual_seed(rank_seed)
        if device.type == "cuda":
            torch.cuda.manual_seed(rank_seed)
    actor = initialize_training_actor(
        architecture_source,
        settings.actor_initialization,
        device,
    )
    del architecture_source
    if settings.actor_initialization == "random" and device.type == "cuda":
        torch.cuda.empty_cache()
    model = OutcomeActorCritic(actor).to(device)
    frozen_actor_parameters = [
        name for name, parameter in model.actor.named_parameters() if not parameter.requires_grad
    ]
    if frozen_actor_parameters:
        raise ValueError(f"RL actor contains frozen parameters: {frozen_actor_parameters[0]}")
    has_quantity, resolved_environment = _validate_actor(
        model,
        keys,
        encoder_version,
        fact_version,
        backend,
        settings,
    )
    has_quantity = has_quantity.to(device)
    optimizer = torch.optim.AdamW(
        [
            {"params": model.actor.parameters(), "lr": settings.actor_learning_rate},
            {"params": model.outcome.parameters(), "lr": settings.critic_learning_rate},
        ],
        weight_decay=settings.weight_decay,
        fused=device.type == "cuda",
    )
    initial_actor_sha256 = sha256_file(settings.initial_actor)
    resume_anchor: tuple[str, dict[str, object], dict[str, Tensor]] | None = None
    if settings.resume_checkpoint is not None and settings.pfsp.enabled:
        anchor_identity = actor_fingerprint(model.actor)
        resume_anchor = (
            anchor_identity,
            {
                "kind": "initial_actor",
                "actor_sha256": initial_actor_sha256,
                "actor_state_sha256": anchor_identity,
            },
            {key: value.detach().cpu().clone() for key, value in model.actor.state_dict().items()},
        )
    start_update = 1
    continuation_seed = rank_seed
    randomizer = random.Random(rank_seed)
    pfsp = (
        HistoricalPfsp(
            capacity=settings.pfsp.history_capacity,
            self_play_probability=settings.pfsp.self_play_probability,
            seed=settings.seed + 7_919,
        )
        if settings.pfsp.enabled
        else None
    )
    resume: dict[str, object] | None = None
    if settings.resume_checkpoint is not None:
        resume = restore_checkpoint(
            settings.resume_checkpoint,
            model,
            optimizer,
            settings,
            initial_actor_sha256,
            randomizer,
            pfsp,
            device,
            distributed_rank=context.rank,
            distributed_world_size=context.world_size,
        )
        resume.pop("opening_exploration_state", None)
        start_update = cast(int, resume["start_update"])
        if not bool(resume["rng_state_restored"]):
            previous_update = start_update - 1
            continuation_seed = (rank_seed + previous_update * 1_000_003) % (2**63 - 1)
            resume["continuation_seed"] = continuation_seed
            random.seed(continuation_seed)
            np.random.seed(continuation_seed % (2**32 - 1))
            torch.manual_seed(continuation_seed)
            if device.type == "cuda":
                torch.cuda.manual_seed(continuation_seed)
            randomizer.seed(continuation_seed)
            pfsp = (
                HistoricalPfsp(
                    capacity=settings.pfsp.history_capacity,
                    self_play_probability=settings.pfsp.self_play_probability,
                    seed=continuation_seed + 7_919,
                )
                if settings.pfsp.enabled
                else None
            )
            if pfsp is not None and resume_anchor is not None:
                pfsp.add_state(*resume_anchor)
    frozen_actor_opponents = {
        opponent_id: load_frozen_actor_opponent(
            model,
            opponent.checkpoint,
            opponent.sha256,
        )
        for opponent_id, opponent in settings.frozen_actor_opponents.items()
    }
    training_model: nn.Module = model
    if context.enabled:
        if device.index is None:
            raise ValueError("distributed CUDA device index is absent")
        training_model = DistributedDataParallel(
            model,
            device_ids=[device.index],
            output_device=device.index,
            broadcast_buffers=False,
            find_unused_parameters=True,
            gradient_as_bucket_view=True,
        )
    local_batch_games = local_value(
        settings.rollout_batch_games,
        context.world_size,
        "rollout_batch_games",
    )
    local_cpu_workers = local_value(
        settings.rollout_cpu_workers,
        context.world_size,
        "rollout_cpu_workers",
    )
    local_actor_streams = local_value(
        settings.rollout_actor_streams,
        context.world_size,
        "rollout_actor_streams",
    )
    local_episodes_per_minibatch = local_value(
        settings.episodes_per_minibatch,
        context.world_size,
        "episodes_per_minibatch",
    )
    initial_policy_identity = actor_fingerprint(model.actor)
    collector = RolloutCollector(
        backend,
        model,
        repository_root,
        settings.public_agent_manifest,
        resolved_environment,
        settings.opponents,
        device,
        settings.unit_limit,
        local_batch_games,
        local_cpu_workers,
        local_actor_streams,
        settings.rollout_gpu_policy_session,
        rank_seed,
        settings.rollout_host_memory_limit_gib / context.world_size,
        settings.rollout_gpu_memory_fraction,
        frozen_actor_models={
            opponent_id: opponent.model for opponent_id, opponent in frozen_actor_opponents.items()
        },
        frozen_actor_identities={
            opponent_id: opponent.identity
            for opponent_id, opponent in frozen_actor_opponents.items()
        },
    )

    if context.primary and not output_prepared:
        _prepare_output(settings, repository_root)
    resolved_path = settings.output_dir / "resolved-settings.json"
    if context.primary:
        resolved_path.write_text(
            json.dumps(
                {
                    "rl": settings.model_dump(mode="json"),
                    "resolved_environment": resolved_environment,
                    "source": training_source,
                    "resume": resume,
                    "actor_initialization": {
                        "mode": settings.actor_initialization,
                        "architecture_source_sha256": initial_actor_sha256,
                        "actor_state_sha256": (initial_policy_identity if resume is None else None),
                        "seed": (
                            settings.seed
                            if resume is None and settings.actor_initialization == "random"
                            else None
                        ),
                    },
                    "distributed": {
                        "world_size": context.world_size,
                        "devices": list(settings.training_devices),
                    },
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    games_path = settings.output_dir / "rollout-games.jsonl"
    metrics_path = settings.output_dir / "metrics.jsonl"
    checkpoint_store = (
        CheckpointStore(settings.output_dir, settings.checkpoint) if context.primary else None
    )
    completed_updates = 0
    last_update: dict[str, object] | None = None
    rollout_source: dict[str, object]
    if resume is None:
        rollout_source = {
            "kind": (
                "random_actor_and_seeded_critic"
                if settings.actor_initialization == "random"
                else "initial_actor_and_seeded_critic"
            ),
            "actor_initialization": settings.actor_initialization,
            "actor_sha256": initial_actor_sha256,
            "actor_state_sha256": initial_policy_identity,
            "actor_initialization_seed": (
                settings.seed if settings.actor_initialization == "random" else None
            ),
            "critic_initialization_seed": settings.seed,
        }
    else:
        rollout_source = cast(dict[str, object], resume["checkpoint"]).copy()
    final_checkpoint: dict[str, object] | None = None
    logger = (
        ScalarLogger(
            settings.output_dir,
            settings.observability,
            run_metadata={
                "kind": "terminal_wdl_actor_critic",
                "initial_actor_sha256": initial_actor_sha256,
                "actor_initialization": settings.actor_initialization,
                "devices": list(settings.training_devices),
                "resolved_settings": settings.model_dump(mode="json"),
                "source": training_source,
                "resume": resume,
            },
        )
        if context.primary
        else None
    )
    training_started = time.perf_counter()
    frozen_opponent: OutcomeActorCritic | None = None
    try:
        for update in range(start_update, settings.updates + 1):
            if device.type == "cuda":
                synchronize(device)
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats(device)
            cuda_baseline_allocated = (
                torch.cuda.memory_allocated(device) if device.type == "cuda" else 0
            )
            cuda_baseline_reserved = (
                torch.cuda.memory_reserved(device) if device.type == "cuda" else 0
            )
            update_started = time.perf_counter()
            global_start = settings.rollout_seed_start + (update - 1) * settings.seeds_per_update
            shard = even_shard(
                settings.seeds_per_update,
                context.rank,
                context.world_size,
            )
            seeds = tuple(global_start + index for index in shard)
            global_seeds = tuple(range(global_start, global_start + settings.seeds_per_update))
            opponent_sampling_seed = (settings.seed + update * 2_000_033) % (2**63 - 1)
            rollout_sampling_seed = (
                settings.seed + update * 1_000_003 + context.rank * 10_000_019
            ) % (2**63 - 1)
            synchronize(device)
            rollout_started = time.perf_counter()
            current_policy_identity = context.consistent_text(
                actor_fingerprint(model.actor),
                "rollout actor",
            )
            rollout_source["actor_state_sha256"] = current_policy_identity
            selected_history: HistoricalPolicy | None = None
            historical_opponent: tuple[str, OutcomeActorCritic] | None = None
            if pfsp is not None:
                pfsp.add(current_policy_identity, rollout_source, model.actor)
                selected_history = pfsp.select(current_policy_identity)
                if selected_history is not None:
                    frozen_opponent = _historical_model(
                        model,
                        selected_history,
                        frozen_opponent,
                    )
                    historical_opponent = (
                        f"history:{selected_history.identity}",
                        frozen_opponent,
                    )

            weighted_jobs = (
                weighted_rollout_jobs(
                    global_seeds,
                    settings.opponent_sampling.weights,
                    rank=context.rank,
                    world_size=context.world_size,
                    sampling_seed=opponent_sampling_seed,
                )
                if settings.opponent_sampling is not None
                else None
            )

            def rollout_progress(
                trajectory: Trajectory,
                completed: int,
                total: int,
                current_update: int = update,
                started_at: float = rollout_started,
            ) -> None:
                if not context.primary:
                    return
                if completed != total and completed % local_batch_games != 0:
                    return
                print(
                    json.dumps(
                        {
                            "event": "rollout_game_completed",
                            "rank": context.rank,
                            "update": current_update,
                            "completed": completed,
                            "total": total,
                            "opponent_id": trajectory.opponent_id,
                            "seed": trajectory.seed,
                            "seat": trajectory.seat,
                            "outcome": trajectory.outcome,
                            "turns": len(trajectory.turns),
                            "elapsed_seconds": time.perf_counter() - started_at,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )

            opening_plan: OpeningNoisePlan | None = None
            opening_exploration_report: dict[str, object]
            if settings.opening_exploration.enabled:
                planned_jobs = tuple(
                    weighted_jobs
                    if weighted_jobs is not None
                    else rollout_jobs(seeds, settings.opponents)
                )
                probe_seeds = tuple(dict.fromkeys(job[0] for job in planned_jobs))[
                    : settings.opening_exploration.probe_seeds
                ]
                planning_started = time.perf_counter()
                probe = probe_official_openings(
                    model,
                    backend,
                    resolved_environment,
                    settings.unit_limit,
                    probe_seeds,
                    device,
                )
                opening_plan = build_opening_noise_plan(
                    probe,
                    planned_jobs,
                    noisy_fraction=settings.opening_exploration.noisy_fraction,
                    selection_seed=(settings.seed + update * 3_000_049 + context.rank * 10_000_019)
                    % (2**63 - 1),
                    direction_seed=(settings.seed + update * 4_000_037 + context.rank * 20_000_033)
                    % (2**63 - 1),
                    prefix_turns=settings.opening_exploration.prefix_turns,
                    target_escape=settings.opening_exploration.escape_target,
                    maximum_scale=settings.opening_exploration.maximum_scale,
                    bisection_steps=settings.opening_exploration.calibration_steps,
                )
                local_opening_report = {
                    "rank": context.rank,
                    **opening_plan.report(),
                    "planning_elapsed_seconds": time.perf_counter() - planning_started,
                }
                worker_opening_reports = context.all_gather(local_opening_report)
                total_perspectives = sum(
                    cast(int, report["total_perspectives"]) for report in worker_opening_reports
                )
                noisy_perspectives = sum(
                    cast(int, report["noisy_perspectives"]) for report in worker_opening_reports
                )
                opening_exploration_report = {
                    "status": (
                        "active" if noisy_perspectives else worker_opening_reports[0]["status"]
                    ),
                    "training_path": "on_policy_ppo",
                    "episode_locked": True,
                    "prefix_turns": settings.opening_exploration.prefix_turns,
                    "total_perspectives": total_perspectives,
                    "noisy_perspectives": noisy_perspectives,
                    "noisy_fraction": noisy_perspectives / total_perspectives,
                    "planning_elapsed_seconds": max(
                        cast(float, report["planning_elapsed_seconds"])
                        for report in worker_opening_reports
                    ),
                    "workers": worker_opening_reports,
                }
                trajectories = collector.collect_jobs(
                    planned_jobs,
                    rollout_progress,
                    sampling_seed=rollout_sampling_seed,
                    opening_plan=opening_plan,
                    force_opening_buffer=True,
                )
            elif settings.opponent_sampling is None:
                opening_exploration_report = {"status": "disabled"}
                trajectories = collector.collect(
                    seeds,
                    rollout_progress,
                    historical_opponent=historical_opponent,
                    sampling_seed=rollout_sampling_seed,
                )
            else:
                opening_exploration_report = {"status": "disabled"}
                if weighted_jobs is None:
                    raise RuntimeError("weighted rollout jobs disappeared")
                trajectories = collector.collect_jobs(
                    weighted_jobs,
                    rollout_progress,
                    sampling_seed=rollout_sampling_seed,
                )
            matches = collector.last_matches
            if pfsp is not None and selected_history is not None:
                pfsp.record(selected_history, trajectories)
            population_metrics: dict[str, float] = {}
            if pfsp is not None:
                population_metrics = {
                    "history_selected": float(selected_history is not None),
                    "history_pool_size": float(pfsp.size),
                }
                if selected_history is not None:
                    population_metrics.update(
                        {
                            "selected_games": float(selected_history.games),
                            "selected_win_probability": selected_history.win_probability,
                            "selected_priority": selected_history.priority,
                        }
                    )
            historical_opponent = None
            behavior_elapsed = 0.0
            if not settings.rollout_gpu_policy_session:
                behavior_started = time.perf_counter()
                trajectories = freeze_behavior_statistics(
                    model,
                    trajectories,
                    device,
                    has_quantity,
                    local_episodes_per_minibatch,
                )
                synchronize(device)
                behavior_elapsed = time.perf_counter() - behavior_started
            rollout_elapsed = time.perf_counter() - rollout_started
            local_rollout = _rollout_summary(
                trajectories,
                matches,
                rollout_elapsed,
                settings,
            )
            pipeline = collector.last_performance
            actor_seconds = _as_float(pipeline.get("actor_seconds", 0.0), "rollout actor time")
            environment_seconds = _as_float(
                pipeline.get("environment_seconds", 0.0),
                "rollout environment time",
            )
            local_rollout.update(
                {
                    "actor_elapsed_seconds": actor_seconds,
                    "environment_elapsed_seconds": environment_seconds,
                    "behavior_evaluation_seconds": behavior_elapsed,
                    "pipeline_unattributed_seconds": max(
                        0.0,
                        rollout_elapsed - actor_seconds - environment_seconds - behavior_elapsed,
                    ),
                    "pipeline": pipeline,
                    "capacity": collector.capacity,
                }
            )
            rollout_payload = {
                "rank": context.rank,
                "device": str(device),
                "summary": local_rollout,
                "matches": matches,
                "trajectory_outcomes": tuple(
                    sorted({trajectory.outcome for trajectory in trajectories})
                ),
                "trajectory_opponents": tuple(
                    trajectory.opponent_id for trajectory in trajectories
                ),
            }
            if context.enabled:
                rollout, matches = aggregate_rollout_shards(context.all_gather(rollout_payload))
            else:
                rollout = local_rollout
            actor_requested = update > settings.critic_warmup_updates
            synchronize(device)
            optimization_started = time.perf_counter()
            optimization = _optimize(
                training_model,
                model,
                trajectories,
                settings,
                device,
                has_quantity,
                actor_requested,
                optimizer,
                randomizer,
                context,
            )
            synchronize(device)
            local_optimization_elapsed = time.perf_counter() - optimization_started
            optimization_elapsed = context.maximum(local_optimization_elapsed)
            optimizer.zero_grad(set_to_none=True)
            trajectories.clear()
            if device.type == "cuda":
                torch.cuda.empty_cache()
            optimization.update(
                {
                    "elapsed_seconds": optimization_elapsed,
                    "turns_per_second": throughput(
                        optimization["optimized_turns"], optimization_elapsed
                    ),
                    "decisions_per_second": throughput(
                        optimization["optimized_decisions"], optimization_elapsed
                    ),
                }
            )
            actor_updated = bool(optimization["actor_update"])
            local_system: dict[str, object] = {
                "rank": context.rank,
                "device": str(device),
                "update_elapsed_seconds": time.perf_counter() - update_started,
                "cuda_peak_allocated_bytes": (
                    torch.cuda.max_memory_allocated(device) if device.type == "cuda" else 0
                ),
                "cuda_peak_reserved_bytes": (
                    torch.cuda.max_memory_reserved(device) if device.type == "cuda" else 0
                ),
                "cuda_baseline_allocated_bytes": cuda_baseline_allocated,
                "cuda_baseline_reserved_bytes": cuda_baseline_reserved,
                "cuda_current_allocated_bytes": (
                    torch.cuda.memory_allocated(device) if device.type == "cuda" else 0
                ),
                "cuda_current_reserved_bytes": (
                    torch.cuda.memory_reserved(device) if device.type == "cuda" else 0
                ),
                "rollout_cpu_workers": local_cpu_workers,
                "rollout_batch_games": local_batch_games,
                "rollout_actor_streams": local_actor_streams,
                "rollout_gpu_policy_session": settings.rollout_gpu_policy_session,
                "rollout_sampling_seed": rollout_sampling_seed,
                "opponent_sampling_seed": opponent_sampling_seed,
                "cpu_affinity": list(context.cpu_affinity),
            }
            worker_systems = context.all_gather(local_system)
            system = {
                "distributed_world_size": context.world_size,
                "devices": list(settings.training_devices),
                "update_elapsed_seconds": max(
                    _as_float(value["update_elapsed_seconds"], "update elapsed")
                    for value in worker_systems
                ),
                "cuda_peak_allocated_bytes": sum(
                    _as_int(value["cuda_peak_allocated_bytes"], "CUDA peak allocated")
                    for value in worker_systems
                ),
                "cuda_peak_reserved_bytes": sum(
                    _as_int(value["cuda_peak_reserved_bytes"], "CUDA peak reserved")
                    for value in worker_systems
                ),
                "cuda_baseline_allocated_bytes": sum(
                    _as_int(value["cuda_baseline_allocated_bytes"], "CUDA baseline allocated")
                    for value in worker_systems
                ),
                "cuda_baseline_reserved_bytes": sum(
                    _as_int(value["cuda_baseline_reserved_bytes"], "CUDA baseline reserved")
                    for value in worker_systems
                ),
                "cuda_current_allocated_bytes": sum(
                    _as_int(value["cuda_current_allocated_bytes"], "CUDA current allocated")
                    for value in worker_systems
                ),
                "cuda_current_reserved_bytes": sum(
                    _as_int(value["cuda_current_reserved_bytes"], "CUDA current reserved")
                    for value in worker_systems
                ),
                "rollout_cpu_workers": settings.rollout_cpu_workers,
                "rollout_batch_games": settings.rollout_batch_games,
                "rollout_actor_streams": settings.rollout_actor_streams,
                "rollout_gpu_policy_session": settings.rollout_gpu_policy_session,
                "rollout_sampling_seeds": [
                    value["rollout_sampling_seed"] for value in worker_systems
                ],
                "opponent_sampling_seed": opponent_sampling_seed,
                "workers": worker_systems,
            }
            row: dict[str, object] = {
                "update": update,
                "seeds": list(global_seeds),
                "rollout": rollout,
                "optimization": optimization,
                "system": system,
                "actor_update_requested": actor_requested,
                "actor_update_applied": actor_updated,
                "rollout_model_source": rollout_source,
                "training_opponent": (
                    {
                        "kind": "weighted_per_seed",
                        "weights": dict(settings.opponent_sampling.weights),
                        "self_play_identity": current_policy_identity,
                    }
                    if settings.opponent_sampling is not None
                    else (
                        {"kind": "self_play", "identity": current_policy_identity}
                        if selected_history is None
                        else {
                            "kind": "historical_actor",
                            "identity": selected_history.identity,
                            "source": selected_history.source,
                        }
                    )
                ),
                "opening_exploration": opening_exploration_report,
                "pfsp": pfsp.report() if pfsp is not None else None,
                "actor_update_skip_reason": (
                    None
                    if actor_updated
                    else (
                        "critic_warmup"
                        if not actor_requested
                        else "rollout_panel_has_insufficient_terminal_return_diversity"
                    )
                ),
            }
            checkpoint: dict[str, object] | None = None
            final_update = update == settings.updates
            checkpoint_due = context.broadcast(
                checkpoint_store.due(update, final=final_update)
                if checkpoint_store is not None
                else None
            )
            if checkpoint_due:
                serialized_states = context.all_gather(
                    serialize_training_state(
                        capture_training_state(
                            randomizer,
                            pfsp,
                            device,
                        )
                    )
                )
                training_states = [deserialize_training_state(state) for state in serialized_states]
                if context.primary:
                    if checkpoint_store is None:
                        raise RuntimeError("primary rank lacks its checkpoint store")
                    checkpoint = checkpoint_store.publish(
                        update,
                        build_checkpoint_payload(
                            model,
                            optimizer,
                            update,
                            settings,
                            initial_actor_sha256,
                            randomizer,
                            pfsp,
                            device,
                            distributed_training_states=training_states,
                        ),
                        final=final_update,
                    )
                    if checkpoint is None:
                        raise RuntimeError("due RL checkpoint was not published")
                checkpoint = context.broadcast(checkpoint)
                final_checkpoint = checkpoint
            row["checkpoint"] = checkpoint
            completed_updates += 1
            last_update = row
            if context.primary:
                if logger is None:
                    raise RuntimeError("primary rank lacks its scalar logger")
                _write_games(games_path, update, matches)
                with metrics_path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(row, sort_keys=True) + "\n")
                logger.scalars("rl/rollout", rollout, update)
                logger.scalars("rl/optimization", optimization, update)
                logger.scalars("rl/system", system, update)
                if population_metrics:
                    logger.scalars("rl/pfsp", population_metrics, update)
                print(json.dumps(row, sort_keys=True), flush=True)
            next_policy_identity = context.consistent_text(
                actor_fingerprint(model.actor),
                "optimized actor",
            )
            rollout_source = {
                "kind": "actor_critic_update",
                "update": update,
                "actor_state_sha256": next_policy_identity,
            }
            if checkpoint is not None:
                rollout_source["checkpoint"] = checkpoint
            context.barrier()
    finally:
        try:
            collector.close()
        finally:
            if logger is not None:
                logger.close()

    if final_checkpoint is None or last_update is None:
        raise RuntimeError("RL training completed without a checkpoint")
    training_elapsed = context.maximum(time.perf_counter() - training_started)
    gpu_names = context.all_gather(
        torch.cuda.get_device_name(device) if device.type == "cuda" else None
    )
    if not context.primary:
        return {}
    if logger is None:
        raise RuntimeError("primary rank lacks its scalar logger")
    actor_artifact = _export_actor(
        settings.output_dir / "actor-fp16.pt",
        model,
        keys,
        encoder_version,
        fact_version,
    )
    report: dict[str, object] = {
        "schema_version": "terminal-reward-actor-critic-v6",
        "generated_at": datetime.now(UTC).isoformat(),
        "purpose": "complete-match terminal-reward challenger; no promotion authority",
        "source": training_source,
        "architecture": model.actor.architecture_json(),
        "objective": {
            "reward": settings.terminal_reward.model_dump(mode="json"),
            "critic_target": "terminal seat-relative W/D/L classification",
            "actor_baseline": "expected W/D/L from the frozen behavior critic",
            "discount": settings.discount,
            "gae_lambda": settings.gae_lambda,
            "critic_actor_gradient": settings.critic_actor_gradient,
            "causal_latent_policy_factor": model.actor.skills is not None,
            "latent_auxiliary_losses": False,
            "actor_update_gate": "nonconstant configured terminal return",
            "trajectory_replay": False,
        },
        "execution": {
            "device": str(device),
            "devices": list(settings.training_devices),
            "gpu": gpu_names[0],
            "gpus": gpu_names,
            "distributed_world_size": context.world_size,
            "distributed_data_parallel": context.enabled,
            "gradient_synchronization": "nccl_ddp" if context.enabled else None,
            "global_episodes_per_minibatch": settings.episodes_per_minibatch,
            "episodes_per_minibatch_per_rank": local_episodes_per_minibatch,
            "rollout_timeout_enforced": False,
            "promotion_authority": False,
            "elapsed_seconds": training_elapsed,
        },
        "observability": observability_report(logger),
        "backend": backend.identity,
        "initial_actor": {
            "path": str(settings.initial_actor),
            "sha256": initial_actor_sha256,
            "initialization": settings.actor_initialization,
            "architecture_source_only": settings.actor_initialization == "random",
            "initial_actor_state_sha256": (initial_policy_identity if resume is None else None),
        },
        "resume": resume,
        "opponents": collector.opponent_identities,
        "training_population": pfsp.report() if pfsp is not None else None,
        "resolved_settings": {
            "rl": settings.model_dump(mode="json"),
            "resolved_environment": resolved_environment,
        },
        "updates": {
            "start_update": start_update,
            "completed": completed_updates,
            "target": settings.updates,
            "last": last_update,
            "metrics": {
                "path": str(metrics_path),
                "sha256": sha256_file(metrics_path),
            },
        },
        "checkpoint": final_checkpoint,
        "rollout_games": {
            "path": str(games_path),
            "sha256": sha256_file(games_path),
            "contents": "outcome summaries only; no observation or action tensors",
        },
        "actor_artifact": actor_artifact,
    }
    (settings.output_dir / "training-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report


def _distributed_worker_entry(
    rank: int,
    settings_payload: dict[str, object],
    repository_root_value: str,
    rendezvous_value: str,
) -> None:
    """Spawn entry point for one NCCL rank."""
    settings = RlSettings.model_validate(settings_payload)
    context = initialize_context(
        rank,
        settings.training_devices,
        Path(rendezvous_value),
    )
    try:
        _train_actor_critic_worker(
            settings,
            Path(repository_root_value),
            context,
            output_prepared=True,
        )
    finally:
        destroy_context(context)


def train_actor_critic(raw_settings: RlSettings, repository_root: Path) -> dict[str, object]:
    """Run one single-GPU or synchronized multi-GPU actor-critic lineage."""
    settings = resolve_rl_paths(raw_settings, repository_root)
    devices = settings.training_devices
    if len(devices) == 1:
        device = torch.device(devices[0])
        return _train_actor_critic_worker(
            settings,
            repository_root,
            single_process_context(device),
            output_prepared=False,
        )
    if not torch.cuda.is_available():
        raise RuntimeError("distributed CUDA RL training requested without CUDA")
    available = torch.cuda.device_count()
    for value in devices:
        device = torch.device(value)
        if device.index is None or device.index >= available:
            raise RuntimeError(f"distributed RL device is unavailable: {value}")
    _prepare_output(settings, repository_root)
    rendezvous = settings.output_dir / ".ddp-rendezvous"
    try:
        torch_multiprocessing.spawn(  # type: ignore[attr-defined, no-untyped-call]
            _distributed_worker_entry,
            args=(
                settings.model_dump(mode="python"),
                str(repository_root),
                str(rendezvous),
            ),
            nprocs=len(devices),
            join=True,
        )
    finally:
        rendezvous.unlink(missing_ok=True)
    report_path = settings.output_dir / "training-report.json"
    value = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("distributed RL training report is not a mapping")
    return cast(dict[str, object], value)


__all__ = ["resolve_rl_paths", "train_actor_critic"]
