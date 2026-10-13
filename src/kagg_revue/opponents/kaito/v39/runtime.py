"""Episode-local runtime for the frozen Kaito v39 behavior."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from kagg_revue.opponents.kaito.v39.native import create_native_session
from kagg_revue.opponents.public import PublicAgentRecord


class KaitoV39Runtime:
    """Native-first v39 runtime with a lazy artifact diagnostic path."""

    native_rollout_required = True
    native_batch_kind = "kaito_v39"

    def __init__(
        self,
        record: PublicAgentRecord,
        repository_root: Path,
        configuration: Mapping[str, Any],
    ) -> None:
        """Create native state without importing or decoding the notebook."""
        self._record = record
        self._repository_root = repository_root
        self._configuration = dict(configuration)
        self._reference: Any | None = None
        maximum_orders = int(configuration.get("maxMarketOrdersPerTurn", 10) or 10)
        self._native_session = create_native_session(maximum_orders)

    @property
    def native_session(self) -> Any:
        """Return episode-local state for direct native-engine rollout."""
        return self._native_session

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Use the frozen artifact only when an observation-only diagnostic asks."""
        if self._reference is None:
            from kagg_revue.opponents.public import PublicAgentRuntime

            self._reference = PublicAgentRuntime(
                self._record,
                self._repository_root,
                self._configuration,
            )
        result = self._reference.act(observation)
        if not isinstance(result, dict):
            raise TypeError("Kaito v39 reference returned a non-dict action")
        return result

    def close(self) -> None:
        """Release no-op episode state through the common agent protocol."""


__all__ = ["KaitoV39Runtime"]
