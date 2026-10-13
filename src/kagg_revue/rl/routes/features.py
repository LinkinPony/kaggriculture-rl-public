"""Actor-visible pooled observations for sparse route decisions."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from kagg_revue.core.backend import BackendApi
from kagg_revue.rl.routes.contract import ROUTE_DECISIONS

ROUTE_FEATURE_WIDTH = 572


def pool_route_features(
    raw_board: Any,
    raw_units: Any,
    raw_globals: Any,
    *,
    decision_index: int,
    candidate_route: int,
    prior_actions: NDArray[np.int64],
    unit_limit: int,
) -> NDArray[np.float32]:
    """Pool actor-observation-v2 arrays from either native or official state."""
    board = np.asarray(raw_board, dtype=np.float32)
    units = np.asarray(raw_units, dtype=np.float32)
    globals_ = np.asarray(raw_globals, dtype=np.float32)
    batch = board.shape[0] if board.ndim else 0
    if prior_actions.shape != (batch,):
        raise ValueError("route prior actions differ from observation batch")
    if not 0 <= decision_index < len(ROUTE_DECISIONS):
        raise ValueError("route decision index is outside the contract")
    if not 0 <= candidate_route < 6:
        raise ValueError("candidate route is outside the Kaito portfolio")
    if board.ndim != 5 or board.shape[:2] != (batch, 2):
        raise ValueError("route board observation has an unexpected shape")
    if units.ndim != 4 or units.shape[:2] != (batch, 2):
        raise ValueError("route unit observation has an unexpected shape")
    if globals_.shape != (batch, 82) or units.shape[-1] != 60 or board.shape[2] != 29:
        raise ValueError("route observation differs from actor-observation-v2")

    board_mean = board.mean(axis=(-2, -1))
    board_max = board.max(axis=(-2, -1))
    valid = units[..., :1] > 0.5
    counts = valid.sum(axis=2, dtype=np.float32)
    safe_counts = np.maximum(counts, 1.0)
    unit_mean = (units * valid).sum(axis=2) / safe_counts
    masked_units = np.where(valid, units, -np.inf)
    unit_max = masked_units.max(axis=2)
    unit_max[~np.isfinite(unit_max)] = 0.0
    farmer = units[:, :, 0, :]

    decision = np.zeros((batch, len(ROUTE_DECISIONS)), dtype=np.float32)
    decision[:, decision_index] = 1.0
    route = np.zeros((batch, 6), dtype=np.float32)
    route[:, candidate_route] = 1.0
    prior = prior_actions.astype(np.float32, copy=False)[:, None]
    features = np.concatenate(
        (
            board_mean.reshape(batch, -1),
            board_max.reshape(batch, -1),
            farmer.reshape(batch, -1),
            unit_mean.reshape(batch, -1),
            unit_max.reshape(batch, -1),
            (counts / float(unit_limit)).reshape(batch, -1),
            globals_,
            decision,
            route,
            prior,
        ),
        axis=1,
        dtype=np.float32,
    )
    if features.shape != (batch, ROUTE_FEATURE_WIDTH):
        raise RuntimeError(f"route feature width drifted: {features.shape}")
    if not np.isfinite(features).all():
        raise ValueError("route features contain non-finite values")
    return features


def encode_route_features(
    backend: BackendApi,
    engines: list[Any],
    players: NDArray[np.int64],
    *,
    decision_index: int,
    candidate_route: int,
    prior_actions: NDArray[np.int64],
    unit_limit: int,
    workers: int,
) -> NDArray[np.float32]:
    """Pool the official actor observation without adding hidden state."""
    batch = len(engines)
    if batch < 1 or players.shape != (batch,) or prior_actions.shape != (batch,):
        raise ValueError("route feature inputs must be aligned and nonempty")
    policy_batch = backend.engine_policy_session_batch(
        engines,
        [int(player) for player in players],
        unit_limit,
        min(workers, batch),
    )
    raw_board, raw_units, raw_globals = policy_batch.encode()
    return pool_route_features(
        raw_board,
        raw_units,
        raw_globals,
        decision_index=decision_index,
        candidate_route=candidate_route,
        prior_actions=prior_actions,
        unit_limit=unit_limit,
    )


__all__ = ["ROUTE_FEATURE_WIDTH", "encode_route_features", "pool_route_features"]
