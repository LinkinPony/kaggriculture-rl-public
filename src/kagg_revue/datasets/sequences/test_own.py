"""Protect account identity and game-time boundaries for own BC teacher seats."""

import json
from pathlib import Path

import pytest

from kagg_revue.artifacts.io import write_json
from kagg_revue.datasets.sequences.own import OwnSettings, freeze


def test_own_games_use_creation_time_and_authenticated_available_seats(tmp_path: Path) -> None:
    """Include older policy versions playing new games, but reject a different account."""
    episodes = [
        {
            "id": key,
            "createTime": date,
            "state": "COMPLETED",
            "type": "EPISODE_TYPE_PUBLIC",
            "agents": [
                {"teamId": 1, "submissionId": 10, "teamName": "Own"},
                {
                    "teamId": 2,
                    "submissionId": 99 if key == 5 else 20,
                    "teamName": "Other",
                    "index": 1,
                },
            ],
        }
        for key, date in (
            (1, "2026-09-24T16:00:59.999Z"),
            (2, "2026-09-25T00:01:00+08:00"),
            (3, "2026-09-25T00:00:00Z"),
            (4, "2026-09-25T01:00:00Z"),
            (5, "2026-09-25T02:00:00Z"),
        )
    ]
    source = tmp_path / "collector.json"
    original = {
        "updated_utc": "2026-09-26T00:00:00Z",
        "episodes": episodes,
        "replays": [{"episode_id": key} for key in (1, 2, 3, 5)],
        "own_submission_ids": [10],
        "excluded_submissions": [99],
    }
    write_json(source, original)
    config = OwnSettings.model_validate(
        {
            "output": tmp_path / "frozen",
            "sources": {"collector": source},
            "team_id": 1,
            "team_name": "Own",
            "created_since": "2026-09-24T16:01:00Z",
        }
    )
    report = freeze(config)
    assert report["episodes"] == report["teacher_trajectories"] == 2
    assert report["not_collected_episode_ids"] == [4]
    selected = json.loads((config.output / "selected.json").read_text())
    assert [e["id"] for e in selected["episodes"]] == [2, 3]
    assert [s["id"] for s in selected["submissions"]] == [10]
    write_json(source, {**original, "own_submission_ids": [30]})
    assert freeze(config) == report
    with pytest.raises(ValueError, match="authenticated account"):
        freeze(config.model_copy(update={"output": tmp_path / "wrong-account"}))
