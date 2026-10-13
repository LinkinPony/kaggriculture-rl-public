"""Asynchronous native teacher labels on live student rollout states."""

from __future__ import annotations

import time
from collections import Counter, deque
from collections.abc import Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.bc.programs.student_state import to_numpy
from kagg_revue.bc.programs.teacher_batch import (
    TeacherProgramTurnBatch,
    compile_teacher_program_turn_batch,
)
from kagg_revue.bc.programs.translate import ProgramReplaySeat
from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.kaito.native import create_native_session as kaito_session
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.runtime import compact_mask_width
from kagg_revue.rl.programs.data import ProgramEpisode


@dataclass
class _TeacherGroup:
    """Preallocated compiler outputs for one fixed-order rollout group."""

    keys: tuple[tuple[int, int], ...]
    sessions: list[Any]
    teacher_sessions: list[Any]
    repairs: list[Counter[str]]
    teacher_tokens: NDArray[np.int64]
    teacher_quantities: NDArray[np.int64]
    teacher_counts: NDArray[np.int64]
    teacher_units: NDArray[np.int64]
    scalars: NDArray[np.int16]
    roots: NDArray[np.float32]
    options: NDArray[np.int32]
    reservations: NDArray[np.int16]
    actions: NDArray[np.int64]
    masks: NDArray[np.bool_]
    quantity_max: NDArray[np.int64]
    decision_counts: NDArray[np.int16]


class FusedTeacherCompiler:
    """Overlap C++ teacher compilation with the frozen student's GPU turn."""

    def __init__(
        self,
        backend: BackendApi,
        maximum_market_orders: int,
        architecture: ActorArchitecture,
        codec: ReplayActionEncoder,
        contract: NativeProgramContract,
        workers: int,
    ) -> None:
        """Retain immutable compilation dependencies and one background lane."""
        self._backend = backend
        self._maximum_market_orders = maximum_market_orders
        self._architecture = architecture
        self._codec = codec
        self._contract = contract
        self._workers = workers
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="native-teacher-compiler",
        )
        self._active: _TeacherGroup | None = None
        self._completed: list[_TeacherGroup] = []
        self._pending: deque[
            tuple[
                _TeacherGroup,
                int,
                Future[tuple[TeacherProgramTurnBatch, float, float, float]],
            ]
        ] = deque()
        self._turn = 0
        self.native_seconds = 0.0
        self.action_seconds = 0.0
        self.compiler_seconds = 0.0
        self.wait_seconds = 0.0
        self.clone_seconds = 0.0

    def start_group(
        self,
        keys: Sequence[tuple[int, int]],
        engines: Sequence[Any],
        players: NDArray[np.int64],
        turns: int,
    ) -> None:
        """Allocate one group before its first frozen pre-action state."""
        if self._active is not None or self._pending:
            raise RuntimeError("fused teacher started an overlapping rollout group")
        batch = len(keys)
        if batch < 1 or len(engines) != batch or players.shape != (batch,) or turns < 1:
            raise ValueError("fused teacher group inputs are misaligned")
        width = self._architecture.max_decisions
        capacity = self._contract.maximum_decisions
        self._active = _TeacherGroup(
            keys=tuple(keys),
            sessions=[
                self._backend.conditional_program_session(
                    dict(engine.configuration),
                    self._contract.unit_limit,
                )
                for engine in engines
            ],
            teacher_sessions=[
                kaito_session(self._maximum_market_orders) for _ in keys
            ],
            repairs=[Counter[str]() for _ in keys],
            teacher_tokens=np.zeros((batch, width), dtype=np.int64),
            teacher_quantities=np.zeros((batch, width), dtype=np.int64),
            teacher_counts=np.zeros(batch, dtype=np.int64),
            teacher_units=np.zeros(batch, dtype=np.int64),
            scalars=np.zeros((batch, turns, capacity, 7), dtype=np.int16),
            roots=np.zeros(
                (batch, turns, capacity, self._contract.root_feature_count),
                dtype=np.float32,
            ),
            options=np.zeros(
                (batch, turns, capacity, self._contract.option_feature_count),
                dtype=np.int32,
            ),
            reservations=np.zeros(
                (batch, turns, capacity, self._contract.tile_count),
                dtype=np.int16,
            ),
            actions=np.zeros((batch, turns, capacity, 9), dtype=np.int64),
            masks=np.zeros(
                (batch, turns, capacity, compact_mask_width(self._contract)),
                dtype=np.bool_,
            ),
            quantity_max=np.zeros((batch, turns, capacity), dtype=np.int64),
            decision_counts=np.zeros((batch, turns), dtype=np.int16),
        )
        self._turn = 0

    def _compile_turn(
        self,
        group: _TeacherGroup,
        engines: Sequence[Any],
        players: NDArray[np.int64],
    ) -> tuple[TeacherProgramTurnBatch, float, float, float]:
        """Query and compile the native teacher without advancing engines."""
        started = time.perf_counter()
        group.teacher_tokens.fill(0)
        group.teacher_quantities.fill(0)
        group.teacher_counts.fill(0)
        group.teacher_units.fill(0)
        self._backend.kaito_v48_action_numeric_batch(
            list(engines),
            players,
            group.teacher_sessions,
            group.teacher_tokens,
            group.teacher_quantities,
            group.teacher_counts,
            group.teacher_units,
            self._workers,
        )
        action_seconds = time.perf_counter() - started
        compiler_started = time.perf_counter()
        trace = compile_teacher_program_turn_batch(
            self._backend,
            group.sessions,
            engines,
            players,
            group.teacher_tokens,
            group.teacher_quantities,
            group.teacher_counts,
            group.teacher_units,
            self._codec,
            self._contract,
            self._workers,
            group.repairs,
        )
        compiler_seconds = time.perf_counter() - compiler_started
        return (
            trace,
            time.perf_counter() - started,
            action_seconds,
            compiler_seconds,
        )

    def begin_turn(
        self,
        engines: Sequence[Any],
        players: NDArray[np.int64],
    ) -> None:
        """Submit teacher work after state encoding and before GPU inference."""
        group = self._active
        if group is None:
            raise RuntimeError("fused teacher turn lifecycle is invalid")
        if self._turn >= group.scalars.shape[1]:
            raise RuntimeError("fused teacher exceeded the official horizon")
        clone_started = time.perf_counter()
        snapshots = [engine.clone() for engine in engines]
        self.clone_seconds += time.perf_counter() - clone_started
        turn = self._turn
        self._turn += 1
        future = self._executor.submit(
            self._compile_turn,
            group,
            snapshots,
            players.copy(),
        )
        self._pending.append((group, turn, future))

    def _install(
        self,
        group: _TeacherGroup,
        turn: int,
        trace: TeacherProgramTurnBatch,
    ) -> None:
        """Store one completed turn without retaining its temporary arrays."""
        group.scalars[:, turn] = trace.scalars
        group.roots[:, turn] = trace.root_features
        group.options[:, turn] = trace.option_features
        group.reservations[:, turn] = trace.target_reservations
        group.actions[:, turn] = trace.actions
        group.masks[:, turn] = trace.conditional_masks
        group.quantity_max[:, turn] = trace.quantity_max
        group.decision_counts[:, turn] = trace.decision_counts

    def _drain(self, *, block: bool) -> None:
        """Install ordered teacher futures, optionally waiting for the tail."""
        while self._pending and (block or self._pending[0][2].done()):
            group, turn, future = self._pending[0]
            started = time.perf_counter()
            trace, elapsed, action_seconds, compiler_seconds = future.result()
            self.wait_seconds += time.perf_counter() - started
            self.native_seconds += elapsed
            self.action_seconds += action_seconds
            self.compiler_seconds += compiler_seconds
            self._install(group, turn, trace)
            self._pending.popleft()

    def finish_turn(self) -> None:
        """Install compiler outputs before the shared engines are advanced."""
        if self._active is None:
            raise RuntimeError("fused teacher has no pending turn")
        self._drain(block=False)

    def finish_group(self) -> None:
        """Publish a complete compiler group for immediate shard assembly."""
        group = self._active
        if group is None:
            raise RuntimeError("fused teacher group lifecycle is invalid")
        if self._turn != group.scalars.shape[1]:
            raise RuntimeError("fused teacher group ended before the official horizon")
        self._drain(block=True)
        self._completed.append(group)
        self._active = None
        self._turn = 0

    def translate(
        self,
        episodes: Sequence[ProgramEpisode],
    ) -> tuple[ProgramReplaySeat, ...]:
        """Join completed teacher programs to exact student behavior tensors."""
        rows = {
            key: (group, row)
            for group in self._completed
            for row, key in enumerate(group.keys)
        }
        if len(rows) != len(episodes) or any(
            (episode.seed, episode.seat) not in rows for episode in episodes
        ):
            raise ValueError("fused teacher outputs do not match student episodes")
        translated: list[ProgramReplaySeat] = []
        for episode in episodes:
            group, row = rows[(episode.seed, episode.seat)]
            translated.append(
                ProgramReplaySeat(
                    board=cast(
                        NDArray[np.float16],
                        to_numpy(episode.board, np.dtype(np.float16)),
                    ),
                    units=cast(
                        NDArray[np.float16],
                        to_numpy(episode.units, np.dtype(np.float16)),
                    ),
                    global_features=cast(
                        NDArray[np.float16],
                        to_numpy(episode.global_features, np.dtype(np.float16)),
                    ),
                    economic_state=cast(
                        NDArray[np.int32],
                        to_numpy(episode.economic_state, np.dtype(np.int32)),
                    ),
                    actions=cast(
                        NDArray[np.int64],
                        to_numpy(episode.actions, np.dtype(np.int64)),
                    ),
                    quantities=cast(
                        NDArray[np.int64],
                        to_numpy(episode.quantities, np.dtype(np.int64)),
                    ),
                    action_decision_counts=cast(
                        NDArray[np.int16],
                        to_numpy(episode.action_decision_counts, np.dtype(np.int16)),
                    ),
                    program_scalars=group.scalars[row],
                    program_root_features=group.roots[row],
                    program_option_features=group.options[row],
                    program_target_reservations=group.reservations[row],
                    program_actions=group.actions[row],
                    program_conditional_masks=group.masks[row],
                    program_quantity_max=group.quantity_max[row],
                    program_decision_counts=group.decision_counts[row],
                    outcome=episode.outcome,
                    statistics=dict(sorted(group.repairs[row].items())),
                )
            )
        self._completed.clear()
        return tuple(translated)

    def close(self) -> None:
        """Release the observer lane after no rollout turn remains active."""
        self._executor.shutdown(wait=True, cancel_futures=False)


__all__ = ["FusedTeacherCompiler"]
