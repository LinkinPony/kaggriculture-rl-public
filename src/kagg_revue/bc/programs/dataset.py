"""Compact streaming shards for conditional-program behavior cloning."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.programs.translate import ProgramReplaySeat
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.programs.schema import ProgramArchitecture
from kagg_revue.rl.programs.data import ProgramEpisode

Partition = Literal["train", "validation", "test"]


class ProgramBcShard(BaseModel):
    """One episode-seat NPZ and its authenticated split identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    shard_id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(gt=0)
    episode_id: str = Field(min_length=1)
    source_date: str = Field(min_length=1)
    seat: int = Field(ge=0, le=1)
    partition: Partition
    turns: int = Field(gt=0)
    maximum_program_decisions: int = Field(gt=0)
    outcome: int = Field(ge=-1, le=1)
    terminal_cash: float
    opponent_cash: float
    statistics: dict[str, int]
    source_group: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]*$")


class ProgramBcManifest(BaseModel):
    """Immutable compiler, actor, source, and shard contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["conditional-program-bc-dataset-v1"]
    dataset_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    generated_at: str
    source: dict[str, object]
    source_actor_identity: dict[str, object]
    native_backend: dict[str, object]
    native_program_abi: str = Field(min_length=1)
    actor_architecture: ActorArchitecture
    program_architecture: ProgramArchitecture
    action_keys: tuple[str, ...]
    environment: dict[str, object]
    translation: dict[str, object]
    selection: dict[str, object]
    partitions: dict[Partition, tuple[str, ...]]
    shards: tuple[ProgramBcShard, ...]


_FIELDS = (
    "board",
    "units",
    "global_features",
    "economic_state",
    "actions",
    "quantities",
    "action_decision_counts",
    "program_scalars",
    "program_root_features",
    "program_option_features",
    "program_target_reservations",
    "program_actions",
    "program_conditional_masks",
    "program_quantity_max",
    "program_decision_counts",
    "outcome",
)


def save_program_replay_shard(path: Path, translated: ProgramReplaySeat) -> dict[str, object]:
    """Atomically save one complete causal episode perspective."""
    arrays: dict[str, NDArray[np.generic]] = {
        name: np.asarray(getattr(translated, name)) for name in _FIELDS
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as stream:
        np.savez_compressed(stream, **cast(dict[str, Any], arrays))
    temporary.replace(path)
    return {
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "turns": int(translated.board.shape[0]),
        "maximum_program_decisions": int(translated.program_decision_counts.max(initial=0)),
        "outcome": translated.outcome,
    }


def load_program_replay_arrays(path: Path) -> dict[str, NDArray[np.generic]]:
    """Load and validate one bounded NPZ without object materialization."""
    with np.load(path, allow_pickle=False) as archive:
        if set(archive.files) != set(_FIELDS):
            raise ValueError(f"program BC shard fields differ: {path}")
        arrays = {name: np.asarray(archive[name]) for name in _FIELDS}
    turns = int(arrays["board"].shape[0])
    if turns < 1 or any(arrays[name].shape[0] != turns for name in _FIELDS if name != "outcome"):
        raise ValueError("program BC shard turn dimensions differ")
    if arrays["outcome"].shape != () or int(arrays["outcome"]) not in {-1, 0, 1}:
        raise ValueError("program BC shard outcome is invalid")
    counts = np.asarray(arrays["program_decision_counts"], dtype=np.int64)
    if np.any((counts < 1) | (counts > arrays["program_actions"].shape[1])):
        raise ValueError("program BC decision counts are outside their buffers")
    return arrays


class ProgramBcDataset:
    """Validated shard index with on-demand NPZ loading."""

    def __init__(self, manifest_path: Path) -> None:
        """Authenticate one dataset manifest and every declared partition."""
        self.root = manifest_path.parent.resolve()
        raw: object = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.manifest = ProgramBcManifest.model_validate(raw)
        self.manifest_sha256 = sha256_file(manifest_path)
        self._shards = {shard.shard_id: shard for shard in self.manifest.shards}
        self._verified: set[str] = set()
        if len(self._shards) != len(self.manifest.shards):
            raise ValueError("program BC manifest repeats a shard identity")
        declared = {
            shard_id for shard_ids in self.manifest.partitions.values() for shard_id in shard_ids
        }
        if declared != set(self._shards):
            raise ValueError("program BC partitions differ from declared shards")

    def shards(self, partition: Partition) -> tuple[ProgramBcShard, ...]:
        """Return stable shard records for one episode-disjoint split."""
        return tuple(self._shards[shard_id] for shard_id in self.manifest.partitions[partition])

    def arrays(self, shard: ProgramBcShard) -> dict[str, NDArray[np.generic]]:
        """Load one shard after verifying its current byte identity."""
        path = (self.root / shard.path).resolve()
        if not path.is_relative_to(self.root) or not path.is_file():
            raise FileNotFoundError(f"program BC shard is absent: {path}")
        if path.stat().st_size != shard.size_bytes:
            raise ValueError(f"program BC shard identity changed: {path}")
        if shard.shard_id not in self._verified:
            if sha256_file(path) != shard.sha256:
                raise ValueError(f"program BC shard identity changed: {path}")
            self._verified.add(shard.shard_id)
        return load_program_replay_arrays(path)

    def episode(self, shard: ProgramBcShard) -> ProgramEpisode:
        """Load one complete program episode from an authenticated shard."""
        arrays = self.arrays(shard)
        turns = shard.turns
        zeros = np.zeros(turns, dtype=np.float32)
        return ProgramEpisode(
            episode_id=shard.episode_id,
            opponent_id="daily_replay",
            seed=0,
            seat=shard.seat,
            outcome=shard.outcome,
            terminal_cash=shard.terminal_cash,
            opponent_cash=shard.opponent_cash,
            board=cast(NDArray[np.float16], arrays["board"]),
            units=cast(NDArray[np.float16], arrays["units"]),
            global_features=cast(NDArray[np.float32], arrays["global_features"]),
            economic_state=cast(NDArray[np.int32], arrays["economic_state"]),
            actions=cast(NDArray[np.int64], arrays["actions"]),
            quantities=cast(NDArray[np.int64], arrays["quantities"]),
            action_decision_counts=cast(NDArray[np.int16], arrays["action_decision_counts"]),
            program_scalars=cast(NDArray[np.int16], arrays["program_scalars"]),
            program_root_features=cast(NDArray[np.float32], arrays["program_root_features"]),
            program_option_features=cast(NDArray[np.int32], arrays["program_option_features"]),
            program_target_reservations=cast(
                NDArray[np.int16], arrays["program_target_reservations"]
            ),
            program_actions=cast(NDArray[np.int64], arrays["program_actions"]),
            program_conditional_masks=cast(NDArray[np.bool_], arrays["program_conditional_masks"]),
            program_quantity_max=cast(NDArray[np.int64], arrays["program_quantity_max"]),
            program_decision_counts=cast(NDArray[np.int16], arrays["program_decision_counts"]),
            old_joint_log_probability=zeros,
            old_values=zeros.copy(),
            stochastic_factor_counts=np.zeros(turns, dtype=np.int16),
            source_group=shard.source_group,
        )

    def episodes(self, partition: Partition) -> Iterator[tuple[ProgramBcShard, ProgramEpisode]]:
        """Stream complete program episodes for one partition."""
        for shard in self.shards(partition):
            yield shard, self.episode(shard)


__all__ = [
    "Partition",
    "ProgramBcDataset",
    "ProgramBcManifest",
    "ProgramBcShard",
    "load_program_replay_arrays",
    "save_program_replay_shard",
]
