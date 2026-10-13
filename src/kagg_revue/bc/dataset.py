"""Streaming sequences from authenticated compact behavior shards."""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict, deque
from collections.abc import Iterator, Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

from kagg_revue.policy.economics import EconomicStateLayout
from kagg_revue.policy.economics.layout import ECONOMIC_STATE_VERSION

Partition = Literal["train", "validation", "test"]


class _ExternalModel(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class ShardRecord(_ExternalModel):
    """Authenticated tensor shard metadata."""

    path: str
    sequences: int = Field(gt=0)
    turns: int = Field(gt=0)
    decisions: int = Field(gt=0)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SourceManifest(_ExternalModel):
    """Replay fields required by the sequential actor."""

    schema_version: Literal[
        "turn-behavior-dataset-v2",
        "turn-behavior-dataset-v3",
        "turn-behavior-dataset-v4",
        "turn-behavior-dataset-v5",
    ]
    dataset_id: str
    source_commit: str
    worktree_dirty: bool
    actor_encoder_version: str
    action_codec_version: str | None = None
    control_spec: str
    action_target_canonicalization: str | None = None
    board_shape: tuple[int, int, int, int]
    unit_shape: tuple[int, int, int]
    global_features: int = Field(gt=0)
    economic_state_version: int | None = None
    economic_state_features: int = Field(default=0, ge=0)
    derived_fact_version: str | None = None
    turn_fact_features: int = Field(default=0, ge=0)
    prefix_fact_features: int = Field(default=0, ge=0)
    candidate_fact_features: int = Field(default=0, ge=0)
    unit_limit: int = Field(gt=0)
    unit_candidate_keys: tuple[str, ...]
    market_candidate_keys: tuple[str, ...]
    shards: tuple[ShardRecord, ...]

    @property
    def action_tokens(self) -> int:
        """Return the unified numeric vocabulary size."""
        return len(self.unit_candidate_keys) + len(self.market_candidate_keys)


@dataclass(frozen=True)
class SequenceRef:
    """One episode seat located inside a shard."""

    shard_index: int
    sequence_index: int
    episode_id: str
    seat: int
    start: int
    stop: int


@dataclass(frozen=True)
class ChunkRef:
    """A continuous context whose suffix contributes optimization loss."""

    sequence: SequenceRef
    start: int
    loss_start: int
    stop: int


@dataclass(frozen=True)
class _ShardIdentity:
    """Filesystem identity captured after authenticating one shard."""

    size: int
    modified_ns: int
    changed_ns: int
    inode: int


@dataclass(frozen=True)
class SequenceBatch:
    """Padded continuous trajectories with explicit turn and loss masks."""

    board: NDArray[np.float16]
    units: NDArray[np.float16]
    global_features: NDArray[np.float16]
    economic_state: NDArray[np.int32]
    turn_facts: NDArray[np.float16]
    turn_fact_mask: NDArray[np.bool_]
    prefix_facts: NDArray[np.float16]
    candidate_facts: NDArray[np.float16]
    actions: NDArray[np.int64]
    quantities: NDArray[np.int64]
    phases: NDArray[np.int64]
    turn_mask: NDArray[np.bool_]
    loss_mask: NDArray[np.bool_]
    decision_mask: NDArray[np.bool_]


def sha256_file(path: Path) -> str:
    """Hash a file without materializing it."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


class SequenceDataset:
    """Verified shard-local episode splits with bounded parallel reads."""

    def __init__(
        self,
        root: Path,
        split_seed: int,
        train_fraction: float,
        validation_fraction: float,
    ) -> None:
        """Authenticate the manifest and form shard-local episode splits."""
        self.root = root.resolve()
        manifest_path = self.root / "manifest.json"
        self.manifest_sha256 = sha256_file(manifest_path)
        self.manifest = SourceManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        self._validate_contract()
        self._verified_shards: dict[int, _ShardIdentity] = {}
        self.refs = self._split(
            self._index_sequences(), split_seed, train_fraction, validation_fraction
        )

    def _validate_contract(self) -> None:
        manifest = self.manifest
        if manifest.board_shape[0] != 2 or manifest.unit_shape[0] != 2:
            raise ValueError("dataset actor tensors must contain two relative farms")
        if manifest.unit_shape[1] != manifest.unit_limit:
            raise ValueError("dataset unit tensor differs from its manifest")
        if manifest.unit_candidate_keys[:5] != (
            "UNIT:PASS",
            "UNIT:NORTH",
            "UNIT:SOUTH",
            "UNIT:EAST",
            "UNIT:WEST",
        ):
            raise ValueError("dataset movement vocabulary is unsupported")
        if not manifest.market_candidate_keys or manifest.market_candidate_keys[0] != (
            "MARKET:STOP"
        ):
            raise ValueError("dataset market vocabulary lacks STOP")
        fact_widths = (
            manifest.turn_fact_features,
            manifest.prefix_fact_features,
            manifest.candidate_fact_features,
        )
        if manifest.schema_version in {
            "turn-behavior-dataset-v4",
            "turn-behavior-dataset-v5",
        }:
            if (
                manifest.actor_encoder_version != "actor-observation-v2"
                or manifest.action_codec_version != "turn-policy-actions-v2"
                or manifest.unit_shape[2] != 60
            ):
                raise ValueError("v4 dataset lacks the inventory-order/action ABI")
            if any(fact_widths) != all(fact_widths):
                raise ValueError("v4 derived-fact tensors are incomplete")
            if all(fact_widths) != (manifest.derived_fact_version is not None):
                raise ValueError("modern derived-fact identity and tensors disagree")
            if manifest.schema_version == "turn-behavior-dataset-v5":
                expected_economic = EconomicStateLayout.create(
                    manifest.board_shape[-1],
                    manifest.unit_limit,
                )
                if (
                    manifest.economic_state_version != ECONOMIC_STATE_VERSION
                    or manifest.economic_state_features != expected_economic.width
                ):
                    raise ValueError("v5 dataset lacks its compact economic-state ABI")
            elif (
                manifest.economic_state_version is not None
                or manifest.economic_state_features
            ):
                raise ValueError("v4 dataset cannot declare compact economic state")
        elif manifest.schema_version == "turn-behavior-dataset-v3":
            if not manifest.derived_fact_version or any(width <= 0 for width in fact_widths):
                raise ValueError("v3 dataset lacks its complete derived-fact contract")
        elif any(fact_widths) or manifest.derived_fact_version is not None:
            raise ValueError("v2 dataset cannot declare derived-fact tensors")

    @staticmethod
    def _file_identity(path: Path) -> _ShardIdentity:
        stat = path.stat()
        return _ShardIdentity(
            size=stat.st_size,
            modified_ns=stat.st_mtime_ns,
            changed_ns=stat.st_ctime_ns,
            inode=stat.st_ino,
        )

    def _verified_path(self, shard_index: int) -> Path:
        """Authenticate a shard once, then recheck it when its metadata changes."""
        record = self.manifest.shards[shard_index]
        path = self.root / record.path
        identity = self._file_identity(path)
        if self._verified_shards.get(shard_index) == identity:
            return path
        if identity.size != record.size_bytes or sha256_file(path) != record.sha256:
            raise ValueError(f"dataset shard identity differs: {path}")
        authenticated_identity = self._file_identity(path)
        if authenticated_identity != identity:
            raise ValueError(f"dataset shard changed while authenticating: {path}")
        self._verified_shards[shard_index] = authenticated_identity
        return path

    def _load_metadata(
        self, shard_index: int
    ) -> tuple[NDArray[np.str_], NDArray[np.uint8], NDArray[np.int64]]:
        path = self._verified_path(shard_index)
        with np.load(path, allow_pickle=False) as archive:
            return (
                np.asarray(archive["episode_id"], dtype=np.str_),
                np.asarray(archive["seat"], dtype=np.uint8),
                np.asarray(archive["sequence_offsets"], dtype=np.int64),
            )

    def _index_sequences(self) -> tuple[SequenceRef, ...]:
        refs: list[SequenceRef] = []
        for shard_index, record in enumerate(self.manifest.shards):
            episode_id, seat, offsets = self._load_metadata(shard_index)
            if episode_id.shape != seat.shape or episode_id.shape != (record.sequences,):
                raise ValueError("dataset sequence metadata shape differs")
            if offsets.shape != (record.sequences + 1,) or int(offsets[-1]) != record.turns:
                raise ValueError("dataset sequence offsets differ")
            for sequence_index in range(record.sequences):
                refs.append(
                    SequenceRef(
                        shard_index=shard_index,
                        sequence_index=sequence_index,
                        episode_id=str(episode_id[sequence_index]),
                        seat=int(seat[sequence_index]),
                        start=int(offsets[sequence_index]),
                        stop=int(offsets[sequence_index + 1]),
                    )
                )
        return tuple(refs)

    @staticmethod
    def _split(
        refs: Sequence[SequenceRef],
        seed: int,
        train_fraction: float,
        validation_fraction: float,
    ) -> dict[Partition, tuple[SequenceRef, ...]]:
        by_shard: dict[int, list[SequenceRef]] = defaultdict(list)
        episode_shards: dict[str, set[int]] = defaultdict(set)
        for ref in refs:
            by_shard[ref.shard_index].append(ref)
            episode_shards[ref.episode_id].add(ref.shard_index)
        crossing = sorted(episode for episode, shards in episode_shards.items() if len(shards) != 1)
        if crossing:
            raise ValueError(
                f"episode spans physical shards and cannot use shard-local splits: {crossing[0]}"
            )
        shards = sorted(
            by_shard,
            key=lambda shard: hashlib.sha256(f"{seed}:{shard}".encode()).digest(),
        )
        if len(shards) < 3:
            raise ValueError("dataset needs at least three shards for disjoint splits")

        episode_counts = [len({ref.episode_id for ref in by_shard[shard]}) for shard in shards]

        def closest_stop(start: int, target: float, maximum: int) -> int:
            cumulative = 0
            candidates: list[tuple[float, int]] = []
            for stop in range(start + 1, maximum + 1):
                cumulative += episode_counts[stop - 1]
                candidates.append((abs(cumulative - target), stop))
            return min(candidates)[1]

        total_episodes = len(episode_shards)
        train_stop = closest_stop(0, total_episodes * train_fraction, len(shards) - 2)
        validation_stop = closest_stop(
            train_stop,
            total_episodes * validation_fraction,
            len(shards) - 1,
        )
        partition_shards: dict[Partition, set[int]] = {
            "train": set(shards[:train_stop]),
            "validation": set(shards[train_stop:validation_stop]),
            "test": set(shards[validation_stop:]),
        }
        return {
            name: tuple(ref for shard in shards if shard in selected for ref in by_shard[shard])
            for name, selected in partition_shards.items()
        }

    def split_summary(self) -> dict[str, object]:
        """Return non-overlapping episode, sequence and turn counts."""
        return {
            name: {
                "sequences": len(refs),
                "episodes": len({ref.episode_id for ref in refs}),
                "shards": len({ref.shard_index for ref in refs}),
                "turns": sum(ref.stop - ref.start for ref in refs),
            }
            for name, refs in self.refs.items()
        }

    def _load_shard(self, shard_index: int) -> dict[str, NDArray[np.generic]]:
        path = self._verified_path(shard_index)
        with np.load(path, allow_pickle=False) as archive:
            return {name: np.asarray(archive[name]) for name in archive.files}

    def _collated_shard(
        self,
        shard_index: int,
        chunks: Sequence[ChunkRef],
        batch_sequences: int,
        max_decisions: int,
    ) -> tuple[SequenceBatch, ...]:
        """Load and collate one shard into a bounded tuple of batches."""
        arrays = self._load_shard(shard_index)
        return tuple(
            self._collate(
                arrays,
                chunks[offset : offset + batch_sequences],
                max_decisions,
            )
            for offset in range(0, len(chunks), batch_sequences)
        )

    @staticmethod
    def _chunks(ref: SequenceRef, unroll: int, burn_in: int) -> list[ChunkRef]:
        chunks: list[ChunkRef] = []
        for loss_start in range(ref.start, ref.stop, unroll):
            chunks.append(
                ChunkRef(
                    sequence=ref,
                    start=max(ref.start, loss_start - burn_in),
                    loss_start=loss_start,
                    stop=min(ref.stop, loss_start + unroll),
                )
            )
        return chunks

    @staticmethod
    def _quantities(arrays: dict[str, NDArray[np.generic]]) -> NDArray[np.int64]:
        stored = np.asarray(arrays["quantity_small"], dtype=np.float32)
        if (
            stored.ndim != 1
            or np.any(~np.isfinite(stored))
            or np.any(stored < 0)
            or np.any(stored != np.floor(stored))
            or np.any(stored >= np.float32(np.iinfo(np.int64).max))
        ):
            raise ValueError("small quantity tensor must contain finite nonnegative integers")
        values = stored.astype(np.int64)
        overflow_indices = np.asarray(
            arrays.get("quantity_overflow_index", np.empty(0)), dtype=np.int64
        )
        overflow_values = np.asarray(
            arrays.get("quantity_overflow_decimal", np.empty(0)), dtype=np.str_
        )
        if (
            overflow_indices.shape != overflow_values.shape
            or overflow_indices.ndim != 1
            or np.any(overflow_indices < 0)
            or np.any(overflow_indices >= values.size)
            or np.unique(overflow_indices).size != overflow_indices.size
        ):
            raise ValueError("quantity overflow arrays differ")
        for index, decimal in zip(overflow_indices, overflow_values, strict=True):
            try:
                parsed = int(str(decimal))
            except ValueError as error:
                raise ValueError("quantity overflow value is not an integer") from error
            if parsed < 1 or parsed > np.iinfo(np.int64).max:
                raise ValueError("quantity overflow value is outside the numeric action ABI")
            values[int(index)] = parsed
        return values

    def _collate(
        self,
        arrays: dict[str, NDArray[np.generic]],
        chunks: Sequence[ChunkRef],
        max_decisions: int,
    ) -> SequenceBatch:
        batch = len(chunks)
        turns = max(chunk.stop - chunk.start for chunk in chunks)
        board_shape = self.manifest.board_shape
        unit_shape = self.manifest.unit_shape
        board = np.zeros((batch, turns, *board_shape), dtype=np.float16)
        units = np.zeros((batch, turns, *unit_shape), dtype=np.float16)
        globals_ = np.zeros((batch, turns, self.manifest.global_features), dtype=np.float16)
        economic_state = np.zeros(
            (batch, turns, self.manifest.economic_state_features),
            dtype=np.int32,
        )
        fact_offsets: NDArray[np.int64] | None = None
        source_turn_facts: NDArray[np.float16] | None = None
        source_prefix_facts: NDArray[np.float16] | None = None
        source_candidate_facts: NDArray[np.float16] | None = None
        maximum_fact_tokens = 0
        if self.manifest.turn_fact_features:
            fact_offsets = np.asarray(arrays["turn_fact_offsets"], dtype=np.int64)
            source_turns = int(np.asarray(arrays["board"]).shape[0])
            if (
                fact_offsets.shape != (source_turns + 1,)
                or int(fact_offsets[0]) != 0
                or np.any(np.diff(fact_offsets) < 0)
            ):
                raise ValueError("derived-fact turn offsets differ")
            source_turn_facts = np.asarray(arrays["turn_facts"], dtype=np.float16)
            source_prefix_facts = np.asarray(arrays["prefix_facts"], dtype=np.float16)
            source_candidate_facts = np.asarray(arrays["candidate_facts"], dtype=np.float16)
            referenced_turns = [turn for chunk in chunks for turn in range(chunk.start, chunk.stop)]
            maximum_fact_tokens = max(
                (int(fact_offsets[turn + 1] - fact_offsets[turn]) for turn in referenced_turns),
                default=0,
            )
        turn_facts = np.zeros(
            (
                batch,
                turns,
                maximum_fact_tokens,
                self.manifest.turn_fact_features,
            ),
            dtype=np.float16,
        )
        turn_fact_mask = np.zeros((batch, turns, maximum_fact_tokens), dtype=np.bool_)
        prefix_facts = np.zeros(
            (batch, turns, max_decisions, self.manifest.prefix_fact_features),
            dtype=np.float16,
        )
        candidate_facts = np.zeros(
            (
                batch,
                turns,
                max_decisions,
                self.manifest.action_tokens,
                self.manifest.candidate_fact_features,
            ),
            dtype=np.float16,
        )
        actions = np.full((batch, turns, max_decisions), -1, dtype=np.int64)
        quantities = np.zeros((batch, turns, max_decisions), dtype=np.int64)
        phases = np.zeros((batch, turns, max_decisions), dtype=np.int64)
        turn_mask = np.zeros((batch, turns), dtype=np.bool_)
        loss_mask = np.zeros((batch, turns), dtype=np.bool_)
        decision_mask = np.zeros((batch, turns, max_decisions), dtype=np.bool_)
        offsets = np.asarray(arrays["turn_decision_offsets"], dtype=np.int64)
        unit_counts = np.asarray(arrays["unit_decisions"], dtype=np.int64)
        tokens = np.asarray(arrays["action_token"], dtype=np.int64)
        all_quantities = self._quantities(arrays)
        source_board = np.asarray(arrays["board"], dtype=np.float16)
        source_units = np.asarray(arrays["units"], dtype=np.float16)
        source_globals = np.asarray(arrays["global_features"], dtype=np.float16)
        source_economic = np.asarray(
            arrays.get(
                "economic_state",
                np.empty((source_board.shape[0], 0), dtype=np.int32),
            ),
            dtype=np.int32,
        )
        source_turns = source_board.shape[0]
        if (
            source_board.shape != (source_turns, *self.manifest.board_shape)
            or source_units.shape != (source_turns, *self.manifest.unit_shape)
            or source_globals.shape != (source_turns, self.manifest.global_features)
            or source_economic.shape
            != (source_turns, self.manifest.economic_state_features)
            or unit_counts.shape != (source_turns,)
            or offsets.shape != (source_turns + 1,)
            or int(offsets[0]) != 0
            or np.any(np.diff(offsets) < 0)
            or tokens.ndim != 1
            or int(offsets[-1]) != tokens.size
            or all_quantities.shape != tokens.shape
        ):
            raise ValueError("dataset turn or decision tensor shapes differ")
        if fact_offsets is not None:
            if source_turn_facts is None or source_turn_facts.shape != (
                int(fact_offsets[-1]),
                self.manifest.turn_fact_features,
            ):
                raise ValueError("turn fact tensor differs from its manifest")
            total_decisions = int(offsets[-1])
            if source_prefix_facts is None or source_prefix_facts.shape != (
                total_decisions,
                self.manifest.prefix_fact_features,
            ):
                raise ValueError("prefix fact tensor differs from its manifest")
            if source_candidate_facts is None or source_candidate_facts.shape != (
                total_decisions,
                self.manifest.action_tokens,
                self.manifest.candidate_fact_features,
            ):
                raise ValueError("candidate fact tensor differs from its manifest")
        unit_vocabulary = len(self.manifest.unit_candidate_keys)
        for row, chunk in enumerate(chunks):
            length = chunk.stop - chunk.start
            source = slice(chunk.start, chunk.stop)
            board[row, :length] = source_board[source]
            units[row, :length] = source_units[source]
            globals_[row, :length] = source_globals[source]
            economic_state[row, :length] = source_economic[source]
            turn_mask[row, :length] = True
            loss_mask[row, chunk.loss_start - chunk.start : length] = True
            for target_turn, source_turn in enumerate(range(chunk.start, chunk.stop)):
                if fact_offsets is not None and source_turn_facts is not None:
                    fact_start = int(fact_offsets[source_turn])
                    fact_stop = int(fact_offsets[source_turn + 1])
                    fact_count = fact_stop - fact_start
                    turn_facts[row, target_turn, :fact_count] = source_turn_facts[
                        fact_start:fact_stop
                    ]
                    turn_fact_mask[row, target_turn, :fact_count] = True
                decision_start = int(offsets[source_turn])
                decision_stop = int(offsets[source_turn + 1])
                count = decision_stop - decision_start
                unit_count = int(unit_counts[source_turn])
                if count > max_decisions or unit_count > count:
                    raise ValueError("dataset turn exceeds the actor decision capacity")
                selected = tokens[decision_start:decision_stop]
                if np.any(selected < 0) or np.any(selected >= self.manifest.action_tokens):
                    raise ValueError("dataset contains an unknown action token")
                if np.any(selected[:unit_count] >= unit_vocabulary) or np.any(
                    selected[unit_count:] < unit_vocabulary
                ):
                    raise ValueError("dataset action phases are not contiguous")
                actions[row, target_turn, :count] = selected
                quantities[row, target_turn, :count] = all_quantities[decision_start:decision_stop]
                phases[row, target_turn, unit_count:count] = 1
                decision_mask[row, target_turn, :count] = True
                if source_prefix_facts is not None and source_candidate_facts is not None:
                    prefix_facts[row, target_turn, :count] = source_prefix_facts[
                        decision_start:decision_stop
                    ]
                    candidate_facts[row, target_turn, :count] = source_candidate_facts[
                        decision_start:decision_stop
                    ]
        return SequenceBatch(
            board=board,
            units=units,
            global_features=globals_,
            economic_state=economic_state,
            turn_facts=turn_facts,
            turn_fact_mask=turn_fact_mask,
            prefix_facts=prefix_facts,
            candidate_facts=candidate_facts,
            actions=actions,
            quantities=quantities,
            phases=phases,
            turn_mask=turn_mask,
            loss_mask=loss_mask,
            decision_mask=decision_mask,
        )

    def iter_batches(
        self,
        partition: Partition,
        batch_sequences: int,
        unroll: int,
        burn_in: int,
        max_decisions: int,
        seed: int,
        epoch: int,
        *,
        loader_workers: int = 1,
        shuffle: bool,
    ) -> Iterator[SequenceBatch]:
        """Yield chunks from a bounded, deterministic shard-loader pipeline."""
        if loader_workers < 1:
            raise ValueError("loader_workers must be positive")
        randomizer = random.Random(seed + 1_000_003 * epoch)
        refs_by_shard: dict[int, list[SequenceRef]] = defaultdict(list)
        for ref in self.refs[partition]:
            refs_by_shard[ref.shard_index].append(ref)
        shard_order = list(refs_by_shard)
        if shuffle:
            randomizer.shuffle(shard_order)
        prepared: list[tuple[int, tuple[ChunkRef, ...]]] = []
        for shard_index in shard_order:
            chunks = [
                chunk
                for ref in refs_by_shard[shard_index]
                for chunk in self._chunks(ref, unroll, burn_in)
            ]
            if shuffle:
                randomizer.shuffle(chunks)
            prepared.append((shard_index, tuple(chunks)))

        if loader_workers == 1:
            for shard_index, shard_chunks in prepared:
                yield from self._collated_shard(
                    shard_index, shard_chunks, batch_sequences, max_decisions
                )
            return

        work = iter(prepared)
        with ThreadPoolExecutor(
            max_workers=loader_workers,
            thread_name_prefix="bc-shard",
        ) as executor:
            pending: deque[Future[tuple[SequenceBatch, ...]]] = deque()
            for _ in range(min(loader_workers, len(prepared))):
                shard_index, shard_chunks = next(work)
                pending.append(
                    executor.submit(
                        self._collated_shard,
                        shard_index,
                        shard_chunks,
                        batch_sequences,
                        max_decisions,
                    )
                )
            for shard_index, shard_chunks in work:
                batches = pending.popleft().result()
                pending.append(
                    executor.submit(
                        self._collated_shard,
                        shard_index,
                        shard_chunks,
                        batch_sequences,
                        max_decisions,
                    )
                )
                yield from batches
            while pending:
                yield from pending.popleft().result()


def write_dataset_identity(dataset: SequenceDataset, path: Path) -> None:
    """Persist the exact external dataset identity used by an experiment."""
    value = {
        "dataset_dir": str(dataset.root),
        "manifest_sha256": dataset.manifest_sha256,
        "dataset_id": dataset.manifest.dataset_id,
        "source_commit": dataset.manifest.source_commit,
        "source_worktree_dirty": dataset.manifest.worktree_dirty,
        "split": dataset.split_summary(),
    }
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


__all__ = [
    "Partition",
    "SequenceBatch",
    "SequenceDataset",
    "SourceManifest",
    "sha256_file",
    "write_dataset_identity",
]
