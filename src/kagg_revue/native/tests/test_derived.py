"""Complete v5b feature boundaries, scenario semantics and weight reuse."""

import math
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.native import _revue_core as native
from kagg_revue.native.derived_fields import (
    BOARD_FIELDS,
    GLOBAL_FIELDS,
    PRODUCT_FIELDS,
    UNIT_FIELDS,
)
from kagg_revue.native.tests.test_agronomy import _tile
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.encoder import ContextEncoder
from kagg_revue.policy.grounded.migration import legacy_contract, migrate_policy
from kagg_revue.policy.spatial.model import Policy


def _layout() -> ContractLayout:
    config = Experiment(
        output_dir=Path("outputs/learning/derived-test"),
        architecture="grounded-v2",
        agronomy=True,
        derived=True,
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


def _encode(observation: dict[str, Any], step: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    layout = _layout()
    session = native.ContractSession({}, 4)
    for turn in range(step + 1):
        observation.update(step=turn, day=turn // 24, hour=turn % 24)
        session.update(observation)
    array = np.empty((1, layout.observation.features), np.float16)
    session.observe_into(array)
    offset = (
        layout.observation.features
        - layout.observation.support_features
        - layout.observation.derived_features
    )
    supplement = array[0, offset : -layout.observation.support_features].astype(float)
    assert np.isfinite(supplement).all()
    return (
        supplement[:24],
        supplement[24:4024].reshape(2, 100, 20),
        supplement[-864:].reshape(9, 96),
    )


def _count(value: float) -> float:
    return math.copysign(math.log1p(abs(value)) / math.log(1025), value)


def test_complete_schema_and_exact_prefix_migration() -> None:
    """All four supplements train without changing existing weights or observation bytes."""
    torch.set_num_threads(1)
    assert tuple(map(len, (GLOBAL_FIELDS, BOARD_FIELDS, UNIT_FIELDS, PRODUCT_FIELDS))) == (
        24,
        20,
        16,
        96,
    )
    layout = _layout()
    previous = legacy_contract(layout)
    actor = Policy.from_layout(previous)
    expanded, report = migrate_policy(actor, layout)
    assert isinstance(actor.encoder, ContextEncoder)
    assert isinstance(expanded.encoder, ContextEncoder)
    session = native.ContractSession({}, 4)
    obs = native.Engine(7).observation(0)
    obs["farms"][0]["tiles"][0][0] = _tile("COW")
    session.update(obs)
    old = np.empty((1, previous.observation.features), np.float16)
    new = np.empty((1, layout.observation.features), np.float16)
    session.observe_into(old)
    session.observe_into(new)
    prefix = old.shape[-1] - previous.observation.support_features
    np.testing.assert_array_equal(old[:, :prefix], new[:, :prefix])
    np.testing.assert_array_equal(old[:, prefix:], new[:, -previous.observation.support_features :])
    assert torch.equal(
        actor.encoder(torch.from_numpy(old)), expanded.encoder(torch.from_numpy(new))
    )
    assert report["added_parameters"] == 16 * (24 + 20 + 16 + 96)
    expanded.encoder(torch.from_numpy(new))[..., 0].sum().backward()
    assert expanded.encoder.supplement is not None
    for parameter in expanded.encoder.supplement.parameters():
        assert parameter.grad is not None and parameter.grad.abs().sum() > 0
    with pytest.raises(ValueError, match="exact v4 contract"):
        migrate_policy(actor, replace(layout, network=replace(layout.network, expansion=4)))


def test_shop_phase_multiplicity_uncertainty_and_terminal_cutoff() -> None:
    """Duplicate pet cafes each drain two carrots; the last action has no phantom next day."""
    obs = native.Engine(7).observation(0)
    obs["town"]["unlocked_shops"] = ["PET_CAFE", "PET_CAFE"]
    _, _, products = _encode(obs, 0)
    assert products[1, 0] == pytest.approx(_count(25), abs=3e-4)
    assert products[8, 0] == products[8, 66] == products[8, 67] == 0
    assert products[1, 71] == 2 / 8
    assert products[0, 66] > 0 and products[0, 67] > 0
    globals_, _, products = _encode(obs, 718)
    assert globals_[:6] == pytest.approx(np.full(6, 1 / 719), abs=1e-6)
    assert not products[:, [0, 8, 16, 24, 32, 40, 66, 67, 68, 69]].any()
    assert not products[:, [61, 62]].any()


def test_feed_reserve_private_stock_and_night_overflow() -> None:
    """Feed counts survive a day boundary; nonproducts still consume shed capacity."""
    obs = native.Engine(7).observation(0)
    obs["farms"][0]["tiles"][0][0] = _tile("COW")
    obs["private"]["shed"]["GOOSE"] = 99
    obs["private"]["inventories"] = [{"CARROT": 3, "WHEAT": 2}]
    _, boards, products = _encode(obs, 23)
    assert products[0, 77] == pytest.approx(_count(3), abs=3e-4)
    assert products[0, 78] == pytest.approx(_count(-1), abs=3e-4)
    assert products[1, 76] == pytest.approx(_count(2), abs=3e-4)
    assert products[0, 76] == pytest.approx(_count(2), abs=3e-4)
    assert boards[0, 0, 13] < 0 and boards[0, 0, 19] == 1
    assert not boards[1, :, 19].any()
    _, _, products = _encode(obs, 718)
    assert not products[:, 76].any()


def test_intervention_maturity_and_terminal_value() -> None:
    """Water can raise a mature one-off yield; late care cannot produce future goods."""
    obs = native.Engine(7).observation(0)
    obs["farms"][0]["tiles"][0][0] = _tile("WHEAT")
    _, boards, _ = _encode(obs, 48)
    assert boards[0, 0, 0] == 1 and boards[0, 0, 1] > 0
    obs["farms"][0]["tiles"][0][0] = _tile("COW")
    _, boards, _ = _encode(obs, 718)
    assert boards[0, 0, 6] == 1 and boards[0, 0, 7] == boards[0, 0, 8] == 0


def test_both_seats_native_replay_visibility_and_rolling_history() -> None:
    """Engine-held opponent private state cannot change any seat-visible v5b field."""
    layout = _layout()
    batch = native.SelfPlayBatch({}, [7], [0], 4, 1, list(layout.observation.quantities))
    actual = np.empty((2, layout.observation.features), np.float16)
    expected = np.empty_like(actual)
    sessions = [native.ContractSession({}, 4) for _ in range(2)]
    plans = np.zeros((2, layout.factors), np.int64)
    plans[0, layout.work_factors : layout.work_factors + 2] = [18, 2]
    plans[1, layout.work_factors : layout.work_factors + 2] = [16, 4]
    for turn in range(101):
        batch.observe_selfplay_into(actual)
        for seat, session in enumerate(sessions):
            session.update(batch.observation(0, seat))
            session.observe_into(expected[seat : seat + 1])
        np.testing.assert_array_equal(actual, expected)
        assert np.isfinite(actual).all()
        batch.advance_programs(plans if turn == 0 else np.zeros_like(plans), 1, 1, True)
