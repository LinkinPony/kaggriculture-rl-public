"""Resolve a sampled opponent into native collection settings and bounded inference graphs."""

import math
from typing import Any

import numpy as np
import torch

from kagg_revue.learning.collection.archive import PopulationCache
from kagg_revue.learning.collection.population import script_games
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.scheduler import Match
from kagg_revue.learning.optimization.settings import HistoricalPopulation
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Policy


class MatchedCollection:
    """Reuse a learner graph per rounded batch size and frozen graphs per layout and size."""

    def __init__(
        self, config: Experiment, settings: RuntimeSettings, state: dict[str, Any], actor: Policy
    ) -> None:
        """Bind all frozen identities to the authoritative training ledger."""
        self.config, self.settings, self.state, self.actor = config, settings, state, actor
        self.cache = PopulationCache(config, state) if config.population.fraction else None
        self.runtimes: dict[int, ActorRuntime] = {}

    def runtime(self, count: int) -> ActorRuntime:
        """Capture each learner row count once, preserving the policy sampling RNG."""
        if count not in self.runtimes:
            self.runtimes[count] = ActorRuntime(
                self.actor,
                count,
                sample=True,
                precision=self.settings.precision,
                bf16_reduced_precision_reduction=False,
                compile_inference=bool(
                    self.config.execution and self.config.execution.compile_inference
                ),
            )
        return self.runtimes[count]

    def prepare(self, world: int) -> None:
        """Capture both rounded script quotas during startup, including archive recovery."""
        config = self.config
        if not config.population.separate_scripts:
            return
        assert config.script_population is not None
        pairs = config.games * config.script_population.fraction / (2 * world)
        base = 2 * (config.games // world) - int(config.games * config.population.fraction) // world
        device = next(self.actor.parameters()).device
        with torch.random.fork_rng(devices=[device] if device.type == "cuda" else []):
            for count in sorted({base - 2 * math.floor(pairs), base - 2 * math.ceil(pairs)}):
                self.runtime(count)

    def selection(
        self, match: Match | None, update: int, world: int
    ) -> tuple[RuntimeSettings, str | None, int]:
        """Resolve physical-game quotas and the immutable frozen identity for an update."""
        config, settings = self.config, self.settings
        games = config.games // world
        history = int(games * config.population.fraction)
        scripts = script_games(settings, games)
        name = None
        public = settings.script_population
        allocation = match.scripts if match else ()
        if config.population.sampled_counts:
            assert match is not None
            counts = match.report["population_games"]
            history = counts.get("historical_self_play", 0) // world
            scripts = sum(count for _, count in match.scripts)
            if scripts:
                assert config.script_population is not None
                public = config.script_population.model_copy(
                    update={
                        "fraction": scripts / games,
                        "agents": tuple(n for n, _ in match.scripts),
                    }
                )
        if history:
            rng = np.random.default_rng([config.seed, update, 1])
            name = (
                match.history
                if match
                else self.state["pool"][int(rng.integers(len(self.state["pool"])))]
            )
        settings = settings.model_copy(
            update={
                "script_population": public,
                "ppo": settings.ppo.model_copy(
                    update={
                        "population": "script_mix" if scripts else "self_play",
                        "script_fraction": scripts / games,
                        "script_opponents": public.agents if public else (),
                        "script_allocation": allocation,
                        "history": HistoricalPopulation(
                            checkpoint=config.output_dir / name, fraction=history / games
                        )
                        if name
                        else None,
                        "concurrent_history_inference": bool(
                            config.population.pfsp and config.population.pfsp.concurrent_inference
                        ),
                    }
                ),
            }
        )
        return settings, name, history

    def resolve(
        self, match: Match | None, update: int, world: int
    ) -> tuple[RuntimeSettings, ActorRuntime, ActorRuntime | None, str | None, int]:
        """Resolve one complete update without altering learner weights or random streams."""
        settings, name, history = self.selection(match, update, world)
        games = self.config.games // world
        count = 2 * games - history - script_games(settings, games)
        runtime = self.runtime(count)
        frozen = None
        if name:
            assert self.cache is not None
            device = next(self.actor.parameters()).device
            with torch.random.fork_rng(devices=[device] if device.type == "cuda" else []):
                frozen = self.cache.runtime(name, device, history)
        return settings, runtime, frozen, name, history
