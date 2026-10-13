"""One dense historical actor and balanced native script groups per global update."""

from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking import separate, unified
from kagg_revue.learning.matchmaking.pool import initialize, member_update
from kagg_revue.learning.matchmaking.statistics import Record, probabilities


class SamplerState(BaseModel):
    """Checkpointed sufficient statistics; choices use independent update-addressed RNG."""

    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = 1
    started_update: int = Field(ge=1)
    last_update: int = Field(ge=0)
    records: dict[str, Record] = Field(default_factory=dict)


@dataclass(frozen=True)
class Match:
    """A rank-invariant draw with per-rank script counts and auditable probabilities."""

    history: str
    scripts: tuple[tuple[str, int], ...]
    report: dict[str, Any]


class Matchmaker:
    """Adapt only between complete games, using globally reduced learned-seat results."""

    def __init__(self, config: Experiment, state: dict[str, Any]) -> None:
        """Validate restored sampling state against the committed learner update."""
        assert config.population.pfsp is not None
        self.config, self.ledger, self.options = config, state, config.population.pfsp
        initialize(config, state)
        self.state = SamplerState.model_validate(state["pfsp"])
        if self.state.last_update != state["completed_update"]:
            raise ValueError("PFSP statistics differ from the committed learner update")
        for record in self.state.records.values():
            record.evidence(self.state.last_update, self.options)

    def _key(self, name: str, *, script: bool = False) -> str:
        if script:
            assert self.config.script_population is not None
            return f"script:{self.config.script_population.sha256}:{name}"
        return f"history:{self.ledger['members'][name]}"

    def _records(self, names: list[str], *, script: bool = False) -> list[Record]:
        return [
            self.state.records.setdefault(self._key(name, script=script), Record())
            for name in names
        ]

    def select(self, update: int, world: int) -> Match:
        """Sample once per update identically on every rank without touching Torch RNG."""
        if update != self.state.last_update + 1:
            raise ValueError("PFSP updates must be consecutive")
        if self.config.population.unified:
            return unified.select(
                self.config,
                self.ledger,
                self.state.records,
                update,
                world,
                self.state.started_update,
            )
        if self.config.population.separate_scripts:
            return separate.select(
                self.config,
                self.ledger,
                self.state.records,
                update,
                world,
                self.state.started_update,
            )
        names = list(self.ledger["pool"])
        records = self._records(names)
        weights = probabilities(records, update, self.options, latest=True)
        rng = np.random.default_rng([self.config.seed, update, 0x50465350])
        index = int(rng.choice(len(names), p=weights))
        scripts = self.config.script_population
        counts: tuple[tuple[str, int], ...] = ()
        script_report: dict[str, Any] = {}
        if scripts is not None:
            agents: list[str] = list(scripts.agents)
            script_records = self._records(agents, script=True)
            weights_script = probabilities(script_records, update, self.options, latest=False)
            pairs = int(self.config.games * scripts.fraction) // (2 * world)
            minimum = self.options.script_min_pairs_per_rank
            remaining = pairs - minimum * len(agents)
            if remaining < 0:
                raise ValueError("script budget cannot cover the PFSP minimum seat pairs")
            allocation = rng.multinomial(remaining, weights_script) + minimum
            counts = tuple(
                (name, 2 * int(count)) for name, count in zip(agents, allocation, strict=True)
            )
            script_report = {
                name: {
                    "score": record.probability(update, self.options),
                    "probability": float((minimum + remaining * probability) / pairs),
                    "games": count * world,
                }
                for (name, count), record, probability in zip(
                    counts, script_records, weights_script, strict=True
                )
            }
        return Match(
            names[index],
            counts,
            {
                "enabled": True,
                "pool_size": len(names),
                "history_entropy": float(-(weights * np.log(weights)).sum()),
                "selected": {
                    "path": names[index],
                    "sha256": self.ledger["members"][names[index]],
                    "update": member_update(names[index]),
                    **(
                        {"source_run": self.ledger["external_opponents"][names[index]]["run"]}
                        if names[index] in self.ledger.get("external_opponents", {})
                        else {}
                    ),
                    "score": records[index].probability(update, self.options),
                    "probability": float(weights[index]),
                },
                "scripts": script_report,
            },
        )

    def observe(self, match: Match, update: int, panels: dict[str, Any]) -> None:
        """Persist only active identities after exactly one global outcome reduction."""
        if update != self.state.last_update + 1:
            raise ValueError("PFSP outcomes were duplicated or skipped")
        if self.config.population.sampled_counts:
            observer = unified.observe if self.config.population.unified else separate.observe
            self.state.records = observer(
                self.config, self.ledger, self.state.records, match, update, panels
            )
            self.state.last_update = update
            self.ledger["pfsp"] = self.state.model_dump(mode="json", exclude_none=True)
            return
        history = panels["historical_self_play"]
        if history["games"] != int(self.config.games * self.config.population.fraction):
            raise ValueError("PFSP historical results have the wrong global game count")
        self.state.records[self._key(match.history)].observe(history, update, self.options)
        for name, expected in match.report["scripts"].items():
            if panels[name]["games"] != expected["games"]:
                raise ValueError("PFSP script results differ from the sampled allocation")
            self.state.records[self._key(name, script=True)].observe(
                panels[name], update, self.options
            )
        active = {self._key(name) for name in self.ledger["pool"]}
        active.update(self._key(name, script=True) for name, _ in match.scripts)
        self.state.records = {key: row for key, row in self.state.records.items() if key in active}
        self.state.last_update = update
        self.ledger["pfsp"] = self.state.model_dump(mode="json", exclude_none=True)


def live_report(config: Experiment, state: dict[str, Any]) -> dict[str, Any]:
    """Expose a bounded history table without requiring the WebUI to read the ledger."""
    options = config.population.pfsp
    if options is None or "pfsp" not in state:
        return {}
    sampler = SamplerState.model_validate(state["pfsp"])
    if config.population.separate_scripts:
        previous = state["records"][-1].get("pfsp", {}) if state["records"] else {}
        return {
            "enabled": True,
            "separate_scripts": True,
            "update": sampler.last_update,
            "started_update": sampler.started_update,
            "pool_size": len(state["pool"]),
            "snapshot_interval": config.population.snapshot_interval,
            "uniform_fraction": options.uniform_fraction,
            "selected": previous.get("selected") if previous.get("separate_scripts") else None,
            "history": unified.table(
                config, state, sampler.records, sampler.last_update + 1, include_scripts=False
            ),
            "scripts": separate.script_table(config, sampler.records, sampler.last_update + 1),
        }
    if config.population.unified:
        entries = unified.table(config, state, sampler.records, sampler.last_update + 1)
        return {
            "enabled": True,
            "unified": True,
            "update": sampler.last_update,
            "started_update": sampler.started_update,
            "pool_size": len(entries),
            "snapshot_interval": config.population.snapshot_interval,
            "uniform_fraction": options.uniform_fraction,
            "pool_fraction": config.population.fraction,
            "selected": state["records"][-1].get("pfsp", {}).get("selected")
            if state["records"]
            else None,
            "history": entries,
        }
    names = list(state["pool"])
    records = [sampler.records.get(f"history:{state['members'][name]}", Record()) for name in names]
    weights = probabilities(records, sampler.last_update + 1, options, latest=True)
    return {
        "enabled": True,
        "update": sampler.last_update,
        "started_update": sampler.started_update,
        "pool_size": len(names),
        "snapshot_interval": config.population.snapshot_interval,
        "uniform_fraction": options.uniform_fraction,
        "selected": state["records"][-1].get("pfsp", {}).get("selected")
        if state["records"]
        else None,
        "history": [
            {
                "update": member_update(name),
                "source_run": state.get("external_opponents", {}).get(name, {}).get("run"),
                "score": record.probability(sampler.last_update + 1, options),
                "probability": float(weight),
                "games": record.wins + record.ties + record.losses,
            }
            for name, record, weight in zip(names, records, weights, strict=True)
        ],
    }
