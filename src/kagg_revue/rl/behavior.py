"""Bulk evaluation of frozen RL behavior after environment generation."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import replace
from typing import Any

import numpy as np
import torch
from torch import Tensor

from kagg_revue.rl.data import (
    Trajectory,
    TrajectoryTurns,
    collate_trajectories,
    opening_residual_inputs,
)
from kagg_revue.rl.outcome import (
    OutcomeActorCritic,
    outcome_values,
    selected_log_probability,
    selected_skill_log_probability,
)


def _autocast(device: torch.device) -> Any:
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.bfloat16)
    return nullcontext()


def freeze_behavior_statistics(
    model: OutcomeActorCritic,
    trajectories: list[Trajectory],
    device: torch.device,
    has_quantity: Tensor,
    episodes_per_batch: int,
) -> list[Trajectory]:
    """Attach behavior log probabilities and values in large GPU batches.

    The actor remains frozen between rollout generation and this pass. Deferring
    these quantities removes critic, log-softmax, quantity-density, and their
    device-to-host synchronizations from every autoregressive decision.
    """
    if episodes_per_batch < 1:
        raise ValueError("behavior evaluation batch size must be positive")
    model.eval()
    frozen: list[Trajectory] = []
    for start in range(0, len(trajectories), episodes_per_batch):
        selected = trajectories[start : start + episodes_per_batch]
        batch = collate_trajectories(selected, device)
        board = batch.board.float() if device.type == "cpu" else batch.board
        units = batch.units.float() if device.type == "cpu" else batch.units
        globals_ = batch.global_features.float() if device.type == "cpu" else batch.global_features
        turn_facts = batch.turn_facts.float() if device.type == "cpu" else batch.turn_facts
        prefix_facts = batch.prefix_facts.float() if device.type == "cpu" else batch.prefix_facts
        candidate_facts = (
            batch.candidate_facts.float() if device.type == "cpu" else batch.candidate_facts
        )
        opening_residual, opening_turn_mask = opening_residual_inputs(batch)
        with torch.inference_mode(), _autocast(device):
            output = model(
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
                actor_grad=False,
                action_head_noise=opening_residual,
                action_head_noise_turn_mask=opening_turn_mask,
            )
            log_probability = selected_log_probability(
                output.policy,
                batch.actions,
                batch.quantities,
                batch.legal_mask,
                batch.decision_mask,
                has_quantity,
            )
            values = outcome_values(output.outcome_logits)
            skill_log_probability = selected_skill_log_probability(
                output.policy,
                batch.skill_ids,
                batch.turn_mask,
            )
        valid = batch.decision_mask & batch.turn_mask[..., None]
        if not bool(torch.isfinite(log_probability[valid]).all().item()):
            raise FloatingPointError("behavior policy log probability is not finite")
        if not bool(torch.isfinite(skill_log_probability[batch.turn_mask]).all().item()):
            raise FloatingPointError("behavior latent selector log probability is not finite")
        log_values = log_probability.float().cpu().numpy()
        old_values = values.float().cpu().numpy()
        old_skill_values = skill_log_probability.float().cpu().numpy()
        for row, trajectory in enumerate(selected):
            if isinstance(trajectory.turns, TrajectoryTurns):
                turns = trajectory.turns
                length = len(turns)
                frozen.append(
                    replace(
                        trajectory,
                        turns=turns.with_behavior(
                            np.asarray(
                                log_values[
                                    row,
                                    :length,
                                    : turns.actions.shape[1],
                                ],
                                dtype=np.float32,
                            ),
                            np.asarray(
                                old_skill_values[row, :length],
                                dtype=np.float32,
                            ),
                            np.asarray(
                                old_values[row, :length],
                                dtype=np.float32,
                            ),
                        ),
                    )
                )
                continue
            legacy_turns = []
            for column, turn in enumerate(trajectory.turns):
                count = turn.actions.shape[0]
                legacy_turns.append(
                    replace(
                        turn,
                        old_log_probability=np.asarray(
                            log_values[row, column, :count], dtype=np.float32
                        ).copy(),
                        old_skill_log_probability=float(old_skill_values[row, column]),
                        old_value=float(old_values[row, column]),
                    )
                )
            frozen.append(replace(trajectory, turns=tuple(legacy_turns)))
    return frozen


__all__ = ["freeze_behavior_statistics"]
