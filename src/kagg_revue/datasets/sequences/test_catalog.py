"""Protect exact teacher membership, paired seats and historical selection compatibility."""

import json
import zipfile
from pathlib import Path

import pytest

from kagg_revue.datasets.sequences.catalog import catalog


def test_explicit_teacher_seats_and_missing_names(tmp_path: Path) -> None:
    """Select both requested seats once, exclude strangers and reject unmatched names."""
    source = tmp_path / "daily.zip"
    with zipfile.ZipFile(source, "w") as archive:
        for episode, pair in enumerate(
            (("M & M & P & Q", "Artem The Farmer 🍅"), ("DSM", "DSM extra")), 1
        ):
            archive.writestr(
                f"{episode}.json",
                json.dumps(
                    {
                        "info": {"EpisodeId": episode, "TeamNames": pair, "seed": 123},
                        "statuses": ["DONE", "DONE"],
                    }
                ),
            )
    entries = [
        (
            str(source),
            str(episode),
            "2026-09-20",
            {"create_time": "2026-09-20T00:00:00Z", "average_score": 1, "minimum_score": 0},
        )
        for episode in (1, 2)
    ]
    names = ("M & M & P & Q", "Artem The Farmer 🍅", "DSM")
    tasks, evidence = catalog(entries, names, None, 62001)
    assert [[seat["seat"] for seat in task["seats"]] for task in tasks] == [[0, 1], [0]]
    assert len({task["split"] for task in tasks}) == 1
    assert evidence["selected_teacher_trajectories"] == dict.fromkeys(names, 1)
    assert all("team_id" not in seat for task in tasks for seat in task["seats"])
    with pytest.raises(ValueError, match="absent.*Majkel1337"):
        catalog(entries, (*names, "Majkel1337"), None, 62001)
    screening = tmp_path / "screening.json"
    screening.write_text(json.dumps({"ranking_evidence": {"aliases": {"DSM": 42}}}))
    historical, evidence = catalog(entries, (), screening, 62001)
    assert len(historical) == 1
    assert historical[0]["seats"] == [{"seat": 0, "name": "DSM", "team_id": 42}]
    assert "ranking_evidence" in evidence
