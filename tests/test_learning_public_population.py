import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from pydantic import ValidationError

from kagg_revue.artifacts.io import digest
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.population import (
    create_training_batch,
    episode_weights,
    outcomes,
    policy_rows,
)
from kagg_revue.learning.collection.public import records
from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.distributed import seed_shard
from kagg_revue.learning.optimization.settings import HistoricalPopulation
from kagg_revue.learning.recovery.population import BatchChange, changed_protocol
from kagg_revue.learning.state import protocol
from kagg_revue.opponents.settings import PublicPopulation
from kagg_revue.policy.contracts import ContractLayout


def script_config(tmp_path, monkeypatch):
    manifest_path = Path("data/external/kaggriculture-public-native-20260916/manifest.json")
    original = json.loads(manifest_path.read_text())
    record = next(row.copy() for row in original["agents"] if row["agent_id"] == "metacounter_r1")
    source = Path(record["main_path"]).read_bytes()
    monkeypatch.chdir(tmp_path)
    path = Path("data/external/test/main.py")
    path.parent.mkdir(parents=True)
    path.write_bytes(source)
    record["main_path"] = str(path)
    manifest = path.with_name("manifest.json")
    manifest.write_text(json.dumps({**original, "agents": [record]}))
    return PublicPopulation(
        manifest=manifest, sha256=digest(manifest), agents=("metacounter_r1",), fraction=0.25
    )


def test_three_population_seeds_cover_budget_once_and_balance_each_rank(tmp_path, monkeypatch):
    scripts = script_config(tmp_path, monkeypatch)
    config = Experiment(
        output_dir=Path("outputs/learning/test"),
        games=128,
        architecture="grounded-v1",
        decision_interval=1,
        population=Population(fraction=0.25),
        script_population=scripts,
    )
    shards = [seed_shard(config, 3, rank, 2) for rank in range(2)]
    full = seed_shard(config, 3, 0, 1)
    assert len(set(shards[0] + shards[1])) == 128
    assert sorted(shards[0] + shards[1]) == full
    assert shards[0][:32] + shards[1][:32] == full[:64]
    assert shards[0][32:48] + shards[1][32:48] == full[64:96]
    assert shards[0][48:] + shards[1][48:] == full[96:]
    with pytest.raises(ValidationError, match="balanced seats"):
        Experiment.model_validate({**protocol(config), "games": 12})


def test_live_scripts_and_history_keep_only_their_learned_seats(tmp_path, monkeypatch):
    config = Experiment(
        output_dir=Path("outputs/learning/test"),
        games=8,
        architecture="grounded-v1",
        decision_interval=1,
        unit_limit=2,
        population=Population(fraction=0.25),
        script_population=script_config(tmp_path, monkeypatch),
        environment={
            "boardSize": 4,
            "episodeSteps": 9,
            "turnsPerDay": 3,
            "maxMarketOrdersPerTurn": 2,
        },
    )
    settings = runtime_settings(config)
    settings = settings.model_copy(
        update={
            "ppo": settings.ppo.model_copy(
                update={
                    "history": HistoricalPopulation(checkpoint=Path("unused.pt"), fraction=0.25),
                }
            )
        }
    )
    layout = ContractLayout.resolve(settings)
    history_views = np.empty((2, layout.observation.features), np.float16)
    history_plans = np.zeros((2, layout.factors), np.int64)
    runtime = SimpleNamespace(
        policy=SimpleNamespace(layout=layout),
        host=SimpleNamespace(numpy=lambda: history_views),
        selected=SimpleNamespace(numpy=lambda: history_plans),
    )
    from kagg_revue.native import _revue_native
    from kagg_revue.opponents.public import PublicAgentRuntime

    def forbidden(*args, **kwargs):
        raise AssertionError("training must not construct a Python script opponent")

    monkeypatch.setattr(PublicAgentRuntime, "__init__", forbidden)
    batch = create_training_batch(settings, list(range(8)), runtime)
    assert isinstance(batch.scripts.groups[0][0], _revue_native.ParallelBatch)
    plans = np.zeros((12, layout.factors), np.int64)
    views = np.empty((12, layout.observation.features), np.float16)
    for _ in range(8):
        batch.observe_into(views)
        batch.advance(plans, 1)
    cash = batch.cash(8)
    np.testing.assert_array_equal(cash[:4], np.full((4, 2), 3000))
    np.testing.assert_array_equal(cash[4:6], [[3000, cash[4, 1]], [3000, cash[5, 1]]])
    np.testing.assert_array_equal(cash[6:], np.full((2, 2), 3000))
    np.testing.assert_array_equal(policy_rows(cash, 4), np.full(12, 3000))
    assert episode_weights(4, 4).sum() == 8
    panels = outcomes(cash, list(batch.opponents))
    assert {name: row["games"] for name, row in panels.items()} == {
        "self_play": 4,
        "metacounter_r1": 2,
        "historical_self_play": 2,
    }
    assert panels["metacounter_r1"]["training_trajectories"] == 2
    assert np.any(cash[4:6, 1] != 3000)


def test_public_sources_reject_modified_script_and_manifest(tmp_path, monkeypatch):
    config = script_config(tmp_path, monkeypatch)
    records(config)
    path = Path("data/external/test/main.py")
    path.write_text(path.read_text() + "# tampered\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        records(config)
    config.manifest.write_text("{}")
    with pytest.raises(ValueError, match="manifest differs"):
        records(config)


def test_population_change_preserves_budget_optimizer_controls_and_history(tmp_path, monkeypatch):
    scripts = script_config(tmp_path, monkeypatch)
    old = Experiment(
        output_dir=Path("outputs/learning/test"),
        games=128,
        architecture="grounded-v1",
        decision_interval=1,
    )
    state = {"protocol": protocol(old)}
    new = changed_protocol(state, Population(fraction=0.25), scripts)
    assert {key for key, value in protocol(new).items() if state["protocol"].get(key) != value} == {
        "population",
        "script_population",
    }
    with pytest.raises(ValueError, match="history archive"):
        changed_protocol(state, Population(fraction=0.25, capacity=4), scripts)


def test_population_change_requires_explicit_execution_to_change_gpu_count(tmp_path, monkeypatch):
    from kagg_revue.learning.execution import Execution

    scripts = script_config(tmp_path, monkeypatch)
    old = Experiment(
        output_dir=Path("outputs/learning/test"),
        games=128,
        architecture="grounded-v2",
        decision_interval=1,
        execution=Execution(devices=("cuda:0",), microbatch_rows=1440),
        population=Population(fraction=0),
    )
    state = {"protocol": protocol(old)}
    assert changed_protocol(state, old.population, scripts).execution == old.execution
    execution = Execution(devices=("cuda:0", "cuda:1"), microbatch_rows=2880)
    new = changed_protocol(state, old.population, scripts, execution=execution)
    assert new.execution == execution
    assert {key for key, value in protocol(new).items() if state["protocol"].get(key) != value} == {
        "execution",
        "script_population",
    }
    assert state["protocol"] == protocol(old)
    full = seed_shard(new, 2392, 0, 1)
    shards = [seed_shard(new, 2392, rank, 2) for rank in range(2)]
    assert sorted(shards[0] + shards[1]) == full
    assert len(set(shards[0] + shards[1])) == old.games


def test_population_change_can_read_retired_boatlee_without_reactivating_it(tmp_path, monkeypatch):
    scripts = script_config(tmp_path, monkeypatch)
    old = Experiment(
        output_dir=Path("outputs/learning/test"),
        games=128,
        architecture="grounded-v2",
        decision_interval=1,
        population=Population(fraction=0),
        script_population=scripts,
    )
    previous = protocol(old)
    previous["script_population"]["agents"] = ["boatlee_v29"]
    with pytest.raises(ValidationError, match="retired opponents"):
        Experiment.model_validate(previous)
    new = changed_protocol({"protocol": previous}, old.population, scripts)
    assert protocol(new) == protocol(old)
    assert previous["script_population"]["agents"] == ["boatlee_v29"]


def test_shop_router_authenticates_every_companion_before_import(tmp_path, monkeypatch):
    from kagg_revue.opponents.public import load_public_agent_manifest, resolve_public_agent_path
    from kagg_revue.opponents.registry import trusted_runtime_identity

    manifest = Path("data/external/kaggriculture-shop-router-0908-20260908/manifest.json")
    record = load_public_agent_manifest(manifest).by_id()["shop_router_0908"]
    source = record.main_path
    content = {name: (source.parent / name).read_bytes() for name in [source.name, *record.files]}
    monkeypatch.chdir(tmp_path)
    source.parent.mkdir(parents=True)
    for name, payload in content.items():
        (source.parent / name).write_bytes(payload)
    assert resolve_public_agent_path(record, tmp_path) == tmp_path / source
    assert trusted_runtime_identity(record) is None  # Retired from new training.
    for name in record.files:
        path = source.parent / name
        path.write_bytes(content[name] + b" ")
        with pytest.raises(ValueError, match="hash mismatch"):
            resolve_public_agent_path(record, tmp_path)
        path.write_bytes(content[name])


def test_add_scripts_with_zero_history_preserves_model_and_publishes_exact_mix(
    tmp_path, monkeypatch
):
    from kagg_revue.learning.progress import publish

    scripts = script_config(tmp_path, monkeypatch).model_copy(
        update={
            "agents": ("ahmed_v45", "farming_v4_0914", "metacounter_r1", "rayk_v38_low_pressure"),
            "fraction": 0.5,
        }
    )
    old = Experiment(
        output_dir=Path("outputs/learning/test"),
        games=128,
        population=Population(fraction=0),
        architecture="grounded-v2",
        decision_interval=1,
    )
    state = {"protocol": protocol(old), "run_id": "fixture", "completed_update": 105, "records": []}
    new = changed_protocol(state, old.population, scripts)
    assert {key for key, value in protocol(new).items() if state["protocol"].get(key) != value} == {
        "script_population"
    }
    publish(new, state, "reinforcement_learning")
    live = json.loads((new.output_dir / "learning-progress.json").read_text())
    assert live["population_games"] == {
        "self_play": 64,
        "ahmed_v45": 16,
        "farming_v4_0914": 16,
        "metacounter_r1": 16,
        "rayk_v38_low_pressure": 16,
    }
    assert live["selfplay_fraction"] == live["script_fraction"] == 0.5
    assert live["history_fraction"] == 0
    assert not live["pure_selfplay"]


def test_batch_resize_preserves_mixture_and_reserves_disjoint_seeds(tmp_path, monkeypatch):
    scripts = script_config(tmp_path, monkeypatch)
    old = Experiment(
        output_dir=Path("outputs/learning/test"),
        games=128,
        updates=100000,
        train_seed=600000000,
        architecture="grounded-v1",
        decision_interval=1,
        population=Population(fraction=0.25),
        script_population=scripts,
    )
    state = {"protocol": protocol(old)}
    batch = BatchChange(games=512, train_seed=800000000)
    new = changed_protocol(state, old.population, scripts, batch)
    assert {key for key, value in protocol(new).items() if state["protocol"].get(key) != value} == {
        "games",
        "train_seed",
    }
    shards = [seed_shard(new, 459, rank, 2) for rank in range(2)]
    assert len(set(shards[0] + shards[1])) == 512
    assert max(seed_shard(old, 458, 0, 1)) < min(shards[0] + shards[1])
    with pytest.raises(ValueError, match="fresh seed allocation"):
        changed_protocol(
            state, old.population, scripts, BatchChange(games=512, train_seed=old.train_seed)
        )
    with pytest.raises(ValueError, match="preserve opponent composition"):
        changed_protocol(state, Population(fraction=0.5), scripts, batch)


def test_active_catalog_authenticates_new_sources_and_rejects_retired_opponents():
    from kagg_revue.opponents.native_batch import create_native_opponent_session
    from kagg_revue.opponents.portfolios.catalog import ACTIVE_IDS
    from kagg_revue.opponents.public import load_public_agent_manifest
    from kagg_revue.opponents.registry import trusted_runtime_identity

    manifest = Path("data/external/kaggriculture-shop-router-0908-20260908/manifest.json")
    records = load_public_agent_manifest(manifest).by_id()
    current = Path("data/external/kaggriculture-shop-router-0909-20260909/manifest.json")
    records.update(load_public_agent_manifest(current).by_id())
    records.update(
        load_public_agent_manifest(
            Path("data/external/kaggriculture-public-native-20260914/manifest.json")
        ).by_id()
    )
    records.update(
        load_public_agent_manifest(
            Path("data/external/kaggriculture-public-native-20260914-v2/manifest.json")
        ).by_id()
    )
    records.update(
        load_public_agent_manifest(
            Path("data/external/kaggriculture-public-native-20260916/manifest.json")
        ).by_id()
    )
    for name in ACTIVE_IDS:
        assert trusted_runtime_identity(records[name]) is not None
        changed = records[name].model_copy(update={"sha256": "0" * 64})
        assert trusted_runtime_identity(changed) is None
    for name in (
        "router_95", "farming_v4", "kaito_v58", "shop_router_0908", "shop_router_0909",
        "ahmed_v41", "ahmed_v42", "farming_v4_0912",
    ):
        assert trusted_runtime_identity(records[name]) is None
        values = dict(manifest=manifest, sha256=digest(manifest), agents=(name,), fraction=0.25)
        with pytest.raises(ValidationError, match="retired opponents"):
            PublicPopulation.model_validate(values)
        assert PublicPopulation.model_validate(values, context={"archived_population": True})
    for name in ("ahmed_v41", "ahmed_v42", "farming_v4_0912"):
        with pytest.raises(ValueError, match="inactive native opponent"):
            create_native_opponent_session(name, 10)
    for name in ("kaito_v39", "kaito_v48", "mugundh_v21", "boatlee_v21", "boatlee_v29"):
        assert trusted_runtime_identity(records[name]) is None
        with pytest.raises(ValueError, match="inactive native opponent"):
            create_native_opponent_session(name, 10)
        with pytest.raises(ValidationError):
            PublicPopulation(
                manifest=manifest, sha256=digest(manifest), agents=(name,), fraction=0.25
            )


def test_native_numeric_batch_rejects_shared_mutable_session_before_stepping():
    from kagg_revue.native import _revue_native as native
    from kagg_revue.opponents.native_batch import create_native_opponent_session

    engines = [native.Engine(seed, {}) for seed in (3, 4)]
    session = create_native_opponent_session("router_95", 10)
    tokens = np.tile([0, 44], (2, 2, 1)).astype(np.int64)
    with pytest.raises(ValueError, match="independent engines and opponent sessions"):
        native.engine_step_native_opponent_batch(
            engines,
            np.array([0, 1], np.int64),
            [session, session],
            tokens,
            np.zeros_like(tokens),
            np.full((2, 2), 2, np.int64),
            np.ones((2, 2), np.int64),
            2,
        )
    assert all(engine.step_index == 0 for engine in engines)
