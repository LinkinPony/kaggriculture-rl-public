"""Batched host storage for compact task PPO traces."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, overload

import numpy as np
from numpy.typing import NDArray

from kagg_revue.policy.tasks.runtime import CompactTaskTrace
from kagg_revue.rl.tasks.compact import CompactTaskTurnRecord

_TASK_FIELDS = 9
_SNAPSHOT_SCALARS = (
    "hour",
    "day",
    "days",
    "unit_counts",
    "history_counts",
    "successful_tasks",
    "failed_tasks",
    "forced_ends",
)
_SNAPSHOT_VECTORS = (
    "replan_mask",
    "optional_mask",
    "replan_reasons",
    "tape_sizes",
)
_STORED_SNAPSHOT_FIELDS = (*_SNAPSHOT_SCALARS, *_SNAPSHOT_VECTORS)


@dataclass(frozen=True)
class TaskValueMoments:
    """Sufficient old-value statistics for episode-normalized advantages."""

    count: int
    total: float
    square_total: float


@dataclass(frozen=True)
class _CompactTaskTurnBatch:
    """One turn's snapshot deltas and ragged behavior tape."""

    turn_index: int
    snapshot: Mapping[str, NDArray[Any]]
    prefix_change_offsets: NDArray[np.int32]
    prefix_change_positions: NDArray[np.uint16]
    prefix_change_values: NDArray[np.int16]
    decision_offsets: NDArray[np.int32]
    actions: NDArray[np.int16]
    counts: NDArray[np.int16]
    old_joint_log_probability: NDArray[np.float32]
    old_values: NDArray[np.float32]

    def arrays(self) -> tuple[NDArray[Any], ...]:
        """Return unique retained payload arrays."""
        return (
            *(self.snapshot[name] for name in _STORED_SNAPSHOT_FIELDS),
            self.prefix_change_offsets,
            self.prefix_change_positions,
            self.prefix_change_values,
            self.decision_offsets,
            self.actions,
            self.counts,
            self.old_joint_log_probability,
            self.old_values,
        )


class CompactTaskPanel:
    """Retain task traces by turn without creating one Python object per game."""

    def __init__(self, games: int) -> None:
        """Create an empty fixed-row panel."""
        if games < 1:
            raise ValueError("compact task panel needs at least one game")
        self._games = games
        self._turns: list[_CompactTaskTurnBatch] = []
        self._sealed = False
        self._record_counts = np.zeros(games, dtype=np.int32)
        self._decision_counts = np.zeros(games, dtype=np.int64)
        self._old_value_sums = np.zeros(games, dtype=np.float64)
        self._old_value_square_sums = np.zeros(games, dtype=np.float64)
        self._row_nbytes = np.zeros(games, dtype=np.int64)
        self._prefix_state: NDArray[np.int16] | None = None
        self._prefix_capacity = 0

    @property
    def games(self) -> int:
        """Return the fixed number of actor rows."""
        return self._games

    @property
    def decisions(self) -> int:
        """Return the number of sampled task factors in the panel."""
        return int(self._decision_counts.sum())

    @property
    def nbytes(self) -> int:
        """Return the exact retained ndarray payload size."""
        return int(self._row_nbytes.sum())

    def _distribute_shared_bytes(self, size: int) -> None:
        """Attribute one shared allocation exactly across episode views."""
        quotient, remainder = divmod(size, self._games)
        self._row_nbytes += quotient
        self._row_nbytes[:remainder] += 1

    def append(self, trace: CompactTaskTrace, turn_index: int) -> None:
        """Retain one complete batched trace by reference after validation."""
        if self._sealed:
            raise RuntimeError("cannot append to a sealed compact task panel")
        if turn_index != len(self._turns):
            raise ValueError("compact task panel turns must be chronological")
        snapshot = {
            name: np.asarray(trace.snapshot[name])
            for name in _STORED_SNAPSHOT_FIELDS
        }
        prefix = np.asarray(trace.snapshot["prefix_fields"], dtype=np.int16)
        counts = np.asarray(trace.counts, dtype=np.int16)
        actions = np.asarray(trace.actions, dtype=np.int16)
        old_log = np.asarray(trace.old_joint_log_probability, dtype=np.float32)
        old_values = np.asarray(trace.old_values, dtype=np.float32)
        if counts.shape != (self._games,) or np.any(counts < 0):
            raise ValueError("compact task trace counts differ from its panel")
        width = actions.shape[1] if actions.ndim == 3 else -1
        if (
            actions.shape != (self._games, width, 5)
            or old_log.shape != (self._games, width)
            or old_values.shape != (self._games, width)
            or width < 1
            or np.any(counts > width)
        ):
            raise ValueError("compact task trace tape fields are misaligned")
        for name in _SNAPSHOT_SCALARS:
            if snapshot[name].shape != (self._games,):
                raise ValueError(f"compact task snapshot {name} has the wrong shape")
        if (
            prefix.ndim != 3
            or prefix.shape[0] != self._games
            or prefix.shape[2] != _TASK_FIELDS
        ):
            raise ValueError("compact task snapshot prefix has the wrong shape")
        if snapshot["replan_mask"].ndim != 2:
            raise ValueError("compact task snapshot replan mask has the wrong shape")
        unit_width = snapshot["replan_mask"].shape[1]
        for name in _SNAPSHOT_VECTORS:
            if snapshot[name].shape != (self._games, unit_width):
                raise ValueError(f"compact task snapshot {name} has the wrong shape")
        active = counts > 0
        if np.any(active & ~np.asarray(snapshot["replan_mask"], dtype=np.bool_).any(axis=1)):
            raise ValueError("compact task trace active row lacks a replanning unit")
        positions = np.arange(width)[None, :] < counts[:, None]
        if (
            np.any(positions & ~np.isfinite(old_log))
            or np.any(positions & ~np.isfinite(old_values))
        ):
            raise ValueError("compact task trace contains non-finite behavior values")
        if self._prefix_state is None:
            self._prefix_state = np.zeros_like(prefix)
            self._prefix_capacity = int(prefix.shape[1])
        elif self._prefix_state.shape != prefix.shape:
            raise ValueError("compact task prefix capacity changed within one panel")
        flat_width = prefix.shape[1] * _TASK_FIELDS
        changed = prefix != self._prefix_state
        changed &= active[:, None, None]
        flat_changes = np.flatnonzero(changed.reshape(self._games, flat_width))
        change_rows = flat_changes // flat_width
        change_counts = np.bincount(
            change_rows, minlength=self._games
        ).astype(np.int32, copy=False)
        prefix_change_offsets = np.empty(self._games + 1, dtype=np.int32)
        prefix_change_offsets[0] = 0
        np.cumsum(change_counts, out=prefix_change_offsets[1:])
        prefix_change_positions = np.asarray(
            flat_changes % flat_width, dtype=np.uint16
        )
        prefix_change_values = np.asarray(
            prefix.reshape(self._games, flat_width).reshape(-1)[flat_changes],
            dtype=np.int16,
        )
        self._prefix_state[active] = prefix[active]

        decision_offsets = np.empty(self._games + 1, dtype=np.int32)
        decision_offsets[0] = 0
        np.cumsum(counts, dtype=np.int32, out=decision_offsets[1:])
        packed_actions = np.ascontiguousarray(actions[positions], dtype=np.int16)
        packed_old_log = np.ascontiguousarray(old_log[positions], dtype=np.float32)
        packed_old_values = np.ascontiguousarray(
            old_values[positions], dtype=np.float32
        )
        batch = _CompactTaskTurnBatch(
            turn_index=turn_index,
            snapshot=snapshot,
            prefix_change_offsets=prefix_change_offsets,
            prefix_change_positions=prefix_change_positions,
            prefix_change_values=prefix_change_values,
            decision_offsets=decision_offsets,
            actions=packed_actions,
            counts=counts,
            old_joint_log_probability=packed_old_log,
            old_values=packed_old_values,
        )
        arrays = batch.arrays()
        for value in arrays:
            value.flags.writeable = False
        live_values = np.where(positions, old_values, 0.0).astype(
            np.float64, copy=False
        )
        self._record_counts += active
        self._decision_counts += counts
        self._old_value_sums += live_values.sum(axis=1, dtype=np.float64)
        self._old_value_square_sums += np.square(live_values).sum(
            axis=1, dtype=np.float64
        )
        fixed_arrays = (
            *(snapshot[name] for name in _STORED_SNAPSHOT_FIELDS),
            counts,
        )
        fixed_bytes = sum(int(value.nbytes) for value in fixed_arrays)
        if fixed_bytes % self._games:
            raise ValueError("compact task fixed payload cannot be divided by row")
        self._row_nbytes += fixed_bytes // self._games
        self._distribute_shared_bytes(int(prefix_change_offsets.nbytes))
        self._distribute_shared_bytes(int(decision_offsets.nbytes))
        self._row_nbytes += change_counts.astype(np.int64) * (
            prefix_change_positions.itemsize + prefix_change_values.itemsize
        )
        self._row_nbytes += counts.astype(np.int64) * (
            packed_actions.shape[1] * packed_actions.itemsize
            + packed_old_log.itemsize
            + packed_old_values.itemsize
        )
        self._turns.append(batch)

    def episode(self, row: int) -> CompactTaskEpisodeTurns:
        """Expose one immutable actor-row view after collection finishes."""
        if row < 0 or row >= self._games:
            raise IndexError("compact task panel row is out of range")
        self._sealed = True
        self._prefix_state = None
        return CompactTaskEpisodeTurns(self, row)

    def _record(
        self,
        turn: _CompactTaskTurnBatch,
        row: int,
        prefix_state: NDArray[np.int16],
    ) -> CompactTaskTurnRecord:
        count = int(turn.counts[row])
        if count < 1:
            raise IndexError("compact task turn has no record for this actor row")
        snapshot = turn.snapshot
        history_count = int(snapshot["history_counts"][row])
        change_start = int(turn.prefix_change_offsets[row])
        change_stop = int(turn.prefix_change_offsets[row + 1])
        prefix_state.reshape(-1)[
            turn.prefix_change_positions[change_start:change_stop]
        ] = turn.prefix_change_values[change_start:change_stop]
        prefix_fields = prefix_state[:history_count].copy()
        prefix_fields.flags.writeable = False
        decision_start = int(turn.decision_offsets[row])
        decision_stop = int(turn.decision_offsets[row + 1])
        if decision_stop - decision_start != count:
            raise RuntimeError("compact task decision offsets are inconsistent")
        return CompactTaskTurnRecord(
            turn_index=turn.turn_index,
            hour=int(snapshot["hour"][row]),
            day=int(snapshot["day"][row]),
            days=int(snapshot["days"][row]),
            unit_count=int(snapshot["unit_counts"][row]),
            history_count=history_count,
            successful_tasks=int(snapshot["successful_tasks"][row]),
            failed_tasks=int(snapshot["failed_tasks"][row]),
            forced_ends=int(snapshot["forced_ends"][row]),
            prefix_fields=prefix_fields,
            replan_mask=snapshot["replan_mask"][row],
            optional_mask=snapshot["optional_mask"][row],
            replan_reasons=snapshot["replan_reasons"][row],
            tape_sizes=snapshot["tape_sizes"][row],
            actions=turn.actions[decision_start:decision_stop],
            old_joint_log_probability=(
                turn.old_joint_log_probability[decision_start:decision_stop]
            ),
            old_values=turn.old_values[decision_start:decision_stop],
            _copy_arrays=False,
        )

    def _iter_records(self, row: int) -> Iterator[CompactTaskTurnRecord]:
        prefix_state = np.zeros(
            (self._prefix_capacity, _TASK_FIELDS), dtype=np.int16
        )
        for turn in self._turns:
            if turn.counts[row] > 0:
                yield self._record(turn, row, prefix_state)

    def _record_at(self, row: int, index: int) -> CompactTaskTurnRecord:
        target = index + int(self._record_counts[row]) if index < 0 else index
        if target < 0 or target >= int(self._record_counts[row]):
            raise IndexError("compact task episode record is out of range")
        found = 0
        prefix_state = np.zeros(
            (self._prefix_capacity, _TASK_FIELDS), dtype=np.int16
        )
        for turn in self._turns:
            if turn.counts[row] == 0:
                continue
            if found == target:
                return self._record(turn, row, prefix_state)
            self._record(turn, row, prefix_state)
            found += 1
        raise RuntimeError("compact task panel record index is inconsistent")

    def _maximum_turn(self, row: int) -> int:
        for turn in reversed(self._turns):
            if turn.counts[row] > 0:
                return turn.turn_index
        return -1

    def _moments(self, row: int) -> TaskValueMoments:
        return TaskValueMoments(
            int(self._decision_counts[row]),
            float(self._old_value_sums[row]),
            float(self._old_value_square_sums[row]),
        )


@dataclass(frozen=True)
class CompactTaskEpisodeTurns(Sequence[CompactTaskTurnRecord]):
    """One actor row lazily materialized from a shared batched task panel."""

    _panel: CompactTaskPanel
    _row: int

    @property
    def nbytes(self) -> int:
        """Return this row's exact share of retained panel payloads."""
        return int(self._panel._row_nbytes[self._row])  # noqa: SLF001

    @property
    def maximum_turn_index(self) -> int:
        """Return the last turn carrying a task decision."""
        return self._panel._maximum_turn(self._row)  # noqa: SLF001

    @property
    def old_value_moments(self) -> TaskValueMoments:
        """Return old-value moments without creating per-turn records."""
        return self._panel._moments(self._row)  # noqa: SLF001

    def __len__(self) -> int:
        """Return the number of turn boundaries with task decisions."""
        return int(self._panel._record_counts[self._row])  # noqa: SLF001

    @overload
    def __getitem__(self, index: int) -> CompactTaskTurnRecord: ...

    @overload
    def __getitem__(self, index: slice) -> tuple[CompactTaskTurnRecord, ...]: ...

    def __getitem__(
        self, index: int | slice
    ) -> CompactTaskTurnRecord | tuple[CompactTaskTurnRecord, ...]:
        """Materialize one record or a bounded tuple of records."""
        if isinstance(index, slice):
            return tuple(self[item] for item in range(*index.indices(len(self))))
        return self._panel._record_at(self._row, index)  # noqa: SLF001

    def __iter__(self) -> Iterator[CompactTaskTurnRecord]:
        """Materialize this episode's records in chronological order."""
        return self._panel._iter_records(self._row)  # noqa: SLF001


__all__ = [
    "CompactTaskEpisodeTurns",
    "CompactTaskPanel",
    "TaskValueMoments",
]
