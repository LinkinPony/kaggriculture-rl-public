from collections import Counter

import numpy as np

from kagg_revue.bc.actions import EncodedTurnAction, ReplayActionEncoder
from kagg_revue.bc.programs.teacher_batch import compile_teacher_program_turn_batch
from kagg_revue.bc.programs.translate import _turn_trace
from kagg_revue.native import _revue_native as native
from kagg_revue.opponents.kaito.native import create_native_session as kaito_session
from kagg_revue.policy.programs.contract import (
    ControlType,
    Direction,
    MarketOrderType,
    QuantityMode,
    RawOperation,
    TaskType,
)
from kagg_revue.policy.programs.native import NativeProgramContract


def test_program_teacher_compacts_empty_market_slots_losslessly() -> None:
    engine = native.Engine(seed=71)
    configuration = dict(engine.configuration)
    observation = dict(engine.observation(0))
    codec = ReplayActionEncoder(native.action_codec_spec())
    encoded = codec.encode(
        {
            "farmer": ["PASS"],
            "market": [None, ["BUY_SEED", "WHEAT", 1]],
        },
        unit_count=1,
        max_market_orders=int(configuration["maxMarketOrdersPerTurn"]),
    )
    contract = NativeProgramContract.from_spec(native.conditional_program_spec(configuration, 4))
    handle = native.ConditionalProgramSession(configuration, 4)

    trace, compiled = _turn_trace(handle, observation, encoded, codec, contract, Counter())

    count = int(compiled["decision_count"])
    keys = [codec.keys[int(token)] for token in np.asarray(compiled["tokens"])[:count]]
    assert keys == ["UNIT:PASS", "MARKET:BUY_SEED:WHEAT"]
    program_count = int(trace["decision_count"])
    assert program_count == count + 1
    assert np.asarray(trace["conditional_masks"])[:program_count].any(axis=1).all()


def test_semantic_replay_teacher_assigns_and_keeps_an_exact_safe_plant() -> None:
    engine = native.Engine(seed=73)
    engine.step(
        {
            "farmer": ["PASS"],
            "market": [["BUY_SEED", "WHEAT", 1]],
        },
        {"farmer": ["PASS"]},
    )
    configuration = dict(engine.configuration)
    codec = ReplayActionEncoder(native.action_codec_spec())
    contract = NativeProgramContract.from_spec(
        native.conditional_program_spec(configuration, 4)
    )
    handle = native.ConditionalProgramSession(configuration, 4)
    observation = dict(engine.observation(0))
    x, y = observation["farms"][0]["farmer"]
    proposal = (
        int(ControlType.ASSIGN),
        int(TaskType.SAFE_PLANT),
        int(y) * contract.board_size + int(x),
        0,
        int(Direction.NORTH),
        int(RawOperation.DROP),
        int(QuantityMode.ONE),
        1,
        int(MarketOrderType.END),
    )
    plant = codec.encode(
        {"farmer": ["PLANT", "WHEAT"]},
        unit_count=1,
        max_market_orders=contract.maximum_market_orders,
    )
    planted_trace, planted = _turn_trace(
        handle,
        observation,
        plant,
        codec,
        contract,
        Counter(),
        ((proposal,),),
    )
    assert int(np.asarray(planted_trace["actions"])[0, 0]) == int(ControlType.ASSIGN)
    engine.step(planted["action"], {"farmer": ["PASS"]})

    water = codec.encode(
        {"farmer": ["WATER"]},
        unit_count=1,
        max_market_orders=contract.maximum_market_orders,
    )
    watered_trace, watered = _turn_trace(
        handle,
        dict(engine.observation(0)),
        water,
        codec,
        contract,
        Counter(),
        ((),),
    )
    assert int(np.asarray(watered_trace["actions"])[0, 0]) == int(ControlType.KEEP)
    count = int(watered["decision_count"])
    assert codec.keys[int(np.asarray(watered["tokens"])[0])] == "UNIT:WATER"
    assert count == 1


def test_semantic_teacher_tries_fetch_after_an_invalid_composite() -> None:
    engine = native.Engine(seed=79)
    observation = dict(engine.observation(0))
    observation["private"]["shed"]["WHEAT"] = 2
    x, y = observation["farms"][0]["farmer"]
    configuration = dict(engine.configuration)
    codec = ReplayActionEncoder(native.action_codec_spec())
    contract = NativeProgramContract.from_spec(
        native.conditional_program_spec(configuration, 4)
    )
    encoded = codec.encode(
        {"farmer": ["PICKUP", "WHEAT", 2]},
        unit_count=1,
        max_market_orders=contract.maximum_market_orders,
    )
    common = (
        int(ControlType.ASSIGN),
        int(TaskType.FEED),
        0,
        0,
        int(Direction.NORTH),
        int(RawOperation.DROP),
        int(QuantityMode.ONE),
        1,
        int(MarketOrderType.END),
    )
    fetch = (
        int(ControlType.ASSIGN),
        int(TaskType.FETCH),
        int(y) * contract.board_size + int(x),
        0,
        int(Direction.NORTH),
        int(RawOperation.DROP),
        int(QuantityMode.EXACT),
        2,
        int(MarketOrderType.END),
    )

    trace, compiled = _turn_trace(
        native.ConditionalProgramSession(configuration, 4),
        observation,
        encoded,
        codec,
        contract,
        Counter(),
        ((common, fetch),),
    )

    assert int(np.asarray(trace["actions"])[0, 0]) == int(ControlType.ASSIGN)
    assert int(np.asarray(trace["actions"])[0, 1]) == int(TaskType.FETCH)
    assert compiled["action"]["farmer"] == ["PICKUP", "WHEAT", 2]


def test_batched_native_teacher_compiler_matches_visible_reference() -> None:
    engines = [native.Engine(seed=81), native.Engine(seed=82)]
    configuration = dict(engines[0].configuration)
    seats = np.asarray([0, 1], dtype=np.int64)
    contract = NativeProgramContract.from_spec(
        native.conditional_program_spec(configuration, 32)
    )
    codec = ReplayActionEncoder(native.action_codec_spec())
    width = 64
    tokens = np.zeros((2, width), dtype=np.int64)
    quantities = np.zeros_like(tokens)
    counts = np.zeros(2, dtype=np.int64)
    unit_counts = np.zeros(2, dtype=np.int64)
    maximum_orders = int(configuration["maxMarketOrdersPerTurn"])
    native.kaito_v48_action_numeric_batch(
        engines,
        seats,
        [kaito_session(maximum_orders) for _ in engines],
        tokens,
        quantities,
        counts,
        unit_counts,
        2,
    )
    expected = []
    expected_repairs = []
    for row, (engine, seat) in enumerate(zip(engines, seats, strict=True)):
        count = int(counts[row])
        repairs: Counter[str] = Counter()
        expected.append(
            _turn_trace(
                native.ConditionalProgramSession(configuration, 32),
                dict(engine.observation(int(seat))),
                EncodedTurnAction(
                    tokens=tuple(int(value) for value in tokens[row, :count]),
                    quantities=tuple(int(value) for value in quantities[row, :count]),
                    unit_decisions=int(unit_counts[row]),
                    market_orders=count - int(unit_counts[row]),
                    repairs={},
                ),
                codec,
                contract,
                repairs,
            )[0]
        )
        expected_repairs.append(repairs)
    actual_repairs = [Counter[str]() for _ in engines]
    actual = compile_teacher_program_turn_batch(
        native,
        [native.ConditionalProgramSession(configuration, 32) for _ in engines],
        engines,
        seats,
        tokens,
        quantities,
        counts,
        unit_counts,
        codec,
        contract,
        2,
        actual_repairs,
    )
    fields = {
        "scalars": actual.scalars,
        "root_features": actual.root_features,
        "option_features": actual.option_features,
        "target_reservations": actual.target_reservations,
        "actions": actual.actions,
        "conditional_masks": actual.conditional_masks,
        "quantity_max": actual.quantity_max,
        "decision_count": actual.decision_counts,
    }
    for row in range(len(engines)):
        for name, values in fields.items():
            assert np.array_equal(values[row], np.asarray(expected[row][name]))
        assert actual_repairs[row] == expected_repairs[row]
