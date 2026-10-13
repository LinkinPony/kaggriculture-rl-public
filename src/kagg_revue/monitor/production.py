"""Normalize spatial-contract records without confusing seats with physical games."""

import math
from collections.abc import Mapping

from kagg_revue.core.observability import numeric_metrics


def metrics(row: Mapping[str, object]) -> dict[str, float]:
    """Map the production tape's coarse rank timings to existing dashboard tags."""
    workers = row.get("workers")
    if not isinstance(workers, list) or "physical_games_per_second" not in row:
        return {}
    output: dict[str, float] = {}

    def add(tag: str, value: object) -> None:
        if isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value):
            output[tag] = float(value)

    for name, tag in {
        "mean_cash": "rl/rollout/mean_terminal_cash",
        "p10_cash": "rl/rollout/p10_terminal_cash",
        "physical_games": "rl/rollout/physical_games",
        "training_trajectories": "rl/rollout/training_trajectories",
        "selfplay_games": "rl/rollout/selfplay_games",
        "script_games": "rl/rollout/script_games",
        "official_transitions": "rl/rollout/official_turns",
        "physical_games_per_second": "rl/system/physical_games_per_second",
        "update_seconds": "rl/system/update_elapsed_seconds",
        "checkpoint_seconds": "rl/system/checkpoint_seconds",
        "prior_scale": "rl/run/prior_scale",
        "temperature": "rl/run/temperature",
        "actor_learning_rate": "rl/optimization/actor_learning_rate",
    }.items():
        add(tag, row.get(name))
    if row.get("population") == "self_play":
        output["rl/run/self_play"] = 1.0
    elif row.get("population") == "script_mix":
        output["rl/run/script_mix"] = 1.0
    ranks = [worker for worker in workers if isinstance(worker, dict)]
    # Preserve new scalar diagnostics automatically, including explicit false/zero
    # states. The existing reduction is the largest reported rank contribution;
    # synchronized optimizer counters are not summed across replicas.
    for group in ("rollout", "optimization"):
        aggregated: dict[str, float] = {}
        for worker in ranks:
            values = worker.get(group)
            if not isinstance(values, Mapping):
                continue
            for name, value in numeric_metrics(values).items():
                if math.isfinite(value):
                    aggregated[name] = max(aggregated.get(name, value), value)
        for name, value in aggregated.items():
            output[f"rl/{group}/{name}"] = value
    for name in ("peak_allocated_bytes", "peak_reserved_bytes"):
        values = [worker[name] for worker in ranks if isinstance(worker.get(name), int | float)]
        if values:
            add(f"rl/system/cuda_{name}", max(values))
    aliases = {
        "rl/rollout/rollout_seconds": "rl/rollout/elapsed_seconds",
        "rl/optimization/learner_seconds": "rl/system/optimization_seconds",
    }
    for source, destination in aliases.items():
        if source in output:
            output[destination] = output[source]
    if row.get("training_phase") in {"expert_iteration", "state_branch"}:
        output[f"rl/run/{row['training_phase']}"] = 1.0
        add("rl/optimization/optimizer_steps", row.get("optimizer_steps"))
        add("rl/rollout/physical_games", row.get("training_games"))
        add("rl/system/search_seconds", row.get("search_seconds"))
        learning = row.get("learning")
        if isinstance(learning, dict):
            output["rl/optimization/learning_performed"] = float(bool(learning.get("performed")))
            add("rl/optimization/expert_fits", learning.get("fits"))
        evaluation = row.get("evaluation")
        if isinstance(evaluation, dict):
            for population, assessment in evaluation.items():
                for role in (
                    "student",
                    "initial",
                    "expert",
                    "origin",
                    "paired_to_initial",
                    "paired_to_expert",
                    "paired_to_origin",
                ):
                    for name, value in assessment.get(role, {}).items():
                        add(f"rl/evaluation/{population}/{role}/{name}", value)
        if row.get("training_phase") == "state_branch":
            search = row.get("search")
            if isinstance(search, dict):
                for name, value in search.items():
                    add(f"rl/search/{name}", value)
    elapsed = output.get("rl/rollout/elapsed_seconds", 0.0)
    games = output.get("rl/rollout/physical_games", 0.0)
    if elapsed > 0.0:
        output["rl/rollout/games_per_second"] = games / elapsed
    output["rl/rollout/games"] = games
    return output
