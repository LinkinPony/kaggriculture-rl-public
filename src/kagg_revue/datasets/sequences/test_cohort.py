"""Protect shared matches and immutable date-scoped teacher selections."""

import json
from pathlib import Path

import pytest

from kagg_revue.datasets.sequences.cohort import CohortSettings, freeze


def test_frozen_cohort_excludes_whole_games_and_keeps_teacher_scope(tmp_path: Path) -> None:
    """A blocked opponent excludes both teachers; an old healthy opponent stays context."""
    episodes = [
        {
            "id": key,
            "createTime": "2026-09-23T12:00:00Z",
            "agents": [
                {"teamId": 1, "submissionId": first},
                {"teamId": 2, "submissionId": second},
            ],
        }
        for key, first, second in ((1, 10, 20), (2, 10, 21), (3, 11, 20))
    ]
    sources = {}
    for team in (1, 2):
        path = tmp_path / f"team-{team}.json"
        manifest = {
            "team_id": team,
            "team_name": f"team-{team}",
            "updated_utc": f"2026-09-24T0{team}:00:00Z",
            "configuration": {"raw": str(tmp_path), "team_id": team, "team_name": f"team-{team}"},
            "submissions": [
                {"id": team * 10, "dateSubmitted": "2026-09-23T00:00:00Z"},
                {"id": team * 10 + 1, "dateSubmitted": "2026-09-22T23:59:59Z"},
            ],
            "episodes": episodes,
            "replays": [{"episode_id": e["id"]} for e in episodes],
        }
        path.write_text(json.dumps(manifest))
        sources[f"team-{team}"] = path
    config = CohortSettings.model_validate(
        {
            "output": tmp_path / "frozen",
            "sources": sources,
            "submitted_since": "2026-09-23T00:00:00Z",
            "excluded_submissions": [21],
        }
    )
    report = freeze(config)
    assert report["unique_episodes"] == 2
    assert report["teacher_trajectories"] == 3
    assert report["excluded_episode_ids"] == [2]
    assert report["submitted_before_exclusive"] == "2026-09-24T01:00:00+00:00"
    assert [r["episodes"] for r in report["sources"]] == [1, 2]
    for path in sources.values():
        assert len(json.loads(path.read_text())["episodes"]) == 3
        path.write_text("{}")
    assert freeze(config) == report
    with pytest.raises(ValueError, match="cannot change frozen"):
        freeze(config.model_copy(update={"excluded_submissions": (21, 999)}))
