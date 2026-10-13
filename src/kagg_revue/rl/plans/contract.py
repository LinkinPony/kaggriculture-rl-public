"""Immutable semantic identities for structured-plan PPO artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

PLAN_RECORD_SCHEMA_VERSION = "structured-plan-transition-v2"


def _identity(value: str, name: str) -> str:
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a nonempty canonical identity")
    return value


@dataclass(frozen=True)
class PlanVersionContract:
    """Exact language, observation, grammar, executor, and record semantics."""

    language_version: str
    observation_version: str
    grammar_version: str
    executor_version: str
    record_schema_version: str = PLAN_RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Reject an artifact whose semantics contain an implicit identity."""
        for name, value in self.payload().items():
            _identity(value, name)

    def payload(self) -> dict[str, str]:
        """Return the canonical serializable version map."""
        return {
            "record_schema_version": self.record_schema_version,
            "language_version": self.language_version,
            "observation_version": self.observation_version,
            "grammar_version": self.grammar_version,
            "executor_version": self.executor_version,
        }

    @property
    def fingerprint(self) -> str:
        """Return one stable fingerprint for rollout/checkpoint compatibility."""
        encoded = json.dumps(
            self.payload(),
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        return hashlib.sha256(encoded).hexdigest()

    def require_compatible(self, other: PlanVersionContract) -> None:
        """Require exact semantics rather than applying an implicit migration."""
        if self != other:
            raise ValueError(
                "structured-plan version contracts differ: "
                f"expected={self.fingerprint}, actual={other.fingerprint}"
            )


__all__ = ["PLAN_RECORD_SCHEMA_VERSION", "PlanVersionContract"]
