"""Shared batched stepping against frozen native notebook opponents."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray

from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.portfolios.native import create_native_session


def create_native_opponent_session(opponent_id: str, maximum_market_orders: int) -> Any:
    """Create an active opponent; retired versions require their legacy modules."""
    return create_native_session(opponent_id, maximum_market_orders)


def step_native_opponent_batch(
    backend: BackendApi,
    engines: list[Any],
    candidate_players: NDArray[np.int64],
    opponent_ids: Sequence[str],
    opponent_sessions: list[Any],
    candidate_tokens: NDArray[np.int64],
    candidate_quantities: NDArray[np.int64],
    candidate_counts: NDArray[np.int64],
    candidate_units: NDArray[np.int64],
    workers: int,
) -> NDArray[np.bool_]:
    """Advance lockstep engines with numeric candidates and grouped opponents."""
    batch = len(engines)
    if not (
        len(candidate_players)
        == len(opponent_ids)
        == len(opponent_sessions)
        == candidate_tokens.shape[0]
        == candidate_quantities.shape[0]
        == len(candidate_counts)
        == len(candidate_units)
        == batch
    ):
        raise ValueError("native opponent batch inputs differ in length")
    if candidate_tokens.ndim != 2 or candidate_quantities.shape != candidate_tokens.shape:
        raise ValueError("native candidate action arrays must share a two-dimensional shape")

    width = candidate_tokens.shape[1]
    tokens = np.zeros((batch, 2, width), dtype=np.int64)
    quantities = np.zeros_like(tokens)
    decision_counts = np.zeros((batch, 2), dtype=np.int64)
    unit_counts = np.zeros((batch, 2), dtype=np.int64)
    rows = np.arange(batch)
    tokens[rows, candidate_players] = candidate_tokens
    quantities[rows, candidate_players] = candidate_quantities
    decision_counts[rows, candidate_players] = candidate_counts
    unit_counts[rows, candidate_players] = candidate_units
    done = np.zeros(batch, dtype=np.bool_)
    for opponent_id in dict.fromkeys(opponent_ids):
        indices = np.asarray(
            [index for index, value in enumerate(opponent_ids) if value == opponent_id],
            dtype=np.int64,
        )
        result = backend.native_opponent_batch_steps[opponent_id](
            [engines[int(index)] for index in indices],
            candidate_players[indices],
            [opponent_sessions[int(index)] for index in indices],
            tokens[indices],
            quantities[indices],
            decision_counts[indices],
            unit_counts[indices],
            min(workers, int(indices.size)),
        )
        done[indices] = np.asarray(result, dtype=np.bool_)
    return done


__all__ = ["create_native_opponent_session", "step_native_opponent_batch"]
