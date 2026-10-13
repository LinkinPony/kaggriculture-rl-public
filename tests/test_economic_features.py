from __future__ import annotations

from typing import Any

import numpy as np
import pytest
import torch

from kagg_revue.policy.economics import (
    CANDIDATE_FEATURES,
    ECONOMIC_FEATURE_VERSION,
    PREFIX_FEATURES,
    QUANTITY_FEATURES,
    TURN_FEATURES,
    EconomicFeatureCompiler,
    EconomicStateLayout,
)
from kagg_revue.policy.economics.pricing import market_price
from kagg_revue.policy.economics.transition import apply_selection
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.rl.outcome import OutcomeActorCritic


def _native_state(*, unit_limit: int = 1) -> tuple[Any, torch.Tensor, torch.Tensor]:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(
        seed=17,
        configuration={
            "boardSize": 2,
            "episodeSteps": 8,
            "maxMarketOrdersPerTurn": 3,
        },
    )
    session = engine.policy_session(0, unit_limit)
    state = torch.from_numpy(np.asarray(session.gpu_state(), dtype=np.int64))[None]
    global_features = torch.from_numpy(
        np.asarray(session.encode()[2], dtype=np.float32)
    )[None]
    return native, state, global_features


def _architecture(*, economic: bool) -> ActorArchitecture:
    return ActorArchitecture(
        board_shape=(2, 1, 2, 2),
        unit_shape=(2, 1, 1),
        global_features=82,
        model_width=8,
        entity_width=4,
        attention_heads=1,
        feedforward_width=16,
        latent_tokens=2,
        scene_layers=0,
        temporal_layers=1,
        action_layers=1,
        max_history=2,
        max_decisions=2,
        unit_action_tokens=44,
        market_action_tokens=23,
        maximum_quantity=128,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
        economic_feature_version=ECONOMIC_FEATURE_VERSION if economic else None,
        economic_turn_features=TURN_FEATURES if economic else 0,
        economic_prefix_features=PREFIX_FEATURES if economic else 0,
        economic_candidate_features=CANDIDATE_FEATURES if economic else 0,
        economic_quantity_features=QUANTITY_FEATURES if economic else 0,
    )


def test_economic_quantity_features_clip_commit_and_mark_conditional_cash() -> None:
    native, state, _ = _native_state()
    layout = EconomicStateLayout.from_spec(
        native.gpu_policy_state_spec(2, 1),
        board_size=2,
        unit_limit=1,
    )
    state[:, layout.shed] = 3
    state[:, 8] = 3
    compiler = EconomicFeatureCompiler(layout)

    facts = compiler.quantity_features(state, torch.tensor([46]))

    assert facts.shape == (1, 128, QUANTITY_FEATURES)
    assert facts[0, :3, 3].tolist() == [1.0, 1.0, 1.0]
    assert facts[0, 3, 3].item() == 0.0
    assert facts[0, :, 5].eq(1.0).all()
    assert facts[0, 2, 8].item() == 0.0


def test_market_price_projection_matches_native_rule_engine() -> None:
    native, state, _ = _native_state()
    engine = native.Engine(seed=41)
    layout = EconomicStateLayout.from_spec(
        native.gpu_policy_state_spec(2, 1),
        board_size=2,
        unit_limit=1,
    )
    inventories = torch.arange(7_000, 13_001, dtype=torch.float64)[None]
    names = list(engine.configuration["marketParams"])

    for product, name in enumerate(names):
        projected = market_price(
            state,
            torch.tensor([product]),
            inventories,
            layout,
        )[0].long()
        expected = torch.tensor(
            [engine.market_price(name, inventory) for inventory in range(7_000, 13_001)]
        )
        torch.testing.assert_close(projected, expected, rtol=0, atol=0)


def test_conditional_market_projection_propagates_through_prefix() -> None:
    native, state, _ = _native_state()
    layout = EconomicStateLayout.from_spec(
        native.gpu_policy_state_spec(2, 1),
        board_size=2,
        unit_limit=1,
    )
    compiler = EconomicFeatureCompiler(layout)
    market_phase = torch.tensor([1])
    state[:, 4] = 1

    before = compiler.candidate_features(state, market_phase)
    assert before[0, 46, 4].item() == 1.0
    assert before[0, 55, 3].item() == 1.0
    apply_selection(
        state,
        torch.tensor([46]),
        torch.tensor([1]),
        torch.tensor([True]),
        layout,
    )

    prefix = compiler.prefix_features(state, market_phase)
    after = compiler.candidate_features(state, market_phase)
    seed_quantities = compiler.quantity_features(state, torch.tensor([55]))
    assert prefix[0, -2:].tolist() == [0.0, 1.0]
    assert after[0, 55, 3:5].tolist() == [0.0, 1.0]
    assert seed_quantities[0, :, 5].eq(1.0).all()


def test_torch_unit_prefix_replay_matches_native_policy_session() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(
        seed=23,
        configuration={"boardSize": 2, "episodeSteps": 8},
    )
    observation = engine.observation(0)
    observation["private"]["shed"]["WHEAT"] = 5
    session = native.PolicySession(observation, engine.configuration, 1)
    layout = EconomicStateLayout.from_spec(
        native.gpu_policy_state_spec(2, 1),
        board_size=2,
        unit_limit=1,
    )
    state = torch.from_numpy(np.asarray(session.gpu_state(), dtype=np.int64))[None]

    apply_selection(
        state,
        torch.tensor([5]),
        torch.tensor([3]),
        torch.tensor([True]),
        layout,
    )
    session.select(5, 3)

    np.testing.assert_array_equal(
        state.numpy(),
        np.asarray(session.gpu_state(), dtype=np.int64)[None],
    )


def test_zero_initialized_economic_paths_preserve_actor_and_critic_outputs() -> None:
    _, state, global_features = _native_state()
    torch.manual_seed(31)
    old_actor = TurnPolicyNet(_architecture(economic=False)).eval()
    torch.manual_seed(37)
    new_actor = TurnPolicyNet(_architecture(economic=True)).eval()
    incompatible = new_actor.load_state_dict(old_actor.state_dict(), strict=False)
    assert not incompatible.unexpected_keys
    assert incompatible.missing_keys
    old_model = OutcomeActorCritic(old_actor).eval()
    new_model = OutcomeActorCritic(new_actor).eval()
    outcome_incompatible = new_model.outcome.load_state_dict(
        old_model.outcome.state_dict(),
        strict=False,
    )
    assert not outcome_incompatible.unexpected_keys
    assert outcome_incompatible.missing_keys

    board = torch.randn((1, 1, 2, 1, 2, 2))
    units = torch.randn((1, 1, 2, 1, 1))
    globals_ = global_features[:, None]
    actions = torch.tensor([[[0, 44]]])
    quantities = torch.zeros_like(actions)
    phases = torch.tensor([[[0, 1]]])
    turn_mask = torch.ones((1, 1), dtype=torch.bool)
    decision_mask = torch.ones((1, 1, 2), dtype=torch.bool)
    empty_turn = torch.empty((1, 1, 0, 0))
    empty_turn_mask = torch.empty((1, 1, 0), dtype=torch.bool)
    empty_prefix = torch.empty((1, 1, 2, 0))
    empty_candidates = torch.empty((1, 1, 2, 67, 0))
    skills = torch.full((1, 1), -1, dtype=torch.long)

    with torch.inference_mode():
        old = old_model(
            board,
            units,
            globals_,
            empty_turn,
            empty_turn_mask,
            empty_prefix,
            empty_candidates,
            actions,
            quantities,
            phases,
            turn_mask,
            decision_mask,
            skills,
        )
        new = new_model(
            board,
            units,
            globals_,
            empty_turn,
            empty_turn_mask,
            empty_prefix,
            empty_candidates,
            actions,
            quantities,
            phases,
            turn_mask,
            decision_mask,
            skills,
            state[:, None],
        )

    torch.testing.assert_close(new.policy.action_logits, old.policy.action_logits, rtol=0, atol=0)
    torch.testing.assert_close(
        new.policy.quantity_logits,
        old.policy.quantity_logits,
        rtol=0,
        atol=0,
    )
    torch.testing.assert_close(new.outcome_logits, old.outcome_logits, rtol=0, atol=0)
