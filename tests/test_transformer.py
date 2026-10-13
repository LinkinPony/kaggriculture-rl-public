import torch

from kagg_revue.policy.model import (
    ActionDecoder,
    ActorArchitecture,
    SceneEncoder,
    TurnContext,
    TurnPolicyNet,
)
from kagg_revue.policy.skills import LatentSkillModel
from kagg_revue.policy.strategy import StrategyWorkspace
from kagg_revue.policy.transformer import TemporalTransformer


def test_incremental_history_matches_full_causal_history() -> None:
    torch.manual_seed(7)
    model = TemporalTransformer(
        width=16,
        heads=2,
        feedforward=24,
        layers=2,
        max_history=8,
    ).eval()
    sequence = torch.randn(2, 5, 16)
    with torch.inference_mode():
        full = model(sequence)
        state = None
        incremental = []
        for turn in range(sequence.shape[1]):
            output, state = model.step(sequence[:, turn : turn + 1], state)
            incremental.append(output)
    assert torch.allclose(full, torch.cat(incremental, dim=1), atol=1e-5, rtol=1e-5)


def test_scene_registers_are_internal_but_influence_formal_latents() -> None:
    torch.manual_seed(9)
    architecture = ActorArchitecture(
        board_shape=(2, 3, 2, 2),
        unit_shape=(2, 2, 4),
        global_features=3,
        model_width=16,
        entity_width=8,
        attention_heads=2,
        feedforward_width=24,
        latent_tokens=2,
        register_tokens=3,
        scene_layers=1,
        temporal_layers=1,
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
    )
    scene_encoder = SceneEncoder(architecture)
    batch = 2
    encoding = scene_encoder(
        board=torch.randn(batch, *architecture.board_shape),
        units=torch.ones(batch, *architecture.unit_shape),
        global_features=torch.randn(batch, architecture.global_features),
        previous_actions=torch.zeros(
            batch, architecture.max_decisions, dtype=torch.long
        ),
        previous_quantities=torch.zeros(
            batch, architecture.max_decisions, dtype=torch.long
        ),
        previous_mask=torch.ones(
            batch, architecture.max_decisions, dtype=torch.bool
        ),
    )

    raw_tokens = 8 + 4 + architecture.global_features + architecture.max_decisions
    assert encoding.registers.shape == (
        batch,
        architecture.register_tokens,
        architecture.model_width,
    )
    assert encoding.memory.shape == (
        batch,
        architecture.latent_tokens + raw_tokens,
        architecture.model_width,
    )
    encoding.summary.square().mean().backward()  # type: ignore[no-untyped-call]
    assert scene_encoder.register_tokens is not None
    assert scene_encoder.register_tokens.grad is not None
    assert torch.count_nonzero(scene_encoder.register_tokens.grad) > 0


def test_incremental_action_decoder_matches_teacher_forcing() -> None:
    torch.manual_seed(11)
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
        temporal_layers=1,
        action_layers=2,
        max_history=8,
        max_decisions=5,
        unit_action_tokens=4,
        market_action_tokens=3,
        maximum_quantity=7,
        derived_fact_version="synthetic-facts",
        turn_fact_features=3,
        prefix_fact_features=4,
        candidate_fact_features=5,
        fact_dropout=0.0,
    )
    decoder = ActionDecoder(architecture).eval()
    actions = torch.randint(0, architecture.action_tokens, (2, 4))
    quantities = torch.randint(0, 10, (2, 4))
    phases = torch.randint(0, 2, (2, 4))
    decision_mask = torch.ones_like(actions, dtype=torch.bool)
    context = TurnContext(
        memory=torch.randn(2, 6, architecture.model_width),
        memory_mask=torch.ones(2, 6, dtype=torch.bool),
    )
    prefix_facts = torch.randn(2, 4, architecture.prefix_fact_features)
    candidate_facts = torch.randn(
        2,
        4,
        architecture.action_tokens,
        architecture.candidate_fact_features,
    )
    candidate_facts[..., 0] = 1.0
    action_head_noise = torch.randn(
        2,
        architecture.action_tokens,
        architecture.model_width,
    )
    with torch.inference_mode():
        full = decoder(
            actions,
            quantities,
            phases,
            decision_mask,
            context.memory,
            context.memory_mask,
            prefix_facts,
            candidate_facts,
            action_head_noise=action_head_noise,
        )
        state = decoder.initial_state(context)
        fixed_state = decoder.initial_fixed_state(context)
        incremental_logits = []
        incremental_quantities = []
        fixed_logits = []
        fixed_quantities = []
        for position in range(actions.shape[1]):
            previous_action = None if position == 0 else actions[:, position - 1]
            previous_quantity = None if position == 0 else quantities[:, position - 1]
            logits, hidden, state = decoder.next_cached(
                previous_action,
                previous_quantity,
                phases[:, position],
                context,
                state,
                prefix_facts[:, position],
                candidate_facts[:, position],
                action_head_noise=action_head_noise,
            )
            incremental_logits.append(logits[:, None])
            selected_facts = candidate_facts[
                torch.arange(actions.shape[0]), position, actions[:, position]
            ]
            incremental_quantities.append(
                decoder.quantity_logits(
                    hidden,
                    actions[:, position],
                    selected_facts,
                )[:, None]
            )
            fixed_previous_action = (
                torch.full(
                    (actions.shape[0],),
                    decoder.begin_token,
                    dtype=torch.long,
                )
                if previous_action is None
                else previous_action
            )
            fixed_previous_quantity = (
                torch.zeros(actions.shape[0], dtype=torch.long)
                if previous_quantity is None
                else previous_quantity
            )
            fixed_logit, fixed_hidden, fixed_state = decoder.next_cached_fixed(
                fixed_previous_action,
                fixed_previous_quantity,
                phases[:, position],
                context,
                fixed_state,
                torch.tensor(position),
                prefix_facts[:, position],
                candidate_facts[:, position],
                action_head_noise=action_head_noise,
            )
            fixed_logits.append(fixed_logit[:, None])
            fixed_quantities.append(
                decoder.quantity_logits(
                    fixed_hidden,
                    actions[:, position],
                    selected_facts,
                )[:, None]
            )
    assert torch.allclose(
        full.action_logits,
        torch.cat(incremental_logits, dim=1),
        atol=1e-5,
        rtol=1e-5,
    )
    assert torch.allclose(
        full.quantity_logits,
        torch.cat(incremental_quantities, dim=1),
        atol=1e-5,
        rtol=1e-5,
    )
    assert torch.allclose(
        torch.cat(incremental_logits, dim=1),
        torch.cat(fixed_logits, dim=1),
        atol=1e-5,
        rtol=1e-5,
    )
    assert torch.allclose(
        torch.cat(incremental_quantities, dim=1),
        torch.cat(fixed_quantities, dim=1),
        atol=1e-5,
        rtol=1e-5,
    )


def test_batched_action_prefill_matches_incremental_suffix() -> None:
    torch.manual_seed(17)
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
        temporal_layers=1,
        action_layers=2,
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
    )
    decoder = ActionDecoder(architecture).eval()
    actions = torch.randint(0, architecture.action_tokens, (2, 3))
    quantities = torch.randint(0, 7, (2, 3))
    phases = torch.randint(0, 2, (2, 3))
    context = TurnContext(
        memory=torch.randn(2, 6, architecture.model_width),
        memory_mask=torch.ones(2, 6, dtype=torch.bool),
    )
    with torch.inference_mode():
        incremental = decoder.initial_fixed_state(context)
        previous_action = torch.full(
            (2,), decoder.begin_token, dtype=torch.long
        )
        previous_quantity = torch.zeros(2, dtype=torch.long)
        for position in range(actions.shape[1]):
            incremental = decoder.advance_cached_fixed(
                previous_action,
                previous_quantity,
                phases[:, position],
                context,
                incremental,
                torch.tensor(position),
            )
            previous_action = actions[:, position]
            previous_quantity = quantities[:, position]
        prefetched = decoder.prefill_fixed(
            actions,
            quantities,
            phases,
            torch.ones_like(actions, dtype=torch.bool),
            context,
        )
        next_phase = torch.randint(0, 2, (2,))
        expected, _expected_hidden, _incremental = decoder.next_cached_fixed(
            previous_action,
            previous_quantity,
            next_phase,
            context,
            incremental,
            torch.tensor(actions.shape[1]),
        )
        actual, _actual_hidden, _prefetched = decoder.next_cached_fixed(
            previous_action,
            previous_quantity,
            next_phase,
            context,
            prefetched,
            torch.tensor(actions.shape[1]),
        )
    torch.testing.assert_close(actual, expected, atol=1e-5, rtol=1e-5)


def test_latent_sequence_matches_incremental_causal_selection() -> None:
    torch.manual_seed(19)
    skills = LatentSkillModel(width=8, skill_tokens=4).eval()
    history = torch.randn(1, 3, 8)
    turn_mask = torch.ones(1, 3, dtype=torch.bool)

    sequence = skills.sequence(history, turn_mask, sample=False)
    steps = [skills.step(history[:, turn], sample=False) for turn in range(history.shape[1])]

    assert torch.equal(sequence.ids, torch.stack([step.ids for step in steps], dim=1))
    assert torch.allclose(
        sequence.embeddings,
        torch.stack([step.embeddings for step in steps], dim=1),
    )


def test_latent_bc_objective_updates_selector_and_codebook() -> None:
    torch.manual_seed(23)
    skills = LatentSkillModel(width=8, skill_tokens=4)
    history = torch.randn(2, 4, 8, requires_grad=True)
    turn_mask = torch.ones(2, 4, dtype=torch.bool)
    output = skills.sequence(history, turn_mask, sample=True)
    loss = output.embeddings.square().mean()

    loss.backward()  # type: ignore[no-untyped-call]

    assert skills.prior[-1].weight.grad is not None
    assert skills.codebook.weight.grad is not None


def test_strategy_sequence_matches_eager_turn_and_action_replay() -> None:
    torch.manual_seed(29)
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
        action_layers=2,
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
    actor = TurnPolicyNet(architecture).eval()
    for block in actor.action.blocks:
        assert block.strategy_cross is not None
        torch.nn.init.normal_(block.strategy_cross.attention.output.weight, std=0.05)
    batch, turns, decisions = 2, 4, 4
    board = torch.randn(batch, turns, *architecture.board_shape)
    units = torch.randn(batch, turns, *architecture.unit_shape)
    global_features = torch.randn(batch, turns, architecture.global_features)
    actions = torch.randint(0, architecture.action_tokens, (batch, turns, decisions))
    quantities = torch.randint(0, 5, actions.shape)
    phases = torch.randint(0, 2, actions.shape)
    turn_mask = torch.ones(batch, turns, dtype=torch.bool)
    decision_mask = torch.ones_like(actions, dtype=torch.bool)
    previous_actions, previous_quantities, previous_mask = actor._previous_actions(
        actions,
        quantities,
        decision_mask,
    )

    with torch.inference_mode():
        encoding = actor.encode_sequence(
            board,
            units,
            global_features,
            actions,
            quantities,
            turn_mask,
            decision_mask,
        )
        expected = actor.decode_sequence(
            encoding,
            actions,
            quantities,
            phases,
            decision_mask,
        )
        history = None
        strategy = None
        for turn in range(turns):
            context, history, strategy, skill = actor.start_turn(
                board[:, turn],
                units[:, turn],
                global_features[:, turn],
                previous_actions[:, turn],
                previous_quantities[:, turn],
                previous_mask[:, turn],
                history,
                strategy_state=strategy,
            )
            assert skill is None
            assert strategy is not None
            assert encoding.strategy is not None
            torch.testing.assert_close(
                context.memory[:, 0], encoding.history[:, turn], atol=1e-5, rtol=1e-5
            )
            assert context.strategy is not None
            torch.testing.assert_close(
                context.strategy,
                encoding.strategy[:, turn],
                atol=1e-5,
                rtol=1e-5,
            )
            state = actor.action.initial_state(context)
            for position in range(decisions):
                previous_action = (
                    None if position == 0 else actions[:, turn, position - 1]
                )
                previous_quantity = (
                    None if position == 0 else quantities[:, turn, position - 1]
                )
                logits, hidden, state = actor.action.next_cached(
                    previous_action,
                    previous_quantity,
                    phases[:, turn, position],
                    context,
                    state,
                )
                torch.testing.assert_close(
                    logits,
                    expected.action_logits[:, turn, position],
                    atol=1e-5,
                    rtol=1e-5,
                )
                quantity_logits = actor.action.quantity_logits(
                    hidden, actions[:, turn, position]
                )
                torch.testing.assert_close(
                    quantity_logits,
                    expected.quantity_logits[:, turn, position],
                    atol=1e-5,
                    rtol=1e-5,
                )


def test_strategy_padding_preserves_recurrent_state() -> None:
    torch.manual_seed(31)
    workspace = StrategyWorkspace(width=8, heads=1, feedforward=12, slots=3).eval()
    history = torch.randn(2, 4, 8)
    scene = torch.randn(2, 4, 2, 8)
    valid = torch.tensor([[True, True, False, False], [True, False, True, False]])

    with torch.inference_mode():
        sequence = workspace.sequence(history, scene, valid)
        state = workspace.initial_state(2)
        expected = []
        for turn in range(history.shape[1]):
            transition = workspace.step(state, history[:, turn], scene[:, turn])
            state = torch.where(valid[:, turn, None, None], transition.state, state)
            expected.append(workspace._readout(state))

    torch.testing.assert_close(sequence, torch.stack(expected, dim=1))
    torch.testing.assert_close(sequence[0, 2], sequence[0, 1])
    torch.testing.assert_close(sequence[0, 3], sequence[0, 2])
    torch.testing.assert_close(sequence[1, 1], sequence[1, 0])
    torch.testing.assert_close(sequence[1, 3], sequence[1, 2])
