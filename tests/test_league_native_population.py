from pathlib import Path

import numpy as np
import pytest
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.league.batches import LeagueBatch
from kagg_revue.learning.league.collection import schedule
from kagg_revue.learning.league.config import League
from kagg_revue.native import _revue_native as native
from kagg_revue.opponents.native_batch import create_native_opponent_session
from kagg_revue.policy.contracts import ContractLayout


def recipe():
    with initialize_config_dir(version_base=None, config_dir=str(Path("configs").resolve())):
        cfg = compose(config_name="learning_league_native")
    values = OmegaConf.to_container(cfg, resolve=True)
    return League.model_validate({**values["league"], "experiment": values["experiment"]})


def test_two_members_five_scripts_have_disjoint_seeds_balanced_seats_and_exact_budgets():
    config = recipe()
    assert config.members == ("bc", "spataro")
    assert len(config.script_names) == 5
    assert config.trajectories_per_member == 152
    seen = set()
    for update in (622, 623):
        for rank in (0, 1):
            seeds, owners = schedule(config, update, rank, 2)
            assert len(seeds) == 96 and not seen.intersection(seeds)
            seen.update(seeds)
            for member in range(2):
                assert (owners == member).sum() == 76
                assert (owners[:, 0] == member).sum() == (owners[:, 1] == member).sum()
                for script in range(2, 7):
                    assert ((owners[:, 0] == member) & (owners[:, 1] == script)).sum() == 2
                    assert ((owners[:, 1] == member) & (owners[:, 0] == script)).sum() == 2
    with pytest.raises(ValueError):
        League.model_validate({**config.protocol(), "games_per_script_per_member": 4})


def test_mixed_native_batch_controls_script_seats_and_matches_direct_sessions():
    config = recipe()
    settings = runtime_settings(config.experiment)
    layout = ContractLayout.resolve(settings)
    owners = np.array([[0, 1], [0, 0], [1, 1], [0, 6], [6, 1]])
    seeds = list(range(1860909400, 1860909405))
    batch = LeagueBatch(config, settings, seeds, owners)
    engines = [native.Engine(seed, config.experiment.environment) for seed in seeds]
    sessions = [create_native_opponent_session(config.script_names[-1], 10) for _ in range(2)]
    actions = np.zeros((10, layout.factors), np.int64)
    host = np.empty((10, layout.observation.features), np.float16)
    for step in range(719):
        if step in (0, 144, 648, 718):
            batch.observe_selfplay_into(host)
            assert np.isfinite(host).all()
        batch.advance_programs(actions, 1, layout.capacity)
        for index, engine in enumerate(engines):
            planned = [{}, {}]
            if index >= 3:
                seat = 1 if index == 3 else 0
                planned[seat] = native.native_opponent_action(engine, seat, sessions[index - 3])
            engine.step(*planned)
    assert batch.completed_games == 5 and batch.transitions == 5 * 719
    np.testing.assert_array_equal(
        batch.cash(), [[engine.money(seat) for seat in (0, 1)] for engine in engines]
    )
