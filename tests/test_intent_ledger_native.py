import numpy as np
import pytest

from kagg_revue.policy.tasks.contract import TaskOperation, UnitTask
from kagg_revue.rl.intents.controller import IntentTurnPlan
from kagg_revue.teacher.intents import ProgramIntentPlan, encode_native_intent_plans


def _candidate_index(
    observation: dict[str, object],
    *,
    kind: int,
    target: int | None = None,
    item: int | None = None,
    maintenance: int | None = None,
    priority: int | None = None,
    quantity: int | None = None,
    unit: int | None = None,
    operation: int | None = None,
) -> int:
    fields = np.asarray(observation["candidate_fields"])
    selected = fields[:, 0] == kind
    if target is not None:
        selected &= fields[:, 1] == target
    if item is not None:
        selected &= fields[:, 2] == item
    if maintenance is not None:
        selected &= fields[:, 3] == maintenance
    if priority is not None:
        selected &= fields[:, 6] == priority
    if quantity is not None:
        selected &= fields[:, 7] == quantity
    if unit is not None:
        selected &= fields[:, 8] == unit
    if operation is not None:
        selected &= fields[:, 9] == operation
    matches = np.flatnonzero(selected)
    assert len(matches) == 1
    return int(matches[0])


def test_intent_transaction_is_canonical_and_market_freezes_ledger() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {"boardSize": 2, "episodeSteps": 12, "turnsPerDay": 4}
    engine = native.Engine(7, configuration)
    session = native.IntentLedgerSession(configuration)
    spec = native.intent_ledger_spec()
    choices = spec["choice_kinds"]

    root = session.observe(engine, 0)
    ids = np.asarray(root["canonical_id"])
    assert len(ids) == len(np.unique(ids))
    session.select(_candidate_index(root, kind=choices["MARKET_BUY_SEED"], item=1))
    quantity = session.observe(engine, 0)
    session.select(
        _candidate_index(
            quantity,
            kind=choices["SELECT_MARKET_QUANTITY"],
            item=1,
            quantity=1,
        )
    )
    frozen = session.observe(engine, 0)
    kinds = set(np.asarray(frozen["candidate_fields"])[:, 0].tolist())
    assert choices["COMMIT"] in kinds
    assert choices["BEGIN_ASSET"] not in kinds
    assert np.asarray(frozen["market_prefix"]).tolist() == [[0, 0, 1]]


def test_intent_market_skip_preserves_settlement_slot() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 12,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 3,
    }
    engine = native.Engine(9, configuration)
    session = native.IntentLedgerSession(configuration)
    choices = native.intent_ledger_spec()["choice_kinds"]

    root = session.observe(engine, 0)
    session.select(_candidate_index(root, kind=choices["MARKET_SKIP_SLOT"]))
    after_skip = session.observe(engine, 0)
    assert np.asarray(after_skip["market_prefix"]).tolist() == [[6, -1, 0]]
    session.select(
        _candidate_index(
            after_skip,
            kind=choices["MARKET_BUY_SEED"],
            item=1,
        )
    )
    quantity = session.observe(engine, 0)
    session.select(
        _candidate_index(
            quantity,
            kind=choices["SELECT_MARKET_QUANTITY"],
            item=1,
            quantity=1,
        )
    )
    final_root = session.observe(engine, 0)
    assert np.asarray(final_root["market_prefix"]).tolist() == [
        [6, -1, 0],
        [0, 0, 1],
    ]
    session.select(_candidate_index(final_root, kind=choices["COMMIT"]))
    assert session.action(engine, 0)["market"] == [[], ["BUY_SEED", "WHEAT", 1]]


def test_asset_contract_persists_and_native_scheduler_executes_prerequisites() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {"boardSize": 2, "episodeSteps": 12, "turnsPerDay": 4}
    engine = native.Engine(11, configuration)
    session = native.IntentLedgerSession(configuration)
    spec = native.intent_ledger_spec()
    choices = spec["choice_kinds"]
    target = 0

    root = session.observe(engine, 0)
    session.select(_candidate_index(root, kind=choices["BEGIN_ASSET"]))
    targets = session.observe(engine, 0)
    session.select(_candidate_index(targets, kind=choices["SELECT_TARGET"], target=target))
    profiles = session.observe(engine, 0)
    session.select(
        _candidate_index(
            profiles,
            kind=choices["SET_ASSET"],
            target=target,
            item=1,
            maintenance=2,
            priority=2,
        )
    )
    root = session.observe(engine, 0)
    session.select(_candidate_index(root, kind=choices["MARKET_BUY_SEED"], item=1))
    quantities = session.observe(engine, 0)
    session.select(
        _candidate_index(
            quantities,
            kind=choices["SELECT_MARKET_QUANTITY"],
            item=1,
            quantity=1,
        )
    )
    root = session.observe(engine, 0)
    session.select(_candidate_index(root, kind=choices["COMMIT"]))
    first = session.action(engine, 0)
    assert first["farmer"] == ["PASS"]
    assert first["market"] == [["BUY_SEED", "WHEAT", 1]]
    engine.step(first, {})

    second_observation = session.observe(engine, 0)
    assert np.asarray(second_observation["ledger"])[target, 0] == 1
    session.select(_candidate_index(second_observation, kind=choices["COMMIT"]))
    second = session.action(engine, 0)
    assert second["farmer"] == ["PLANT", "WHEAT"]
    engine.step(second, {})

    third_observation = session.observe(engine, 0)
    assert np.asarray(third_observation["ledger"])[target, 7] == 1
    session.select(_candidate_index(third_observation, kind=choices["COMMIT"]))
    third = session.action(engine, 0)
    assert third["farmer"] == ["WATER"]


def test_intent_native_batch_boundary_emits_fixed_width_tensors() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {"boardSize": 2, "episodeSteps": 8}
    engines = [native.Engine(seed, configuration) for seed in (13, 17)]
    sessions = [native.IntentLedgerSession(configuration) for _ in engines]
    players = np.asarray([0, 1], dtype=np.int64)
    observations = native.intent_ledger_observations_batch(sessions, engines, players, workers=2)

    candidate_count = observations["candidate_fields"].shape[1]
    assert observations["candidate_fields"].shape == (2, candidate_count, 10)
    assert observations["candidate_features"].shape == (2, candidate_count, 12)
    assert observations["ledger"].shape == (2, 4, 8)
    assert observations["status"].shape == (2, 4, 4)
    assert observations["work_orders"].shape == (2, 0, 9)
    assert observations["work_mask"].shape == (2, 0)
    np.testing.assert_array_equal(
        observations["candidate_counts"], [candidate_count, candidate_count]
    )

    native.intent_ledger_select_batch(
        sessions,
        np.zeros(2, dtype=np.int64),
        np.ones(2, dtype=np.int64),
        workers=2,
    )
    actions = native.intent_ledger_actions_batch(sessions, engines, players, workers=2)
    assert actions["tokens"].shape == (2, 1)
    np.testing.assert_array_equal(actions["decision_counts"], [1, 1])
    np.testing.assert_array_equal(actions["unit_counts"], [1, 1])

    batch_sessions = [native.IntentLedgerSession(configuration) for _ in engines]
    native_batch = native.IntentLedgerBatch(batch_sessions, engines, players, workers=2)
    active = np.asarray([1, 0], dtype=np.int64)
    batched = native_batch.observe(active, maximum_steps=2)
    np.testing.assert_array_equal(batched["candidate_counts"], [candidate_count, candidate_count])
    phases = native_batch.select(active, np.zeros(2, dtype=np.int64))
    done_phase = native.intent_ledger_spec()["phases"]["DONE"]
    np.testing.assert_array_equal(phases, [done_phase, done_phase])
    native_batch.reset_transaction()
    assert native_batch.batch_size == 2

    recorded_sessions = [native.IntentLedgerSession(configuration) for _ in engines]
    recorded_batch = native.IntentLedgerBatch(recorded_sessions, engines, players, workers=2)
    recorded_batch.observe(active, maximum_steps=2)
    selected = np.zeros(2, dtype=np.int64)
    recorded_batch.record_prepared_indexed(selected, behavior_offset=7, turn_index=0)
    recorded_batch.select(active, selected)
    buckets = recorded_batch.export_rollout_buckets()
    assert len(buckets) == 1
    np.testing.assert_array_equal(buckets[0]["behavior_index"], [8, 7])
    np.testing.assert_array_equal(buckets[0]["episode_index"], [0, 1])
    assert buckets[0]["candidate_fields"].shape[:2] == (2, candidate_count)

    replay_sessions = [native.IntentLedgerSession(configuration) for _ in engines]
    replay_batch = native.IntentLedgerBatch(replay_sessions, engines, players, workers=2)
    replayed = replay_batch.observe(active, maximum_steps=2)
    auxiliary = replay_batch.device_auxiliary()
    selected_fields = np.asarray(replayed["candidate_fields"])[:, :1].copy()
    forced = replay_batch.replay_transaction(
        np.zeros((2, 1), dtype=np.int64),
        selected_fields,
        np.ones(2, dtype=np.int64),
        behavior_offset=11,
        turn_index=0,
        maximum_steps=2,
    )
    replay_buckets = replay_batch.export_rollout_buckets()
    assert forced == 0
    assert np.asarray(auxiliary["inactive_status"]).shape == (2, 4, 2)
    assert np.asarray(auxiliary["asset_risk"]).shape == (2, 4)
    np.testing.assert_array_equal(replay_buckets[0]["behavior_index"], [11, 12])


def test_unit_bound_fetch_compiles_one_bulk_pickup_and_reconciles() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 12,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 10,
    }
    engine = native.Engine(19, configuration)
    session = native.IntentLedgerSession(configuration)
    spec = native.intent_ledger_spec()
    choices = spec["choice_kinds"]

    root = session.observe(engine, 0)
    session.select(_candidate_index(root, kind=choices["MARKET_BUY_PRODUCT"], item=1))
    quantities = session.observe(engine, 0)
    session.select(
        _candidate_index(
            quantities,
            kind=choices["SELECT_MARKET_QUANTITY"],
            item=1,
            quantity=3,
        )
    )
    root = session.observe(engine, 0)
    session.select(_candidate_index(root, kind=choices["COMMIT"]))
    engine.step(session.action(engine, 0), {})

    root = session.observe(engine, 0)
    session.select(_candidate_index(root, kind=choices["BEGIN_FETCH"]))
    units = session.observe(engine, 0)
    session.select(
        _candidate_index(
            units,
            kind=choices["SELECT_FETCH_UNIT"],
            unit=1,
        )
    )
    items = session.observe(engine, 0)
    session.select(
        _candidate_index(
            items,
            kind=choices["SELECT_FETCH_ITEM"],
            item=1,
            unit=1,
        )
    )
    quantities = session.observe(engine, 0)
    session.select(
        _candidate_index(
            quantities,
            kind=choices["SET_FETCH"],
            item=1,
            quantity=3,
            unit=1,
        )
    )
    pending = session.observe(engine, 0)
    assert np.asarray(pending["work_orders"]).tolist() == [
        [spec["work_kinds"]["FETCH"], -1, 1, 3, 2, 2, 0, 11, 1]
    ]
    session.select(_candidate_index(pending, kind=choices["COMMIT"]))
    assert session.action(engine, 0)["farmer"] == ["PICKUP", "WHEAT", 3]
    engine.step(session.action(engine, 0), {})

    reconciled = session.observe(engine, 0)
    assert np.asarray(reconciled["work_orders"]).shape == (0, 9)
    assert engine.observation(0)["private"]["inventories"][0]["WHEAT"] == 3


def test_unit_directive_preserves_actor_operation_and_quantity() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 12,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 10,
    }
    engine = native.Engine(23, configuration)
    session = native.IntentLedgerSession(configuration)
    spec = native.intent_ledger_spec()
    choices = spec["choice_kinds"]
    pickup = spec["directive_operations"]["PICKUP"]

    root = session.observe(engine, 0)
    session.select(_candidate_index(root, kind=choices["MARKET_BUY_PRODUCT"], item=1))
    quantities = session.observe(engine, 0)
    session.select(
        _candidate_index(
            quantities,
            kind=choices["SELECT_MARKET_QUANTITY"],
            item=1,
            quantity=3,
        )
    )
    root = session.observe(engine, 0)
    session.select(_candidate_index(root, kind=choices["COMMIT"]))
    engine.step(session.action(engine, 0), {})

    root = session.observe(engine, 0)
    session.select(_candidate_index(root, kind=choices["BEGIN_DIRECTIVE"]))
    units = session.observe(engine, 0)
    session.select(_candidate_index(units, kind=choices["SELECT_DIRECTIVE_UNIT"], unit=1))
    operations = session.observe(engine, 0)
    session.select(
        _candidate_index(
            operations,
            kind=choices["SELECT_DIRECTIVE_OPERATION"],
            unit=1,
            operation=pickup,
        )
    )
    targets = session.observe(engine, 0)
    session.select(
        _candidate_index(
            targets,
            kind=choices["SELECT_DIRECTIVE_TARGET"],
            target=0,
            unit=1,
            operation=pickup,
        )
    )
    items = session.observe(engine, 0)
    session.select(
        _candidate_index(
            items,
            kind=choices["SELECT_DIRECTIVE_ITEM"],
            target=0,
            item=1,
            unit=1,
            operation=pickup,
        )
    )
    quantities = session.observe(engine, 0)
    session.select(
        _candidate_index(
            quantities,
            kind=choices["SET_DIRECTIVE"],
            target=0,
            item=1,
            quantity=3,
            unit=1,
            operation=pickup,
        )
    )
    pending = session.observe(engine, 0)
    assert np.asarray(pending["work_orders"])[0, [0, 1, 2, 3, 8]].tolist() == [
        spec["work_kinds"]["DIRECTIVE_PICKUP"],
        0,
        1,
        3,
        1,
    ]
    session.select(_candidate_index(pending, kind=choices["COMMIT"]))
    assert session.action(engine, 0)["farmer"] == ["PICKUP", "WHEAT", 3]


def test_native_teacher_batch_records_dynamic_canonical_choices() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 12,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 2,
    }
    engines = [native.Engine(29, configuration), native.Engine(31, configuration)]
    sessions = [native.IntentLedgerSession(configuration) for _ in engines]
    players = np.asarray([0, 1], dtype=np.int64)
    batch = native.IntentLedgerBatch(sessions, engines, players, workers=2)
    wait = UnitTask(
        operation=TaskOperation.WAIT,
        target=None,
        argument=None,
        quantity=0,
        earliest_start=1,
        deadline=1,
    )
    plans = [
        ProgramIntentPlan(
            intent=IntentTurnPlan(
                action={"market": [["SELL", "WHEAT", 1]]},
                active_tasks=(wait,),
            ),
            tasks=(wait,),
            route_id="synthetic",
            first_event_day=None,
        )
        for _ in engines
    ]
    encoded = encode_native_intent_plans(
        plans,
        native.intent_ledger_spec(),
        board_size=2,
        unit_limit=2,
        maximum_market_orders=2,
    )

    result = batch.apply_teacher_plans(*encoded.arguments(), 0, 8)
    np.testing.assert_array_equal(result["decision_counts"], [6, 6])
    np.testing.assert_array_equal(result["omitted_sell_orders"], [0, 0])
    np.testing.assert_array_equal(result["replaced_unavailable_sell_slots"], [1, 1])
    compiled = native.intent_ledger_actions_batch(sessions, engines, players, workers=2)
    assert native.decode_action_tokens(
        compiled["tokens"][0],
        compiled["quantities"][0],
        int(compiled["decision_counts"][0]),
        int(compiled["unit_counts"][0]),
        2,
    ) == {"farmer": ["PASS"], "hands": [], "market": [[]]}
    buckets = batch.export_rollout_buckets()
    assert sum(len(bucket["selected"]) for bucket in buckets) == 12
    assert all(np.asarray(bucket["selected_canonical_id"]).dtype == np.uint64 for bucket in buckets)
