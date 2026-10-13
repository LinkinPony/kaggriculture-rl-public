"""Range fidelity, weighted trends, change boundaries, and live append behavior."""

import json
from array import array
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from kagg_revue.monitor.artifacts import RunRepository
from kagg_revue.monitor.config import MonitorSettings
from kagg_revue.monitor.curves import CurveQuery, CurveReader, column_curves
from kagg_revue.monitor.history import HistoryReader, ScalarHistory


def settings() -> MonitorSettings:
    return MonitorSettings(
        outputs_dir=Path("outputs"),
        port=8765,
        refresh_seconds=5,
        stale_after_seconds=180,
        max_points=400,
    )


def test_trends_use_full_weighted_windows_before_the_visible_range() -> None:
    column = ScalarHistory(
        steps=array("q", [1, 2, 3, 4]),
        values=array("d", [0.5, 1, 0, 0.5]),
        weights=array("d", [2, 8, 8, 2]),
    )
    raw, trend, summary = column_curves(column, 4, 4, 2, 100)
    assert raw == [{"step": 4, "value": 0.5, "segment": 0}]
    assert trend[0]["value"] == pytest.approx(0.1)
    assert summary["previous_mean"] == pytest.approx(0.9)
    assert summary["delta"] == pytest.approx(-0.8)
    assert summary["samples"] == 10
    assert summary["count"] == 2


def test_old_ranges_and_spikes_survive_long_history_and_downsampling(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    path.write_text(
        "".join(
            json.dumps(
                {
                    "update": step,
                    "optimization": {"maximum_prefix_kl": 9 if step == 211 else 0.01},
                }
            )
            + "\n"
            for step in range(1, 3001)
        )
    )
    reader = CurveReader(settings())
    tag = "rl/optimization/maximum_prefix_kl"
    full = reader.read(path, CurveQuery(window=0))
    assert len(full["series"][tag]) <= 400
    assert any(point["step"] == 211 and point["value"] == 9 for point in full["series"][tag])
    assert full["series"][tag][0]["step"] == 1
    assert full["series"][tag][-1]["step"] == 3000
    zoom = reader.read(path, CurveQuery(start=201, end=220))
    assert [point["step"] for point in zoom["series"][tag]] == list(range(201, 221))
    assert zoom["summaries"][tag]["max"] == 9
    assert zoom["trends"][tag][10]["value"] == pytest.approx((31 * 0.01 + 9) / 32)
    assert reader.read(path, CurveQuery(start=201, end=220)) is zoom


def test_population_device_changes_and_absent_opponents_break_trends(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    rows = []
    for step, device, names in [
        (1, "cuda:0", ["a"]),
        (2, "cuda:1", ["a"]),
        (3, "cuda:1", ["b"]),
        (4, "cuda:1", ["a"]),
    ]:
        rows.append(
            {
                "update": step,
                "physical_games": 16,
                "history_score": None,
                "workers": [{"device": device}],
                "populations": {
                    name: {"games": 16, "wins": 16 if step == 1 else 0} for name in names
                },
            }
        )
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    result = CurveReader(settings()).read(path, CurveQuery(window=0))
    assert [(event["step"], event["kind"]) for event in result["events"]] == [
        (2, "execution"),
        (3, "population"),
        (4, "population"),
    ]
    trend = result["trends"]["rl/rollout/opponents/a/win_rate"]
    assert [point["step"] for point in trend] == [1, 2, 4]
    assert [point["value"] for point in trend] == [1, 0.5, 0]
    assert len({point["segment"] for point in trend}) == 2
    assert result["summaries"]["rl/rollout/opponents/a/win_rate"]["previous_mean"] is None


def sampled_row(
    step: int, name: str, games: int, wins: int, cash: float, *, unified: bool = False
) -> dict[str, Any]:
    populations = {
        "self_play": {"games": 40},
        name: {"games": games, "wins": wins, "mean_terminal_cash": cash},
    }
    if not unified:
        populations.setdefault("historical_self_play", {"games": 64, "wins": 32})
    history = populations.get("historical_self_play")
    return {
        "update": step,
        "physical_games": sum(panel["games"] for panel in populations.values()),
        "history_score": history["wins"] / history["games"] if history else None,
        "populations": populations,
        "pfsp": {
            "enabled": True,
            "unified": unified,
            "separate_scripts": not unified,
            "selfplay_fraction": 0.3,
            "pool_fraction": 0.7,
            "script_fraction": 0.2,
            "history_fraction": 0.5,
            "selected": {"kind": "history" if history else "script"},
            "scripts": {script: {"games": games if script == name else 0} for script in ("a", "b")},
        },
    }


@pytest.mark.parametrize("unified", [False, True])
def test_unsampled_pfsp_opponents_keep_connected_weighted_trends(
    tmp_path: Path, unified: bool
) -> None:
    path = tmp_path / "metrics.jsonl"
    rows = [
        sampled_row(step, name, games, wins, cash, unified=unified)
        for step, name, games, wins, cash in [
            (1, "a", 24, 12, 100),
            (2, "historical_self_play", 64, 32, 200),
            (3, "b", 28, 0, 50),
            (4, "a", 28, 21, 200),
            (5, "historical_self_play", 64, 64, 300),
        ]
    ]
    # Exercise the same cached history across polling requests.
    path.write_text(json.dumps(rows[0]) + "\n")
    reader = CurveReader(settings())
    reader.read(path, CurveQuery(window=0, smoothing=5))
    with path.open("a") as stream:
        stream.writelines(json.dumps(row) + "\n" for row in rows[1:])
    result = reader.read(path, CurveQuery(window=0, smoothing=5))
    assert result["events"] == []
    for field, expected, samples in [
        ("win_rate", 33 / 52, 52),
        ("mean_terminal_cash", (24 * 100 + 28 * 200) / 52, 52),
        ("games", 26, 2),
    ]:
        tag = f"rl/rollout/opponents/a/{field}"
        assert [point["step"] for point in result["series"][tag]] == [1, 4]
        assert [point["segment"] for point in result["trends"][tag]] == [0, 0]
        assert result["trends"][tag][-1]["value"] == pytest.approx(expected)
        assert result["summaries"][tag]["samples"] == samples
        zoom = reader.read(path, CurveQuery(start=4, end=4, smoothing=5))
        assert zoom["trends"][tag][0]["value"] == pytest.approx(expected)
    if unified:
        for tag in ("rl/rollout/opponents/history/win_rate", "rl/run/history_score"):
            points = result["trends"][tag]
            assert [point["step"] for point in points] == [2, 5]
            assert [point["segment"] for point in points] == [0, 0]
            assert points[-1]["value"] == 0.75


@pytest.mark.parametrize("interruption", ["population", "missing"])
def test_sparse_opponents_retain_interruptions_during_unsampled_rounds(
    tmp_path: Path, interruption: str
) -> None:
    path = tmp_path / "metrics.jsonl"
    rows = [sampled_row(step, "a" if step in (1, 4) else "b", 24, 12, 100) for step in range(1, 5)]
    if interruption == "population":
        for row in rows[1:]:
            row["pfsp"]["scripts"]["c"] = {"games": 0}
    else:
        # Games were played, but their outcome fields are missing.
        rows[1]["populations"]["a"] = {"games": 24}
        rows[1]["pfsp"]["scripts"]["a"]["games"] = 24
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    result = CurveReader(settings()).read(path, CurveQuery(window=0))
    assert [event["step"] for event in result["events"]] == (
        [2] if interruption == "population" else []
    )
    for field in ("win_rate", "mean_terminal_cash"):
        tag = f"rl/rollout/opponents/a/{field}"
        assert [point["segment"] for point in result["trends"][tag]] == [0, 1]
        assert result["summaries"][tag]["count"] == 1


def test_history_tails_complete_rows_and_rebuilds_after_truncation(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"

    def row(step):
        return json.dumps({"update": step, "optimization": {"value_loss": step}})

    path.write_text(row(1) + "\n" + row(2))
    reader = HistoryReader(cache_runs=1)
    history = reader.read(path)
    assert history.last_step == 1
    with path.open("a") as stream:
        stream.write("\n" + row(3) + "\n")
    assert reader.read(path) is history
    assert history.last_step == 3
    path.write_text(row(7) + "\n")
    assert reader.read(path).last_step == 7
    assert reader.read(path).series["rl/optimization/value_loss"].steps.tolist() == [7]


def test_curve_queries_validate_bounds_and_serve_only_resolved_runs(tmp_path: Path) -> None:
    run = tmp_path / "outputs/learning/run"
    run.mkdir(parents=True)
    (run / "metrics.jsonl").write_text('{"update":1,"optimization":{"value_loss":2}}\n')
    repository = RunRepository(tmp_path, settings())
    result = repository.curves("learning/run", CurveQuery(start=1, end=1, smoothing=8))
    assert result["trends"]["rl/optimization/value_loss"][0]["value"] == 2
    for fields in (
        {"start": 8, "end": 2},
        {"smoothing": 0},
        {"start": -1},
        {"tags": tuple(f"tag_{index}" for index in range(129))},
    ):
        with pytest.raises(ValidationError):
            CurveQuery(**fields)
    for run_id in ("learning/missing", "learning/run/nested", "../learning/run"):
        with pytest.raises(FileNotFoundError):
            repository.curves(run_id, CurveQuery())


@pytest.mark.parametrize("tag_count", [75, 128])
def test_curve_queries_serve_full_league_chart_count_up_to_the_limit(
    tmp_path: Path, tag_count: int
) -> None:
    run = tmp_path / "outputs/learning/run"
    run.mkdir(parents=True)
    values = {f"value_{index}": index for index in range(tag_count)}
    (run / "metrics.jsonl").write_text(json.dumps({"update": 1, "optimization": values}) + "\n")
    tags = tuple(f"rl/optimization/{name}" for name in values)
    curves = RunRepository(tmp_path, settings()).curves("learning/run", CurveQuery(tags=tags))
    assert set(curves["series"]) == set(curves["trends"]) == set(tags)
    for tag, value in zip(tags, values.values(), strict=True):
        assert curves["trends"][tag][-1]["value"] == value
