"""Construction boundary for the source-authenticated native portfolio."""

from __future__ import annotations

from functools import cache
from typing import Any

from kagg_revue.native import _revue_native
from kagg_revue.opponents.mugundh.asset import load_portfolio


@cache
def _portfolio() -> Any:
    tokens, quantities, decision_counts, unit_counts = load_portfolio()
    return _revue_native.MugundhV21Portfolio(
        tokens,
        quantities,
        decision_counts,
        unit_counts,
    )


def create_native_session() -> Any:
    """Create fresh episode state sharing one immutable decoded portfolio."""
    return _revue_native.MugundhV21Session(_portfolio())


def native_action(session: Any, engine: Any, player: int) -> dict[str, Any]:
    """Expose direct-engine evaluation for conformance diagnostics."""
    return _revue_native.mugundh_v21_action(engine, player, session)


__all__ = ["create_native_session", "native_action"]
