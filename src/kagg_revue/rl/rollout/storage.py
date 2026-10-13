"""Contiguous field-major storage for one lockstep rollout group."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from kagg_revue.policy.economics import EconomicStateLayout
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.rl.data import TrajectoryTurns
from kagg_revue.rl.rollout.packing import PackedBoolArray


class StoredTurn(Protocol):
    """Array boundary supplied by the batched actor sampler."""

    board: NDArray[np.float32] | NDArray[np.float16]
    units: NDArray[np.float32] | NDArray[np.float16]
    globals_: NDArray[np.float32] | NDArray[np.float16]
    economic_state: NDArray[np.int32] | NDArray[np.int64]
    turn_facts: NDArray[np.float32]
    prefix_facts: NDArray[np.float16]
    candidate_facts: NDArray[np.float16]
    legal: NDArray[np.bool_]
    actions: NDArray[np.int64]
    quantities: NDArray[np.int64]
    phases: NDArray[np.int64]
    decisions: NDArray[np.bool_]
    log_probability: NDArray[np.float32]
    skill_id: int
    skill_log_probability: float
    old_value: float


@dataclass(frozen=True)
class BatchedStoredTurns:
    """GPU graph outputs before selecting the candidate rows.

    Observations are row-major. Autoregressive outputs are decision-major to
    match their persistent graph buffers and are transposed as views on write.
    """

    board: NDArray[np.float16]
    units: NDArray[np.float16]
    global_features: NDArray[np.float32]
    economic_state: NDArray[np.int32]
    legal_mask: NDArray[np.bool_]
    actions: NDArray[np.int64]
    quantities: NDArray[np.int64]
    phases: NDArray[np.int64]
    decision_mask: NDArray[np.bool_]
    old_log_probability: NDArray[np.float32]
    skill_ids: NDArray[np.int64] | None
    old_skill_log_probability: NDArray[np.float32] | None
    old_values: NDArray[np.float32]
    inactive_values_initialized: bool = False


class RolloutPanel:
    """Preallocated turn-major arrays for a complete lockstep group.

    This storage is used by the production raw-observation actor. Derived facts
    have a variable entity count and continue through the legacy storage path.
    Rollout writes are contiguous; per-game views are exposed only after the
    group has finished.
    """

    def __init__(
        self,
        games: int,
        turn_capacity: int,
        architecture: ActorArchitecture,
    ) -> None:
        """Allocate every field once for the maximum official episode length."""
        if games < 1 or turn_capacity < 1:
            raise ValueError("rollout panel dimensions must be positive")
        if architecture.turn_fact_features:
            raise ValueError("contiguous rollout panels require raw observations")
        decisions = architecture.max_decisions
        tokens = architecture.action_tokens
        shape = (turn_capacity, games)
        self._games = games
        self._capacity = turn_capacity
        self._length = 0
        self._action_tokens = tokens
        self.board = np.empty((*shape, *architecture.board_shape), dtype=np.float16)
        self.units = np.empty((*shape, *architecture.unit_shape), dtype=np.float16)
        self.global_features = np.empty((*shape, architecture.global_features), dtype=np.float32)
        economic_width = (
            EconomicStateLayout.create(
                architecture.board_shape[-1],
                architecture.unit_shape[1],
            ).width
            if architecture.economic_feature_version is not None
            else 0
        )
        self.economic_state = np.empty((*shape, economic_width), dtype=np.int32)
        self.turn_facts = np.empty((*shape, 0, 0), dtype=np.float16)
        self.turn_fact_mask = np.empty((*shape, 0), dtype=np.bool_)
        self.prefix_facts = np.empty(
            (*shape, decisions, architecture.prefix_fact_features), dtype=np.float16
        )
        self.candidate_facts = np.empty(
            (
                *shape,
                decisions,
                tokens,
                architecture.candidate_fact_features,
            ),
            dtype=np.float16,
        )
        self.legal_mask = np.empty(
            (*shape, decisions, (tokens + 7) // 8), dtype=np.uint8
        )
        action_dtype = (
            np.int8 if tokens <= 128 else np.int16 if tokens <= 32768 else np.int32
        )
        quantity_dtype = (
            np.uint8
            if architecture.maximum_quantity <= 255
            else np.uint16
            if architecture.maximum_quantity <= 65535
            else np.uint32
        )
        self.actions = np.empty((*shape, decisions), dtype=action_dtype)
        self.quantities = np.empty((*shape, decisions), dtype=quantity_dtype)
        self.phases = np.empty((*shape, decisions), dtype=np.uint8)
        self.decision_mask = np.empty((*shape, decisions), dtype=np.bool_)
        self.old_log_probability = np.empty((*shape, decisions), dtype=np.float32)
        self.skill_ids = np.empty(shape, dtype=np.int64)
        self.old_skill_log_probability = np.empty(shape, dtype=np.float32)
        self.old_values = np.empty(shape, dtype=np.float32)

    @property
    def games(self) -> int:
        """Return the fixed number of episode rows."""
        return self._games

    @property
    def length(self) -> int:
        """Return the number of complete turns currently stored."""
        return self._length

    @property
    def nbytes(self) -> int:
        """Return physical array payload bytes, excluding small Python headers."""
        return sum(
            value.nbytes
            for value in (
                self.board,
                self.units,
                self.global_features,
                self.economic_state,
                self.turn_facts,
                self.turn_fact_mask,
                self.prefix_facts,
                self.candidate_facts,
                self.legal_mask,
                self.actions,
                self.quantities,
                self.phases,
                self.decision_mask,
                self.old_log_probability,
                self.skill_ids,
                self.old_skill_log_probability,
                self.old_values,
            )
        )

    def append(self, turns: Sequence[StoredTurn]) -> None:
        """Copy one sampled lockstep turn into its final episode-major slots."""
        column = self.reserve()
        self.append_reserved(column, turns)

    def reserve(self) -> int:
        """Reserve one chronological column before an asynchronous write."""
        if self._length >= self._capacity:
            raise RuntimeError("rollout exceeded the configured episode capacity")
        column = self._length
        self._length += 1
        return column

    def append_reserved(self, column: int, turns: Sequence[StoredTurn]) -> None:
        """Copy one sampled turn into an already reserved column."""
        if len(turns) != self.games:
            raise ValueError("sampled rollout row count differs from its panel")
        if column < 0 or column >= self._length:
            raise ValueError("rollout panel column was not reserved")
        for row, turn in enumerate(turns):
            count = int(turn.decisions.sum())
            if count < 1:
                raise RuntimeError("sampled rollout turn contains no decisions")
            if count > self.actions.shape[-1]:
                raise RuntimeError("sampled rollout exceeds the actor decision capacity")
            self.board[column, row] = turn.board
            self.units[column, row] = turn.units
            self.global_features[column, row] = turn.globals_
            self.economic_state[column, row] = turn.economic_state
            self.legal_mask[column, row].fill(0)
            self.actions[column, row].fill(-1)
            self.quantities[column, row].fill(0)
            self.phases[column, row].fill(0)
            self.decision_mask[column, row].fill(False)
            self.old_log_probability[column, row].fill(0)
            self.legal_mask[column, row, :count] = np.packbits(
                turn.legal[:count], axis=-1, bitorder="little"
            )
            self.actions[column, row, :count] = turn.actions[:count]
            self.quantities[column, row, :count] = turn.quantities[:count]
            self.phases[column, row, :count] = turn.phases[:count]
            self.decision_mask[column, row, :count] = turn.decisions[:count]
            self.old_log_probability[column, row, :count] = turn.log_probability[:count]
            self.skill_ids[column, row] = turn.skill_id
            self.old_skill_log_probability[column, row] = turn.skill_log_probability
            self.old_values[column, row] = turn.old_value

    def append_batched(
        self,
        turns: BatchedStoredTurns,
        rows: slice | NDArray[np.int64],
    ) -> None:
        """Write one GPU graph result with three observation and six action copies."""
        column = self.reserve()
        self.append_batched_reserved(column, turns, rows)

    def append_batched_reserved(
        self,
        column: int,
        turns: BatchedStoredTurns,
        rows: slice | NDArray[np.int64],
    ) -> None:
        """Write a GPU result into an already reserved chronological column."""
        if column < 0 or column >= self._length:
            raise ValueError("rollout panel column was not reserved")
        selected_board = turns.board[rows]
        if selected_board.shape[0] != self.games:
            raise ValueError("sampled rollout row count differs from its panel")
        self.board[column] = selected_board
        self.units[column] = turns.units[rows]
        self.global_features[column] = turns.global_features[rows]
        self.economic_state[column] = turns.economic_state[rows]

        decisions = turns.decision_mask[:, rows].T
        if decisions.shape != self.decision_mask[column].shape:
            raise ValueError("batched rollout decision shape differs from its panel")
        if not decisions.any(axis=1).all():
            raise RuntimeError("sampled rollout turn contains no decisions")
        self.decision_mask[column] = decisions
        if turns.inactive_values_initialized:
            self.actions[column] = turns.actions[:, rows].T
            self.quantities[column] = turns.quantities[:, rows].T
            # The CUDA sampler uses phase 2 to mark completed rows.  Inactive
            # positions still flow through the teacher-forced action decoder,
            # whose phase embedding only accepts the two prediction phases.
            self.phases[column].fill(0)
            np.copyto(
                self.phases[column],
                turns.phases[:, rows].T,
                where=decisions,
                casting="unsafe",
            )
            self.legal_mask[column] = np.packbits(
                turns.legal_mask[:, rows].transpose(1, 0, 2),
                axis=-1,
                bitorder="little",
            )
            self.old_log_probability[column] = (
                turns.old_log_probability[:, rows].T
            )
        else:
            self.actions[column].fill(-1)
            self.quantities[column].fill(0)
            self.phases[column].fill(0)
            self.legal_mask[column].fill(0)
            self.old_log_probability[column].fill(0)
            np.copyto(
                self.actions[column],
                turns.actions[:, rows].T,
                where=decisions,
                casting="unsafe",
            )
            np.copyto(
                self.quantities[column],
                turns.quantities[:, rows].T,
                where=decisions,
                casting="unsafe",
            )
            np.copyto(
                self.phases[column],
                turns.phases[:, rows].T,
                where=decisions,
                casting="unsafe",
            )
            packed_legal = np.packbits(
                turns.legal_mask[:, rows].transpose(1, 0, 2),
                axis=-1,
                bitorder="little",
            )
            np.copyto(
                self.legal_mask[column],
                packed_legal,
                where=decisions[..., None],
            )
            np.copyto(
                self.old_log_probability[column],
                turns.old_log_probability[:, rows].T,
                where=decisions,
            )
        if turns.skill_ids is None:
            self.skill_ids[column].fill(-1)
        else:
            self.skill_ids[column] = turns.skill_ids[rows]
        if turns.old_skill_log_probability is None:
            self.old_skill_log_probability[column].fill(0)
        else:
            self.old_skill_log_probability[column] = turns.old_skill_log_probability[rows]
        self.old_values[column] = turns.old_values[rows]

    def trajectory(self, row: int) -> TrajectoryTurns:
        """Return immutable episode views without copying the panel payload."""
        if row < 0 or row >= self.games:
            raise IndexError("rollout panel row is out of range")
        if self._length < 1:
            raise RuntimeError("rollout panel contains no complete turns")
        turns = slice(0, self._length)
        return TrajectoryTurns(
            board=self.board[turns, row],
            units=self.units[turns, row],
            global_features=self.global_features[turns, row],
            economic_state=self.economic_state[turns, row],
            turn_facts=self.turn_facts[turns, row],
            turn_fact_mask=self.turn_fact_mask[turns, row],
            prefix_facts=self.prefix_facts[turns, row],
            candidate_facts=self.candidate_facts[turns, row],
            legal_mask=PackedBoolArray(
                self.legal_mask[turns, row],
                (self._length, self.actions.shape[-1], self._action_tokens),
            ),
            actions=self.actions[turns, row],
            quantities=self.quantities[turns, row],
            phases=self.phases[turns, row],
            decision_mask=self.decision_mask[turns, row],
            old_log_probability=self.old_log_probability[turns, row],
            skill_ids=self.skill_ids[turns, row],
            old_skill_log_probability=self.old_skill_log_probability[turns, row],
            old_values=self.old_values[turns, row],
        )


__all__ = ["BatchedStoredTurns", "RolloutPanel", "StoredTurn"]
