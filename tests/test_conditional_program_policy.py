from __future__ import annotations

import numpy as np
import torch

from kagg_revue.native import _revue_native as native
from kagg_revue.policy.programs import (
    ConditionalProgramPolicy,
    ControlType,
    MarketOrderType,
    NativeProgramContract,
    ProgramActionSequence,
    ProgramMaskSequence,
    ProgramSequenceInputs,
    QuantityMode,
    TaskType,
    decision_inputs,
)


def _policy(*, context_width: int = 32) -> tuple[NativeProgramContract, ConditionalProgramPolicy]:
    contract = NativeProgramContract.from_spec(native.conditional_program_spec())
    architecture = contract.architecture(
        context_width=context_width,
        model_width=32,
        feedforward_width=64,
    )
    return contract, ConditionalProgramPolicy(architecture, contract)


def _tensors(
    raw: dict[str, object], contract: NativeProgramContract, width: int = 32
) -> tuple[object, object, torch.Tensor]:
    batch = int(np.asarray(raw["scalars"]).shape[0])
    context = torch.randn(batch, width)
    tiles = torch.randn(batch, contract.tile_count, width)
    inputs, masks = decision_inputs(raw, context, tiles, contract, device="cpu", validate=True)
    return inputs, masks, context


def test_exact_quantity_binary_replay_is_lossless() -> None:
    _contract, policy = _policy()
    bounds: list[int] = []
    quantities: list[int] = []
    for maximum in range(2, 33):
        bounds.extend([maximum] * maximum)
        quantities.extend(range(1, maximum + 1))
    quantity_max = torch.tensor(bounds, dtype=torch.long)
    selected = torch.tensor(quantities, dtype=torch.long)
    state = torch.randn(len(bounds), policy.architecture.model_width)
    output = policy.exact.evaluate(
        state,
        quantity_max,
        selected,
        torch.ones(len(bounds), dtype=torch.bool),
        validate=True,
    )
    torch.testing.assert_close(output.quantity, selected)
    assert torch.isfinite(output.factor_log_probability).all()
    assert torch.isfinite(output.factor_entropy).all()


def test_inactive_exact_quantity_is_canonical_without_factors() -> None:
    _contract, policy = _policy()
    batch = 3
    state = torch.randn(batch, policy.architecture.model_width)
    bounds = torch.zeros(batch, dtype=torch.long)
    active = torch.zeros(batch, dtype=torch.bool)
    sampled = policy.exact.rollout(
        state,
        bounds,
        active,
        sample=True,
        generator=torch.Generator().manual_seed(7),
        compute_entropy=True,
        validate=True,
    )
    replayed = policy.exact.evaluate(
        state,
        bounds,
        torch.zeros_like(bounds),
        active,
        validate=True,
    )
    for output in (sampled, replayed):
        torch.testing.assert_close(output.quantity, torch.ones_like(bounds))
        assert not bool(output.factors.any())
        assert not bool(output.factor_log_probability.any())
        assert not bool(output.factor_entropy.any())


def test_market_exact_rollout_replays_identical_conditional_probability() -> None:
    engine = native.Engine(seed=19)
    session = native.ConditionalProgramSession(None, 4)
    session.select(
        engine,
        0,
        int(ControlType.CANCEL_PASS),
        0,
        -1,
        0,
        0,
        0,
        0,
        1,
    )
    raw = native.conditional_program_observations_batch(
        [session], [engine], np.zeros(1, dtype=np.int64), 1
    )
    contract, policy = _policy()
    inputs, masks, context = _tensors(raw, contract)
    with torch.no_grad():
        policy.market_head.weight.zero_()
        policy.market_head.bias.fill_(-10.0)
        policy.market_head.bias[int(MarketOrderType.BUY_SEED)] = 10.0
        policy.market_item_head.weight.zero_()
        policy.market_item_head.bias.fill_(-10.0)
        policy.market_item_head.bias[0] = 10.0
        policy.quantity_mode_head.weight.zero_()
        policy.quantity_mode_head.bias.fill_(-10.0)
        policy.quantity_mode_head.bias[int(QuantityMode.EXACT)] = 10.0
    prefix = policy.initial_prefix(context)
    sampled = policy.rollout_step(
        inputs,
        masks,
        prefix,
        sample=False,
        compute_entropy=True,
    )
    assert int(sampled.actions.market_order[0]) == int(MarketOrderType.BUY_SEED)
    assert int(sampled.actions.quantity_mode[0]) == int(QuantityMode.EXACT)
    assert 1 <= int(sampled.actions.exact_quantity[0]) <= int(sampled.masks.quantity_max[0])
    replayed = policy.evaluate_step(inputs, sampled.actions, sampled.masks, prefix)
    torch.testing.assert_close(sampled.joint_log_probability, replayed.joint_log_probability)
    torch.testing.assert_close(sampled.factor_log_probability, replayed.factor_log_probability)
    torch.testing.assert_close(sampled.factor_entropy, replayed.factor_entropy)
    loss = -replayed.joint_log_probability.mean() + replayed.outcome_logits.square().mean()
    loss.backward()
    gradients = [parameter.grad for parameter in policy.parameters() if parameter.grad is not None]
    assert gradients
    assert all(torch.isfinite(gradient).all() for gradient in gradients)
    session.select(
        engine,
        0,
        0,
        int(sampled.actions.market_order[0]),
        -1,
        int(sampled.actions.argument[0]),
        0,
        0,
        int(sampled.actions.quantity_mode[0]),
        int(sampled.actions.exact_quantity[0]),
    )


def test_safe_plant_can_point_to_any_native_legal_tile() -> None:
    engine = native.Engine(seed=23)
    engine.step(
        {"farmer": ["PASS"], "market": [["BUY_SEED", "WHEAT", 2]]},
        {"farmer": ["PASS"]},
    )
    session = native.ConditionalProgramSession(None, 4)
    raw = native.conditional_program_observations_batch(
        [session], [engine], np.zeros(1, dtype=np.int64), 1
    )
    contract, policy = _policy()
    inputs, masks, context = _tensors(raw, contract)
    target_mask = np.asarray(raw["task_target_mask"])[0, int(TaskType.SAFE_PLANT), 0]
    legal = np.flatnonzero(target_mask)
    farmer_x, farmer_y = engine.observation(0)["farms"][0]["farmer"]
    target = int(
        max(
            legal,
            key=lambda tile: (
                abs(int(tile) % contract.board_size - farmer_x)
                + abs(int(tile) // contract.board_size - farmer_y)
            ),
        )
    )
    with torch.no_grad():
        policy.control_head.weight.zero_()
        policy.control_head.bias.fill_(-10.0)
        policy.control_head.bias[int(ControlType.ASSIGN)] = 10.0
        policy.task_head.weight.zero_()
        policy.task_head.bias.fill_(-10.0)
        policy.task_head.bias[int(TaskType.SAFE_PLANT)] = 10.0
        policy.argument_head.weight.zero_()
        policy.argument_head.bias.fill_(-10.0)
        policy.argument_head.bias[0] = 10.0
        policy.target_bias.fill_(-10.0)
        policy.target_bias[target] = 10.0
    prefix = policy.initial_prefix(context)
    sampled = policy.rollout_step(inputs, masks, prefix, sample=False)
    assert int(sampled.actions.task[0]) == int(TaskType.SAFE_PLANT)
    assert int(sampled.actions.target[0]) == target
    assert not torch.equal(prefix.hidden, sampled.next_prefix.hidden)
    prepared = policy.prepare_rollout(context, inputs.tile_tokens)
    cached = policy.rollout_step(
        inputs,
        masks,
        prefix,
        sample=False,
        prepared=prepared,
    )
    torch.testing.assert_close(cached.actions.target, sampled.actions.target)
    torch.testing.assert_close(
        cached.joint_log_probability,
        sampled.joint_log_probability,
    )
    torch.testing.assert_close(
        cached.next_prefix.hidden,
        sampled.next_prefix.hidden,
    )
    replayed = policy.evaluate_step(inputs, sampled.actions, sampled.masks, prefix)
    torch.testing.assert_close(sampled.joint_log_probability, replayed.joint_log_probability)
    session.select(
        engine,
        0,
        int(sampled.actions.control[0]),
        int(sampled.actions.task[0]),
        int(sampled.actions.target[0]),
        int(sampled.actions.argument[0]),
        int(sampled.actions.direction[0]),
        int(sampled.actions.raw_operation[0]),
        int(sampled.actions.quantity_mode[0]),
        int(sampled.actions.exact_quantity[0]),
    )


def test_sequence_replay_uses_one_joint_turn_probability() -> None:
    engine = native.Engine(seed=29)
    session = native.ConditionalProgramSession(None, 4)
    contract, policy = _policy()
    with torch.no_grad():
        policy.control_head.weight.zero_()
        policy.control_head.bias.fill_(-10.0)
        policy.control_head.bias[int(ControlType.CANCEL_PASS)] = 10.0
        policy.market_head.weight.zero_()
        policy.market_head.bias.fill_(-10.0)
        policy.market_head.bias[int(MarketOrderType.BUY_SEED)] = 10.0
        policy.market_item_head.weight.zero_()
        policy.market_item_head.bias.fill_(-10.0)
        policy.market_item_head.bias[0] = 10.0
        policy.quantity_mode_head.weight.zero_()
        policy.quantity_mode_head.bias.fill_(-10.0)
        policy.quantity_mode_head.bias[int(QuantityMode.EXACT)] = 10.0
    raw_unit = native.conditional_program_observations_batch(
        [session], [engine], np.zeros(1, dtype=np.int64), 1
    )
    unit_inputs, unit_masks, context = _tensors(raw_unit, contract)
    prefix = policy.initial_prefix(context)
    unit_output = policy.rollout_step(
        unit_inputs,
        unit_masks,
        prefix,
        sample=False,
        compute_entropy=True,
    )
    session.select(
        engine,
        0,
        int(unit_output.actions.control[0]),
        int(unit_output.actions.task[0]),
        int(unit_output.actions.target[0]),
        int(unit_output.actions.argument[0]),
        int(unit_output.actions.direction[0]),
        int(unit_output.actions.raw_operation[0]),
        int(unit_output.actions.quantity_mode[0]),
        int(unit_output.actions.exact_quantity[0]),
    )
    raw_market = native.conditional_program_observations_batch(
        [session], [engine], np.zeros(1, dtype=np.int64), 1
    )
    market_inputs, market_masks = decision_inputs(
        raw_market,
        unit_inputs.context,
        unit_inputs.tile_tokens,
        contract,
        device="cpu",
        validate=True,
    )
    market_output = policy.rollout_step(
        market_inputs,
        market_masks,
        unit_output.next_prefix,
        sample=False,
        compute_entropy=True,
    )
    assert int(market_output.actions.quantity_mode[0]) == int(QuantityMode.EXACT)
    dynamic_names = (
        "root_features",
        "option_features",
        "target_reservations",
        "phase",
        "unit_index",
        "market_slot",
        "unit_count",
        "current_x",
        "current_y",
        "forced",
    )
    sequence_inputs = ProgramSequenceInputs(
        context=unit_inputs.context,
        tile_tokens=unit_inputs.tile_tokens,
        decision_mask=torch.ones((1, 2), dtype=torch.bool),
        **{
            name: torch.stack((getattr(unit_inputs, name), getattr(market_inputs, name)), dim=1)
            for name in dynamic_names
        },
    )
    sequence_actions = ProgramActionSequence(
        **{
            name: torch.stack(
                (
                    getattr(unit_output.actions, name),
                    getattr(market_output.actions, name),
                ),
                dim=1,
            )
            for name in unit_output.actions.__dataclass_fields__
        }
    )
    sequence_masks = ProgramMaskSequence(
        **{
            name: torch.stack(
                (
                    getattr(unit_output.masks, name),
                    getattr(market_output.masks, name),
                ),
                dim=1,
            )
            for name in unit_output.masks.__dataclass_fields__
        }
    )
    replayed = policy.evaluate_sequence(sequence_inputs, sequence_actions, sequence_masks)
    expected_log = unit_output.joint_log_probability + market_output.joint_log_probability
    torch.testing.assert_close(replayed.joint_log_probability, expected_log)
    factor_count = unit_output.factor_counts + market_output.factor_counts
    expected_entropy = (unit_output.entropy + market_output.entropy) / factor_count.clamp_min(1)
    torch.testing.assert_close(replayed.normalized_entropy, expected_entropy)
