"""One PFSP distribution over scripts and frozen policies, with exact cumulative budgets."""

from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np

from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.pool import member_update
from kagg_revue.learning.matchmaking.statistics import Record, probabilities

if TYPE_CHECKING:
    from kagg_revue.learning.matchmaking.scheduler import Match


def pooled_games(config: Experiment, update: int, world: int, started: int) -> int:
    """Round cumulative seat pairs, keeping long-run fractions exact without extra RNG."""
    elapsed = update - started + 1
    if elapsed <= 0:
        raise ValueError("unified sampling precedes its activation boundary")
    pairs = Fraction(str(config.population.fraction)) * config.games / (2 * world)
    return 2 * world * (round(elapsed * pairs) - round((elapsed - 1) * pairs))


def table(
    config: Experiment,
    ledger: dict[str, Any],
    records: dict[str, Record],
    update: int,
    *,
    include_scripts: bool = True,
) -> list[dict[str, Any]]:
    """Normalize every eligible identity together, with latest coverage on own history."""
    options = config.population.pfsp
    assert options is not None
    entries: list[dict[str, Any]] = []
    scripts = config.script_population
    if scripts is not None and include_scripts:
        entries.extend(
            {"kind": "script", "name": name, "key": f"script:{scripts.sha256}:{name}"}
            for name in scripts.agents
        )
    entries.extend(
        {
            "kind": "history",
            "name": name,
            "path": name,
            "sha256": ledger["members"][name],
            "key": f"history:{ledger['members'][name]}",
            "update": member_update(name),
            "source_run": ledger.get("external_opponents", {}).get(name, {}).get("run"),
        }
        for name in ledger["pool"]
    )
    evidence = [records.get(entry["key"], Record()) for entry in entries]
    weights = probabilities(evidence, update, options, latest=True)
    return [
        {
            **entry,
            "score": record.probability(update, options),
            "probability": float(weight),
            "games": record.wins + record.ties + record.losses,
            **(
                {"mastered": record.mastered(options) and entry is not entries[-1]}
                if options.mastery is not None
                else {}
            ),
        }
        for entry, record, weight in zip(entries, evidence, weights, strict=True)
    ]


def select(
    config: Experiment,
    ledger: dict[str, Any],
    records: dict[str, Record],
    update: int,
    world: int,
    started: int,
) -> "Match":
    """Draw one dense opponent batch from the common pool identically on all ranks."""
    from kagg_revue.learning.matchmaking.scheduler import Match

    entries = table(config, ledger, records, update)
    weights = np.asarray([entry["probability"] for entry in entries])
    rng = np.random.default_rng([config.seed, update, 0x50465350])
    selected = entries[int(rng.choice(len(entries), p=weights))]
    frozen = pooled_games(config, update, world, started)
    script = selected["kind"] == "script"
    label = selected["name"] if script else "historical_self_play"
    return Match(
        "" if script else selected["name"],
        ((selected["name"], frozen // world),) if script else (),
        {
            "enabled": True,
            "unified": True,
            "pool_size": len(entries),
            "history_entropy": float(-(weights * np.log(weights)).sum()),
            "pool_fraction": config.population.fraction,
            "selfplay_fraction": 1 - config.population.fraction,
            "population_games": {"self_play": config.games - frozen, label: frozen},
            "selected": selected,
            "scripts": {
                entry["name"]: {
                    "score": entry["score"],
                    "probability": entry["probability"],
                    "games": frozen if entry["key"] == selected["key"] else 0,
                }
                for entry in entries
                if entry["kind"] == "script"
            },
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
    """Credit only actual learned-seat games and retain evidence for unsampled scripts."""
    options = config.population.pfsp
    assert options is not None
    expected = match.report["population_games"]
    if {name: panel["games"] for name, panel in panels.items()} != expected:
        raise ValueError("unified PFSP results differ from the sampled game allocation")
    selected = match.report["selected"]
    name = selected["name"] if selected["kind"] == "script" else "historical_self_play"
    records.setdefault(selected["key"], Record()).observe(panels[name], update, options)
    active = {entry["key"] for entry in table(config, ledger, records, update)}
    return {key: record for key, record in records.items() if key in active}
