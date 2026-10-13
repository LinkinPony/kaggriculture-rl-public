"""Autoregressive pointer policy for native conditional turn programs."""

from __future__ import annotations

import math
from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.cuda.categorical import sample_masked_factor
from kagg_revue.policy.programs.contract import (
    NONE_ARGUMENT,
    ControlType,
    QuantityMode,
)
from kagg_revue.policy.programs.distributions import (
    choose_masked,
    evaluate_masked,
)
from kagg_revue.policy.programs.encoding import (
    ProgramPreparedContext,
    ProgramStateEncoder,
)
from kagg_revue.policy.programs.grammar import (
    NativeProgramMasks,
    ProgramActions,
    ProgramActionSequence,
    ProgramConditionalMasks,
    ProgramDecisionInputs,
    ProgramMaskSequence,
    ProgramPrefixState,
    ProgramSequenceInputs,
)
from kagg_revue.policy.programs.language import (
    MARKET_ITEM_REQUIRED,
    RAW_ARGUMENT_REQUIRED,
    RAW_QUANTITY_REQUIRED,
    TASK_ARGUMENT_REQUIRED,
    TASK_QUANTITY_REQUIRED,
    TASK_TARGET_REQUIRED,
)
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.quantity import ExactQuantityDecoder
from kagg_revue.policy.programs.schema import (
    ProgramArchitecture,
    ProgramSequenceOutput,
    ProgramStepOutput,
)
from kagg_revue.policy.programs.sequence import evaluate_program_sequence


def _outcome_values(logits: Tensor) -> Tensor:
    probabilities = torch.softmax(logits.float(), dim=-1)
    return probabilities[:, 2] - probabilities[:, 0]


def _one_hot(batch: int, width: int, index: int, device: torch.device) -> Tensor:
    result = torch.zeros((batch, width), dtype=torch.bool, device=device)
    result[:, index] = True
    return result


class ConditionalProgramPolicy(nn.Module):
    """Shared unit/market actor with a recurrent turn-level action prefix."""

    _rollout_base_bias: Tensor
    _rollout_base_splits: tuple[int, int, int, int, int]
    _rollout_base_weight: Tensor
    _market_item_required: Tensor
    _raw_argument_required: Tensor
    _raw_quantity_required: Tensor
    _task_argument_required: Tensor
    _task_quantity_required: Tensor
    _task_target_required: Tensor

    def __init__(
        self,
        architecture: ProgramArchitecture,
        contract: NativeProgramContract,
    ) -> None:
        """Create conditional heads around one authenticated compiler ABI."""
        super().__init__()
        if architecture.native_abi_version != contract.version:
            raise ValueError("conditional-program model and native ABI differ")
        measured = contract.architecture(
            context_width=architecture.context_width,
            model_width=architecture.model_width,
            feedforward_width=architecture.feedforward_width,
        )
        if measured != architecture:
            raise ValueError("conditional-program architecture differs from native shapes")
        self.architecture = architecture
        self.contract = contract
        width = architecture.model_width
        self.encoder = ProgramStateEncoder(architecture)
        self.control_head = nn.Linear(width, architecture.control_count)
        self.task_head = nn.Linear(width, architecture.task_count)
        self.direction_head = nn.Linear(width, architecture.direction_count)
        self.raw_head = nn.Linear(width, architecture.raw_operation_count)
        self.argument_head = nn.Linear(width, architecture.argument_count)
        self.market_head = nn.Linear(width, architecture.market_order_count)
        self.market_item_head = nn.Linear(width, architecture.item_count)
        self.quantity_mode_head = nn.Linear(width, architecture.quantity_mode_count)
        self._rollout_base_splits = (
            architecture.control_count,
            architecture.task_count,
            architecture.direction_count,
            architecture.raw_operation_count,
            architecture.market_order_count,
        )
        packed_width = sum(self._rollout_base_splits)
        self.register_buffer(
            "_rollout_base_weight",
            torch.empty(
                (packed_width, width),
                dtype=self.control_head.weight.dtype,
            ),
            persistent=False,
        )
        self.register_buffer(
            "_rollout_base_bias",
            torch.empty(packed_width, dtype=self.control_head.bias.dtype),
            persistent=False,
        )
        self.task = nn.Embedding(architecture.task_count, width)
        self.argument = nn.Embedding(architecture.argument_count, width)
        self.raw = nn.Embedding(architecture.raw_operation_count, width)
        self.market = nn.Embedding(architecture.market_order_count, width)
        self.quantity_mode = nn.Embedding(architecture.quantity_mode_count, width)
        self.target_key = nn.Linear(width, width, bias=False)
        self.target_query = nn.Linear(width, width, bias=False)
        self.target_bias = nn.Parameter(torch.zeros(architecture.tile_count))
        self.exact = ExactQuantityDecoder(architecture)
        self.outcome = nn.Sequential(
            nn.LayerNorm(width),
            nn.Linear(width, architecture.feedforward_width),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, 3),
        )
        self.register_buffer(
            "_task_argument_required",
            torch.tensor(TASK_ARGUMENT_REQUIRED, dtype=torch.bool),
            persistent=False,
        )
        self.register_buffer(
            "_task_target_required",
            torch.tensor(TASK_TARGET_REQUIRED, dtype=torch.bool),
            persistent=False,
        )
        self.register_buffer(
            "_task_quantity_required",
            torch.tensor(TASK_QUANTITY_REQUIRED, dtype=torch.bool),
            persistent=False,
        )
        self.register_buffer(
            "_raw_argument_required",
            torch.tensor(RAW_ARGUMENT_REQUIRED, dtype=torch.bool),
            persistent=False,
        )
        self.register_buffer(
            "_raw_quantity_required",
            torch.tensor(RAW_QUANTITY_REQUIRED, dtype=torch.bool),
            persistent=False,
        )
        self.register_buffer(
            "_market_item_required",
            torch.tensor(MARKET_ITEM_REQUIRED, dtype=torch.bool),
            persistent=False,
        )
        self.refresh_rollout_parameters()

    @torch.no_grad()
    def refresh_rollout_parameters(self) -> None:
        """Refresh the read-only packed heads used by captured rollout graphs."""
        heads = (
            self.control_head,
            self.task_head,
            self.direction_head,
            self.raw_head,
            self.market_head,
        )
        self._rollout_base_weight.copy_(torch.cat(tuple(head.weight for head in heads), dim=0))
        self._rollout_base_bias.copy_(torch.cat(tuple(head.bias for head in heads), dim=0))

    def initial_prefix(self, context: Tensor) -> ProgramPrefixState:
        """Start one policy-owned action prefix for a new environment turn."""
        return self.encoder.initial_prefix(context)

    def prepare_rollout(self, context: Tensor, tile_tokens: Tensor) -> ProgramPreparedContext:
        """Encode features that remain constant throughout one turn."""
        batch = context.shape[0]
        if context.shape != (batch, self.architecture.context_width) or (
            tile_tokens.shape
            != (
                batch,
                self.architecture.tile_count,
                self.architecture.context_width,
            )
        ):
            raise ValueError("conditional-program turn-static inputs have the wrong shape")
        encoded_context = self.encoder.encode_context(context)
        target_keys = self.target_key(self.encoder.encode_tiles(tile_tokens))
        return ProgramPreparedContext(encoded_context, target_keys)

    def rollout_step(
        self,
        inputs: ProgramDecisionInputs,
        masks: NativeProgramMasks,
        prefix: ProgramPrefixState,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
        compute_entropy: bool = False,
        compute_outcome: bool = True,
        validate_inputs: bool = True,
        static_execution: bool = False,
        prepared: ProgramPreparedContext | None = None,
    ) -> ProgramStepOutput:
        """Sample one complete active branch under native exact legality."""
        return self._decode(
            inputs,
            prefix,
            native_masks=masks,
            actions=None,
            replay_masks=None,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            compute_outcome=compute_outcome,
            validate=validate_inputs,
            static_execution=static_execution,
            prepared=prepared,
        )

    def evaluate_step(
        self,
        inputs: ProgramDecisionInputs,
        actions: ProgramActions,
        masks: ProgramConditionalMasks,
        prefix: ProgramPrefixState,
        *,
        validate: bool = True,
        validate_inputs: bool = True,
        compute_outcome: bool = True,
        prepared: ProgramPreparedContext | None = None,
        compute_prefix: bool = True,
    ) -> ProgramStepOutput:
        """Teacher-force one choice under its exact stored conditional masks."""
        return self._decode(
            inputs,
            prefix,
            native_masks=None,
            actions=actions,
            replay_masks=masks,
            sample=False,
            generator=None,
            compute_entropy=True,
            compute_outcome=compute_outcome,
            validate=validate and validate_inputs,
            static_execution=False,
            prepared=prepared,
            compute_prefix=compute_prefix,
        )

    def evaluate_sequence(
        self,
        inputs: ProgramSequenceInputs,
        actions: ProgramActionSequence,
        masks: ProgramMaskSequence,
        *,
        validate: bool = True,
    ) -> ProgramSequenceOutput:
        """Reconstruct one combined policy ratio per complete turn program."""
        return evaluate_program_sequence(self, inputs, actions, masks, validate=validate)

    def _decode(
        self,
        inputs: ProgramDecisionInputs,
        prefix: ProgramPrefixState,
        *,
        native_masks: NativeProgramMasks | None,
        actions: ProgramActions | None,
        replay_masks: ProgramConditionalMasks | None,
        sample: bool,
        generator: torch.Generator | None,
        compute_entropy: bool,
        compute_outcome: bool,
        validate: bool,
        static_execution: bool,
        prepared: ProgramPreparedContext | None,
        compute_prefix: bool = True,
    ) -> ProgramStepOutput:
        rollout = actions is None
        if (rollout and (native_masks is None or replay_masks is not None)) or (
            not rollout and (native_masks is not None or replay_masks is None)
        ):
            raise ValueError("conditional-program decode boundary is ambiguous")
        batch = inputs.batch_size
        if validate:
            inputs.validate(self.contract, self.architecture.context_width)
            if native_masks is not None:
                native_masks.validate(batch, self.contract)
            if actions is not None and replay_masks is not None:
                actions.validate(batch)
                replay_masks.validate(batch, self.contract)
        if prepared is None:
            context_token = self.encoder.encode_context(inputs.context)
            target_keys = self.target_key(
                self.encoder.encode_tiles(inputs.tile_tokens)
                + self.encoder.encode_reservations(inputs.target_reservations)
            )
        else:
            context_token = prepared.context
            if context_token.shape != (
                batch,
                self.architecture.model_width,
            ) or prepared.target_keys.shape != (
                batch,
                self.architecture.tile_count,
                self.architecture.model_width,
            ):
                raise ValueError("conditional-program prepared rollout has the wrong shape")
            target_keys = prepared.target_keys + self.target_key(
                self.encoder.encode_reservations(inputs.target_reservations)
            )
        state = self.encoder.decision_state(inputs, prefix, context_token)
        device = state.device
        rows = torch.arange(batch, device=device)
        unit = inputs.phase == 0
        market_phase = inputs.phase == 1
        if rollout and static_execution and device.type == "cuda":
            base_logits = F.linear(
                state,
                self._rollout_base_weight,
                self._rollout_base_bias,
            )
            (
                control_logits,
                task_logits,
                direction_logits,
                raw_logits,
                market_logits,
            ) = torch.split(
                base_logits,
                list(self._rollout_base_splits),
                dim=1,
            )
        else:
            control_logits = self.control_head(state)
            task_logits = self.task_head(state)
            direction_logits = self.direction_head(state)
            raw_logits = self.raw_head(state)
            market_logits = self.market_head(state)
        fused_uniforms = (
            torch.rand(
                (10 + self.architecture.exact_quantity_bits, batch),
                dtype=torch.float32,
                device=device,
                generator=generator,
            )
            if (
                rollout
                and sample
                and static_execution
                and not compute_entropy
                and generator is not None
                and device.type == "cuda"
            )
            else None
        )
        fused_uniform_index = 0

        def categorical(
            logits: Tensor,
            mask: Tensor,
            active: Tensor,
            selected: Tensor | None,
        ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
            nonlocal fused_uniform_index
            if selected is None:
                if fused_uniforms is not None:
                    chosen, log_probability, factors = sample_masked_factor(
                        logits,
                        mask,
                        active,
                        fused_uniforms[fused_uniform_index],
                    )
                    fused_uniform_index += 1
                    return (
                        chosen,
                        log_probability,
                        torch.zeros_like(log_probability),
                        factors,
                    )
                return choose_masked(
                    logits,
                    mask,
                    active,
                    sample=sample,
                    generator=generator,
                    compute_entropy=compute_entropy,
                )
            log_probability, entropy, factors = evaluate_masked(
                logits, mask, selected, active, validate=validate
            )
            return selected, log_probability, entropy, factors

        control_fallback = _one_hot(batch, self.architecture.control_count, 0, device)
        control_mask = (
            torch.where(unit[:, None], native_masks.control, control_fallback)
            if native_masks is not None
            else cast(ProgramConditionalMasks, replay_masks).control
        )
        control, control_log, control_entropy, control_factor = categorical(
            control_logits,
            control_mask,
            unit,
            None if actions is None else actions.control,
        )
        assign = unit & (control == int(ControlType.ASSIGN))
        step = unit & (control == int(ControlType.STEP))
        raw_branch = unit & (control == int(ControlType.RAW_LOCAL))

        market_fallback = _one_hot(batch, self.architecture.market_order_count, 0, device)
        market_mask = (
            torch.where(market_phase[:, None], native_masks.market_order, market_fallback)
            if native_masks is not None
            else cast(ProgramConditionalMasks, replay_masks).market_order
        )
        market_order, market_log, market_entropy, market_factor = categorical(
            market_logits,
            market_mask,
            market_phase,
            None if actions is None else actions.market_order,
        )

        task_fallback = _one_hot(batch, self.architecture.task_count, 0, device)
        task_mask = (
            torch.where(assign[:, None], native_masks.task, task_fallback)
            if native_masks is not None
            else cast(ProgramConditionalMasks, replay_masks).task
        )
        task, task_log, task_entropy, task_factor = categorical(
            task_logits,
            task_mask,
            assign,
            None if actions is None else actions.task,
        )
        safe_task = task.clamp(0, self.architecture.task_count - 1)
        task_argument_branch = assign & self._task_argument_required[safe_task]
        task_target_branch = assign & self._task_target_required[safe_task]
        task_quantity_branch = assign & self._task_quantity_required[safe_task]

        direction_fallback = _one_hot(batch, self.architecture.direction_count, 0, device)
        direction_mask = (
            torch.where(step[:, None], native_masks.direction, direction_fallback)
            if native_masks is not None
            else cast(ProgramConditionalMasks, replay_masks).direction
        )
        direction, direction_log, direction_entropy, direction_factor = categorical(
            direction_logits,
            direction_mask,
            step,
            None if actions is None else actions.direction,
        )

        raw_fallback = _one_hot(batch, self.architecture.raw_operation_count, 0, device)
        raw_mask = (
            torch.where(raw_branch[:, None], native_masks.raw_operation, raw_fallback)
            if native_masks is not None
            else cast(ProgramConditionalMasks, replay_masks).raw_operation
        )
        raw_operation, raw_log, raw_entropy, raw_factor = categorical(
            raw_logits,
            raw_mask,
            raw_branch,
            None if actions is None else actions.raw_operation,
        )
        safe_raw = raw_operation.clamp(0, self.architecture.raw_operation_count - 1)
        raw_argument_branch = raw_branch & self._raw_argument_required[safe_raw]
        raw_quantity_branch = raw_branch & self._raw_quantity_required[safe_raw]

        none_argument = _one_hot(batch, self.architecture.argument_count, NONE_ARGUMENT, device)
        if native_masks is not None:
            selected_task_argument = native_masks.task_argument[rows, safe_task]
            task_argument_mask = torch.where(
                task_argument_branch[:, None], selected_task_argument, none_argument
            )
        else:
            task_argument_mask = cast(ProgramConditionalMasks, replay_masks).argument
        task_argument, task_argument_log, task_argument_entropy, task_argument_factor = categorical(
            self.argument_head(state + self.task(safe_task)),
            task_argument_mask,
            task_argument_branch,
            None if actions is None else actions.argument,
        )

        if native_masks is not None:
            selected_raw_argument = native_masks.raw_argument[rows, safe_raw]
            raw_argument_mask = torch.where(
                raw_argument_branch[:, None], selected_raw_argument, none_argument
            )
        else:
            raw_argument_mask = cast(ProgramConditionalMasks, replay_masks).argument
        raw_argument, raw_argument_log, raw_argument_entropy, raw_argument_factor = categorical(
            self.argument_head(state + self.raw(safe_raw)),
            raw_argument_mask,
            raw_argument_branch,
            None if actions is None else actions.argument,
        )

        safe_market = market_order.clamp(0, self.architecture.market_order_count - 1)
        market_item_branch = market_phase & self._market_item_required[safe_market]
        market_item_fallback = _one_hot(batch, self.architecture.item_count, 0, device)
        if native_masks is not None:
            selected_market_item = native_masks.market_item[rows, safe_market]
            market_item_mask = torch.where(
                market_item_branch[:, None],
                selected_market_item,
                market_item_fallback,
            )
        else:
            market_item_mask = cast(ProgramConditionalMasks, replay_masks).market_item
        market_item, item_log, item_entropy, item_factor = categorical(
            self.market_item_head(state + self.market(safe_market)),
            market_item_mask,
            market_item_branch,
            None if actions is None else actions.argument,
        )

        argument = torch.where(
            market_phase,
            torch.zeros(batch, dtype=torch.long, device=device),
            torch.full((batch,), NONE_ARGUMENT, dtype=torch.long, device=device),
        )
        argument = torch.where(task_argument_branch, task_argument, argument)
        argument = torch.where(raw_argument_branch, raw_argument, argument)
        argument = torch.where(market_item_branch, market_item, argument)
        if actions is not None:
            argument = actions.argument
        safe_argument = argument.clamp(0, self.architecture.argument_count - 1)

        target_fallback = _one_hot(batch, self.architecture.tile_count, 0, device)
        if native_masks is not None:
            task_target_mask = native_masks.task_target[rows, safe_task, safe_argument]
            target_mask = torch.where(
                task_target_branch[:, None], task_target_mask, target_fallback
            )
        else:
            target_mask = cast(ProgramConditionalMasks, replay_masks).target
        target_state = state + self.task(safe_task) + self.argument(safe_argument)
        target_logits = (
            torch.bmm(
                target_keys,
                self.target_query(target_state)[:, :, None],
            ).squeeze(-1)
            / math.sqrt(self.architecture.model_width)
            + self.target_bias
        )
        target, target_log, target_entropy, target_factor = categorical(
            target_logits,
            target_mask,
            task_target_branch,
            None if actions is None else actions.target,
        )
        target = torch.where(task_target_branch, target, torch.full_like(target, -1))
        if actions is not None:
            target = actions.target

        if native_masks is not None:
            task_quantity_mask = native_masks.task_quantity_mode[rows, safe_task, safe_argument]
            task_quantity_max = native_masks.task_quantity_max[rows, safe_task, safe_argument]
            raw_quantity_mask = native_masks.raw_quantity_mode[rows, safe_raw, safe_argument]
            raw_quantity_max = native_masks.raw_quantity_max[rows, safe_raw, safe_argument]
            market_quantity_mask = native_masks.market_quantity_mode[
                rows, safe_market, safe_argument.clamp_max(self.architecture.item_count - 1)
            ]
            market_quantity_max = native_masks.market_quantity_max[
                rows,
                safe_market,
                safe_argument.clamp_max(self.architecture.item_count - 1),
            ]
            quantity_fallback = _one_hot(batch, self.architecture.quantity_mode_count, 0, device)
            quantity_mask = quantity_fallback
            quantity_mask = torch.where(
                task_quantity_branch[:, None], task_quantity_mask, quantity_mask
            )
            quantity_mask = torch.where(
                raw_quantity_branch[:, None], raw_quantity_mask, quantity_mask
            )
            quantity_mask = torch.where(
                market_item_branch[:, None], market_quantity_mask, quantity_mask
            )
            quantity_max = torch.zeros(batch, dtype=torch.long, device=device)
            quantity_max = torch.where(task_quantity_branch, task_quantity_max, quantity_max)
            quantity_max = torch.where(raw_quantity_branch, raw_quantity_max, quantity_max)
            quantity_max = torch.where(market_item_branch, market_quantity_max, quantity_max)
        else:
            compact = cast(ProgramConditionalMasks, replay_masks)
            quantity_mask = compact.quantity_mode
            quantity_max = compact.quantity_max
        quantity_branch = task_quantity_branch | raw_quantity_branch | market_item_branch
        quantity_state = (
            state
            + self.task(safe_task) * task_quantity_branch[:, None]
            + self.raw(safe_raw) * raw_quantity_branch[:, None]
            + self.market(safe_market) * market_item_branch[:, None]
            + self.argument(safe_argument) * quantity_branch[:, None]
        )
        quantity_mode, quantity_log, quantity_entropy, quantity_factor = categorical(
            self.quantity_mode_head(quantity_state),
            quantity_mask,
            quantity_branch,
            None if actions is None else actions.quantity_mode,
        )
        exact_branch = quantity_branch & (quantity_mode == int(QuantityMode.EXACT))
        exact_state = quantity_state + self.quantity_mode(
            quantity_mode.clamp(0, self.architecture.quantity_mode_count - 1)
        )
        exact = (
            self.exact.rollout(
                exact_state,
                quantity_max,
                exact_branch,
                sample=sample,
                generator=generator,
                compute_entropy=compute_entropy,
                validate=validate,
                static_execution=static_execution,
                uniforms=(
                    fused_uniforms[fused_uniform_index:] if fused_uniforms is not None else None
                ),
            )
            if actions is None
            else self.exact.evaluate(
                exact_state,
                quantity_max,
                actions.exact_quantity,
                exact_branch,
                validate=validate,
            )
        )
        exact_quantity = exact.quantity if actions is None else actions.exact_quantity

        if actions is None:
            actions = ProgramActions(
                control=control,
                task=task,
                target=target,
                argument=argument,
                direction=direction,
                raw_operation=raw_operation,
                quantity_mode=quantity_mode,
                exact_quantity=exact_quantity,
                market_order=market_order,
            )
            replay_masks = ProgramConditionalMasks(
                control=control_mask,
                direction=direction_mask,
                task=task_mask,
                argument=torch.where(
                    task_argument_branch[:, None],
                    task_argument_mask,
                    torch.where(raw_argument_branch[:, None], raw_argument_mask, none_argument),
                ),
                target=target_mask,
                raw_operation=raw_mask,
                quantity_mode=quantity_mask,
                market_order=market_mask,
                market_item=market_item_mask,
                quantity_max=quantity_max,
            )

        base_log = torch.stack(
            (
                control_log,
                task_log,
                direction_log,
                raw_log,
                task_argument_log + raw_argument_log + item_log,
                target_log,
                quantity_log,
                market_log,
            ),
            dim=1,
        )
        base_entropy = torch.stack(
            (
                control_entropy,
                task_entropy,
                direction_entropy,
                raw_entropy,
                task_argument_entropy + raw_argument_entropy + item_entropy,
                target_entropy,
                quantity_entropy,
                market_entropy,
            ),
            dim=1,
        )
        base_factors = torch.stack(
            (
                control_factor,
                task_factor,
                direction_factor,
                raw_factor,
                task_argument_factor | raw_argument_factor | item_factor,
                target_factor,
                quantity_factor,
                market_factor,
            ),
            dim=1,
        )
        factor_log = torch.cat((base_log, exact.factor_log_probability), dim=1)
        factor_entropy = torch.cat((base_entropy, exact.factor_entropy), dim=1)
        factors = torch.cat((base_factors, exact.factors), dim=1)
        outcome_logits = (
            self.outcome(context_token) if compute_outcome else state.new_zeros((batch, 3))
        )
        next_prefix = (
            self.encoder.update_prefix(prefix, actions, inputs.phase) if compute_prefix else prefix
        )
        return ProgramStepOutput(
            actions=actions,
            masks=cast(ProgramConditionalMasks, replay_masks),
            joint_log_probability=factor_log.sum(dim=1),
            factor_log_probability=factor_log,
            entropy=factor_entropy.sum(dim=1),
            factor_entropy=factor_entropy,
            factors=factors,
            outcome_logits=outcome_logits,
            value=_outcome_values(outcome_logits),
            next_prefix=next_prefix,
        )


__all__ = ["ConditionalProgramPolicy"]
