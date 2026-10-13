"""Teacher-forced reconstruction of complete turn-level program ratios."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import torch
from torch import Tensor
from torch.nn import functional as F

from kagg_revue.policy.programs.contract import ControlType, QuantityMode
from kagg_revue.policy.programs.distributions import evaluate_masked
from kagg_revue.policy.programs.encoding import scaled_counts
from kagg_revue.policy.programs.grammar import (
    ProgramActionSequence,
    ProgramMaskSequence,
    ProgramSequenceInputs,
)
from kagg_revue.policy.programs.schema import ProgramSequenceOutput

if TYPE_CHECKING:
    from kagg_revue.policy.programs.model import ConditionalProgramPolicy


def _evaluate_factor(
    logits: Tensor,
    mask: Tensor,
    selected: Tensor,
    active: Tensor,
    *,
    validate: bool,
) -> tuple[Tensor, Tensor, Tensor]:
    """Evaluate one factor over a dense turn-by-decision surface."""
    batch, decisions = selected.shape
    logs, entropies, factors = evaluate_masked(
        logits.flatten(0, 1),
        mask.flatten(0, 1),
        selected.flatten(),
        active.flatten(),
        validate=validate,
    )
    shape = (batch, decisions)
    return logs.view(shape), entropies.view(shape), factors.view(shape)


def evaluate_program_sequence(
    policy: ConditionalProgramPolicy,
    inputs: ProgramSequenceInputs,
    actions: ProgramActionSequence,
    masks: ProgramMaskSequence,
    *,
    validate: bool,
) -> ProgramSequenceOutput:
    """Reconstruct all teacher-forced decisions as one dense GPU workload."""
    batch = inputs.batch_size
    decisions = inputs.decision_capacity
    if validate:
        inputs.validate(policy.contract, policy.architecture.context_width)
        actions.validate(batch, decisions)
        masks.validate(batch, decisions, policy.contract)

    prefix = policy.initial_prefix(inputs.context)
    prepared = policy.prepare_rollout(inputs.context, inputs.tile_tokens)
    prefix_hidden = policy.encoder.sequence_prefixes(prefix, actions, inputs.phase)
    state = policy.encoder.sequence_states(inputs, prefix_hidden, prepared.context)

    head_weights = torch.cat(
        (
            policy.control_head.weight,
            policy.task_head.weight,
            policy.direction_head.weight,
            policy.raw_head.weight,
            policy.market_head.weight,
        )
    )
    head_biases = torch.cat(
        (
            policy.control_head.bias,
            policy.task_head.bias,
            policy.direction_head.bias,
            policy.raw_head.bias,
            policy.market_head.bias,
        )
    )
    base_logits = F.linear(state, head_weights, head_biases)
    (
        control_logits,
        task_logits,
        direction_logits,
        raw_logits,
        market_logits,
    ) = torch.split(base_logits, list(policy._rollout_base_splits), dim=-1)

    unit = inputs.phase == 0
    market_phase = inputs.phase == 1
    control = actions.control
    task = actions.task
    direction = actions.direction
    raw = actions.raw_operation
    market = actions.market_order
    argument = actions.argument
    quantity_mode = actions.quantity_mode
    assign = unit & (control == int(ControlType.ASSIGN))
    step = unit & (control == int(ControlType.STEP))
    raw_branch = unit & (control == int(ControlType.RAW_LOCAL))
    safe_task = task.clamp(0, policy.architecture.task_count - 1)
    safe_raw = raw.clamp(0, policy.architecture.raw_operation_count - 1)
    safe_market = market.clamp(0, policy.architecture.market_order_count - 1)
    safe_argument = argument.clamp(0, policy.architecture.argument_count - 1)
    task_argument_branch = assign & policy._task_argument_required[safe_task]
    task_target_branch = assign & policy._task_target_required[safe_task]
    task_quantity_branch = assign & policy._task_quantity_required[safe_task]
    raw_argument_branch = raw_branch & policy._raw_argument_required[safe_raw]
    raw_quantity_branch = raw_branch & policy._raw_quantity_required[safe_raw]
    market_item_branch = market_phase & policy._market_item_required[safe_market]

    control_result = _evaluate_factor(
        control_logits, masks.control, control, unit, validate=validate
    )
    task_result = _evaluate_factor(
        task_logits, masks.task, task, assign, validate=validate
    )
    direction_result = _evaluate_factor(
        direction_logits, masks.direction, direction, step, validate=validate
    )
    raw_result = _evaluate_factor(
        raw_logits, masks.raw_operation, raw, raw_branch, validate=validate
    )
    market_result = _evaluate_factor(
        market_logits, masks.market_order, market, market_phase, validate=validate
    )
    task_argument_result = _evaluate_factor(
        policy.argument_head(state + policy.task(safe_task)),
        masks.argument,
        argument,
        task_argument_branch,
        validate=validate,
    )
    raw_argument_result = _evaluate_factor(
        policy.argument_head(state + policy.raw(safe_raw)),
        masks.argument,
        argument,
        raw_argument_branch,
        validate=validate,
    )
    market_item_result = _evaluate_factor(
        policy.market_item_head(state + policy.market(safe_market)),
        masks.market_item,
        argument,
        market_item_branch,
        validate=validate,
    )

    target_state = state + policy.task(safe_task) + policy.argument(safe_argument)
    target_query = policy.target_query(target_state)
    target_logits = torch.bmm(
        target_query,
        prepared.target_keys.transpose(1, 2),
    )
    reservation_key = F.linear(
        policy.encoder.reservation.weight.T,
        policy.target_key.weight,
    )
    reservation_coefficient = (target_query * reservation_key).sum(
        dim=-1, keepdim=True
    )
    reservation_scale = scaled_counts(inputs.target_reservations).to(
        reservation_coefficient.dtype
    )
    target_logits = (
        target_logits + reservation_scale * reservation_coefficient
    ) / math.sqrt(policy.architecture.model_width) + policy.target_bias
    target_result = _evaluate_factor(
        target_logits,
        masks.target,
        actions.target,
        task_target_branch,
        validate=validate,
    )

    quantity_branch = task_quantity_branch | raw_quantity_branch | market_item_branch
    quantity_state = (
        state
        + policy.task(safe_task) * task_quantity_branch[..., None]
        + policy.raw(safe_raw) * raw_quantity_branch[..., None]
        + policy.market(safe_market) * market_item_branch[..., None]
        + policy.argument(safe_argument) * quantity_branch[..., None]
    )
    quantity_result = _evaluate_factor(
        policy.quantity_mode_head(quantity_state),
        masks.quantity_mode,
        quantity_mode,
        quantity_branch,
        validate=validate,
    )
    exact_branch = quantity_branch & (quantity_mode == int(QuantityMode.EXACT))
    exact_state = quantity_state + policy.quantity_mode(
        quantity_mode.clamp(0, policy.architecture.quantity_mode_count - 1)
    )
    exact = policy.exact.evaluate(
        exact_state.flatten(0, 1),
        masks.quantity_max.flatten(),
        actions.exact_quantity.flatten(),
        exact_branch.flatten(),
        validate=validate,
    )
    exact_shape = (batch, decisions, policy.architecture.exact_quantity_bits)

    argument_result = tuple(
        task_value + raw_value + market_value
        for task_value, raw_value, market_value in zip(
            task_argument_result,
            raw_argument_result,
            market_item_result,
            strict=True,
        )
    )
    base_results = (
        control_result,
        task_result,
        direction_result,
        raw_result,
        argument_result,
        target_result,
        quantity_result,
        market_result,
    )
    base_logs = torch.stack(tuple(result[0] for result in base_results), dim=-1)
    base_entropies = torch.stack(tuple(result[1] for result in base_results), dim=-1)
    base_factors = torch.stack(tuple(result[2] for result in base_results), dim=-1)
    logs = torch.cat(
        (base_logs, exact.factor_log_probability.view(exact_shape)), dim=-1
    )
    entropies = torch.cat(
        (base_entropies, exact.factor_entropy.view(exact_shape)), dim=-1
    )
    factors = torch.cat((base_factors, exact.factors.view(exact_shape)), dim=-1)
    active = inputs.decision_mask.bool()[..., None]
    logs = logs * active
    entropies = entropies * active
    factors = factors & active
    counts = factors.sum(dim=(1, 2))
    outcome_logits = policy.outcome(prepared.context)
    outcome_probabilities = torch.softmax(outcome_logits.float(), dim=-1)
    value = outcome_probabilities[..., 2] - outcome_probabilities[..., 0]
    return ProgramSequenceOutput(
        joint_log_probability=logs.sum(dim=(1, 2)),
        normalized_entropy=entropies.sum(dim=(1, 2)) / counts.clamp_min(1),
        factor_log_probability=logs,
        factor_entropy=entropies,
        factors=factors,
        outcome_logits=outcome_logits,
        value=value,
    )


__all__ = ["evaluate_program_sequence"]
