import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pytest

from kagg_revue.policy.facts import DerivedFactEpisodeEncoder, OpponentInventoryBounds


def _index(names: Sequence[str]) -> dict[str, int]:
    return {name: index for index, name in enumerate(names)}


def _signed_log_inverse(value: float) -> float:
    return math.copysign(math.expm1(abs(value) * 12.0), value)


def _clamp_ratio(value: float, scale: float) -> float:
    return max(-1.0, min(1.0, value / scale))


def _pass_action() -> dict[str, Any]:
    return {"farmer": ["PASS"], "hands": [], "market": []}


def _product_holdings(private: Mapping[str, Any], product: str) -> int:
    shed = int(private["shed"].get(product, 0))
    carried = sum(int(inventory.get(product, 0)) for inventory in private["inventories"])
    return shed + carried


def test_fact_contract_matches_both_native_policy_boundaries() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(seed=17, configuration={"episodeSteps": 100})
    direct = engine.policy_session(0, 4)
    observed = native.PolicySession(engine.observation(0), dict(engine.configuration), 4)
    spec = native.derived_fact_spec()

    for width_key, names_key in (
        ("turn_features", "turn_feature_names"),
        ("prefix_features", "prefix_feature_names"),
        ("candidate_features", "candidate_feature_names"),
    ):
        names = list(spec[names_key])
        assert len(names) == int(spec[width_key])
        assert len(names) == len(set(names))

    products = int(spec["products"])
    lower = np.zeros(products, dtype=np.int64)
    upper = np.arange(products, dtype=np.int64)
    np.testing.assert_array_equal(
        direct.turn_facts(lower, upper), observed.turn_facts(lower, upper)
    )
    turn_names = _index(spec["turn_feature_names"])
    unknown = np.asarray(direct.turn_facts())
    market_rows = unknown[unknown[:, turn_names["type_market"]] > 0.5]
    assert np.all(
        market_rows[:, turn_names["opponent_product_upper_bound"]]
        > market_rows[:, turn_names["opponent_product_lower_bound"]]
    )
    np.testing.assert_array_equal(direct.prefix_facts(), observed.prefix_facts())
    np.testing.assert_array_equal(direct.candidate_facts(), observed.candidate_facts())
    np.testing.assert_array_equal(direct.legal_mask(), observed.legal_mask())
    for name in (
        "market_inventory",
        "town_consumption",
        "opponent_unit_gain_upper",
    ):
        np.testing.assert_array_equal(direct.flow_snapshot()[name], observed.flow_snapshot()[name])

    keys = list(native.action_codec_spec()["keys"])
    for token in (keys.index("UNIT:PASS"), keys.index("MARKET:STOP")):
        direct.select(token)
        observed.select(token)
    assert direct.action() == observed.action()
    np.testing.assert_array_equal(
        direct.own_market_flow_bounds(), observed.own_market_flow_bounds()
    )


def test_episode_encoder_aligns_facts_before_each_selected_decision() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(seed=18, configuration={"episodeSteps": 100})
    keys = list(native.action_codec_spec()["keys"])
    selected = np.asarray([keys.index("UNIT:PASS"), keys.index("MARKET:STOP")], dtype=np.int64)
    quantities = np.zeros_like(selected)
    reference = engine.policy_session(0, 4)
    expected_prefix = [np.asarray(reference.prefix_facts())]
    expected_candidates = [np.asarray(reference.candidate_facts())]
    reference.select(int(selected[0]))
    expected_prefix.append(np.asarray(reference.prefix_facts()))
    expected_candidates.append(np.asarray(reference.candidate_facts()))

    encoder = DerivedFactEpisodeEncoder(int(native.derived_fact_spec()["products"]))
    encoded = encoder.encode_turn(engine.policy_session(0, 4), selected, quantities)
    np.testing.assert_array_equal(encoded.prefix, np.stack(expected_prefix))
    np.testing.assert_array_equal(encoded.candidates, np.stack(expected_candidates))


def test_candidate_facts_equal_exact_unit_and_market_transitions() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(seed=19, configuration={"episodeSteps": 100})
    configuration = dict(engine.configuration)
    rules = native.game_rules()
    keys = list(native.action_codec_spec()["keys"])
    names = _index(native.derived_fact_spec()["candidate_feature_names"])
    session = engine.policy_session(0, 4)
    candidates = np.asarray(session.candidate_facts())
    unit_tokens = int(native.action_codec_spec()["unit_tokens"])
    np.testing.assert_array_equal(
        candidates[:unit_tokens, names["executable"]] > 0.5,
        np.asarray(session.legal_mask(), dtype=np.bool_)[:unit_tokens],
    )
    before = engine.observation(0)
    before_position = before["farms"][0]["farmer"]
    board_size = int(configuration["boardSize"])

    movements = {
        "UNIT:NORTH": (0, -1),
        "UNIT:SOUTH": (0, 1),
        "UNIT:EAST": (1, 0),
        "UNIT:WEST": (-1, 0),
    }
    movement_key, (requested_dx, requested_dy) = next(
        (key, delta)
        for key, delta in movements.items()
        if 0 <= before_position[0] + delta[0] < board_size
        and 0 <= before_position[1] + delta[1] < board_size
    )
    movement = candidates[keys.index(movement_key)]
    moved = engine.clone()
    moved.step(
        {"farmer": [movement_key.removeprefix("UNIT:")], "hands": [], "market": []},
        _pass_action(),
    )
    after_position = moved.observation(0)["farms"][0]["farmer"]
    actual_dx = int(after_position[0]) - int(before_position[0])
    actual_dy = int(after_position[1]) - int(before_position[1])
    assert (actual_dx, actual_dy) == (requested_dx, requested_dy)
    assert movement[names["executable"]] == 1.0
    assert movement[names["exact"]] == 1.0
    assert movement[names["delta_x"]] == pytest.approx(_clamp_ratio(actual_dx, board_size - 1))
    assert movement[names["delta_y"]] == pytest.approx(_clamp_ratio(actual_dy, board_size - 1))

    session.select(keys.index("UNIT:PASS"))
    candidates = np.asarray(session.candidate_facts())
    seed_key = "MARKET:BUY_SEED:WHEAT"
    seed = candidates[keys.index(seed_key)]
    seed_cost = int(rules["crops"]["WHEAT"]["seed_cost"])
    expected_seed_maximum = int(engine.money(0) // seed_cost)
    encoded_seed_maximum = round(
        _signed_log_inverse(float(seed[names["maximum_feasible_quantity"]]))
    )
    assert encoded_seed_maximum == expected_seed_maximum
    assert seed[names["exact"]] == 1.0
    assert seed[names["conditional_no_opponent"]] == 0.0

    maximum_seed_purchase = engine.clone()
    maximum_seed_purchase.step(
        {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_SEED", "WHEAT", encoded_seed_maximum]],
        },
        _pass_action(),
    )
    purchased_seeds = maximum_seed_purchase.observation(0)["private"]["seeds"]["WHEAT"]
    assert int(purchased_seeds) == encoded_seed_maximum
    maximum_cash_delta = _signed_log_inverse(float(seed[names["maximum_quantity_cash_delta"]]))
    assert maximum_cash_delta == pytest.approx(
        maximum_seed_purchase.money(0) - engine.money(0), abs=1e-3
    )

    sell = candidates[keys.index("MARKET:SELL:WHEAT")]
    assert sell[names["exact"]] == 0.0
    assert sell[names["conditional_no_opponent"]] == 1.0
    assert _signed_log_inverse(float(sell[names["maximum_feasible_quantity"]])) == 0.0

    buy_key = "MARKET:BUY_PRODUCT:WHEAT"
    buy = candidates[keys.index(buy_key)]
    encoded_buy_maximum = round(_signed_log_inverse(float(buy[names["maximum_feasible_quantity"]])))
    maximum_product_purchase = engine.clone()
    maximum_product_purchase.step(
        {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_PRODUCT", "WHEAT", encoded_buy_maximum]],
        },
        _pass_action(),
    )
    purchased_products = _product_holdings(
        maximum_product_purchase.observation(0)["private"], "WHEAT"
    )
    assert purchased_products == encoded_buy_maximum
    assert buy[names["conditional_no_opponent"]] == 1.0
    assert _signed_log_inverse(float(buy[names["maximum_quantity_cash_delta"]])) == pytest.approx(
        maximum_product_purchase.money(0) - engine.money(0), abs=1e-3
    )

    stocked = engine.clone()
    stocked.step(
        {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_PRODUCT", "WHEAT", 3]],
        },
        _pass_action(),
    )
    pickup = np.asarray(stocked.policy_session(0, 4).candidate_facts())
    quantity_pickup = pickup[keys.index("UNIT:PICKUP:WHEAT")]
    assert (
        round(_signed_log_inverse(float(quantity_pickup[names["maximum_feasible_quantity"]]))) == 3
    )

    stocked_market = stocked.policy_session(0, 4)
    stocked_market.select(keys.index("UNIT:PASS"))
    stocked_candidates = np.asarray(stocked_market.candidate_facts())
    stocked_sell = stocked_candidates[keys.index("MARKET:SELL:WHEAT")]
    encoded_sell_maximum = round(
        _signed_log_inverse(float(stocked_sell[names["maximum_feasible_quantity"]]))
    )
    assert encoded_sell_maximum == 3
    maximum_sale = stocked.clone()
    maximum_sale.step(
        {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["SELL", "WHEAT", encoded_sell_maximum]],
        },
        _pass_action(),
    )
    assert _signed_log_inverse(
        float(stocked_sell[names["maximum_quantity_cash_delta"]])
    ) == pytest.approx(maximum_sale.money(0) - stocked.money(0), abs=1e-3)

    prefix_quantity = min(3, encoded_seed_maximum)
    session.select(keys.index(seed_key), prefix_quantity)
    prefix_names = _index(native.derived_fact_spec()["prefix_feature_names"])
    prefix = np.asarray(session.prefix_facts())
    projected = engine.clone()
    projected.step(
        {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_SEED", "WHEAT", prefix_quantity]],
        },
        _pass_action(),
    )
    assert _signed_log_inverse(float(prefix[prefix_names["projected_money"]])) == (
        pytest.approx(projected.money(0), abs=1e-3)
    )
    assert round(_signed_log_inverse(float(prefix[prefix_names["seed_wheat"]]))) == prefix_quantity
    assert prefix[prefix_names["projection_exact"]] == 1.0

    has_quantity = np.asarray(native.action_codec_spec()["has_quantity"], dtype=np.bool_)
    initial_market = engine.policy_session(0, 4)
    initial_market.select(keys.index("UNIT:PASS"))
    market_candidates = np.asarray(initial_market.candidate_facts())
    for token in range(unit_tokens, len(keys)):
        row = market_candidates[token]
        maximum = round(_signed_log_inverse(float(row[names["maximum_feasible_quantity"]])))
        if has_quantity[token] and maximum <= 0:
            continue
        projected_session = engine.policy_session(0, 4)
        projected_session.select(keys.index("UNIT:PASS"))
        projected_session.select(token, maximum if has_quantity[token] else 0)
        if int(projected_session.phase) != 2:
            projected_session.select(keys.index("MARKET:STOP"))
        projected_engine = engine.clone()
        projected_engine.step(projected_session.action(), _pass_action())
        assert _signed_log_inverse(
            float(row[names["maximum_quantity_cash_delta"]])
        ) == pytest.approx(projected_engine.money(0) - engine.money(0), abs=1e-3)


def test_turn_facts_encode_lifecycle_geometry_and_relaxed_reachability() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(seed=23, configuration={"episodeSteps": 100})
    configuration = dict(engine.configuration)
    rules = native.game_rules()
    engine.step(
        {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_SEED", "WHEAT", 1]],
        },
        _pass_action(),
    )
    engine.step(
        {"farmer": ["PLANT", "WHEAT"], "hands": [], "market": []},
        _pass_action(),
    )

    observation = engine.observation(0)
    position = observation["farms"][0]["farmer"]
    tile = observation["farms"][0]["tiles"][position[1]][position[0]]
    session = engine.policy_session(0, 4)
    spec = native.derived_fact_spec()
    names = _index(spec["turn_feature_names"])
    facts = np.asarray(session.turn_facts())
    asset_rows = facts[
        (facts[:, names["type_asset"]] > 0.5) & (facts[:, names["item_wheat"]] > 0.5)
    ]
    assert asset_rows.shape[0] == 1
    asset = asset_rows[0]
    episode_steps = int(configuration["episodeSteps"])
    turns_per_day = int(configuration["turnsPerDay"])
    maturity_step = (
        int(tile["planted_day"]) + int(rules["crops"]["WHEAT"]["first_yield_day"])
    ) * turns_per_day
    assert asset[names["turns_to_maturity"]] == pytest.approx(
        _clamp_ratio(maturity_step - int(observation["step"]), episode_steps)
    )

    market_rows = facts[
        (facts[:, names["type_market"]] > 0.5) & (facts[:, names["item_wheat"]] > 0.5)
    ]
    assert market_rows.shape[0] == 1
    market = market_rows[0]
    inventory = int(observation["market"]["inventory"]["WHEAT"])
    floor = engine.market_price("WHEAT", inventory + 1_000_000_000)
    units_to_floor = round(
        _signed_log_inverse(float(market[names["sell_units_to_floor_or_slot_cap"]]))
    )
    assert units_to_floor > 0
    reached_floor = market[names["sell_floor_reached_within_slot"]] > 0.5
    boundary_price = engine.market_price("WHEAT", inventory + units_to_floor)
    assert (boundary_price == floor) == reached_floor
    if reached_floor:
        assert engine.market_price("WHEAT", inventory + units_to_floor - 1) > floor
    base_price = float(configuration["marketParams"]["WHEAT"]["base"])
    curve_inventory = inventory
    revenue = 0
    for _ in range(4):
        price = engine.market_price("WHEAT", curve_inventory)
        revenue += price
        if price > floor:
            curve_inventory += 1
    assert market[names["sell_average_four"]] == pytest.approx(
        _clamp_ratio(revenue / 4, 5 * base_price)
    )

    service_rows = facts[
        (facts[:, names["type_unit_service"]] > 0.5) & (facts[:, names["service_water"]] > 0.5)
    ]
    assert service_rows.shape[0] == 1
    service = service_rows[0]
    board_size = int(configuration["boardSize"])
    target_x = round(float(service[names["x"]]) * (board_size - 1))
    target_y = round(float(service[names["y"]]) * (board_size - 1))
    distance = abs(int(position[0]) - target_x) + abs(int(position[1]) - target_y)
    encoded_distance = float(service[names["manhattan_distance"]]) * (2 * (board_size - 1))
    terminal_turns = float(service[names["turns_to_terminal_deadline"]]) * episode_steps
    arrival_slack = float(service[names["arrival_slack"]]) * episode_steps
    assert encoded_distance == pytest.approx(distance)
    assert arrival_slack == pytest.approx(terminal_turns - distance, abs=1e-4)
    assert service[names["reachable"]] == float(arrival_slack >= 0)

    keys = list(native.action_codec_spec()["keys"])
    candidate_names = _index(spec["candidate_feature_names"])
    water = np.asarray(session.candidate_facts())[keys.index("UNIT:WATER")]
    watered = engine.clone()
    watered.step(
        {"farmer": ["WATER"], "hands": [], "market": []},
        _pass_action(),
    )
    after_tile = watered.observation(0)["farms"][0]["tiles"][position[1]][position[0]]
    assert water[candidate_names["executable"]] == 1.0
    assert water[candidate_names["exact"]] == 1.0
    assert water[candidate_names["watered_delta"]] == (
        float(after_tile["watered_today"]) - float(tile["watered_today"])
    )
    assert water[candidate_names["changed_tile_fraction"]] == pytest.approx(
        1.0 / (board_size * board_size)
    )

    relaxed = facts[facts[:, names["type_relaxed_feasibility"]] > 0.5]
    assert relaxed.shape[0] == 1
    assert "relaxation" in str(spec["matching_semantics"])


def test_opponent_inventory_upper_bound_contains_native_hidden_truth() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(seed=29, configuration={"episodeSteps": 100})
    products = list(native.game_rules()["products"])
    tracker = OpponentInventoryBounds(len(products))
    keys = list(native.action_codec_spec()["keys"])

    own = engine.policy_session(0, 4)
    tracker.update(own.flow_snapshot())
    own.select(keys.index("UNIT:PASS"))
    own.select(keys.index("MARKET:STOP"))
    tracker.record_own_flow(own.own_market_flow_bounds())
    engine.step(
        own.action(),
        {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_PRODUCT", "WHEAT", 3]],
        },
    )

    own = engine.policy_session(0, 4)
    lower, upper = tracker.update(own.flow_snapshot())
    hidden = engine.observation(1)["private"]
    actual = np.asarray(
        [_product_holdings(hidden, product) for product in products], dtype=np.int64
    )
    assert np.all(lower <= actual)
    assert np.all(actual <= upper)
    assert upper[products.index("WHEAT")] == actual[products.index("WHEAT")]

    own.select(keys.index("UNIT:PASS"))
    own.select(keys.index("MARKET:STOP"))
    tracker.record_own_flow(own.own_market_flow_bounds())
    engine.step(
        own.action(),
        {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["SELL", "WHEAT", 2]],
        },
    )
    own = engine.policy_session(0, 4)
    lower, upper = tracker.update(own.flow_snapshot())
    hidden = engine.observation(1)["private"]
    actual = np.asarray(
        [_product_holdings(hidden, product) for product in products], dtype=np.int64
    )
    assert np.all(lower <= actual)
    assert np.all(actual <= upper)


def test_opponent_inventory_upper_bound_includes_visible_fertilizer_collection() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(seed=31, configuration={"episodeSteps": 20, "turnsPerDay": 4})
    products = list(native.game_rules()["products"])
    fertilizer = products.index("FERTILIZER")
    tracker = OpponentInventoryBounds(len(products))
    keys = list(native.action_codec_spec()["keys"])
    own_pass = _pass_action()
    opponent_setup = {
        0: {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_ANIMAL", "GOOSE", 1]],
        },
        1: {"farmer": ["PICKUP", "GOOSE", 1], "hands": [], "market": []},
        2: {"farmer": ["BUILD_COOP"], "hands": [], "market": []},
        3: {"farmer": ["PLACE", "GOOSE", 1], "hands": [], "market": []},
        4: {"farmer": ["COLLECT_FERTILIZER"], "hands": [], "market": []},
    }

    for step in range(5):
        session = engine.policy_session(0, 4)
        tracker.update(session.flow_snapshot())
        session.select(keys.index("UNIT:PASS"))
        session.select(keys.index("MARKET:STOP"))
        tracker.record_own_flow(session.own_market_flow_bounds())
        engine.step(own_pass, opponent_setup.get(step, own_pass))

    session = engine.policy_session(0, 4)
    lower, upper = tracker.update(session.flow_snapshot())
    hidden = engine.observation(1)["private"]
    actual = _product_holdings(hidden, "FERTILIZER")
    assert actual == 1
    assert int(lower[fertilizer]) <= actual <= int(upper[fertilizer])
    assert int(upper[fertilizer]) == actual
