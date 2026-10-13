"""Independent script draws and history-only PFSP with exact cumulative game budgets."""

from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np

from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.statistics import Record, probabilities
from kagg_revue.learning.matchmaking.unified import table

if TYPE_CHECKING:
    from kagg_revue.learning.matchmaking.scheduler import Match


def game_counts(config: Experiment, update: int, world: int, started: int) -> tuple[int, int]:
    """Round cumulative script seat pairs without changing the fixed historical quota."""
    scripts = config.script_population
    assert scripts is not None
    elapsed = update - started + 1
    if elapsed <= 0:
        raise ValueError("separate script sampling precedes its activation boundary")
    pairs = Fraction(str(scripts.fraction)) * config.games / (2 * world)
    count = 2 * world * (round(elapsed * pairs) - round((elapsed - 1) * pairs))
    return int(config.games * config.population.fraction), count


def script_table(
    config: Experiment, records: dict[str, Record], update: int
) -> dict[str, dict[str, float | int]]:
    """Normalize recent loss priorities exclusively within the script pool."""
    scripts, options = config.script_population, config.population.pfsp
    assert scripts is not None and options is not None
    evidence = [records.get(f"script:{scripts.sha256}:{name}", Record()) for name in scripts.agents]
    weights = probabilities(evidence, update, options, latest=False)
    return {
        name: {
            "score": record.probability(update, options),
            "probability": float(weight),
            "overall_probability": scripts.fraction * float(weight),
            "games": 0,
        }
        for name, record, weight in zip(scripts.agents, evidence, weights, strict=True)
    }


def select(
    config: Experiment,
    ledger: dict[str, Any],
    records: dict[str, Record],
    update: int,
    world: int,
    started: int,
) -> "Match":
    """Draw one historical model and one script using independent addressed random streams."""
    from kagg_revue.learning.matchmaking.scheduler import Match

    entries = table(config, ledger, records, update, include_scripts=False)
    weights = np.asarray([entry["probability"] for entry in entries])
    history_rng = np.random.default_rng([config.seed, update, 0x50465350])
    selected = entries[int(history_rng.choice(len(entries), p=weights))]
    scripts = config.script_population
    assert scripts is not None
    script_rng = np.random.default_rng([config.seed, update, 0x53435250])
    script_report = script_table(config, records, update)
    script_weights = np.asarray([row["probability"] for row in script_report.values()])
    script = scripts.agents[int(script_rng.choice(len(scripts.agents), p=script_weights))]
    history, count = game_counts(config, update, world, started)
    script_report[script]["games"] = count
    return Match(
        selected["name"],
        ((script, count // world),),
        {
            "enabled": True,
            "separate_scripts": True,
            "pool_size": len(entries),
            "history_entropy": float(-(weights * np.log(weights)).sum()),
            "history_fraction": config.population.fraction,
            "script_fraction": scripts.fraction,
            "selfplay_fraction": 1 - config.population.fraction - scripts.fraction,
            "population_games": {
                "self_play": config.games - history - count,
                "historical_self_play": history,
                script: count,
            },
            "selected": selected,
            "scripts": script_report,
        },
    )


def observe(
    config: Experiment,
    ledger: dict[str, Any],
    records: dict[str, Record],
    match: "Match",
    update: int,
    panels: dict[str, Any],
) -> dict[str, Record]:
    """Credit each disjoint quota without mixing script and history sampling evidence."""
    options, scripts = config.population.pfsp, config.script_population
    assert options is not None and scripts is not None
    if {name: panel["games"] for name, panel in panels.items()} != match.report["population_games"]:
        raise ValueError("separate population results differ from their sampled game budgets")
    key = f"history:{ledger['members'][match.history]}"
    records.setdefault(key, Record()).observe(panels["historical_self_play"], update, options)
    for name, _ in match.scripts:
        records.setdefault(f"script:{scripts.sha256}:{name}", Record()).observe(
            panels[name], update, options
        )
    active = {f"history:{ledger['members'][name]}" for name in ledger["pool"]}
    active.update(f"script:{scripts.sha256}:{name}" for name in scripts.agents)
    return {key: record for key, record in records.items() if key in active}
