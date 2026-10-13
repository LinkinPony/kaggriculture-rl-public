"""Cross-run provenance, exact quantity semantics and paused PFSP continuation."""

import copy
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.archive import PopulationCache
from kagg_revue.learning.collection.population import create_training_batch
from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.matchmaking.archives import HistoricalArchive, import_archive
from kagg_revue.learning.matchmaking.config import HistoricalSource, Pfsp
from kagg_revue.learning.matchmaking.imports import (
    ensure_imported,
    import_opponents,
    registered,
    transition,
)
from kagg_revue.learning.matchmaking.observations import legacy_layout
from kagg_revue.learning.matchmaking.pool import snapshot
from kagg_revue.learning.matchmaking.scheduler import Matchmaker
from kagg_revue.learning.optimization.settings import HistoricalPopulation
from kagg_revue.learning.pretraining.config import InitialWeights
from kagg_revue.learning.state import load_member, member_path, protocol
from kagg_revue.native import _revue_core as core
from kagg_revue.policy.checkpoints import save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.migration import legacy_contract
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Policy


def _config(path: Path) -> Experiment:
    return Experiment(
        output_dir=path,
        games=4,
        width=16,
        depth=1,
        heads=2,
        critic_width=16,
        critic_depth=1,
        architecture="grounded-v2",
        decision_interval=1,
        unit_limit=2,
        quantity_max=2,
        quantity_extra=(5, 9),
        compile=False,
        environment={
            "boardSize": 4,
            "episodeSteps": 9,
            "turnsPerDay": 3,
            "maxMarketOrdersPerTurn": 2,
        },
        population=Population(fraction=0.5, capacity=8, pfsp=Pfsp()),
    )


@pytest.mark.parametrize("market_budget", [False, True])
@pytest.mark.parametrize(
    "agronomy,derived,previous",
    [(False, False, "same"), (True, False, "v2"), (True, True, "v2"), (True, True, "v4")],
)
def test_foreign_vocabulary_executes_exact_original_programs(
    market_budget: bool, agronomy: bool, derived: bool, previous: str
) -> None:
    """Every seat's program matches its own native session despite incompatible indices."""
    torch.set_num_threads(1)
    config = _config(Path("outputs/learning/quantity-test"))
    config = config.model_copy(
        update={"market_budget": market_budget, "agronomy": agronomy, "derived": derived}
    )
    settings = runtime_settings(config)
    settings = settings.model_copy(
        update={
            "ppo": settings.ppo.model_copy(
                update={"history": HistoricalPopulation(checkpoint=Path("unused.pt"), fraction=0.5)}
            )
        }
    )
    learner = ContractLayout.resolve(settings)
    opponent = replace(
        learner,
        observation=replace(learner.observation, quantities=(1, 2, 3, 9)),
        network=replace(learner.network, market_budget=False),
    )
    if derived:
        opponent = legacy_contract(opponent)
    if previous == "v2":
        opponent = legacy_layout(opponent)
    runtime = ActorRuntime(Policy.from_layout(opponent), 2, sample=True, precision="fp32")
    batch = create_training_batch(settings, [61, 62, 63, 64], runtime)
    historical = batch.scripts
    observations = np.empty((6, learner.observation.features), np.float16)
    plans = np.zeros((6, learner.factors), np.int64)
    rng = np.random.default_rng(19)
    sessions = [core.ContractSession(config.environment, 2) for _ in range(4)]
    engines = [core.Engine(seed, config.environment) for seed in (63, 64)]
    for _ in range(8):
        batch.observe_into(observations)
        plans[:] = rng.integers(np.asarray(learner.cardinalities), size=plans.shape)
        runtime.selected[:] = torch.from_numpy(
            rng.integers(np.asarray(opponent.cardinalities), size=(2, opponent.factors))
        )
        for programs in (plans, runtime.selected.numpy()):
            operations = programs[:, 1 : learner.work_factors : 4]
            operations[(operations > 0) & (operations < 5)] = 0
        saved = plans.copy(), runtime.selected.clone()
        expected = []
        for lane in range(2):
            actions = []
            for seat in range(2):
                session = sessions[2 * lane + seat]
                session.update(historical.batch.observation(lane, seat))
                learned = seat == lane
                expected_view = np.empty(
                    (1, (learner if learned else opponent).observation.features), np.float16
                )
                session.observe_into(expected_view)
                actual_view = (
                    observations[4 + lane : 5 + lane]
                    if learned
                    else runtime.host.numpy()[lane : lane + 1]
                )
                np.testing.assert_array_equal(actual_view, expected_view)
                program = (
                    plans[4 + lane : 5 + lane]
                    if learned
                    else runtime.selected[lane : lane + 1].numpy()
                )
                quantities = settings.quantities if learned else opponent.observation.quantities
                session.set_program(program, 1, list(quantities))
                actions.append(dict(session.program_action()))
            engine = engines[lane]
            engine.step(*actions)
            expected.append(engine)
        batch.advance(plans, 1)
        np.testing.assert_array_equal(plans, saved[0])
        torch.testing.assert_close(runtime.selected, saved[1])
        for lane, engine in enumerate(expected):
            for seat in (0, 1):
                assert historical.batch.observation(lane, seat) == engine.observation(seat)


def test_import_keeps_foreign_lineage_and_is_not_learner_input(
    tmp_path: Path, monkeypatch: Any
) -> None:
    """Explicit imports authenticate source bytes and never bypass learner ancestry checks."""
    monkeypatch.chdir(tmp_path)
    source = Path("outputs/learning/old")
    config = _config(source)
    settings = runtime_settings(config)
    actor = Policy.from_layout(ContractLayout.resolve(settings))
    name = "checkpoints/update-000004.pt"
    save_policy(
        source / name,
        actor,
        settings,
        update=4,
        lineage={"run_id": "old-root", "kind": "reinforcement_learning"},
    )
    old: dict[str, Any] = {
        "protocol": protocol(config),
        "run_id": "old-root",
        "native": "engine",
        "completed_update": 4,
        "members": {name: digest(source / name)},
    }
    write_json(source / "state.json", old)
    destination = _config(Path("outputs/learning/new"))
    selection = HistoricalSource(
        run=source, state_sha256=digest(source / "state.json"), checkpoints=(name,)
    )
    destination = destination.model_copy(
        update={"population": destination.population.model_copy(update={"sources": (selection,)})}
    )
    state: dict[str, Any] = {"run_id": "new-root", "native": "engine", "members": {}}
    assert not registered(destination, state)
    import_opponents(destination, state)
    assert registered(destination, state)
    imported = next(iter(state["external_opponents"]))
    assert state["external_opponents"][imported]["run_id"] == "old-root"
    assert state["members"][imported] == old["members"][name]
    assert (
        digest(member_path(destination, state, imported))
        == state["inference_artifacts"][imported]["sha256"]
    )
    state.update(completed_update=0, rl_initial="pretraining/shard-000004.pt")
    state["members"][state["rl_initial"]] = "own-bc"
    transition(destination, state, destination)
    assert state["pool"] == [state["rl_initial"], imported]
    assert state["pfsp"]["started_update"] == 1
    assert state["pfsp"]["records"] == {}
    cache = PopulationCache(destination, state)
    target = Policy.from_layout(actor.layout)
    cache.load(imported, target)
    runtime = cache.runtime(imported, torch.device("cpu"), 2)
    wider = cache.runtime(imported, torch.device("cpu"), 4)
    assert runtime.host.shape[0] == 2 and wider.host.shape[0] == 4
    assert cache.runtime(imported, torch.device("cpu"), 2) is runtime
    for key, tensor in actor.state_dict().items():
        torch.testing.assert_close(target.state_dict()[key], tensor, rtol=0, atol=0)
    with pytest.raises(ValueError, match="lineage differs"):
        load_member(destination, state, imported, torch.device("cpu"))
    unregistered = copy.deepcopy(state)
    del unregistered["external_opponents"]
    assert not registered(destination, unregistered)
    with pytest.raises(ValueError, match="different random root"):
        PopulationCache(destination, unregistered).load(imported, target)
    old["members"][name] = "0" * 64
    write_json(source / "state.json", old)
    with pytest.raises(ValueError, match="ledger hash"):
        import_opponents(destination, state)
    before = copy.deepcopy(state)
    ensure_imported(destination, state)
    assert state == before
    member_path(destination, state, imported).write_bytes(b"corrupted local opponent")
    with pytest.raises(ValueError, match="authenticated member"):
        ensure_imported(destination, state)


def test_reactivation_keeps_evidence_and_pins_external_history() -> None:
    """Paused evidence decays through the gap and the latest bonus stays on the own run."""
    config = _config(Path("outputs/learning/resume-test"))
    state: dict[str, Any] = {
        "completed_update": 4,
        "members": {"initial.pt": "root"},
        "pool": ["initial.pt"],
        "records": [],
    }
    first = Matchmaker(config, state)
    match = first.select(5, 1)
    first.observe(
        match, 5, {"historical_self_play": {"games": 2, "wins": 2, "ties": 0, "losses": 0}}
    )
    previous_records = copy.deepcopy(state["pfsp"]["records"])
    state["completed_update"] = 500
    external = "historical/old/update-004302.pt"
    state["external_opponents"] = {external: {"run": "outputs/learning/old"}}
    state["members"][external] = "old"
    previous = config.model_copy(update={"population": Population(fraction=0, capacity=8)})
    transition(config, state, previous)
    assert state["pfsp"]["records"] == previous_records
    assert state["pfsp"]["last_update"] == 500 and state["pfsp"]["started_update"] == 501
    for update in range(504, 601, 4):
        name = f"checkpoints/update-{update:06d}.pt"
        state["members"][name] = str(update)
        snapshot(config, state, name)
    assert external in state["pool"] and len(state["pool"]) == 8
    assert state["pool"][-1] == "checkpoints/update-000600.pt"
    assert Matchmaker(config, copy.deepcopy(state)).select(501, 1) == Matchmaker(
        config, state
    ).select(501, 1)


@pytest.mark.parametrize("kind", ["random", "checkpoint"])
def test_initial_opponent_retains_root_provenance_and_transitive_native_evidence(
    tmp_path: Path, monkeypatch: Any, kind: str
) -> None:
    """Carry an old initial policy across archives without losing or inventing ancestry."""
    monkeypatch.chdir(tmp_path)
    source = Path("outputs/learning/old-root")
    config = _config(source)
    if kind == "checkpoint":
        parent = source / "weight-transfer/parent.pt"
        parent.parent.mkdir(parents=True)
        parent.write_bytes(b"authenticated parent fixture")
        config = config.model_copy(
            update={
                "initial_weights": InitialWeights(
                    run=Path("outputs/learning/parent"),
                    checkpoint="checkpoints/update-000004.pt",
                    sha256=digest(parent),
                )
            }
        )
    settings = runtime_settings(config)
    actor = Policy.from_layout(ContractLayout.resolve(settings))
    lineage = {"run_id": "root-run", "kind": kind, "seed": config.seed}
    if config.initial_weights:
        lineage["parent_sha256"] = config.initial_weights.sha256
    save_policy(source / "initial.pt", actor, settings, lineage=lineage)
    original: dict[str, Any] = {
        "schema": f"{kind}-root-league-v1",
        "initialization": kind,
        "protocol": protocol(config),
        "run_id": "root-run",
        "native": "old-engine",
        "completed_update": 0,
        "members": {"initial.pt": digest(source / "initial.pt")},
        "input_weights": [config.initial_weights.model_dump(mode="json")]
        if config.initial_weights
        else [],
    }
    if config.initial_weights:
        original["weight_transfer"] = {
            "artifact": "weight-transfer/parent.pt",
            "sha256": config.initial_weights.sha256,
        }
    write_json(source / "state.json", original)
    selection = HistoricalSource(
        run=source,
        state_sha256=digest(source / "state.json"),
        checkpoints=("initial.pt",),
    )
    donor = _config(Path("outputs/learning/donor"))
    donor = donor.model_copy(
        update={"population": donor.population.model_copy(update={"sources": (selection,)})}
    )
    ledger: dict[str, Any] = {"native": "old-engine", "members": {}}
    import_opponents(donor, ledger)
    name = "historical/old-root/initial.pt"
    assert ledger["external_opponents"][name]["root_kind"] == kind
    # Historical ledgers predate the optional v5b fields; absent fields mean zero.
    archived_layout = ledger["external_opponents"][name]["layout"]
    for field in tuple(archived_layout["observation"]):
        if field.startswith("derived_"):
            assert archived_layout["observation"].pop(field) == 0
    assert archived_layout["network"].pop("derived") is False
    evidence = Path("outputs/analysis/native.json")
    write_json(
        evidence,
        {
            "passed": True,
            "source_native_sha256": "old-engine",
            "target_native_sha256": "new-engine",
            "legacy_version": "grounded-production-context-v2",
            "target_version": "grounded-production-context-v4",
            "checked_observations": 10000,
            "matched_engine_trajectories": True,
        },
    )
    pointer = {"path": str(evidence), "sha256": digest(evidence)}
    ledger.update(
        native="new-engine",
        protocol=protocol(donor),
        population_history=[
            {
                "historical_archive": {"native_evidence": pointer},
            }
        ],
    )
    write_json(donor.output_dir / "state.json", ledger)
    archive = HistoricalArchive(
        run=donor.output_dir,
        state_sha256=digest(donor.output_dir / "state.json"),
    )
    target = donor.model_copy(
        update={"output_dir": Path("outputs/learning/target"), "agronomy": True}
    )
    state: dict[str, Any] = {"native": "new-engine", "members": {}}
    import_archive(target, state, archive)
    assert (
        state["external_opponents"][name]
        == json.loads((donor.output_dir / "state.json").read_text())["external_opponents"][name]
    )
    assert state["opponent_native_qualification"] == pointer
    assert "pfsp" not in state
    original_evidence = evidence.read_bytes()
    evidence.write_text("changed")
    with pytest.raises(ValueError, match="authenticated replay evidence"):
        import_archive(target, {"native": "new-engine", "members": {}}, archive)
    replacement = Path("outputs/analysis/repeated-native-audit.json")
    replacement.write_bytes(original_evidence)
    replacement_archive = HistoricalArchive.model_validate(
        {
            **archive.model_dump(mode="json"),
            "native_qualification": {"path": str(replacement), "sha256": digest(replacement)},
        }
    )
    refreshed: dict[str, Any] = {"native": "new-engine", "members": {}}
    import_archive(target, refreshed, replacement_archive)
    assert refreshed["external_opponents"] == state["external_opponents"]
    assert digest(donor.output_dir / "state.json") == archive.state_sha256
    replacement.write_text("changed")
    with pytest.raises(ValueError, match="authenticated replay evidence"):
        import_archive(target, {"native": "new-engine", "members": {}}, replacement_archive)
    save_policy(source / "initial.pt", actor, settings, lineage={**lineage, "kind": "wrong"})
    original["members"]["initial.pt"] = digest(source / "initial.pt")
    write_json(source / "state.json", original)
    altered = donor.model_copy(
        update={
            "population": donor.population.model_copy(
                update={
                    "sources": (
                        selection.model_copy(
                            update={"state_sha256": digest(source / "state.json")}
                        ),
                    )
                }
            )
        }
    )
    with pytest.raises(ValueError, match="historical checkpoint lineage"):
        import_opponents(altered, {"native": "old-engine", "members": {}})
