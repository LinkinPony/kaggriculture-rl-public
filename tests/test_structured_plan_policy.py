from __future__ import annotations

import numpy as np
import pytest
import torch

from kagg_revue.policy.plans import (
    BOARD_SHAPE,
    CONTINUE,
    ECONOMIC_STATE_FEATURES,
    GLOBAL_FEATURES,
    GLOBAL_FIELDS,
    GLOBAL_SET,
    LINE_FIELDS,
    PRODUCTION_LINES,
    STOP,
    UNIT_SHAPE,
    UPSERT,
    PlanInputs,
    StructuredPlanArchitecture,
    StructuredPlanPolicy,
)


def _architecture(
    observation_features: int = 12,
    journal_features: int = 5,
    event_features: int = 7,
) -> StructuredPlanArchitecture:
    return StructuredPlanArchitecture(
        observation_features=observation_features,
        journal_features=journal_features,
        event_features=event_features,
        production_lines=PRODUCTION_LINES,
        line_fields=LINE_FIELDS,
        global_fields=GLOBAL_FIELDS,
        model_width=24,
        feedforward_width=48,
    )


def _inputs(batch: int) -> PlanInputs:
    lines = torch.zeros(batch, PRODUCTION_LINES, LINE_FIELDS, dtype=torch.long)
    mask = torch.zeros(batch, PRODUCTION_LINES, dtype=torch.bool)
    lines[0, 0] = torch.tensor([2, 0, 3, 1, 0, 0])
    lines[0, 5] = torch.tensor([1, 1, 2, 0, 1, 1])
    mask[0, (0, 5)] = True
    return PlanInputs(
        board=torch.randn(batch, *BOARD_SHAPE),
        units=torch.randn(batch, *UNIT_SHAPE),
        global_features=torch.randn(batch, GLOBAL_FEATURES),
        economic_state=torch.zeros(
            batch,
            ECONOMIC_STATE_FEATURES,
            dtype=torch.int32,
        ),
        features=torch.randn(batch, 12),
        journal=torch.randn(batch, 5),
        events=torch.randint(0, 2, (batch, 7)).float(),
        active_lines=lines,
        active_line_mask=mask,
        global_plan=torch.zeros(batch, GLOBAL_FIELDS, dtype=torch.long),
    )


def _continue_policy() -> StructuredPlanPolicy:
    policy = StructuredPlanPolicy(_architecture())
    with torch.no_grad():
        policy.mode_head.weight.zero_()
        policy.mode_head.bias.copy_(torch.tensor([50.0, -50.0]))
    return policy


def _events(inputs: PlanInputs, event: int) -> PlanInputs:
    values = torch.zeros_like(inputs.events)
    values[:, event] = 1.0
    return PlanInputs(
        board=inputs.board,
        units=inputs.units,
        global_features=inputs.global_features,
        economic_state=inputs.economic_state,
        features=inputs.features,
        journal=inputs.journal,
        events=values,
        active_lines=inputs.active_lines,
        active_line_mask=inputs.active_line_mask,
        global_plan=inputs.global_plan,
    )


def test_fresh_plan_heads_are_neutral_except_for_sparse_edits() -> None:
    policy = StructuredPlanPolicy(_architecture())
    for head in (
        policy.mode_head,
        policy.line_operation_head,
        policy.line_value_head,
        policy.global_operation_head,
        policy.global_value_head,
    ):
        assert torch.count_nonzero(head.weight) == 0
    torch.testing.assert_close(
        torch.softmax(policy.mode_head.bias, dim=0),
        torch.tensor([0.5, 0.5]),
    )
    torch.testing.assert_close(
        torch.softmax(policy.line_operation_head.bias, dim=0),
        torch.tensor([0.9, 0.08, 0.02]),
    )
    torch.testing.assert_close(
        torch.softmax(policy.global_operation_head.bias, dim=0),
        torch.tensor([0.9, 0.1]),
    )


def _concat_inputs(values: tuple[PlanInputs, ...]) -> PlanInputs:
    return PlanInputs(
        **{
            name: torch.cat(tuple(getattr(value, name) for value in values))
            for name in PlanInputs.__dataclass_fields__
        }
    )


def test_structured_plan_policy_replays_exact_sparse_patch_likelihood() -> None:
    torch.manual_seed(11)
    policy = _continue_policy()
    inputs = _inputs(16)
    rollout = policy.rollout(
        inputs,
        sample=True,
        generator=torch.Generator().manual_seed(12),
    )
    replay = policy.evaluate_actions(
        inputs,
        rollout.actions,
        rollout.masks,
        validate=True,
    )
    actions = rollout.actions
    assert torch.all(actions.mode == CONTINUE)
    assert torch.equal(actions.mode, replay.actions.mode)
    assert torch.equal(actions.line_operations, replay.actions.line_operations)
    assert torch.equal(actions.line_values, replay.actions.line_values)
    assert torch.allclose(rollout.joint_log_probability, replay.joint_log_probability)
    assert torch.allclose(rollout.entropy, replay.entropy)

    upsert = actions.line_operations == UPSERT
    assert torch.count_nonzero(actions.line_values[~upsert]) == 0
    assert torch.count_nonzero(actions.global_values[actions.global_operation != GLOBAL_SET]) == 0
    expected_factors = (
        1
        + PRODUCTION_LINES
        + upsert.sum(dim=1) * LINE_FIELDS
        + 1
        + (actions.global_operation == GLOBAL_SET).long() * GLOBAL_FIELDS
    )
    assert torch.equal(rollout.factor_counts, expected_factors)

    # Initial portfolios must create at least one complete line and global policy.
    assert torch.all(upsert[1:].any(dim=1))
    assert torch.all(actions.global_operation[1:] == GLOBAL_SET)

    # Every active-line UPSERT and global SET is a real semantic change.
    active_upsert = inputs.active_line_mask & upsert
    assert torch.all((actions.line_values != inputs.active_lines).any(dim=-1)[active_upsert])
    global_set = actions.global_operation == GLOBAL_SET
    initialized_set = global_set & inputs.active_line_mask.any(dim=1)
    assert torch.all((actions.global_values != inputs.global_plan).any(dim=1)[initialized_set])


def test_rollout_behavior_omits_entropy_without_changing_persisted_fields() -> None:
    torch.manual_seed(13)
    policy = _continue_policy().eval()
    inputs = _events(_inputs(4), 0)
    with torch.no_grad():
        full, _full_state = policy.rollout_advance(
            inputs,
            None,
            sample=True,
            generator=torch.Generator().manual_seed(14),
        )
        behavior, _behavior_state = policy.rollout_behavior_advance(
            inputs,
            None,
            generator=torch.Generator().manual_seed(14),
        )

    for name in full.actions.__dataclass_fields__:
        assert torch.equal(
            getattr(behavior.actions, name),
            getattr(full.actions, name),
        )
    for name in full.masks.__dataclass_fields__:
        assert torch.equal(
            getattr(behavior.masks, name),
            getattr(full.masks, name),
        )
    torch.testing.assert_close(
        behavior.joint_log_probability,
        full.joint_log_probability,
    )
    torch.testing.assert_close(behavior.value, full.value)


def test_day_history_rollout_matches_sequence_replay_and_is_causal() -> None:
    torch.manual_seed(17)
    policy = _continue_policy().eval()
    initial = _events(_inputs(2), 0)
    constraint = _events(_inputs(2), 2)
    next_day = _events(_inputs(2), 1)
    with torch.no_grad():
        first, state = policy.rollout_advance(initial, None, sample=False)
        middle = policy.rollout_event(
            constraint,
            state.current_history,
            state.current_strategy,
            sample=False,
        )
        final, _state = policy.rollout_advance(next_day, state, sample=False)

    inputs = _concat_inputs((initial, constraint, next_day))
    outputs = (first, middle, final)
    action_type = type(first.actions)
    actions = action_type(
        **{
            name: torch.cat(tuple(getattr(output.actions, name) for output in outputs))
            for name in first.actions.__dataclass_fields__
        }
    )
    mask_type = type(first.masks)
    masks = mask_type(
        **{
            name: torch.cat(tuple(getattr(output.masks, name) for output in outputs))
            for name in first.masks.__dataclass_fields__
        }
    )
    episode_index = torch.tensor([0, 1, 0, 1, 0, 1])
    with torch.no_grad():
        replay = policy.evaluate_actions(
            inputs,
            actions,
            masks,
            episode_index=episode_index,
            validate=True,
        )
    expected = torch.cat(tuple(output.joint_log_probability for output in outputs))
    torch.testing.assert_close(replay.joint_log_probability, expected)

    changed_board = inputs.board.clone()
    changed_board[-2:] += 10.0
    changed = PlanInputs(
        board=changed_board,
        units=inputs.units,
        global_features=inputs.global_features,
        economic_state=inputs.economic_state,
        features=inputs.features,
        journal=inputs.journal,
        events=inputs.events,
        active_lines=inputs.active_lines,
        active_line_mask=inputs.active_line_mask,
        global_plan=inputs.global_plan,
    )
    with torch.no_grad():
        causal = policy.evaluate_actions(
            changed,
            actions,
            masks,
            episode_index=episode_index,
        )
    torch.testing.assert_close(
        causal.joint_log_probability[:-2],
        replay.joint_log_probability[:-2],
    )


def test_action_only_opponent_path_preserves_sampled_bundle() -> None:
    torch.manual_seed(19)
    policy = _continue_policy().eval()
    inputs = _events(_inputs(4), 0)
    with torch.no_grad():
        _anchor, state = policy.rollout_advance(
            inputs,
            None,
            sample=True,
            generator=torch.Generator().manual_seed(20),
        )
        full = policy.rollout_event(
            inputs,
            state.current_history,
            state.current_strategy,
            sample=True,
            generator=torch.Generator().manual_seed(21),
        )
        actions = policy.sample_actions_event(
            inputs,
            state.current_history,
            state.current_strategy,
            generator=torch.Generator().manual_seed(21),
        )

    for name in full.actions.__dataclass_fields__:
        assert torch.equal(getattr(full.actions, name), getattr(actions, name))


def test_structured_plan_stop_requires_an_active_portfolio() -> None:
    policy = StructuredPlanPolicy(_architecture())
    with torch.no_grad():
        policy.mode_head.weight.zero_()
        policy.mode_head.bias.copy_(torch.tensor([-50.0, 50.0]))
        policy.line_operation_head.weight.zero_()
        policy.line_operation_head.bias.copy_(torch.tensor([50.0, -50.0, -50.0]))
        policy.global_operation_head.weight.zero_()
        policy.global_operation_head.bias.copy_(torch.tensor([50.0, -50.0]))
    output = policy.rollout(_inputs(4), sample=False)
    assert output.actions.mode[0] == STOP
    assert torch.all(output.actions.mode[1:] == CONTINUE)
    assert torch.count_nonzero(output.actions.line_operations[0]) == 0
    assert torch.count_nonzero(output.actions.line_values[0]) == 0
    assert output.actions.global_operation[0] == 0
    assert output.factor_counts[0] == 1 + PRODUCTION_LINES + 1
    assert torch.all((output.actions.line_operations[1:] == UPSERT).any(dim=1))
    assert torch.all(output.actions.global_operation[1:] == GLOBAL_SET)
    assert torch.all(output.actions.global_values[1:, 2] <= 9)
    assert torch.all(output.actions.global_values[1:, 3] >= 5)


def test_structured_plan_critic_does_not_train_actor_encoder() -> None:
    torch.manual_seed(21)
    policy = _continue_policy()
    inputs = _inputs(4)
    output = policy.rollout(inputs, sample=False)
    output.value_logits.square().mean().backward()
    assert policy.outcome_head.network[-1].weight.grad is not None
    assert policy.backbone.portfolio.features.network[0].weight.grad is None
    assert policy.mode_head.weight.grad is None

    policy.zero_grad(set_to_none=True)
    replay = policy.evaluate_actions(inputs, output.actions, output.masks)
    (-replay.joint_log_probability.mean()).backward()
    assert policy.backbone.portfolio.features.network[0].weight.grad is not None
    assert policy.backbone.scene.tile_encoder.network[0].weight.grad is not None
    assert policy.mode_head.weight.grad is not None


def test_structured_plan_stored_masks_and_inactive_lines_are_audited() -> None:
    policy = _continue_policy()
    inputs = _inputs(3)
    output = policy.rollout(
        inputs,
        sample=True,
        generator=torch.Generator().manual_seed(32),
    )
    corrupted = output.masks.line_operations.clone()
    corrupted[:, -1] = False
    corrupted[:, -1, 0] = True
    masks = type(output.masks)(
        mode=output.masks.mode,
        line_operations=corrupted,
        line_values=output.masks.line_values,
        global_operation=output.masks.global_operation,
        global_values=output.masks.global_values,
        factors=output.masks.factors,
    )
    with pytest.raises(ValueError, match="line-operation"):
        policy.evaluate_actions(inputs, output.actions, masks, validate=True)

    malformed_lines = inputs.active_lines.clone()
    malformed_lines[1, 2, 0] = 1
    malformed = PlanInputs(
        board=inputs.board,
        units=inputs.units,
        global_features=inputs.global_features,
        economic_state=inputs.economic_state,
        features=inputs.features,
        journal=inputs.journal,
        events=inputs.events,
        active_lines=malformed_lines,
        active_line_mask=inputs.active_line_mask,
        global_plan=inputs.global_plan,
    )
    with pytest.raises(ValueError, match="canonical zero"):
        policy.rollout(malformed, sample=False)


def test_sampled_portfolio_language_is_accepted_by_native_executor() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    architecture = _architecture(90, 32, 32)
    policy = StructuredPlanPolicy(architecture)
    with torch.no_grad():
        policy.mode_head.weight.zero_()
        policy.mode_head.bias.copy_(torch.tensor([50.0, -50.0]))
    inputs = PlanInputs(
        board=torch.randn(32, *BOARD_SHAPE),
        units=torch.randn(32, *UNIT_SHAPE),
        global_features=torch.randn(32, GLOBAL_FEATURES),
        economic_state=torch.zeros(
            32,
            ECONOMIC_STATE_FEATURES,
            dtype=torch.int32,
        ),
        features=torch.randn(32, 90),
        journal=torch.randn(32, 32),
        events=torch.zeros(32, 32),
        active_lines=torch.zeros(32, PRODUCTION_LINES, LINE_FIELDS, dtype=torch.long),
        active_line_mask=torch.zeros(32, PRODUCTION_LINES, dtype=torch.bool),
        global_plan=torch.zeros(32, GLOBAL_FIELDS, dtype=torch.long),
    )
    output = policy.rollout(
        inputs,
        sample=True,
        generator=torch.Generator().manual_seed(51),
    )
    configuration = {"episodeSteps": 48}
    for row in range(32):
        engine = native.Engine(seed=53 + row, configuration=configuration)
        session = native.StructuredPlanSession(configuration)
        session.apply(
            engine,
            0,
            int(output.actions.mode[row]),
            output.actions.line_operations[row].numpy().astype(np.int64),
            output.actions.line_values[row].numpy().astype(np.int64),
            int(output.actions.global_operation[row]),
            output.actions.global_values[row].numpy().astype(np.int64),
        )
