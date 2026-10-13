"""Neural policy and exact likelihood for incremental portfolios."""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import Tensor, nn

from kagg_revue.policy.economics.layout import TURN_FEATURES
from kagg_revue.policy.plans.backbone import (
    PlanBackboneEncoding,
    StructuredPlanBackbone,
)
from kagg_revue.policy.plans.critic import StructuredPlanOutcomeHead
from kagg_revue.policy.plans.decoder import StructuredPlanFactorDecoder
from kagg_revue.policy.plans.grammar import (
    GLOBAL_FIELD_CARDINALITIES,
    GLOBAL_FIELDS,
    GLOBAL_OPERATION_TOKENS,
    GLOBAL_SET,
    GLOBAL_VALUE_TOKENS,
    LINE_FIELD_CARDINALITIES,
    LINE_FIELDS,
    LINE_OPERATION_TOKENS,
    LINE_VALUE_TOKENS,
    MODE_TOKENS,
    PRODUCTION_LINES,
    UPSERT,
    PlanActions,
    PlanConditionalMasks,
    PlanInputs,
    global_field_mask,
    global_operation_mask,
    line_field_mask,
    line_operation_mask,
    mode_mask,
)
from kagg_revue.policy.plans.runtime import StructuredPlanRuntimeMixin
from kagg_revue.policy.plans.schema import (
    StructuredPlanArchitecture,
    StructuredPlanBehaviorOutput,
    StructuredPlanPolicyOutput,
)


@dataclass(frozen=True)
class _CategoricalResult:
    selected: Tensor
    log_probability: Tensor
    entropy: Tensor


class StructuredPlanPolicy(StructuredPlanRuntimeMixin, nn.Module):
    """Select multi-line portfolio patches from actor-visible state."""

    def __init__(self, architecture: StructuredPlanArchitecture) -> None:
        """Build a vectorized actor with a detached W/D/L baseline head."""
        super().__init__()
        self.architecture = architecture
        width = architecture.model_width

        self.backbone = StructuredPlanBackbone(architecture)
        self.factor_decoder = StructuredPlanFactorDecoder(architecture)
        self.line_identity_embedding = nn.Embedding(PRODUCTION_LINES, width)
        self.line_field_embeddings = nn.ModuleList(
            nn.Embedding(cardinality, width) for cardinality in LINE_FIELD_CARDINALITIES
        )
        self.global_field_embeddings = nn.ModuleList(
            nn.Embedding(cardinality, width) for cardinality in GLOBAL_FIELD_CARDINALITIES
        )
        self.mode_embedding = nn.Embedding(MODE_TOKENS, width)
        self.line_operation_embedding = nn.Embedding(
            LINE_OPERATION_TOKENS,
            width,
        )
        self.global_operation_embedding = nn.Embedding(
            GLOBAL_OPERATION_TOKENS,
            width,
        )
        self.mode_head = nn.Linear(width, MODE_TOKENS)
        self.line_operation_head = nn.Linear(width, LINE_OPERATION_TOKENS)
        self.line_value_head = nn.Linear(width, LINE_VALUE_TOKENS)
        self.global_operation_head = nn.Linear(width, GLOBAL_OPERATION_TOKENS)
        self.global_value_head = nn.Linear(width, GLOBAL_VALUE_TOKENS)
        self.outcome_head = StructuredPlanOutcomeHead(
            width,
            architecture.rich_global_features,
            architecture.attention_heads,
            TURN_FEATURES,
            architecture.strategy_tokens,
        )
        self._initialize_action_heads()

    def _initialize_action_heads(self) -> None:
        """Start new bundle heads neutral over values and sparse over edits."""
        for head in (
            self.mode_head,
            self.line_operation_head,
            self.line_value_head,
            self.global_operation_head,
            self.global_value_head,
        ):
            nn.init.zeros_(head.weight)
            nn.init.zeros_(head.bias)
        with torch.no_grad():
            self.line_operation_head.bias.copy_(
                torch.tensor(tuple(math.log(value) for value in (0.9, 0.08, 0.02)))
            )
            self.global_operation_head.bias.copy_(
                torch.tensor(tuple(math.log(value) for value in (0.9, 0.1)))
            )

    @staticmethod
    def action_initialization_report() -> dict[str, list[float]]:
        """Return the semantic prior applied only to fresh action heads."""
        return {
            "mode": [0.5, 0.5],
            "line_operation": [0.9, 0.08, 0.02],
            "global_operation": [0.9, 0.1],
            "conditional_values": [1.0 / LINE_VALUE_TOKENS] * LINE_VALUE_TOKENS,
        }

    def parameter_report(self) -> dict[str, int]:
        """Measure actor, critic, and total parameters from the built model."""
        critic = sum(parameter.numel() for parameter in self.outcome_head.parameters())
        total = sum(parameter.numel() for parameter in self.parameters())
        return {
            "actor": total - critic,
            "critic": critic,
            "total": total,
            "trainable": sum(
                parameter.numel()
                for parameter in self.parameters()
                if parameter.requires_grad
            ),
        }

    def _encode(
        self,
        inputs: PlanInputs,
        *,
        validate_values: bool,
        episode_index: Tensor | None = None,
        encoding: PlanBackboneEncoding | None = None,
    ) -> tuple[PlanBackboneEncoding, Tensor]:
        architecture = self.architecture
        inputs.validate(
            observation_features=architecture.observation_features,
            journal_features=architecture.journal_features,
            event_features=architecture.event_features,
            production_lines=architecture.production_lines,
            line_fields=architecture.line_fields,
            global_fields=architecture.global_fields,
            board_shape=architecture.board_shape,
            unit_shape=architecture.unit_shape,
            global_features=architecture.rich_global_features,
            economic_state_features=architecture.economic_state_features,
            validate_values=validate_values,
        )
        if encoding is None:
            encoding = (
                self.backbone.encode_sequence(inputs, episode_index)
                if episode_index is not None
                else self.backbone.encode_current(inputs)
            )
        factors = self.factor_decoder(
            encoding.decoder_memory,
            encoding.decoder_memory_mask,
            encoding.strategy,
        )
        return encoding, factors

    @staticmethod
    def _categorical(
        logits: Tensor,
        mask: Tensor,
        supplied: Tensor | None,
        *,
        sample: bool,
        generator: torch.Generator | None,
        validate: bool,
        statistics: bool = True,
        record_entropy: bool = True,
    ) -> _CategoricalResult:
        """Sample a tensor of categorical factors in one vectorized operation."""
        legal = mask.bool()
        if legal.shape != logits.shape:
            raise ValueError("structured-plan logits and conditional mask must align")
        prefix = logits.shape[:-1]
        vocabulary = logits.shape[-1]
        flat_legal = legal.reshape(-1, vocabulary)
        flat_logits = logits.float().reshape(-1, vocabulary)
        if validate and bool(torch.any(~flat_legal.any(dim=1))):
            raise ValueError("structured-plan conditional distribution has no legal token")
        masked_logits = flat_logits.masked_fill(~flat_legal, float("-inf"))
        log_probabilities = torch.log_softmax(masked_logits, dim=-1)
        probabilities = torch.exp(log_probabilities)
        if supplied is not None:
            selected = supplied.long().reshape(-1)
        elif sample:
            selected = torch.multinomial(
                probabilities,
                num_samples=1,
                generator=generator,
            ).squeeze(1)
        else:
            selected = masked_logits.argmax(dim=-1)
        if validate:
            if bool(torch.any((selected < 0) | (selected >= vocabulary))):
                raise ValueError("structured-plan selected token is outside its vocabulary")
            if bool(torch.any(~flat_legal.gather(1, selected[:, None]).squeeze(1))):
                raise ValueError("structured-plan selected token violates its conditional mask")
        if not statistics:
            unused = flat_logits.new_empty(selected.shape)
            return _CategoricalResult(
                selected.reshape(prefix),
                unused.reshape(prefix),
                unused.reshape(prefix),
            )
        selected_log_probability = log_probabilities.gather(
            1,
            selected[:, None],
        ).squeeze(1)
        entropy = (
            -(probabilities * log_probabilities.masked_fill(~flat_legal, 0.0)).sum(dim=-1)
            if record_entropy
            else flat_logits.new_empty(0)
        )
        return _CategoricalResult(
            selected.reshape(prefix),
            selected_log_probability.reshape(prefix),
            entropy.reshape(prefix) if record_entropy else entropy,
        )

    @staticmethod
    def _select_mask(
        generated: Tensor,
        stored: Tensor | None,
        *,
        validate: bool,
        name: str,
    ) -> Tensor:
        if stored is None:
            return generated
        selected = stored.bool()
        if validate and not torch.equal(generated.bool(), selected):
            raise ValueError(f"stored structured-plan {name} mask differs from its prefix")
        return selected

    def _line_operations(
        self,
        factors: Tensor,
        inputs: PlanInputs,
        mode: _CategoricalResult,
        actions: PlanActions | None,
        masks: PlanConditionalMasks | None,
        *,
        sample: bool,
        generator: torch.Generator | None,
        validate: bool,
        statistics: bool,
        record_entropy: bool,
    ) -> tuple[_CategoricalResult, Tensor, Tensor]:
        batch = inputs.batch_size
        line_ids = self.line_identity_embedding.weight[None].expand(batch, -1, -1)
        operation_hidden = factors[:, 1 : 1 + PRODUCTION_LINES]
        context = (
            operation_hidden
            + line_ids
            + self.mode_embedding(mode.selected)[:, None]
        )
        logits = self.line_operation_head(context)
        prefix_generated = torch.stack(
            tuple(
                line_operation_mask(inputs.active_line_mask[:, line])
                for line in range(PRODUCTION_LINES - 1)
            ),
            dim=1,
        )
        prefix_mask = self._select_mask(
            prefix_generated,
            None if masks is None else masks.line_operations[:, :-1],
            validate=validate,
            name="line-operation prefix",
        )
        prefix = self._categorical(
            logits[:, :-1],
            prefix_mask,
            None if actions is None else actions.line_operations[:, :-1],
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )
        active_portfolio = inputs.active_line_mask.bool().any(dim=1)
        force_last = ~active_portfolio & ~(prefix.selected == UPSERT).any(dim=1)
        final_generated = line_operation_mask(
            inputs.active_line_mask[:, -1],
            force_upsert=force_last,
        )
        final_mask = self._select_mask(
            final_generated,
            None if masks is None else masks.line_operations[:, -1],
            validate=validate,
            name="final line-operation",
        )
        final = self._categorical(
            logits[:, -1],
            final_mask,
            None if actions is None else actions.line_operations[:, -1],
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )
        selected = torch.cat((prefix.selected, final.selected[:, None]), dim=1)
        log_probability = torch.cat(
            (prefix.log_probability, final.log_probability[:, None]),
            dim=1,
        )
        entropy = (
            torch.cat((prefix.entropy, final.entropy[:, None]), dim=1)
            if record_entropy
            else logits.new_empty(0, dtype=torch.float32)
        )
        selected_masks = (
            torch.cat((prefix_mask, final_mask[:, None]), dim=1)
            if statistics
            else final_mask.new_empty(
                (
                    inputs.batch_size,
                    PRODUCTION_LINES,
                    LINE_OPERATION_TOKENS,
                )
            )
        )
        return (
            _CategoricalResult(selected, log_probability, entropy),
            selected_masks,
            context,
        )

    def _line_values(
        self,
        factors: Tensor,
        inputs: PlanInputs,
        mode: _CategoricalResult,
        operations: _CategoricalResult,
        actions: PlanActions | None,
        masks: PlanConditionalMasks | None,
        *,
        sample: bool,
        generator: torch.Generator | None,
        validate: bool,
        statistics: bool,
        record_entropy: bool,
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        upsert = operations.selected == UPSERT
        value_start = 1 + PRODUCTION_LINES
        hidden = factors[
            :,
            value_start : value_start + PRODUCTION_LINES * LINE_FIELDS,
        ].reshape(
            inputs.batch_size,
            PRODUCTION_LINES,
            LINE_FIELDS,
            -1,
        )
        base = (
            self.line_identity_embedding.weight[None]
            + self.mode_embedding(mode.selected)[:, None]
            + self.line_operation_embedding(operations.selected)
        )
        prefix_generated = torch.stack(
            tuple(
                line_field_mask(field, upsert.flatten()).reshape(
                    inputs.batch_size,
                    PRODUCTION_LINES,
                    LINE_VALUE_TOKENS,
                )
                for field in range(LINE_FIELDS - 1)
            ),
            dim=2,
        )
        prefix_mask = self._select_mask(
            prefix_generated,
            None if masks is None else masks.line_values[..., :-1, :],
            validate=validate,
            name="line-value prefix",
        )
        prefix = self._categorical(
            self.line_value_head(hidden[..., :-1, :] + base[..., None, :]),
            prefix_mask,
            None if actions is None else actions.line_values[..., :-1],
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )
        prefix_selected = prefix.selected
        prefix_context = torch.stack(
            tuple(
                embedding(prefix_selected[..., field])
                for field, embedding in enumerate(self.line_field_embeddings[:-1])
            ),
            dim=0,
        ).sum(dim=0)
        final_generated = line_field_mask(
            LINE_FIELDS - 1,
            upsert.flatten(),
        ).reshape(
            inputs.batch_size,
            PRODUCTION_LINES,
            LINE_VALUE_TOKENS,
        )
        same_prefix = (
            inputs.active_line_mask.bool()
            & upsert
            & (prefix_selected == inputs.active_lines[..., :-1]).all(dim=-1)
        )
        forbidden = torch.zeros_like(final_generated)
        forbidden.scatter_(
            -1,
            inputs.active_lines[..., -1, None].long(),
            same_prefix[..., None],
        )
        final_generated &= ~forbidden
        final_mask = self._select_mask(
            final_generated,
            None if masks is None else masks.line_values[..., -1, :],
            validate=validate,
            name="final line-value",
        )
        final = self._categorical(
            self.line_value_head(hidden[..., -1, :] + base + prefix_context),
            final_mask,
            None if actions is None else actions.line_values[..., -1],
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )
        values = torch.cat((prefix_selected, final.selected[..., None]), dim=-1)
        if statistics:
            log_probability = torch.cat(
                (prefix.log_probability, final.log_probability[..., None]),
                dim=-1,
            )
            entropy = (
                torch.cat(
                    (prefix.entropy, final.entropy[..., None]),
                    dim=-1,
                )
                if record_entropy
                else hidden.new_empty(0, dtype=torch.float32)
            )
            selected_masks = torch.cat(
                (prefix_mask, final_mask[..., None, :]),
                dim=2,
            )
        else:
            shape = (inputs.batch_size, PRODUCTION_LINES, LINE_FIELDS)
            log_probability = hidden.new_empty(shape, dtype=torch.float32)
            entropy = hidden.new_empty(shape, dtype=torch.float32)
            selected_masks = final_mask.new_empty((*shape, LINE_VALUE_TOKENS))
        return values, log_probability, entropy, selected_masks

    def _global_update(
        self,
        factors: Tensor,
        inputs: PlanInputs,
        mode: _CategoricalResult,
        line_operations: _CategoricalResult,
        actions: PlanActions | None,
        masks: PlanConditionalMasks | None,
        *,
        sample: bool,
        generator: torch.Generator | None,
        validate: bool,
        statistics: bool,
        record_entropy: bool,
    ) -> tuple[_CategoricalResult, Tensor, Tensor, Tensor, Tensor, Tensor]:
        initial_update = ~inputs.active_line_mask.bool().any(dim=1)
        operation_generated = global_operation_mask(initial_update)
        operation_mask = self._select_mask(
            operation_generated,
            None if masks is None else masks.global_operation,
            validate=validate,
            name="global-operation",
        )
        operation_index = 1 + PRODUCTION_LINES + PRODUCTION_LINES * LINE_FIELDS
        operation_context = (
            factors[:, operation_index]
            + self.mode_embedding(mode.selected)
            + self.line_operation_embedding(line_operations.selected).mean(dim=1)
        )
        operation = self._categorical(
            self.global_operation_head(operation_context),
            operation_mask,
            None if actions is None else actions.global_operation,
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )
        update = operation.selected == GLOBAL_SET
        value_hidden = factors[
            :,
            operation_index + 1 : operation_index + 1 + GLOBAL_FIELDS,
        ]
        base = (
            self.mode_embedding(mode.selected)
            + self.line_operation_embedding(line_operations.selected).mean(dim=1)
            + self.global_operation_embedding(operation.selected)
        )
        prefix_generated = torch.stack(
            tuple(
                global_field_mask(
                    field,
                    update,
                    initial=initial_update,
                )
                for field in range(GLOBAL_FIELDS - 1)
            ),
            dim=1,
        )
        prefix_mask = self._select_mask(
            prefix_generated,
            None if masks is None else masks.global_values[:, :-1],
            validate=validate,
            name="global-value prefix",
        )
        prefix = self._categorical(
            self.global_value_head(value_hidden[:, :-1] + base[:, None]),
            prefix_mask,
            None if actions is None else actions.global_values[:, :-1],
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )
        prefix_selected = prefix.selected
        prefix_context = torch.stack(
            tuple(
                embedding(prefix_selected[:, field])
                for field, embedding in enumerate(self.global_field_embeddings[:-1])
            ),
            dim=0,
        ).sum(dim=0)
        final_generated = global_field_mask(
            GLOBAL_FIELDS - 1,
            update,
            initial=initial_update,
        )
        initialized = inputs.active_line_mask.bool().any(dim=1)
        same_prefix = (
            initialized & update & (prefix_selected == inputs.global_plan[:, :-1]).all(dim=1)
        )
        forbidden = torch.zeros_like(final_generated)
        forbidden.scatter_(
            1,
            inputs.global_plan[:, -1, None].long(),
            same_prefix[:, None],
        )
        final_generated &= ~forbidden
        final_mask = self._select_mask(
            final_generated,
            None if masks is None else masks.global_values[:, -1],
            validate=validate,
            name="final global-value",
        )
        final = self._categorical(
            self.global_value_head(value_hidden[:, -1] + base + prefix_context),
            final_mask,
            None if actions is None else actions.global_values[:, -1],
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )
        values = torch.cat((prefix_selected, final.selected[:, None]), dim=1)
        if statistics:
            value_log_probability = torch.cat(
                (prefix.log_probability, final.log_probability[:, None]),
                dim=1,
            )
            value_entropy = (
                torch.cat(
                    (prefix.entropy, final.entropy[:, None]),
                    dim=1,
                )
                if record_entropy
                else value_hidden.new_empty(0, dtype=torch.float32)
            )
            value_masks = torch.cat(
                (prefix_mask, final_mask[:, None]),
                dim=1,
            )
        else:
            shape = (inputs.batch_size, GLOBAL_FIELDS)
            value_log_probability = value_hidden.new_empty(shape, dtype=torch.float32)
            value_entropy = value_hidden.new_empty(shape, dtype=torch.float32)
            value_masks = final_mask.new_empty((*shape, GLOBAL_VALUE_TOKENS))
        return (
            operation,
            operation_mask,
            values,
            value_log_probability,
            value_entropy,
            value_masks,
        )

    def _decode(
        self,
        inputs: PlanInputs,
        actions: PlanActions | None,
        masks: PlanConditionalMasks | None,
        *,
        sample: bool,
        generator: torch.Generator | None,
        validate: bool,
        validate_inputs: bool,
        statistics: bool = True,
        behavior_only: bool = False,
        episode_index: Tensor | None = None,
        encoding: PlanBackboneEncoding | None = None,
    ) -> StructuredPlanPolicyOutput | StructuredPlanBehaviorOutput | PlanActions:
        if behavior_only and not statistics:
            raise ValueError("execution-only decoding cannot retain PPO behavior")
        record_entropy = statistics and not behavior_only
        encoding, factors = self._encode(
            inputs,
            validate_values=validate_inputs,
            episode_index=episode_index,
            encoding=encoding,
        )
        root = factors[:, 0]
        batch = inputs.batch_size
        architecture = self.architecture
        if actions is not None:
            actions.validate(
                batch,
                architecture.production_lines,
                architecture.line_fields,
                architecture.global_fields,
            )
        if masks is not None:
            masks.validate(
                batch,
                architecture.production_lines,
                architecture.line_fields,
                architecture.global_fields,
            )

        active_portfolio = inputs.active_line_mask.bool().any(dim=1)
        generated_mode_mask = mode_mask(active_portfolio)
        selected_mode_mask = self._select_mask(
            generated_mode_mask,
            None if masks is None else masks.mode,
            validate=validate,
            name="mode",
        )
        mode = self._categorical(
            self.mode_head(root),
            selected_mode_mask,
            None if actions is None else actions.mode,
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )
        line_operations, line_operation_masks, _line_context = self._line_operations(
            factors,
            inputs,
            mode,
            actions,
            masks,
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )
        (
            line_values,
            line_value_log_probability,
            line_value_entropy,
            line_value_masks,
        ) = self._line_values(
            factors,
            inputs,
            mode,
            line_operations,
            actions,
            masks,
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )
        (
            global_operation,
            global_operation_mask_selected,
            global_values,
            global_value_log_probability,
            global_value_entropy,
            global_value_masks,
        ) = self._global_update(
            factors,
            inputs,
            mode,
            line_operations,
            actions,
            masks,
            sample=sample,
            generator=generator,
            validate=validate,
            statistics=statistics,
            record_entropy=record_entropy,
        )

        decoded_actions = PlanActions(
            mode=mode.selected,
            line_operations=line_operations.selected,
            line_values=line_values,
            global_operation=global_operation.selected,
            global_values=global_values,
        )
        if not statistics:
            return decoded_actions

        upsert = line_operations.selected == UPSERT
        global_set = global_operation.selected == GLOBAL_SET
        generated_factor_mask = torch.cat(
            (
                torch.ones((batch, 1), dtype=torch.bool, device=root.device),
                torch.ones(
                    (batch, PRODUCTION_LINES),
                    dtype=torch.bool,
                    device=root.device,
                ),
                upsert[..., None].expand(-1, -1, LINE_FIELDS).flatten(1),
                torch.ones((batch, 1), dtype=torch.bool, device=root.device),
                global_set[:, None].expand(-1, GLOBAL_FIELDS),
            ),
            dim=1,
        )
        selected_factor_mask = self._select_mask(
            generated_factor_mask,
            None if masks is None else masks.factors,
            validate=validate,
            name="factor",
        )
        factor_log_probability = torch.cat(
            (
                mode.log_probability[:, None],
                line_operations.log_probability,
                line_value_log_probability.flatten(1),
                global_operation.log_probability[:, None],
                global_value_log_probability,
            ),
            dim=1,
        )
        joint_log_probability = factor_log_probability.masked_fill(
            ~selected_factor_mask,
            0.0,
        ).sum(dim=1)
        if record_entropy:
            operation_entropy = (line_operations.entropy.sum(dim=1) + global_operation.entropy) / (
                PRODUCTION_LINES + 1
            )
            value_factor_count = (
                upsert.sum(dim=1) * LINE_FIELDS + global_set.to(torch.long) * GLOBAL_FIELDS
            )
            value_entropy = (
                line_value_entropy.sum(dim=(1, 2)) + global_value_entropy.sum(dim=1)
            ) / value_factor_count.clamp_min(1).to(line_value_entropy.dtype)
            has_values = value_factor_count > 0
            entropy = (
                mode.entropy + operation_entropy + value_entropy.masked_fill(~has_values, 0.0)
            ) / (2 + has_values.to(torch.long)).to(mode.entropy.dtype)
        else:
            entropy = root.new_empty(0, dtype=torch.float32)

        value_logits = self.outcome_head(
            encoding.history.detach(),
            inputs.global_features,
            encoding.scene_memory.detach(),
            encoding.scene_memory_mask,
            encoding.economic_features.detach(),
            None if encoding.strategy is None else encoding.strategy.detach(),
        )
        probabilities = torch.softmax(value_logits.float(), dim=-1)
        value = probabilities[:, 2] - probabilities[:, 0]
        behavior = StructuredPlanBehaviorOutput(
            actions=decoded_actions,
            masks=PlanConditionalMasks(
                mode=selected_mode_mask,
                line_operations=line_operation_masks,
                line_values=line_value_masks,
                global_operation=global_operation_mask_selected,
                global_values=global_value_masks,
                factors=selected_factor_mask,
            ),
            joint_log_probability=joint_log_probability,
            value=value,
        )
        if behavior_only:
            return behavior
        return StructuredPlanPolicyOutput(
            actions=behavior.actions,
            masks=behavior.masks,
            joint_log_probability=joint_log_probability,
            factor_log_probability=factor_log_probability,
            entropy=entropy,
            value_logits=value_logits,
            value=value,
        )

__all__ = [
    "StructuredPlanArchitecture",
    "StructuredPlanBehaviorOutput",
    "StructuredPlanPolicy",
    "StructuredPlanPolicyOutput",
]
