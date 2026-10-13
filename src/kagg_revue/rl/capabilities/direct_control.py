"""Frozen DIRECT control matches for capability policy-gradient variance reduction."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.kaito.native import create_native_session as kaito_session
from kagg_revue.opponents.native_batch import (
    create_native_opponent_session,
    step_native_opponent_batch,
)


@dataclass(frozen=True)
class DirectControlResult:
    """Official terminal outcomes from an action-independent DIRECT policy."""

    outcomes: NDArray[np.float32]
    terminal_cash: NDArray[np.float64]
    opponent_cash: NDArray[np.float64]
    primitive_turns: int
    elapsed_seconds: float


def create_opponent_session(opponent_id: str, maximum_market_orders: int) -> Any:
    """Create one source-authenticated native opponent state."""
    return create_native_opponent_session(opponent_id, maximum_market_orders)


def collect_paired_direct_control(
    backend: BackendApi,
    environment: Mapping[str, object],
    jobs: Sequence[tuple[int, int, str]],
    *,
    maximum_market_orders: int,
    cpu_workers: int,
) -> DirectControlResult:
    """Run Kaito DIRECT on the same seed, seat and frozen opponent as each job."""
    if not jobs:
        raise ValueError("paired DIRECT control needs at least one rollout job")
    engines = [
        backend.engine(seed=int(seed), configuration=environment) for seed, _seat, _opponent in jobs
    ]
    seats = np.asarray([seat for _seed, seat, _opponent in jobs], dtype=np.int64)
    opponent_ids = tuple(opponent for _seed, _seat, opponent in jobs)
    direct_sessions = [kaito_session(maximum_market_orders) for _ in jobs]
    opponent_sessions = [
        create_opponent_session(opponent_id, maximum_market_orders) for opponent_id in opponent_ids
    ]
    width = maximum_market_orders + 65
    tokens = np.zeros((len(jobs), width), dtype=np.int64)
    quantities = np.zeros_like(tokens)
    decision_counts = np.zeros(len(jobs), dtype=np.int64)
    unit_counts = np.zeros(len(jobs), dtype=np.int64)
    done = np.zeros(len(jobs), dtype=np.bool_)
    primitive_turns = 0
    started = time.perf_counter()
    while not bool(done.all()):
        step = int(engines[0].step_index)
        if any(int(engine.step_index) != step for engine in engines):
            raise RuntimeError("paired DIRECT control lanes lost lockstep")
        tokens.fill(0)
        quantities.fill(0)
        decision_counts.fill(0)
        unit_counts.fill(0)
        backend.kaito_v48_action_numeric_batch(
            engines,
            seats,
            direct_sessions,
            tokens,
            quantities,
            decision_counts,
            unit_counts,
            cpu_workers,
        )
        done = step_native_opponent_batch(
            backend,
            engines,
            seats,
            opponent_ids,
            opponent_sessions,
            tokens,
            quantities,
            decision_counts,
            unit_counts,
            cpu_workers,
        )
        primitive_turns += len(jobs)

    terminal_cash = np.asarray(
        [engine.money(int(seat)) for engine, seat in zip(engines, seats, strict=True)],
        dtype=np.float64,
    )
    opponent_cash = np.asarray(
        [engine.money(1 - int(seat)) for engine, seat in zip(engines, seats, strict=True)],
        dtype=np.float64,
    )
    outcomes = np.sign(terminal_cash - opponent_cash).astype(np.float32, copy=False)
    return DirectControlResult(
        outcomes=outcomes,
        terminal_cash=terminal_cash,
        opponent_cash=opponent_cash,
        primitive_turns=primitive_turns,
        elapsed_seconds=time.perf_counter() - started,
    )


__all__ = [
    "DirectControlResult",
    "collect_paired_direct_control",
    "create_opponent_session",
]
