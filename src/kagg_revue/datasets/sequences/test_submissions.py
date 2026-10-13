"""Protect current-public OR submission-date selection across collector archives."""

import json
from pathlib import Path

import pytest

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.sequences.submissions import SubmissionSettings, freeze


def test_union_preserves_old_active_and_cross_collector_recent_games(tmp_path: Path) -> None:
    """Include the boundary, recover archived versions, and supervise only selected seats."""
    episodes = [
        {
            "id": key,
            "createTime": "2026-09-25T22:00:00Z",
            "state": "COMPLETED",
            "type": "EPISODE_TYPE_PUBLIC",
            "agents": [
                {"teamId": 1, "submissionId": first, "teamName": "one"},
                {"teamId": 2, "submissionId": second, "teamName": "two", "index": 1},
            ],
        }
        for key, first, second in (
            (1, 10, 20),
            (2, 12, 20),
            (3, 11, 21),
            (4, 13, 99),
            (5, 12, 20),
            (6, 11, 20),
        )
    ]
    sources = {}
    raw = tmp_path / "raw"
    for team, name in ((1, "one"), (2, "two")):
        versions = [
            {"id": team * 10, "dateSubmitted": "2026-09-23T00:00:00Z"},
            {"id": team * 10 + 1, "dateSubmitted": "2026-09-24T16:00:59.999Z"},
        ]
        outside = (
            [
                {"id": 12, "dateSubmitted": "2026-09-25T00:01:00+08:00"},
                {"id": 13, "dateSubmitted": "2026-09-25T00:00:00Z"},
            ]
            if team == 1
            else []
        )
        source = tmp_path / f"{name}.json"
        sources[name] = source
        write_json(
            source,
            {
                "team_id": team,
                "team_name": name,
                "updated_utc": "2026-09-26T00:00:00Z",
                "configuration": {"submitted_since": "2026-09-25T16:01:00Z"},
                "submissions": versions,
                "episodes": episodes,
                "replays": [
                    {"episode_id": key} for key in ((1, 3, 4, 6) if team == 1 else (1, 2, 3, 4, 6))
                ],
                "outside_scope": {"submissions": outside, "episodes": [], "replays": []},
            },
        )
        public = raw / name / "public-submissions.json"
        write_json(public, {"submissions": [versions[0]]})
        write_json(
            public.with_suffix(".source.json"),
            {
                "method": "list_team_public_submissions",
                "request": {"team_id": team},
                "sha256": digest(public),
                "retrieved_utc": "2026-09-26T00:00:00Z",
            },
        )
    config = SubmissionSettings.model_validate(
        {
            "output": tmp_path / "frozen",
            "raw": raw,
            "sources": sources,
            "submitted_since": "2026-09-24T16:01:00Z",
            "excluded_submissions": [99],
        }
    )
    report = freeze(config)
    assert report["unique_episodes"] == 3
    assert report["teacher_trajectories"] == 5
    assert report["sources"][0]["reused_other_collector_episode_ids"] == [2]
    assert report["sources"][0]["not_collected_episode_ids"] == [5]
    selected = json.loads((config.output / "one/selected.json").read_text())
    assert {row["id"] for row in selected["submissions"]} == {10, 12, 13}
    assert {row["id"] for row in selected["episodes"]} == {1, 2}
    assert selected["configuration"]["submitted_since"] is None
    assert selected["submissions"][0]["selection_reasons"] == ["current_public"]
    assert selected["submissions"][1]["selection_reasons"] == ["submitted_since"]
    for path in sources.values():
        path.write_text("{}")
    for path in raw.glob("*/public-submissions*.json"):
        path.write_text("{}")
    assert freeze(config) == report
    with pytest.raises(ValueError, match="cannot change frozen"):
        freeze(config.model_copy(update={"excluded_submissions": (99, 10)}))
