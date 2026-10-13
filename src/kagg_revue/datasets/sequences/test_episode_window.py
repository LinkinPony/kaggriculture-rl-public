"""Check game-date selection without replacing it with submission dates."""

import json
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.datasets.sequences.episode_window import EpisodeWindowSettings, freeze


def test_episode_dates_and_frozen_source(tmp_path: Path) -> None:
    """Keep an older version's game at the start, excluding both outer boundaries."""
    dates = ["2026-09-21T23:59:59Z", "2026-09-22T00:00:00Z", "2026-09-24T00:00:00Z"]
    manifest: dict[str, Any] = {
        "team_id": 1,
        "team_name": "DSM",
        "updated_utc": "2026-09-24T01:00:00Z",
        "configuration": {"submitted_since": "2026-09-17T00:00:00Z"},
        "submissions": [{"id": 7, "dateSubmitted": "2026-09-21T00:00:00Z"}],
        "episodes": [
            {"id": i, "createTime": date, "agents": [{"teamId": 1, "submissionId": 7}]}
            for i, date in enumerate(dates)
        ],
        "replays": [{"episode_id": 1}],
    }
    source = tmp_path / "live.json"
    source.write_text(json.dumps(manifest))
    config = EpisodeWindowSettings.model_validate(
        {
            "source": source,
            "output": tmp_path / "frozen",
            "created_since": dates[1],
            "created_before": dates[2],
            "expected_episodes": 1,
        }
    )
    report = freeze(config)
    selected = json.loads((config.output / "selected.json").read_text())
    assert [e["id"] for e in selected["episodes"]] == [1]
    assert selected["submissions"][0]["dateSubmitted"].startswith("2026-09-21")
    source.write_text("{}")
    assert freeze(config) == report
    with pytest.raises(ValueError, match="episode count"):
        freeze(config.model_copy(update={"expected_episodes": 2}))
