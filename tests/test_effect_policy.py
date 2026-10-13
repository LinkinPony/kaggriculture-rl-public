import numpy as np
import pytest
import torch

from kagg_revue.policy.effects import (
    EffectActorCritic,
    EffectArchitecture,
    EffectPolicy,
    NativeEffectContract,
    tensor_state_from_native,
)
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet


def _policy(native: object, *, board_size: int = 2) -> EffectPolicy:
    encoder = native.actor_encoder_spec()
    contract = NativeEffectContract.from_spec(
        native.effect_policy_spec(),
        board_size=board_size,
    )
    architecture = EffectArchitecture.from_contract(
        contract,
        item_count=int(encoder["num_items"]),
        unit_limit=4,
        maximum_market_orders=2,
        context_width=16,
        model_width=16,
        feedforward_width=32,
        attention_heads=2,
        state_layers=1,
    )
    return EffectPolicy(architecture)


def test_effect_pointer_scores_complete_native_candidate_batches() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 5,
        "maxMarketOrdersPerTurn": 2,
    }
    engines = [native.Engine(seed, configuration) for seed in (11, 13)]
    sessions = [native.AtomicEffectSession(configuration, 4, 8) for _ in engines]
    sessions[1].select(engines[1], 1, 0)
    payload = native.effect_policy_observations_batch(
        sessions,
        engines,
        np.asarray([0, 1], dtype=np.int64),
        workers=1,
    )
    state = tensor_state_from_native(payload, "cpu")
    policy = _policy(native)
    context = torch.randn(2, policy.architecture.context_width)
    tiles = torch.randn(
        2,
        policy.architecture.tile_count,
        policy.architecture.context_width,
    )

    output = policy(context, tiles, state)

    assert output.candidate_logits.shape == state.candidate_mask.shape
    assert output.outcome_logits.shape == (2, 3)
    assert torch.isfinite(output.candidate_logits[state.candidate_mask]).all()
    assert torch.isneginf(output.candidate_logits[~state.candidate_mask]).all()
    assert bool(((output.value >= -1.0) & (output.value <= 1.0)).all())


def test_ranked_work_selection_reuses_logits_under_each_native_mask() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 8,
        "maxMarketOrdersPerTurn": 2,
    }
    engine = native.Engine(17, configuration)
    engine.step({"farmer": ["PASS"], "market": [["HIRE"]]}, {})
    session = native.AtomicEffectSession(configuration, 4, 8)
    players = np.asarray([0], dtype=np.int64)
    first_payload = native.effect_policy_observations_batch(
        [session], [engine], players, workers=1
    )
    first = tensor_state_from_native(first_payload, "cpu")
    policy = _policy(native)
    context = torch.randn(1, policy.architecture.context_width)
    tiles = torch.randn(
        1,
        policy.architecture.tile_count,
        policy.architecture.context_width,
    )
    output = policy(context, tiles, first)
    fields = np.asarray(first_payload["candidate_fields"])[0]
    kinds = native.effect_policy_spec()["request_kinds"]
    stage = int(np.flatnonzero(fields[:, 0] == kinds["STAGE"])[0])
    session.select(engine, 0, stage)
    second_payload = native.effect_policy_observations_batch(
        [session], [engine], players, workers=1
    )
    second_mask = torch.as_tensor(second_payload["candidate_mask"], dtype=torch.bool)

    selection = policy.select_output(
        output,
        sample=False,
        candidate_mask=second_mask,
    )
    expected = output.candidate_logits.masked_fill(~second_mask, -torch.inf)
    expected_probability = torch.softmax(expected.float(), dim=-1).gather(
        1, selection.indices[:, None]
    )

    np.testing.assert_array_equal(
        first_payload["candidate_fields"], second_payload["candidate_fields"]
    )
    np.testing.assert_array_equal(
        first_payload["candidate_features"], second_payload["candidate_features"]
    )
    assert not bool(second_mask[0, stage])
    assert bool(second_mask[0, selection.indices.item()])
    torch.testing.assert_close(
        selection.log_probability,
        expected_probability.squeeze(1).log(),
    )
    torch.testing.assert_close(selection.value, output.value)


def test_effect_candidate_bucketing_preserves_policy_results() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {
        "boardSize": 2,
        "episodeSteps": 5,
        "maxMarketOrdersPerTurn": 2,
    }
    engines = [native.Engine(seed, configuration) for seed in (19, 23)]
    sessions = [native.AtomicEffectSession(configuration, 4, 8) for _ in engines]
    sessions[1].select(engines[1], 1, 0)
    payload = native.effect_policy_observations_batch(
        sessions,
        engines,
        np.asarray([0, 1], dtype=np.int64),
        workers=1,
    )
    state = tensor_state_from_native(payload, "cpu")
    policy = _policy(native).eval()
    context = torch.randn(2, policy.architecture.context_width)
    tiles = torch.randn(
        2,
        policy.architecture.tile_count,
        policy.architecture.context_width,
    )
    counts = torch.as_tensor(payload["candidate_counts"])

    with torch.inference_mode():
        eager = policy(context, tiles, state)
        bucketed = policy.forward_bucketed(context, tiles, state, counts)

    torch.testing.assert_close(bucketed.candidate_logits, eager.candidate_logits)
    torch.testing.assert_close(bucketed.outcome_logits, eager.outcome_logits)


def test_effect_actor_sequence_reconstructs_incremental_turn_context() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    encoder = native.actor_encoder_spec()
    codec = native.action_codec_spec()
    architecture = ActorArchitecture(
        board_shape=(2, int(encoder["board_channels"]), 2, 2),
        unit_shape=(2, 4, int(encoder["unit_feat"])),
        global_features=int(encoder["global_feat"]),
        model_width=16,
        entity_width=8,
        attention_heads=2,
        feedforward_width=32,
        latent_tokens=2,
        scene_layers=1,
        temporal_layers=1,
        action_layers=1,
        max_history=2,
        max_decisions=4,
        unit_action_tokens=int(codec["unit_tokens"]),
        market_action_tokens=len(codec["keys"]) - int(codec["unit_tokens"]),
        maximum_quantity=8,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
        strategy_tokens=2,
        strategy_version="gru-v1",
    )
    model = EffectActorCritic(TurnPolicyNet(architecture), _policy(native)).eval()
    configuration = {
        "boardSize": 2,
        "episodeSteps": 5,
        "maxMarketOrdersPerTurn": 2,
    }
    engine = native.Engine(29, configuration)
    session = native.AtomicEffectSession(configuration, 4, 8)
    payload = native.effect_policy_observations_batch(
        [session],
        [engine],
        np.asarray([0], dtype=np.int64),
        workers=1,
    )
    state = tensor_state_from_native(payload, "cpu")
    board = torch.randn(1, *architecture.board_shape)
    units = torch.randn(1, *architecture.unit_shape)
    global_features = torch.randn(1, architecture.global_features)
    previous_actions = torch.zeros(1, 4, dtype=torch.long)
    previous_quantities = torch.zeros_like(previous_actions)
    previous_mask = torch.zeros_like(previous_actions, dtype=torch.bool)

    with torch.inference_mode():
        context, tiles, strategy, _history, _strategy_state = model.start_turn(
            board,
            units,
            global_features,
            previous_actions,
            previous_quantities,
            previous_mask,
            None,
            None,
            None,
        )
        incremental = model.effects(context, tiles, state, strategy)
        sequence = model.evaluate_sequences(
            board[:, None],
            units[:, None],
            global_features[:, None],
            previous_actions[:, None],
            previous_quantities[:, None],
            torch.ones((1, 1), dtype=torch.bool),
            previous_mask[:, None],
            state,
            torch.zeros(1, dtype=torch.long),
            torch.zeros(1, dtype=torch.long),
            None,
        )

    torch.testing.assert_close(sequence.candidate_logits, incremental.candidate_logits)
    torch.testing.assert_close(sequence.outcome_logits, incremental.outcome_logits)
