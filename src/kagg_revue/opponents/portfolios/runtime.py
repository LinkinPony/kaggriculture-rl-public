"""Common native-only runtime for the active public script population."""

from collections.abc import Mapping
from typing import Any, NoReturn

from kagg_revue.opponents.portfolios.native import create_native_session


class NativeRuntime:
    """Bind an authenticated source identity to an isolated C++ session."""

    native_rollout_required = True

    def __init__(self, agent_id: str, configuration: Mapping[str, Any]) -> None:
        """Create mutable episode state with shared immutable route data."""
        self.native_batch_kind = agent_id
        maximum_orders = int(configuration.get("maxMarketOrdersPerTurn", 10) or 10)
        self.native_session = create_native_session(agent_id, maximum_orders)

    def act(self, observation: Mapping[str, Any]) -> NoReturn:
        """Require the direct native-engine boundary used by batched training."""
        del observation
        raise RuntimeError(f"{self.native_batch_kind} requires a native engine session")

    def close(self) -> None:
        """Release no external resources."""
