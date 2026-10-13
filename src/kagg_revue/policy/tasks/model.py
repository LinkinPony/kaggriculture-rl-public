"""Conditional pointer policy over compiler-generated unit tasks."""

from __future__ import annotations

import math
from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.cuda.categorical import sample_masked
from kagg_revue.policy.tasks.contract import SuffixMode, TaskOperation
from kagg_revue.policy.tasks.factorized import FactorizedTaskPolicy
from kagg_revue.policy.tasks.grammar import (
    TASK_FACTOR_COUNT,
    FactorizedTaskDecisionInputs,
    FactorizedTaskMasks,
    TaskActions,
    TaskCatalog,
    TaskConditionalMasks,
    TaskDecisionInputs,
    conditional_masks,
)
from kagg_revue.policy.tasks.pooled import (
    PooledCandidateEncoder,
    PooledTaskPrefixEncoder,
)
from kagg_revue.policy.tasks.schema import TaskPolicyOutput, TaskTapeArchitecture


def _outcome_values(logits: Tensor) -> Tensor:
    """Return expected seat-relative W/D/L without an RL-package dependency."""
    probabilities = torch.softmax(logits.float(), dim=-1)
    return probabilities[..., 2] - probabilities[..., 0]


def _masked_statistics(
    logits: Tensor,
    mask: Tensor,
    selected: Tensor,
    active: Tensor,
    *,
    validate: bool,
) -> tuple[Tensor, Tensor]:
    safe_mask = mask.bool()
    safe_selected = selected.clamp(0, logits.shape[1] - 1)
    if validate:
        if not bool(safe_mask.any(dim=1).all()):
            raise ValueError("unit-task categorical factor has an empty legal set")
        chosen_legal = safe_mask.gather(1, safe_selected[:, None]).squeeze(1)
        if bool(torch.any(active & ~chosen_legal)):
            raise ValueError("unit-task selected token is absent from its exact mask")
    masked_logits = logits.float().masked_fill(~safe_mask, -torch.inf)
    log_probabilities = torch.log_softmax(masked_logits, dim=1)
    probabilities = log_probabilities.exp()
    selected_log_probability = log_probabilities.gather(1, safe_selected[:, None]).squeeze(1)
    entropy = -(probabilities * log_probabilities.masked_fill(~safe_mask, 0.0)).sum(dim=1)
    zeros = torch.zeros_like(selected_log_probability)
    return (
        torch.where(active, selected_log_probability, zeros),
        torch.where(active, entropy, zeros),
    )


def _choose_statistics(
    logits: Tensor,
    mask: Tensor,
    *,
    sample: bool,
    generator: torch.Generator | None,
    compute_entropy: bool,
    uniform: Tensor | None = None,
) -> tuple[Tensor, Tensor, Tensor]:
    """Select once and reuse its normalized distribution statistics."""
    if uniform is not None:
        if not sample or compute_entropy or torch.is_grad_enabled():
            raise ValueError("fused categorical sampling is inference-only without entropy")
        selected, selected_log_probability = sample_masked(
            logits.contiguous(), mask.bool().contiguous(), uniform
        )
        return (
            selected,
            selected_log_probability,
            torch.zeros_like(selected_log_probability),
        )
    masked = logits.float().masked_fill(~mask.bool(), -torch.inf)
    log_probabilities = torch.log_softmax(masked, dim=1)
    if sample:
        probabilities = log_probabilities.exp()
        selected = torch.multinomial(
            probabilities,
            1,
            generator=generator,
        ).squeeze(1)
    else:
        selected = masked.argmax(dim=1)
    selected_log_probability = log_probabilities.gather(1, selected[:, None]).squeeze(1)
    if compute_entropy:
        if not sample:
            probabilities = log_probabilities.exp()
        entropy = -(probabilities * log_probabilities.masked_fill(~mask.bool(), 0.0)).sum(dim=1)
    else:
        entropy = torch.zeros_like(selected_log_probability)
    return selected, selected_log_probability, entropy


class TaskPrefixEncoder(nn.Module):
    """Encode the complete accepted task/result prefix with stable positions."""

    def __init__(self, architecture: TaskTapeArchitecture) -> None:
        """Create typed task embeddings and a compact transformer."""
        super().__init__()
        width = architecture.model_width
        self.architecture = architecture
        self.unit = nn.Embedding(architecture.unit_limit, width)
        self.operation = nn.Embedding(architecture.operation_tokens, width)
        self.argument = nn.Embedding(architecture.item_tokens + 1, width)
        self.x = nn.Embedding(architecture.board_size + 1, width)
        self.y = nn.Embedding(architecture.board_size + 1, width)
        self.quantity = nn.Embedding(architecture.maximum_quantity + 1, width)
        self.earliest = nn.Embedding(architecture.time_tokens, width)
        self.deadline = nn.Embedding(architecture.time_tokens, width)
        self.status = nn.Embedding(architecture.status_tokens, width)
        self.position = nn.Embedding(architecture.prefix_capacity + 1, width)
        self.begin = nn.Parameter(torch.empty(width).normal_(std=0.02))
        layer = nn.TransformerEncoderLayer(
            d_model=width,
            nhead=architecture.attention_heads,
            dim_feedforward=architecture.feedforward_width,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.blocks = nn.TransformerEncoder(
            layer,
            num_layers=architecture.prefix_layers,
            enable_nested_tensor=False,
        )
        self.output_norm = nn.LayerNorm(width)

    def forward(
        self,
        fields: Tensor,
        mask: Tensor,
        active_length: int | None = None,
    ) -> Tensor:
        """Return the summary token after attending over valid prefix rows."""
        # Rollout and dataset collation already know the contiguous prefix length
        # on the host. Carrying it with the batch avoids a mid-forward CUDA-to-host
        # synchronization while still trimming quadratic attention over padding.
        active = (
            int(mask.sum(dim=1).max().detach().cpu()) if active_length is None else active_length
        )
        if active < 0 or active > fields.shape[1]:
            raise ValueError("unit-task active prefix length is outside its tensor")
        values = fields[:, :active]
        mask = mask[:, :active]
        hidden = (
            self.unit(values[..., 0].clamp(0, self.architecture.unit_limit - 1))
            + self.operation(values[..., 1].clamp(0, self.architecture.operation_tokens - 1))
            + self.argument(values[..., 2].clamp(0, self.architecture.item_tokens))
            + self.x(values[..., 3].clamp(0, self.architecture.board_size))
            + self.y(values[..., 4].clamp(0, self.architecture.board_size))
            + self.quantity(values[..., 5].clamp(0, self.architecture.maximum_quantity))
            + self.earliest(values[..., 6].clamp(0, self.architecture.time_tokens - 1))
            + self.deadline(values[..., 7].clamp(0, self.architecture.time_tokens - 1))
            + self.status(values[..., 8].clamp(0, self.architecture.status_tokens - 1))
        )
        batch = fields.shape[0]
        begin = self.begin[None, None].expand(batch, 1, -1)
        hidden = torch.cat((begin, hidden), dim=1)
        positions = torch.arange(hidden.shape[1], device=hidden.device)
        hidden = hidden + self.position(positions)[None]
        valid = torch.cat(
            (
                torch.ones((batch, 1), dtype=torch.bool, device=mask.device),
                mask.bool(),
            ),
            dim=1,
        )
        encoded = self.blocks(hidden, src_key_padding_mask=~valid)
        return cast(Tensor, self.output_norm(encoded[:, 0]))


class UnitTaskPolicy(nn.Module):
    """Task-level actor-critic sharing a verified observation context."""

    catalog_operations: Tensor
    catalog_arguments: Tensor
    catalog_targets: Tensor
    catalog_requires_quantity: Tensor
    catalog_operation_turns: Tensor

    def __init__(
        self,
        architecture: TaskTapeArchitecture,
        catalog: TaskCatalog,
    ) -> None:
        """Create conditional heads around one authenticated native catalog."""
        super().__init__()
        catalog.validate()
        if catalog.candidate_count != architecture.candidate_count:
            raise ValueError("unit-task catalog differs from the architecture")
        self.architecture = architecture
        self.register_buffer("catalog_operations", catalog.operations.long().clone())
        self.register_buffer("catalog_arguments", catalog.arguments.long().clone())
        self.register_buffer("catalog_targets", catalog.targets.long().clone())
        self.register_buffer("catalog_requires_quantity", catalog.requires_quantity.bool().clone())
        self.register_buffer("catalog_operation_turns", catalog.operation_turns.long().clone())
        self.factorized: FactorizedTaskPolicy | None = None
        self._rollout_candidate_static: Tensor | None = None
        if architecture.architecture_version == "factorized-v3":
            self.factorized = FactorizedTaskPolicy(architecture, catalog)
            return
        width = architecture.model_width
        self.context = nn.Sequential(
            nn.LayerNorm(architecture.context_width),
            nn.Linear(architecture.context_width, width),
            nn.SiLU(),
        )
        self.root = nn.Sequential(
            nn.Linear(architecture.root_features, width),
            nn.SiLU(),
            nn.Linear(width, width),
        )
        self.prefix: TaskPrefixEncoder | PooledTaskPrefixEncoder
        self.prefix = (
            PooledTaskPrefixEncoder(architecture)
            if architecture.architecture_version == "pooled-v2"
            else TaskPrefixEncoder(architecture)
        )
        self.state = nn.Sequential(
            nn.LayerNorm(3 * width),
            nn.Linear(3 * width, architecture.feedforward_width),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, width),
            nn.LayerNorm(width),
        )
        self.operation = nn.Embedding(architecture.operation_tokens, width)
        self.argument = nn.Embedding(architecture.item_tokens + 1, width)
        self.x = nn.Embedding(architecture.board_size + 1, width)
        self.y = nn.Embedding(architecture.board_size + 1, width)
        self.candidate_features: nn.Module = (
            PooledCandidateEncoder(architecture)
            if architecture.architecture_version == "pooled-v2"
            else nn.Sequential(
                nn.Linear(
                    architecture.candidate_features,
                    architecture.feedforward_width,
                ),
                nn.SiLU(),
                nn.Linear(architecture.feedforward_width, width),
                nn.LayerNorm(width),
            )
        )
        self.legal_attention: nn.MultiheadAttention | None = (
            None
            if architecture.architecture_version == "pooled-v2"
            else nn.MultiheadAttention(
                width,
                architecture.attention_heads,
                batch_first=True,
            )
        )
        self.mode_head = nn.Linear(width, 2)
        self.candidate_query = nn.Linear(width, width, bias=False)
        self.candidate_bias = nn.Linear(width, 1, bias=False)
        self.quantity_embedding = nn.Embedding(architecture.maximum_quantity + 1, width)
        self.time_embedding = nn.Embedding(architecture.time_tokens, width)
        self.quantity_head = nn.Linear(width, architecture.maximum_quantity)
        self.earliest_head = nn.Linear(width, architecture.time_tokens)
        self.deadline_head = nn.Linear(width, architecture.time_tokens)
        self.task_condition = nn.Sequential(
            nn.LayerNorm(2 * width),
            nn.Linear(2 * width, width),
            nn.SiLU(),
        )
        self.outcome_head = nn.Sequential(
            nn.LayerNorm(width),
            nn.Linear(width, width),
            nn.SiLU(),
            nn.Linear(width, 3),
        )
        self._initialize_actor_heads()

    def _initialize_actor_heads(self) -> None:
        """Start all strategic choices neutral over their exact legal sets."""
        for head in (
            self.mode_head,
            self.candidate_query,
            self.candidate_bias,
            self.quantity_head,
            self.earliest_head,
            self.deadline_head,
        ):
            nn.init.zeros_(head.weight)
            if head.bias is not None:
                nn.init.zeros_(head.bias)

    def catalog(self) -> TaskCatalog:
        """Return the registered immutable candidate tensors."""
        return TaskCatalog(
            operations=self.catalog_operations,
            arguments=self.catalog_arguments,
            targets=self.catalog_targets,
            requires_quantity=self.catalog_requires_quantity,
            operation_turns=self.catalog_operation_turns,
        )

    def train(self, mode: bool = True) -> UnitTaskPolicy:
        """Switch modes without invalidating captured rollout storage."""
        return super().train(mode)

    def prepare_rollout(self) -> None:
        """Refresh parameter-dependent catalog embeddings at a stable address."""
        if self.factorized is not None:
            return
        if self.training:
            raise RuntimeError("unit-task rollout cache requires evaluation mode")
        with torch.inference_mode():
            updated = self._static_candidate_encoding()
            cached = self._rollout_candidate_static
            if (
                cached is None
                or cached.shape != updated.shape
                or cached.dtype != updated.dtype
                or cached.device != updated.device
            ):
                self._rollout_candidate_static = updated
            else:
                cached.copy_(updated)

    def _validate_inputs(self, inputs: TaskDecisionInputs, *, values: bool) -> None:
        architecture = self.architecture
        inputs.validate(
            context_width=architecture.context_width,
            root_features=architecture.root_features,
            prefix_capacity=architecture.prefix_capacity,
            task_fields=architecture.task_fields,
            candidate_count=architecture.candidate_count,
            candidate_features=architecture.candidate_features,
            time_tokens=architecture.time_tokens,
        )
        if not values:
            return
        active = inputs.prefix_fields[inputs.prefix_mask.bool()]
        if active.numel() == 0:
            return
        limits = (
            architecture.unit_limit,
            architecture.operation_tokens,
            architecture.item_tokens + 1,
            architecture.board_size + 1,
            architecture.board_size + 1,
            architecture.maximum_quantity + 1,
            architecture.time_tokens,
            architecture.time_tokens,
            architecture.status_tokens,
        )
        for field, limit in enumerate(limits):
            if bool(torch.any((active[:, field] < 0) | (active[:, field] >= limit))):
                raise ValueError("unit-task prefix contains a token outside the ABI")

    def _static_candidate_encoding(self) -> Tensor:
        operations = self.catalog_operations
        arguments = self.catalog_arguments + 1
        targets = self.catalog_targets + 1
        return cast(
            Tensor,
            (
                self.operation(operations)[None]
                + self.argument(arguments)[None]
                + self.x(targets[:, 0])[None]
                + self.y(targets[:, 1])[None]
            ),
        )

    def _candidate_encoding(self, inputs: TaskDecisionInputs) -> Tensor:
        static = None if self.training else self._rollout_candidate_static
        if static is None or static.device != inputs.context.device:
            static = self._static_candidate_encoding()
        if self.architecture.architecture_version == "pooled-v2":
            return static.expand(inputs.batch_size, -1, -1)
        candidate_features = inputs.candidate_features
        if not torch.is_autocast_enabled(candidate_features.device.type):
            candidate_features = candidate_features.float()
        dynamic = cast(Tensor, self.candidate_features(candidate_features))
        return static + dynamic

    def _encoding(self, inputs: TaskDecisionInputs) -> tuple[Tensor, Tensor, Tensor]:
        prefix = self.prefix(
            inputs.prefix_fields,
            inputs.prefix_mask,
            inputs.prefix_length,
        )
        state = self.state(
            torch.cat(
                (
                    self.context(inputs.context.float()),
                    self.root(inputs.root_features.float()),
                    prefix,
                ),
                dim=1,
            )
        )
        candidates = self._candidate_encoding(inputs)
        if self.legal_attention is not None:
            legal, _weights = self.legal_attention(
                state[:, None],
                candidates,
                candidates,
                key_padding_mask=~inputs.candidate_mask.bool(),
                need_weights=False,
            )
            state = state + legal[:, 0]
        score_vector = self.candidate_query(state) / math.sqrt(self.architecture.model_width)
        score_vector = score_vector + self.candidate_bias.weight
        candidate_logits = torch.bmm(
            candidates,
            score_vector[:, :, None],
        ).squeeze(-1)
        if self.architecture.architecture_version == "pooled-v2":
            projection = cast(PooledCandidateEncoder, self.candidate_features).projection
            feature_weights = torch.matmul(score_vector, projection.weight)
            feature_values = inputs.candidate_features
            if not torch.is_autocast_enabled(feature_values.device.type):
                feature_values = feature_values.float()
            candidate_logits = candidate_logits + torch.bmm(
                feature_values,
                feature_weights[:, :, None],
            ).squeeze(-1)
        return state, candidates, candidate_logits

    def _selected_candidate_encoding(
        self,
        inputs: TaskDecisionInputs,
        candidates: Tensor,
        selected: Tensor,
    ) -> Tensor:
        """Encode only selected dynamic facts for the conditional factor heads."""
        rows = torch.arange(inputs.batch_size, device=selected.device)
        result = candidates[rows, selected]
        if self.architecture.architecture_version != "pooled-v2":
            return result
        features = inputs.candidate_features[rows, selected]
        if not torch.is_autocast_enabled(features.device.type):
            features = features.float()
        return cast(Tensor, result + self.candidate_features(features))

    def _logits_for_actions(
        self,
        inputs: TaskDecisionInputs,
        state: Tensor,
        candidates: Tensor,
        actions: TaskActions,
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        selected_candidate = self._selected_candidate_encoding(
            inputs,
            candidates,
            actions.candidate.clamp(0, self.architecture.candidate_count - 1),
        )
        conditioned = self.task_condition(torch.cat((state, selected_candidate), dim=1))
        quantity_hidden = conditioned + self.quantity_embedding(
            actions.quantity.clamp(0, self.architecture.maximum_quantity)
        )
        earliest_hidden = quantity_hidden
        deadline_hidden = earliest_hidden + self.time_embedding(
            actions.earliest.clamp(0, self.architecture.time_tokens - 1)
        )
        return (
            self.mode_head(state),
            self.quantity_head(conditioned),
            self.earliest_head(earliest_hidden),
            self.deadline_head(deadline_hidden),
        )

    def _output_from_logits(
        self,
        inputs: TaskDecisionInputs,
        state: Tensor,
        actions: TaskActions,
        masks: TaskConditionalMasks,
        logits: tuple[Tensor, Tensor, Tensor, Tensor, Tensor],
        *,
        validate: bool,
    ) -> TaskPolicyOutput:
        """Build behavior statistics without repeating the shared encoder."""
        batch = inputs.batch_size
        actions.validate(batch)
        if validate:
            masks.validate(
                batch,
                self.architecture.candidate_count,
                self.architecture.maximum_quantity,
                self.architecture.time_tokens,
            )
            expected = conditional_masks(
                inputs,
                self.catalog(),
                actions,
                maximum_quantity=self.architecture.maximum_quantity,
                time_tokens=self.architecture.time_tokens,
            )
            for name in masks.__dataclass_fields__:
                if not torch.equal(getattr(masks, name).bool(), getattr(expected, name).bool()):
                    raise ValueError(f"stored unit-task {name} mask differs from its prefix")
        factor_log_probability = torch.zeros(
            (batch, TASK_FACTOR_COUNT), dtype=torch.float32, device=state.device
        )
        factor_entropy = torch.zeros_like(factor_log_probability)
        selections = (
            actions.mode,
            actions.candidate,
            (actions.quantity - 1).clamp_min(0),
            actions.earliest,
            actions.deadline,
        )
        factor_masks = (
            masks.mode,
            masks.candidate,
            masks.quantity,
            masks.earliest,
            masks.deadline,
        )
        for factor, (factor_logits, factor_mask, selection) in enumerate(
            zip(logits, factor_masks, selections, strict=True)
        ):
            log_probability, entropy = _masked_statistics(
                factor_logits,
                factor_mask,
                selection,
                masks.factors[:, factor].bool(),
                validate=validate,
            )
            factor_log_probability[:, factor] = log_probability
            factor_entropy[:, factor] = entropy
        outcome_logits = self.outcome_head(state.detach())
        return TaskPolicyOutput(
            actions=actions,
            masks=masks,
            joint_log_probability=factor_log_probability.sum(dim=1),
            factor_log_probability=factor_log_probability,
            entropy=factor_entropy.sum(dim=1),
            factor_entropy=factor_entropy,
            outcome_logits=outcome_logits,
            value=_outcome_values(outcome_logits),
        )

    def _evaluate(
        self,
        inputs: TaskDecisionInputs,
        actions: TaskActions,
        masks: TaskConditionalMasks,
        *,
        validate: bool,
    ) -> TaskPolicyOutput:
        state, candidates, candidate_logits = self._encoding(inputs)
        mode_logits, quantity_logits, earliest_logits, deadline_logits = self._logits_for_actions(
            inputs, state, candidates, actions
        )
        return self._output_from_logits(
            inputs,
            state,
            actions,
            masks,
            (
                mode_logits,
                candidate_logits,
                quantity_logits,
                earliest_logits,
                deadline_logits,
            ),
            validate=validate,
        )

    def rollout(
        self,
        inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
        uniforms: Tensor | None = None,
        validate_inputs: bool = True,
        compute_entropy: bool = True,
    ) -> TaskPolicyOutput:
        """Sample or greedily decode one compiler-in-the-loop task."""
        if self.factorized is not None:
            if not isinstance(inputs, FactorizedTaskDecisionInputs):
                raise TypeError("factorized task policy requires compact decision inputs")
            return self.factorized.rollout(
                inputs,
                self.catalog(),
                sample=sample,
                generator=generator,
                uniforms=uniforms,
                validate_inputs=validate_inputs,
                compute_entropy=compute_entropy,
            )
        if not isinstance(inputs, TaskDecisionInputs):
            raise TypeError("legacy task policy requires its dense decision inputs")
        if validate_inputs:
            self._validate_inputs(inputs, values=True)
        state, candidates, candidate_logits = self._encoding(inputs)
        if uniforms is not None and (
            uniforms.shape != (TASK_FACTOR_COUNT, inputs.batch_size)
            or uniforms.dtype != torch.float32
            or uniforms.device != state.device
            or not sample
            or compute_entropy
            or torch.is_grad_enabled()
        ):
            raise ValueError("task uniforms require inference sampling")
        fused_uniforms = uniforms if uniforms is not None else (
            torch.rand(
                (TASK_FACTOR_COUNT, inputs.batch_size),
                dtype=torch.float32,
                device=state.device,
                generator=generator,
            )
            if sample
            and not compute_entropy
            and state.device.type == "cuda"
            and not torch.is_grad_enabled()
            else None
        )
        mode_logits = self.mode_head(state)
        mode, mode_log_probability, mode_entropy = _choose_statistics(
            mode_logits,
            inputs.mode_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=None if fused_uniforms is None else fused_uniforms[0],
        )
        rewrite = mode == int(SuffixMode.REWRITE)
        chosen, candidate_log_probability, candidate_entropy = _choose_statistics(
            candidate_logits,
            inputs.candidate_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=None if fused_uniforms is None else fused_uniforms[1],
        )
        candidate = torch.where(rewrite, chosen, torch.zeros_like(chosen))
        rows = torch.arange(inputs.batch_size, device=state.device)
        operation = self.catalog_operations[candidate]
        is_end = operation == int(TaskOperation.END)
        needs_quantity = self.catalog_requires_quantity[candidate].bool() & rewrite
        active_task = rewrite & ~is_end
        quantity_mask = torch.zeros(
            (inputs.batch_size, self.architecture.maximum_quantity),
            dtype=torch.bool,
            device=state.device,
        )
        quantity_mask[:, 0] = True
        quantity_mask[needs_quantity] = True
        times = torch.arange(self.architecture.time_tokens, device=state.device)[None]
        available = inputs.available_at[:, None]
        day_end = inputs.day_end[:, None]
        arrival = inputs.candidate_arrivals[rows, candidate][:, None]
        operation_turns = self.catalog_operation_turns[candidate][:, None]
        earliest_mask = active_task[:, None] & (times >= available)
        earliest_mask &= times <= day_end
        wait = operation[:, None] == int(TaskOperation.WAIT)
        earliest_mask &= ~wait | (times > available)
        completion_by_time = torch.maximum(arrival, times) + operation_turns
        earliest_mask &= completion_by_time <= day_end
        earliest_mask[~active_task] = False
        earliest_mask[~active_task, 0] = True
        selected_candidates = self._selected_candidate_encoding(
            inputs,
            candidates,
            candidate,
        )
        conditioned = self.task_condition(torch.cat((state, selected_candidates), dim=1))
        quantity_logits = self.quantity_head(conditioned)
        (
            quantity_index,
            quantity_log_probability,
            quantity_entropy,
        ) = _choose_statistics(
            quantity_logits,
            quantity_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=None if fused_uniforms is None else fused_uniforms[2],
        )
        quantity = torch.where(
            needs_quantity,
            quantity_index + 1,
            torch.zeros_like(quantity_index),
        )
        earliest_hidden = conditioned + self.quantity_embedding(quantity)
        earliest_logits = self.earliest_head(earliest_hidden)
        earliest, earliest_log_probability, earliest_entropy = _choose_statistics(
            earliest_logits,
            earliest_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=None if fused_uniforms is None else fused_uniforms[3],
        )
        completion = torch.maximum(arrival, earliest[:, None]) + operation_turns
        deadline_mask = active_task[:, None] & (times >= completion)
        deadline_mask &= times <= day_end
        deadline_mask[~active_task] = False
        deadline_mask[~active_task, 0] = True
        deadline_hidden = earliest_hidden + self.time_embedding(earliest)
        deadline_logits = self.deadline_head(deadline_hidden)
        deadline, deadline_log_probability, deadline_entropy = _choose_statistics(
            deadline_logits,
            deadline_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=None if fused_uniforms is None else fused_uniforms[4],
        )
        actions = TaskActions(mode, candidate, quantity, earliest, deadline)
        factor_mask = torch.zeros(
            (inputs.batch_size, TASK_FACTOR_COUNT),
            dtype=torch.bool,
            device=state.device,
        )
        factor_mask[:, 0] = inputs.mode_mask.sum(dim=1) > 1
        factor_mask[:, 1] = rewrite & (inputs.candidate_mask.sum(dim=1) > 1)
        factor_mask[:, 2] = needs_quantity & (self.architecture.maximum_quantity > 1)
        factor_mask[:, 3] = active_task & (earliest_mask.sum(dim=1) > 1)
        factor_mask[:, 4] = active_task & (deadline_mask.sum(dim=1) > 1)
        masks = TaskConditionalMasks(
            mode=inputs.mode_mask.bool(),
            candidate=inputs.candidate_mask.bool(),
            quantity=quantity_mask,
            earliest=earliest_mask,
            deadline=deadline_mask,
            factors=factor_mask,
        )
        factor_log_probability = torch.stack(
            (
                mode_log_probability,
                candidate_log_probability,
                quantity_log_probability,
                earliest_log_probability,
                deadline_log_probability,
            ),
            dim=1,
        )
        factor_log_probability = factor_log_probability.masked_fill(~masks.factors.bool(), 0.0)
        factor_entropy = (
            torch.stack(
                (
                    mode_entropy,
                    candidate_entropy,
                    quantity_entropy,
                    earliest_entropy,
                    deadline_entropy,
                ),
                dim=1,
            ).masked_fill(~masks.factors.bool(), 0.0)
            if compute_entropy
            else torch.zeros_like(factor_log_probability)
        )
        outcome_logits = self.outcome_head(state.detach())
        return TaskPolicyOutput(
            actions=actions,
            masks=masks,
            joint_log_probability=factor_log_probability.sum(dim=1),
            factor_log_probability=factor_log_probability,
            entropy=factor_entropy.sum(dim=1),
            factor_entropy=factor_entropy,
            outcome_logits=outcome_logits,
            value=_outcome_values(outcome_logits),
        )

    def evaluate_actions(
        self,
        inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs,
        actions: TaskActions,
        masks: TaskConditionalMasks | FactorizedTaskMasks,
        *,
        validate: bool = True,
        validate_inputs: bool = True,
    ) -> TaskPolicyOutput:
        """Recompute task-level likelihood under stored exact masks."""
        if self.factorized is not None:
            if not isinstance(inputs, FactorizedTaskDecisionInputs) or not isinstance(
                masks, FactorizedTaskMasks
            ):
                raise TypeError("factorized task evaluation requires compact masks")
            return self.factorized.evaluate_actions(
                inputs,
                self.catalog(),
                actions,
                masks,
                validate=validate,
                validate_inputs=validate_inputs,
            )
        if not isinstance(inputs, TaskDecisionInputs) or not isinstance(
            masks, TaskConditionalMasks
        ):
            raise TypeError("legacy task evaluation requires dense masks")
        if validate_inputs:
            self._validate_inputs(inputs, values=True)
        return self._evaluate(inputs, actions, masks, validate=validate)


__all__ = ["TaskPrefixEncoder", "UnitTaskPolicy"]
