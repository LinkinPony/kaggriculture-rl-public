"""Pure mirror games preserve both learner seats and authenticated continuation controls."""

import json
from pathlib import Path

import numpy as np
import pytest

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.population import create_training_batch, outcomes, policy_rows
from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.distributed import seed_shard
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.matchmaking.config import Pfsp
from kagg_revue.learning.progress import publish
from kagg_revue.learning.recovery.selfplay import SelfPlayChange, resolved
from kagg_revue.learning.state import protocol
from kagg_revue.policy.contracts import ContractLayout


def test_pure_selfplay_has_two_current_policy_trajectories_per_native_game() -> None:
    """No frozen runtime is needed, and all full-game seats belong to the learner."""
    config = Experiment(
        output_dir=Path("outputs/learning/test"),
        games=4,
        architecture="grounded-v2",
        decision_interval=1,
        population=Population(fraction=0),
        unit_limit=2,
        environment={
            "boardSize": 4,
            "episodeSteps": 9,
            "turnsPerDay": 3,
            "maxMarketOrdersPerTurn": 2,
        },
    )
    settings = runtime_settings(config)
    assert settings.ppo.history is None and settings.script_population is None
    layout = ContractLayout.resolve(settings)
    batch = create_training_batch(settings, seed_shard(config, 1, 0, 1))
    assert batch.scripts is None and batch.selfplay_games == 4
    views = np.empty((8, layout.observation.features), np.float16)
    actions = np.zeros((8, layout.factors), np.int64)
    for _ in range(8):
        batch.observe_into(views)
        batch.advance(actions, 1)
    cash = batch.cash(8)
    assert len(policy_rows(cash, 4)) == 8
    panels = outcomes(cash, list(batch.opponents))
    assert set(panels) == {"self_play"}
    assert panels["self_play"]["games"] == 4
    assert panels["self_play"]["training_trajectories"] == 8


def test_selfplay_tuning_preserves_model_learning_rates_and_allocates_fresh_seeds() -> None:
    """Changing sampling and batch geometry must not silently reset model or PPO controls."""
    old = Experiment(output_dir=Path("outputs/learning/test"), execution=Execution(), games=512)
    request = SelfPlayChange(
        run=old.output_dir,
        train_seed=800000000,
        batch_rows=7680,
        execution=Execution(microbatch_rows=3840),
        qualification=Path("outputs/analysis/test.json"),
    )
    state = {"protocol": protocol(old)}
    new = resolved(state, request)
    assert new.games == 128 and new.population.fraction == 0 and new.script_population is None
    changed = {key for key, value in protocol(new).items() if protocol(old).get(key) != value}
    assert changed == {"games", "train_seed", "batch_rows", "execution", "population"}
    with pytest.raises(ValueError, match="fresh seed"):
        resolved(state, request.model_copy(update={"train_seed": old.train_seed}))
    with pytest.raises(ValueError, match="worker RNG"):
        resolved(state, request.model_copy(update={"execution": Execution(devices=("cuda:0",))}))


def test_pause_pfsp_preserves_seed_allocation_and_hides_live_sampler(tmp_path: Path) -> None:
    """An opponent-only switch disables PFSP without resetting the ongoing run's seeds."""
    old = Experiment(
        output_dir=Path("outputs/learning/test"),
        games=128,
        execution=Execution(),
        population=Population(fraction=0.5, pfsp=Pfsp()),
    )
    assert old.execution is not None
    request = SelfPlayChange(
        run=Path("outputs/learning/test"),
        games=old.games,
        train_seed=old.train_seed,
        batch_rows=old.batch_rows,
        execution=old.execution,
        qualification=Path("outputs/analysis/test.json"),
    )
    new = resolved({"protocol": protocol(old)}, request)
    assert new.population.fraction == 0 and new.population.pfsp is None
    assert new.script_population is None
    assert {k for k in protocol(new) if protocol(new)[k] != protocol(old)[k]} == {"population"}
    assert sorted(seed for rank in range(2) for seed in seed_shard(new, 125, rank, 2)) == sorted(
        seed for rank in range(2) for seed in seed_shard(old, 125, rank, 2)
    )
    state = {"run_id": "test", "completed_update": 124, "records": [], "pfsp": {"frozen": True}}
    publish(new.model_copy(update={"output_dir": tmp_path}), state, "reinforcement_learning")
    live = json.loads((tmp_path / "learning-progress.json").read_text())
    assert live["pure_selfplay"] and live["population_games"] == {"self_play": 128}
    assert "pfsp" not in live
