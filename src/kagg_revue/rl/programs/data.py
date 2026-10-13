"""Compact complete-match records for conditional-program PPO."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.programs.grammar import (
    ProgramActionSequence,
    ProgramMaskSequence,
    ProgramSequenceInputs,
)
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.runtime import ProgramTurnTrace, trace_sequence


@dataclass(frozen=True)
class ProgramEpisode:
    """One complete official-rule perspective and exact behavior surface."""

    episode_id: str
    opponent_id: str
    seed: int
    seat: int
    outcome: int
    terminal_cash: float
    opponent_cash: float
    board: NDArray[np.float16] | Tensor
    units: NDArray[np.float16] | Tensor
    global_features: NDArray[np.float32] | Tensor
    economic_state: NDArray[np.int32] | Tensor
    actions: NDArray[np.int64] | Tensor
    quantities: NDArray[np.int64] | Tensor
    action_decision_counts: NDArray[np.int16] | Tensor
    program_scalars: NDArray[np.int16] | Tensor
    program_root_features: NDArray[np.float32] | Tensor
    program_option_features: NDArray[np.int32] | Tensor
    program_target_reservations: NDArray[np.int16] | Tensor
    program_actions: NDArray[np.int64] | Tensor
    program_conditional_masks: NDArray[np.bool_] | Tensor
    program_quantity_max: NDArray[np.int64] | Tensor
    program_decision_counts: NDArray[np.int16] | Tensor
    old_joint_log_probability: NDArray[np.float32] | Tensor
    old_values: NDArray[np.float32] | Tensor
    stochastic_factor_counts: NDArray[np.int16] | Tensor
    program_decision_max: int | None = None
    source_group: str | None = None

    def __post_init__(self) -> None:
        """Validate field-major alignment without freezing experiment values."""
        turns = self.board.shape[0]
        if turns < 1 or self.outcome not in {-1, 0, 1} or self.seat not in {0, 1}:
            raise ValueError("conditional-program episode identity is invalid")
        if self.actions.ndim != 2 or self.program_actions.ndim != 3:
            raise ValueError("conditional-program episode action tensors are malformed")
        fields = (
            self.units,
            self.global_features,
            self.economic_state,
            self.actions,
            self.quantities,
            self.action_decision_counts,
            self.program_scalars,
            self.program_root_features,
            self.program_option_features,
            self.program_target_reservations,
            self.program_actions,
            self.program_conditional_masks,
            self.program_quantity_max,
            self.program_decision_counts,
            self.old_joint_log_probability,
            self.old_values,
            self.stochastic_factor_counts,
        )
        tensor_backed = isinstance(self.board, Tensor)
        if any(isinstance(value, Tensor) != tensor_backed for value in fields):
            raise ValueError("conditional-program episode mixed host and CUDA fields")
        if any(value.shape[0] != turns for value in fields):
            raise ValueError("conditional-program episode fields have different turns")
        official_width = self.actions.shape[1]
        program_width = self.program_actions.shape[1]
        if (
            self.quantities.shape != (turns, official_width)
            or self.action_decision_counts.shape != (turns,)
            or self.program_scalars.shape[:2] != (turns, program_width)
            or self.program_actions.shape != (turns, program_width, 9)
            or self.program_conditional_masks.shape[:2]
            != (turns, program_width)
            or self.program_quantity_max.shape != (turns, program_width)
            or self.program_decision_counts.shape != (turns,)
            or self.old_joint_log_probability.shape != (turns,)
            or self.old_values.shape != (turns,)
            or self.stochastic_factor_counts.shape != (turns,)
        ):
            raise ValueError("conditional-program episode tensor ABI is inconsistent")
        decision_max = self.program_decision_max
        if tensor_backed:
            if decision_max is None:
                raise ValueError("CUDA program episode needs its host decision maximum")
        else:
            assert isinstance(self.action_decision_counts, np.ndarray)
            assert isinstance(self.program_decision_counts, np.ndarray)
            if np.any(
                (self.action_decision_counts < 1)
                | (self.action_decision_counts > official_width)
                | (self.program_decision_counts < 1)
                | (self.program_decision_counts > program_width)
            ):
                raise ValueError("conditional-program episode counts are outside buffers")
            decision_max = int(self.program_decision_counts.max(initial=0))
            object.__setattr__(self, "program_decision_max", decision_max)
        if decision_max is None or not 1 <= decision_max <= program_width:
            raise ValueError("conditional-program episode decision maximum is invalid")
        if not np.isfinite(self.terminal_cash) or not np.isfinite(self.opponent_cash):
            raise ValueError("conditional-program episode contains non-finite values")
        if not tensor_backed and not (
            np.isfinite(self.board).all()
            and np.isfinite(self.units).all()
            and np.isfinite(self.global_features).all()
            and np.isfinite(self.program_root_features).all()
            and np.isfinite(self.old_joint_log_probability).all()
            and np.isfinite(self.old_values).all()
        ):
            raise ValueError("conditional-program episode contains non-finite values")

    @property
    def turn_count(self) -> int:
        """Return the number of official transitions."""
        return int(self.board.shape[0])


@dataclass(frozen=True)
class ProgramBatch:
    """Device tensors for complete episodes and every valid turn program."""

    board: Tensor
    units: Tensor
    global_features: Tensor
    economic_state: Tensor
    actions: Tensor
    quantities: Tensor
    turn_mask: Tensor
    decision_mask: Tensor
    program_inputs: ProgramSequenceInputs
    program_actions: ProgramActionSequence
    program_masks: ProgramMaskSequence
    program_episode_index: Tensor
    program_turn_index: Tensor
    old_joint_log_probability: Tensor
    old_values: Tensor
    stochastic_factor_counts: Tensor
    outcomes: Tensor


def collate_program_episodes(
    episodes: list[ProgramEpisode] | tuple[ProgramEpisode, ...],
    contract: NativeProgramContract,
    context_width: int,
    device: torch.device,
    *,
    validate: bool = False,
) -> ProgramBatch:
    """Collate complete episodes without materializing per-turn Python rows."""
    if not episodes:
        raise ValueError("conditional-program batch needs complete episodes")
    turns = episodes[0].turn_count
    if any(episode.turn_count != turns for episode in episodes):
        raise ValueError("conditional-program batch episodes have different lengths")
    count = len(episodes)

    tensor_backed = isinstance(episodes[0].board, Tensor)
    if any(isinstance(episode.board, Tensor) != tensor_backed for episode in episodes):
        raise ValueError("conditional-program minibatch mixed host and CUDA episodes")

    def stack(
        name: str,
        *,
        dtype: torch.dtype | None = None,
        program_capacity: int | None = None,
    ) -> Tensor:
        values = [getattr(episode, name) for episode in episodes]
        if program_capacity is not None:
            values = [value[:, :program_capacity] for value in values]
        if tensor_backed:
            return torch.stack(
                [value.to(device=device, dtype=dtype, non_blocking=True) for value in values]
            )
        return torch.as_tensor(
            np.stack(values), dtype=dtype, device=device
        )

    board = stack("board")
    units = stack("units")
    global_features = stack("global_features", dtype=torch.float32)
    economic_state = stack("economic_state", dtype=torch.int32)
    actions = stack("actions", dtype=torch.long)
    quantities = stack("quantities", dtype=torch.long)
    action_counts = stack("action_decision_counts", dtype=torch.long)
    turn_mask = torch.ones((count, turns), dtype=torch.bool, device=device)
    decision_mask = (
        torch.arange(actions.shape[2], device=device)[None, None]
        < action_counts[:, :, None]
    )
    program_capacity = max(
        episode.program_decision_max or 0 for episode in episodes
    )
    flat_turns = count * turns
    trace = ProgramTurnTrace(
        scalars=stack(
            "program_scalars", dtype=torch.int16, program_capacity=program_capacity
        ).reshape(
            flat_turns, program_capacity, 7
        ),
        root_features=stack(
            "program_root_features",
            dtype=torch.float32,
            program_capacity=program_capacity,
        ).reshape(
            flat_turns, program_capacity, contract.root_feature_count
        ),
        option_features=stack(
            "program_option_features",
            dtype=torch.int32,
            program_capacity=program_capacity,
        ).reshape(
            flat_turns, program_capacity, contract.option_feature_count
        ),
        target_reservations=stack(
            "program_target_reservations",
            dtype=torch.int16,
            program_capacity=program_capacity,
        ).reshape(
            flat_turns, program_capacity, contract.tile_count
        ),
        actions=stack(
            "program_actions", dtype=torch.long, program_capacity=program_capacity
        ).reshape(
            flat_turns, program_capacity, 9
        ),
        conditional_masks=stack(
            "program_conditional_masks",
            dtype=torch.bool,
            program_capacity=program_capacity,
        ).reshape(
            flat_turns,
            program_capacity,
            episodes[0].program_conditional_masks.shape[2],
        ),
        quantity_max=stack(
            "program_quantity_max",
            dtype=torch.long,
            program_capacity=program_capacity,
        ).reshape(
            flat_turns, program_capacity
        ),
        decision_counts=stack("program_decision_counts", dtype=torch.int16).reshape(
            flat_turns
        ),
        old_joint_log_probability=stack(
            "old_joint_log_probability", dtype=torch.float32
        ).reshape(flat_turns),
        old_values=stack("old_values", dtype=torch.float32).reshape(flat_turns),
        stochastic_factor_counts=stack(
            "stochastic_factor_counts", dtype=torch.int16
        ).reshape(flat_turns),
    )
    placeholder_context = torch.zeros(
        (flat_turns, context_width), dtype=torch.float32, device=device
    )
    placeholder_tiles = torch.zeros(
        (flat_turns, contract.tile_count, context_width),
        dtype=torch.float32,
        device=device,
    )
    program_inputs, program_actions, program_masks = trace_sequence(
        trace,
        placeholder_context,
        placeholder_tiles,
        contract,
        device=device,
        validate=validate,
    )
    episode_index = torch.arange(count, device=device).repeat_interleave(turns)
    turn_index = torch.arange(turns, device=device).repeat(count)
    return ProgramBatch(
        board=board,
        units=units,
        global_features=global_features,
        economic_state=economic_state,
        actions=actions,
        quantities=quantities,
        turn_mask=turn_mask,
        decision_mask=decision_mask,
        program_inputs=program_inputs,
        program_actions=program_actions,
        program_masks=program_masks,
        program_episode_index=episode_index,
        program_turn_index=turn_index,
        old_joint_log_probability=torch.as_tensor(
            trace.old_joint_log_probability,
            dtype=torch.float32,
            device=device,
        ),
        old_values=torch.as_tensor(
            trace.old_values, dtype=torch.float32, device=device
        ),
        stochastic_factor_counts=torch.as_tensor(
            trace.stochastic_factor_counts, dtype=torch.long, device=device
        ),
        outcomes=torch.tensor(
            [episode.outcome for episode in episodes],
            dtype=torch.int8,
            device=device,
        ),
    )


__all__ = ["ProgramBatch", "ProgramEpisode", "collate_program_episodes"]
