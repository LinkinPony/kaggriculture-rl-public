"""Disjoint script/history budgets, resumable draws, and combined native collection."""

import copy
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.archive import PopulationCache
from kagg_revue.learning.collection.matched import MatchedCollection
from kagg_revue.learning.collection.population import create_training_batch
from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.distributed import seed_shard
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.matchmaking.config import Pfsp
from kagg_revue.learning.matchmaking.imports import transition
from kagg_revue.learning.matchmaking.scheduler import Matchmaker, live_report
from kagg_revue.learning.matchmaking.separate import script_table, select
from kagg_revue.learning.matchmaking.statistics import Record
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.learning.state import protocol
from kagg_revue.monitor.history import row_signatures
from kagg_revue.opponents.settings import PublicPopulation
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Policy


def _fixture() -> tuple[Experiment, dict[str, Any]]:
    config = Experiment(
        output_dir=Path("outputs/learning/separate-test"),
        games=128,
        architecture="grounded-v2",
        decision_interval=1,
        execution=Execution(),
        population=Population(
            fraction=0.5, capacity=8, pfsp=Pfsp(script_sampling="independent_pfsp")
        ),
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
            fraction=0.2,
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


def test_separate_budgets_rng_independence_and_recovery() -> None:
    """Keep exact 30/20/50 totals while script draws ignore all history weights."""
    config, state = _fixture()
    first = Matchmaker(config, state)
    second = Matchmaker(config, copy.deepcopy(state))
    totals: Counter[str] = Counter()
    seen: set[str] = set()
    signatures: set[str] = set()
    for update in range(1024, 1224):
        match = first.select(update, 2)
        assert match == second.select(update, 2)
        altered = {**state, "pool": list(reversed(state["pool"]))}
        script_records = {k: v for k, v in first.state.records.items() if k.startswith("script:")}
        assert match.scripts == select(config, altered, script_records, update, 2, 1024).scripts
        script, rank_games = match.scripts[0]
        seen.add(script)
        counts = match.report["population_games"]
        assert counts == {
            "self_play": 64 - rank_games * 2,
            "historical_self_play": 64,
            script: rank_games * 2,
        }
        assert rank_games in {12, 14}
        totals.update(selfplay=counts["self_play"], history=64, scripts=rank_games * 2)
        elapsed = update - 1023
        if elapsed % 5 == 0:
            assert totals == {
                "selfplay": elapsed * 128 * 3 // 10,
                "history": elapsed * 64,
                "scripts": elapsed * 128 // 5,
            }
        weights = [row["probability"] for row in match.report["scripts"].values()]
        assert sum(weights) == pytest.approx(1) and min(weights) >= 0.04
        assert all(
            row["overall_probability"] == pytest.approx(0.2 * row["probability"])
            for row in match.report["scripts"].values()
        )
        seeds = [
            seed_shard(config, update, rank, 2, counts=(64, 2 * rank_games)) for rank in (0, 1)
        ]
        assert len(set(seeds[0]) | set(seeds[1])) == 128
        assert not set(seeds[0]) & set(seeds[1])
        panels = {
            name: {
                "games": n,
                "wins": n if name == script else 0,
                "ties": 0,
                "losses": 0 if name == script else n,
            }
            for name, n in counts.items()
        }
        for scheduler in (first, second):
            scheduler.observe(match, update, panels)
            scheduler.ledger["completed_update"] = update
        signatures.add(row_signatures({"pfsp": match.report, "populations": panels})["population"])
        if update % 7 == 0:
            second = Matchmaker(config, copy.deepcopy(second.ledger))
    assert len(seen) == 5 and len(signatures) == 1 and first.state == second.state
    entries = live_report(config, state)["history"]
    assert len(entries) == 2 and all(entry["kind"] == "history" for entry in entries)
    assert sum(entry["probability"] for entry in entries) == pytest.approx(1)


def test_script_probabilities_follow_script_results_only() -> None:
    """Prefer difficult scripts, retain exploration, and ignore historical evidence."""
    config, _ = _fixture()
    assert config.script_population is not None and config.population.pfsp is not None
    prefix = f"script:{config.script_population.sha256}:"
    hard = Record(effective_games=128, effective_score=0, last_update=1023)
    easy = Record(effective_games=128, effective_score=128, last_update=1023)
    records = {f"{prefix}ahmed_v45": hard, f"{prefix}farming_v4_0914": easy}
    report = script_table(config, records, 1024)
    assert report["ahmed_v45"]["probability"] > report["metacounter_r1"]["probability"]
    assert report["metacounter_r1"]["probability"] > report["farming_v4_0914"]["probability"]
    assert script_table(config, {**records, "history:unrelated": hard}, 1024) == report
    swapped = script_table(
        config, {f"{prefix}ahmed_v45": easy, f"{prefix}farming_v4_0914": hard}, 1024
    )
    assert swapped["ahmed_v45"]["probability"] < swapped["farming_v4_0914"]["probability"]
    assert script_table(config, records, 10000)["ahmed_v45"]["probability"] == pytest.approx(0.2)


def test_separate_native_batches_and_runtime_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise self-play, one C++ script and a frozen neural policy in the same batch."""
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
    settings = runtime_settings(config)
    actor = Policy.from_layout(ContractLayout.resolve(settings))
    monkeypatch.setattr(
        PopulationCache,
        "runtime",
        lambda self, name, device, count: ActorRuntime(actor, count, sample=True, precision="fp32"),
    )
    collection = MatchedCollection(config, settings, state, actor)
    for update in (1024, 1025):
        match = select(config, state, {}, update, 2, 1024)
        active, runtime, frozen, _, history = collection.resolve(match, update, 2)
        RuntimeSettings.model_validate(active.model_dump())
        assert history == 32 and frozen is not None
        scripts = match.scripts[0][1]
        seeds = seed_shard(config, update, 0, 2, counts=(64, scripts * 2))
        batch = create_training_batch(active, seeds, frozen)
        assert Counter(batch.opponents) == {
            "self_play": 32 - scripts,
            "historical_self_play": 32,
            match.scripts[0][0]: scripts,
        }
        assert runtime.host.shape[0] == 96 - scripts
        batch.observe_into(runtime.host.numpy())
        assert np.isfinite(runtime.host.numpy()).all()
        runtime.act(0)
        frozen.act(0)
        batch.advance(runtime.selected.numpy(), 1)
        assert batch.step_index == 1


def test_quota_transition_preserves_pool_and_evidence() -> None:
    """Only move the sampling boundary; retain history membership and previous evidence."""
    config, state = _fixture()
    old = config.model_copy(
        update={
            "population": Population(fraction=0.65, capacity=8, unified=True, pfsp=Pfsp()),
            "script_population": config.script_population.model_copy(update={"fraction": 0})
            if config.script_population
            else None,
        }
    )
    Matchmaker(old, state)
    state["pfsp"]["started_update"] = 500
    before = copy.deepcopy(state)
    transition(config, state, old)
    assert state["pool"] == before["pool"]
    assert state["pfsp"]["records"] == before["pfsp"]["records"]
    assert state["pfsp"]["started_update"] == 1024
    assert "script_sampling" not in protocol(old)["population"]["pfsp"]
    invalid = protocol(config)
    invalid["population"]["unified"] = True
    with pytest.raises(ValueError, match="outside the unified"):
        Experiment.model_validate(invalid)


def test_script_replacement_preserves_checkpoint_evidence_and_history_pool() -> None:
    """New source identities get fresh priorities without altering saved history."""
    config, state = _fixture()
    Matchmaker(config, state)
    assert config.script_population is not None
    state["pool"] = ["initial.pt"]
    before = copy.deepcopy(state)
    new = config.model_copy(
        update={
            "script_population": config.script_population.model_copy(update={"sha256": "1" * 64})
        }
    )
    transition(new, state, config)
    assert state["pool"] == before["pool"]
    assert state["pfsp"] == before["pfsp"]
    table = script_table(new, {}, 1024)
    assert all(row["probability"] == pytest.approx(0.2) for row in table.values())
