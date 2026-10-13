from __future__ import annotations

import numpy as np
import pytest
import torch

from kagg_revue.native import _revue_native as native
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.policy.programs import (
    ControlType,
    MarketDecision,
    MarketOrderType,
    ProgramSession,
    TaskType,
    UnitDecision,
)
from kagg_revue.policy.programs.grammar import ProgramActions
from kagg_revue.policy.programs.model import ConditionalProgramPolicy
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.runtime import (
    decode_program_turn,
    program_context,
    trace_sequence,
)
from kagg_revue.rl.programs.data import ProgramEpisode, collate_program_episodes
from kagg_revue.rl.programs.model import ProgramActorCritic


def _strategy_actor_architecture() -> ActorArchitecture:
    return ActorArchitecture(
        board_shape=(2, 3, 2, 2),
        unit_shape=(2, 3, 4),
        global_features=7,
        model_width=16,
        entity_width=8,
        attention_heads=2,
        feedforward_width=32,
        latent_tokens=2,
        scene_layers=1,
        temporal_layers=2,
        action_layers=1,
        max_history=4,
        max_decisions=5,
        unit_action_tokens=3,
        market_action_tokens=2,
        maximum_quantity=4,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
        strategy_tokens=2,
        strategy_version="gru-v1",
    )


def test_unused_strategy_can_be_skipped_without_changing_program_context() -> None:
    architecture = _strategy_actor_architecture()
    actor = TurnPolicyNet(architecture).eval()
    batch = 2
    turns = 3
    board = torch.randn((batch, turns, *architecture.board_shape))
    units = torch.randn((batch, turns, *architecture.unit_shape))
    global_features = torch.randn((batch, turns, architecture.global_features))
    actions = torch.zeros((batch, turns, architecture.max_decisions), dtype=torch.long)
    quantities = torch.zeros_like(actions)
    turn_mask = torch.ones((batch, turns), dtype=torch.bool)
    decision_mask = torch.zeros_like(actions, dtype=torch.bool)
    with torch.inference_mode():
        full = actor.encode_sequence(
            board,
            units,
            global_features,
            actions,
            quantities,
            turn_mask,
            decision_mask,
        )
        programs = actor.encode_sequence(
            board,
            units,
            global_features,
            actions,
            quantities,
            turn_mask,
            decision_mask,
            compute_strategy=False,
        )
    assert full.strategy is not None
    assert programs.strategy is None
    torch.testing.assert_close(programs.history, full.history)
    torch.testing.assert_close(programs.memory, full.memory)
    torch.testing.assert_close(programs.memory_mask, full.memory_mask)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_program_turn_graph_matches_incremental_actor_context() -> None:
    from kagg_revue.policy.programs.gpu import ProgramTurnGraph, ProgramTurnInputs

    device = torch.device("cuda")
    architecture = _strategy_actor_architecture()
    actor = TurnPolicyNet(architecture).to(device).eval()
    generator = torch.Generator(device=device).manual_seed(53)

    def inputs() -> ProgramTurnInputs:
        batch = 2
        return ProgramTurnInputs(
            board=torch.randn(
                (batch, *architecture.board_shape),
                generator=generator,
                device=device,
            ),
            units=torch.randn(
                (batch, *architecture.unit_shape),
                generator=generator,
                device=device,
            ),
            global_features=torch.randn(
                (batch, architecture.global_features),
                generator=generator,
                device=device,
            ),
            previous_actions=torch.zeros(
                (batch, architecture.max_decisions),
                dtype=torch.long,
                device=device,
            ),
            previous_quantities=torch.zeros(
                (batch, architecture.max_decisions),
                dtype=torch.long,
                device=device,
            ),
            previous_mask=torch.zeros(
                (batch, architecture.max_decisions),
                dtype=torch.bool,
                device=device,
            ),
            economic_state=None,
        )

    turns = [inputs() for _ in range(3)]
    history = None
    strategy = None
    with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
        graph = ProgramTurnGraph(actor, turns[0])
        try:
            for turn in turns:
                expected, history, strategy, _skill = actor.start_turn(
                    turn.board,
                    turn.units,
                    turn.global_features,
                    turn.previous_actions,
                    turn.previous_quantities,
                    turn.previous_mask,
                    history,
                    strategy_state=strategy,
                    sample_skill=False,
                )
                actual = graph.decode(turn)
                torch.cuda.synchronize(device)
                torch.testing.assert_close(actual.memory, expected.memory, rtol=2e-2, atol=2e-2)
                torch.testing.assert_close(actual.memory_mask, expected.memory_mask, rtol=0, atol=0)
                assert actual.strategy is None
        finally:
            graph.close()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_program_decision_graph_pool_replays_legal_compacted_rows() -> None:
    from kagg_revue.policy.programs.gpu import ProgramDecisionGraphPool

    configuration = {"episodeSteps": 3, "maxMarketOrdersPerTurn": 3}
    unit_limit = 4
    device = torch.device("cuda")
    engines = [native.Engine(seed=seed, configuration=configuration) for seed in (37, 41)]
    sessions = [native.ConditionalProgramSession(configuration, unit_limit) for _engine in engines]
    contract = NativeProgramContract.from_spec(
        native.conditional_program_spec(configuration, unit_limit)
    )
    architecture = contract.architecture(
        context_width=16,
        model_width=16,
        feedforward_width=32,
    )
    policy = ConditionalProgramPolicy(architecture, contract).to(device).eval()
    context = torch.randn((2, 16), device=device)
    tiles = torch.randn((2, contract.tile_count, 16), device=device)
    generator = torch.Generator(device=device).manual_seed(67)
    graphs = ProgramDecisionGraphPool(
        policy,
        generator,
        maximum_rows=2,
    )
    try:
        with torch.autocast("cuda", dtype=torch.bfloat16):
            rollout = decode_program_turn(
                native,
                policy,
                contract,
                sessions,
                engines,
                np.zeros(2, dtype=np.int64),
                context,
                tiles,
                workers=2,
                sample=True,
                generator=generator,
                decision_graphs=graphs,
            )
            replay_engines = [
                native.Engine(seed=seed, configuration=configuration) for seed in (37, 41)
            ]
            replay_sessions = [
                native.ConditionalProgramSession(configuration, unit_limit)
                for _engine in replay_engines
            ]
            generator.manual_seed(67)
            repeated = decode_program_turn(
                native,
                policy,
                contract,
                replay_sessions,
                replay_engines,
                np.zeros(2, dtype=np.int64),
                context,
                tiles,
                workers=2,
                sample=True,
                generator=generator,
                decision_graphs=graphs,
            )
            inputs, actions, masks = trace_sequence(
                rollout.trace,
                context,
                tiles,
                contract,
                device=device,
                validate=True,
            )
            replayed = policy.evaluate_sequence(inputs, actions, masks)
        torch.cuda.synchronize(device)
        np.testing.assert_array_equal(
            repeated.trace.actions,
            rollout.trace.actions,
        )
        np.testing.assert_array_equal(
            repeated.compiled.tokens,
            rollout.compiled.tokens,
        )
        np.testing.assert_array_equal(
            repeated.compiled.quantities,
            rollout.compiled.quantities,
        )
        torch.testing.assert_close(
            replayed.joint_log_probability,
            torch.as_tensor(
                rollout.trace.old_joint_log_probability,
                device=device,
            ),
            rtol=2e-2,
            atol=4e-2,
        )
        torch.testing.assert_close(
            replayed.factor_counts,
            torch.as_tensor(
                rollout.trace.stochastic_factor_counts,
                device=device,
                dtype=replayed.factor_counts.dtype,
            ),
        )
    finally:
        graphs.close()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_gpu_compiler_matches_native_for_v2_program_tasks() -> None:
    from kagg_revue.policy.programs.gpu.compiler import ProgramGpuCompiler

    configuration = {"episodeSteps": 8, "maxMarketOrdersPerTurn": 3}
    engine = native.Engine(seed=83, configuration=configuration)
    engine.step(
        {
            "farmer": ["PASS"],
            "market": [
                ["BUY_SEED", "WHEAT", 1],
                ["BUY_PRODUCT", "WHEAT", 2],
            ],
        },
        {"farmer": ["PASS"]},
    )
    unit_limit = 4
    contract = NativeProgramContract.from_spec(
        native.conditional_program_spec(configuration, unit_limit)
    )
    device = torch.device("cuda:1" if torch.cuda.device_count() > 1 else "cuda:0")

    def gpu_token(decision: tuple[int, int, int, int]) -> int:
        policy_batch = native.engine_policy_session_batch(
            [engine], [0], unit_limit, 1
        )
        state = torch.as_tensor(
            np.asarray(policy_batch.gpu_state_compact(), dtype=np.int32),
            device=device,
        )
        compiler = ProgramGpuCompiler(
            contract,
            1,
            device,
            episode_steps=int(engine.configuration["episodeSteps"]),
            turns_per_day=int(engine.configuration["turnsPerDay"]),
        )
        compiler.begin_turn(state, int(engine.step_index))
        control, task, target, argument = decision
        values = {
            "control": control,
            "task": task,
            "target": target,
            "argument": argument,
            "direction": 0,
            "raw_operation": 0,
            "quantity_mode": 0,
            "exact_quantity": 1,
            "market_order": 0,
        }
        actions = ProgramActions(
            **{
                name: torch.tensor([value], dtype=torch.long, device=device)
                for name, value in values.items()
            }
        )
        with torch.cuda.device(device):
            compiler.apply_selection(
                actions,
                torch.zeros(1, dtype=torch.long, device=device),
                torch.ones(1, dtype=torch.bool, device=device),
            )
            return int(compiler.output().tokens[0, 0].item())

    observation = engine.observation(0)
    x, y = observation["farms"][0]["farmer"]
    board_size = int(engine.configuration["boardSize"])
    opposite_shed = (y + 1) * board_size + (x + 1)
    current = y * board_size + x
    decisions = (
        UnitDecision(
            ControlType.ASSIGN,
            task=TaskType.FETCH,
            target=opposite_shed,
            argument=0,
        ),
        UnitDecision(
            ControlType.ASSIGN,
            task=TaskType.PLANT,
            target=current,
            argument=0,
        ),
        UnitDecision(ControlType.ASSIGN, task=TaskType.WAIT),
    )
    for decision in decisions:
        session = ProgramSession(configuration, unit_limit=unit_limit, backend=native)
        session.select_unit(engine, 0, decision)
        session.select_market(engine, 0, MarketDecision(MarketOrderType.END))
        expected = int(session.compile(engine, 0).tokens[0])
        actual = gpu_token(
            (
                int(decision.control),
                int(decision.task),
                decision.target,
                decision.argument,
            )
        )
        assert actual == expected

    engine.step(
        {"farmer": ["PICKUP", "WHEAT", 2]},
        {"farmer": ["PASS"]},
    )
    observation = engine.observation(0)
    x, y = observation["farms"][0]["farmer"]
    target = y * board_size + x
    decision = UnitDecision(
        ControlType.ASSIGN,
        task=TaskType.STORE_ALL,
        target=target,
    )
    session = ProgramSession(configuration, unit_limit=unit_limit, backend=native)
    session.select_unit(engine, 0, decision)
    session.select_market(engine, 0, MarketDecision(MarketOrderType.END))
    assert gpu_token(
        (int(decision.control), int(decision.task), target, decision.argument)
    ) == int(session.compile(engine, 0).tokens[0])


def test_batched_program_trace_replays_through_causal_actor_context() -> None:
    configuration = {
        "episodeSteps": 4,
        "maxMarketOrdersPerTurn": 3,
    }
    unit_limit = 4
    engine = native.Engine(seed=31, configuration=configuration)
    contract = NativeProgramContract.from_spec(
        native.conditional_program_spec(configuration, unit_limit)
    )
    policy_batch = native.engine_policy_session_batch([engine], [0], unit_limit, 1)
    board_raw, units_raw, global_raw = policy_batch.encode_compact()
    board_values = np.asarray(board_raw, dtype=np.float16)
    unit_values = np.asarray(units_raw, dtype=np.float16)
    global_values = np.asarray(global_raw, dtype=np.float32)
    codec = native.action_codec_spec()
    actor_architecture = ActorArchitecture(
        board_shape=tuple(board_values.shape[1:]),
        unit_shape=tuple(unit_values.shape[1:]),
        global_features=global_values.shape[1],
        model_width=8,
        entity_width=4,
        attention_heads=1,
        feedforward_width=16,
        latent_tokens=2,
        scene_layers=0,
        temporal_layers=1,
        action_layers=1,
        max_history=4,
        max_decisions=contract.maximum_decisions,
        unit_action_tokens=int(codec["unit_tokens"]),
        market_action_tokens=int(codec["market_tokens"]),
        maximum_quantity=4,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
    )
    actor = TurnPolicyNet(actor_architecture).eval()
    program_architecture = contract.architecture(
        context_width=actor_architecture.model_width,
        model_width=8,
        feedforward_width=16,
    )
    programs = ConditionalProgramPolicy(program_architecture, contract).eval()
    model = ProgramActorCritic(actor, programs).eval()
    board = torch.as_tensor(board_values)
    units = torch.as_tensor(unit_values)
    globals_ = torch.as_tensor(global_values)
    previous_actions = torch.zeros((1, actor_architecture.max_decisions), dtype=torch.long)
    previous_quantities = torch.zeros_like(previous_actions)
    previous_mask = torch.zeros_like(previous_actions, dtype=torch.bool)
    turn_context, _history, _strategy, _skill = actor.start_turn(
        board,
        units,
        globals_,
        previous_actions,
        previous_quantities,
        previous_mask,
        None,
    )
    context, tile_tokens = program_context(actor_architecture, turn_context)
    session = native.ConditionalProgramSession(configuration, unit_limit)
    rollout = decode_program_turn(
        native,
        programs,
        contract,
        [session],
        [engine],
        np.zeros(1, dtype=np.int64),
        context,
        tile_tokens,
        workers=1,
        sample=False,
        validate_inputs=True,
    )
    trace = rollout.trace
    compiled = rollout.compiled
    episode = ProgramEpisode(
        episode_id="synthetic-program",
        opponent_id="synthetic",
        seed=31,
        seat=0,
        outcome=0,
        terminal_cash=0.0,
        opponent_cash=0.0,
        board=board_values,
        units=unit_values,
        global_features=global_values,
        economic_state=np.zeros((1, 0), dtype=np.int32),
        actions=compiled.tokens,
        quantities=compiled.quantities,
        action_decision_counts=compiled.decision_counts.astype(np.int16),
        program_scalars=trace.scalars,
        program_root_features=trace.root_features,
        program_option_features=trace.option_features,
        program_target_reservations=trace.target_reservations,
        program_actions=trace.actions,
        program_conditional_masks=trace.conditional_masks,
        program_quantity_max=trace.quantity_max,
        program_decision_counts=trace.decision_counts,
        old_joint_log_probability=trace.old_joint_log_probability,
        old_values=trace.old_values,
        stochastic_factor_counts=trace.stochastic_factor_counts,
    )
    batch = collate_program_episodes(
        [episode],
        contract,
        actor_architecture.model_width,
        torch.device("cpu"),
        validate=True,
    )
    replayed = model(
        batch.board,
        batch.units,
        batch.global_features,
        batch.actions,
        batch.quantities,
        batch.turn_mask,
        batch.decision_mask,
        batch.program_inputs,
        batch.program_actions,
        batch.program_masks,
        batch.program_episode_index,
        batch.program_turn_index,
        economic_state=None,
    )
    torch.testing.assert_close(
        replayed.programs.joint_log_probability,
        batch.old_joint_log_probability,
        atol=1e-5,
        rtol=1e-5,
    )
