"""PFSP evidence, reproducible recovery, temporal coverage and monitor boundaries."""

import copy
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.matchmaking.config import Pfsp
from kagg_revue.learning.matchmaking.pool import member_update, retain, snapshot
from kagg_revue.learning.matchmaking.scheduler import Matchmaker
from kagg_revue.learning.matchmaking.statistics import Record, probabilities
from kagg_revue.learning.state import protocol
from kagg_revue.monitor.history import row_signatures
from kagg_revue.monitor.learning import metrics
from kagg_revue.opponents.settings import PublicPopulation


def _fixture() -> tuple[Experiment, dict[str, Any]]:
    config = Experiment(
        output_dir=Path("outputs/learning/pfsp-test"),
        games=128,
        architecture="grounded-v2",
        decision_interval=1,
        execution=Execution(),
        population=Population(fraction=0.25, capacity=8, snapshot_interval=64, pfsp=Pfsp()),
        script_population=PublicPopulation(
            manifest=Path("data/external/fixture.json"),
            sha256="0" * 64,
            agents=("ahmed_v45", "farming_v4_0914", "shop_router_0913", "rayk_v38_low_pressure"),
            fraction=0.5,
        ),
    )
    names = [
        "initial.pt",
        *(f"checkpoints/update-{update:06d}.pt" for update in range(64, 641, 64)),
    ]
    state = {
        "protocol": protocol(config),
        "completed_update": 640,
        "members": {name: str(index) for index, name in enumerate(names)},
        "pool": names[-8:],
        "records": [],
    }
    return config, state


def _panel(games: int, *, win: bool) -> dict[str, int]:
    return {"games": games, "wins": games if win else 0, "ties": 0, "losses": 0 if win else games}


def test_loss_priority_decay_draws_and_exploration() -> None:
    """Hard opponents get more mass while draws, uncertainty and stale data stay calibrated."""
    options = Pfsp()
    easy, hard, tied = Record(), Record(), Record()
    easy.observe(_panel(512, win=True), 1, options)
    hard.observe(_panel(512, win=False), 1, options)
    tied.observe({"games": 32, "wins": 0, "ties": 32, "losses": 0}, 1, options)
    assert tied.probability(1, options) == 0.5
    assert easy.effective_games == options.max_effective_games
    weights = probabilities([easy, hard, tied], 2, options, latest=False)
    assert weights[1] > weights[2] > weights[0] >= options.uniform_fraction / 3
    assert weights.sum() == pytest.approx(1)
    assert abs(easy.probability(10000, options) - 0.5) < 1e-10
    with pytest.raises(ValueError, match="every physical game"):
        easy.observe({"games": 3, "wins": 1, "ties": 1, "losses": 0}, 2, options)


def test_rank_identical_pair_allocations_resume_and_no_duplicate_outcomes() -> None:
    """Adaptive allocations keep exact budgets and continue from serialized evidence."""
    config, state = _fixture()
    ranks = [Matchmaker(config, state), Matchmaker(config, copy.deepcopy(state))]
    draws = []
    for update in range(641, 651):
        match = ranks[0].select(update, 2)
        assert match == ranks[1].select(update, 2)
        assert sum(count for _, count in match.scripts) == 32
        assert all(count >= 2 and count % 2 == 0 for _, count in match.scripts)
        draws.append(match.scripts)
        panels = {
            "historical_self_play": _panel(32, win=False),
            **{name: _panel(count * 2, win=name != "ahmed_v45") for name, count in match.scripts},
        }
        for rank in ranks:
            rank.observe(match, update, panels)
        if update == 645:
            saved = copy.deepcopy(ranks[1].ledger)
            saved["completed_update"] = update
            ranks[1] = Matchmaker(config, saved)
    assert len(set(draws)) > 1
    assert ranks[0].ledger["pfsp"] == ranks[1].ledger["pfsp"]
    assert ranks[0].select(651, 2) == ranks[1].select(651, 2)
    with pytest.raises(ValueError, match="duplicated or skipped"):
        ranks[0].observe(match, 650, panels)


def test_pool_retains_initial_recent_and_old_eras() -> None:
    """Dense recent saves cannot evict the BC control or all earlier training eras."""
    names = ["pretraining/shard-000400.pt"]
    names += [
        f"checkpoints/update-{i:06d}.pt" for i in (100, 500, 1000, 2000, *range(3700, 3801, 4))
    ]
    pool = retain(names, 16, 4)
    assert len(pool) == len(set(pool)) == 16
    assert pool[0] == names[0]
    assert pool[-4:] == names[-4:]
    assert 1000 in [member_update(name) for name in pool]
    config, state = _fixture()
    state["members"]["anchors/seed-901.pt"] = "anchor"
    Matchmaker(config, state)
    assert not any("anchors/" in name for name in state["pool"])
    added = "checkpoints/update-000704.pt"
    state["members"][added] = "new-snapshot-hash"
    snapshot(config, state, added)
    assert state["pool"][-1] == added and len(state["pool"]) == config.population.capacity
    state["completed_update"] = state["pfsp"]["last_update"] = 704
    restored = Matchmaker(config, state)
    match = restored.select(705, 2)
    assert match.report["pool_size"] == config.population.capacity
    assert restored.state.records["history:new-snapshot-hash"].effective_games == 0


def test_uniform_protocol_compatibility_and_invalid_pfsp_budget() -> None:
    """Opt-in fields leave old recovery identities unchanged and reject impossible batches."""
    old = Experiment(output_dir=Path("outputs/learning/old"))
    assert "pfsp" not in protocol(old)["population"]
    with pytest.raises(ValueError, match="older snapshots"):
        Population(fraction=0, pfsp=Pfsp())
    config, _ = _fixture()
    with pytest.raises(ValueError, match="minimum seat pairs"):
        Experiment.model_validate(
            {
                **protocol(config),
                "population": {
                    **protocol(config)["population"],
                    "pfsp": {"script_min_pairs_per_rank": 5},
                },
            }
        )


def test_fresh_bc_history_without_scripts_grows_and_resumes() -> None:
    """A fresh neural-only run starts at its BC endpoint and admits its own snapshots."""
    config, _ = _fixture()
    config = Experiment.model_validate(
        {
            **protocol(config),
            "script_population": None,
            "population": {**protocol(config)["population"], "fraction": 0.5},
        }
    )
    endpoint = "pretraining/shard-000904.pt"
    state: dict[str, Any] = {
        "completed_update": 0,
        "rl_initial": endpoint,
        "members": {
            "initial.pt": "random-root",
            "anchors/seed-901.pt": "evaluation-only",
            "pretraining/shard-000226.pt": "earlier-bc-epoch",
            endpoint: "final-bc",
        },
        "pool": [endpoint],
        "records": [],
    }
    scheduler = Matchmaker(config, state)
    for update in range(1, 65):
        match = scheduler.select(update, 2)
        assert match.history == endpoint
        assert match.scripts == () and match.report["scripts"] == {}
        assert match.report["selected"]["probability"] == pytest.approx(1.0)
        scheduler.observe(match, update, {"historical_self_play": _panel(64, win=True)})
        state["completed_update"] = update
    name = "checkpoints/update-000064.pt"
    state["members"][name] = "first-rl-snapshot"
    snapshot(config, state, name)
    restored = Matchmaker(config, copy.deepcopy(state))
    assert state["pool"] == [endpoint, name]
    assert scheduler.select(65, 2) == restored.select(65, 2)
    assert all(key.startswith("history:") for key in restored.state.records)


def test_dynamic_pfsp_counts_do_not_break_every_chart_window() -> None:
    """Keep one protocol transition while preserving actual sample weights and identity."""
    row: dict[str, Any] = {
        "physical_games": 128,
        "history_score": 0.5,
        "populations": {
            "self_play": {"games": 32},
            "historical_self_play": {"games": 32},
            "ahmed_v45": {"games": 16},
            "farming_v4_0914": {"games": 48},
        },
        "pfsp": {"enabled": True, "selected": {"update": 128, "score": 0.4, "probability": 0.2}},
    }
    changed = copy.deepcopy(row)
    changed["populations"]["ahmed_v45"]["games"] = 24
    changed["populations"]["farming_v4_0914"]["games"] = 40
    assert row_signatures(row) == row_signatures(changed)
    del changed["pfsp"]
    assert row_signatures(row) != row_signatures(changed)
    assert metrics(row)["rl/rollout/opponents/history/opponent_update"] == 128
    assert np.isfinite(list(metrics(row).values())).all()
