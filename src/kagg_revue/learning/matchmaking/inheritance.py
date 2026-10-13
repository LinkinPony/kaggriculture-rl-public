"""Discounted PFSP evidence carried from predecessor learners at one boundary."""

import json
from collections import Counter
from collections.abc import Sequence
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.archives import HistoricalArchive
from kagg_revue.learning.matchmaking.config import Pfsp
from kagg_revue.learning.matchmaking.statistics import Inherited, Record


def opponent_keys(config: Experiment, state: dict[str, Any]) -> list[str]:
    """Name every current script and pool member exactly as the sampler keys them."""
    scripts = config.script_population
    names = [f"script:{scripts.sha256}:{name}" for name in scripts.agents] if scripts else []
    return [*names, *(f"history:{state['members'][name]}" for name in state["pool"])]


def _ledgers(
    config: Experiment, donors: Sequence[HistoricalArchive]
) -> list[tuple[HistoricalArchive, dict[str, Any], Pfsp]]:
    """Authenticate donor ledgers whose sampler statistics are committed."""
    result = []
    for donor in donors:
        path = donor.run / "state.json"
        if donor.run == config.output_dir or digest(path) != donor.state_sha256:
            raise ValueError(f"PFSP donor ledger differs from its pinned identity: {donor.run}")
        ledger = json.loads(path.read_text())
        options = Experiment.model_validate(
            ledger["protocol"], context={"archived_population": True}
        ).population.pfsp
        if options is None or ledger["pfsp"]["last_update"] != ledger["completed_update"]:
            raise ValueError(f"PFSP donor lacks committed sampler statistics: {donor.run}")
        result.append((donor, ledger, options))
    return result


def inherit(
    config: Experiment, state: dict[str, Any], donors: Sequence[HistoricalArchive]
) -> dict[str, Any]:
    """Seed unmet opponents from the nearest donor and register a replayable event.

    Donors are ordered from the nearest predecessor. The k-th donor's evidence,
    decayed to its own last update, is scaled by ``discount ** k``. Evidence a
    donor itself only inherited keeps its original observation, so chained
    discounts compound while mastery follows the last real encounter.
    """
    options = config.population.pfsp
    if options is None or options.inheritance is None or not donors:
        raise ValueError("PFSP inheritance requires a configured discount and donors")
    update = state["completed_update"]
    sampler = state["pfsp"]
    if sampler["last_update"] != update:
        raise ValueError("PFSP inheritance requires committed sampler statistics")
    ledgers = _ledgers(config, donors)
    discount = options.inheritance.discount
    added: dict[str, Any] = {}
    sources: Counter[str] = Counter()
    for key in opponent_keys(config, state):
        if key in sampler["records"]:
            continue
        for generation, (donor, ledger, donor_options) in enumerate(ledgers, start=1):
            source = ledger["pfsp"]["records"].get(key)
            if source is None:
                continue
            record = Record.model_validate(source)
            games, score = record.evidence(ledger["pfsp"]["last_update"], donor_options)
            met = record.wins + record.ties + record.losses
            observed = (
                record.inherited
                if record.inherited is not None and not met
                else Inherited(
                    run=str(donor.run),
                    update=record.last_update,
                    games=record.effective_games,
                    score=record.effective_score,
                )
            )
            factor = discount**generation
            seeded = Record(
                effective_games=games * factor,
                effective_score=score * factor,
                last_update=update,
                inherited=observed,
            )
            added[key] = seeded.model_dump(mode="json", exclude_none=True)
            sources[str(donor.run)] += 1
            break
    sampler["records"] = {**sampler["records"], **added}
    event = {
        "completed_update": update,
        "discount": discount,
        "donors": [donor.model_dump(mode="json") for donor in donors],
        "records": added,
    }
    state["pfsp_inheritance_history"] = [*state.get("pfsp_inheritance_history", []), event]
    return {
        "completed_update": update,
        "discount": discount,
        "opponents": len(opponent_keys(config, state)),
        "own_evidence": len(sampler["records"]) - len(added),
        "inherited": len(added),
        "inherited_mastered": sum(
            Record.model_validate(value).mastered(options) for value in added.values()
        ),
        "by_donor": dict(sources),
    }
