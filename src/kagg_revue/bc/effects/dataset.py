"""Authenticated compact shards for atomic-effect behavior cloning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.rl.effects.data import EffectRolloutBatch

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
    "jobs",
    "job_counts",
    "work_prefix",
    "work_counts",
    "market_prefix",
    "market_counts",
    "previous_action",
    "previous_counts",
    "phase",
    "work_limit",
    "candidate_counts",
    "selected",
    "selected_canonical_id",
    "policy_mask",
    "value_mask",
    "episode_index",
    "turn_index",
)


class EffectTeacherShard(BaseModel):
    """Immutable identity and direct outcomes for one paired-seat shard."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int = Field(ge=0)
    shard_id: str | None = Field(default=None, min_length=1)
    path: str = Field(min_length=1)
    partition: Literal["train", "validation", "test"] | None = None
    source_group: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]*$")
    seed_start: int = Field(ge=0)
    games: int = Field(gt=0)
    physical_games: int | None = Field(default=None, gt=0)
    episodes: int = Field(gt=0)
    turns_per_episode: int = Field(gt=0)
    factors: int = Field(gt=0)
    policy_factors: int = Field(gt=0)
    maximum_transaction_steps: int = Field(gt=0)
    bucket_widths: tuple[int, ...] = Field(min_length=1)
    terminal_cash_sum: float
    opponent_cash_sum: float
    better: int = Field(ge=0)
    ties: int = Field(ge=0)
    worse: int = Field(ge=0)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_counts(self) -> EffectTeacherShard:
        """Keep paired perspectives and terminal outcomes complete."""
        if self.episodes != 2 * self.games:
            raise ValueError("effect teacher shard must retain both seats")
        if self.physical_games is not None and self.physical_games < self.games:
            raise ValueError("effect teacher physical games cannot be below paired groups")
        if self.better + self.ties + self.worse != self.episodes:
            raise ValueError("effect teacher shard outcomes do not cover every episode")
        if self.policy_factors > self.factors:
            raise ValueError("effect teacher policy factors exceed all factors")
        if tuple(sorted(set(self.bucket_widths))) != self.bucket_widths:
            raise ValueError("effect teacher bucket widths must be unique and ordered")
        return self


class EffectTeacherManifest(BaseModel):
    """Artifact and ABI identities required to consume effect BC labels."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[
        "atomic-effect-teacher-dataset-v1",
        "atomic-effect-teacher-dataset-v2",
    ]
    dataset_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    generated_at: str = Field(min_length=1)
    source: dict[str, object]
    native_backend: dict[str, object]
    teacher: dict[str, object]
    effect_abi_version: str = Field(min_length=1)
    effect_spec_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    actor_encoder_version: str = Field(min_length=1)
    action_codec_version: str = Field(min_length=1)
    unit_limit: int = Field(gt=0)
    maximum_quantity: int = Field(gt=0)
    environment: dict[str, object]
    collection: dict[str, object]
    route_codes: dict[str, int]
    partitions: dict[
        Literal["train", "validation", "test"],
        tuple[str, ...],
    ] | None = None
    shards: tuple[EffectTeacherShard, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_shards(self) -> EffectTeacherManifest:
        """Require one ordered, non-overlapping complete seed range."""
        expected_seed = min(shard.seed_start for shard in self.shards)
        for expected_index, shard in enumerate(self.shards):
            if shard.index != expected_index:
                raise ValueError("effect teacher shard indices are not ordered")
            if (
                self.schema_version == "atomic-effect-teacher-dataset-v1"
                and shard.seed_start != expected_seed
            ):
                raise ValueError("effect teacher shards are not contiguous and ordered")
            expected_seed += shard.games
        if set(self.route_codes.values()) != set(range(len(self.route_codes))):
            raise ValueError("effect teacher route codes must be dense")
        if self.schema_version == "atomic-effect-teacher-dataset-v1":
            if self.partitions is not None or any(
                shard.shard_id is not None
                or shard.partition is not None
                or shard.source_group is not None
                for shard in self.shards
            ):
                raise ValueError("effect teacher v1 cannot declare aggregate partitions")
            return self
        if self.partitions is None:
            raise ValueError("effect teacher v2 requires explicit partitions")
        identities = [shard.shard_id for shard in self.shards]
        if any(identity is None for identity in identities) or len(set(identities)) != len(
            identities
        ):
            raise ValueError("effect teacher v2 shard identities must be unique")
        declared = {
            identity
            for partition in self.partitions.values()
            for identity in partition
        }
        if declared != set(cast(list[str], identities)):
            raise ValueError("effect teacher v2 partitions differ from its shards")
        for shard in self.shards:
            if (
                shard.partition is None
                or shard.source_group is None
                or shard.shard_id not in self.partitions[shard.partition]
            ):
                raise ValueError("effect teacher v2 shard partition is incomplete")
        return self


@dataclass(frozen=True, slots=True)
class LoadedEffectTeacherShard:
    """One authenticated shard in the current effect rollout representation."""

    batch: EffectRolloutBatch
    seeds: NDArray[np.int64]
    seats: NDArray[np.uint8]
    terminal_cash: NDArray[np.float64]
    opponent_cash: NDArray[np.float64]
    route_codes: NDArray[np.uint8]
    first_event_days: NDArray[np.int16]


def pack_effect_teacher_arrays(
    *,
    base: dict[str, NDArray[np.generic]],
    decisions: list[dict[str, Any]],
) -> dict[str, NDArray[np.generic]]:
    """Pack native width buckets without rollout-wide candidate padding."""
    missing = set(_BASE_FIELDS) - set(base)
    if missing:
        raise ValueError(f"effect teacher base arrays are incomplete: {sorted(missing)}")
    arrays = {name: np.asarray(base[name]) for name in _BASE_FIELDS}
    widths = np.asarray(arrays["bucket_widths"], dtype=np.int32)
    if len(decisions) != len(widths):
        raise ValueError("effect teacher bucket metadata differs from native tape")
    for index, payload in enumerate(decisions):
        for field in _DECISION_FIELDS:
            if field not in payload:
                raise ValueError(f"effect teacher native bucket lacks {field}")
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
            raise ValueError(f"effect teacher shard fields differ: {path}")
        return {name: np.asarray(archive[name]) for name in archive.files}


def load_effect_teacher_shard(
    dataset_dir: Path,
    shard: EffectTeacherShard,
) -> LoadedEffectTeacherShard:
    """Authenticate and load one shard as the current effect learner ABI."""
    path = (dataset_dir / shard.path).resolve()
    root = dataset_dir.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("effect teacher shard escaped its dataset")
    if path.stat().st_size != shard.size_bytes or sha256_file(path) != shard.sha256:
        raise ValueError(f"effect teacher shard identity differs: {path}")
    arrays = _load_arrays(path, len(shard.bucket_widths))
    decisions: list[dict[str, Any]] = []
    for index, width in enumerate(shard.bucket_widths):
        payload = {
            field: arrays[f"bucket_{index:03d}_{field}"]
            for field in _DECISION_FIELDS
        }
        counts = np.asarray(payload["candidate_counts"], dtype=np.int64)
        if counts.size == 0 or int(counts.max()) > width:
            raise ValueError("effect teacher candidate count exceeds its bucket")
        rows = counts.shape[0]
        payload["old_log_probability"] = np.zeros(rows, dtype=np.float32)
        payload["old_value"] = np.zeros(rows, dtype=np.float32)
        decisions.append(payload)
    batch = EffectRolloutBatch.from_native_buckets(
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
        or batch.factor_count != shard.factors
        or int(batch.board.shape[1]) != shard.turns_per_episode
    ):
        raise ValueError("effect teacher shard dimensions differ from its manifest")
    return LoadedEffectTeacherShard(
        batch=batch,
        seeds=np.asarray(arrays["seeds"], dtype=np.int64),
        seats=np.asarray(arrays["seats"], dtype=np.uint8),
        terminal_cash=np.asarray(arrays["terminal_cash"], dtype=np.float64),
        opponent_cash=np.asarray(arrays["opponent_cash"], dtype=np.float64),
        route_codes=np.asarray(arrays["route_codes"], dtype=np.uint8),
        first_event_days=np.asarray(arrays["first_event_days"], dtype=np.int16),
    )


def load_effect_teacher_manifest(dataset_dir: Path) -> EffectTeacherManifest:
    """Load one strict atomic-effect teacher manifest."""
    path = dataset_dir.resolve() / "manifest.json"
    return EffectTeacherManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))


__all__ = [
    "EffectTeacherManifest",
    "EffectTeacherShard",
    "LoadedEffectTeacherShard",
    "load_effect_teacher_manifest",
    "load_effect_teacher_shard",
    "pack_effect_teacher_arrays",
]
