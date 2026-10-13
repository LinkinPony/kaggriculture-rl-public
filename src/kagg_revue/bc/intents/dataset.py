"""Authenticated compact shards for canonical-intent behavior cloning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.rl.intents.data import IntentRolloutBatch

_BASE_FIELDS = (
    "board",
    "units",
    "global_features",
    "economic_state",
    "actions",
    "quantities",
    "decision_counts",
    "outcomes",
    "seeds",
    "seats",
    "terminal_cash",
    "opponent_cash",
    "route_codes",
    "first_event_days",
    "bucket_widths",
)
_DECISION_FIELDS = (
    "candidate_fields",
    "candidate_features",
    "candidate_mask",
    "ledger",
    "status",
    "work_priorities",
    "work_orders",
    "work_mask",
    "positions",
    "market_prefix",
    "phase",
    "candidate_counts",
    "work_counts",
    "market_counts",
    "selected",
    "selected_canonical_id",
    "episode_index",
    "turn_index",
)


class IntentTeacherShard(BaseModel):
    """Immutable identity and direct diagnostics for one complete-game shard."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int = Field(ge=0)
    path: str = Field(min_length=1)
    seed_start: int = Field(ge=0)
    games: int = Field(gt=0)
    episodes: int = Field(gt=0)
    turns_per_episode: int = Field(gt=0)
    decisions: int = Field(gt=0)
    maximum_transaction_steps: int = Field(gt=0)
    bucket_widths: tuple[int, ...] = Field(min_length=1)
    terminal_cash_sum: float
    opponent_cash_sum: float
    better: int = Field(ge=0)
    ties: int = Field(ge=0)
    worse: int = Field(ge=0)
    clipped_market_quantities: int = Field(ge=0)
    omitted_sell_orders: int = Field(ge=0)
    replaced_unavailable_sell_slots: int = Field(default=0, ge=0)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_counts(self) -> IntentTeacherShard:
        """Keep paired perspectives and terminal outcomes complete."""
        if self.episodes != 2 * self.games:
            raise ValueError("intent teacher shard must retain both seats")
        if self.better + self.ties + self.worse != self.episodes:
            raise ValueError("intent teacher shard outcomes do not cover every episode")
        if tuple(sorted(set(self.bucket_widths))) != self.bucket_widths:
            raise ValueError("intent teacher bucket widths must be unique and ordered")
        return self


class IntentTeacherManifest(BaseModel):
    """Artifact and ABI identities required to consume intent BC labels."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["canonical-intent-teacher-dataset-v1"]
    dataset_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    generated_at: str = Field(min_length=1)
    source: dict[str, object]
    native_backend: dict[str, object]
    teacher: dict[str, object]
    intent_abi_version: str = Field(min_length=1)
    intent_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    actor_encoder_version: str = Field(min_length=1)
    action_codec_version: str = Field(min_length=1)
    unit_limit: int = Field(gt=0)
    max_transaction_steps: int = Field(gt=1)
    environment: dict[str, object]
    collection: dict[str, object]
    route_codes: dict[str, int]
    shards: tuple[IntentTeacherShard, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_shards(self) -> IntentTeacherManifest:
        """Require one ordered, non-overlapping complete seed range."""
        expected_seed = min(shard.seed_start for shard in self.shards)
        for expected_index, shard in enumerate(self.shards):
            if shard.index != expected_index or shard.seed_start != expected_seed:
                raise ValueError("intent teacher shards are not contiguous and ordered")
            expected_seed += shard.games
        if set(self.route_codes.values()) != set(range(len(self.route_codes))):
            raise ValueError("intent teacher route codes must be dense")
        return self


@dataclass(frozen=True, slots=True)
class LoadedIntentTeacherShard:
    """One authenticated shard in the current RL rollout representation."""

    batch: IntentRolloutBatch
    seeds: NDArray[np.int64]
    seats: NDArray[np.uint8]
    terminal_cash: NDArray[np.float64]
    opponent_cash: NDArray[np.float64]
    route_codes: NDArray[np.uint8]
    first_event_days: NDArray[np.int16]


def pack_intent_teacher_arrays(
    *,
    base: dict[str, NDArray[np.generic]],
    decisions: list[dict[str, Any]],
) -> dict[str, NDArray[np.generic]]:
    """Pack native width buckets without rollout-wide padding."""
    missing = set(_BASE_FIELDS) - set(base)
    if missing:
        raise ValueError(f"intent teacher base arrays are incomplete: {sorted(missing)}")
    arrays = {name: np.asarray(base[name]) for name in _BASE_FIELDS}
    widths = np.asarray(arrays["bucket_widths"], dtype=np.int32)
    if len(decisions) != len(widths):
        raise ValueError("intent teacher bucket metadata differs from native tape")
    for index, payload in enumerate(decisions):
        for field in _DECISION_FIELDS:
            if field not in payload:
                raise ValueError(f"intent teacher native bucket lacks {field}")
            arrays[f"bucket_{index:03d}_{field}"] = np.asarray(payload[field])
    return arrays


def _load_arrays(path: Path, bucket_count: int) -> dict[str, NDArray[np.generic]]:
    with np.load(path, allow_pickle=False) as archive:
        expected = set(_BASE_FIELDS)
        expected.update(
            f"bucket_{index:03d}_{field}"
            for index in range(bucket_count)
            for field in _DECISION_FIELDS
        )
        if set(archive.files) != expected:
            raise ValueError(f"intent teacher shard fields differ: {path}")
        return {name: np.asarray(archive[name]) for name in archive.files}


def load_intent_teacher_shard(
    dataset_dir: Path,
    shard: IntentTeacherShard,
) -> LoadedIntentTeacherShard:
    """Authenticate and load one shard as the current intent learner ABI."""
    path = (dataset_dir / shard.path).resolve()
    root = dataset_dir.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("intent teacher shard escaped its dataset")
    if path.stat().st_size != shard.size_bytes or sha256_file(path) != shard.sha256:
        raise ValueError(f"intent teacher shard identity differs: {path}")
    arrays = _load_arrays(path, len(shard.bucket_widths))
    decisions: list[dict[str, Any]] = []
    for index, width in enumerate(shard.bucket_widths):
        payload = {field: arrays[f"bucket_{index:03d}_{field}"] for field in _DECISION_FIELDS}
        counts = np.asarray(payload["candidate_counts"], dtype=np.int64)
        if counts.size == 0 or int(counts.max()) > width:
            raise ValueError("intent teacher candidate count exceeds its bucket")
        rows = counts.shape[0]
        payload["old_log_probability"] = np.zeros(rows, dtype=np.float32)
        payload["old_value"] = np.zeros(rows, dtype=np.float32)
        payload["policy_mask"] = counts > 1
        decisions.append(payload)
    batch = IntentRolloutBatch.from_native_buckets(
        board=cast(NDArray[np.float16], arrays["board"]),
        units=cast(NDArray[np.float16], arrays["units"]),
        global_features=cast(NDArray[np.float32], arrays["global_features"]),
        economic_state=cast(NDArray[np.int32], arrays["economic_state"]),
        actions=np.asarray(arrays["actions"], dtype=np.int64),
        quantities=np.asarray(arrays["quantities"], dtype=np.int64),
        decision_counts=np.asarray(arrays["decision_counts"], dtype=np.int64),
        decisions=decisions,
        outcomes=np.asarray(arrays["outcomes"], dtype=np.float32),
    )
    if (
        batch.episode_count != shard.episodes
        or batch.decision_count != shard.decisions
        or int(batch.board.shape[1]) != shard.turns_per_episode
    ):
        raise ValueError("intent teacher shard dimensions differ from its manifest")
    return LoadedIntentTeacherShard(
        batch=batch,
        seeds=np.asarray(arrays["seeds"], dtype=np.int64),
        seats=np.asarray(arrays["seats"], dtype=np.uint8),
        terminal_cash=np.asarray(arrays["terminal_cash"], dtype=np.float64),
        opponent_cash=np.asarray(arrays["opponent_cash"], dtype=np.float64),
        route_codes=np.asarray(arrays["route_codes"], dtype=np.uint8),
        first_event_days=np.asarray(arrays["first_event_days"], dtype=np.int16),
    )


def load_intent_teacher_manifest(dataset_dir: Path) -> IntentTeacherManifest:
    """Load one strict canonical-intent teacher manifest."""
    path = dataset_dir.resolve() / "manifest.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    return IntentTeacherManifest.model_validate(value)


__all__ = [
    "IntentTeacherManifest",
    "IntentTeacherShard",
    "LoadedIntentTeacherShard",
    "load_intent_teacher_manifest",
    "load_intent_teacher_shard",
    "pack_intent_teacher_arrays",
]
