from __future__ import annotations

import copy
from typing import Any

import numpy as np
import pytest
import torch
from torch.nn import functional


def _cuda_dependencies() -> tuple[Any, Any]:
    pytest.importorskip("triton")
    if not torch.cuda.is_available():
        pytest.skip("CUDA is required for GPU PolicySession parity")
    native = pytest.importorskip("kagg_revue.native._revue_native")
    return native, torch.device("cuda:0")


def _plant(*, watered: bool = False, mature: bool = False) -> dict[str, object]:
    return {
        "kind": "PLANT",
        "crop": "WHEAT",
        "planted_day": 0,
        "watered_today": watered,
        "consecutive_unwatered": 0,
        "yield_units": 3 if mature else 1,
        "max_lifespan_step": -1,
        "fertilized_until_day": -1,
    }


def _animal(*, fertilizer: bool = False) -> dict[str, object]:
    return {
        "kind": "COOP",
        "animal": "GOOSE",
        "placed_day": 0,
        "yield_units": 2,
        "consecutive_unfed": 0,
        "fed_today": False,
        "cared_today": False,
        "fertilizer_available": fertilizer,
        "pending_care_bonus": 0,
    }


def _session_for_unit_token(native: Any, token: int, keys: list[str]) -> Any:
    engine = native.Engine(
        seed=token + 1,
        configuration={"episodeSteps": 8, "maxMarketOrdersPerTurn": 3},
    )
    observation = copy.deepcopy(engine.observation(0))
    configuration = dict(engine.configuration)
    board_size = int(configuration["boardSize"])
    half = board_size // 2
    farm = observation["farms"][0]
    farm["farmer"] = [half - 1, half - 1]
    item_names = list(observation["private"]["shed"])
    crop_names = list(observation["private"]["seeds"])
    observation["private"]["shed"] = {name: 7 for name in item_names}
    observation["private"]["seeds"] = {name: 7 for name in crop_names}
    observation["private"]["inventories"] = [
        {name: index + 2 for index, name in enumerate(item_names)}
    ]
    key = keys[token]
    tile: object = None
    if key.startswith("UNIT:PLACE") and key.endswith("GOOSE"):
        tile = {"kind": "COOP"}
    elif key.startswith("UNIT:PLACE") and (key.endswith("COW") or key.endswith("SHEEP")):
        tile = {"kind": "PASTURE"}
    elif key in {"UNIT:WATER", "UNIT:FERTILIZE"}:
        tile = _plant()
    elif key == "UNIT:HARVEST":
        observation["step"] = 3 * int(configuration["turnsPerDay"])
        tile = _plant(mature=True)
    elif key == "UNIT:DIG":
        tile = {"kind": "WEED"}
    elif key in {"UNIT:FEED", "UNIT:CARE"}:
        tile = _animal()
    elif key == "UNIT:COLLECT_FERTILIZER":
        tile = _animal(fertilizer=True)
    farm["tiles"][half - 1][half - 1] = tile
    return native.PolicySession(observation, configuration, 1)


def test_economic_replay_matches_every_native_unit_transition() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    from kagg_revue.policy.economics import EconomicStateLayout
    from kagg_revue.policy.economics.transition import apply_selection

    codec = native.action_codec_spec()
    keys = list(codec["keys"])
    unit_tokens = int(codec["unit_tokens"])
    sessions = [_session_for_unit_token(native, token, keys) for token in range(unit_tokens)]
    batch = native.PolicySessionBatch(sessions, workers=8)
    board_size = int(dict(native.Engine(seed=1).configuration)["boardSize"])
    layout = EconomicStateLayout.from_spec(
        native.gpu_policy_state_spec(board_size, 1),
        board_size=board_size,
        unit_limit=1,
    )
    state = torch.from_numpy(np.asarray(batch.gpu_state(), dtype=np.int32))
    selected = torch.arange(unit_tokens, dtype=torch.long)
    quantities = torch.arange(1, unit_tokens + 1, dtype=torch.long)
    active = torch.ones(unit_tokens, dtype=torch.bool)

    apply_selection(state, selected, quantities, active, layout)
    batch.select(selected.numpy(), quantities.numpy(), active.numpy().astype(np.uint8))

    np.testing.assert_array_equal(
        state.numpy(),
        np.asarray(batch.gpu_state(), dtype=np.int32),
    )


def test_gpu_policy_session_matches_every_native_unit_transition() -> None:
    native, device = _cuda_dependencies()
    from kagg_revue.policy.cuda.session import (
        GpuPolicyStateLayout,
        compile_policy_legal,
        select_policy_actions,
    )

    codec = native.action_codec_spec()
    keys = list(codec["keys"])
    unit_tokens = int(codec["unit_tokens"])
    sessions = [_session_for_unit_token(native, token, keys) for token in range(unit_tokens)]
    batch = native.PolicySessionBatch(sessions, workers=8)
    board_size = int(dict(native.Engine(seed=1).configuration)["boardSize"])
    layout = GpuPolicyStateLayout.from_spec(
        native.gpu_policy_state_spec(board_size, 1),
        board_size=board_size,
        unit_limit=1,
    )
    state = torch.from_numpy(np.asarray(batch.gpu_state(), dtype=np.int32)).to(device)
    legal = torch.empty((len(sessions), len(keys)), dtype=torch.bool, device=device)
    phases = torch.empty(len(sessions), dtype=torch.long, device=device)
    decisions = torch.empty(len(sessions), dtype=torch.bool, device=device)

    compile_policy_legal(state, legal, phases, decisions, layout)
    torch.cuda.synchronize(device)
    expected_legal = np.stack(
        [np.asarray(session.legal_mask(), dtype=np.bool_) for session in sessions]
    )
    np.testing.assert_array_equal(legal.cpu().numpy(), expected_legal)
    selected = np.arange(unit_tokens, dtype=np.int64)
    assert expected_legal[np.arange(unit_tokens), selected].all()
    quantities = np.arange(1, unit_tokens + 1, dtype=np.int64)
    active = np.ones(unit_tokens, dtype=np.uint8)
    batch.select(selected, quantities, active)
    select_policy_actions(
        state,
        torch.from_numpy(selected).to(device),
        torch.from_numpy(quantities).to(device),
        layout,
    )
    torch.cuda.synchronize(device)
    np.testing.assert_array_equal(
        state.cpu().numpy(), np.asarray(batch.gpu_state(), dtype=np.int32)
    )

    for market_step in range(3):
        compile_policy_legal(state, legal, phases, decisions, layout)
        torch.cuda.synchronize(device)
        native_phases, native_legal = batch.decision_inputs()
        np.testing.assert_array_equal(phases.cpu().numpy(), native_phases)
        np.testing.assert_array_equal(legal.cpu().numpy(), native_legal)
        active = np.asarray(native_phases) != 2
        if not active.any():
            break
        selected = np.zeros(unit_tokens, dtype=np.int64)
        selected[active] = unit_tokens + (
            np.arange(unit_tokens, dtype=np.int64)[active] % (len(keys) - unit_tokens)
        )
        selected[
            active & ~np.asarray(native_legal[np.arange(unit_tokens), selected], dtype=np.bool_)
        ] = keys.index("MARKET:STOP")
        quantities.fill(market_step + 1)
        batch.select(selected, quantities, active.astype(np.uint8))
        select_policy_actions(
            state,
            torch.from_numpy(selected).to(device),
            torch.from_numpy(quantities).to(device),
            layout,
        )
        torch.cuda.synchronize(device)
        np.testing.assert_array_equal(
            state.cpu().numpy(), np.asarray(batch.gpu_state(), dtype=np.int32)
        )


def test_gpu_hire_mask_tracks_projected_same_turn_capacity() -> None:
    native, device = _cuda_dependencies()
    from kagg_revue.policy.cuda.session import (
        GpuPolicyStateLayout,
        compile_policy_legal,
        select_policy_actions,
    )

    engine = native.Engine(
        seed=37,
        configuration={"episodeSteps": 8, "maxMarketOrdersPerTurn": 4},
    )
    session = engine.policy_session(0, 3)
    keys = list(native.action_codec_spec()["keys"])
    hire = keys.index("MARKET:HIRE")
    session.select(keys.index("UNIT:PASS"))
    board_size = int(engine.configuration["boardSize"])
    layout = GpuPolicyStateLayout.from_spec(
        native.gpu_policy_state_spec(board_size, 3),
        board_size=board_size,
        unit_limit=3,
    )
    state = torch.from_numpy(np.asarray(session.gpu_state(), dtype=np.int32))[None].to(device)
    legal = torch.empty((1, len(keys)), dtype=torch.bool, device=device)
    phases = torch.empty(1, dtype=torch.long, device=device)
    decisions = torch.empty(1, dtype=torch.bool, device=device)
    selected = torch.tensor([hire], dtype=torch.long, device=device)
    quantities = torch.zeros(1, dtype=torch.long, device=device)

    for expected in (True, True, False):
        compile_policy_legal(state, legal, phases, decisions, layout)
        torch.cuda.synchronize(device)
        assert bool(legal[0, hire]) is expected
        assert bool(session.legal_mask()[hire]) is expected
        if expected:
            session.select(hire)
            select_policy_actions(state, selected, quantities, layout)
            torch.cuda.synchronize(device)
            np.testing.assert_array_equal(
                state.cpu().numpy(),
                np.asarray(session.gpu_state(), dtype=np.int32)[None],
            )


def test_cuda_static_history_strategy_matches_eager_recurrence() -> None:
    _, device = _cuda_dependencies()
    from kagg_revue.policy.cuda.history import CudaStaticHistory
    from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet

    architecture = ActorArchitecture(
        board_shape=(2, 3, 2, 2),
        unit_shape=(2, 2, 4),
        global_features=3,
        model_width=16,
        entity_width=8,
        attention_heads=2,
        feedforward_width=24,
        latent_tokens=2,
        scene_layers=1,
        temporal_layers=2,
        action_layers=1,
        max_history=8,
        max_decisions=5,
        unit_action_tokens=4,
        market_action_tokens=3,
        maximum_quantity=7,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
        strategy_tokens=3,
        strategy_version="gru-v1",
    )
    torch.manual_seed(47)
    actor = TurnPolicyNet(architecture).to(device).eval()
    static = CudaStaticHistory(actor, batch=2, dtype=torch.float32)
    previous_actions = torch.zeros((2, 5), dtype=torch.long, device=device)
    previous_quantities = torch.zeros_like(previous_actions)
    previous_mask = torch.zeros_like(previous_actions, dtype=torch.bool)
    history = None
    strategy = None

    with torch.inference_mode():
        for _ in range(4):
            board = torch.randn(2, *architecture.board_shape, device=device)
            units = torch.randn(2, *architecture.unit_shape, device=device)
            globals_ = torch.randn(2, architecture.global_features, device=device)
            scene = actor.scene(
                board,
                units,
                globals_,
                previous_actions,
                previous_quantities,
                previous_mask,
            )
            eager, history, strategy, _ = actor.start_turn(
                board,
                units,
                globals_,
                previous_actions,
                previous_quantities,
                previous_mask,
                history,
                strategy_state=strategy,
            )
            graphable, _ = static.start_turn(scene)
            torch.testing.assert_close(graphable.memory, eager.memory, atol=2e-5, rtol=2e-5)
            torch.testing.assert_close(graphable.strategy, eager.strategy, atol=2e-5, rtol=2e-5)
    assert int(static.position.item()) == 4


def test_fused_cuda_economic_features_and_market_replay_match_cpu() -> None:
    native, device = _cuda_dependencies()
    from kagg_revue.policy.economics import (
        EconomicFeatureCompiler,
        EconomicStateLayout,
    )
    from kagg_revue.policy.economics.transition import apply_selection

    engine = native.Engine(
        seed=43,
        configuration={"boardSize": 2, "episodeSteps": 8},
    )
    layout = EconomicStateLayout.from_spec(
        native.gpu_policy_state_spec(2, 1),
        board_size=2,
        unit_limit=1,
    )
    base = torch.from_numpy(np.asarray(engine.policy_session(0, 1).gpu_state(), dtype=np.int32))[
        None
    ]
    rows = len(native.action_codec_spec()["keys"])
    state = base.repeat(rows, 1).contiguous()
    row = torch.arange(rows, dtype=torch.int32)
    state[:, 5] = 100
    state[:, 8] = row % 80
    state[:, 9] = row * 137 + 50
    state[:, 10] = row % 12
    state[:, 11] = row % 4
    for item in range(12):
        state[:, layout.shed + item] = (row * (item + 3)) % 40
    for product in range(9):
        state[:, layout.market_inventory + product] = 7_000 + (row * 97 + product * 211) % 6_001
    phases = (torch.arange(rows) % 2).long()
    tokens = torch.arange(rows, dtype=torch.long)
    compiler = EconomicFeatureCompiler(layout)

    expected_candidates = compiler.candidate_features(state, phases)
    expected_quantities = compiler.quantity_features(state, tokens)
    actual_candidates = compiler.candidate_features(
        state.to(device),
        phases.to(device),
    ).cpu()
    actual_quantities = compiler.quantity_features(
        state.to(device),
        tokens.to(device),
    ).cpu()
    torch.testing.assert_close(actual_candidates, expected_candidates, rtol=0, atol=2e-6)
    torch.testing.assert_close(actual_quantities, expected_quantities, rtol=0, atol=2e-6)

    market_tokens = torch.arange(
        int(native.action_codec_spec()["unit_tokens"]), rows, dtype=torch.long
    )
    market_state = state[: market_tokens.numel()].clone()
    market_state[:, 4] = 1
    cuda_market_state = market_state.to(device)
    quantities = (torch.arange(market_tokens.numel()) * 17 % 129).long()
    active = torch.ones(market_tokens.numel(), dtype=torch.bool)
    apply_selection(market_state, market_tokens, quantities, active, layout)
    apply_selection(
        cuda_market_state,
        market_tokens.to(device),
        quantities.to(device),
        active.to(device),
        layout,
    )
    torch.cuda.synchronize(device)
    torch.testing.assert_close(cuda_market_state.cpu(), market_state, rtol=0, atol=0)


def test_native_engine_policy_batch_matches_individual_sessions() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {"episodeSteps": 3, "maxMarketOrdersPerTurn": 2}
    engines = [native.Engine(seed=seed, configuration=configuration) for seed in range(4)]
    players = [0, 1, 1, 0]
    sessions = [
        engine.policy_session(player, 2) for engine, player in zip(engines, players, strict=True)
    ]
    expected = native.PolicySessionBatch(sessions, workers=2)
    actual = native.engine_policy_session_batch(engines, players, 2, 2)
    fused = native.engine_policy_turn_inputs(engines, players, 2, 2)
    fused_into = tuple(np.empty_like(value) for value in fused)
    native.engine_policy_turn_inputs_into(
        engines,
        players,
        2,
        2,
        *fused_into,
    )
    compact_into = (
        *(np.empty(value.shape, dtype=np.float16) for value in fused[:2]),
        np.empty_like(fused[2]),
        np.empty_like(fused[3]),
        np.empty(fused[4].shape, dtype=np.int32),
    )
    native.engine_policy_turn_inputs_compact_into(
        engines,
        players,
        2,
        2,
        *compact_into,
    )

    for expected_value, actual_value, fused_value, into_value in zip(
        expected.encode(), actual.encode(), fused[:3], fused_into[:3], strict=True
    ):
        np.testing.assert_array_equal(actual_value, expected_value)
        np.testing.assert_array_equal(fused_value, expected_value)
        np.testing.assert_array_equal(into_value, expected_value)
    for expected_value, compact_value in zip(expected.encode()[:2], compact_into[:2], strict=True):
        np.testing.assert_array_equal(np.asarray(expected_value, dtype=np.float16), compact_value)
    np.testing.assert_array_equal(expected.encode()[2], compact_into[2])
    np.testing.assert_array_equal(actual.gpu_state(), expected.gpu_state())
    np.testing.assert_array_equal(actual.unit_counts(), expected.unit_counts())
    np.testing.assert_array_equal(fused[3], expected.unit_counts())
    np.testing.assert_array_equal(fused[4], expected.gpu_state())
    np.testing.assert_array_equal(fused_into[3], expected.unit_counts())
    np.testing.assert_array_equal(fused_into[4], expected.gpu_state())
    np.testing.assert_array_equal(compact_into[3], expected.unit_counts())
    np.testing.assert_array_equal(compact_into[4], expected.gpu_state())

    compact = actual.encode_compact()
    for full_value, compact_value in zip(actual.encode()[:2], compact[:2], strict=True):
        np.testing.assert_array_equal(np.asarray(full_value, dtype=np.float16), compact_value)
    np.testing.assert_array_equal(actual.encode()[2], compact[2])
    np.testing.assert_array_equal(actual.gpu_state(), actual.gpu_state_compact())

    snapshots = actual.flow_snapshots()
    for name in (
        "market_inventory",
        "town_consumption",
        "opponent_unit_gain_upper",
    ):
        np.testing.assert_array_equal(
            snapshots[name],
            np.stack([session.flow_snapshot()[name] for session in sessions]),
        )
    products = int(native.derived_fact_spec()["products"])
    lower = np.zeros((len(sessions), products), dtype=np.int64)
    upper = np.broadcast_to(np.arange(products, dtype=np.int64), lower.shape).copy()
    batched_facts = actual.turn_facts_batch(lower, upper)
    counts = np.asarray(batched_facts["counts"], dtype=np.int64)
    values = np.asarray(batched_facts["values"])
    for row, session in enumerate(sessions):
        reference = np.asarray(session.turn_facts(lower[row], upper[row]))
        assert counts[row] == reference.shape[0]
        np.testing.assert_array_equal(values[row, : counts[row]], reference)

    keys = list(native.action_codec_spec()["keys"])
    active = np.ones(len(sessions), dtype=np.uint8)
    zero = np.zeros(len(sessions), dtype=np.int64)
    for token in (keys.index("UNIT:PASS"), keys.index("MARKET:STOP")):
        selected = np.full(len(sessions), token, dtype=np.int64)
        actual.select(selected, zero, active)
        expected.select(selected, zero, active)
    np.testing.assert_array_equal(
        actual.own_market_flow_bounds_batch(),
        np.stack([session.own_market_flow_bounds() for session in sessions]),
    )

    individual = [engine.clone() for engine in engines]
    paired_engines = [engine for engine in engines for _ in range(2)]
    paired_players = [player for _ in engines for player in (0, 1)]
    paired = native.engine_policy_turn_inputs(paired_engines, paired_players, 2, 2)
    unit_counts = np.asarray(paired[3], dtype=np.int64).reshape(len(engines), 2)
    decision_counts = unit_counts + 1
    width = int(decision_counts.max())
    tokens = np.zeros((len(engines), 2, width), dtype=np.int64)
    quantities = np.zeros_like(tokens)
    market_stop = int(native.action_codec_spec()["market_stop_token"])
    for environment in range(len(engines)):
        for player in range(2):
            tokens[environment, player, unit_counts[environment, player]] = market_stop
    done = native.engine_step_numeric_batch(
        engines,
        tokens,
        quantities,
        decision_counts,
        unit_counts,
        2,
    )
    for environment, engine in enumerate(individual):
        expected_done = engine.step_numeric(
            tokens[environment],
            quantities[environment],
            decision_counts[environment],
            unit_counts[environment],
        )
        assert bool(done[environment]) is expected_done
        for player in range(2):
            expected_encoded = engine.encode_numeric(player, 2)
            actual_encoded = engines[environment].encode_numeric(player, 2)
            for expected_value, actual_value in zip(
                expected_encoded,
                actual_encoded,
                strict=True,
            ):
                np.testing.assert_array_equal(actual_value, expected_value)


def test_fused_categorical_sampler_matches_inverse_cdf_and_log_probability() -> None:
    _, device = _cuda_dependencies()
    from kagg_revue.policy.cuda.categorical import (
        sample_action,
        sample_masked,
        sample_quantity,
    )

    generator = torch.Generator(device=device).manual_seed(19)
    batch = 257
    action_tokens = 91
    quantity_tokens = 128
    logits = torch.randn(
        (batch, action_tokens),
        dtype=torch.bfloat16,
        device=device,
        generator=generator,
    )
    legal = torch.rand((batch, action_tokens), device=device, generator=generator) > 0.25
    legal[:, 0] = True
    active = torch.rand(batch, device=device, generator=generator) > 0.1
    uniform = torch.rand(batch, device=device, generator=generator)
    tokens = torch.empty(batch, dtype=torch.long, device=device)
    log_probability = torch.empty(batch, dtype=torch.float32, device=device)

    sample_action(logits, legal, active, uniform, tokens, log_probability)
    safe_legal = legal | (
        (~active)[:, None] & (torch.arange(action_tokens, device=device)[None] == 0)
    )
    masked_logits = logits.float().masked_fill(~safe_legal, -torch.inf)
    expected_tokens = (
        (masked_logits.softmax(dim=-1).cumsum(dim=-1) <= uniform[:, None])
        .sum(dim=-1)
        .clamp_max(action_tokens - 1)
    )
    expected_log_probability = masked_logits.log_softmax(dim=-1).gather(1, tokens[:, None])[:, 0]

    masked_tokens, masked_log_probability = sample_masked(logits, legal, uniform)
    masked_reference = logits.float().masked_fill(~legal, -torch.inf)
    expected_masked_tokens = (
        (masked_reference.softmax(dim=-1).cumsum(dim=-1) <= uniform[:, None])
        .sum(dim=-1)
        .clamp_max(action_tokens - 1)
    )
    expected_masked_log_probability = masked_reference.log_softmax(dim=-1).gather(
        1, masked_tokens[:, None]
    )[:, 0]

    has_quantity = torch.rand(action_tokens, device=device, generator=generator) > 0.5
    quantity_logits = torch.randn(
        (batch, quantity_tokens),
        dtype=torch.bfloat16,
        device=device,
        generator=generator,
    )
    quantity_uniform = torch.rand(batch, device=device, generator=generator)
    quantities = torch.empty(batch, dtype=torch.long, device=device)
    combined_log_probability = log_probability.clone()
    sample_quantity(
        quantity_logits,
        tokens,
        has_quantity,
        quantity_uniform,
        quantities,
        combined_log_probability,
    )
    quantity_active = has_quantity[tokens]
    expected_quantities = (
        quantity_logits.float().softmax(dim=-1).cumsum(dim=-1) <= quantity_uniform[:, None]
    ).sum(dim=-1).clamp_max(quantity_tokens - 1) + 1
    expected_quantities = torch.where(
        quantity_active,
        expected_quantities,
        torch.zeros_like(expected_quantities),
    )
    quantity_log_probability = (
        quantity_logits.float()
        .log_softmax(dim=-1)
        .gather(
            1,
            (quantities - 1).clamp_min(0)[:, None],
        )[:, 0]
    )
    expected_combined = expected_log_probability + torch.where(
        quantity_active,
        quantity_log_probability,
        torch.zeros_like(quantity_log_probability),
    )

    torch.cuda.synchronize(device)
    torch.testing.assert_close(tokens, expected_tokens, rtol=0, atol=0)
    torch.testing.assert_close(masked_tokens, expected_masked_tokens, rtol=0, atol=0)
    torch.testing.assert_close(
        masked_log_probability,
        expected_masked_log_probability,
        rtol=0,
        atol=1e-6,
    )
    torch.testing.assert_close(quantities, expected_quantities, rtol=0, atol=0)
    torch.testing.assert_close(log_probability, expected_log_probability, rtol=0, atol=1e-6)
    torch.testing.assert_close(combined_log_probability, expected_combined, rtol=0, atol=2e-6)


def test_prefix_bounded_history_attention_matches_sdpa() -> None:
    _, device = _cuda_dependencies()
    from kagg_revue.policy.cuda.history_attention import history_attention_step

    generator = torch.Generator(device=device).manual_seed(29)
    batch = 4
    heads = 2
    history = 130
    head_width = 16
    projected = torch.randn(
        (batch, 1, 3, heads, head_width),
        dtype=torch.bfloat16,
        device=device,
        generator=generator,
    )
    query, key, value = projected.unbind(dim=2)
    query = query.transpose(1, 2)
    key = key.transpose(1, 2)
    value = value.transpose(1, 2)

    for index in (0, 63, 64, 127, 128, history - 1):
        key_cache = torch.randn(
            (batch, heads, history, head_width),
            dtype=torch.bfloat16,
            device=device,
            generator=generator,
        )
        value_cache = torch.randn(
            key_cache.shape,
            dtype=torch.bfloat16,
            device=device,
            generator=generator,
        )
        expected_key = key_cache.clone()
        expected_value = value_cache.clone()
        position = torch.tensor([index], dtype=torch.long, device=device)

        actual = history_attention_step(
            query,
            key,
            value,
            key_cache,
            value_cache,
            position,
        )
        expected_key[:, :, index : index + 1].copy_(key)
        expected_value[:, :, index : index + 1].copy_(value)
        expected = functional.scaled_dot_product_attention(
            query,
            expected_key[:, :, : index + 1],
            expected_value[:, :, : index + 1],
            dropout_p=0.0,
            is_causal=False,
        )

        torch.cuda.synchronize(device)
        torch.testing.assert_close(key_cache[:, :, index : index + 1], key, rtol=0, atol=0)
        torch.testing.assert_close(value_cache[:, :, index : index + 1], value, rtol=0, atol=0)
        torch.testing.assert_close(actual, expected, rtol=5e-3, atol=8e-3)


def test_complete_rollout_turn_cuda_graph_replays_native_legal_prefix() -> None:
    native, device = _cuda_dependencies()
    from kagg_revue.policy.cuda.rollout_turn_graph import (
        CudaRolloutTurnGraph,
        CudaRolloutTurnInputs,
    )
    from kagg_revue.policy.cuda.session import GpuPolicyStateLayout
    from kagg_revue.policy.economics import (
        CANDIDATE_FEATURES,
        ECONOMIC_FEATURE_VERSION,
        PREFIX_FEATURES,
        QUANTITY_FEATURES,
        TURN_FEATURES,
    )
    from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
    from kagg_revue.rl.outcome import (
        OutcomeActorCritic,
        outcome_values,
        selected_log_probability,
    )

    configuration = {
        "boardSize": 2,
        "episodeSteps": 4,
        "maxMarketOrdersPerTurn": 2,
    }
    sessions = [
        native.Engine(seed=seed, configuration=configuration).policy_session(0, 1)
        for seed in range(1, 5)
    ]
    batch = native.PolicySessionBatch(sessions, workers=2)
    engine_configuration = dict(native.Engine(seed=1, configuration=configuration).configuration)
    board_size = int(engine_configuration["boardSize"])
    layout = GpuPolicyStateLayout.from_spec(
        native.gpu_policy_state_spec(board_size, 1),
        board_size=board_size,
        unit_limit=1,
    )
    architecture = ActorArchitecture(
        board_shape=(2, 1, 2, 2),
        unit_shape=(2, 1, 1),
        global_features=82,
        model_width=32,
        entity_width=16,
        attention_heads=1,
        feedforward_width=64,
        latent_tokens=2,
        register_tokens=2,
        scene_layers=0,
        temporal_layers=1,
        action_layers=1,
        max_history=1,
        max_decisions=3,
        unit_action_tokens=int(native.action_codec_spec()["unit_tokens"]),
        market_action_tokens=len(native.action_codec_spec()["keys"])
        - int(native.action_codec_spec()["unit_tokens"]),
        maximum_quantity=128,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
        skill_tokens=4,
        economic_feature_version=ECONOMIC_FEATURE_VERSION,
        economic_turn_features=TURN_FEATURES,
        economic_prefix_features=PREFIX_FEATURES,
        economic_candidate_features=CANDIDATE_FEATURES,
        economic_quantity_features=QUANTITY_FEATURES,
    )
    model = OutcomeActorCritic(TurnPolicyNet(architecture)).to(device).eval()
    rows = len(sessions)
    inputs = CudaRolloutTurnInputs(
        board=torch.randn((rows, *architecture.board_shape), device=device),
        units=torch.randn((rows, *architecture.unit_shape), device=device),
        global_features=torch.randn((rows, architecture.global_features), device=device),
        previous_actions=torch.zeros(
            (rows, architecture.max_decisions), dtype=torch.long, device=device
        ),
        previous_quantities=torch.zeros(
            (rows, architecture.max_decisions), dtype=torch.long, device=device
        ),
        previous_mask=torch.zeros(
            (rows, architecture.max_decisions), dtype=torch.bool, device=device
        ),
        policy_state=torch.from_numpy(np.asarray(batch.gpu_state(), dtype=np.int32)).to(device),
        action_head_noise=torch.randn(
            rows,
            architecture.action_tokens,
            architecture.model_width,
            device=device,
        ),
    )
    has_quantity = torch.as_tensor(
        native.action_codec_spec()["has_quantity"], dtype=torch.bool, device=device
    )
    generator = torch.Generator(device=device).manual_seed(71)
    initial_economic_state = inputs.policy_state.clone()
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        graph = CudaRolloutTurnGraph(
            model.actor,
            inputs,
            layout,
            has_quantity,
            generator,
            behavior_value=model.behavior_value,
        )
        graph.start_turn(inputs)
        graph.replay()
        torch.cuda.current_stream(device).synchronize()
        assert graph.log_probabilities is not None
        assert graph.value is not None
        assert graph.skill_ids is not None
        actions = graph.tokens.T[:, None]
        sampled_quantities = graph.quantities.T[:, None]
        sampled_phases = graph.phases.T[:, None]
        decision_mask = graph.decisions.T[:, None]
        legal_mask = graph.legal.permute(1, 0, 2)[:, None]
        turn_mask = torch.ones((rows, 1), dtype=torch.bool, device=device)
        output = model(
            inputs.board[:, None],
            inputs.units[:, None],
            inputs.global_features[:, None],
            torch.empty((rows, 1, 0, 0), device=device),
            torch.empty((rows, 1, 0), dtype=torch.bool, device=device),
            torch.empty((rows, 1, architecture.max_decisions, 0), device=device),
            torch.empty(
                (rows, 1, architecture.max_decisions, architecture.action_tokens, 0),
                device=device,
            ),
            actions,
            sampled_quantities,
            sampled_phases,
            turn_mask,
            decision_mask,
            graph.skill_ids[:, None],
            initial_economic_state[:, None],
            actor_grad=False,
            action_head_noise=inputs.action_head_noise,
        )
        expected_log_probability = selected_log_probability(
            output.policy,
            actions,
            sampled_quantities,
            legal_mask,
            decision_mask,
            has_quantity,
        )[:, 0]
        expected_value = outcome_values(output.outcome_logits)[:, 0]
        active_log_probability = graph.log_probabilities.T[decision_mask[:, 0]]
        expected_active_log_probability = expected_log_probability[decision_mask[:, 0]]
        torch.testing.assert_close(
            active_log_probability,
            expected_active_log_probability,
            atol=2e-2,
            rtol=2e-2,
        )
        torch.testing.assert_close(graph.value, expected_value, atol=2e-2, rtol=2e-2)
        tokens = graph.tokens.cpu().numpy()
        quantities = graph.quantities.cpu().numpy()
        phases = graph.phases.cpu().numpy()
        decisions = graph.decisions.cpu().numpy()
        legal = graph.legal.cpu().numpy()
        final_phases = graph.final_phases.cpu().numpy()
        skill_ids = graph.skill_ids
        skill_log_probability = graph.skill_log_probability

    np.testing.assert_array_equal(final_phases, np.full(len(sessions), 2))
    assert skill_ids is not None and skill_ids.shape == (rows,)
    assert skill_log_probability is not None
    assert torch.isfinite(skill_log_probability).all()
    for row, session in enumerate(sessions):
        for position in range(architecture.max_decisions):
            active = int(session.phase) != 2
            assert bool(decisions[position, row]) == active
            if not active:
                continue
            assert phases[position, row] == session.phase
            np.testing.assert_array_equal(
                legal[position, row], np.asarray(session.legal_mask(), dtype=np.bool_)
            )
            session.select(
                int(tokens[position, row]),
                int(quantities[position, row]),
            )
        assert session.phase == 2

    next_sessions = [
        native.Engine(seed=seed, configuration=configuration).policy_session(1, 1)
        for seed in range(11, 15)
    ]
    next_batch = native.PolicySessionBatch(next_sessions, workers=2)
    graph.reset_episode()
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        inputs.policy_state.copy_(torch.from_numpy(np.asarray(next_batch.gpu_state())).to(device))
        inputs.board.normal_()
        inputs.units.normal_()
        inputs.global_features.normal_()
        assert inputs.action_head_noise is not None
        inputs.action_head_noise.normal_()
        graph.start_turn(inputs)
        graph.replay()
        next_decisions = graph.decisions.cpu().numpy()
        next_final_phases = graph.final_phases.cpu().numpy()
    np.testing.assert_array_equal(next_final_phases, np.full(len(next_sessions), 2))
    assert next_decisions.any(axis=0).all()
    graph.close()
