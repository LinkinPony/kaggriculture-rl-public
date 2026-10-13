"""Immutable identities for capability proposal, search, and execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

CAPABILITY_RECORD_SCHEMA_VERSION = "capability-search-record-v1"


def _require_identity(value: str, name: str) -> str:
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a nonempty canonical identity")
    return value


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class CapabilityVersionContract:
    """Exact ABI versions that give a stored macro choice its meaning.

    Versions are opaque identities rather than ordered semantic versions. A
    rollout collected with a different proposal, search, or executor ABI must
    not be silently replayed under the current implementation.
    """

    proposal_version: str
    search_version: str
    executor_version: str
    record_schema_version: str = CAPABILITY_RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Reject incomplete identities before a rollout can be recorded."""
        for name in (
            "proposal_version",
            "search_version",
            "executor_version",
            "record_schema_version",
        ):
            _require_identity(str(getattr(self, name)), name)

    def payload(self) -> dict[str, str]:
        """Return the canonical serializable contract."""
        return {
            "record_schema_version": self.record_schema_version,
            "proposal_version": self.proposal_version,
            "search_version": self.search_version,
            "executor_version": self.executor_version,
        }

    @property
    def fingerprint(self) -> str:
        """Return one stable identity for artifact and batch contracts."""
        return _fingerprint(self.payload())

    def require_compatible(self, other: CapabilityVersionContract) -> None:
        """Require exact semantics rather than attempting an implicit migration."""
        if self != other:
            raise ValueError(
                "capability version contracts differ: "
                f"expected={self.fingerprint}, actual={other.fingerprint}"
            )


@dataclass(frozen=True)
class FrozenSearchContext:
    """All immutable identities used to construct and score one candidate set.

    ``actor_visible_state_id`` deliberately identifies the actor-visible
    history rather than a privileged engine state. Snapshot identities bind
    resolved parameters/configuration, while the version contract binds their
    ABI. The search seed is retained so a candidate set can be audited without
    regenerating it during PPO.
    """

    contract: CapabilityVersionContract
    actor_visible_state_id: str
    proposal_snapshot_id: str
    search_snapshot_id: str
    executor_snapshot_id: str
    opponent_population_id: str
    continuation_policy_id: str
    search_seed: int
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Canonicalize immutable metadata and validate every artifact identity."""
        for name in (
            "actor_visible_state_id",
            "proposal_snapshot_id",
            "search_snapshot_id",
            "executor_snapshot_id",
            "opponent_population_id",
            "continuation_policy_id",
        ):
            _require_identity(str(getattr(self, name)), name)
        if self.search_seed < 0:
            raise ValueError("capability search seed must be non-negative")
        normalized = tuple(
            sorted((_require_identity(key, "metadata key"), value) for key, value in self.metadata)
        )
        if len({key for key, _ in normalized}) != len(normalized):
            raise ValueError("capability search metadata keys must be unique")
        for _, value in normalized:
            _require_identity(value, "metadata value")
        object.__setattr__(self, "metadata", normalized)

    def payload(self) -> dict[str, object]:
        """Return the canonical complete context used for fingerprinting."""
        return {
            "contract": self.contract.payload(),
            "actor_visible_state_id": self.actor_visible_state_id,
            "proposal_snapshot_id": self.proposal_snapshot_id,
            "search_snapshot_id": self.search_snapshot_id,
            "executor_snapshot_id": self.executor_snapshot_id,
            "opponent_population_id": self.opponent_population_id,
            "continuation_policy_id": self.continuation_policy_id,
            "search_seed": self.search_seed,
            "metadata": dict(self.metadata),
        }

    @property
    def fingerprint(self) -> str:
        """Return the exact per-decision frozen-context identity."""
        return _fingerprint(self.payload())

    @property
    def batch_contract(self) -> tuple[str, ...]:
        """Return identities that must remain frozen across one PPO batch."""
        return (
            self.contract.fingerprint,
            self.proposal_snapshot_id,
            self.search_snapshot_id,
            self.executor_snapshot_id,
            self.opponent_population_id,
            self.continuation_policy_id,
        )

    def require_batch_compatible(self, other: FrozenSearchContext) -> None:
        """Reject a minibatch that mixes behavior/search/executor snapshots."""
        if self.batch_contract != other.batch_contract:
            raise ValueError("capability PPO batch mixes frozen search contexts")


__all__ = [
    "CAPABILITY_RECORD_SCHEMA_VERSION",
    "CapabilityVersionContract",
    "FrozenSearchContext",
]
