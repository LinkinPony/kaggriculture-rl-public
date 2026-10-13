"""Preallocated field-major host storage for conditional-program rollout."""

from __future__ import annotations

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.runtime import ProgramTurnRollout
from kagg_revue.rl.programs.data import ProgramEpisode


class ProgramGroupStorage:
    """Own every compact turn field for one lockstep engine batch."""

    def __init__(
        self,
        batch: int,
        turns: int,
        board: NDArray[np.float16],
        units: NDArray[np.float16],
        global_features: NDArray[np.float32],
        economic_state: NDArray[np.int32],
        contract: NativeProgramContract,
        mask_width: int,
        action_width: int,
    ) -> None:
        """Allocate the bounded arrays once before recording official turns."""
        capacity = contract.maximum_decisions
        self.length = 0
        self.board = np.empty((batch, turns, *board.shape[1:]), dtype=np.float16)
        self.units = np.empty((batch, turns, *units.shape[1:]), dtype=np.float16)
        self.global_features = np.empty(
            (batch, turns, global_features.shape[1]), dtype=np.float32
        )
        self.economic_state = np.empty(
            (batch, turns, economic_state.shape[1]), dtype=np.int32
        )
        if action_width < capacity:
            raise ValueError("actor history is narrower than native program actions")
        self.actions = np.zeros((batch, turns, action_width), dtype=np.int64)
        self.quantities = np.empty_like(self.actions)
        self.action_decision_counts = np.empty((batch, turns), dtype=np.int16)
        self.program_scalars = np.empty(
            (batch, turns, capacity, 7), dtype=np.int16
        )
        self.program_root_features = np.empty(
            (batch, turns, capacity, contract.root_feature_count), dtype=np.float32
        )
        self.program_option_features = np.empty(
            (batch, turns, capacity, contract.option_feature_count), dtype=np.int32
        )
        self.program_target_reservations = np.empty(
            (batch, turns, capacity, contract.tile_count), dtype=np.int16
        )
        self.program_actions = np.empty(
            (batch, turns, capacity, 9), dtype=np.int64
        )
        self.program_conditional_masks = np.empty(
            (batch, turns, capacity, mask_width), dtype=np.bool_
        )
        self.program_quantity_max = np.empty(
            (batch, turns, capacity), dtype=np.int64
        )
        self.program_decision_counts = np.empty((batch, turns), dtype=np.int16)
        self.old_joint_log_probability = np.empty((batch, turns), dtype=np.float32)
        self.old_values = np.empty((batch, turns), dtype=np.float32)
        self.stochastic_factor_counts = np.empty((batch, turns), dtype=np.int16)

    def append(
        self,
        board: NDArray[np.float16],
        units: NDArray[np.float16],
        global_features: NDArray[np.float32],
        economic_state: NDArray[np.int32],
        rollout: ProgramTurnRollout,
    ) -> None:
        """Copy one entire vectorized turn into its reserved column."""
        turn = self.length
        if turn >= self.board.shape[1]:
            raise RuntimeError("conditional-program rollout exceeded episode capacity")
        compiled = rollout.compiled
        trace = rollout.trace
        self.board[:, turn] = board
        self.units[:, turn] = units
        self.global_features[:, turn] = global_features
        self.economic_state[:, turn] = economic_state
        width = compiled.tokens.shape[1]
        self.actions[:, turn, :width] = compiled.tokens
        self.quantities[:, turn] = 0
        self.quantities[:, turn, :width] = compiled.quantities
        self.action_decision_counts[:, turn] = compiled.decision_counts
        self.program_scalars[:, turn] = trace.scalars
        self.program_root_features[:, turn] = trace.root_features
        self.program_option_features[:, turn] = trace.option_features
        self.program_target_reservations[:, turn] = trace.target_reservations
        self.program_actions[:, turn] = trace.actions
        self.program_conditional_masks[:, turn] = trace.conditional_masks
        self.program_quantity_max[:, turn] = trace.quantity_max
        self.program_decision_counts[:, turn] = trace.decision_counts
        self.old_joint_log_probability[:, turn] = trace.old_joint_log_probability
        self.old_values[:, turn] = trace.old_values
        self.stochastic_factor_counts[:, turn] = trace.stochastic_factor_counts
        self.length += 1

    @property
    def nbytes(self) -> int:
        """Return allocated host bytes retained by this group."""
        return sum(
            int(getattr(self, name).nbytes)
            for name in self.__dict__
            if name != "length"
        )

    @property
    def device_nbytes(self) -> int:
        """Return zero for the host-backed fallback collector."""
        return 0

    def episode(
        self,
        row: int,
        *,
        episode_id: str,
        opponent_id: str,
        seed: int,
        seat: int,
        outcome: int,
        terminal_cash: float,
        opponent_cash: float,
    ) -> ProgramEpisode:
        """Expose one completed row without copying the field-major storage."""
        turn_slice = slice(0, self.length)
        return ProgramEpisode(
            episode_id=episode_id,
            opponent_id=opponent_id,
            seed=seed,
            seat=seat,
            outcome=outcome,
            terminal_cash=terminal_cash,
            opponent_cash=opponent_cash,
            board=self.board[row, turn_slice],
            units=self.units[row, turn_slice],
            global_features=self.global_features[row, turn_slice],
            economic_state=self.economic_state[row, turn_slice],
            actions=self.actions[row, turn_slice],
            quantities=self.quantities[row, turn_slice],
            action_decision_counts=self.action_decision_counts[row, turn_slice],
            program_scalars=self.program_scalars[row, turn_slice],
            program_root_features=self.program_root_features[row, turn_slice],
            program_option_features=self.program_option_features[row, turn_slice],
            program_target_reservations=self.program_target_reservations[
                row, turn_slice
            ],
            program_actions=self.program_actions[row, turn_slice],
            program_conditional_masks=self.program_conditional_masks[
                row, turn_slice
            ],
            program_quantity_max=self.program_quantity_max[row, turn_slice],
            program_decision_counts=self.program_decision_counts[row, turn_slice],
            old_joint_log_probability=self.old_joint_log_probability[
                row, turn_slice
            ],
            old_values=self.old_values[row, turn_slice],
            stochastic_factor_counts=self.stochastic_factor_counts[
                row, turn_slice
            ],
        )


class ProgramGpuGroupStorage:
    """Keep complete training traces on their rollout H200."""

    _DEVICE_FIELDS = (
        "board",
        "units",
        "global_features",
        "economic_state",
        "actions",
        "quantities",
        "action_decision_counts",
        "program_scalars",
        "program_root_features",
        "program_option_features",
        "program_target_reservations",
        "program_actions",
        "program_conditional_masks",
        "program_quantity_max",
        "program_decision_counts",
        "old_joint_log_probability",
        "old_values",
        "stochastic_factor_counts",
    )

    def __init__(
        self,
        batch: int,
        turns: int,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        economic_state: Tensor,
        contract: NativeProgramContract,
        mask_width: int,
        action_width: int,
    ) -> None:
        """Allocate turn-major device storage for contiguous per-turn writes."""
        capacity = contract.maximum_decisions
        if board.device.type != "cuda" or any(
            value.device != board.device
            for value in (units, global_features, economic_state)
        ):
            raise ValueError("program GPU storage inputs must share one CUDA device")
        if action_width < capacity:
            raise ValueError("actor history is narrower than native program actions")
        device = board.device
        self.length = 0
        self._capacity = capacity
        self._decision_max = np.ones(batch, dtype=np.int16)
        self.board = torch.empty(
            (turns, batch, *board.shape[1:]), dtype=board.dtype, device=device
        )
        self.units = torch.empty(
            (turns, batch, *units.shape[1:]), dtype=units.dtype, device=device
        )
        self.global_features = torch.empty(
            (turns, batch, global_features.shape[1]),
            dtype=torch.float32,
            device=device,
        )
        self.economic_state = torch.empty(
            (turns, batch, economic_state.shape[1]),
            dtype=torch.int32,
            device=device,
        )
        self.actions = torch.zeros(
            (turns, batch, action_width), dtype=torch.long, device=device
        )
        self.quantities = torch.zeros_like(self.actions)
        self.action_decision_counts = torch.empty(
            (turns, batch), dtype=torch.long, device=device
        )
        self.program_scalars = torch.empty(
            (turns, batch, capacity, 7), dtype=torch.int16, device=device
        )
        self.program_root_features = torch.empty(
            (turns, batch, capacity, contract.root_feature_count),
            dtype=torch.float32,
            device=device,
        )
        self.program_option_features = torch.empty(
            (turns, batch, capacity, contract.option_feature_count),
            dtype=torch.int32,
            device=device,
        )
        self.program_target_reservations = torch.empty(
            (turns, batch, capacity, contract.tile_count),
            dtype=torch.int16,
            device=device,
        )
        self.program_actions = torch.empty(
            (turns, batch, capacity, 9), dtype=torch.long, device=device
        )
        self.program_conditional_masks = torch.empty(
            (turns, batch, capacity, mask_width), dtype=torch.bool, device=device
        )
        self.program_quantity_max = torch.empty(
            (turns, batch, capacity), dtype=torch.long, device=device
        )
        self.program_decision_counts = torch.empty(
            (turns, batch), dtype=torch.int16, device=device
        )
        self.old_joint_log_probability = torch.empty(
            (turns, batch), dtype=torch.float32, device=device
        )
        self.old_values = torch.empty(
            (turns, batch), dtype=torch.float32, device=device
        )
        self.stochastic_factor_counts = torch.empty(
            (turns, batch), dtype=torch.int16, device=device
        )

    def destinations(self) -> tuple[tuple[Tensor, ...], tuple[Tensor, ...]]:
        """Return graph destinations for the current official turn."""
        turn = self.length
        if turn >= self.board.shape[0]:
            raise RuntimeError("conditional-program rollout exceeded episode capacity")
        compiled = (
            self.actions[turn, :, : self._capacity],
            self.quantities[turn, :, : self._capacity],
            self.action_decision_counts[turn],
        )
        trace = (
            self.program_scalars[turn],
            self.program_root_features[turn],
            self.program_option_features[turn],
            self.program_target_reservations[turn],
            self.program_actions[turn],
            self.program_conditional_masks[turn],
            self.program_quantity_max[turn],
            self.program_decision_counts[turn],
            self.old_joint_log_probability[turn],
            self.old_values[turn],
            self.stochastic_factor_counts[turn],
        )
        return compiled, trace

    def append(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        economic_state: Tensor,
        rollout: ProgramTurnRollout,
    ) -> None:
        """Retain observations after graph-owned trace copies are complete."""
        turn = self.length
        counts = rollout.trace_decision_counts_host
        if counts is None:
            raise RuntimeError("CUDA program rollout omitted host decision counts")
        self.board[turn].copy_(board, non_blocking=True)
        self.units[turn].copy_(units, non_blocking=True)
        self.global_features[turn].copy_(global_features, non_blocking=True)
        self.economic_state[turn].copy_(economic_state, non_blocking=True)
        np.maximum(self._decision_max, counts, out=self._decision_max)
        self.length += 1

    @property
    def nbytes(self) -> int:
        """Return the tiny host metadata retained by this group."""
        return int(self._decision_max.nbytes)

    @property
    def device_nbytes(self) -> int:
        """Return allocated HBM bytes retained by this group."""
        return sum(
            int(getattr(self, name).numel() * getattr(self, name).element_size())
            for name in self._DEVICE_FIELDS
        )

    def episode(
        self,
        row: int,
        *,
        episode_id: str,
        opponent_id: str,
        seed: int,
        seat: int,
        outcome: int,
        terminal_cash: float,
        opponent_cash: float,
    ) -> ProgramEpisode:
        """Expose one GPU-resident perspective without copying its trajectory."""
        turn_slice = slice(0, self.length)
        return ProgramEpisode(
            episode_id=episode_id,
            opponent_id=opponent_id,
            seed=seed,
            seat=seat,
            outcome=outcome,
            terminal_cash=terminal_cash,
            opponent_cash=opponent_cash,
            board=self.board[turn_slice, row],
            units=self.units[turn_slice, row],
            global_features=self.global_features[turn_slice, row],
            economic_state=self.economic_state[turn_slice, row],
            actions=self.actions[turn_slice, row],
            quantities=self.quantities[turn_slice, row],
            action_decision_counts=self.action_decision_counts[turn_slice, row],
            program_scalars=self.program_scalars[turn_slice, row],
            program_root_features=self.program_root_features[turn_slice, row],
            program_option_features=self.program_option_features[turn_slice, row],
            program_target_reservations=self.program_target_reservations[
                turn_slice, row
            ],
            program_actions=self.program_actions[turn_slice, row],
            program_conditional_masks=self.program_conditional_masks[
                turn_slice, row
            ],
            program_quantity_max=self.program_quantity_max[turn_slice, row],
            program_decision_counts=self.program_decision_counts[turn_slice, row],
            old_joint_log_probability=self.old_joint_log_probability[turn_slice, row],
            old_values=self.old_values[turn_slice, row],
            stochastic_factor_counts=self.stochastic_factor_counts[turn_slice, row],
            program_decision_max=int(self._decision_max[row]),
        )


__all__ = ["ProgramGpuGroupStorage", "ProgramGroupStorage"]
