"""League telemetry survives the BC-to-PPO transition and both GPU replicas."""

import json
import os
from pathlib import Path

from kagg_revue.monitor.artifacts import RunRepository
from kagg_revue.monitor.config import MonitorSettings
from kagg_revue.monitor.curves import CurveQuery
from kagg_revue.monitor.league import metrics


def _row(update: int, games: int = 4, wins: int = 1) -> dict:
    return {
        "update": update,
        "physical_games": games,
        "cumulative_physical_games": update * games,
        "update_seconds": 20,
        "pairs": {
            "a_vs_bc": {
                "games": games,
                "wins": wins,
                "draws": 1,
                "losses": games - wins - 1,
                "cash_left_sum": 10 * games,
                "cash_right_sum": 20 * games,
            },
        },
        "workers": [
            {
                "rank": rank,
                "physical_games": games // 2,
                "rollout_seconds": 5 + rank,
                "peak_allocated_bytes": 100 + rank,
                "optimization": {
                    name: {
                        "actor_steps": 2,
                        "critic_steps": 4,
                        "rejected_actor_steps": 0,
                        "value_loss": 3 + rank,
                        "actor_learning_rate": 0.001,
                        "maximum_prefix_kl": 0.01 + rank / 100,
                        "learner_seconds": 3 + rank,
                        "actor_early_stop": False,
                    }
                    for name in ("a", "bc", "spataro")
                },
            }
            for rank in (0, 1)
        ],
    }


def test_league_uses_global_games_and_replica_steps_with_left_relative_outcomes() -> None:
    result = metrics(_row(1))
    assert result["rl/rollout/physical_games"] == 4
    assert result["rl/system/physical_games_per_second"] == 0.2
    assert result["rl/rollout/games_per_second"] == 4 / 6
    assert result["rl/system/optimization_seconds"] == 12
    assert result["rl/system/cuda_peak_allocated_bytes"] == 101
    assert result["rl/league/ranks/0/peak_allocated_bytes"] == 100
    assert result["rl/league/optimization/a/actor_steps"] == 2
    assert result["rl/league/optimization/a/value_loss"] == 3.5
    assert result["rl/league/optimization/a/maximum_prefix_kl"] == 0.02
    assert result["rl/league/optimization/a/actor_early_stop"] == 0
    assert result["rl/league/pairs/a_vs_bc/win_rate"] == 0.25
    assert result["rl/league/pairs/a_vs_bc/ties"] == 1
    assert result["rl/league/pairs/a_vs_bc/mean_cash_difference"] == -10
    assert result["rl/league/members/bc/wins"] == 2
    assert result["rl/league/members/bc/mean_terminal_cash"] == 20
    assert result["rl/rollout/mean_terminal_cash"] == 15
    assert "rl/rollout/win_rate" not in result
    assert "rl/optimization/actor_steps" not in result


def test_league_bc_progress_refresh_then_rl_curves_and_separate_evaluation(tmp_path: Path) -> None:
    run = tmp_path / "outputs/learning/league"
    (run / "a").mkdir(parents=True)
    config = {
        "experiment": {"updates": 100000, "games": 192, "checkpoint_interval": 4},
        "games_per_pair": 64,
        "bc_epochs": 6,
    }
    (run / "resolved-config.json").write_text(json.dumps(config))
    (run / "league-progress.json").write_text(
        json.dumps(
            {
                "phase": "bc",
                "active_member": "a",
                "epochs": 6,
                "members": {"a": {}},
            }
        )
    )
    child = run / "a/learning-progress.json"
    child.write_text(json.dumps({"phase": "demonstrations", "epoch": 1, "cursor": 3}))
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
    detail = repository.detail("learning/league", {"learning/league"}, [])
    assert detail["run"]["progress"]["target"] == 100000
    assert detail["run"]["progress"]["current"] == 0
    assert detail["run"]["learning"]["phase"] == "demonstrations"
    assert detail["run"]["learning"]["cursor"] == 3
    previous = detail["run"]["modified_timestamp"]
    child.write_text(json.dumps({"epoch": 1, "cursor": 4, "selection_nll": 0.5}))
    os.utime(child, (previous + 1, previous + 1))
    detail = repository.detail("learning/league", set(), [], after_modified=previous)
    assert "unchanged" not in detail
    assert detail["run"]["learning"]["cursor"] == 4

    (run / "league-progress.json").write_text(
        json.dumps(
            {
                "phase": "rl",
                "completed_update": 2,
                "members": {"a": {"bc_epochs": 6}},
            }
        )
    )
    (run / "run-status.json").write_text(json.dumps({"status": "running", "completed_update": 1}))
    path = run / "metrics.jsonl"
    path.write_text(json.dumps(_row(1)) + "\n")
    (run / "evaluation").mkdir()
    evaluation = _row(0)
    del evaluation["workers"]
    (run / "evaluation/update-000000.json").write_text(json.dumps(evaluation))
    detail = repository.detail("learning/league", set(), [])
    assert detail["metrics"]["scalar_count"] > 30
    assert detail["metrics"]["last_step"] == 1
    assert detail["run"]["learning"]["update"] == 2
    assert detail["run"]["learning"]["checkpoint_update"] == 1
    assert detail["run"]["learning"]["pretraining"]["a"]["completed_epochs"] == 6
    assert detail["run"]["has_evaluation"]
    point = detail["evaluation_history"]["points"][0]
    assert point["step"] == 0
    assert point["pairs"]["a_vs_bc"]["mean_cash_left"] == 10
    assert "overall" not in point
    tag = "rl/league/pairs/a_vs_bc/win_rate"
    repository.curves("learning/league", CurveQuery(tags=(tag,)))
    with path.open("a") as stream:
        stream.write(json.dumps(_row(2, games=8, wins=6)) + "\n")
    curves = repository.curves("learning/league", CurveQuery(tags=(tag,), smoothing=2))
    assert curves["extent"] == {"start": 1, "end": 2}
    assert curves["trends"][tag][-1]["value"] == 0.75
    assert curves["events"][-1]["kind"] == "population"
    assert repository.detail("learning/league", set(), [])["metrics"]["last_step"] == 2


def test_selfplay_metrics_count_games_once_and_keep_mutual_win_rates_separate() -> None:
    row = _row(2)
    row["pairs"]["a_vs_a"] = {
        "games": 4,
        "wins": 3,
        "draws": 0,
        "losses": 1,
        "cash_left_sum": 120,
        "cash_right_sum": 40,
        "absolute_cash_difference_sum": 100,
    }
    row["physical_games"] = 8
    result = metrics(row)
    assert result["rl/league/pairs/a_vs_a/win_rate"] == 0.75  # Physical seat 0, not both views.
    assert result["rl/league/pairs/a_vs_a/mean_terminal_cash"] == 20
    assert result["rl/league/pairs/a_vs_a/mean_absolute_cash_difference"] == 25
    assert result["rl/league/members/a/games"] == 8
    assert result["rl/league/members/a/mean_terminal_cash"] == 15
    assert result["rl/league/members/a/win_rate"] == 0.25  # Only mutual games.
    assert result["rl/rollout/mean_terminal_cash"] == 17.5
    assert result["rl/league/selfplay_physical_games"] == 4
    assert result["rl/league/mutual_physical_games"] == 4
