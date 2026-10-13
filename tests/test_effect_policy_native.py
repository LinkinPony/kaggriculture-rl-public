import numpy as np
import pytest

from kagg_revue.bc.effects.correction_observer import (
    effect_candidate_canonical_id,
)


def _candidate(
    observation: dict[str, object],
    kind: int,
    *,
    target: int | None = None,
    item: int | None = None,
    quantity: int | None = None,
    unit: int | None = None,
) -> int:
    fields = np.asarray(observation["candidate_fields"])
    matches = fields[:, 0] == kind
    if target is not None:
        matches &= fields[:, 1] == target
    if item is not None:
        matches &= fields[:, 2] == item
    if quantity is not None:
        matches &= fields[:, 3] == quantity
    if unit is not None:
        matches &= fields[:, 5] == unit + 1
    indices = np.flatnonzero(matches & np.asarray(observation["candidate_mask"]))
    if unit is None and len(indices) > 1:
        indices = indices[fields[indices, 5] == 0]
    assert len(indices) == 1
    return int(indices[0])


def _stop(session: object, engine: object, player: int, stop: int) -> None:
    observation = session.observe(engine, player)
    session.select(engine, player, _candidate(observation, stop))


def test_effect_candidates_are_complete_tuples_with_exact_market_prefix() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 12,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 3,
    }
    engine = native.Engine(7, configuration)
    session = native.AtomicEffectSession(configuration, 4, 16)
    spec = native.effect_policy_spec()
    kinds = spec["request_kinds"]

    work = session.observe(engine, 0)
    assert work["phase_name"] == "WORK"
    assert len(np.unique(np.asarray(work["canonical_id"]))) == work["candidate_count"]
    session.select(engine, 0, _candidate(work, kinds["STOP"]))

    market = session.observe(engine, 0)
    buy_two = _candidate(market, kinds["BUY_SEED"], item=1, quantity=2)
    session.select(engine, 0, buy_two)
    projected = session.observe(engine, 0)
    np.testing.assert_array_equal(projected["market_prefix"], [[kinds["BUY_SEED"], -1, 1, 2, 0, 0]])
    session.select(engine, 0, _candidate(projected, kinds["STOP"]))
    assert session.action(engine, 0)["market"] == [["BUY_SEED", "WHEAT", 2]]


def test_effect_correction_reconstructs_native_candidate_ids() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 12,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 3,
    }
    engine = native.Engine(71, configuration)
    session = native.AtomicEffectSession(configuration, 4, 16)
    kinds = native.effect_policy_spec()["request_kinds"]
    work = session.observe(engine, 0)
    work_fields = np.asarray(work["candidate_fields"], dtype=np.int64)
    work_ids = np.asarray(work["canonical_id"], dtype=np.uint64)
    reconstructed_work = np.asarray(
        [
            effect_candidate_canonical_id(
                fields,
                phase=0,
                turn=0,
                market_prefix=np.empty((0, 6), dtype=np.int64),
            )
            for fields in work_fields
        ],
        dtype=np.uint64,
    )
    np.testing.assert_array_equal(reconstructed_work, work_ids)

    session.select(engine, 0, _candidate(work, kinds["STOP"]))
    market = session.observe(engine, 0)
    session.select(
        engine,
        0,
        _candidate(market, kinds["BUY_SEED"], item=1, quantity=2),
    )
    projected = session.observe(engine, 0)
    market_fields = np.asarray(projected["candidate_fields"], dtype=np.int64)
    market_ids = np.asarray(projected["canonical_id"], dtype=np.uint64)
    market_prefix = np.asarray(projected["market_prefix"], dtype=np.int64)
    reconstructed_market = np.asarray(
        [
            effect_candidate_canonical_id(
                fields,
                phase=1,
                turn=0,
                market_prefix=market_prefix,
            )
            for fields in market_fields
        ],
        dtype=np.uint64,
    )
    np.testing.assert_array_equal(reconstructed_market, market_ids)


def test_effect_market_skip_preserves_rejected_raw_slot() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 12,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 3,
    }
    engine = native.Engine(8, configuration)
    session = native.AtomicEffectSession(configuration, 4, 16)
    kinds = native.effect_policy_spec()["request_kinds"]

    _stop(session, engine, 0, kinds["STOP"])
    market = session.observe(engine, 0)
    session.select(engine, 0, _candidate(market, kinds["SKIP_MARKET_SLOT"]))
    market = session.observe(engine, 0)
    session.select(
        engine,
        0,
        _candidate(market, kinds["BUY_SEED"], item=1, quantity=2),
    )
    _stop(session, engine, 0, kinds["STOP"])
    assert session.action(engine, 0)["market"] == [
        [],
        ["BUY_SEED", "WHEAT", 2],
    ]


def test_effect_exact_transfer_respects_unit_execution_prefix() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 12,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 3,
    }
    engine = native.Engine(9, configuration)
    engine.step(
        {
            "farmer": ["PASS"],
            "market": [["BUY_PRODUCT", "WHEAT", 3], ["HIRE"]],
        },
        {},
    )
    engine.step({"farmer": ["PICKUP", "WHEAT", 3], "hands": [["PASS"]]}, {})

    session = native.AtomicEffectSession(configuration, 4, 16)
    kinds = native.effect_policy_spec()["request_kinds"]
    work = session.observe(engine, 0)
    session.select(
        engine,
        0,
        _candidate(work, kinds["UNLOAD"], item=1, quantity=2, unit=0),
    )
    work = session.observe(engine, 0)
    session.select(
        engine,
        0,
        _candidate(work, kinds["LOAD"], item=1, quantity=2, unit=1),
    )
    _stop(session, engine, 0, kinds["STOP"])
    assert session.action(engine, 0) == {
        "farmer": ["PLACE", "WHEAT", 2],
        "hands": [["PICKUP", "WHEAT", 2]],
        "market": [],
    }


def test_effect_pickup_can_enable_a_later_unit_drop() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 12,
        "turnsPerDay": 12,
        "maxMarketOrdersPerTurn": 3,
        "shedCapacity": 3,
    }
    engine = native.Engine(12, configuration)
    engine.step(
        {
            "farmer": ["PASS"],
            "market": [["BUY_PRODUCT", "WHEAT", 3], ["HIRE"]],
        },
        {},
    )
    engine.step(
        {"farmer": ["PASS"], "hands": [["PICKUP", "WHEAT", 1]]},
        {},
    )
    engine.step(
        {
            "farmer": ["PASS"],
            "hands": [["PASS"]],
            "market": [["BUY_PRODUCT", "WHEAT", 1]],
        },
        {},
    )

    session = native.AtomicEffectSession(configuration, 4, 16)
    kinds = native.effect_policy_spec()["request_kinds"]
    work = session.observe(engine, 0)
    fields = np.asarray(work["candidate_fields"])
    mask = np.asarray(work["candidate_mask"])
    hand_bank = (
        (fields[:, 0] == kinds["BANK"])
        & (fields[:, 5] == 2)
    )
    assert int(hand_bank.sum()) == 1
    assert not bool(mask[hand_bank][0])
    session.select(
        engine,
        0,
        _candidate(work, kinds["LOAD"], item=1, quantity=1, unit=0),
    )
    work = session.observe(engine, 0)
    session.select(engine, 0, _candidate(work, kinds["BANK"], unit=1))
    _stop(session, engine, 0, kinds["STOP"])
    assert session.action(engine, 0) == {
        "farmer": ["PICKUP", "WHEAT", 1],
        "hands": [["DROP"]],
        "market": [],
    }


def test_effect_work_cannot_cross_the_end_of_day() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 4,
        "episodeSteps": 30,
        "turnsPerDay": 4,
        "maxMarketOrdersPerTurn": 3,
    }
    engine = native.Engine(10, configuration)
    for _ in range(3):
        engine.step({}, {})
    session = native.AtomicEffectSession(configuration, 4, 16)
    kinds = native.effect_policy_spec()["request_kinds"]
    work = session.observe(engine, 0)
    fields = np.asarray(work["candidate_fields"])
    mask = np.asarray(work["candidate_mask"])
    long_stage = mask & (fields[:, 0] == kinds["STAGE"]) & (fields[:, 1] == 15)
    assert not bool(long_stage.any())


def test_effect_job_persists_only_until_requested_effect_and_never_adds_water() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 4,
        "episodeSteps": 30,
        "turnsPerDay": 24,
        "maxMarketOrdersPerTurn": 3,
    }
    engine = native.Engine(11, configuration)
    session = native.AtomicEffectSession(configuration, 4, 16)
    kinds = native.effect_policy_spec()["request_kinds"]

    _stop(session, engine, 0, kinds["STOP"])
    market = session.observe(engine, 0)
    session.select(
        engine,
        0,
        _candidate(market, kinds["BUY_SEED"], item=1, quantity=1),
    )
    _stop(session, engine, 0, kinds["STOP"])
    engine.step(session.action(engine, 0), {})

    work = session.observe(engine, 0)
    session.select(engine, 0, _candidate(work, kinds["PLANT"], target=0, item=1))
    _stop(session, engine, 0, kinds["STOP"])
    first = session.action(engine, 0)
    assert first["farmer"] in (["NORTH"], ["WEST"])
    engine.step(first, {})

    while True:
        work = session.observe(engine, 0)
        assert np.asarray(work["jobs"]).shape[0] == 1
        assert np.any(np.asarray(work["candidate_fields"])[:, 0] == kinds["CANCEL"])
        _stop(session, engine, 0, kinds["STOP"])
        _stop(session, engine, 0, kinds["STOP"])
        action = session.action(engine, 0)
        engine.step(action, {})
        if action["farmer"] == ["PLANT", "WHEAT"]:
            break

    work = session.observe(engine, 0)
    assert np.asarray(work["jobs"]).shape[0] == 0
    assert _candidate(work, kinds["WATER"], target=0) >= 0
    _stop(session, engine, 0, kinds["STOP"])
    _stop(session, engine, 0, kinds["STOP"])
    assert session.action(engine, 0)["farmer"] == ["PASS"]


def test_feed_compiler_adds_only_the_required_pickup() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 20,
        "turnsPerDay": 24,
        "maxMarketOrdersPerTurn": 4,
    }
    engine = native.Engine(13, configuration)
    engine.step(
        {
            "farmer": ["BUILD_COOP"],
            "market": [
                ["BUY_ANIMAL", "GOOSE", 1],
                ["BUY_PRODUCT", "WHEAT", 1],
            ],
        },
        {},
    )
    engine.step({"farmer": ["PICKUP", "GOOSE", 1]}, {})
    engine.step({"farmer": ["PLACE", "GOOSE", 1]}, {})

    session = native.AtomicEffectSession(configuration, 4, 16)
    kinds = native.effect_policy_spec()["request_kinds"]
    work = session.observe(engine, 0)
    session.select(engine, 0, _candidate(work, kinds["FEED"], target=0))
    _stop(session, engine, 0, kinds["STOP"])
    pickup = session.action(engine, 0)
    assert pickup["farmer"] == ["PICKUP", "WHEAT", 1]
    engine.step(pickup, {})

    _stop(session, engine, 0, kinds["STOP"])
    _stop(session, engine, 0, kinds["STOP"])
    effect = session.action(engine, 0)
    assert effect["farmer"] == ["FEED"]
    assert effect["market"] == []


def test_effect_native_batch_keeps_parallel_rows_aligned() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {"boardSize": 2, "episodeSteps": 8}
    engines = [native.Engine(seed, configuration) for seed in (17, 19)]
    sessions = [native.AtomicEffectSession(configuration, 4, 8) for _ in engines]
    players = np.asarray([0, 1], dtype=np.int64)
    observed = native.effect_policy_observations_batch(
        sessions, engines, players, workers=2
    )
    assert observed["candidate_fields"].shape[:2] == (2, int(observed["candidate_counts"][0]))
    np.testing.assert_array_equal(observed["phase"], [0, 0])

    selected = np.zeros(2, dtype=np.int64)
    active = np.ones(2, dtype=np.int64)
    phases = native.effect_policy_select_batch(
        sessions, engines, players, selected, active, workers=2
    )
    np.testing.assert_array_equal(phases, [1, 1])
    observed = native.effect_policy_observations_batch(
        sessions, engines, players, workers=2
    )
    phases = native.effect_policy_select_batch(
        sessions, engines, players, selected, active, workers=2
    )
    np.testing.assert_array_equal(phases, [2, 2])
    actions = native.effect_policy_actions_batch(
        sessions, engines, players, workers=2
    )
    np.testing.assert_array_equal(actions["decision_counts"], [1, 1])
    np.testing.assert_array_equal(actions["unit_counts"], [1, 1])


def test_ranked_work_set_reuses_one_static_candidate_surface() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {"boardSize": 4, "episodeSteps": 12}
    engine = native.Engine(23, configuration)
    engine.step({"farmer": ["PASS"], "market": [["HIRE"]]}, {})
    session = native.AtomicEffectSession(configuration, 4, 8)
    kinds = native.effect_policy_spec()["request_kinds"]

    first = session.observe(engine, 0)
    assert first["work_limit"] == 2
    stage = _candidate(first, kinds["STAGE"], target=0)
    session.select(engine, 0, stage)
    second = session.observe(engine, 0)
    assert second["phase_name"] == "WORK"
    np.testing.assert_array_equal(first["candidate_fields"], second["candidate_fields"])
    np.testing.assert_array_equal(first["candidate_features"], second["candidate_features"])
    assert not bool(np.asarray(second["candidate_mask"])[stage])


def test_effect_batch_seals_factor_tape_with_one_turn_value() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 8,
        "maxMarketOrdersPerTurn": 2,
    }
    engines = [native.Engine(seed, configuration) for seed in (31, 37)]
    sessions = [native.AtomicEffectSession(configuration, 4, 8) for _ in engines]
    players = np.asarray([0, 1], dtype=np.int64)
    batch = native.AtomicEffectBatch(sessions, engines, players, workers=2)
    active = np.arange(2, dtype=np.int64)
    batch.reset_transaction()

    work = batch.observe(active)
    phases = batch.advance(
        np.zeros(2, dtype=np.int64),
        np.asarray([-0.4, -0.5], dtype=np.float32),
        np.asarray([0.2, -0.1], dtype=np.float32),
        turn_index=0,
    )
    np.testing.assert_array_equal(phases, [1, 1])
    market = batch.observe(active)
    phases = batch.advance(
        np.zeros(2, dtype=np.int64),
        np.asarray([-0.2, -0.3], dtype=np.float32),
        np.asarray([0.2, -0.1], dtype=np.float32),
        turn_index=0,
    )
    np.testing.assert_array_equal(phases, [2, 2])
    assert np.asarray(work["phase"]).tolist() == [0, 0]
    assert np.asarray(market["phase"]).tolist() == [1, 1]
    assert batch.actions()["tokens"].shape[0] == 2

    buckets = batch.export_rollout_buckets()
    rows = sum(int(np.asarray(bucket["selected"]).shape[0]) for bucket in buckets)
    value_rows = sum(
        int(np.asarray(bucket["value_mask"]).sum()) for bucket in buckets
    )
    phases = np.concatenate([np.asarray(bucket["phase"]) for bucket in buckets])
    assert rows == 4
    assert value_rows == 2
    assert sorted(phases.tolist()) == [0, 0, 1, 1]


def test_effect_batch_seals_ranked_work_against_immutable_root_state() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 8,
        "maxMarketOrdersPerTurn": 2,
    }
    engine = native.Engine(41, configuration)
    engine.step({"farmer": ["PASS"], "market": [["HIRE"]]}, {})
    session = native.AtomicEffectSession(configuration, 4, 8)
    batch = native.AtomicEffectBatch(
        [session], [engine], np.asarray([0], dtype=np.int64), workers=1
    )
    active = np.asarray([0], dtype=np.int64)
    batch.reset_transaction()
    first = batch.observe(active)
    kinds = native.effect_policy_spec()["request_kinds"]
    fields = np.asarray(first["candidate_fields"])[0]
    stage = int(np.flatnonzero(fields[:, 0] == kinds["STAGE"])[0])
    phase = batch.advance(
        np.asarray([stage], dtype=np.int64),
        np.asarray([-1.0], dtype=np.float32),
        np.asarray([0.0], dtype=np.float32),
        turn_index=0,
    )
    np.testing.assert_array_equal(phase, [0])
    second = batch.observe(active)
    stop = int(np.flatnonzero(np.asarray(second["candidate_fields"])[0, :, 0] == 0)[0])
    batch.advance(
        np.asarray([stop], dtype=np.int64),
        np.asarray([-0.5], dtype=np.float32),
        np.asarray([0.0], dtype=np.float32),
        turn_index=0,
    )
    batch.observe(active)
    batch.advance(
        np.zeros(1, dtype=np.int64),
        np.asarray([-0.1], dtype=np.float32),
        np.asarray([0.0], dtype=np.float32),
        turn_index=0,
    )

    buckets = batch.export_rollout_buckets()
    work_rows = [
        (bucket, row)
        for bucket in buckets
        for row in range(len(np.asarray(bucket["phase"])))
        if int(np.asarray(bucket["phase"])[row]) == 0
    ]
    assert len(work_rows) == 2
    assert all(int(np.asarray(bucket["work_counts"])[row]) == 0 for bucket, row in work_rows)
    assert sorted(
        int(np.asarray(bucket["transaction_step"])[row]) for bucket, row in work_rows
    ) == [0, 1]
    assert sum(
        int(np.asarray(bucket["value_mask"])[row]) for bucket, row in work_rows
    ) == 1


def test_effect_batch_writes_reusable_buffers_and_indexes_device_behavior() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 8,
        "maxMarketOrdersPerTurn": 2,
    }
    engine = native.Engine(43, configuration)
    engine.step({"farmer": ["PASS"], "market": [["HIRE"]]}, {})
    session = native.AtomicEffectSession(configuration, 4, 8)
    batch = native.AtomicEffectBatch(
        [session], [engine], np.asarray([0], dtype=np.int64), workers=1
    )
    active = np.asarray([0], dtype=np.int64)
    batch.reset_transaction()

    widths = batch.observe_compact(active)
    spec = native.effect_policy_spec()
    rows = 2
    candidates, jobs, work, market, previous, policy_rows = widths
    assert policy_rows == 1
    fields = np.empty(
        (rows, candidates, int(spec["candidate_field_count"])), dtype=np.int64
    )
    features = np.empty(
        (rows, candidates, int(spec["candidate_feature_count"])), dtype=np.float32
    )
    candidate_mask = np.empty((rows, candidates), dtype=np.bool_)
    job_values = np.empty(
        (rows, jobs, int(spec["job_field_count"])), dtype=np.int64
    )
    job_mask = np.empty((rows, jobs), dtype=np.bool_)
    action_fields = int(spec["action_field_count"])
    work_values = np.empty((rows, work, action_fields), dtype=np.int64)
    work_mask = np.empty((rows, work), dtype=np.bool_)
    market_values = np.empty((rows, market, action_fields), dtype=np.int64)
    market_mask = np.empty((rows, market), dtype=np.bool_)
    previous_values = np.empty((rows, previous, action_fields), dtype=np.int64)
    previous_mask = np.empty((rows, previous), dtype=np.bool_)
    phase = np.empty(rows, dtype=np.int64)
    work_limit = np.empty(rows, dtype=np.int64)
    model_rows = np.empty(rows, dtype=np.int64)
    batch.write_prepared(
        fields,
        features,
        candidate_mask,
        job_values,
        job_mask,
        work_values,
        work_mask,
        market_values,
        market_mask,
        previous_values,
        previous_mask,
        phase,
        work_limit,
        model_rows,
    )
    np.testing.assert_array_equal(fields[1], fields[0])
    np.testing.assert_array_equal(candidate_mask[1], candidate_mask[0])
    np.testing.assert_array_equal(model_rows, [0, 0])

    kinds = spec["request_kinds"]
    stage = int(np.flatnonzero(fields[0, :, 0] == kinds["STAGE"])[0])
    next_phase = batch.advance_indexed(
        np.asarray([stage], dtype=np.int64), behavior_offset=5, turn_index=0
    )
    np.testing.assert_array_equal(next_phase, [0])

    next_widths = batch.observe_compact(active)
    assert next_widths[0] == candidates
    batch.write_prepared_mask(candidate_mask, model_rows)
    assert not bool(candidate_mask[0, stage])
    np.testing.assert_array_equal(candidate_mask[1], candidate_mask[0])
    batch.advance_indexed(
        np.asarray([0], dtype=np.int64), behavior_offset=10, turn_index=0
    )
    batch.observe_compact(active)
    batch.advance_indexed(
        np.asarray([0], dtype=np.int64), behavior_offset=15, turn_index=0
    )

    buckets = batch.export_rollout_buckets()
    behavior_indices = np.concatenate(
        [np.asarray(bucket["behavior_index"]) for bucket in buckets]
    )
    assert sorted(behavior_indices.tolist()) == [5, 10, 15]
