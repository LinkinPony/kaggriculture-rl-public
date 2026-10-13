"""Construction boundary for the source-authenticated native v39 portfolio."""

from __future__ import annotations

from functools import cache
from typing import Any

from kagg_revue.native import _revue_native
from kagg_revue.opponents.kaito.v39.asset import portfolio_arrays


@cache
def _portfolio(maximum_market_orders: int) -> Any:
    if maximum_market_orders < 1:
        raise ValueError("maximum market orders must be positive")
    arrays = portfolio_arrays()
    return _revue_native.KaitoV39Portfolio(
        arrays["tokens"],
        arrays["quantities"],
        arrays["decision_counts"],
        arrays["unit_counts"],
        arrays["parts_layout"],
        arrays["parts_numeric"],
        arrays["parts_actor_lengths"],
        arrays["parts_unlocks"],
        arrays["parts_shop_counts"],
        arrays["parts_seats"],
        arrays["nested_indices"],
        arrays["nested_margins"],
        arrays["fallback_indices"],
        arrays["fallback_margins"],
        arrays["stage1_indices"],
        arrays["stage1_margins"],
        arrays["stage2_indices"],
        arrays["stage2_margins"],
        maximum_market_orders,
    )


def create_native_session(maximum_market_orders: int) -> Any:
    """Create episode-local v39 state sharing one immutable portfolio."""
    return _revue_native.KaitoV39Session(_portfolio(maximum_market_orders))


def native_action(session: Any, engine: Any, player: int) -> dict[str, Any]:
    """Evaluate v39 directly from one native engine for diagnostics."""
    return _revue_native.kaito_v39_action(engine, player, session)


__all__ = ["create_native_session", "native_action"]

