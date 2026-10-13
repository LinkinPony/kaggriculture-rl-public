"""Check submission boundaries, seat identity and complete snapshot freezing."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.datasets.sequences.window import WindowSettings, freeze, select_window


def _manifest() -> dict[str, Any]:
    dates = ("2026-09-20T23:59:59Z", "2026-09-21T00:00:00Z", "2026-09-23T01:00:00Z")
    return {
        "team_id": 1,
        "team_name": "DSM",
        "updated_utc": dates[-1],
        "configuration": {"submitted_since": "2026-09-17T00:00:00Z"},
        "submissions": [{"id": i, "dateSubmitted": date} for i, date in enumerate(dates)],
        "episodes": [
            {
                "id": i,
                "createTime": "2026-09-23T00:30:00Z",
                "agents": [{"teamId": team, "submissionId": submission}],
            }
            for i, (team, submission) in enumerate(((1, 0), (1, 1), (1, 2), (2, 1)))
        ],
        "replays": [{"episode_id": 1}, {"episode_id": 2}, {"episode_id": 3}],
    }


def test_window_uses_submission_time_and_team_identity() -> None:
    """Include the exact start, exclude the end, and ignore unrelated backlog."""
    original = _manifest()
    selected = select_window(
        original,
        datetime.fromisoformat("2026-09-21T00:00:00Z"),
        datetime.fromisoformat("2026-09-23T01:00:00Z"),
    )
    assert [s["id"] for s in selected["submissions"]] == [1]
    assert [e["id"] for e in selected["episodes"]] == [1]
    assert selected["episodes"][0]["createTime"].startswith("2026-09-23")
    assert len(original["submissions"]) == 3
    original["replays"] = []
    with pytest.raises(ValueError, match="fully downloaded"):
        select_window(
            original,
            datetime.fromisoformat("2026-09-21T00:00:00Z"),
            datetime.fromisoformat("2026-09-23T01:00:00Z"),
        )


def test_freeze_retains_original_after_collector_advances(tmp_path: Path) -> None:
    """A replayable snapshot cannot silently switch to the live collector state."""
    source = tmp_path / "live.json"
    raw = json.dumps(_manifest()).encode()
    source.write_bytes(raw)
    config = WindowSettings.model_validate(
        {
            "source": source,
            "output": tmp_path / "frozen",
            "submitted_since": "2026-09-21T00:00:00Z",
        }
    )
    first = freeze(config)
    source.write_text("{}")
    assert freeze(config) == first
    assert (config.output / "collector-original.json").read_bytes() == raw
    changed = config.model_copy(
        update={"submitted_since": datetime.fromisoformat("2026-09-21T00:00:01Z")}
    )
    with pytest.raises(ValueError):
        freeze(changed)
