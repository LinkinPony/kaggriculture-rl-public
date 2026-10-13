"""Fresh policy suffix rollouts over authenticated, immutable source states."""

from typing import Any

import numpy as np

from kagg_revue.datasets.restarts import RestartBank
from kagg_revue.learning.collection.history import HistoricalBatch
from kagg_revue.learning.collection.population import TrainingBatch, historical_games, script_games
from kagg_revue.learning.collection.sampling import Rollout, collect
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import rank_world, seed_shard
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Policy


def create_bank(config: Experiment, policy: Policy, split: str = "train") -> RestartBank | None:
    """Bind the source bank to the exact learner observation and official geometry."""
    if config.curriculum is None:
        return None
    return RestartBank(
        config.curriculum,
        split=split,
        environment=config.environment,
        units=config.unit_limit,
        quantities=policy.layout.observation.quantities,
        workers=config.workers,
        features=policy.layout.observation.features,
        starts=config.curriculum.starts,
    )


def collect_update(
    config: Experiment,
    settings: RuntimeSettings,
    policy: Policy,
    runtime: ActorRuntime,
    history_runtime: ActorRuntime | None,
    bank: RestartBank | None,
    update: int,
) -> tuple[Rollout, dict[str, Any]]:
    """Credit only the sampled suffix and retain periodic whole-season training."""
    start = 0 if config.curriculum is None else config.curriculum.start(update)
    rank, world = rank_world()
    seeds = seed_shard(
        config,
        update,
        rank,
        world,
        counts=(historical_games(settings, config.games), script_games(settings, config.games))
        if config.population.sampled_counts
        else None,
    )
    games = len(seeds)
    seed = seeds[0]
    initial = np.full((games, 2), config.environment.get("startingMoney", 3000), np.float64)
    batch = None
    metadata: dict[str, Any] = {
        "start_step": 0,
        "split": "fresh",
        "official_prefix_actions_in_ppo": 0,
    }
    if start:
        if bank is None:
            raise ValueError("curriculum update requires an authenticated source bank")
        restored, metadata = bank.sample(start, games, seed)
        history = int(games * config.population.fraction)
        selfplay = games - history
        seats = np.arange(history, dtype=np.int64) % 2
        frozen = None
        if history:
            if history_runtime is None:
                raise ValueError("historical curriculum games require a frozen actor runtime")
            frozen = HistoricalBatch(
                restored.fork(np.arange(selfplay, games, dtype=np.int64)),
                seats,
                history_runtime.host.numpy(),
                history_runtime.selected.numpy(),
                support_features=history_runtime.policy.layout.observation.support_features,
            )
        batch = TrainingBatch(
            restored.fork(np.arange(selfplay, dtype=np.int64)),
            frozen,
            selfplay,
            ("self_play",) * selfplay + ("historical_self_play",) * history,
            policy.layout.capacity,
        )
        initial = np.asarray(metadata["initial_cash"], dtype=np.float64)
        initial[selfplay:] = initial[selfplay:][
            np.arange(history)[:, None], np.stack((seats, 1 - seats), axis=1)
        ]
    rollout = collect(
        settings,
        policy,
        runtime,
        seeds,
        history_runtime,
        prepared_batch=batch,
        start_decision=start,
        initial_cash=initial,
    )
    metadata["mean_cash_change"] = float((rollout.cash - initial).mean())
    metadata["policy_transitions"] = games * (settings.turns - start)
    return rollout, metadata
