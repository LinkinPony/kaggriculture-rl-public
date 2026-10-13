import copy
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch
from torch.optim import AdamW

from kagg_revue.core.backend import load_backend
from kagg_revue.policy.intents.contract import NativeIntentContract
from kagg_revue.policy.intents.gpu import (
    IntentDecisionGraphPool,
    IntentGpuTransactionGraph,
    IntentTurnGraph,
    PinnedIntentTurnStaging,
)
from kagg_revue.policy.intents.gpu.ledger import IntentGpuLedger
from kagg_revue.policy.intents.gpu.staging import PinnedIntentTransactionStaging
from kagg_revue.policy.intents.model import (
    IntentActorCritic,
    IntentPolicy,
)
from kagg_revue.policy.intents.schema import IntentArchitecture, IntentPolicyOutput
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.rl.intents.config import IntentOptimizationSettings
from kagg_revue.rl.intents.data import tensor_state_from_native
from kagg_revue.rl.intents.learning import (
    audit_intent_behavior,
    optimize_intent_batch,
)
from kagg_revue.rl.intents.objective import intent_behavior_cloning_loss, intent_ppo_loss
from kagg_revue.rl.intents.rollout import IntentRolloutCollector


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _model(
    backend: object, configuration: dict[str, object]
) -> tuple[IntentActorCritic, NativeIntentContract]:
    encoder = backend.actor_encoder_spec()
    codec = backend.action_codec_spec()
    unit_limit = 4
    actor_architecture = ActorArchitecture(
        board_shape=(2, int(encoder["board_channels"]), 2, 2),
        unit_shape=(2, unit_limit, int(encoder["unit_feat"])),
        global_features=int(encoder["global_feat"]),
        model_width=16,
        entity_width=8,
        attention_heads=2,
        feedforward_width=32,
        latent_tokens=4,
        scene_layers=0,
        temporal_layers=1,
        action_layers=1,
        max_history=1,
        max_decisions=6,
        unit_action_tokens=int(codec["unit_tokens"]),
        market_action_tokens=len(codec["keys"]) - int(codec["unit_tokens"]),
        maximum_quantity=128,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
    )
    contract = NativeIntentContract.from_spec(backend.intent_ledger_spec(), board_size=2)
    intent_architecture = IntentArchitecture.from_contract(
        contract,
        item_count=int(encoder["num_items"]),
        unit_limit=unit_limit,
        maximum_market_orders=int(configuration["maxMarketOrdersPerTurn"]),
        context_width=actor_architecture.model_width,
        model_width=16,
        feedforward_width=32,
    )
    actor = TurnPolicyNet(actor_architecture)
    actor.requires_grad_(False)
    return IntentActorCritic(actor, IntentPolicy(intent_architecture)), contract


def test_intent_rollout_replays_each_pseudo_step_and_updates() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, contract = _model(backend, configuration)
    generator = torch.Generator().manual_seed(3)
    collector = IntentRolloutCollector(
        backend,
        model,
        contract,
        configuration,
        unit_limit=4,
        cpu_workers=1,
        max_transaction_steps=2,
        device=torch.device("cpu"),
        action_generator=generator,
    )

    rollout = collector.collect((17,))
    replay = audit_intent_behavior(
        model,
        rollout.batch,
        torch.device("cpu"),
        episodes_per_batch=2,
    )
    settings = IntentOptimizationSettings(
        ppo_epochs=1,
        episodes_per_minibatch=2,
        episodes_per_microbatch=1,
        learning_rate=1e-4,
        weight_decay=0.0,
        clip_epsilon=0.1,
        value_loss_weight=1.0,
        entropy_weight=0.0,
        gradient_clip=1.0,
        target_kl=1.0,
        normalize_advantage=True,
    )
    full_batch_model = copy.deepcopy(model)
    optimizer = AdamW(model.intents.parameters(), lr=settings.learning_rate)
    full_batch_optimizer = AdamW(full_batch_model.intents.parameters(), lr=settings.learning_rate)
    metrics = optimize_intent_batch(
        model,
        optimizer,
        rollout.batch,
        settings,
        torch.device("cpu"),
        __import__("random").Random(5),
    )
    full_batch_metrics = optimize_intent_batch(
        full_batch_model,
        full_batch_optimizer,
        rollout.batch,
        settings.model_copy(update={"episodes_per_microbatch": 2}),
        torch.device("cpu"),
        __import__("random").Random(5),
    )

    assert rollout.batch.episode_count == 2
    assert rollout.batch.decision_count >= 2
    assert replay["maximum_absolute_log_probability_error"] < 1e-4
    assert metrics["optimizer_steps"] == 1
    assert full_batch_metrics["optimizer_steps"] == 1
    expected_total = metrics["policy_loss"] + metrics["value_loss"]
    if metrics["actor_update"]:
        expected_total -= settings.entropy_weight * metrics["entropy"]
    assert metrics["loss"] == pytest.approx(expected_total)
    for name in (
        "loss",
        "policy_loss",
        "value_loss",
        "entropy",
        "approximate_kl",
        "clip_fraction",
        "behavior_approximate_kl",
        "behavior_clip_fraction",
    ):
        assert metrics[name] == pytest.approx(full_batch_metrics[name], abs=1e-5)
    assert metrics["last_approximate_kl"] == pytest.approx(0.0, abs=1e-7)
    assert metrics["first_approximate_kl"] == pytest.approx(0.0, abs=1e-7)
    assert metrics["maximum_approximate_kl"] == pytest.approx(0.0, abs=1e-7)
    assert metrics["trigger_approximate_kl"] is None
    assert metrics["evaluated_minibatches"] == 1
    assert metrics["optimizer_episodes"] == 2


def test_intent_ppo_excludes_forced_entropy_and_balances_episodes() -> None:
    logits = torch.tensor([[0.4, -0.2], [0.1, 0.3], [-0.5, 0.7]], requires_grad=True)
    output = IntentPolicyOutput(
        candidate_logits=logits,
        outcome_logits=torch.zeros((3, 3), requires_grad=True),
    )
    selected = torch.tensor([0, 1, 1])
    current = torch.log_softmax(logits.detach(), dim=-1).gather(1, selected[:, None]).squeeze(1)
    old = current - torch.tensor([0.05, -0.03, 0.0])
    advantages = torch.tensor([1.0, 3.0, -2.0])
    outcomes = torch.tensor([1.0, -1.0])
    episode_index = torch.tensor([0, 0, 1])
    policy_mask = torch.tensor([True, True, False])

    loss = intent_ppo_loss(
        output,
        selected,
        old,
        current,
        torch.log_softmax(logits.detach(), dim=-1),
        advantages,
        outcomes,
        episode_index,
        policy_mask,
        clip_epsilon=0.1,
        value_loss_weight=0.0,
        entropy_weight=0.0,
        actor_update=True,
    )
    ratios = torch.exp(current[:2] - old[:2])
    expected = -(ratios * advantages[:2]).mean()

    torch.testing.assert_close(loss.policy, expected)
    torch.testing.assert_close(loss.approximate_kl, torch.tensor(0.0))
    assert float(loss.behavior_approximate_kl) > 0.0
    assert int(loss.policy_steps) == 2
    assert torch.isfinite(loss.total)


def test_intent_ppo_uses_exact_categorical_kl() -> None:
    current_logits = torch.tensor([[0.8, -0.1, -0.4], [0.2, 0.5, -0.3]])
    reference_logits = torch.tensor([[0.4, 0.1, -0.2], [-0.1, 0.7, 0.0]])
    reference_log_probabilities = torch.log_softmax(reference_logits, dim=-1)
    selected = torch.tensor([0, 1])
    selected_reference = reference_log_probabilities.gather(
        1, selected[:, None]
    ).squeeze(1)
    output = IntentPolicyOutput(
        candidate_logits=current_logits,
        outcome_logits=torch.zeros((2, 3)),
    )

    loss = intent_ppo_loss(
        output,
        selected,
        selected_reference,
        selected_reference,
        reference_log_probabilities,
        torch.ones(2),
        torch.tensor([1.0, -1.0]),
        torch.arange(2),
        torch.ones(2, dtype=torch.bool),
        clip_epsilon=0.1,
        value_loss_weight=0.0,
        entropy_weight=0.0,
        actor_update=True,
    )
    current_log_probabilities = torch.log_softmax(current_logits, dim=-1)
    expected = (
        reference_log_probabilities.exp()
        * (reference_log_probabilities - current_log_probabilities)
    ).sum(dim=-1).mean()

    torch.testing.assert_close(loss.approximate_kl, expected)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_intent_kl_stop_uses_frozen_learner_likelihood_before_step() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, contract = _model(backend, configuration)
    collector = IntentRolloutCollector(
        backend,
        model,
        contract,
        configuration,
        unit_limit=4,
        cpu_workers=1,
        max_transaction_steps=2,
        device=torch.device("cpu"),
        action_generator=torch.Generator().manual_seed(43),
    )
    rollout = collector.collect((47, 53))
    batch = replace(rollout.batch, outcomes=torch.tensor([1.0, -1.0, 1.0, -1.0]))
    device = torch.device("cuda")
    model = model.to(device)
    reference = copy.deepcopy(model)
    settings = IntentOptimizationSettings(
        ppo_epochs=2,
        episodes_per_minibatch=2,
        episodes_per_microbatch=1,
        learning_rate=1e-2,
        weight_decay=0.0,
        clip_epsilon=0.1,
        value_loss_weight=1.0,
        entropy_weight=0.0,
        gradient_clip=1.0,
        target_kl=1e-10,
        normalize_advantage=True,
    )
    metrics = optimize_intent_batch(
        model,
        AdamW(model.intents.parameters(), lr=settings.learning_rate),
        batch,
        settings,
        device,
        __import__("random").Random(59),
        reference_model=reference,
    )

    assert metrics["kl_early_stop"] is True
    assert metrics["optimizer_steps"] == 1
    assert metrics["evaluated_minibatches"] == 2
    assert metrics["optimizer_episodes"] == 2
    assert metrics["evaluated_episodes"] == 4
    assert metrics["trigger_approximate_kl"] == metrics["last_approximate_kl"]
    assert float(metrics["first_approximate_kl"]) <= settings.target_kl
    assert float(metrics["maximum_approximate_kl"]) > settings.target_kl
    assert float(metrics["behavior_approximate_kl"]) > 0.0


def test_intent_bc_sums_joint_choices_on_fixed_turn_horizon() -> None:
    logits = torch.zeros((4, 2), requires_grad=True)
    output = IntentPolicyOutput(
        candidate_logits=logits,
        outcome_logits=torch.zeros((4, 3)),
    )
    loss = intent_behavior_cloning_loss(
        output,
        selected=torch.tensor([0, 1, 0, 1]),
        policy_mask=torch.tensor([True, True, True, False]),
        episode_index=torch.tensor([0, 0, 1, 1]),
        turn_index=torch.tensor([0, 0, 2, 3]),
        episode_count=2,
        turn_horizon=4,
    )

    torch.testing.assert_close(loss, torch.log(torch.tensor(2.0)) * 3 / 8)


def test_intent_residual_factorization_matches_concatenated_head() -> None:
    backend = load_backend(_root())
    model, _contract = _model(
        backend,
        {
            "boardSize": 2,
            "episodeSteps": 1,
            "turnsPerDay": 1,
            "maxMarketOrdersPerTurn": 1,
        },
    )
    policy = model.intents
    generator = torch.Generator().manual_seed(29)
    hidden = torch.randn((3, policy.architecture.model_width), generator=generator)
    candidates = torch.randn((3, 7, policy.architecture.model_width), generator=generator)
    expanded = hidden[:, None].expand_as(candidates)
    expected = policy.residual(torch.cat((expanded, candidates), dim=-1)).squeeze(-1)
    expected_pointer = (policy.query(hidden)[:, None] * policy.key(candidates)).sum(
        dim=-1
    ) * policy.scale

    actual = policy._residual_scores(hidden, candidates)
    actual_pointer = policy._pointer_scores(hidden, candidates)

    torch.testing.assert_close(actual, expected, atol=2e-6, rtol=2e-6)
    torch.testing.assert_close(actual_pointer, expected_pointer, atol=2e-6, rtol=2e-6)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_intent_turn_cuda_graph_matches_eager_context() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, _contract = _model(backend, configuration)
    model = model.to("cuda").eval()
    engines = [backend.engine(seed, configuration) for seed in (37, 41)]
    players = [0, 1]
    staging = PinnedIntentTurnStaging(
        model.actor.architecture,
        len(engines),
        torch.device("cuda"),
    )
    staging.install_native(backend, engines, players, unit_limit=4, workers=2)
    inputs = staging.inputs
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        expected_context, expected_tiles, _history, _strategy = model.start_turn(
            inputs.board,
            inputs.units,
            inputs.global_features,
            inputs.previous_actions,
            inputs.previous_quantities,
            inputs.previous_mask,
            None,
            None,
            None,
        )
    graph = IntentTurnGraph(
        model.actor,
        inputs,
        model.intents.architecture.tile_count,
    )
    try:
        context, tiles = graph.replay(inputs)
        torch.cuda.synchronize()
        torch.testing.assert_close(context, expected_context, atol=2e-2, rtol=2e-2)
        torch.testing.assert_close(tiles, expected_tiles, atol=2e-2, rtol=2e-2)
    finally:
        graph.close()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_intent_cuda_graph_preserves_greedy_policy_outputs() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, _contract = _model(backend, configuration)
    model = model.to("cuda").eval()
    engines = [native.Engine(seed, configuration) for seed in (23, 29)]
    sessions = [native.IntentLedgerSession(configuration) for _ in engines]
    players = np.asarray([0, 1], dtype=np.int64)
    native_batch = backend.intent_ledger_batch(sessions, engines, players, 2)
    active = np.asarray([0, 1], dtype=np.int64)
    raw = native_batch.observe(active, 2)
    candidate_mask = np.asarray(raw["candidate_mask"], dtype=np.bool_)
    architecture = model.intents.architecture
    context = torch.randn((2, architecture.context_width), device="cuda")
    tiles = torch.randn((2, architecture.tile_count, architecture.context_width), device="cuda")
    state = tensor_state_from_native(raw, candidate_mask, torch.device("cuda"))
    with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        expected = model.intents.select(
            context,
            tiles,
            state,
            sample=False,
            compute_entropy=False,
        )

    generator = torch.Generator(device="cuda").manual_seed(31)
    graphs = IntentDecisionGraphPool(model.intents, generator, maximum_rows=2, sample=False)
    try:
        graphs.start_turn(context, tiles)
        indices, log_probability, value = graphs.decode(
            raw,
            candidate_mask,
            active,
            native_batch,
        )
        compact_widths = native_batch.observe_compact(active, 2)
        compact_indices, compact_log_probability, compact_value = graphs.decode_compact(
            compact_widths, active, native_batch
        )
        graphs.start_recording(2)
        recorded_indices, behavior_offset = graphs.decode_compact_recording(
            compact_widths, active, native_batch
        )
        behavior = graphs.finish_recording()
    finally:
        graphs.close()
    np.testing.assert_array_equal(indices, expected.indices.cpu().numpy())
    np.testing.assert_array_equal(compact_indices, indices)
    np.testing.assert_array_equal(recorded_indices, indices)
    assert behavior_offset == 0
    np.testing.assert_allclose(
        log_probability,
        expected.log_probability.cpu().numpy(),
        rtol=2e-3,
        atol=2e-3,
    )
    np.testing.assert_allclose(
        value,
        expected.value.cpu().numpy(),
        rtol=2e-3,
        atol=2e-3,
    )
    np.testing.assert_allclose(compact_log_probability, log_probability, atol=2e-3)
    np.testing.assert_allclose(compact_value, value, atol=2e-3)
    np.testing.assert_allclose(behavior[:, 0], log_probability, atol=2e-3)
    np.testing.assert_allclose(behavior[:, 1], value, atol=2e-3)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_intent_cuda_transaction_trace_replays_in_native_ledger() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 3,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, _contract = _model(backend, configuration)
    model = model.to("cuda").eval()
    seeds = (43, 47)
    players = np.asarray([0, 1], dtype=np.int64)
    architecture = model.intents.architecture
    context = torch.randn((2, architecture.context_width), device="cuda")
    tiles = torch.randn((2, architecture.tile_count, architecture.context_width), device="cuda")
    engines = [native.Engine(seed, configuration) for seed in seeds]
    sessions = [native.IntentLedgerSession(configuration) for _ in engines]
    native_batch = native.IntentLedgerBatch(sessions, engines, players, workers=2)
    active = np.arange(2, dtype=np.int64)
    raw = native_batch.observe(active, maximum_steps=3)
    auxiliary = native_batch.device_auxiliary()
    economic = np.asarray(
        backend.engine_policy_turn_inputs(engines, players.tolist(), 4, 2)[4],
        dtype=np.int32,
    )
    state = tensor_state_from_native(
        raw,
        np.asarray(raw["candidate_mask"], dtype=np.bool_),
        torch.device("cuda"),
    )
    with torch.inference_mode(), torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        expected = model.intents(context, tiles, state)
        encoded_context, encoded_tiles = model.intents.prepare_turn(context, tiles)
        work_summary = model.intents.state_encoder.summarize_work(
            state.work_orders, state.work_mask
        )
        prepared = model.intents.forward_prepared(
            encoded_context, encoded_tiles, state, work_summary
        )
    torch.testing.assert_close(
        prepared.candidate_logits, expected.candidate_logits, atol=2e-3, rtol=2e-3
    )
    torch.testing.assert_close(
        prepared.outcome_logits, expected.outcome_logits, atol=2e-3, rtol=2e-3
    )
    graph_generator = torch.Generator(device="cuda").manual_seed(53)
    graph = IntentGpuTransactionGraph(
        model.intents,
        graph_generator,
        batch=2,
        unit_limit=4,
        maximum_steps=3,
        episode_steps=3,
        turns_per_day=1,
        sample=True,
    )
    try:
        graph.start_recording(4 * graph.ledger.trace_capacity)
        initial_generator_state = graph_generator.get_state()
        trace = graph.replay(raw, auxiliary, economic, context, tiles)
        first_generator_state = graph_generator.get_state()
        graph.replay(raw, auxiliary, economic, context, tiles)
        second_generator_state = graph_generator.get_state()
        forced = native_batch.replay_transaction(
            trace.selected,
            trace.selected_fields,
            trace.counts,
            trace.behavior_offset,
            turn_index=0,
            maximum_steps=3,
        )
        behavior = graph.finish_recording()
        buckets = native_batch.export_rollout_buckets()
    finally:
        graph.close()

    assert forced >= 0
    assert not torch.equal(initial_generator_state, first_generator_state)
    assert not torch.equal(first_generator_state, second_generator_state)
    assert np.all(trace.counts >= 1)
    assert sum(len(bucket["selected"]) for bucket in buckets) == int(trace.counts.sum())
    assert behavior.shape == (4 * graph.ledger.trace_capacity, 2)
    assert np.isfinite(behavior).all()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_intent_cuda_skip_slot_matches_native_successor() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 3,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, _contract = _model(backend, configuration)
    architecture = model.intents.architecture
    engine = native.Engine(59, configuration)
    session = native.IntentLedgerSession(configuration)
    players = np.asarray([0], dtype=np.int64)
    native_batch = native.IntentLedgerBatch([session], [engine], players, workers=1)
    active = np.asarray([0], dtype=np.int64)
    raw = native_batch.observe(active, maximum_steps=4)
    auxiliary = native_batch.device_auxiliary()
    economic = np.asarray(
        backend.engine_policy_turn_inputs([engine], [0], 4, 1)[4],
        dtype=np.int32,
    )
    ledger = IntentGpuLedger(
        architecture,
        batch=1,
        unit_limit=4,
        device=torch.device("cuda"),
        maximum_steps=4,
        episode_steps=3,
        turns_per_day=1,
    )
    staging = PinnedIntentTransactionStaging(
        batch=1,
        cells=ledger.cells,
        work_capacity=ledger.work_capacity,
        work_field_count=architecture.work_field_count,
        market_capacity=architecture.maximum_market_orders,
        economic_width=ledger.layout.width,
        device=torch.device("cuda"),
    )
    staging.install(raw, auxiliary, economic)
    ledger.begin_turn(**staging.device)
    decision = ledger.decision(64)
    skip = int(backend.intent_ledger_spec()["choice_kinds"]["MARKET_SKIP_SLOT"])
    matches = decision.state.candidate_mask[0] & (decision.state.candidate_fields[0, :, 0] == skip)
    selected = matches.long().argmax().reshape(1)
    assert bool(matches[selected.item()])
    ledger.apply_selection(
        decision,
        selected,
        torch.zeros(1, device="cuda"),
        torch.zeros(1, device="cuda"),
    )
    torch.testing.assert_close(
        ledger.market_prefix[0, 0],
        torch.tensor([6, -1, 0], device="cuda"),
    )

    native_fields = np.asarray(raw["candidate_fields"])[0]
    native_skip = int(np.flatnonzero(native_fields[:, 0] == skip)[0])
    session.select(native_skip)
    native_after = session.observe(engine, 0)
    device_after = ledger.decision(64)
    count = int(device_after.candidate_counts[0])
    np.testing.assert_array_equal(
        device_after.state.candidate_fields[0, :count].cpu().numpy(),
        native_after["candidate_fields"],
    )
    np.testing.assert_allclose(
        device_after.state.candidate_features[0, :count].cpu().numpy(),
        native_after["candidate_features"],
        rtol=1e-6,
        atol=1e-6,
    )
