"""Episode-local native runtime for the frozen Mugundh v21 behavior."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, NoReturn

from kagg_revue.opponents.mugundh.native import create_native_session


class MugundhV21Runtime:
    """Native-only runtime with no Python observation fallback."""

    native_rollout_required = True
    native_batch_kind = "mugundh_v21"

    def __init__(self, configuration: Mapping[str, Any]) -> None:
        """Create isolated state after validating the supported market width."""
        raw_maximum_orders = configuration.get("maxMarketOrdersPerTurn", 10)
        maximum_orders = 10 if raw_maximum_orders is None else int(raw_maximum_orders)
        if maximum_orders < 1:
            raise ValueError("maximum market orders must be positive")
        self._native_session = create_native_session()

    @property
    def native_session(self) -> Any:
        """Return episode-local state for the direct native-engine hot path."""
        return self._native_session

    def act(self, observation: Mapping[str, Any]) -> NoReturn:
        """Fail closed because equivalence requires the native engine state."""
        del observation
        raise RuntimeError("Mugundh v21 is available only through its native engine session")

    def close(self) -> None:
        """Release no-op episode state through the common runtime protocol."""


__all__ = ["MugundhV21Runtime"]
