"""Read random-root learning telemetry without importing a training workflow."""

import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from kagg_revue.monitor import league
from kagg_revue.monitor.snapshots import read_snapshot


def has_evaluation(run_dir: Path) -> bool:
    """Recognize either fixed-seed role without reading match payloads."""
    directory = run_dir / "evaluation"
    return any(
        any(directory.glob(pattern))
        for pattern in ("selection-*.json", "confirmation-*.json", "update-*.json")
    )


def progress(run_dir: Path) -> dict[str, Any]:
    """Read live snapshots including the opponent pool, never the full model ledger."""
    if live := league.progress(run_dir):
        return live
    return read_snapshot(run_dir / "learning-progress.json")


def metrics(row: Mapping[str, object]) -> dict[str, float]:
    """Normalize actual cash, history score and timing without inventing WDL counts."""
    if "history_score" not in row or "physical_games" not in row:
        return {}
    output = {"rl/run/random_root": float(row.get("initialization", "random") == "random")}
    pfsp = row.get("pfsp")
    if isinstance(pfsp, Mapping):
        output["rl/pfsp/enabled"] = 1.0
        output["rl/pfsp/separate_scripts"] = float(bool(pfsp.get("separate_scripts")))
        for name in ("pool_size", "history_entropy"):
            value = pfsp.get(name)
            if isinstance(value, int | float) and math.isfinite(value):
                output[f"rl/pfsp/{name}"] = float(value)
        selected = pfsp.get("selected")
        if isinstance(selected, Mapping):
            for name in ("update", "score", "probability"):
                value = selected.get(name)
                if isinstance(value, int | float) and math.isfinite(value):
                    output[f"rl/pfsp/selected/{name}"] = float(value)
            if "rl/pfsp/selected/update" in output and selected.get("kind") != "script":
                output["rl/rollout/opponents/history/opponent_update"] = output[
                    "rl/pfsp/selected/update"
                ]
        scripts = pfsp.get("scripts")
        if isinstance(scripts, Mapping):
            for name, panel in scripts.items():
                if isinstance(panel, Mapping):
                    for field in ("score", "probability"):
                        value = panel.get(field)
                        if isinstance(value, int | float) and math.isfinite(value):
                            output[f"rl/pfsp/scripts/{name}/{field}"] = float(value)
    populations = row.get("populations")
    if isinstance(populations, Mapping):
        output["rl/run/script_mix"] = 1.0
        for name, panel in populations.items():
            if not isinstance(panel, Mapping):
                continue
            label = "history" if name == "historical_self_play" else name
            prefix = f"rl/rollout/opponents/{label}"
            for field in (
                "games",
                "training_fraction",
                "training_trajectories",
                "wins",
                "ties",
                "losses",
                "mean_terminal_cash",
                "mean_cash_difference",
            ):
                value = panel.get(field)
                if (
                    isinstance(value, int | float)
                    and not isinstance(value, bool)
                    and math.isfinite(value)
                ):
                    output[f"{prefix}/{field}"] = float(value)
            games = output.get(f"{prefix}/games", 0)
            wins = output.get(f"{prefix}/wins")
            if games > 0 and wins is not None:
                output[f"{prefix}/win_rate"] = wins / games
    for name, tag in {
        "mean_cash": "rl/rollout/mean_terminal_cash",
        "history_score": "rl/run/history_score",
        "physical_games": "rl/rollout/physical_games",
        "cumulative_physical_games": "rl/rollout/cumulative_physical_games",
        "official_transitions": "rl/rollout/official_turns",
        "update_seconds": "rl/system/update_elapsed_seconds",
        "peak_allocated_bytes": "rl/system/cuda_peak_allocated_bytes",
    }.items():
        value = row.get(name)
        if isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value):
            output[tag] = float(value)
    for group, name, tag in (
        ("rollout", "rollout_seconds", "rl/rollout/elapsed_seconds"),
        ("optimization", "learner_seconds", "rl/system/optimization_seconds"),
        ("optimization", "temperature", "rl/run/temperature"),
    ):
        nested = row.get(group)
        value = nested.get(name) if isinstance(nested, Mapping) else None
        if isinstance(value, int | float) and math.isfinite(value):
            output[tag] = float(value)
    duration = output.get("rl/system/update_elapsed_seconds", 0)
    if duration > 0:
        output["rl/system/physical_games_per_second"] = (
            output.get("rl/rollout/physical_games", 0) / duration
        )
    return output
