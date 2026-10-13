"""Construction boundary for the source-authenticated native portfolio."""

from __future__ import annotations

from functools import cache
from typing import Any

from kagg_revue.native import _revue_native
from kagg_revue.opponents.boatlee.asset import load_portfolio


@cache
def _portfolio(maximum_market_orders: int) -> Any:
    if maximum_market_orders < 1:
        raise ValueError("maximum market orders must be positive")
    tokens, quantities, decision_counts, unit_counts = load_portfolio()
    return _revue_native.BoatleeV21Portfolio(
        tokens,
        quantities,
        decision_counts,
        unit_counts,
        maximum_market_orders,
    )


def create_native_session(maximum_market_orders: int) -> Any:
    """Create fresh episode state sharing one immutable decoded portfolio."""
    return _revue_native.BoatleeV21Session(_portfolio(maximum_market_orders))


def native_action(session: Any, engine: Any, player: int) -> dict[str, Any]:
    """Expose direct-engine evaluation for conformance diagnostics."""
    return _revue_native.boatlee_v21_action(engine, player, session)


__all__ = ["create_native_session", "native_action"]
