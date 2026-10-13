from __future__ import annotations

from typing import Any

import numpy as np
import pytest


def _native() -> Any:
    return pytest.importorskip("kagg_revue.native._revue_native")


def _zeros() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.zeros(8, dtype=np.int64),
        np.zeros((8, 6), dtype=np.int64),
        np.zeros(10, dtype=np.int64),
    )


def _global_plan() -> np.ndarray:
    return np.asarray([0, 0, 0, 15, 15, 14, 13, 12, 11, 10], dtype=np.int64)


def _apply_initial(
    native: Any,
    session: Any,
    engine: Any,
    lines: dict[int, list[int]],
    player: int = 0,
) -> None:
    operations, values, _global_values = _zeros()
    for line, fields in lines.items():
        operations[line] = native.structured_plan_spec()["line_operations"]["UPSERT"]
        values[line] = fields
    spec = native.structured_plan_spec()
    session.apply(
        engine,
        player,
        spec["modes"]["CONTINUE"],
        operations,
        values,
        spec["global_operations"]["SET"],
        _global_plan(),
    )


def _acknowledge(native: Any, session: Any, engine: Any, player: int = 0) -> None:
    operations, values, global_values = _zeros()
    session.apply(
        engine,
        player,
        native.structured_plan_spec()["modes"]["CONTINUE"],
        operations,
        values,
        native.structured_plan_spec()["global_operations"]["KEEP"],
        global_values,
    )


def _step_with_candidate(engine: Any, action: dict[str, Any], seat: int = 0) -> None:
    width = max(1, int(action["decision_count"]))
    tokens = np.zeros((2, width), dtype=np.int64)
    quantities = np.zeros_like(tokens)
    decision_counts = np.ones(2, dtype=np.int64)
    unit_counts = np.ones(2, dtype=np.int64)
    count = int(action["decision_count"])
    tokens[seat, :count] = action["tokens"]
    quantities[seat, :count] = action["quantities"]
    decision_counts[seat] = count
    unit_counts[seat] = int(action["unit_count"])
    engine.step_numeric(tokens, quantities, decision_counts, unit_counts)


def _decoded(native: Any, action: dict[str, Any]) -> dict[str, Any]:
    return native.decode_action_tokens(
        action["tokens"],
        action["quantities"],
        int(action["decision_count"]),
        int(action["unit_count"]),
        10,
    )


def test_empty_portfolio_rejects_stop() -> None:
    native = _native()
    configuration = {"episodeSteps": 72}
    engine = native.Engine(seed=13, configuration=configuration)
    session = native.StructuredPlanSession(configuration)
    operations, values, global_values = _zeros()

    with pytest.raises(ValueError, match="STOP requires an active production portfolio"):
        session.apply(
            engine,
            0,
            native.structured_plan_spec()["modes"]["STOP"],
            operations,
            values,
            native.structured_plan_spec()["global_operations"]["KEEP"],
            global_values,
        )


def test_initial_patch_rejects_an_inert_budget() -> None:
    native = _native()
    configuration = {"episodeSteps": 72}
    engine = native.Engine(seed=14, configuration=configuration)
    session = native.StructuredPlanSession(configuration)
    operations, values, _global_values = _zeros()
    spec = native.structured_plan_spec()
    operations[0] = spec["line_operations"]["UPSERT"]
    values[0] = [1, 0, 1, 0, 0, 0]
    inert = _global_plan()
    inert[2] = 10

    with pytest.raises(ValueError, match="authorize one production input"):
        session.apply(
            engine,
            0,
            spec["modes"]["CONTINUE"],
            operations,
            values,
            spec["global_operations"]["SET"],
            inert,
        )
    inert[2] = 0
    inert[3] = 4
    with pytest.raises(ValueError, match="authorize one production input"):
        session.apply(
            engine,
            0,
            spec["modes"]["CONTINUE"],
            operations,
            values,
            spec["global_operations"]["SET"],
            inert,
        )


def test_portfolio_executor_is_deterministic_and_traces_complete_bundles() -> None:
    native = _native()
    configuration = {"episodeSteps": 72}
    engines = [native.Engine(seed=17, configuration=configuration) for _ in range(2)]
    sessions = [native.StructuredPlanSession(configuration) for _ in range(2)]
    lines = {
        0: [2, 0, 10, 0, 0, 0],
        5: [1, 0, 9, 0, 0, 1],
    }
    for session, engine in zip(sessions, engines, strict=True):
        _apply_initial(native, session, engine, lines)

    observed_sources: set[int] = set()
    saw_unit_work = False
    for _ in range(36):
        if sessions[0].decision_required(engines[0], 0):
            assert sessions[1].decision_required(engines[1], 0)
            for session, engine in zip(sessions, engines, strict=True):
                _acknowledge(native, session, engine)
        actions = [
            session.action_numeric(engine, 0)
            for session, engine in zip(sessions, engines, strict=True)
        ]
        for key in (
            "tokens",
            "quantities",
            "unit_sources",
            "unit_reasons",
            "market_sources",
        ):
            np.testing.assert_array_equal(actions[0][key], actions[1][key])
        tokens = np.asarray(actions[0]["tokens"])
        unit_count = int(actions[0]["unit_count"])
        sources = np.asarray(actions[0]["unit_sources"])
        active_units = tokens[:unit_count] != 0
        assert np.all(sources[active_units] >= 0)
        assert np.all(np.asarray(actions[0]["market_sources"]) >= 0)
        observed_sources.update(int(value) for value in sources[active_units])
        observed_sources.update(int(value) for value in actions[0]["market_sources"])
        saw_unit_work |= bool(active_units.any())
        for engine, action in zip(engines, actions, strict=True):
            _step_with_candidate(engine, action)
        assert engines[0].observation(0) == engines[1].observation(0)

    assert {0, 5} <= observed_sources
    assert saw_unit_work


def test_incremental_patch_retains_lines_and_stop_keeps_maintenance() -> None:
    native = _native()
    configuration = {"episodeSteps": 72}
    engine = native.Engine(seed=23, configuration=configuration)
    session = native.StructuredPlanSession(configuration)
    _apply_initial(native, session, engine, {0: [2, 0, 8, 0, 0, 0]})

    planted = False
    for _ in range(24):
        if session.decision_required(engine, 0):
            _acknowledge(native, session, engine)
        action = session.action_numeric(engine, 0)
        decoded = _decoded(native, action)
        planted = any(
            unit and unit[0] == "PLANT" for unit in (decoded["farmer"], *decoded["hands"])
        )
        _step_with_candidate(engine, action)
        if planted:
            break
    assert planted

    operations, values, global_values = _zeros()
    session.apply(
        engine,
        0,
        native.structured_plan_spec()["modes"]["STOP"],
        operations,
        values,
        native.structured_plan_spec()["global_operations"]["KEEP"],
        global_values,
    )
    stopped_observation = session.observation(engine, 0)
    assert session.paused
    assert stopped_observation["active_line_mask"][0] == 1
    stopped_action = session.action_numeric(engine, 0)
    assert _decoded(native, stopped_action)["farmer"][0] == "WATER"
    np.testing.assert_array_equal(stopped_action["unit_sources"], [0])
    assert np.asarray(stopped_action["market_sources"]).size == 0

    _acknowledge(native, session, engine)
    spec = native.structured_plan_spec()
    operations, values, global_values = _zeros()
    operations[0] = spec["line_operations"]["UPSERT"]
    values[0] = [3, 0, 8, 0, 0, 0]
    operations[5] = spec["line_operations"]["UPSERT"]
    values[5] = [1, 0, 7, 0, 0, 1]
    session.apply(
        engine,
        0,
        spec["modes"]["CONTINUE"],
        operations,
        values,
        spec["global_operations"]["KEEP"],
        global_values,
    )
    observation = session.observation(engine, 0)
    np.testing.assert_array_equal(observation["active_line_mask"][[0, 5]], [1, 1])
    np.testing.assert_array_equal(observation["active_lines"][5], values[5])

    operations, values, global_values = _zeros()
    operations[0] = spec["line_operations"]["RETIRE"]
    session.apply(
        engine,
        0,
        spec["modes"]["CONTINUE"],
        operations,
        values,
        spec["global_operations"]["KEEP"],
        global_values,
    )
    observation = session.observation(engine, 0)
    np.testing.assert_array_equal(observation["active_line_mask"][[0, 5]], [0, 1])
    operations, values, global_values = _zeros()
    operations[5] = spec["line_operations"]["UPSERT"]
    values[5] = [2, 0, 7, 0, 0, 1]
    session.apply(
        engine,
        0,
        spec["modes"]["STOP"],
        operations,
        values,
        spec["global_operations"]["KEEP"],
        global_values,
    )
    assert session.paused
    np.testing.assert_array_equal(session.observation(engine, 0)["active_lines"][5], values[5])


def test_stop_replenishes_feed_needed_by_an_active_animal_line() -> None:
    native = _native()
    configuration = {"episodeSteps": 144}
    engine = native.Engine(seed=23, configuration=configuration)
    session = native.StructuredPlanSession(configuration)
    _apply_initial(native, session, engine, {5: [1, 0, 9, 0, 0, 0]})

    fed = False
    for _ in range(100):
        if session.decision_required(engine, 0):
            _acknowledge(native, session, engine)
        action = session.action_numeric(engine, 0)
        fed = _decoded(native, action)["farmer"][0] == "FEED"
        _step_with_candidate(engine, action)
        if fed:
            break
    assert fed

    operations, values, global_values = _zeros()
    session.apply(
        engine,
        0,
        native.structured_plan_spec()["modes"]["STOP"],
        operations,
        values,
        native.structured_plan_spec()["global_operations"]["KEEP"],
        global_values,
    )
    stopped = session.action_numeric(engine, 0)
    assert ["BUY_PRODUCT", "WHEAT", 1] in _decoded(native, stopped)["market"]
    np.testing.assert_array_equal(stopped["market_sources"], [5])


def test_portfolio_numeric_action_matches_official_action_boundary() -> None:
    native = _native()
    configuration = {"episodeSteps": 48}
    numeric_engine = native.Engine(seed=29, configuration=configuration)
    official_engine = numeric_engine.clone()
    session = native.StructuredPlanSession(configuration)
    _apply_initial(native, session, numeric_engine, {0: [2, 0, 8, 0, 0, 0]})
    action = session.action_numeric(numeric_engine, 0)
    decoded = _decoded(native, action)
    _step_with_candidate(numeric_engine, action)
    official_engine.step(
        decoded,
        {"farmer": ["PASS"], "hands": [], "market": []},
    )
    assert numeric_engine.observation(0) == official_engine.observation(0)
    assert numeric_engine.observation(1) == official_engine.observation(1)


def test_portfolio_batch_supports_all_lines_and_reports_truncation_event() -> None:
    native = _native()
    configuration = {"episodeSteps": 48, "maxMarketOrdersPerTurn": 1}
    engines = [native.Engine(seed=seed, configuration=configuration) for seed in (31, 37)]
    sessions = [native.StructuredPlanSession(configuration) for _ in engines]
    players = np.asarray([0, 1], dtype=np.int64)
    observations = native.structured_plan_observations_batch(sessions, engines, players, 2)
    assert observations["features"].shape == (2, 90)
    assert observations["journal"].shape == (2, 32)
    assert observations["active_lines"].shape == (2, 8, 6)
    assert observations["active_line_mask"].shape == (2, 8)
    assert observations["global_plan"].shape == (2, 10)

    spec = native.structured_plan_spec()
    modes = np.full(2, spec["modes"]["CONTINUE"], dtype=np.int64)
    line_operations = np.full(
        (2, 8),
        spec["line_operations"]["UPSERT"],
        dtype=np.int64,
    )
    line_values = np.zeros((2, 8, 6), dtype=np.int64)
    for line in range(8):
        line_values[:, line] = [1, 0, 15 - line, 0, 0, line % 2]
    global_operations = np.full(2, spec["global_operations"]["SET"], dtype=np.int64)
    global_values = np.repeat(_global_plan()[None], 2, axis=0)
    native.structured_plan_apply_batch(
        sessions,
        engines,
        players,
        modes,
        line_operations,
        line_values,
        global_operations,
        global_values,
        2,
    )
    assert all(session.active_line_count == 8 for session in sessions)
    actions = native.structured_plan_actions_batch(sessions, engines, players, 2)
    assert actions["tokens"].shape[0] == 2
    assert not np.asarray(actions["requires_decision"]).any()
    assert np.all(np.asarray(actions["market_sources"])[:, 0] >= 0)
    truncation = spec["events"].index("MARKET_SLOTS_TRUNCATED")
    assert all(session.pending_events & (1 << truncation) for session in sessions)

    for session, engine, player in zip(sessions, engines, players, strict=True):
        _acknowledge(native, session, engine, int(player))
        session.action_numeric(engine, int(player))
        assert not session.pending_events & (1 << truncation)

        operations, values, global_values = _zeros()
        session.apply(
            engine,
            int(player),
            spec["modes"]["STOP"],
            operations,
            values,
            spec["global_operations"]["KEEP"],
            global_values,
        )
        session.action_numeric(engine, int(player))
        _acknowledge(native, session, engine, int(player))
        session.action_numeric(engine, int(player))
        assert session.pending_events & (1 << truncation)

    with pytest.raises(ValueError, match="semantic change"):
        sessions[0].apply(
            engines[0],
            0,
            spec["modes"]["CONTINUE"],
            np.where(np.arange(8) == 0, spec["line_operations"]["UPSERT"], 0).astype(np.int64),
            np.where(
                (np.arange(8) == 0)[:, None],
                line_values[0, 0],
                np.zeros((8, 6), dtype=np.int64),
            ),
            spec["global_operations"]["KEEP"],
            np.zeros(10, dtype=np.int64),
        )


def test_portfolio_ready_batch_and_fused_self_play_match_manual_tick() -> None:
    native = _native()
    configuration = {"episodeSteps": 48}
    reference = native.Engine(seed=41, configuration=configuration)
    fused = native.Engine(seed=41, configuration=configuration)
    reference_sessions = [native.StructuredPlanSession(configuration) for _ in range(2)]
    fused_sessions = [native.StructuredPlanSession(configuration) for _ in range(2)]
    players = np.asarray([0, 1], dtype=np.int64)

    ready = native.structured_plan_ready_observations_batch(
        fused_sessions,
        [fused, fused],
        players,
        2,
    )
    np.testing.assert_array_equal(ready["indices"], players)
    assert ready["active_lines"].shape == (2, 8, 6)

    for sessions, engine in (
        (reference_sessions, reference),
        (fused_sessions, fused),
    ):
        _apply_initial(native, sessions[0], engine, {0: [2, 0, 8, 0, 0, 0]}, 0)
        _apply_initial(native, sessions[1], engine, {1: [2, 0, 8, 0, 0, 0]}, 1)

    empty = native.structured_plan_ready_observations_batch(
        fused_sessions,
        [fused, fused],
        players,
        2,
    )
    assert np.asarray(empty["indices"]).size == 0
    assert empty["features"].shape == (0, 90)

    actions = native.structured_plan_actions_batch(
        reference_sessions,
        [reference, reference],
        players,
        2,
    )
    native.engine_step_numeric_batch(
        [reference],
        np.asarray(actions["tokens"])[None],
        np.asarray(actions["quantities"])[None],
        np.asarray(actions["decision_counts"])[None],
        np.asarray(actions["unit_counts"])[None],
        1,
    )
    native.structured_plan_step_self_play_batch(
        [fused],
        np.asarray([0], dtype=np.int64),
        [fused_sessions[0]],
        [fused_sessions[1]],
        1,
    )
    assert fused.observation(0) == reference.observation(0)
    assert fused.observation(1) == reference.observation(1)


def test_portfolio_native_scheduler_stops_at_the_next_decision() -> None:
    native = _native()
    configuration = {"episodeSteps": 48}
    reference = native.Engine(seed=43, configuration=configuration)
    fused = native.Engine(seed=43, configuration=configuration)
    reference_sessions = [native.StructuredPlanSession(configuration) for _ in range(2)]
    fused_sessions = [native.StructuredPlanSession(configuration) for _ in range(2)]
    players = np.asarray([0, 1], dtype=np.int64)
    for sessions, engine in (
        (reference_sessions, reference),
        (fused_sessions, fused),
    ):
        _apply_initial(native, sessions[0], engine, {0: [8, 0, 8, 0, 0, 0]}, 0)
        _apply_initial(native, sessions[1], engine, {1: [8, 0, 8, 0, 0, 0]}, 1)

    manual_advanced = 0
    while not any(
        session.decision_required(reference, player)
        for session, player in zip(reference_sessions, players, strict=True)
    ):
        actions = native.structured_plan_actions_batch(
            reference_sessions,
            [reference, reference],
            players,
            2,
        )
        native.engine_step_numeric_batch(
            [reference],
            np.asarray(actions["tokens"])[None],
            np.asarray(actions["quantities"])[None],
            np.asarray(actions["decision_counts"])[None],
            np.asarray(actions["unit_counts"])[None],
            1,
        )
        manual_advanced += 1

    result = native.structured_plan_advance_self_play_batch(
        [fused],
        np.asarray([0], dtype=np.int64),
        [fused_sessions[0]],
        [fused_sessions[1]],
        1,
    )
    assert manual_advanced > 1
    assert int(np.asarray(result["advanced_turns"])[0]) == manual_advanced
    assert bool(np.asarray(result["done"])[0]) is reference.done
    assert fused.step_index == reference.step_index
    assert fused.observation(0) == reference.observation(0)
    assert fused.observation(1) == reference.observation(1)
