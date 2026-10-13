"""Exact-source registry for trusted training-time opponent implementations."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol

from kagg_revue.opponents.portfolios.catalog import SOURCES, Source
from kagg_revue.opponents.portfolios.native import ASSET_SHA256
from kagg_revue.opponents.public import PublicAgentRecord, resolve_public_agent_path


class TrustedAgentRuntime(Protocol):
    """Episode-local runtime allowed to execute inside the trainer process."""

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return one official-format action."""

    def close(self) -> None:
        """Release any episode-local resources."""


def _runtime_spec(record: PublicAgentRecord) -> Source | None:
    for spec in SOURCES:
        if (
            record.agent_id == spec.agent_id
            and record.notebook_ref == spec.notebook_ref
            and record.sha256 == spec.sha256
            and record.files == dict(spec.files)
            and record.entrypoint == spec.entrypoint
        ):
            return spec
    return None


def trusted_runtime_identity(record: PublicAgentRecord) -> dict[str, object] | None:
    """Return the derived identity only for the exact frozen source artifact."""
    spec = _runtime_spec(record)
    if spec is None:
        return None
    return {
        "implementation": f"native-{spec.agent_id}-v1",
        "source_artifact_sha256": spec.sha256,
        "portfolio_asset_sha256": ASSET_SHA256[spec.agent_id],
        "process_isolated": False,
    }


def create_trusted_runtime(
    record: PublicAgentRecord,
    repository_root: Path,
    configuration: Mapping[str, Any],
) -> TrustedAgentRuntime | None:
    """Create a source-authenticated runtime, importing its code lazily."""
    spec = _runtime_spec(record)
    if spec is None:
        return None
    resolve_public_agent_path(record, repository_root)
    from kagg_revue.opponents.portfolios.runtime import NativeRuntime

    return NativeRuntime(spec.agent_id, configuration)


__all__ = ["TrustedAgentRuntime", "create_trusted_runtime", "trusted_runtime_identity"]
