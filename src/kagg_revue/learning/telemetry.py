"""Combine simultaneous worker measurements without double counting physical games."""

from typing import Any

from kagg_revue.learning.collection.quadrants import combine as combine_quadrants
from kagg_revue.learning.config import Experiment


def populations(workers: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine opponent panels by physical games, excluding frozen-seat cash."""
    combined: dict[str, Any] = {}
    for worker in workers:
        for name, row in worker.get("populations", {}).items():
            result = combined.setdefault(
                name,
                dict.fromkeys(
                    ("games", "training_trajectories", "wins", "ties", "losses", "cash", "gap"),
                    0,
                ),
            )
            for key in ("games", "training_trajectories", "wins", "ties", "losses"):
                result[key] += row[key]
            result["cash"] += row["mean_terminal_cash"] * row["training_trajectories"]
            result["gap"] += row["mean_cash_difference"] * row["games"]
    total = sum(row["games"] for row in combined.values())
    for row in combined.values():
        row["mean_terminal_cash"] = row.pop("cash") / row["training_trajectories"]
        row["mean_cash_difference"] = row.pop("gap") / row["games"]
        row["training_fraction"] = row["games"] / total
    return combined


def combine(config: Experiment, workers: list[dict[str, Any]]) -> dict[str, Any]:
    """Reduce synchronous worker timings by wall time and equal-size outcomes by mean."""
    first = workers[0]
    timing = {key: max(worker["rollout"][key] for worker in workers) for key in first["rollout"]}
    timing["physical_games_per_second"] = config.games / timing["rollout_seconds"]
    optimization = dict(first["optimization"])
    for key in ("learner_seconds", "credit_seconds", "protection_seconds"):
        optimization[key] = max(worker["optimization"][key] for worker in workers)
    restart = dict(first["restart"])
    restart["mean_cash_change"] = sum(w["restart"]["mean_cash_change"] for w in workers) / len(
        workers
    )
    restart["policy_transitions"] = sum(w["restart"]["policy_transitions"] for w in workers)
    return {
        "initialization": "checkpoint" if config.initial_weights is not None else "random",
        "restart": restart,
        "official_transitions": restart["policy_transitions"],
        "mean_cash": sum(w["mean_cash"] for w in workers) / len(workers),
        "history_score": (
            sum(w["history_score"] for w in workers) / len(workers)
            if all(w["history_score"] is not None for w in workers)
            else None
        ),
        "populations": populations(workers),
        "land": combine_quadrants([worker.get("land") or {} for worker in workers]),
        "rollout": timing,
        "optimization": optimization,
        "peak_allocated_bytes": max(w["peak_allocated_bytes"] for w in workers),
        "update_seconds": max(w["update_seconds"] for w in workers),
        "workers": workers,
    }
