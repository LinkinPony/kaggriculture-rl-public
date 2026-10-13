"""Opponent attribution, weighted evidence, cursor stability and shared incremental reads."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from kagg_revue.monitor.artifacts import RunRepository
from kagg_revue.monitor.config import MonitorSettings
from kagg_revue.monitor.curves import CurveQuery
from kagg_revue.monitor.opponents.query import OpponentQuery


def settings() -> MonitorSettings:
    """Use the production point budgets and a local temporary output root."""
    return MonitorSettings(
        outputs_dir=Path("outputs"),
        port=8765,
        refresh_seconds=5,
        stale_after_seconds=180,
        max_points=400,
    )


def member(name: str, *, script: bool = False) -> dict[str, Any]:
    """Give two models the same checkpoint number but distinct immutable identities."""
    kind = "script" if script else "history"
    return {
        "key": f"{kind}:{name}",
        "kind": kind,
        "name": name,
        "update": 512,
        "path": f"historical/{name}/update-000512.pt",
        "source_run": f"outputs/learning/{name}",
        "score": 0.6,
        "probability": 0.2,
    }


def battle(
    update: int,
    entry: dict[str, Any],
    games: int,
    wins: int,
    ties: int = 0,
    cash: float = 100,
) -> dict[str, Any]:
    """Produce realistic global telemetry, including worker data that must be ignored."""
    panel = {
        "games": games,
        "wins": wins,
        "ties": ties,
        "losses": games - wins - ties,
        "mean_terminal_cash": cash,
        "mean_cash_difference": cash / 10,
    }
    name = entry["name"] if entry.get("kind") == "script" else "historical_self_play"
    return {
        "update": update,
        "physical_games": games + 4,
        "history_score": wins / games,
        "populations": {name: panel, "self_play": {"games": 4, "wins": 2}},
        "pfsp": {"enabled": True, "selected": entry},
        "workers": [{"populations": {name: panel}}] * 2,
    }


def setup_run(tmp_path: Path, rows: list[dict[str, Any]]) -> tuple[RunRepository, Path]:
    """Write only the committed records needed by the dashboard."""
    run = tmp_path / "outputs/learning/example"
    run.mkdir(parents=True)
    (run / "metrics.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    return RunRepository(tmp_path, settings()), run


def test_attribution_weighting_live_membership_and_ranges(tmp_path: Path) -> None:
    """Separate learner identities and report real sample mass rather than batch means."""
    a, b, script, unseen = member("a"), member("b"), member("script", script=True), member("new")
    rows = [
        battle(1, a, 2, 1, 1),
        battle(2, b, 4, 0),
        battle(3, script, 4, 3, 1),
        battle(4, a, 8, 6, cash=300),
        battle(5, {}, 4, 4),
    ]
    repo, run = setup_run(tmp_path, rows)
    (run / "learning-progress.json").write_text(
        json.dumps(
            {
                "update": 7,
                "pfsp": {"update": 7, "history": [a, script, unseen]},
            }
        )
    )
    result: Any = repo.opponents(
        "learning/example", OpponentQuery(start=4, end=5, opponent=a["key"])
    )
    entries = {row["key"]: row for row in result["entries"]}
    actual = entries[a["key"]]
    assert actual["lifetime"]["games"] == 10
    assert actual["lifetime"]["wins"] == 7
    assert actual["lifetime"]["win_rate"] == 0.7
    assert actual["lifetime"]["observed_score"] == 0.75
    assert actual["lifetime"]["mean_terminal_cash"] == 260
    assert actual["interval"]["win_rate"] == 0.75
    assert entries[b["key"]]["in_pool"] is False
    assert entries[b["key"]]["interval"]["win_rate"] is None
    assert entries[unseen["key"]]["lifetime"]["win_rate"] is None
    assert entries[script["key"]]["lifetime"]["games"] == 4
    assert result["unassigned_games"] == 4
    assert result["saved_update"] == 5 and result["pfsp_update"] == 7
    selected: Any = result["selected"]
    assert selected["batches"]["rows"][0]["sampling_score"] == 0.6
    assert selected["curves"]["trends"]["win_rate"][0]["value"] == 0.7
    assert selected["curves"]["summaries"]["win_rate"]["samples"] == 10
    json.dumps(result, allow_nan=False)


def test_shared_append_partial_line_cursor_and_replacement(tmp_path: Path) -> None:
    """Keep earlier pages stable across appends and discard statistics after rollback."""
    a = member("a")
    repo, run = setup_run(tmp_path, [battle(i, a, 4, i % 4) for i in range(1, 5)])
    query = OpponentQuery(window=0, opponent=a["key"], limit=2)
    first: Any = repo.opponents("learning/example", query)
    assert [row["update"] for row in first["selected"]["batches"]["rows"]] == [4, 3]
    assert first["selected"]["batches"]["next_before"] == 3
    path = run / "metrics.jsonl"
    with path.open("a") as stream:
        stream.write(json.dumps(battle(5, a, 4, 4)) + "\n" + '{"update":6')
    curves = repo.curves("learning/example", CurveQuery(window=0))
    assert curves["extent"] == {"start": 1, "end": 5}
    second: Any = repo.opponents("learning/example", query.model_copy(update={"before": 3}))
    assert [row["update"] for row in second["selected"]["batches"]["rows"]] == [2, 1]
    assert second["selected"]["lifetime"]["games"] == 20
    assert second["selected"]["batches"]["next_before"] is None
    path.write_text(json.dumps(battle(1, a, 2, 1)) + "\n")
    rolled: Any = repo.opponents("learning/example", query)
    assert rolled["selected"]["lifetime"]["games"] == 2
    replacement = run / "replacement.jsonl"
    replacement.write_text(json.dumps(battle(1, a, 8, 8)) + "\n")
    replacement.replace(path)
    replaced: Any = repo.opponents("learning/example", query)
    assert replaced["selected"]["lifetime"]["games"] == 8
    # Re-reading an unchanged file cannot credit the same physical games twice.
    assert repo.opponents("learning/example", query) == replaced


def test_legacy_identity_and_incomplete_outcomes(tmp_path: Path) -> None:
    """Read recorded model hashes and leave absent legacy script identities unassigned."""
    row = battle(1, {"sha256": "old", "path": "checkpoints/update-000512.pt"}, 8, 5)
    row["opponent"] = row.pop("pfsp")["selected"]
    broken = battle(2, member("a"), 8, 5)
    del broken["populations"]["historical_self_play"]["ties"]
    repo, _ = setup_run(tmp_path, [row, broken])
    result: Any = repo.opponents("learning/example", OpponentQuery(opponent="history:old"))
    assert result["selected"]["lifetime"]["games"] == 8
    assert result["selected"]["in_pool"] is None
    assert result["selected"]["batches"]["rows"][0]["sampling_score"] is None
    assert result["invalid_panels"] == 1


def test_query_validation_and_finite_empty_detail(tmp_path: Path) -> None:
    """Reject invalid ranges and run paths; preserve nulls for an unplayed opponent."""
    repo, run = setup_run(tmp_path, [])
    a = member("unseen")
    (run / "learning-progress.json").write_text(json.dumps({"pfsp": {"history": [a]}}))
    result: Any = repo.opponents("learning/example", OpponentQuery(opponent=a["key"]))
    assert result["selected"]["batches"]["rows"] == []
    assert result["selected"]["curves"]["series"]["win_rate"] == []
    json.dumps(result, allow_nan=False)
    for parameters in ({"start": 5, "end": 2}, {"limit": 201}, {"before": 0}):
        with pytest.raises(ValidationError):
            OpponentQuery.model_validate(parameters)
    with pytest.raises(FileNotFoundError):
        repo.opponents("learning/missing", OpponentQuery())
    with pytest.raises(FileNotFoundError):
        repo.opponents("../outside", OpponentQuery())
