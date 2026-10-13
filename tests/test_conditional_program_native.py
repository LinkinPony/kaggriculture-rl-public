from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np
import pytest

from kagg_revue.native import _revue_native as native
from kagg_revue.policy.programs import (
    ControlType,
    Direction,
    MarketDecision,
    MarketOrderType,
    ProgramSession,
    QuantityMode,
    TaskType,
    UnitDecision,
)


def _end_market(session: ProgramSession, engine: Any) -> None:
    session.select_market(engine, 0, MarketDecision(MarketOrderType.END))


def _pass_action() -> dict[str, list[str]]:
    return {"farmer": ["PASS"]}


def test_exact_quantity_is_bounded_by_the_current_shadow_state() -> None:
    engine = native.Engine(seed=5)
    session = ProgramSession(unit_limit=4, backend=native)
    session.select_unit(engine, 0, UnitDecision(ControlType.CANCEL_PASS))
    raw = session.observation(engine, 0)
    maximum = int(np.asarray(raw["market_quantity_max"])[int(MarketOrderType.BUY_SEED), 0])

    with pytest.raises(ValueError, match="exact quantity is outside"):
        session.select_market(
            engine,
            0,
            MarketDecision(
                MarketOrderType.BUY_SEED,
                item=0,
                quantity_mode=QuantityMode.EXACT,
                exact_quantity=maximum + 1,
            ),
        )

    session.select_market(
        engine,
        0,
        MarketDecision(MarketOrderType.BUY_SEED, quantity_mode=QuantityMode.ONE),
    )
    _end_market(session, engine)
    compiled = session.compile(engine, 0)
    assert not compiled.action["farmer"] or compiled.action["farmer"] == ["PASS"]
    assert len(compiled.trace.unit_decisions) == 1
    assert len(compiled.trace.market_decisions) == 2


def test_safe_plant_persists_until_the_followup_water() -> None:
    engine = native.Engine(seed=7)
    session = ProgramSession(unit_limit=4, backend=native)
    session.select_unit(engine, 0, UnitDecision(ControlType.CANCEL_PASS))
    session.select_market(
        engine,
        0,
        MarketDecision(MarketOrderType.BUY_SEED, quantity_mode=QuantityMode.ONE),
    )
    _end_market(session, engine)
    engine.step(session.compile(engine, 0).action, _pass_action())

    farmer_x, farmer_y = engine.observation(0)["farms"][0]["farmer"]
    board_size = int(engine.configuration["boardSize"])
    target = farmer_y * board_size + farmer_x
    session.select_unit(
        engine,
        0,
        UnitDecision(
            ControlType.ASSIGN,
            task=TaskType.SAFE_PLANT,
            target=target,
            argument=0,
        ),
    )
    _end_market(session, engine)
    planted = session.compile(engine, 0)
    assert planted.action["farmer"] == ["PLANT", "WHEAT"]
    engine.step(planted.action, _pass_action())

    continued = session.observation(engine, 0)
    assert np.asarray(continued["control_mask"])[int(ControlType.KEEP)]
    session.select_unit(engine, 0, UnitDecision(ControlType.KEEP))
    _end_market(session, engine)
    watered = session.compile(engine, 0)
    assert watered.action["farmer"] == ["WATER"]
    engine.step(watered.action, _pass_action())
    tile = engine.observation(0)["farms"][0]["tiles"][farmer_y][farmer_x]
    assert tile["kind"] == "PLANT"
    assert tile["watered_today"]


def test_keep_masks_a_persistent_exact_quantity_above_current_supply() -> None:
    engine = native.Engine(seed=29)
    state = deepcopy(engine.observation(0))
    item = next(iter(state["private"]["shed"]))
    farmer_x, farmer_y = state["farms"][0]["farmer"]
    state["private"]["shed"][item] = 3
    state["farms"][0]["farmer"] = [farmer_x + 3, farmer_y]
    board_size = int(engine.configuration["boardSize"])
    target = farmer_y * board_size + farmer_x
    session = ProgramSession(unit_limit=4, backend=native)
    session.select_unit_visible(
        state,
        UnitDecision(
            ControlType.ASSIGN,
            task=TaskType.FETCH,
            target=target,
            argument=0,
            quantity_mode=QuantityMode.EXACT,
            exact_quantity=3,
        ),
    )
    session.select_market_visible(state, MarketDecision(MarketOrderType.END))

    next_state = deepcopy(state)
    next_state["step"] += 1
    next_state["farms"][0]["farmer"] = [farmer_x + 2, farmer_y]
    next_state["private"]["shed"][item] = 1
    continued = session.observation_visible(next_state)

    assert not np.asarray(continued["control_mask"])[int(ControlType.KEEP)]
    assert np.asarray(continued["option_features"])[8] == 0


def test_plant_does_not_force_a_followup_water() -> None:
    engine = native.Engine(seed=37)
    state = deepcopy(engine.observation(0))
    crop = next(iter(state["private"]["seeds"]))
    state["private"]["seeds"][crop] = 1
    x, y = state["farms"][0]["farmer"]
    target = y * int(engine.configuration["boardSize"]) + x
    session = ProgramSession(unit_limit=4, backend=native)

    session.select_unit_visible(
        state,
        UnitDecision(
            ControlType.ASSIGN,
            task=TaskType.PLANT,
            target=target,
            argument=0,
        ),
    )
    session.select_market_visible(state, MarketDecision(MarketOrderType.END))
    compiled = session.compile_visible(state)

    assert compiled.action["farmer"] == ["PLANT", "WHEAT"]


def test_wait_persists_as_an_interruptible_pass() -> None:
    engine = native.Engine(seed=41)
    session = ProgramSession(unit_limit=4, backend=native)
    session.select_unit(
        engine,
        0,
        UnitDecision(ControlType.ASSIGN, task=TaskType.WAIT),
    )
    _end_market(session, engine)
    first = session.compile(engine, 0)
    assert first.action["farmer"] == ["PASS"]
    engine.step(first.action, _pass_action())

    observed = session.observation(engine, 0)
    assert np.asarray(observed["control_mask"])[int(ControlType.KEEP)]
    session.select_unit(engine, 0, UnitDecision(ControlType.KEEP))
    _end_market(session, engine)
    assert session.compile(engine, 0).action["farmer"] == ["PASS"]


def test_store_all_compiles_to_drop_at_the_selected_shed() -> None:
    engine = native.Engine(seed=43)
    state = deepcopy(engine.observation(0))
    state["private"]["inventories"][0]["WHEAT"] = 2
    x, y = state["farms"][0]["farmer"]
    target = y * int(engine.configuration["boardSize"]) + x
    session = ProgramSession(unit_limit=4, backend=native)

    session.select_unit_visible(
        state,
        UnitDecision(
            ControlType.ASSIGN,
            task=TaskType.STORE_ALL,
            target=target,
        ),
    )
    session.select_market_visible(state, MarketDecision(MarketOrderType.END))

    assert session.compile_visible(state).action["farmer"] == ["DROP"]


def test_keep_masks_safe_plant_without_a_last_hour_waterer() -> None:
    configuration = {"turnsPerDay": 2}
    engine = native.Engine(seed=31, configuration=configuration)
    state = deepcopy(engine.observation(0))
    farmer_x, farmer_y = state["farms"][0]["farmer"]
    crop = next(iter(state["private"]["seeds"]))
    state["private"]["seeds"][crop] = 1
    state["farms"][0]["farmer"] = [farmer_x + 1, farmer_y]
    target = farmer_y * int(engine.configuration["boardSize"]) + farmer_x
    session = ProgramSession(configuration, unit_limit=4, backend=native)
    session.select_unit_visible(
        state,
        UnitDecision(
            ControlType.ASSIGN,
            task=TaskType.SAFE_PLANT,
            target=target,
            argument=0,
        ),
    )
    session.select_market_visible(state, MarketDecision(MarketOrderType.END))

    next_state = deepcopy(state)
    next_state["step"] += 1
    next_state["farms"][0]["farmer"] = [farmer_x, farmer_y]
    continued = session.observation_visible(next_state)

    assert not np.asarray(continued["control_mask"])[int(ControlType.KEEP)]
    assert np.asarray(continued["option_features"])[8] == 0


def test_last_hour_safe_plant_reserves_a_later_unit_for_water() -> None:
    configuration = {
        "episodeSteps": 8,
        "turnsPerDay": 3,
        "maxMarketOrdersPerTurn": 3,
    }
    engine = native.Engine(seed=11, configuration=configuration)
    session = ProgramSession(configuration, unit_limit=3, backend=native)
    session.select_unit(engine, 0, UnitDecision(ControlType.CANCEL_PASS))
    session.select_market(
        engine,
        0,
        MarketDecision(MarketOrderType.BUY_SEED, quantity_mode=QuantityMode.ONE),
    )
    session.select_market(engine, 0, MarketDecision(MarketOrderType.HIRE))
    _end_market(session, engine)
    engine.step(session.compile(engine, 0).action, _pass_action())

    observation = engine.observation(0)
    farmer_x, farmer_y = observation["farms"][0]["farmer"]
    hand_x, hand_y = observation["farms"][0]["hands"][0]
    assert (hand_x, hand_y) == (farmer_x + 1, farmer_y)
    session.select_unit(engine, 0, UnitDecision(ControlType.CANCEL_PASS))
    session.select_unit(
        engine,
        0,
        UnitDecision(ControlType.STEP, direction=Direction.WEST),
    )
    _end_market(session, engine)
    engine.step(session.compile(engine, 0).action, _pass_action())

    observation = engine.observation(0)
    farmer_x, farmer_y = observation["farms"][0]["farmer"]
    hand_x, hand_y = observation["farms"][0]["hands"][0]
    assert (hand_x, hand_y) == (farmer_x, farmer_y)
    board_size = int(engine.configuration["boardSize"])
    target = farmer_y * board_size + farmer_x
    session.select_unit(
        engine,
        0,
        UnitDecision(
            ControlType.ASSIGN,
            task=TaskType.SAFE_PLANT,
            target=target,
            argument=0,
        ),
    )
    forced = session.observation(engine, 0)
    assert int(forced["forced"]) == 1
    assert np.flatnonzero(forced["control_mask"]).tolist() == [int(ControlType.KEEP)]
    session.select_unit(engine, 0, UnitDecision(ControlType.KEEP))
    _end_market(session, engine)
    compiled = session.compile(engine, 0)
    assert compiled.action["farmer"] == ["PLANT", "WHEAT"]
    assert compiled.action["hands"] == [["WATER"]]
    engine.step(compiled.action, _pass_action())
    tile = engine.observation(0)["farms"][0]["tiles"][farmer_y][farmer_x]
    assert tile["kind"] == "PLANT"


def test_visible_and_batched_boundaries_match_incremental_compilation() -> None:
    engines = [native.Engine(seed=seed) for seed in (13, 17)]
    sessions = [native.ConditionalProgramSession(None, 4) for _ in engines]
    players = np.zeros(len(engines), dtype=np.int64)
    cancel = np.zeros((len(engines), 8), dtype=np.int64)
    cancel[:, 0] = int(ControlType.CANCEL_PASS)
    active = np.ones(len(engines), dtype=np.uint8)
    native.conditional_program_select_batch(sessions, engines, players, cancel, active, 2)
    market = native.conditional_program_observations_batch(sessions, engines, players, 2)
    assert np.all(np.asarray(market["scalars"])[:, 0] == 1)
    end = np.zeros_like(cancel)
    end[:, 1] = int(MarketOrderType.END)
    first_only = np.asarray([1, 0], dtype=np.uint8)
    native.conditional_program_select_batch(sessions, engines, players, end, first_only, 2)
    full = native.conditional_program_observations_batch(sessions, engines, players, 2)
    compact = native.conditional_program_active_observations_batch(sessions, engines, players, 2)
    np.testing.assert_array_equal(compact["active_rows"], [1])
    for name, values in compact.items():
        if name != "active_rows":
            np.testing.assert_array_equal(values[0], full[name][1])
    second_only = np.asarray([0, 1], dtype=np.uint8)
    native.conditional_program_select_batch(sessions, engines, players, end, second_only, 2)
    batched = native.conditional_program_actions_batch(sessions, engines, players, 2)

    for row, engine in enumerate(engines):
        visible = ProgramSession(unit_limit=4, backend=native)
        official = engine.observation(0)
        visible.select_unit_visible(official, UnitDecision(ControlType.CANCEL_PASS))
        visible.select_market_visible(official, MarketDecision(MarketOrderType.END))
        reference = visible.compile_visible(official)
        np.testing.assert_array_equal(batched["tokens"][row], reference.tokens)
        np.testing.assert_array_equal(batched["quantities"][row], reference.quantities)
