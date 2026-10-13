"""Protect teacher seat scope when continuous collector datasets overlap."""

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from kagg_revue.datasets.sequences.sources import read_replay
from kagg_revue.datasets.sequences.watching import catalog


def _snapshots(root: Path) -> tuple[Path, ...]:
    """Create overlapping sources and an old DSM opponent outside its scope."""
    episodes = []
    replays = []
    for key, submission in ((1, 101), (2, 99)):
        raw = json.dumps(
            {
                "info": {"EpisodeId": key, "seed": key, "TeamNames": ["DSM", "MM"]},
                "statuses": ["DONE", "DONE"],
            }
        ).encode()
        path = root / f"{key}.json.gz"
        path.write_bytes(gzip.compress(raw))
        source = root / f"{key}.source.json"
        source.write_text(json.dumps({"raw_sha256": hashlib.sha256(raw).hexdigest()}))
        episodes.append(
            {
                "id": key,
                "createTime": "2026-09-22T00:00:00Z",
                "agents": [
                    {"teamId": 1, "submissionId": submission, "teamName": "DSM"},
                    {"teamId": 2, "submissionId": 201, "teamName": "MM", "index": 1},
                ],
            }
        )
        replays.append(
            {
                "episode_id": key,
                "path": str(path),
                "source": str(source),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    paths = []
    for team, name, count, submission in ((1, "DSM", 1, 101), (2, "MM", 2, 201)):
        path = root / f"team-{team}.json"
        path.write_text(
            json.dumps(
                {
                    "team_id": team,
                    "team_name": name,
                    "updated_utc": "2026-09-22T00:00:00Z",
                    "configuration": {
                        "submitted_since": "2026-09-17T00:00:00Z" if team == 1 else None
                    },
                    "submissions": [{"id": submission, "dateSubmitted": "2026-09-18T00:00:00Z"}],
                    "episodes": episodes[:count],
                    "replays": replays[:count],
                    "excluded_submissions": [],
                }
            )
        )
        paths.append(path)
    return tuple(paths)


def test_overlap_preserves_only_each_collectors_teacher_scope(tmp_path: Path) -> None:
    """Retain both eligible seats once, excluding the opponent's older DSM version."""
    tasks, sources, evidence = catalog(_snapshots(tmp_path), ("DSM", "MM"), 62001)
    assert sources["episodes"] == 2
    assert [[s["team_id"] for s in t["seats"]] for t in tasks] == [[1, 2], [2]]
    assert evidence["selected_teacher_trajectories"] == {"DSM": 1, "MM": 2}
    assert json.loads(read_replay(tasks[0]))["info"]["EpisodeId"] == 1
    Path(tasks[0]["path"]).write_bytes(gzip.compress(b"changed"))
    with pytest.raises(ValueError, match="changed after"):
        read_replay(tasks[0])


@pytest.mark.parametrize("invalid", ["excluded", "retired", "cutoff", "missing"])
def test_inconsistent_snapshot_is_rejected(tmp_path: Path, invalid: str) -> None:
    """Never silently train on excluded submissions or partially downloaded snapshots."""
    paths = _snapshots(tmp_path)
    manifest = json.loads(paths[0].read_text())
    if invalid == "excluded":
        manifest["excluded_submissions"] = [201]
    elif invalid == "retired":
        manifest["episodes"][0]["agents"][1]["submissionId"] = 56484772
    elif invalid == "cutoff":
        manifest["submissions"][0]["dateSubmitted"] = "2026-09-16T00:00:00Z"
    else:
        manifest["replays"] = []
    paths[0].write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        catalog(paths, ("DSM", "MM"), 62001)
