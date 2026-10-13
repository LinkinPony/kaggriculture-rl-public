"""Random-root progress and fixed-seed match roles remain distinct in the UI."""

import json
from pathlib import Path

from kagg_revue.monitor.artifacts import RunRepository
from kagg_revue.monitor.config import MonitorSettings
from kagg_revue.monitor.metrics import JsonlMetricReader


def test_learning_pretraining_live_progress_and_sampled_evaluation_roles(tmp_path: Path) -> None:
    run = tmp_path / "outputs/learning/run"
    run.mkdir(parents=True)
    (run / "resolved-config.json").write_text(json.dumps({"updates": 100000}))
    (run / "run-status.json").write_text(json.dumps({"status": "running"}))
    (run / "learning-progress.json").write_text(
        json.dumps({"phase": "demonstrations", "cursor": 7, "total_shards": 672, "update": 0})
    )
    repository = RunRepository(
        tmp_path,
        MonitorSettings(
            outputs_dir=Path("outputs"),
            port=8765,
            refresh_seconds=5,
            stale_after_seconds=180,
            max_points=400,
        ),
    )
    detail = repository.detail("learning/run", {"learning/run"}, [])
    assert detail["run"]["kind"] == "rl"
    assert detail["run"]["status"] == "running"
    assert detail["run"]["progress"]["target"] == 100000
    assert detail["run"]["progress"]["current"] == 0
    assert detail["run"]["learning"]["cursor"] == 7
    assert not detail["run"]["has_evaluation"]
    row = {
        "update": 4,
        "mean_cash": 70000,
        "history_score": 0.625,
        "physical_games": 128,
        "update_seconds": 16,
        "peak_allocated_bytes": 1234,
        "optimization": {"learner_seconds": 11, "actor_learning_rate": 0.000025},
        "rollout": {"rollout_seconds": 5},
    }
    (run / "metrics.jsonl").write_text(json.dumps(row) + "\n")
    (run / "run-status.json").write_text(json.dumps({"status": "complete"}))
    (run / "evaluation").mkdir()
    game = {"opponent": "anchor", "cash": 5, "opponent_cash": 2, "outcome": 1}
    for role, outcome in (("selection", 1), ("confirmation", -1)):
        (run / "evaluation" / f"{role}-000004.json").write_text(
            json.dumps(
                {"temperature": 1, "scope": "own controls", "games": [{**game, "outcome": outcome}]}
            )
        )
    detail = repository.detail("learning/run", set(), [])
    assert detail["run"]["status"] == "trained"
    assert detail["run"]["has_evaluation"]
    assert detail["run"]["progress"]["current"] == 4
    assert detail["run"]["headline"]["mean_terminal_cash"] == 70000
    assert detail["run"]["headline"]["wins"] is None
    assert detail["metrics"]["latest"]["rl/run/history_score"] == 0.625
    panels = {p["mode"]: p for p in detail["evaluation_history"]["points"]}
    assert panels["selection_sampled"]["overall"]["wins"] == 1
    assert panels["confirmation_sampled"]["overall"]["losses"] == 1


def test_learning_script_stats_follow_actual_batch_sizes_and_omit_missing_history(
    tmp_path: Path,
) -> None:
    path = tmp_path / "metrics.jsonl"
    rows = []
    for update, games, script_games, wins in (
        (316, 128, None, None),
        (458, 128, 8, 0),
        (459, 512, 32, 8),
    ):
        row = {"update": update, "physical_games": games, "history_score": 0.5}
        if script_games:
            row["populations"] = {
                "kaito_v39": {
                    "games": script_games,
                    "wins": wins,
                    "ties": 0,
                    "losses": script_games - wins,
                    "training_fraction": 0.0625,
                    "training_trajectories": script_games,
                    "mean_terminal_cash": 70000,
                    "mean_cash_difference": -15000,
                }
            }
        rows.append(row)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    reader = JsonlMetricReader(max_points=400)
    snapshot = reader.read(path)
    prefix = "rl/rollout/opponents/kaito_v39/"
    assert [(p.step, p.value) for p in snapshot.series[prefix + "win_rate"]] == [
        (458, 0),
        (459, 0.25),
    ]
    assert snapshot.latest[prefix + "games"] == 32
    assert snapshot.latest[prefix + "training_fraction"] == 0.0625
    assert snapshot.latest[prefix + "mean_cash_difference"] == -15000
    assert snapshot.latest["rl/run/script_mix"] == 1
    assert reader.read(path).row_count == 3


def test_population_switch_clears_current_opponents_and_retains_historical_series(tmp_path):
    path = tmp_path / "metrics.jsonl"
    old = {
        "update": 1,
        "physical_games": 128,
        "history_score": 0.25,
        "populations": {"kaito_v39": {"games": 16, "wins": 2, "ties": 0, "losses": 14}},
    }
    path.write_text(json.dumps(old) + "\n")
    reader = JsonlMetricReader(max_points=400)
    assert reader.read(path).latest["rl/run/history_score"] == 0.25
    latest = {
        "update": 106,
        "physical_games": 128,
        "history_score": None,
        "populations": {"self_play": {"games": 64, "training_trajectories": 128}},
    }
    for name in ("router_95", "farming_v4", "kaito_v58", "shop_router_0908"):
        latest["populations"][name] = {
            "games": 16,
            "wins": 3,
            "ties": 1,
            "losses": 12,
            "training_fraction": 0.125,
            "training_trajectories": 16,
            "mean_terminal_cash": 1000,
            "mean_cash_difference": -200,
        }
    with path.open("a") as stream:
        stream.write(json.dumps(latest) + "\n")
    snapshot = reader.read(path)
    assert "rl/run/history_score" not in snapshot.latest
    assert not any("kaito_v39" in tag for tag in snapshot.latest)
    assert snapshot.series["rl/rollout/opponents/kaito_v39/games"][0].step == 1
    assert snapshot.latest["rl/rollout/opponents/router_95/win_rate"] == 3 / 16
    assert snapshot.latest["rl/rollout/opponents/router_95/mean_cash_difference"] == -200
    assert (
        sum(
            value
            for tag, value in snapshot.latest.items()
            if tag.endswith("/training_trajectories")
        )
        == 192
    )
