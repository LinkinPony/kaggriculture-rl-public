"""Episode-local native runtime for the frozen Boatlee v21 behavior."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, NoReturn

from kagg_revue.opponents.boatlee.native import create_native_session


class BoatleeV21Runtime:
    """Native-only runtime with no Python observation fallback."""

    native_rollout_required = True
    native_batch_kind = "boatlee_v21"

    def __init__(self, configuration: Mapping[str, Any]) -> None:
        """Create one isolated portfolio-routing session."""
        maximum_orders = int(configuration.get("maxMarketOrdersPerTurn", 10) or 10)
        self._native_session = create_native_session(maximum_orders)

    @property
    def native_session(self) -> Any:
        """Return episode-local state for the direct native-engine hot path."""
        return self._native_session

    def act(self, observation: Mapping[str, Any]) -> NoReturn:
        """Fail closed because equivalence requires the native engine state."""
        del observation
        raise RuntimeError("Boatlee v21 is available only through its native engine session")

    def close(self) -> None:
        """Release no-op episode state through the common runtime protocol."""


__all__ = ["BoatleeV21Runtime"]
