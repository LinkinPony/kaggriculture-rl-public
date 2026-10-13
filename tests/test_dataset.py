import hashlib
import os
import threading
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from kagg_revue.bc import dataset as dataset_module
from kagg_revue.bc.dataset import (
    ChunkRef,
    SequenceBatch,
    SequenceDataset,
    SequenceRef,
    ShardRecord,
    SourceManifest,
)


def _source_manifest(shards: tuple[ShardRecord, ...] = ()) -> SourceManifest:
    return SourceManifest.model_validate(
        {
            "schema_version": "turn-behavior-dataset-v3",
            "dataset_id": "synthetic",
            "source_commit": "synthetic",
            "worktree_dirty": False,
            "actor_encoder_version": "synthetic",
            "control_spec": "synthetic",
            "board_shape": (2, 1, 1, 1),
            "unit_shape": (2, 1, 1),
            "global_features": 1,
            "derived_fact_version": "synthetic-facts",
            "turn_fact_features": 2,
            "prefix_fact_features": 3,
            "candidate_fact_features": 4,
            "unit_limit": 1,
            "unit_candidate_keys": (
                "UNIT:PASS",
                "UNIT:NORTH",
                "UNIT:SOUTH",
                "UNIT:EAST",
                "UNIT:WEST",
            ),
            "market_candidate_keys": ("MARKET:STOP",),
            "shards": shards,
        }
    )


def test_v3_collation_aligns_ragged_turn_and_decision_facts() -> None:
    manifest = _source_manifest()
    dataset = object.__new__(SequenceDataset)
    dataset.manifest = manifest
    sequence = SequenceRef(
        shard_index=0,
        sequence_index=0,
        episode_id="episode",
        seat=0,
        start=0,
        stop=2,
    )
    chunk = ChunkRef(sequence=sequence, start=0, loss_start=1, stop=2)
    action_tokens = manifest.action_tokens
    source_turn_facts = np.arange(6, dtype=np.float16).reshape(3, 2)
    source_prefix_facts = np.arange(12, dtype=np.float16).reshape(4, 3)
    source_candidate_facts = np.arange(4 * action_tokens * 4, dtype=np.float16).reshape(
        4, action_tokens, 4
    )
    arrays: dict[str, NDArray[np.generic]] = {
        "board": np.zeros((2, *manifest.board_shape), dtype=np.float16),
        "units": np.zeros((2, *manifest.unit_shape), dtype=np.float16),
        "global_features": np.zeros((2, manifest.global_features), dtype=np.float16),
        "turn_decision_offsets": np.asarray([0, 2, 4], dtype=np.int64),
        "unit_decisions": np.asarray([1, 1], dtype=np.int64),
        "action_token": np.asarray([0, 5, 1, 5], dtype=np.int64),
        "quantity_small": np.zeros(4, dtype=np.float32),
        "turn_fact_offsets": np.asarray([0, 1, 3], dtype=np.int64),
        "turn_facts": source_turn_facts,
        "prefix_facts": source_prefix_facts,
        "candidate_facts": source_candidate_facts,
    }

    dataset._validate_contract()
    batch = dataset._collate(arrays, [chunk], max_decisions=3)

    np.testing.assert_array_equal(batch.turn_facts[0, 0, :1], source_turn_facts[:1])
    np.testing.assert_array_equal(batch.turn_facts[0, 1, :2], source_turn_facts[1:])
    np.testing.assert_array_equal(batch.turn_fact_mask[0].sum(axis=1), [1, 2])
    np.testing.assert_array_equal(batch.prefix_facts[0, :, :2].reshape(4, 3), source_prefix_facts)
    np.testing.assert_array_equal(
        batch.candidate_facts[0, :, :2].reshape(4, action_tokens, 4),
        source_candidate_facts,
    )
    np.testing.assert_array_equal(batch.loss_mask, [[False, True]])


def test_quantity_overflow_restores_exact_int64_targets() -> None:
    arrays: dict[str, NDArray[np.generic]] = {
        "quantity_small": np.asarray([3, 0], dtype=np.float32),
        "quantity_overflow_index": np.asarray([1], dtype=np.int64),
        "quantity_overflow_decimal": np.asarray(["16777217"], dtype=np.str_),
    }

    quantities = SequenceDataset._quantities(arrays)

    assert quantities.dtype == np.int64
    np.testing.assert_array_equal(quantities, [3, 16777217])


def test_split_keeps_shards_and_episodes_in_one_partition() -> None:
    refs = tuple(
        SequenceRef(
            shard_index=shard,
            sequence_index=seat,
            episode_id=f"episode-{shard}",
            seat=seat,
            start=0,
            stop=3,
        )
        for shard in range(10)
        for seat in range(2)
    )

    partitions = SequenceDataset._split(refs, 17, 0.7, 0.2)

    shard_sets = [
        {ref.shard_index for ref in partitions[name]} for name in ("train", "validation", "test")
    ]
    episode_sets = [
        {ref.episode_id for ref in partitions[name]} for name in ("train", "validation", "test")
    ]
    assert all(shard_sets)
    assert all(episode_sets)
    assert sum(len(values) for values in shard_sets) == 10
    assert all(
        first.isdisjoint(second)
        for index, first in enumerate(shard_sets)
        for second in shard_sets[index + 1 :]
    )
    assert all(
        first.isdisjoint(second)
        for index, first in enumerate(episode_sets)
        for second in episode_sets[index + 1 :]
    )


def test_split_rejects_episode_spanning_shards() -> None:
    refs = (
        SequenceRef(0, 0, "crossing", 0, 0, 3),
        SequenceRef(1, 0, "crossing", 1, 0, 3),
        SequenceRef(2, 0, "local", 0, 0, 3),
    )

    with pytest.raises(ValueError, match="episode spans physical shards"):
        SequenceDataset._split(refs, 17, 0.6, 0.2)


def test_verified_path_hashes_once_until_file_identity_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contents = b"0123456789abcdef"
    shard_path = tmp_path / "shard.npz"
    shard_path.write_bytes(contents)
    record = ShardRecord(
        path=shard_path.name,
        sequences=1,
        turns=1,
        decisions=1,
        size_bytes=len(contents),
        sha256=hashlib.sha256(contents).hexdigest(),
    )
    dataset = object.__new__(SequenceDataset)
    dataset.root = tmp_path
    dataset.manifest = _source_manifest((record,))
    dataset._verified_shards = {}
    original_sha256_file = dataset_module.sha256_file
    hash_calls = 0

    def counted_sha256_file(path: Path) -> str:
        nonlocal hash_calls
        hash_calls += 1
        return original_sha256_file(path)

    monkeypatch.setattr(dataset_module, "sha256_file", counted_sha256_file)

    assert dataset._verified_path(0) == shard_path
    assert dataset._verified_path(0) == shard_path
    assert hash_calls == 1

    identity = shard_path.stat()
    shard_path.write_bytes(b"fedcba9876543210")
    os.utime(
        shard_path,
        ns=(identity.st_atime_ns, identity.st_mtime_ns + 1_000_000_000),
    )
    with pytest.raises(ValueError, match="dataset shard identity differs"):
        dataset._verified_path(0)
    assert hash_calls == 2


def test_parallel_loader_preserves_shard_order_and_bounds_concurrency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refs = tuple(SequenceRef(shard, 0, f"episode-{shard}", 0, 0, 1) for shard in range(4))
    dataset = object.__new__(SequenceDataset)
    dataset.refs = {"train": refs, "validation": (), "test": ()}
    barrier = threading.Barrier(2)
    lock = threading.Lock()
    active = 0
    maximum_active = 0
    sentinels = tuple(object.__new__(SequenceBatch) for _ in refs)

    def collated_shard(
        shard_index: int,
        chunks: object,
        batch_sequences: int,
        max_decisions: int,
    ) -> tuple[SequenceBatch, ...]:
        del chunks, batch_sequences, max_decisions
        nonlocal active, maximum_active
        with lock:
            active += 1
            maximum_active = max(maximum_active, active)
        if shard_index < 2:
            barrier.wait(timeout=5.0)
        with lock:
            active -= 1
        return (sentinels[shard_index],)

    monkeypatch.setattr(dataset, "_collated_shard", collated_shard)

    batches = list(
        dataset.iter_batches(
            "train",
            batch_sequences=1,
            unroll=1,
            burn_in=0,
            max_decisions=1,
            seed=3,
            epoch=1,
            loader_workers=2,
            shuffle=False,
        )
    )

    assert all(batch is sentinels[index] for index, batch in enumerate(batches))
    assert maximum_active == 2
