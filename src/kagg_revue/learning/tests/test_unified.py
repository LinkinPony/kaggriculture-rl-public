"""Unified PFSP budget, identity, recovery and native collection regressions."""

import copy
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.matched import MatchedCollection
from kagg_revue.learning.collection.population import create_training_batch
from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.distributed import seed_shard
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.matchmaking.config import Mastery, Pfsp
from kagg_revue.learning.matchmaking.scheduler import Matchmaker, live_report
from kagg_revue.learning.matchmaking.unified import table
from kagg_revue.learning.state import protocol
from kagg_revue.monitor.history import row_signatures
from kagg_revue.opponents.settings import PublicPopulation
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.model import Policy


def _fixture() -> tuple[Experiment, dict[str, Any]]:
    config = Experiment(
        output_dir=Path("outputs/learning/unified-test"),
        games=128,
        architecture="grounded-v2",
        decision_interval=1,
        execution=Execution(),
        population=Population(fraction=0.65, capacity=8, unified=True, pfsp=Pfsp()),
        script_population=PublicPopulation(
            manifest=Path("data/external/kaggriculture-public-native-20260916/manifest.json"),
            sha256="6d66d351cc01eb3e6e58f9921de0a1842f78aee03686b0312355725e1bdf2aa8",
            agents=(
                "ahmed_v45",
                "farming_v4_0914",
                "metacounter_r1",
                "rayk_v38_low_pressure",
                "shop_router_0913",
            ),
            fraction=0,
        ),
    )
    state: dict[str, Any] = {
        "protocol": protocol(config),
        "completed_update": 1023,
        "members": {"initial.pt": "initial", "checkpoints/update-001024.pt": "recent"},
        "pool": ["initial.pt", "checkpoints/update-001024.pt"],
        "records": [],
    }
    return config, state


@pytest.mark.parametrize("mastery", [None, Mastery()])
def test_unified_budget_probabilities_and_recovery(mastery: Mastery | None) -> None:
    """Share loss weights across types, preserve unsampled evidence and replay every rank."""
    config, state = _fixture()
    config = config.model_copy(
        update={"population": config.population.model_copy(update={"pfsp": Pfsp(mastery=mastery)})}
    )
    first = Matchmaker(config, state)
    second = Matchmaker(config, copy.deepcopy(state))
    seen: set[str] = set()
    selfplay = 0
    signatures = set()
    for update in range(1024, 1224):
        match = first.select(update, 2)
        assert match == second.select(update, 2)
        chosen = match.report["selected"]
        seen.add(chosen["name"])
        counts = match.report["population_games"]
        assert sum(counts.values()) == 128 and counts["self_play"] in {44, 48}
        selfplay += counts["self_play"]
        if (update - 1023) % 5 == 0:
            assert selfplay == (update - 1023) * 128 * 35 // 100
        global_counts = (
            counts.get("historical_self_play", 0),
            sum(n for _, n in match.scripts) * 2,
        )
        seeds = [seed_shard(config, update, rank, 2, counts=global_counts) for rank in (0, 1)]
        assert len(set(seeds[0]) | set(seeds[1])) == 128
        assert not set(seeds[0]) & set(seeds[1])
        panels = {
            name: {
                "games": games,
                "wins": games if chosen["kind"] == "history" else 0,
                "ties": 0,
                "losses": games if chosen["kind"] == "script" else 0,
            }
            for name, games in counts.items()
        }
        for scheduler in (first, second):
            scheduler.observe(match, update, panels)
            scheduler.ledger["completed_update"] = update
        signatures.add(row_signatures({"pfsp": match.report, "populations": panels})["population"])
        if update % 7 == 0:
            second = Matchmaker(config, copy.deepcopy(second.ledger))
    assert len(seen) == 7 and len(signatures) == 1
    assert first.state == second.state
    entries = live_report(config, state)["history"]
    assert sum(entry["probability"] for entry in entries) == pytest.approx(1)
    assert all(entry["games"] > 0 for entry in entries)
    if mastery is not None:
        reviewed = [entry for entry in entries if entry["mastered"]]
        assert reviewed and sum(entry["probability"] for entry in reviewed) == pytest.approx(0.05)
    assert min(e["probability"] for e in entries if e["kind"] == "script") > next(
        e["probability"] for e in entries if e["name"] == "initial.pt"
    )
    with pytest.raises(ValueError, match="duplicated or skipped"):
        first.observe(match, 1223, panels)


def test_script_draw_resolves_balanced_native_batch() -> None:
    """A script-only frozen batch leaves both self-play seats and no stale neural runtime."""
    torch.set_num_threads(1)
    config, state = _fixture()
    config = config.model_copy(
        update={
            "device": "cpu",
            "width": 16,
            "depth": 1,
            "heads": 2,
            "critic_width": 16,
            "critic_depth": 1,
            "compile": False,
            "execution": Execution(compile_inference=False),
        }
    )
    scheduler = Matchmaker(config, state)
    # Search independent root seeds without mutating any rollout or Torch RNG.
    for seed in range(100):
        scheduler.config = config.model_copy(update={"seed": seed})
        match = scheduler.select(1024, 2)
        if match.scripts:
            break
    assert match.scripts
    settings = runtime_settings(config)
    actor = Policy.from_layout(ContractLayout.resolve(settings))
    collection = MatchedCollection(config, settings, state, actor)
    active, runtime, frozen, name, history = collection.resolve(match, 1024, 2)
    assert frozen is None and name is None and history == 0
    assert active.ppo.history is None and len(active.ppo.script_opponents) == 1
    seeds = seed_shard(config, 1024, 0, 2, counts=(0, match.scripts[0][1] * 2))
    batch = create_training_batch(active, seeds)
    assert batch.selfplay_games == 22 and runtime.host.shape[0] == 86
    assert len(batch.opponents) == 64 and set(batch.opponents) == {"self_play", match.scripts[0][0]}
    batch.observe_into(runtime.host.numpy())
    assert np.isfinite(runtime.host.numpy()).all()
    actions, _ = runtime.act(0)
    batch.advance(actions.numpy(), 1)
    assert batch.step_index == 1


def test_unified_distribution_prior_and_invalid_quota() -> None:
    """Exploration is per identity across types; scripts cannot retain a separate quota."""
    config, state = _fixture()
    scheduler = Matchmaker(config, state)
    entries = table(config, state, scheduler.state.records, 1024)
    assert [e["probability"] for e in entries[:-1]] == pytest.approx([0.9 / 7] * 6)
    assert entries[-1]["name"] == "checkpoints/update-001024.pt"
    assert entries[-1]["probability"] == pytest.approx(0.1 + 0.9 / 7)
    raw = protocol(config)
    raw["script_population"]["fraction"] = 0.25
    with pytest.raises(ValueError, match="public mixtures"):
        Experiment.model_validate(raw)


def test_unified_scripts_have_no_separate_minimum_or_reserved_games() -> None:
    """Legacy script minimums cannot alter common-pool probabilities or allocation."""
    config, state = _fixture()
    values = protocol(config)
    values["population"]["fraction"] = 0.7
    config = Experiment.model_validate(values)
    values["population"]["pfsp"]["script_min_pairs_per_rank"] = 1000
    alternate = Experiment.model_validate(values)
    first = Matchmaker(config, copy.deepcopy(state))
    second = Matchmaker(alternate, copy.deepcopy(state))
    seen: set[str] = set()
    selfplay = 0
    for update in range(1024, 1044):
        match = first.select(update, 2)
        assert match == second.select(update, 2)
        chosen = match.report["selected"]
        seen.add(chosen["kind"])
        counts = match.report["population_games"]
        assert len(counts) == 2 and sum(counts.values()) == 128
        selfplay += counts["self_play"]
        if chosen["kind"] == "history":
            assert match.scripts == ()
            assert all(row["games"] == 0 for row in match.report["scripts"].values())
        else:
            assert match.history == ""
            assert match.scripts == ((chosen["name"], counts[chosen["name"]] // 2),)
        panels = {
            name: {"games": games, "wins": 0, "ties": games, "losses": 0}
            for name, games in counts.items()
        }
        for sampler in (first, second):
            sampler.observe(match, update, panels)
    assert selfplay == 20 * 128 * 3 // 10
    assert seen == {"history", "script"}
