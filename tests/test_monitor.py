import json
from pathlib import Path

import pytest
from torch.utils.tensorboard import SummaryWriter

from kagg_revue.monitor.metrics import JsonlMetricReader, TensorboardMetricReader


@pytest.mark.parametrize(
    "kl_field",
    ["maximum_plan_kl", "maximum_field_kl", "maximum_prefix_kl", "maximum_new_scope_kl"],
)
def test_production_kl_reaches_dashboard_series_with_its_scope(
    tmp_path: Path, kl_field: str
) -> None:
    path = tmp_path / "metrics.jsonl"
    rank_values = ((0.07, 0.04), (0.0, 0.0))
    rows = [
        {
            "update": step,
            "physical_games_per_second": 1.0,
            "workers": [{"optimization": {kl_field: value}} for value in values],
        }
        for step, values in enumerate(rank_values, start=1)
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    snapshot = JsonlMetricReader(max_points=5).read(path)
    tag = f"rl/optimization/{kl_field}"
    assert [point.value for point in snapshot.series[tag]] == [
        max(values) for values in rank_values
    ]
    assert snapshot.latest[tag] == max(rank_values[-1])
    assert {key for key in snapshot.latest if key.endswith("_kl")} == {tag}


def test_production_metrics_preserve_new_scalars_flags_and_actual_temperature(
    tmp_path: Path,
) -> None:
    path = tmp_path / "metrics.jsonl"
    row = {
        "update": 1,
        "physical_games_per_second": 1.0,
        "temperature": 0.0,
        "actor_learning_rate": 0.0,
        "workers": [
            {
                "rollout": {"new_timing": {"seconds": 0.25}},
                "optimization": {
                    "actor_early_stop": False,
                    "critic_warmup": True,
                    "actor_steps": 0,
                    "critic_steps": 2,
                    "state_value_loss": 0.75,
                    "prefix_value_loss": 0.125,
                    "new_diagnostic": {"value": -0.5},
                    "invalid": float("nan"),
                    "label": "ignored",
                },
            },
            {"optimization": {"critic_steps": 2, "new_diagnostic": {"value": -0.25}}},
        ],
    }
    path.write_text(json.dumps(row) + "\n")
    reader = JsonlMetricReader(max_points=5)
    latest = reader.read(path).latest
    assert latest["rl/run/temperature"] == row["temperature"]
    assert latest["rl/optimization/actor_learning_rate"] == row["actor_learning_rate"]
    assert latest["rl/optimization/actor_early_stop"] == 0.0
    assert latest["rl/optimization/critic_warmup"] == 1.0
    assert latest["rl/optimization/actor_steps"] == 0.0
    assert latest["rl/optimization/critic_steps"] == 2.0
    assert latest["rl/optimization/state_value_loss"] == 0.75
    assert latest["rl/optimization/prefix_value_loss"] == 0.125
    assert latest["rl/optimization/new_diagnostic/value"] == -0.25
    assert latest["rl/rollout/new_timing/seconds"] == 0.25
    assert "rl/optimization/invalid" not in latest
    assert "rl/optimization/label" not in latest

    row.update(update=2, temperature=0.125, actor_learning_rate=4e-8)
    with path.open("a") as stream:
        stream.write(json.dumps(row) + "\n")
    snapshot = reader.read(path)
    assert [point.value for point in snapshot.series["rl/run/temperature"]] == [
        0.0,
        row["temperature"],
    ]
    assert snapshot.latest["rl/optimization/actor_learning_rate"] == row["actor_learning_rate"]


def test_jsonl_metric_reader_waits_for_complete_appended_record(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    first = {"update": 1, "rollout": {"wins": 2, "nested": {"rate": 0.5}}}
    second = {"update": 2, "rollout": {"wins": 3, "nested": {"rate": 0.75}}}
    encoded_second = json.dumps(second)
    split = len(encoded_second) // 2
    path.write_text(json.dumps(first) + "\n" + encoded_second[:split], encoding="utf-8")

    reader = JsonlMetricReader(max_points=50)
    partial = reader.read(path)

    assert partial.row_count == 1
    assert partial.last_step == 1
    assert partial.latest["rl/rollout/nested/rate"] == 0.5

    with path.open("a", encoding="utf-8") as stream:
        stream.write(encoded_second[split:] + "\n")
    complete = reader.read(path)

    assert complete.row_count == 2
    assert complete.last_step == 2
    assert [point.step for point in complete.series["rl/rollout/wins"]] == [1, 2]
    assert complete.latest["rl/rollout/nested/rate"] == 0.75


def test_production_metrics_keep_physical_games_and_full_update_timing(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    row = {
        "update": 1,
        "population": "self_play",
        "physical_games": 6,
        "training_trajectories": 12,
        "wins": 2,
        "ties": 1,
        "losses": 3,
        "mean_cash": 25,
        "p10_cash": 12,
        "update_seconds": 4,
        "physical_games_per_second": 1.5,
        "workers": [
            {"rollout": {"rollout_seconds": 2}, "peak_allocated_bytes": 128},
            {"rollout": {"rollout_seconds": 3}, "peak_allocated_bytes": 256},
        ],
    }
    path.write_text(json.dumps(row) + "\n")
    latest = JsonlMetricReader(max_points=5).read(path).latest
    assert latest["rl/rollout/games"] * 2 == latest["rl/rollout/training_trajectories"]
    assert latest["rl/rollout/games_per_second"] == row["physical_games"] / 3
    assert latest["rl/system/physical_games_per_second"] == row["physical_games"] / 4
    assert latest["rl/system/cuda_peak_allocated_bytes"] == 256


def test_jsonl_metric_reader_normalizes_capability_run_metrics(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    row = {
        "update": 3,
        "elapsed_seconds": 9.0,
        "outcomes": {
            "overall": {"games": 6, "wins": 2, "ties": 1, "losses": 3},
            "alpha": {
                "games": 2,
                "wins": 1,
                "ties": 0,
                "losses": 1,
                "win_rate": 0.5,
                "mean_terminal_cash": 100.0,
                "mean_cash_difference": 10.0,
            },
            "beta": {
                "games": 4,
                "wins": 1,
                "ties": 1,
                "losses": 2,
                "win_rate": 0.25,
                "mean_terminal_cash": 40.0,
                "mean_cash_difference": -5.0,
            },
        },
        "rollout": {"turns_per_second": 12.0},
        "optimization": {
            "loss": 0.7,
            "root_value_loss": 0.4,
            "candidate_value_loss": 0.3,
            "gradient_norm": 1.5,
        },
        "search": {
            "selected_direct_fraction": 0.75,
            "selected_mode_fraction": {"0": 0.75, "1": 0.05, "2": 0.0, "3": 0.2},
        },
        "batch": {"episodes": 6},
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    snapshot = JsonlMetricReader(max_points=50).read(path)

    assert snapshot.latest["rl/rollout/wins"] == 2.0
    assert snapshot.latest["rl/rollout/tie_rate"] == 1.0 / 6.0
    assert snapshot.latest["rl/rollout/mean_terminal_cash"] == 60.0
    assert snapshot.latest["rl/rollout/mean_cash_difference"] == 0.0
    assert snapshot.latest["rl/rollout/opponents/alpha/training_fraction"] == 1.0 / 3.0
    assert snapshot.latest["rl/rollout/opponents/beta/wins"] == 1.0
    assert snapshot.latest["rl/optimization/total_loss"] == 0.7
    assert snapshot.latest["rl/optimization/maximum_gradient_norm"] == 1.5
    assert snapshot.latest["rl/search/selected_capability_fraction"] == 0.25
    assert snapshot.latest["rl/search/selected_mode_fraction/3"] == 0.2
    assert snapshot.latest["rl/batch/episodes"] == 6.0
    assert snapshot.latest["rl/system/elapsed_seconds"] == 9.0


def test_jsonl_metric_reader_normalizes_flat_program_outcomes(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    row = {
        "update": 4,
        "outcomes": {
            "episodes": 8,
            "wins": 3,
            "ties": 2,
            "losses": 3,
            "mean_terminal_cash": 75.0,
            "mean_cash_difference": 5.0,
            "opponents": {
                "kaito": {
                    "episodes": 8,
                    "wins": 3,
                    "ties": 2,
                    "losses": 3,
                }
            },
        },
        "rollout": {
            "turns_per_second": 15.0,
            "physical_games_per_second": 4.0,
        },
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    snapshot = JsonlMetricReader(max_points=50).read(path)

    assert snapshot.latest["rl/rollout/wins"] == 3.0
    assert snapshot.latest["rl/rollout/tie_rate"] == 0.25
    assert snapshot.latest["rl/rollout/opponents/kaito/losses"] == 3.0
    assert snapshot.latest["rl/rollout/games_per_second"] == 4.0


def test_jsonl_metric_reader_preserves_unit_task_diagnostics(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    base = {
        "outcomes": {
            "overall": {
                "games": 2,
                "training_episodes": 4,
                "wins": 1,
                "ties": 0,
                "losses": 1,
            },
            "self_play": {
                "games": 2,
                "training_episodes": 4,
                "wins": 1,
                "ties": 0,
                "losses": 1,
            },
        },
        "rollout": {
            "seconds": 5.0,
            "training_episodes_per_second": 0.8,
            "task_decisions_per_second": 12.0,
        },
        "optimization": {
            "task_value_loss": 0.4,
            "market_value_loss": 0.3,
            "peak_gpu_allocated_bytes": 1024,
            "peak_gpu_reserved_bytes": 2048,
        },
        "optimization_seconds": 2.0,
    }
    rows = [
        {"update": 1, "elapsed_seconds": 8.0, **base},
        {"update": 2, "elapsed_seconds": 17.0, **base},
    ]
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    snapshot = JsonlMetricReader(max_points=50).read(path)

    assert snapshot.latest["rl/rollout/opponents/self_play/training_trajectories"] == 4
    assert snapshot.latest["rl/rollout/opponents/self_play/win_rate"] == 0.5
    assert snapshot.latest["rl/rollout/elapsed_seconds"] == 5.0
    assert snapshot.latest["rl/system/optimization_seconds"] == 2.0
    assert snapshot.latest["rl/system/update_elapsed_seconds"] == 9.0
    assert snapshot.latest["rl/system/cuda_peak_allocated_bytes"] == 1024
    assert snapshot.latest["rl/system/cuda_peak_reserved_bytes"] == 2048
    assert snapshot.latest["rl/optimization/task_value_loss"] == 0.4


def test_jsonl_metric_reader_bounds_rotating_history_opponents(
    tmp_path: Path,
) -> None:
    path = tmp_path / "metrics.jsonl"
    rows = []
    for update in range(1, 81):
        snapshot_update = update - 1
        identity = f"history:u{snapshot_update:08d}:{snapshot_update:064x}"
        rows.append(
            {
                "update": update,
                "outcomes": {
                    "overall": {"games": 4, "wins": 2, "ties": 0, "losses": 2},
                    "self_play": {
                        "games": 2,
                        "wins": 1,
                        "ties": 0,
                        "losses": 1,
                        "win_rate": 0.5,
                    },
                    identity: {
                        "games": 2,
                        "wins": 1,
                        "ties": 0,
                        "losses": 1,
                        "win_rate": 0.5,
                    },
                },
            }
        )
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    snapshot = JsonlMetricReader(max_points=50).read(path)
    opponent_tags = {tag for tag in snapshot.series if tag.startswith("rl/rollout/opponents/")}

    opponent_names = {
        tag.removeprefix("rl/rollout/opponents/").split("/", maxsplit=1)[0] for tag in opponent_tags
    }
    assert opponent_names == {"history", "self_play"}
    assert all("history:u" not in tag for tag in opponent_tags)
    assert snapshot.latest["rl/rollout/opponents/history/opponent_update"] == 79.0
    assert len(snapshot.series["rl/rollout/opponents/history/win_rate"]) == 50


def test_jsonl_metric_reader_normalizes_intent_ledger_metrics(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    row = {
        "update": 2,
        "wins": 3,
        "ties": 1,
        "losses": 2,
        "mean_terminal_cash": 120.0,
        "mean_cash_difference": 8.0,
        "rollout": {
            "physical_games": 16,
            "episodes": 32,
            "official_turns": 1000,
            "elapsed_seconds": 10.0,
            "physical_games_per_second": 1.6,
            "pseudo_steps_per_second": 40000.0,
            "policy_seconds": 8.0,
        },
        "optimization": {
            "loss": 0.5,
            "value_loss": 0.4,
            "policy_loss": 0.01,
            "approximate_kl": 0.002,
            "clip_fraction": 0.05,
            "entropy": 3.2,
            "gradient_norm": 1.1,
            "optimizer_steps": 16,
        },
        "timing": {
            "update_seconds": 18.0,
            "optimization_seconds": 6.0,
            "physical_games_per_second": 1.5,
        },
        "cuda_memory": {
            "cuda:0": {
                "peak_allocated_bytes": 1000,
                "peak_reserved_bytes": 2000,
            },
            "cuda:1": {
                "peak_allocated_bytes": 1500,
                "peak_reserved_bytes": 2500,
            },
        },
        "behavior_replay": {
            "maximum_absolute_log_probability_error": 0.01,
            "maximum_absolute_value_error": 0.02,
        },
    }
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    snapshot = JsonlMetricReader(max_points=50).read(path)

    assert snapshot.latest["rl/rollout/wins"] == 3.0
    assert snapshot.latest["rl/rollout/win_rate"] == 0.5
    assert snapshot.latest["rl/rollout/games"] == 6.0
    assert snapshot.latest["rl/rollout/games_per_second"] == 1.6
    assert snapshot.latest["rl/rollout/turns_per_second"] == 100.0
    assert snapshot.latest["rl/system/update_elapsed_seconds"] == 18.0
    assert snapshot.latest["rl/system/optimization_seconds"] == 6.0
    assert snapshot.latest["rl/system/cuda_peak_allocated_bytes"] == 1500.0
    assert snapshot.latest["rl/system/cuda_peak_reserved_bytes"] == 2500.0
    assert snapshot.latest["rl/behavior_replay/log_probability_error"] == 0.01
    assert snapshot.latest["rl/optimization/total_loss"] == 0.5
    assert snapshot.latest["rl/optimization/maximum_gradient_norm"] == 1.1


def test_tensorboard_metric_reader_exposes_scalar_steps(tmp_path: Path) -> None:
    with SummaryWriter(log_dir=tmp_path) as writer:
        writer.add_scalar("phase/accuracy", 0.25, 4)
        writer.add_scalar("phase/accuracy", 0.5, 5)

    snapshot = TensorboardMetricReader(max_points=50).read(tmp_path)

    assert snapshot.last_step == 5
    assert [point.step for point in snapshot.series["phase/accuracy"]] == [4, 5]
    assert snapshot.latest["phase/accuracy"] == 0.5
