"""Small live status snapshots, independent of the growing checkpoint ledger."""

import time
from typing import Any

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.scheduler import live_report


def publish(config: Experiment, state: dict[str, Any], phase: str, **details: Any) -> None:
    """Publish operational progress without presenting it as a recoverable checkpoint."""
    history = int(config.games * config.population.fraction)
    scripts = (
        int(config.games * config.script_population.fraction) if config.script_population else 0
    )
    populations = {"self_play": config.games - history - scripts}
    if history:
        populations["historical_self_play"] = history
    if config.script_population:
        populations.update(
            {
                name: scripts // len(config.script_population.agents)
                for name in config.script_population.agents
            }
        )
    pfsp = live_report(config, state)
    current_phase = bool(
        state["records"]
        and (
            not config.population.separate_scripts
            or state["records"][-1].get("pfsp", {}).get("separate_scripts")
        )
    )
    if pfsp and current_phase and "pfsp" in state["records"][-1]:
        populations = {
            name: panel["games"] for name, panel in state["records"][-1]["populations"].items()
        }
    if config.population.sampled_counts and not (current_phase and "pfsp" in state["records"][-1]):
        populations = {}
    actual_history = populations.get("historical_self_play", 0) / config.games
    actual_scripts = (
        sum(
            count
            for name, count in populations.items()
            if name not in {"self_play", "historical_self_play"}
        )
        / config.games
    )
    write_json(
        config.output_dir / "learning-progress.json",
        {
            "run_id": state["run_id"],
            "phase": phase,
            "pretraining_only": config.pretraining_only,
            "update": state["completed_update"],
            "target_updates": config.updates,
            "checkpoint_update": state["completed_update"],
            "checkpoint_interval": config.checkpoint_interval,
            "games_per_update": config.games,
            "pure_selfplay": config.population.fraction == 0 and config.script_population is None,
            "population_games": populations,
            "population_update": state["records"][-1]["update"] if state.get("records") else 0,
            **({"pfsp": pfsp} if pfsp else {}),
            "history_fraction": actual_history
            if config.population.sampled_counts
            else config.population.fraction,
            "script_fraction": actual_scripts
            if config.population.sampled_counts
            else scripts / config.games,
            "selfplay_fraction": populations.get("self_play", 0) / config.games,
            **(
                {
                    "target_selfplay_fraction": 1 - config.population.fraction,
                    "unified_pool_fraction": config.population.fraction,
                }
                if config.population.unified
                else {}
            ),
            **(
                {
                    "target_selfplay_fraction": 1
                    - config.population.fraction
                    - config.script_population.fraction,
                    "target_history_fraction": config.population.fraction,
                    "target_script_fraction": config.script_population.fraction,
                }
                if config.population.separate_scripts and config.script_population is not None
                else {}
            ),
            "batch_rows": config.batch_rows,
            "microbatch_rows": config.execution.microbatch_rows
            if config.execution
            else config.microbatch_rows,
            "updated_at": time.time(),
            **details,
        },
    )
