import copy
import random
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch
from torch.optim import AdamW

from kagg_revue.core.backend import load_backend
from kagg_revue.policy.effects import (
    EffectActorCritic,
    EffectArchitecture,
    EffectPolicy,
    NativeEffectContract,
)
from kagg_revue.policy.effects.data import tensor_state_from_native
from kagg_revue.policy.effects.gpu import (
    EffectDecisionGraphPool,
    EffectTurnGraph,
    PinnedEffectTurnStaging,
)
from kagg_revue.policy.effects.schema import EffectSequenceContext
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.rl.effects.chunked import backward_sharded_ppo
from kagg_revue.rl.effects.config import EffectOptimizationSettings
from kagg_revue.rl.effects.fleet import EffectRolloutFleet
from kagg_revue.rl.effects.initialization import effect_optimizer_parameters
from kagg_revue.rl.effects.learning import (
    audit_effect_behavior,
    optimize_effect_batch,
)
from kagg_revue.rl.effects.objective import effect_ppo_loss, official_turn_mean
from kagg_revue.rl.effects.population import effect_outcome_metrics
from kagg_revue.rl.effects.reuse import evaluate_reused_work
from kagg_revue.rl.effects.rollout import EffectRolloutCollector
from kagg_revue.rl.rollout.population import weighted_rollout_jobs


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _model(
    backend: object,
    configuration: dict[str, object],
    *,
    strategy_tokens: int = 0,
) -> tuple[EffectActorCritic, NativeEffectContract]:
    encoder = backend.actor_encoder_spec()
    codec = backend.action_codec_spec()
    unit_limit = 4
    board_size = int(configuration["boardSize"])
    actor_architecture = ActorArchitecture(
        board_shape=(
            2,
            int(encoder["board_channels"]),
            board_size,
            board_size,
        ),
        unit_shape=(2, unit_limit, int(encoder["unit_feat"])),
        global_features=int(encoder["global_feat"]),
        model_width=16,
        entity_width=8,
        attention_heads=2,
        feedforward_width=32,
        latent_tokens=2,
        scene_layers=0,
        temporal_layers=1,
        action_layers=1,
        max_history=1,
        max_decisions=6,
        unit_action_tokens=int(codec["unit_tokens"]),
        market_action_tokens=len(codec["keys"]) - int(codec["unit_tokens"]),
        maximum_quantity=8,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
        strategy_tokens=strategy_tokens,
        strategy_version="gru-v1" if strategy_tokens else None,
    )
    contract = NativeEffectContract.from_spec(backend.effect_policy_spec(), board_size=board_size)
    effect_architecture = EffectArchitecture.from_contract(
        contract,
        item_count=int(encoder["num_items"]),
        unit_limit=unit_limit,
        maximum_market_orders=int(configuration["maxMarketOrdersPerTurn"]),
        context_width=actor_architecture.model_width,
        model_width=16,
        feedforward_width=32,
        attention_heads=2,
        state_layers=1,
    )
    actor = TurnPolicyNet(actor_architecture)
    actor.requires_grad_(False)
    return EffectActorCritic(actor, EffectPolicy(effect_architecture)), contract


def test_official_turn_mean_does_not_overweight_long_factor_lists() -> None:
    values = torch.tensor([2.0, 4.0, 6.0, 10.0, 14.0, 18.0, 22.0])
    episodes = torch.tensor([0, 0, 0, 1, 1, 1, 1])
    turns = torch.tensor([0, 0, 1, 0, 1, 1, 1])

    result = official_turn_mean(values, episodes, turns, 2, 2)

    assert float(result) == pytest.approx(9.25)


def test_reused_work_retains_newly_legal_candidates_and_gradients() -> None:
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 8,
        "maxMarketOrdersPerTurn": 2,
    }
    model, _contract = _model(backend, configuration)
    engine = backend.engine(17, configuration)
    engine.step({"farmer": ["PASS"], "market": [["HIRE"]]}, {})
    session = backend.effect_policy_session(configuration, 4, 8)
    native = backend.effect_policy_batch([session], [engine], np.array([0]), workers=1)
    first = tensor_state_from_native(native.observe(np.array([0])), "cpu")
    state = type(first)(
        **{
            name: getattr(first, name).repeat(2, *([1] * (getattr(first, name).ndim - 1)))
            for name in first.__dataclass_fields__
        }
    )
    mask = torch.zeros_like(state.candidate_mask)
    mask[0, :2] = True
    mask[1, 1:3] = True
    state = replace(state, candidate_mask=mask)
    sequence = EffectSequenceContext(
        context=torch.randn(1, 1, model.effects.architecture.context_width),
        tile_context=torch.randn(
            1, 1, model.effects.architecture.tile_count, model.effects.architecture.context_width
        ),
        strategy=None,
    )
    episodes = torch.zeros(2, dtype=torch.long)
    turns = torch.zeros_like(episodes)
    expected = model.evaluate_effect_sequence_context(
        sequence,
        state,
        episodes,
        turns,
        candidate_states=(state,),
    )
    actual = evaluate_reused_work(model, sequence, state, episodes, turns, state)
    torch.testing.assert_close(actual.candidate_logits, expected.candidate_logits)
    choices = torch.tensor([[0], [2]])
    expected_loss = expected.candidate_logits.log_softmax(-1).gather(1, choices).sum()
    actual_loss = actual.candidate_logits.log_softmax(-1).gather(1, choices).sum()
    parameters = tuple(model.effects.parameters())
    expected_gradients = torch.autograd.grad(expected_loss, parameters, allow_unused=True)
    actual_gradients = torch.autograd.grad(actual_loss, parameters, allow_unused=True)
    for actual_gradient, expected_gradient in zip(
        actual_gradients,
        expected_gradients,
        strict=True,
    ):
        torch.testing.assert_close(actual_gradient, expected_gradient, atol=2e-6, rtol=2e-5)


def test_effect_state_encoding_is_invariant_to_group_padding() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    torch.manual_seed(3)
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 3,
        "turnsPerDay": 2,
        "maxMarketOrdersPerTurn": 2,
    }
    model, _contract = _model(backend, configuration)
    engine = backend.engine(3, configuration)
    session = backend.effect_policy_session(configuration, 4, 8)
    active = np.asarray([0], dtype=np.int64)
    native_batch = backend.effect_policy_batch(
        [session],
        [engine],
        active,
        workers=1,
    )
    native_batch.reset_transaction()
    root = native_batch.observe(active)
    kinds = backend.effect_policy_spec()["request_kinds"]
    stop = int(np.flatnonzero(np.asarray(root["candidate_fields"])[0, :, 0] == kinds["STOP"])[0])
    native_batch.advance(
        np.asarray([stop], dtype=np.int64),
        np.zeros(1, dtype=np.float32),
        np.zeros(1, dtype=np.float32),
        0,
    )
    market = native_batch.observe(active)
    market_fields = np.asarray(market["candidate_fields"])[0]
    order = int(
        np.flatnonzero(
            (market_fields[:, 0] != kinds["STOP"])
            & (market_fields[:, 0] != kinds["SKIP_MARKET_SLOT"])
        )[0]
    )
    native_batch.advance(
        np.asarray([order], dtype=np.int64),
        np.zeros(1, dtype=np.float32),
        np.zeros(1, dtype=np.float32),
        0,
    )
    state = tensor_state_from_native(native_batch.observe(active), "cpu")
    architecture = model.effects.architecture

    def padded(values: torch.Tensor, width: int) -> torch.Tensor:
        result = values.new_zeros((values.shape[0], width, *values.shape[2:]))
        result[:, : values.shape[1]] = values
        return result

    padded_state = replace(
        state,
        jobs=padded(state.jobs, architecture.unit_limit),
        job_mask=padded(state.job_mask, architecture.unit_limit),
        work_prefix=padded(state.work_prefix, architecture.unit_limit),
        work_mask=padded(state.work_mask, architecture.unit_limit),
        market_prefix=padded(
            state.market_prefix,
            architecture.maximum_market_orders,
        ),
        market_mask=padded(
            state.market_mask,
            architecture.maximum_market_orders,
        ),
        previous_action=padded(
            state.previous_action,
            architecture.unit_limit + architecture.maximum_market_orders,
        ),
        previous_mask=padded(
            state.previous_mask,
            architecture.unit_limit + architecture.maximum_market_orders,
        ),
    )
    context = torch.randn((1, architecture.context_width))
    tiles = torch.randn((1, architecture.tile_count, architecture.context_width))
    with torch.inference_mode():
        compact = model.effects.forward_logits(context, tiles, state)
        fixed = model.effects.forward_logits(context, tiles, padded_state)

    torch.testing.assert_close(fixed, compact, atol=1e-5, rtol=1e-5)


def test_effect_rollout_replays_factors_and_updates_once() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    torch.manual_seed(7)
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, contract = _model(backend, configuration)
    collector = EffectRolloutCollector(
        backend,
        model,
        contract,
        configuration,
        unit_limit=4,
        cpu_workers=1,
        device=torch.device("cpu"),
        action_generator=torch.Generator().manual_seed(3),
    )

    rollout = collector.collect((17, 19))
    replay = audit_effect_behavior(
        model,
        rollout.batch,
        torch.device("cpu"),
        episodes_per_batch=2,
    )
    settings = EffectOptimizationSettings(
        ppo_epochs=1,
        episodes_per_minibatch=4,
        episodes_per_microbatch=2,
        actor_learning_rate=1e-4,
        critic_learning_rate=2e-4,
        critic_warmup_updates=0,
        critic_actor_gradient=False,
        weight_decay=0.0,
        clip_epsilon=0.1,
        value_loss_weight=1.0,
        entropy_weight=0.0,
        gradient_clip=1.0,
        target_kl=1.0,
        normalize_advantage=True,
    )
    full_batch_model = copy.deepcopy(model)
    cached_reference_model = copy.deepcopy(model)
    metrics = optimize_effect_batch(
        model,
        AdamW(model.effects.parameters(), lr=settings.actor_learning_rate),
        rollout.batch,
        settings,
        torch.device("cpu"),
        random.Random(5),
    )
    full_batch_metrics = optimize_effect_batch(
        full_batch_model,
        AdamW(full_batch_model.effects.parameters(), lr=settings.actor_learning_rate),
        rollout.batch,
        settings.model_copy(update={"episodes_per_microbatch": 4}),
        torch.device("cpu"),
        random.Random(5),
    )
    cached_reference_metrics = optimize_effect_batch(
        cached_reference_model,
        AdamW(
            cached_reference_model.effects.parameters(),
            lr=settings.actor_learning_rate,
        ),
        replace(
            rollout.batch,
            outcomes=torch.tensor([-1.0, 1.0, -1.0, 1.0]),
        ),
        settings.model_copy(update={"ppo_epochs": 2}),
        torch.device("cpu"),
        random.Random(5),
    )

    assert rollout.batch.episode_count == 4
    assert rollout.batch.official_turn_count == 4
    assert rollout.batch.factor_count >= 8
    assert replay["maximum_absolute_log_probability_error"] < 1e-2
    assert replay["maximum_absolute_value_error"] < 1e-2
    assert metrics["optimizer_steps"] == 1
    assert full_batch_metrics["optimizer_steps"] == 1
    assert cached_reference_metrics["optimizer_steps"] == 2
    assert cached_reference_metrics["reference_forward_microbatches_per_rank"] == 2
    assert cached_reference_metrics["reference_cache_bytes_per_rank"] > 0
    for name in (
        "loss",
        "policy_loss",
        "value_loss",
        "entropy",
        "approximate_kl",
        "clip_fraction",
    ):
        assert metrics[name] == pytest.approx(full_batch_metrics[name], abs=1e-2)


@pytest.mark.parametrize("reject_actor", [False, True])
def test_effect_critic_warmup_does_not_mutate_actor_parameters(
    reject_actor: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    torch.manual_seed(11)
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, contract = _model(backend, configuration)
    collector = EffectRolloutCollector(
        backend,
        model,
        contract,
        configuration,
        unit_limit=4,
        cpu_workers=1,
        device=torch.device("cpu"),
        action_generator=torch.Generator().manual_seed(13),
    )
    rollout = collector.collect((23, 29))
    if reject_actor:
        from kagg_revue.rl.effects.trust_region import EffectPolicyGuard

        def reject_update(self: EffectPolicyGuard) -> float:
            return float("inf") if any(p in optimizer.state for p in actor_parameters) else 0.0

        monkeypatch.setattr(EffectPolicyGuard, "__call__", reject_update)
        rollout = replace(
            rollout,
            batch=replace(
                rollout.batch,
                outcomes=torch.tensor([-1.0, 1.0, -1.0, 1.0]),
            ),
        )
    settings = EffectOptimizationSettings(
        ppo_epochs=1,
        episodes_per_minibatch=2,
        episodes_per_microbatch=1,
        actor_learning_rate=1e-4,
        critic_learning_rate=2e-4,
        critic_warmup_updates=5,
        critic_actor_gradient=False,
        weight_decay=1e-2,
        clip_epsilon=0.1,
        value_loss_weight=1.0,
        entropy_weight=0.0,
        gradient_clip=1.0,
        target_kl=1.0,
        normalize_advantage=True,
    )
    actor_parameters, critic_parameters = effect_optimizer_parameters(model)
    actor_before = tuple(parameter.detach().clone() for parameter in actor_parameters)
    critic_before = tuple(parameter.detach().clone() for parameter in critic_parameters)
    optimizer = AdamW(
        [
            {"params": actor_parameters, "lr": settings.actor_learning_rate},
            {"params": critic_parameters, "lr": settings.critic_learning_rate},
        ],
        weight_decay=settings.weight_decay,
    )

    metrics = optimize_effect_batch(
        model,
        optimizer,
        rollout.batch,
        settings,
        torch.device("cpu"),
        random.Random(17),
        actor_requested=reject_actor,
        critic_actor_gradient=False,
    )

    assert metrics["actor_optimizer_steps"] == 0
    assert metrics["critic_optimizer_steps"] == 2
    assert all(
        torch.equal(before, parameter)
        for before, parameter in zip(actor_before, actor_parameters, strict=True)
    )
    assert any(
        not torch.equal(before, parameter)
        for before, parameter in zip(critic_before, critic_parameters, strict=True)
    )


def test_effect_rollout_uses_paired_native_opponent_population() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, contract = _model(backend, configuration)
    collector = EffectRolloutCollector(
        backend,
        model,
        contract,
        configuration,
        unit_limit=4,
        cpu_workers=2,
        device=torch.device("cpu"),
        action_generator=torch.Generator().manual_seed(71),
        sample_actions=False,
    )
    jobs = weighted_rollout_jobs(
        (73, 79),
        {"self_play": 0.5, "kaito_v48": 0.5},
        rank=0,
        world_size=1,
        sampling_seed=83,
    )

    rollout = collector.collect_jobs(jobs)
    metrics = effect_outcome_metrics(rollout.games)

    assert rollout.batch.episode_count == 4
    assert rollout.diagnostics["physical_games"] == 3
    assert {game.opponent_id for game in rollout.games} == {
        "self_play",
        "kaito_v48",
    }
    assert {game.seat for game in rollout.games if game.opponent_id == "kaito_v48"} == {0, 1}
    assert metrics["self_play"]["games"] == 2
    assert metrics["kaito_v48"]["games"] == 2
    for values in metrics.values():
        assert values["wins"] + values["ties"] + values["losses"] == values["games"]


def test_effect_evaluation_omits_the_training_tape() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, contract = _model(backend, configuration)
    collector = EffectRolloutCollector(
        backend,
        model,
        contract,
        configuration,
        unit_limit=4,
        cpu_workers=2,
        device=torch.device("cpu"),
        action_generator=torch.Generator().manual_seed(73),
        sample_actions=False,
    )

    try:
        result = collector.evaluate_jobs(((79, 0, "kaito_v48"), (79, 1, "kaito_v48")))
    finally:
        collector.close()

    assert len(result.games) == 2
    assert result.diagnostics["physical_games"] == 2
    assert result.diagnostics["native_rollout_buckets"] == 0
    assert result.diagnostics["factors"] >= 4
    assert native.effect_policy_spec()["abi_version"] == contract.version


def test_effect_rollout_fleet_concatenates_complete_cpu_streams() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, contract = _model(backend, configuration)
    fleet = EffectRolloutFleet(
        backend,
        model,
        contract,
        configuration,
        unit_limit=4,
        cpu_workers=2,
        device=torch.device("cpu"),
        action_generators=(
            torch.Generator().manual_seed(89),
            torch.Generator().manual_seed(97),
        ),
        maximum_graph_variants=8,
        sample_actions=False,
    )
    jobs = weighted_rollout_jobs(
        (101, 103, 107, 109),
        {"self_play": 0.5, "kaito_v48": 0.5},
        rank=0,
        world_size=1,
        sampling_seed=113,
    )
    try:
        rollout = fleet.collect_jobs(jobs)
    finally:
        fleet.close()

    assert rollout.batch.episode_count == 8
    assert rollout.diagnostics["physical_games"] == 6
    assert rollout.diagnostics["actor_streams"] == 2
    assert len(rollout.games) == rollout.batch.episode_count


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_effect_turn_cuda_graph_matches_eager_context() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, _contract = _model(backend, configuration, strategy_tokens=2)
    model = model.to("cuda").eval()
    engines = [backend.engine(seed, configuration) for seed in (37, 41)]
    staging = PinnedEffectTurnStaging(
        model.actor.architecture,
        len(engines),
        torch.device("cuda"),
    )
    staging.install_native(backend, engines, [0, 1], unit_limit=4, workers=2)
    inputs = staging.inputs
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        expected_context, expected_tiles, expected_strategy, _history, _state = model.start_turn(
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
    graph = EffectTurnGraph(
        model.actor,
        inputs,
        model.effects.architecture.tile_count,
    )
    try:
        context, tiles, strategy = graph.replay(inputs)
        torch.cuda.synchronize()
        torch.testing.assert_close(context, expected_context, atol=2e-2, rtol=2e-2)
        torch.testing.assert_close(tiles, expected_tiles, atol=2e-2, rtol=2e-2)
        assert strategy is not None
        assert expected_strategy is not None
        torch.testing.assert_close(strategy, expected_strategy, atol=2e-2, rtol=2e-2)
    finally:
        graph.close()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_effect_cuda_graph_preserves_root_work_and_market_outputs() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    torch.manual_seed(43)
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 4,
        "episodeSteps": 12,
        "turnsPerDay": 24,
        "maxMarketOrdersPerTurn": 2,
    }
    model, _contract = _model(backend, configuration)
    model = model.to("cuda").eval()
    engine = native.Engine(43, configuration)
    engine.step({"farmer": ["PASS"], "market": [["HIRE"]]}, {})
    session = native.AtomicEffectSession(configuration, 4, 8)
    active = np.asarray([0], dtype=np.int64)
    native_batch = native.AtomicEffectBatch(
        [session],
        [engine],
        active,
        workers=1,
    )
    architecture = model.effects.architecture
    context = torch.randn((1, architecture.context_width), device="cuda")
    tiles = torch.randn(
        (1, architecture.tile_count, architecture.context_width),
        device="cuda",
    )
    raw_root = native_batch.observe(active)
    root_state = tensor_state_from_native(raw_root, torch.device("cuda"))
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        root = model.effects(context, tiles, root_state)
        expected_root = model.effects.select_output(
            root,
            sample=False,
            compute_entropy=False,
        )

    generator = torch.Generator(device="cuda").manual_seed(47)
    graphs = EffectDecisionGraphPool(
        model.effects,
        generator,
        maximum_rows=1,
        sample=False,
    )
    graphs.start_turn(context, tiles, None)
    graphs.start_recording(4)
    try:
        root_widths = native_batch.observe_compact(active)
        root_selected, root_offset = graphs.decode_root(
            root_widths,
            active,
            native_batch,
        )
        np.testing.assert_array_equal(
            root_selected,
            expected_root.indices.cpu().numpy(),
        )

        fields = np.asarray(raw_root["candidate_fields"])[0]
        stage_kind = native.effect_policy_spec()["request_kinds"]["STAGE"]
        stage = int(np.flatnonzero(fields[:, 0] == stage_kind)[0])
        native_batch.advance_indexed(
            np.asarray([stage], dtype=np.int64),
            root_offset,
            turn_index=0,
        )
        raw_work = native_batch.observe(active)
        work_mask = torch.as_tensor(
            np.asarray(raw_work["candidate_mask"]),
            dtype=torch.bool,
            device="cuda",
        )
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            expected_work = model.effects.select_output(
                root,
                sample=False,
                candidate_mask=work_mask,
                compute_entropy=False,
            )
        work_widths = native_batch.observe_compact(active)
        work_selected, work_offset = graphs.decode_work(
            work_widths,
            active,
            native_batch,
        )
        np.testing.assert_array_equal(
            work_selected,
            expected_work.indices.cpu().numpy(),
        )

        stop_kind = native.effect_policy_spec()["request_kinds"]["STOP"]
        stop = int(
            np.flatnonzero(np.asarray(raw_work["candidate_fields"])[0, :, 0] == stop_kind)[0]
        )
        native_batch.advance_indexed(
            np.asarray([stop], dtype=np.int64),
            work_offset,
            turn_index=0,
        )
        expected_markets = []
        market_selected = np.zeros(1, dtype=np.int64)
        for iteration in range(2):
            raw_market = native_batch.observe(active)
            market_state = tensor_state_from_native(
                raw_market,
                torch.device("cuda"),
            )
            with (
                torch.inference_mode(),
                torch.autocast(
                    "cuda",
                    dtype=torch.bfloat16,
                ),
            ):
                market_logits = model.effects.forward_logits(
                    context,
                    tiles,
                    market_state,
                )
                expected_market = model.effects.select_logits(
                    market_logits,
                    root.value,
                    sample=False,
                    compute_entropy=False,
                )
            expected_markets.append(expected_market)
            market_widths = native_batch.observe_compact(active)
            market_selected, market_offset = graphs.decode_market(
                market_widths,
                active,
                native_batch,
            )
            np.testing.assert_array_equal(
                market_selected,
                expected_market.indices.cpu().numpy(),
            )
            if iteration == 0:
                fields = np.asarray(raw_market["candidate_fields"])[0]
                forced = int(
                    np.flatnonzero(
                        (fields[:, 0] != stop_kind)
                        & (
                            fields[:, 0]
                            != native.effect_policy_spec()["request_kinds"]["SKIP_MARKET_SLOT"]
                        )
                    )[0]
                )
                native_batch.advance_indexed(
                    np.asarray([forced], dtype=np.int64),
                    market_offset,
                    turn_index=0,
                )
        behavior = graphs.finish_recording()
    finally:
        graphs.close()
    expected_log_probability = np.asarray(
        [
            float(expected_root.log_probability.item()),
            float(expected_work.log_probability.item()),
            *(float(item.log_probability.item()) for item in expected_markets),
        ],
        dtype=np.float32,
    )
    statistics = np.asarray(behavior["statistics"])
    np.testing.assert_allclose(
        statistics[:, 0],
        expected_log_probability,
        atol=2e-3,
        rtol=2e-3,
    )
    np.testing.assert_allclose(
        statistics[:, 1],
        float(root.value.item()),
        atol=2e-3,
        rtol=2e-3,
    )
    for index, expected in enumerate((expected_root, expected_work, *expected_markets)):
        width = int(behavior["distribution_width"][index])
        row = int(behavior["distribution_row"][index])
        recorded = behavior["candidate_log_probabilities"][width][row]
        expected_logs = expected.candidate_log_probabilities.squeeze(0).cpu().numpy()
        np.testing.assert_allclose(
            recorded[: expected_logs.shape[0]],
            expected_logs,
            atol=2e-3,
            rtol=2e-3,
        )


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_effect_work_cache_can_select_a_newly_legal_candidate() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    environment: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, _contract = _model(backend, environment)
    model = model.to("cuda").eval()
    engine = backend.engine(3, environment)
    session = backend.effect_policy_session(environment, 4, 8)
    active = np.asarray([0], dtype=np.int64)
    native = backend.effect_policy_batch([session], [engine], active, 1)
    widths = native.observe_compact(active)

    class ChangingMask:
        """Supply synthetic support changes over an unchanged native surface."""

        @staticmethod
        def write_prepared(*arrays: np.ndarray) -> None:
            native.write_prepared(*arrays)
            arrays[2].fill(False)
            arrays[2][:, 0] = True

        @staticmethod
        def write_prepared_mask(mask: np.ndarray, rows: np.ndarray) -> None:
            native.write_prepared_mask(mask, rows)
            mask.fill(False)
            mask[:, 1] = True

    width = model.effects.architecture.context_width
    context = torch.zeros((1, width), device="cuda")
    tiles = torch.zeros((1, model.effects.architecture.tile_count, width), device="cuda")
    graphs = EffectDecisionGraphPool(model.effects, torch.Generator(device="cuda"), 1, sample=False)
    try:
        graphs.start_turn(context, tiles, None)
        graphs.start_recording(2)
        root, _offset = graphs.decode_root(widths, active, ChangingMask())
        assert root.item() == 0
        work, _offset = graphs.decode_work(widths, active, ChangingMask())
        assert work.item() == 1
        behavior = graphs.finish_recording()
        assert np.isfinite(behavior["statistics"]).all()
    finally:
        graphs.close()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_effect_cuda_rollout_uses_compact_device_behavior_path() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    torch.manual_seed(53)
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, contract = _model(backend, configuration)
    model = model.to("cuda").eval()
    collector = EffectRolloutCollector(
        backend,
        model,
        contract,
        configuration,
        unit_limit=4,
        cpu_workers=2,
        device=torch.device("cuda"),
        action_generator=torch.Generator(device="cuda").manual_seed(59),
    )
    try:
        rollouts = (collector.collect((61,)), collector.collect((67,)))
    finally:
        collector.close()
    assert int(rollouts[0].diagnostics["graph_variants_created"]) >= 2
    replay = audit_effect_behavior(
        model,
        rollouts[0].batch,
        torch.device("cuda"),
        episodes_per_batch=2,
        candidate_elements_per_chunk=1,
    )
    assert replay["maximum_absolute_log_probability_error"] < 0.1
    assert replay["maximum_absolute_value_error"] < 0.1
    for rollout in rollouts:
        assert rollout.diagnostics["optimized_cuda_path"] is True
        assert torch.isfinite(rollout.batch.old_log_probability).all()
        assert torch.isfinite(rollout.batch.old_value).all()
        assert all(
            shard.reference_candidate_log_probabilities is not None
            for shard in rollout.batch.decision_shards
        )
        offset = 0
        for shard in rollout.batch.decision_shards:
            reference = shard.reference_candidate_log_probabilities
            assert reference is not None
            stop = offset + shard.row_count
            selected = rollout.batch.selected[offset:stop]
            recorded = reference.gather(1, selected[:, None]).squeeze(1)
            torch.testing.assert_close(
                recorded,
                rollout.batch.old_log_probability[offset:stop],
                atol=2e-3,
                rtol=2e-3,
            )
            assert torch.isneginf(reference[~shard.state.candidate_mask]).all()
            offset = stop
        selected_batch = rollout.batch.subset(
            tuple(range(rollout.batch.episode_count)),
            torch.device("cuda"),
        )
        reference = selected_batch.reference_candidate_log_probabilities
        assert reference is not None
        padded_masks = []
        for shard in selected_batch.decision_shards:
            mask = shard.state.candidate_mask
            padded = torch.zeros(
                (mask.shape[0], selected_batch.candidate_width),
                dtype=torch.bool,
                device=mask.device,
            )
            padded[:, : mask.shape[1]] = mask
            padded_masks.append(padded)
        candidate_mask = torch.cat(padded_masks)
        assert torch.isneginf(reference[~candidate_mask]).all()
        torch.testing.assert_close(
            reference.gather(1, selected_batch.selected[:, None]).squeeze(1),
            selected_batch.old_log_probability,
            atol=2e-3,
            rtol=2e-3,
        )


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_effect_cuda_rollout_can_omit_training_only_distributions() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    torch.manual_seed(79)
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, contract = _model(backend, configuration)
    model = model.to("cuda").eval()
    collector = EffectRolloutCollector(
        backend,
        model,
        contract,
        configuration,
        unit_limit=4,
        cpu_workers=2,
        device=torch.device("cuda"),
        action_generator=torch.Generator(device="cuda").manual_seed(83),
        retain_behavior_distributions=False,
    )
    try:
        rollout = collector.collect((89,))
    finally:
        collector.close()

    assert torch.isfinite(rollout.batch.old_log_probability).all()
    assert torch.isfinite(rollout.batch.old_value).all()
    assert all(
        shard.reference_candidate_log_probabilities is None
        for shard in rollout.batch.decision_shards
    )


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_chunked_effect_ppo_matches_full_candidate_objective() -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    torch.manual_seed(71)
    backend = load_backend(_root())
    configuration: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 2,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    source, contract = _model(backend, configuration)
    source = source.to("cuda").eval()
    collector = EffectRolloutCollector(
        backend,
        source,
        contract,
        configuration,
        unit_limit=4,
        cpu_workers=2,
        device=torch.device("cuda"),
        action_generator=torch.Generator(device="cuda").manual_seed(73),
        sample_actions=False,
    )
    try:
        rollout = collector.collect((79,))
    finally:
        collector.close()
    selected = rollout.batch.subset((0, 1), torch.device("cuda"))
    reference = selected.reference_candidate_log_probabilities
    assert reference is not None
    advantages = (
        selected.outcomes.float()[selected.episode_index] - selected.old_value.detach().float()
    )
    settings = EffectOptimizationSettings(
        ppo_epochs=1,
        episodes_per_minibatch=2,
        episodes_per_microbatch=2,
        actor_learning_rate=1e-4,
        critic_learning_rate=2e-4,
        critic_warmup_updates=0,
        critic_actor_gradient=False,
        weight_decay=0.0,
        clip_epsilon=0.1,
        value_loss_weight=1.0,
        entropy_weight=0.01,
        gradient_clip=1.0,
        target_kl=1.0,
        normalize_advantage=False,
        candidate_elements_per_chunk=1,
    )
    full_model = copy.deepcopy(source).train()
    chunked_model = copy.deepcopy(source).train()
    with torch.autocast("cuda", dtype=torch.bfloat16):
        sequence = full_model.encode_effect_sequences(
            selected.board,
            selected.units,
            selected.global_features,
            selected.actions,
            selected.quantities,
            selected.turn_mask,
            selected.decision_mask,
            (
                selected.economic_state
                if full_model.actor.architecture.economic_feature_version is not None
                else None
            ),
        )
        assert selected.state is not None
        output = full_model.evaluate_effect_sequence_context(
            sequence,
            selected.state,
            selected.episode_index,
            selected.turn_index,
            candidate_states=tuple(shard.state for shard in selected.decision_shards),
            critic_actor_gradient=False,
        )
        full_loss = effect_ppo_loss(
            output,
            selected.selected,
            selected.old_log_probability,
            reference.gather(1, selected.selected[:, None]).squeeze(1),
            reference,
            advantages,
            selected.outcomes,
            selected.episode_index,
            selected.turn_index,
            selected.policy_mask,
            selected.value_mask,
            turn_horizon=selected.board.shape[1],
            clip_epsilon=settings.clip_epsilon,
            value_loss_weight=settings.value_loss_weight,
            entropy_weight=settings.entropy_weight,
            actor_update=True,
        )
    full_loss.total.backward()
    chunked_loss, _behavior_ratio = backward_sharded_ppo(
        chunked_model,
        selected,
        advantages,
        settings,
        value_scale=torch.ones((), device="cuda"),
        policy_scale=torch.ones((), device="cuda"),
        critic_actor_gradient=False,
        validate=True,
    )

    for name in (
        "total",
        "policy",
        "value",
        "entropy",
        "approximate_kl",
        "clip_fraction",
        "behavior_approximate_kl",
        "behavior_clip_fraction",
    ):
        torch.testing.assert_close(
            getattr(chunked_loss, name),
            getattr(full_loss, name),
            atol=2e-3,
            rtol=2e-3,
        )
    full_gradients = {
        name: parameter.grad
        for name, parameter in full_model.named_parameters()
        if parameter.grad is not None
    }
    chunked_gradients = {
        name: parameter.grad
        for name, parameter in chunked_model.named_parameters()
        if parameter.grad is not None
    }
    assert chunked_gradients.keys() == full_gradients.keys(), (
        sorted(chunked_gradients.keys() - full_gradients.keys()),
        sorted(full_gradients.keys() - chunked_gradients.keys()),
    )
    for name in full_gradients:
        torch.testing.assert_close(
            chunked_gradients[name],
            full_gradients[name],
            atol=1e-2,
            rtol=2e-2,
        )
