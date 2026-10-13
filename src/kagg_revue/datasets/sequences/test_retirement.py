"""Prevent retired teacher and opponent games from returning through frozen BC inputs."""

import json
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.exclusions import validate_manifest
from kagg_revue.datasets.sequences.retirement import revise


def test_revision_removes_whole_games_and_preserves_source(tmp_path: Path) -> None:
    """Filter teachers and opponents without touching original arrays or split membership."""
    source = tmp_path / "original"
    source.mkdir()
    shards: list[dict[str, Any]] = []
    episodes = []
    for key, teacher, opponent, split in (
        (1, 56484772, 10, "train"),
        (2, 56521745, 56484772, "val"),
        (3, 56521745, 10, "train"),
        (4, 56521745, 10, "val"),
    ):
        identities = [{"submissionId": teacher}, {"submissionId": opponent}]
        task = {
            "episode_id": key,
            "seats": [{"name": "Boey", "submission_id": teacher}],
            "agent_identity": identities,
            "split": split,
        }
        array = source / f"{key}.npy"
        array.write_bytes(f"immutable array {key}".encode())
        shards.append(
            {
                "task": task,
                "split": split,
                "source_date": "2026-09-25",
                "rows": 719,
                "usable_rows": 718,
                "observations": array.name,
                "hashes": {"observations": digest(array)},
            }
        )
        episodes.append({"id": key, "agents": identities, "createTime": "2026-09-25T00:00:00Z"})
    snapshot = source / "selected.json"
    write_json(
        snapshot,
        {
            "team_id": 1,
            "team_name": "Boey",
            "configuration": {"seed_submissions": [56484772], "seed_episodes": [1]},
            "submissions": [{"id": 56484772}, {"id": 56521745}],
            "episodes": episodes,
            "replays": [{"episode_id": row["id"]} for row in episodes],
            "submission_selection": {"public_submission_ids": [56484772, 56521745]},
        },
    )
    path = source / "manifest.json"
    write_json(
        path,
        {
            "sequence_format": "complete-turn-seat-v1",
            "shards": shards,
            "configuration": {"output": str(source), "watch_manifests": [str(snapshot)]},
            "sources": {
                "collector_snapshots": [{"path": str(snapshot), "sha256": digest(snapshot)}]
            },
            "coverage": {"train": {}, "val": {}},
            "exclusions": [],
            "teacher_selection": {"excluded_submissions": []},
            "scope": "Fixture.",
        },
    )
    original_hash = digest(path)
    with pytest.raises(ValueError, match="56484772"):
        validate_manifest(json.loads(path.read_text()))
    output = tmp_path / "cleaned"
    receipt = revise(path, output)
    cleaned = json.loads((output / "manifest.json").read_text())
    validate_manifest(cleaned)
    assert receipt["removed_episode_ids"] == [1, 2]
    assert receipt["removed_trajectories"] == 2
    assert receipt["retained_arrays_same_inode"] == 2
    assert cleaned["selected_teacher_trajectories"] == {"Boey": 2}
    assert [row["task"]["episode_id"] for row in cleaned["shards"]] == [3, 4]
    assert [row["split"] for row in cleaned["shards"]] == ["train", "val"]
    assert cleaned["coverage"]["train"]["trajectories"] == 1
    assert cleaned["coverage"]["val"]["trajectories"] == 1
    assert not (output / "1.npy").exists() and not (output / "2.npy").exists()
    assert (output / "3.npy").samefile(source / "3.npy")
    assert digest(path) == original_hash
    assert all(
        digest(source / row["observations"]) == row["hashes"]["observations"] for row in shards
    )
    selected = json.loads(Path(cleaned["configuration"]["watch_manifests"][0]).read_text())
    assert [row["id"] for row in selected["episodes"]] == [3, 4]
    assert selected["configuration"]["seed_submissions"] == []
    assert selected["submission_selection"]["public_submission_ids"] == [56521745]
    assert json.loads((source / "retired.json").read_text())["replacement"] == str(
        output / "manifest.json"
    )
