"""Protect acquisition cutoffs independently of game and submission dates."""

import json
from pathlib import Path

import pytest

from kagg_revue.artifacts.io import write_json
from kagg_revue.datasets.sequences.collected import CollectionSettings, freeze


def _sources(tmp_path: Path) -> dict[str, Path]:
    sources = {}
    for team in (1, 2):
        episodes, replays = [], []
        for key in (1, 2, 3, 4):
            date = "2026-09-24T00:00:00Z"
            if key == 1 and team == 1:
                date = "2026-09-23T23:59:59Z"
            # Episode 3 is a late download of an older game and must be retained.
            episodes.append(
                {
                    "id": key,
                    "createTime": "2026-09-20T00:00:00Z",
                    "agents": [
                        {"teamId": 1, "submissionId": 10},
                        {"teamId": 2, "submissionId": 99 if key == 4 else 20, "index": 1},
                    ],
                }
            )
            source = tmp_path / f"{team}-{key}.source.json"
            write_json(
                source,
                {
                    "episode_id": key,
                    "retrieved_utc": date,
                    "compressed_sha256": "a" * 64,
                },
            )
            replays.append(
                {
                    "episode_id": key,
                    "retrieved_utc": date,
                    "sha256": "a" * 64,
                    "source": str(source),
                }
            )
        path = tmp_path / f"team-{team}.json"
        write_json(
            path,
            {
                "team_id": team,
                "team_name": str(team),
                "updated_utc": "2026-09-25T12:00:00Z",
                "configuration": {},
                "submissions": [{"id": team * 10}],
                "episodes": episodes,
                "replays": replays,
                "excluded_submissions": [99],
            },
        )
        sources[str(team)] = path
    return sources


def test_first_download_boundary_shared_games_and_frozen_provenance(tmp_path: Path) -> None:
    """Earlier copies exclude later duplicates; old game dates do not limit downloads."""
    sources = _sources(tmp_path)
    config = CollectionSettings.model_validate(
        {
            "output": tmp_path / "frozen",
            "sources": sources,
            "collected_since": "2026-09-24T00:00:00Z",
        }
    )
    report = freeze(config)
    assert report["unique_episodes"] == 2
    assert report["teacher_trajectories"] == 4
    assert set(report["earliest_download_utc"]) == {"2", "3"}
    for path in sources.values():
        path.write_text("{}")
    for source in tmp_path.glob("*.source.json"):
        source.write_text("{}")
    assert freeze(config) == report


def test_daily_archive_proves_old_acquisition_without_inventing_a_download_date(
    tmp_path: Path,
) -> None:
    """Reused old archives override recent copies; uncertain dates fail explicitly."""
    sources = _sources(tmp_path)
    archive = tmp_path / "daily" / "episodes.zip"
    source = sources["1"]
    manifest = json.loads(source.read_text())
    manifest["replays"][1] = {
        "episode_id": 2,
        "storage": "daily_zip",
        "path": str(archive),
    }
    write_json(source, manifest)
    write_json(
        archive.parent / "manifest.json",
        {
            "verified_at_utc": "2026-09-23T23:59:59Z",
            "daily_archives": [{"path": str(archive)}],
        },
    )
    config = CollectionSettings.model_validate(
        {
            "output": tmp_path / "frozen",
            "sources": sources,
            "collected_since": "2026-09-24T00:00:00Z",
        }
    )
    report = freeze(config)
    assert report["unique_episodes"] == 1
    assert set(report["earliest_download_utc"]) == {"3"}
    assert report["preexisting_daily_episode_ids"] == [2]
    write_json(
        archive.parent / "manifest.json",
        {
            "verified_at_utc": "2026-09-24T01:00:00Z",
            "daily_archives": [{"path": str(archive)}],
        },
    )
    with pytest.raises(ValueError, match="provable pre-cutoff"):
        freeze(config.model_copy(update={"output": tmp_path / "uncertain"}))
