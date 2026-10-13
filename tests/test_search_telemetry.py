import json
from pathlib import Path
from typing import Any

from kagg_revue.monitor.metrics import JsonlMetricReader
from kagg_revue.production.expert.telemetry import (
    candidate_summary,
    generation_summary,
    panel_summary,
)


def _panel(outcomes: list[int]) -> dict[str, Any]:
    games = [
        {"opponent": "rival", "outcome": outcome, "cash": 10 + outcome, "opponent_cash": 10}
        for outcome in outcomes
    ]
    return {
        "wins": outcomes.count(1),
        "ties": outcomes.count(0),
        "losses": outcomes.count(-1),
        "mean_cash": sum(game["cash"] for game in games) / len(games),
        "mean_cash_difference": sum(outcomes) / len(outcomes),
        "games": games,
    }


def test_candidate_gain_does_not_hide_population_regression() -> None:
    baseline = _panel([0, 0])
    candidate = {
        "candidate": 0,
        "mutation_seed": 0,
        "scale": 0.5,
        "scripts": _panel([0, -1]),
        "neural": _panel([1, 1]),
    }
    observed = candidate_summary(candidate, {"scripts": baseline, "neural": baseline})
    assert observed["scripts_wdl_gain"] + observed["neural_wdl_gain"] > 0
    assert not observed["eligible"]
    assert "games" not in observed["scripts"] or isinstance(observed["scripts"]["games"], int)


def test_adopted_panels_remain_separate_from_search_winner() -> None:
    baseline, proposal = _panel([0, 0]), _panel([1, 1])
    candidate = {
        "candidate": 0,
        "mutation_seed": 0,
        "scale": 0.5,
        "scripts": proposal,
        "neural": proposal,
    }
    controls = {"scripts": baseline, "neural": baseline}
    ranks = [
        {
            "rank": 0,
            "search": {
                "seed_start": 0,
                "controls": controls,
                "candidates": [candidate_summary(candidate, controls)],
            },
        }
    ]
    selected = {
        "seed_start": 1,
        "selected": None,
        "paired_scripts": {},
        "paired_neural": {},
        "scripts": baseline,
        "neural": baseline,
        "baseline_scripts": baseline,
        "baseline_neural": baseline,
        "candidates": [],
    }
    summary = generation_summary(ranks, selected)
    assert summary["counts"]["eligible"] > summary["counts"]["accepted"]
    assert summary["selection"]["scripts"]["wins"] == baseline["wins"]
    assert summary["search"]["candidates"][0]["scripts"]["wins"] == proposal["wins"]
    assert summary["selection"]["scripts"]["opponents"]["rival"]["ties"] == len(baseline["games"])
    assert isinstance(panel_summary(proposal)["games"], int)


def test_generation_ingestion_is_incremental_and_counts_only_adoptions(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    rows = [
        {
            "generation": index,
            "timestamp": float(index),
            "accepted_policy_update": accepted,
            "timing": {
                "generation_seconds": 4,
                "physical_games": 8,
                "physical_games_per_second": 2,
            },
            "policy_search": {"counts": {"accepted": int(accepted)}},
        }
        for index, accepted in enumerate((True, False, True), start=1)
    ]
    path.write_text(json.dumps(rows[0]) + "\n" + json.dumps(rows[1]))
    reader = JsonlMetricReader(max_points=10)
    first = reader.read(path)
    assert first.row_count == 1
    assert first.series["search/counts/accepted_total"][0].wall_time == rows[0]["timestamp"]
    with path.open("a") as stream:
        stream.write("\n" + json.dumps(rows[2]) + "\n")
    final = reader.read(path)
    assert final.latest["search/counts/accepted_total"] == sum(
        row["accepted_policy_update"] for row in rows
    )
    assert final.row_count == len(rows)
    assert reader.read(path).latest == final.latest
    assert final.context["generation"] == final.last_step
    assert not any(tag.startswith("rl/") for tag in final.latest)


def test_old_generation_without_archives_still_has_timing(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    first = {
        "generation": 0,
        "accepted_policy_update": False,
        "policy_search": {"selection": {"scripts": _panel([1])}},
    }
    row = {"generation": 1, "accepted_policy_update": False, "timing": {"generation_seconds": 2}}
    path.write_text(json.dumps(first) + "\n" + json.dumps(row) + "\n")
    snapshot = JsonlMetricReader(max_points=10).read(path)
    assert (
        snapshot.latest["search/timing/generation_seconds"] == row["timing"]["generation_seconds"]
    )
    assert snapshot.last_step == row["generation"]
    assert "search/selection/scripts/wins" not in snapshot.latest
    assert snapshot.series["search/selection/scripts/wins"]


def test_apprentice_metrics_separate_student_quality_and_collection_throughput(
    tmp_path: Path,
) -> None:
    path = tmp_path / "metrics.jsonl"
    row = {
        "update": 1,
        "training_phase": "expert_iteration",
        "physical_games": 12,
        "training_games": 4,
        "physical_games_per_second": 3,
        "optimizer_steps": 2,
        "workers": [
            {
                "rollout": {"rollout_seconds": 2},
                "optimization": {"actor_steps": 2, "encoder_parameter_delta_l2": 0.2},
            }
        ],
        "evaluation": {
            "neural": {
                "student": {"wins": 2, "ties": 1, "losses": 1},
                "expert": {"wins": 3, "ties": 0, "losses": 1},
            }
        },
    }
    path.write_text(json.dumps(row) + "\n")
    latest = JsonlMetricReader(max_points=5).read(path).latest
    assert latest["rl/rollout/games_per_second"] == row["training_games"] / 2
    assert latest["rl/system/physical_games_per_second"] == row["physical_games_per_second"]
    assert latest["rl/evaluation/neural/student/wins"] < latest["rl/evaluation/neural/expert/wins"]
    assert latest["rl/optimization/optimizer_steps"] == row["optimizer_steps"]
    assert latest["rl/optimization/encoder_parameter_delta_l2"] > 0
    skipped = {
        **row,
        "update": row["update"] + 1,
        "training_games": 0,
        "learning": {"performed": False, "fits": 1},
        "workers": [{"rollout": {"rollout_seconds": 0}, "optimization": {"actor_steps": 0}}],
        "evaluation": {},
    }
    with path.open("a") as stream:
        stream.write(json.dumps(skipped) + "\n")
    snapshot = JsonlMetricReader(max_points=5).read(path)
    assert not snapshot.context["learning"]["performed"]
    assert snapshot.latest["rl/optimization/optimizer_steps"] == row["optimizer_steps"]
    assert snapshot.latest["rl/optimization/actor_steps"] == 0
    assert snapshot.latest["rl/rollout/physical_games"] == 0
    assert len(snapshot.series["rl/evaluation/neural/student/wins"]) == 1


def test_state_branch_labels_never_replace_independent_student_outcomes(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    row = {
        "update": 1,
        "training_phase": "state_branch",
        "physical_games_per_second": 3,
        "optimizer_steps": 2,
        "training_games": 4,
        "search": {"roots": 4, "improved_roots": 3, "hindsight_labels_only": True},
        "workers": [{"rank": 0, "search": {"candidates": []}}],
        "evaluation": {"scripts": {"student": {"wins": 1}, "initial": {"wins": 2}}},
    }
    path.write_text(json.dumps(row) + "\n")
    result = JsonlMetricReader(max_points=5).read(path)
    assert (
        result.latest["rl/search/improved_roots"]
        > result.latest["rl/evaluation/scripts/student/wins"]
    )
    assert (
        result.latest["rl/evaluation/scripts/initial/wins"]
        == row["evaluation"]["scripts"]["initial"]["wins"]
    )
    assert result.context["search"]["hindsight_labels_only"]
