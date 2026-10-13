"""Production boundaries, legacy compatibility and public/private feature parity."""

import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.native import _revue_core as native
from kagg_revue.native.agronomy import BOARD_FIELDS, GLOBAL_FIELDS, PRODUCT_FIELDS, UNIT_FIELDS
from kagg_revue.policy.contracts import ContractLayout

BOARD = 2 * 100 * len(BOARD_FIELDS)
PRODUCTS = 9 * len(PRODUCT_FIELDS)
UNITS = 2 * 4 * len(UNIT_FIELDS)
TOTAL = BOARD + PRODUCTS + len(GLOBAL_FIELDS) + UNITS


def _layout() -> ContractLayout:
    config = Experiment(
        output_dir=Path("outputs/learning/agronomy-test"),
        architecture="grounded-v2",
        agronomy=True,
        decision_interval=1,
        width=16,
        depth=1,
        critic_width=16,
        critic_depth=1,
        unit_limit=4,
        quantity_max=100,
        quantity_extra=(),
    )
    return ContractLayout.resolve(runtime_settings(config))


def _tile(kind: str, **values: Any) -> dict[str, Any]:
    if kind in {"WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"}:
        return dict(
            kind="PLANT",
            crop=kind,
            planted_day=0,
            yield_units=1,
            watered_today=False,
            consecutive_unwatered=0,
            max_lifespan_step=-1,
            fertilized_until_day=-1,
            **values,
        )
    return dict(
        kind="COOP" if kind == "GOOSE" else "PASTURE",
        animal=kind,
        placed_day=0,
        yield_units=0,
        fed_today=False,
        consecutive_unfed=0,
        cared_today=False,
        fertilizer_available=True,
        pending_care_bonus=0,
        **values,
    )


@dataclass(frozen=True)
class Block:
    """Decoded v4 agronomy block for the north-west corner tile of the own farm."""

    tile: dict[str, float]
    products: np.ndarray
    globals: dict[str, float]
    units: np.ndarray

    def product(self, index: int, name: str) -> float:
        """Read one named product field."""
        return float(self.products[index, PRODUCT_FIELDS.index(name)])


def _decode(packed: np.ndarray, layout: ContractLayout) -> Block:
    start = layout.observation.features - layout.observation.support_features - TOTAL
    segment = packed[start : start + TOTAL].astype(float)
    tile = segment[: len(BOARD_FIELDS)]
    products = segment[BOARD : BOARD + PRODUCTS].reshape(9, len(PRODUCT_FIELDS))
    globals_ = segment[BOARD + PRODUCTS : BOARD + PRODUCTS + len(GLOBAL_FIELDS)]
    units = segment[BOARD + PRODUCTS + len(GLOBAL_FIELDS) :].reshape(2, 4, len(UNIT_FIELDS))
    return Block(
        dict(zip(BOARD_FIELDS, tile, strict=True)),
        products,
        dict(zip(GLOBAL_FIELDS, globals_, strict=True)),
        units,
    )


def _encode(tile: dict[str, Any] | None, step: int, **updates: Any) -> Block:
    layout = _layout()
    observation = native.Engine(7).observation(0)
    observation["farms"][0]["tiles"][0][0] = tile
    for key, value in updates.items():
        for field, entries in value.items():
            observation[key][field].update(entries)
    session = native.ContractSession({}, 4)
    for turn in range(step + 1):
        observation.update(step=turn, day=turn // 24, hour=turn % 24)
        session.update(observation)
    packed = np.empty((1, layout.observation.features), np.float16)
    session.observe_into(packed)
    return _decode(packed[0], layout)


def test_maturity_and_watering_effects_are_separate() -> None:
    """An immature wheat has stock but is not harvestable; bonus watering is causal."""
    block = _encode(_tile("WHEAT"), 0)
    assert block.tile["harvestable"] == 0 and block.tile["water_immediate_yield_gain"] == 0
    assert block.product(0, "own_harvestable_quantity") == 0
    block = _encode(_tile("WHEAT"), 48)
    assert block.tile["harvestable"] == 1 and block.tile["watering_bonus_window"] == 1
    assert block.tile["water_immediate_yield_gain"] == pytest.approx(1 / 6, abs=1e-4)
    assert block.tile["fertilize_then_water_extra_gain"] == pytest.approx(1 / 6, abs=1e-4)


@pytest.mark.parametrize("crop,last_day", [("TOMATO", 11), ("STRAWBERRY", 16)])
def test_ongoing_crops_expose_finite_production(crop: str, last_day: int) -> None:
    """No fifth production event is invented after four scheduled batches."""
    block = _encode(_tile(crop), 0)
    assert block.tile["remaining_production_events"] == pytest.approx(4 / 30, abs=1e-4)
    assert block.tile["has_decay_deadline"] == 1
    block = _encode(_tile(crop), last_day * 24)
    assert block.tile["next_production_turns"] == 0
    assert block.tile["remaining_production_events"] == 0


def test_cow_capacity_bonus_order_and_feeding_rescue() -> None:
    """Today's care banks after production, and feeding preserves existing bonuses."""
    tile = _tile("COW")
    tile.update(yield_units=5, pending_care_bonus=2, cared_today=True, consecutive_unfed=1)
    block = _encode(tile, 7 * 24 + 23)
    assert block.tile["next_maintained_production"] == 0.5
    assert block.tile["next_production_overflow_without_harvest"] == pytest.approx(2 / 6, abs=1e-4)
    assert block.tile["maintenance_prevents_day_end_loss"] == 1
    assert block.tile["day_end_maintained_yield_delta"] == pytest.approx(1 / 6, abs=1e-4)
    tile["cared_today"] = False
    block = _encode(tile, 7 * 24 + 23)
    assert block.tile["new_care_payout_turns"] == pytest.approx(49 / 719, abs=1e-4)
    block = _encode(tile, 718)
    assert block.tile["new_care_can_pay_before_end"] == 0
    assert block.tile["next_production_turns"] == 0


def test_geometry_labor_and_resource_reachability() -> None:
    """Distances come from the farmer at (4, 4); wheat in the shed enables a feed trip."""
    block = _encode(_tile("COW"), 0)
    assert block.tile["nearest_unit_distance"] == pytest.approx(8 / 20, abs=1e-3)
    assert block.tile["shed_distance"] == pytest.approx(8 / 20, abs=1e-3)
    assert block.tile["reachable_before_day_end"] == 1
    assert block.tile["has_feed_carrier"] == 0 and block.tile["shed_has_wheat"] == 0
    assert block.globals["own_due_task_tiles"] == pytest.approx(1 / 100, abs=1e-4)
    assert block.globals["own_unit_turns_left"] == pytest.approx(math.log1p(24) / 7, abs=1e-3)
    assert block.globals["own_travel_estimate"] == pytest.approx(math.log1p(8) / 8, abs=1e-3)
    farmer = block.units[0, 0]
    assert farmer[UNIT_FIELDS.index("has_needs_feed")] == 1
    assert farmer[UNIT_FIELDS.index("nearest_needs_feed")] == pytest.approx(8 / 20, abs=1e-3)
    assert farmer[UNIT_FIELDS.index("due_tiles_north")] == pytest.approx(1 / 16, abs=1e-4)
    assert farmer[UNIT_FIELDS.index("due_tiles_east")] == 0
    assert block.units[1].sum() == block.units[1, 0, UNIT_FIELDS.index("has_plantable")] == 1
    block = _encode(_tile("COW"), 23, private={"shed": {"WHEAT": 3}})
    assert block.tile["reachable_before_day_end"] == 0
    assert block.tile["shed_has_wheat"] == 1
    assert block.tile["feed_via_shed_distance"] == pytest.approx(9 / 40, abs=1e-3)
    assert block.globals["farm_wheat_stored"] == pytest.approx(math.log1p(3) / 5, abs=1e-3)
    assert block.globals["farm_feed_shortfall"] == 0


def test_market_impact_follows_the_official_curve() -> None:
    """Own sales walk down the curve; a glut above the anchor exposes recovery time."""
    block = _encode(None, 0)
    assert 0 < block.product(3, "sell_average_price_64") < block.product(3, "sell_average_price_2")
    assert block.product(3, "sell_average_price_2") <= 0.25
    assert block.product(3, "market_glutted") == 0 and block.product(3, "glut_recovery_days") == 0
    assert (
        block.product(0, "buy_average_price_10") > 0.25
        and block.product(1, "buy_average_price_10") == 0
    )
    assert block.product(8, "town_consumption_per_day") == 0
    inventory = {"CARROT": 10010}
    block = _encode(None, 0, market={"inventory": inventory})
    assert block.product(1, "market_glutted") == 1
    assert block.product(1, "glut_recovery_days") == pytest.approx(10 / 30, abs=1e-3)
    assert block.product(1, "units_until_price_below_75pct") < block.product(
        1, "units_until_price_floor"
    )


def test_public_ledger_attributes_visible_harvests_and_market_flow() -> None:
    """A yield drop on either farm and a market inventory rise are public estimates."""
    layout = _layout()
    session = native.ContractSession({}, 4)
    observation = native.Engine(7).observation(0)
    observation["farms"][0]["tiles"][0][0] = {**_tile("WHEAT"), "yield_units": 3}
    observation["farms"][1]["tiles"][0][0] = {
        **_tile("TOMATO"),
        "yield_units": 2,
        "planted_day": -6,
    }
    for turn in range(49):
        observation.update(step=turn, day=turn // 24, hour=turn % 24)
        session.update(observation)
    observation["farms"][0]["tiles"][0][0] = None
    observation["farms"][1]["tiles"][0][0]["yield_units"] = 0
    observation["market"]["inventory"]["WHEAT"] += 3
    observation.update(step=49, hour=1)
    session.update(observation)
    packed = np.empty((1, layout.observation.features), np.float16)
    session.observe_into(packed)
    block = _decode(packed[0], layout)
    assert block.product(0, "own_harvested_cumulative") == pytest.approx(
        math.log1p(3) / 5, abs=1e-3
    )
    assert block.product(2, "opponent_harvested_cumulative") == pytest.approx(
        math.log1p(2) / 5, abs=1e-3
    )
    # The frozen inventory absorbed three center ticks (steps 0, 24, 48) as player flow.
    assert block.product(0, "players_net_market_flow_cumulative") == pytest.approx(
        math.log1p(6 / 400) / 2, abs=1e-4
    )
    assert block.product(1, "players_net_market_flow_cumulative") == pytest.approx(
        math.log1p(3 / 450) / 2, abs=1e-4
    )


def test_new_features_preserve_legacy_bytes_and_model_gradients() -> None:
    """V2 stays byte-identical, while every new projection learns from V4 inputs."""
    torch.set_num_threads(1)
    layout = _layout()
    old = replace(
        layout.observation,
        version="grounded-production-context-v2",
        context_features=1800,
        agronomy_board_features=0,
        agronomy_product_features=0,
        agronomy_global_features=0,
        agronomy_unit_features=0,
    )
    session = native.ContractSession({}, 4)
    observation = native.Engine(7).observation(0)
    observation["farms"][0]["tiles"][0][0] = _tile("WHEAT")
    session.update(observation)
    new_array = np.empty((1, layout.observation.features), np.float16)
    old_array = np.empty((1, old.features), np.float16)
    session.observe_into(new_array)
    session.observe_into(old_array)
    prefix = old.features - old.support_features
    np.testing.assert_array_equal(new_array[:, :prefix], old_array[:, :prefix])
    np.testing.assert_array_equal(
        new_array[:, -old.support_features :], old_array[:, -old.support_features :]
    )
    actor = random_policy(
        layout, 17, Experiment(output_dir=Path("outputs/learning/test")).exploration
    )
    encoded = actor.encoder(torch.from_numpy(new_array))
    assert encoded.shape == (1, 230, 16)
    encoded[..., 0].sum().backward()
    projections = (
        (actor.encoder.board, len(BOARD_FIELDS)),
        (actor.encoder.products, len(PRODUCT_FIELDS)),
        (actor.encoder.units, len(UNIT_FIELDS) + 8 + len(BOARD_FIELDS)),
        (actor.encoder.global_state[0], len(GLOBAL_FIELDS)),
    )
    for projection, extra in projections:
        assert isinstance(projection, torch.nn.Linear) and projection.weight.grad is not None
        assert projection.weight.grad[:, -extra:].abs().sum() > 0


def test_native_batch_equals_seat_visible_encoding() -> None:
    """Hidden opponent inventory is absent and both seats use the same native ABI."""
    layout = _layout()
    batch = native.SelfPlayBatch({}, [7], [0], 4, 1, list(layout.observation.quantities))
    actual = np.empty((2, layout.observation.features), np.float16)
    expected = np.empty_like(actual)
    sessions = [native.ContractSession({}, 4) for _ in range(2)]
    plans = np.zeros((2, layout.factors), np.int64)
    # Buy different hidden goods on each side, then verify native/public parity.
    plans[0, layout.work_factors : layout.work_factors + 2] = [18, 2]
    plans[1, layout.work_factors : layout.work_factors + 2] = [16, 4]
    for turn in range(25):
        batch.observe_selfplay_into(actual)
        for seat, session in enumerate(sessions):
            session.update(batch.observation(0, seat))
            session.observe_into(expected[seat : seat + 1])
        np.testing.assert_array_equal(actual, expected)
        assert np.isfinite(actual).all()
        batch.advance_programs(plans if turn == 0 else np.zeros_like(plans), 1, 1, True)
