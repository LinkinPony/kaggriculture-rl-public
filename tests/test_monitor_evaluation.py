"""Independent match history uses only synthetic evidence artifacts."""

import json
from pathlib import Path

import numpy as np
import pytest

from kagg_revue.monitor.evaluation import EvaluationHistoryReader, summarize_matches


def test_match_summary_preserves_candidate_perspective_and_weighted_population() -> None:
    summary = summarize_matches(
        np.array(["alpha", "alpha", "beta"]),
        np.array([[4, 2], [3, 3], [1, 8]]),
        np.array([1, 0, -1]),
    )
    overall = summary["overall"]
    assert (overall["wins"], overall["ties"], overall["losses"]) == (1, 1, 1)
    assert overall["mean_terminal_cash"] == pytest.approx(8 / 3)
    assert overall["mean_cash_difference"] == pytest.approx(-5 / 3)
    assert summary["opponents"]["alpha"]["games"] == 2
    assert summary["opponents"]["beta"]["wins"] == 0
    assert sum(row["games"] for row in summary["opponents"].values()) == overall["games"]


def test_history_prefers_match_details_and_recovers_after_partial_artifact(tmp_path: Path) -> None:
    selection = tmp_path / "selection"
    selection.mkdir()
    step = 2
    summary = {"update": step, "wins": 1, "ties": 1, "losses": 0, "mean_cash": 3.5}
    log = tmp_path / "selection-metrics.jsonl"
    log.write_text(json.dumps(summary) + "\n" + '{"update":')
    path = selection / f"update-{step}.npz"
    path.write_bytes(b"unfinished archive")
    reader = EvaluationHistoryReader()
    partial = reader.read(tmp_path)
    assert len(partial["points"]) == 1
    assert not partial["points"][0]["opponents"]
    assert partial["unreadable_sources"]

    np.savez(
        path,
        opponents=np.array(["alpha", "beta"]),
        cash=np.array([[4, 2], [3, 3]]),
        outcomes=np.array([1, 0]),
    )
    complete = reader.read(tmp_path)
    assert not complete["unreadable_sources"]
    assert len(complete["points"]) == 1
    assert complete["points"][0]["step"] == step
    assert set(complete["points"][0]["opponents"]) == {"alpha", "beta"}
    assert reader.read(tmp_path) == complete
    log.write_text(json.dumps(summary) + "\n" + json.dumps({**summary, "update": step + 1}) + "\n")
    updated = reader.read(tmp_path)
    assert [point["step"] for point in updated["points"]] == [step, step + 1]
    assert not updated["points"][-1]["opponents"]


def test_comparison_history_keeps_greedy_and_sampled_panels_separate(tmp_path: Path) -> None:
    directory = tmp_path / "selection" / "update-3"
    directory.mkdir(parents=True)
    game = {"opponent": "alpha", "cash": 3, "opponent_cash": 1, "outcome": 1}
    report = {
        "results": {
            "greedy": {"games": [game]},
            "sampled": {"games": [{**game, "cash": 0, "outcome": -1}], "temperature": 0.75},
        }
    }
    (directory / "comparison.json").write_text(json.dumps(report))
    history = EvaluationHistoryReader().read(tmp_path)
    panels = {point["mode"]: point for point in history["points"]}
    assert panels["greedy"]["overall"]["wins"] == 1
    assert panels["sampled"]["overall"]["wins"] == 0
    assert panels["sampled"]["temperature"] == report["results"]["sampled"]["temperature"]
