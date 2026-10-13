"""Reusable collation and transfer buffers for complete-match PPO."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.rl.data import (
    TensorRolloutBatch,
    Trajectory,
    TrajectoryTurns,
    TurnRecord,
)
from kagg_revue.rl.rollout.packing import PackedBoolArray


@dataclass(frozen=True)
class _BatchLayout:
    capacity: int
    turns: int
    decisions: int
    facts: int
    board_shape: tuple[int, ...]
    unit_shape: tuple[int, ...]
    global_features: int
    economic_state_features: int
    fact_features: int
    prefix_features: int
    action_tokens: int
    candidate_features: int
    opening_residual_shape: tuple[int, int]


@dataclass(frozen=True)
class _EpisodeLayout:
    turns: int
    decisions: int
    facts: int
    board_shape: tuple[int, ...]
    unit_shape: tuple[int, ...]
    global_features: int
    economic_state_features: int
    fact_features: int
    prefix_features: int
    action_tokens: int
    candidate_features: int
    opening_residual_shape: tuple[int, int] | None


def _validate_turn(turn: TurnRecord, action_tokens: int | None = None) -> None:
    decisions = turn.actions.shape[0]
    tokens = turn.legal_mask.shape[-1]
    if decisions < 1 or (
        turn.actions.shape != (decisions,)
        or turn.quantities.shape != (decisions,)
        or turn.phases.shape != (decisions,)
        or turn.decision_mask.shape != (decisions,)
        or turn.old_log_probability.shape != (decisions,)
        or turn.legal_mask.shape != (decisions, tokens)
        or turn.prefix_facts.shape[0] != decisions
        or turn.candidate_facts.shape[:2] != (decisions, tokens)
    ):
        raise ValueError("rollout decision tensors are not internally aligned")
    if action_tokens is not None and tokens != action_tokens:
        raise ValueError("rollout action vocabulary changed within an episode")
    if not np.isfinite(turn.old_log_probability).all():
        raise ValueError("rollout policy behavior statistics are invalid")
    if not np.isfinite(turn.old_value):
        raise ValueError("rollout critic behavior statistics are invalid")
    if turn.skill_id < -1 or not np.isfinite(turn.old_skill_log_probability):
        raise ValueError("rollout latent behavior statistics are invalid")


def _stored_decision_width(turns: TrajectoryTurns) -> int:
    """Return the occupied decision prefix without trailing storage padding."""
    occupied = np.flatnonzero(turns.decision_mask.any(axis=0))
    if not occupied.size:
        raise ValueError("stored rollout contains no valid decisions")
    return int(occupied[-1]) + 1


def _episode_layout(trajectory: Trajectory) -> _EpisodeLayout:
    if not trajectory.turns:
        raise ValueError("rollout trajectory cannot be empty")
    if trajectory.outcome not in (-1, 0, 1):
        raise ValueError("rollout outcome must be loss, tie or win")
    residual = trajectory.opening_residual
    residual_shape: tuple[int, int] | None = None
    if residual is not None:
        if residual.ndim != 2 or not np.isfinite(residual).all():
            raise ValueError("opening residual must be one finite action-head matrix")
        if trajectory.opening_residual_turns < 1:
            raise ValueError("opening residual trajectory lacks its active prefix")
        residual_shape = (int(residual.shape[0]), int(residual.shape[1]))
    elif trajectory.opening_residual_turns != 0:
        raise ValueError("clean trajectory cannot carry an opening residual horizon")
    if isinstance(trajectory.turns, TrajectoryTurns):
        turns = trajectory.turns
        return _EpisodeLayout(
            turns=len(turns),
            decisions=_stored_decision_width(turns),
            facts=turns.turn_facts.shape[1],
            board_shape=turns.board.shape[1:],
            unit_shape=turns.units.shape[1:],
            global_features=turns.global_features.shape[-1],
            economic_state_features=turns.economic_state.shape[-1],
            fact_features=turns.turn_facts.shape[-1],
            prefix_features=turns.prefix_facts.shape[-1],
            action_tokens=turns.legal_mask.shape[-1],
            candidate_features=turns.candidate_facts.shape[-1],
            opening_residual_shape=residual_shape,
        )
    first = trajectory.turns[0]
    action_tokens = first.legal_mask.shape[-1]
    decisions = 0
    facts = 0
    for turn in trajectory.turns:
        _validate_turn(turn, action_tokens)
        if (
            turn.board.shape != first.board.shape
            or turn.units.shape != first.units.shape
            or turn.global_features.shape != first.global_features.shape
            or turn.economic_state.shape != first.economic_state.shape
            or turn.turn_facts.shape[-1] != first.turn_facts.shape[-1]
            or turn.prefix_facts.shape[1:] != first.prefix_facts.shape[1:]
            or turn.candidate_facts.shape[1:] != first.candidate_facts.shape[1:]
        ):
            raise ValueError("rollout tensor ABI changed across episodes")
        decisions = max(decisions, turn.actions.shape[0])
        facts = max(facts, turn.turn_facts.shape[0])
    return _EpisodeLayout(
        turns=len(trajectory.turns),
        decisions=decisions,
        facts=facts,
        board_shape=first.board.shape,
        unit_shape=first.units.shape,
        global_features=first.global_features.shape[-1],
        economic_state_features=first.economic_state.shape[-1],
        fact_features=first.turn_facts.shape[-1],
        prefix_features=first.prefix_facts.shape[-1],
        action_tokens=action_tokens,
        candidate_features=first.candidate_facts.shape[-1],
        opening_residual_shape=residual_shape,
    )


def _layout(trajectories: list[Trajectory], capacity: int) -> _BatchLayout:
    if not trajectories:
        raise ValueError("cannot collate an empty rollout minibatch")
    if capacity < 1:
        raise ValueError("rollout batch capacity must be positive")
    episodes = [_episode_layout(trajectory) for trajectory in trajectories]
    exemplar = episodes[0]
    residual_shapes = {
        episode.opening_residual_shape
        for episode in episodes
        if episode.opening_residual_shape is not None
    }
    if len(residual_shapes) > 1:
        raise ValueError("opening residual shape changed within a minibatch")
    residual_shape = next(iter(residual_shapes), (0, 0))
    for episode in episodes[1:]:
        if (
            episode.board_shape != exemplar.board_shape
            or episode.unit_shape != exemplar.unit_shape
            or episode.global_features != exemplar.global_features
            or episode.economic_state_features != exemplar.economic_state_features
            or episode.fact_features != exemplar.fact_features
            or episode.prefix_features != exemplar.prefix_features
            or episode.action_tokens != exemplar.action_tokens
            or episode.candidate_features != exemplar.candidate_features
        ):
            raise ValueError("rollout tensor ABI changed across episodes")
    if residual_shape != (0, 0) and residual_shape[0] != exemplar.action_tokens:
        raise ValueError("opening residual action rows differ from the rollout vocabulary")
    return _BatchLayout(
        capacity=capacity,
        turns=max(episode.turns for episode in episodes),
        decisions=max(episode.decisions for episode in episodes),
        facts=max(episode.facts for episode in episodes),
        board_shape=exemplar.board_shape,
        unit_shape=exemplar.unit_shape,
        global_features=exemplar.global_features,
        economic_state_features=exemplar.economic_state_features,
        fact_features=exemplar.fact_features,
        prefix_features=exemplar.prefix_features,
        action_tokens=exemplar.action_tokens,
        candidate_features=exemplar.candidate_features,
        opening_residual_shape=residual_shape,
    )


def _allocate(
    layout: _BatchLayout,
    device: torch.device,
    *,
    pin_memory: bool = False,
) -> TensorRolloutBatch:
    if pin_memory and device.type != "cpu":
        raise ValueError("only CPU rollout buffers can be pinned")

    def empty(shape: tuple[int, ...], dtype: torch.dtype) -> Tensor:
        return torch.empty(
            shape,
            dtype=dtype,
            device=device,
            pin_memory=pin_memory,
        )

    batch = layout.capacity
    turns = layout.turns
    decisions = layout.decisions
    facts = layout.facts
    return TensorRolloutBatch(
        board=empty((batch, turns, *layout.board_shape), torch.float16),
        units=empty((batch, turns, *layout.unit_shape), torch.float16),
        global_features=empty((batch, turns, layout.global_features), torch.float32),
        economic_state=empty(
            (batch, turns, layout.economic_state_features),
            torch.int32,
        ),
        turn_facts=empty((batch, turns, facts, layout.fact_features), torch.float16),
        turn_fact_mask=empty((batch, turns, facts), torch.bool),
        prefix_facts=empty((batch, turns, decisions, layout.prefix_features), torch.float16),
        candidate_facts=empty(
            (
                batch,
                turns,
                decisions,
                layout.action_tokens,
                layout.candidate_features,
            ),
            torch.float16,
        ),
        legal_mask=empty((batch, turns, decisions, layout.action_tokens), torch.bool),
        actions=empty((batch, turns, decisions), torch.int64),
        quantities=empty((batch, turns, decisions), torch.int64),
        phases=empty((batch, turns, decisions), torch.int64),
        turn_mask=empty((batch, turns), torch.bool),
        decision_mask=empty((batch, turns, decisions), torch.bool),
        old_log_probability=empty((batch, turns, decisions), torch.float32),
        skill_ids=empty((batch, turns), torch.int64),
        old_skill_log_probability=empty((batch, turns), torch.float32),
        old_values=empty((batch, turns), torch.float32),
        opening_residual=empty((batch, *layout.opening_residual_shape), torch.float32),
        opening_residual_turns=empty((batch,), torch.int64),
        outcomes=empty((batch,), torch.int64),
        cash_differences=empty((batch,), torch.float32),
    )


@dataclass(frozen=True)
class _NumpyBatch:
    board: NDArray[np.float16]
    units: NDArray[np.float16]
    global_features: NDArray[np.float32]
    economic_state: NDArray[np.int32]
    turn_facts: NDArray[np.float16]
    turn_fact_mask: NDArray[np.bool_]
    prefix_facts: NDArray[np.float16]
    candidate_facts: NDArray[np.float16]
    legal_mask: NDArray[np.bool_]
    actions: NDArray[np.int64]
    quantities: NDArray[np.int64]
    phases: NDArray[np.int64]
    turn_mask: NDArray[np.bool_]
    decision_mask: NDArray[np.bool_]
    old_log_probability: NDArray[np.float32]
    skill_ids: NDArray[np.int64]
    old_skill_log_probability: NDArray[np.float32]
    old_values: NDArray[np.float32]
    opening_residual: NDArray[np.float32]
    opening_residual_turns: NDArray[np.int64]
    outcomes: NDArray[np.int64]
    cash_differences: NDArray[np.float32]

    @classmethod
    def from_tensors(cls, batch: TensorRolloutBatch) -> _NumpyBatch:
        """Create stable NumPy views over one CPU allocation."""
        if any(tensor.device.type != "cpu" for tensor in batch.tensors()):
            raise ValueError("NumPy rollout views require CPU tensors")
        return cls(*(tensor.numpy() for tensor in batch.tensors()))

    def clear_row(self, row: int) -> None:
        """Reset padding before copying a variable-shape legacy trajectory."""
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
            self.quantities,
            self.phases,
            self.turn_mask,
            self.decision_mask,
            self.old_log_probability,
            self.old_skill_log_probability,
            self.old_values,
            self.opening_residual,
        ):
            value[row].fill(0)
        self.actions[row].fill(-1)
        self.skill_ids[row].fill(-1)
        self.opening_residual_turns[row] = 0


def _copy_stored(
    destination: _NumpyBatch,
    row: int,
    turns: TrajectoryTurns,
    layout: _BatchLayout,
) -> None:
    length = len(turns)
    decisions = _stored_decision_width(turns)
    facts = turns.turn_facts.shape[1]
    exact = length == layout.turns and decisions == layout.decisions and facts == layout.facts
    if not exact:
        destination.clear_row(row)
    destination.board[row, :length] = turns.board
    destination.units[row, :length] = turns.units
    destination.global_features[row, :length] = turns.global_features
    destination.economic_state[row, :length] = turns.economic_state
    destination.turn_facts[row, :length, :facts] = turns.turn_facts
    destination.turn_fact_mask[row, :length, :facts] = turns.turn_fact_mask
    destination.prefix_facts[row, :length, :decisions] = turns.prefix_facts[:, :decisions]
    destination.candidate_facts[row, :length, :decisions] = turns.candidate_facts[:, :decisions]
    legal_mask = (
        turns.legal_mask.unpack(decisions)
        if isinstance(turns.legal_mask, PackedBoolArray)
        else turns.legal_mask[:, :decisions]
    )
    destination.legal_mask[row, :length, :decisions] = legal_mask
    destination.actions[row, :length, :decisions] = turns.actions[:, :decisions]
    destination.quantities[row, :length, :decisions] = turns.quantities[:, :decisions]
    destination.phases[row, :length, :decisions] = turns.phases[:, :decisions]
    destination.turn_mask[row, :length] = True
    destination.decision_mask[row, :length, :decisions] = turns.decision_mask[:, :decisions]
    destination.old_log_probability[row, :length, :decisions] = turns.old_log_probability[
        :, :decisions
    ]
    destination.skill_ids[row, :length] = turns.skill_ids
    destination.old_skill_log_probability[row, :length] = turns.old_skill_log_probability
    destination.old_values[row, :length] = turns.old_values


def _copy_legacy(
    destination: _NumpyBatch,
    row: int,
    trajectory: Trajectory,
) -> None:
    destination.clear_row(row)
    for column, turn in enumerate(trajectory.turns):
        fact_count = turn.turn_facts.shape[0]
        decision_count = turn.actions.shape[0]
        destination.board[row, column] = turn.board
        destination.units[row, column] = turn.units
        destination.global_features[row, column] = turn.global_features
        destination.economic_state[row, column] = turn.economic_state
        destination.turn_facts[row, column, :fact_count] = turn.turn_facts
        destination.turn_fact_mask[row, column, :fact_count] = True
        destination.prefix_facts[row, column, :decision_count] = turn.prefix_facts
        destination.candidate_facts[row, column, :decision_count] = turn.candidate_facts
        destination.legal_mask[row, column, :decision_count] = turn.legal_mask
        destination.actions[row, column, :decision_count] = turn.actions
        destination.quantities[row, column, :decision_count] = turn.quantities
        destination.phases[row, column, :decision_count] = turn.phases
        destination.turn_mask[row, column] = True
        destination.decision_mask[row, column, :decision_count] = turn.decision_mask
        destination.old_log_probability[row, column, :decision_count] = turn.old_log_probability
        destination.skill_ids[row, column] = turn.skill_id
        destination.old_skill_log_probability[row, column] = turn.old_skill_log_probability
        destination.old_values[row, column] = turn.old_value


def _collate_into(
    trajectories: list[Trajectory],
    destination: _NumpyBatch,
    layout: _BatchLayout,
) -> None:
    if not trajectories or len(trajectories) > layout.capacity:
        raise ValueError("rollout minibatch does not fit its reusable allocation")
    for row, trajectory in enumerate(trajectories):
        if trajectory.outcome not in (-1, 0, 1):
            raise ValueError("rollout outcome must be loss, tie or win")
        if isinstance(trajectory.turns, TrajectoryTurns):
            _copy_stored(destination, row, trajectory.turns, layout)
        else:
            _copy_legacy(destination, row, trajectory)
        destination.opening_residual[row].fill(0.0)
        if trajectory.opening_residual is not None:
            if destination.opening_residual[row].shape != trajectory.opening_residual.shape:
                raise ValueError("opening residual does not fit the minibatch allocation")
            destination.opening_residual[row] = trajectory.opening_residual
        destination.opening_residual_turns[row] = trajectory.opening_residual_turns
        destination.outcomes[row] = trajectory.outcome
        destination.cash_differences[row] = trajectory.terminal_cash - trajectory.opponent_cash


def collate_trajectories(
    trajectories: list[Trajectory],
    device: torch.device,
) -> TensorRolloutBatch:
    """Collate one variable-shape minibatch through a compact CPU allocation."""
    layout = _layout(trajectories, len(trajectories))
    host = _allocate(layout, torch.device("cpu"))
    _collate_into(trajectories, _NumpyBatch.from_tensors(host), layout)
    view = host.view(
        len(trajectories),
        layout.turns,
        layout.decisions,
        layout.facts,
    )
    return view if device.type == "cpu" else move_rollout_batch(view, device)


def move_rollout_batch(
    batch: TensorRolloutBatch,
    device: torch.device,
) -> TensorRolloutBatch:
    """Transfer a one-off episode minibatch to one device."""
    return TensorRolloutBatch(*(value.to(device) for value in batch.tensors()))


@dataclass(frozen=True)
class PreparedBatch:
    """One host slot filled by the collation worker."""

    slot: int
    size: int


@dataclass
class _PipelineSlot:
    host: TensorRolloutBatch
    arrays: _NumpyBatch
    device: TensorRolloutBatch
    transfer_done: torch.cuda.Event | None
    compute_done: torch.cuda.Event | None
    transfer_recorded: bool = False
    compute_recorded: bool = False


class RolloutBatchPipeline:
    """Double-buffer CPU collation, pinned H2D, and PPO consumption."""

    slots = 2

    def __init__(
        self,
        trajectories: list[Trajectory],
        capacity: int,
        device: torch.device,
    ) -> None:
        """Allocate a fixed layout covering the complete rollout panel."""
        if capacity < 1:
            raise ValueError("rollout minibatch capacity must be positive")
        self._layout = _layout(trajectories, capacity)
        self._device = device
        self._transfer_stream = (
            torch.cuda.Stream(device=device)  # type: ignore[no-untyped-call]
            if device.type == "cuda"
            else None
        )
        self._slots: list[_PipelineSlot] = []
        for _ in range(self.slots):
            host = _allocate(
                self._layout,
                torch.device("cpu"),
                pin_memory=device.type == "cuda",
            )
            destination = _allocate(self._layout, device) if device.type == "cuda" else host
            self._slots.append(
                _PipelineSlot(
                    host=host,
                    arrays=_NumpyBatch.from_tensors(host),
                    device=destination,
                    transfer_done=(
                        torch.cuda.Event()  # type: ignore[no-untyped-call]
                        if device.type == "cuda"
                        else None
                    ),
                    compute_done=(
                        torch.cuda.Event()  # type: ignore[no-untyped-call]
                        if device.type == "cuda"
                        else None
                    ),
                )
            )

    def wait_host_reusable(self, slot: int) -> None:
        """Wait only when a prior H2D still reads this slot's pinned memory."""
        state = self._slots[slot]
        if state.transfer_recorded and state.transfer_done is not None:
            state.transfer_done.synchronize()

    def prepare(self, slot: int, trajectories: list[Trajectory]) -> PreparedBatch:
        """Fill one host slot and queue H2D; safe to call on a worker thread."""
        if slot < 0 or slot >= self.slots:
            raise IndexError("rollout pipeline slot is out of range")
        state = self._slots[slot]
        _collate_into(trajectories, state.arrays, self._layout)
        if self._device.type == "cuda":
            if (
                self._transfer_stream is None
                or state.transfer_done is None
                or state.compute_done is None
            ):
                raise RuntimeError("CUDA rollout pipeline lacks synchronization state")
            host = state.host.view(
                len(trajectories),
                self._layout.turns,
                self._layout.decisions,
                self._layout.facts,
            )
            destination = state.device.view(
                len(trajectories),
                self._layout.turns,
                self._layout.decisions,
                self._layout.facts,
            )
            with torch.cuda.stream(self._transfer_stream):
                if state.compute_recorded:
                    self._transfer_stream.wait_event(state.compute_done)
                for target, source in zip(destination.tensors(), host.tensors(), strict=True):
                    target.copy_(source, non_blocking=True)
                state.transfer_done.record(self._transfer_stream)
            state.transfer_recorded = True
        return PreparedBatch(slot=slot, size=len(trajectories))

    def upload(self, prepared: PreparedBatch) -> TensorRolloutBatch:
        """Make the compute stream depend on the worker-queued H2D."""
        state = self._slots[prepared.slot]
        host = state.host.view(
            prepared.size,
            self._layout.turns,
            self._layout.decisions,
            self._layout.facts,
        )
        if self._device.type != "cuda":
            return host
        if state.transfer_done is None:
            raise RuntimeError("CUDA rollout pipeline lacks synchronization state")
        destination = state.device.view(
            prepared.size,
            self._layout.turns,
            self._layout.decisions,
            self._layout.facts,
        )
        torch.cuda.current_stream(self._device).wait_event(state.transfer_done)
        return destination

    def finish(self, prepared: PreparedBatch) -> None:
        """Protect a device slot until its PPO step has finished."""
        state = self._slots[prepared.slot]
        if self._device.type == "cuda":
            if state.compute_done is None:
                raise RuntimeError("CUDA rollout pipeline lacks a completion event")
            state.compute_done.record(torch.cuda.current_stream(self._device))
            state.compute_recorded = True


__all__ = [
    "PreparedBatch",
    "RolloutBatchPipeline",
    "collate_trajectories",
    "move_rollout_batch",
]
