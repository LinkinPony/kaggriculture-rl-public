"""Construction boundary for the source-authenticated native v48 portfolio."""

from __future__ import annotations

from functools import cache
from typing import Any

import numpy as np
from numpy.typing import NDArray

from kagg_revue.bc.actions import EncodedTurnAction, ReplayActionEncoder
from kagg_revue.native import _revue_native
from kagg_revue.opponents.kaito.routes import ROUTE_LENGTH, ROUTE_NAMES, ROUTES


@cache
def _portfolio(maximum_market_orders: int) -> Any:
    if maximum_market_orders < 1:
        raise ValueError("maximum market orders must be positive")
    encoder = ReplayActionEncoder(_revue_native.action_codec_spec())
    rows: list[list[EncodedTurnAction]] = []
    width = 1
    for route_name in ROUTE_NAMES:
        route: list[EncodedTurnAction] = []
        for step in range(ROUTE_LENGTH):
            action = ROUTES.action(route_name, step)
            unit_count = 1 + len(action.get("hands", []))
            encoded = encoder.encode(
                action,
                unit_count=unit_count,
                max_market_orders=maximum_market_orders,
            )
            route.append(encoded)
            width = max(width, len(encoded.tokens))
        rows.append(route)

    shape = (len(ROUTE_NAMES), ROUTE_LENGTH, width)
    tokens: NDArray[np.int64] = np.zeros(shape, dtype=np.int64)
    quantities: NDArray[np.int64] = np.zeros(shape, dtype=np.int64)
    decision_counts: NDArray[np.int64] = np.empty(shape[:2], dtype=np.int64)
    unit_counts: NDArray[np.int64] = np.empty(shape[:2], dtype=np.int64)
    for route_index, route in enumerate(rows):
        for step, encoded in enumerate(route):
            count = len(encoded.tokens)
            tokens[route_index, step, :count] = encoded.tokens
            quantities[route_index, step, :count] = encoded.quantities
            decision_counts[route_index, step] = count
            unit_counts[route_index, step] = encoded.unit_decisions
    return _revue_native.KaitoV48Portfolio(
        tokens,
        quantities,
        decision_counts,
        unit_counts,
        maximum_market_orders,
    )


def create_native_session(maximum_market_orders: int) -> Any:
    """Create episode-local state sharing one immutable decoded route library."""
    return _revue_native.KaitoV48Session(_portfolio(maximum_market_orders))


def native_action(session: Any, engine: Any, player: int) -> dict[str, Any]:
    """Expose the direct-engine path for conformance diagnostics."""
    return _revue_native.kaito_v48_action(engine, player, session)


__all__ = ["create_native_session", "native_action"]
