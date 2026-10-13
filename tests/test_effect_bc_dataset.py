import numpy as np
import pytest

from kagg_revue.bc.effects.correction import _episode_decisions
from kagg_revue.bc.effects.correction_observer import (
    prefix_consistent_policy_mask,
)
from kagg_revue.bc.effects.dataset import EffectTeacherManifest
from kagg_revue.bc.effects.train import _partitions


def _shard(index: int, partition: str) -> dict[str, object]:
    return {
        "index": index,
        "shard_id": f"source:{index}",
        "path": f"shards/source/effect-{index:05d}.npz",
        "partition": partition,
        "source_group": "source",
        "seed_start": 100 + index * 10,
        "games": 1,
        "episodes": 2,
        "turns_per_episode": 3,
        "factors": 4,
        "policy_factors": 3,
        "maximum_transaction_steps": 2,
        "bucket_widths": [2],
        "terminal_cash_sum": 10.0,
        "opponent_cash_sum": 9.0,
        "better": 1,
        "ties": 0,
        "worse": 1,
        "size_bytes": 10,
        "sha256": f"{index + 1:064x}",
    }


def test_effect_v2_manifest_preserves_explicit_component_partitions() -> None:
    manifest = EffectTeacherManifest.model_validate(
        {
            "schema_version": "atomic-effect-teacher-dataset-v2",
            "dataset_id": "a" * 64,
            "generated_at": "2026-09-04T00:00:00+00:00",
            "source": {},
            "native_backend": {},
            "teacher": {},
            "effect_abi_version": "atomic-effect-policy-v2",
            "effect_spec_sha256": "b" * 64,
            "actor_encoder_version": "actor-v1",
            "action_codec_version": "action-v1",
            "unit_limit": 4,
            "maximum_quantity": 8,
            "environment": {},
            "collection": {},
            "route_codes": {"default": 0},
            "partitions": {
                "train": ["source:0", "source:1"],
                "validation": ["source:2"],
                "test": ["source:3"],
            },
            "shards": [
                _shard(0, "train"),
                _shard(1, "train"),
                _shard(2, "validation"),
                _shard(3, "test"),
            ],
        }
    )

    partitions = _partitions(manifest, validation_games=99, test_games=99)

    assert [shard.shard_id for shard in partitions["train"]] == [
        "source:0",
        "source:1",
    ]
    assert [shard.shard_id for shard in partitions["validation"]] == [
        "source:2"
    ]
    assert [shard.shard_id for shard in partitions["test"]] == ["source:3"]


def test_effect_correction_splits_paired_seed_rows_from_native_buckets() -> None:
    buckets = [
        {
            "episode_index": np.asarray([0, 2, 1, 3], dtype=np.int64),
            "turn_index": np.asarray([0, 0, 1, 1], dtype=np.int64),
            "selected": np.asarray([4, 5, 6, 7], dtype=np.int64),
        }
    ]

    selected = _episode_decisions(buckets, episode_start=2)

    assert len(selected) == 1
    np.testing.assert_array_equal(selected[0]["episode_index"], [0, 1])
    np.testing.assert_array_equal(selected[0]["turn_index"], [0, 1])
    np.testing.assert_array_equal(selected[0]["selected"], [5, 7])


def test_effect_correction_masks_only_rows_after_each_first_divergence() -> None:
    retained = prefix_consistent_policy_mask(
        episode_index=np.asarray([0, 0, 0, 0, 0, 1], dtype=np.int64),
        turn_index=np.asarray([2, 2, 2, 2, 2, 2], dtype=np.int64),
        transaction_step=np.asarray([2, 0, 1, 4, 3, 0], dtype=np.int64),
        student_agreement=np.asarray(
            [True, True, False, True, False, False], dtype=np.bool_
        ),
        policy_mask=np.ones(6, dtype=np.bool_),
    )

    np.testing.assert_array_equal(retained, [False, True, True, False, False, True])


def test_effect_correction_rejects_noncontiguous_phase_steps() -> None:
    with pytest.raises(ValueError, match="contiguous"):
        prefix_consistent_policy_mask(
            episode_index=np.zeros(2, dtype=np.int64),
            turn_index=np.zeros(2, dtype=np.int64),
            transaction_step=np.asarray([0, 2], dtype=np.int64),
            student_agreement=np.ones(2, dtype=np.bool_),
            policy_mask=np.ones(2, dtype=np.bool_),
        )
