"""Typed task policy over operation, argument, and board-target factors."""

from __future__ import annotations

import math
from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.cuda.categorical import sample_masked
from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.tasks.contract import SuffixMode, TaskOperation
from kagg_revue.policy.tasks.gpu.factorized import (
    factorized_argument_inputs,
    factorized_deadline_mask,
    factorized_operation_inputs,
    factorized_route_inputs,
    factorized_temporal_inputs,
)
from kagg_revue.policy.tasks.gpu.normalization import h200_layer_norm
from kagg_revue.policy.tasks.grammar import (
    FACTORIZED_RESOURCE_COUNT,
    FACTORIZED_TASK_FACTOR_COUNT,
    NONE_ARGUMENT,
    FactorizedTaskDecisionInputs,
    FactorizedTaskMasks,
    TaskActions,
    TaskCatalog,
    factorized_argument_mask,
    factorized_arrival,
    factorized_conditional_masks,
    factorized_operation_mask,
    factorized_target_mask,
)
from kagg_revue.policy.tasks.pooled import PooledTaskPrefixEncoder
from kagg_revue.policy.tasks.schema import TaskPolicyOutput, TaskTapeArchitecture


def _outcome_values(logits: Tensor) -> Tensor:
    probabilities = torch.softmax(logits.float(), dim=-1)
    return probabilities[..., 2] - probabilities[..., 0]


def _choose_statistics(
    logits: Tensor,
    mask: Tensor,
    *,
    sample: bool,
    generator: torch.Generator | None,
    compute_entropy: bool,
    uniform: Tensor | None,
) -> tuple[Tensor, Tensor, Tensor]:
    """Choose from one exact mask and reuse its normalized statistics."""
    if uniform is not None:
        selected, log_probability = sample_masked(
            logits.contiguous(), mask.bool().contiguous(), uniform
        )
        return selected, log_probability, torch.zeros_like(log_probability)
    masked = logits.float().masked_fill(~mask.bool(), -torch.inf)
    log_probabilities = torch.log_softmax(masked, dim=1)
    probabilities = log_probabilities.exp()
    selected = (
        torch.multinomial(probabilities, 1, generator=generator).squeeze(1)
        if sample
        else masked.argmax(dim=1)
    )
    log_probability = log_probabilities.gather(1, selected[:, None]).squeeze(1)
    entropy = (
        -(
            probabilities
            * log_probabilities.masked_fill(~mask.bool(), 0.0)
        ).sum(dim=1)
        if compute_entropy
        else torch.zeros_like(log_probability)
    )
    return selected, log_probability, entropy


def _masked_statistics(
    logits: Tensor,
    mask: Tensor,
    selected: Tensor,
    active: Tensor,
    *,
    validate: bool,
) -> tuple[Tensor, Tensor]:
    """Evaluate one teacher-forced typed factor."""
    safe_selected = selected.clamp(0, logits.shape[1] - 1)
    safe_mask = mask.bool()
    if validate:
        if not bool(safe_mask.any(dim=1).all()):
            raise ValueError("factorized unit-task factor has an empty legal set")
        chosen = safe_mask.gather(1, safe_selected[:, None]).squeeze(1)
        if bool(torch.any(active & ~chosen)):
            raise ValueError("factorized unit-task token is absent from its exact mask")
    masked = logits.float().masked_fill(~safe_mask, -torch.inf)
    log_probabilities = torch.log_softmax(masked, dim=1)
    probabilities = log_probabilities.exp()
    log_probability = log_probabilities.gather(1, safe_selected[:, None]).squeeze(1)
    entropy = -(
        probabilities * log_probabilities.masked_fill(~safe_mask, 0.0)
    ).sum(dim=1)
    zeros = torch.zeros_like(log_probability)
    return torch.where(active, log_probability, zeros), torch.where(
        active, entropy, zeros
    )


def _scaled_counts(values: Tensor) -> Tensor:
    """Compress heterogeneous integer counts without fixed game-value bounds."""
    floats = values.float()
    return torch.sign(floats) * torch.log1p(floats.abs()).clamp_max(16.0) / 8.0


class _FactorizedSequential(nn.Sequential):
    """Preserve training modules while fusing rollout LayerNorm on H200."""

    def forward(self, values: Tensor) -> Tensor:
        """Run the exact sequence with launch-efficient inference norms."""
        if values.device.type != "cuda" or torch.is_grad_enabled():
            return cast(
                Tensor,
                super().forward(values),  # type: ignore[no-untyped-call]
            )
        output = values
        for index in range(len(self)):
            module = self[index]
            if isinstance(module, nn.LayerNorm):
                weight = module.weight
                bias = module.bias
                if weight is None or bias is None:
                    raise RuntimeError("factorized task LayerNorm lost affine state")
                output = h200_layer_norm(
                    output.contiguous(), weight, bias, module.eps
                )
            else:
                output = module(output)
        return output


class FactorizedTaskPolicy(nn.Module):
    """Decode the task language hierarchically from compact planner state."""

    candidate_lookup: Tensor
    _argument_indices: Tensor
    _crop_argument_indices: Tensor
    _item_indices: Tensor
    _none_argument_mask: Tensor
    _operation_indices: Tensor
    _quantity_indices: Tensor
    _safe_argument_indices: Tensor
    _target_token_indices: Tensor
    _target_x_indices: Tensor
    _target_y_indices: Tensor
    _time_indices: Tensor

    def __init__(
        self,
        architecture: TaskTapeArchitecture,
        catalog: TaskCatalog,
    ) -> None:
        """Create a scene-aware typed decoder and its exact catalog bridge."""
        super().__init__()
        if architecture.architecture_version != "factorized-v3":
            raise ValueError("factorized task policy requires its checkpoint version")
        self.architecture = architecture
        self.layout = EconomicStateLayout.create(
            architecture.board_size, architecture.unit_limit
        )
        width = architecture.model_width
        tiles = architecture.board_size * architecture.board_size

        lookup = torch.full(
            (architecture.operation_tokens, architecture.item_tokens + 1, tiles + 1),
            -1,
            dtype=torch.long,
        )
        for index in range(catalog.candidate_count):
            operation = int(catalog.operations[index])
            raw_argument = int(catalog.arguments[index])
            argument = raw_argument if raw_argument >= 0 else NONE_ARGUMENT
            target_x = int(catalog.targets[index, 0])
            target_y = int(catalog.targets[index, 1])
            target = target_y * architecture.board_size + target_x if target_x >= 0 else tiles
            if int(lookup[operation, argument, target]) >= 0:
                raise ValueError("factorized task catalog contains an alias")
            lookup[operation, argument, target] = index
        self.register_buffer("candidate_lookup", lookup)
        argument_indices = torch.arange(architecture.item_tokens + 1)[None]
        target_indices = torch.arange(tiles)
        self.register_buffer(
            "_item_indices", torch.arange(12)[None], persistent=False
        )
        self.register_buffer(
            "_operation_indices",
            torch.arange(architecture.operation_tokens)[None],
            persistent=False,
        )
        self.register_buffer(
            "_argument_indices", argument_indices, persistent=False
        )
        self.register_buffer(
            "_safe_argument_indices",
            argument_indices.clamp_max(11),
            persistent=False,
        )
        self.register_buffer(
            "_crop_argument_indices",
            argument_indices.clamp_max(4),
            persistent=False,
        )
        self.register_buffer(
            "_none_argument_mask",
            argument_indices == NONE_ARGUMENT,
            persistent=False,
        )
        self.register_buffer(
            "_target_x_indices",
            target_indices % architecture.board_size,
            persistent=False,
        )
        self.register_buffer(
            "_target_y_indices",
            target_indices // architecture.board_size,
            persistent=False,
        )
        self.register_buffer(
            "_target_token_indices",
            torch.arange(tiles + 1)[None],
            persistent=False,
        )
        self.register_buffer(
            "_quantity_indices",
            torch.arange(architecture.maximum_quantity)[None],
            persistent=False,
        )
        self.register_buffer(
            "_time_indices",
            torch.arange(architecture.time_tokens)[None],
            persistent=False,
        )

        self.context = _FactorizedSequential(
            nn.LayerNorm(architecture.context_width),
            nn.Linear(architecture.context_width, width),
            nn.SiLU(),
        )
        self.root = _FactorizedSequential(
            nn.Linear(architecture.root_features, width),
            nn.SiLU(),
            nn.Linear(width, width),
        )
        self.prefix = PooledTaskPrefixEncoder(architecture)
        global_width = 14 + 12 + 12 + 5
        self.economic_global = _FactorizedSequential(
            nn.LayerNorm(global_width),
            nn.Linear(global_width, architecture.feedforward_width),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, width),
        )
        self.tile_features = _FactorizedSequential(
            nn.LayerNorm(self.layout.tile_fields + 1),
            nn.Linear(self.layout.tile_fields + 1, architecture.feedforward_width),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, width),
            nn.LayerNorm(width),
        )
        self.state = _FactorizedSequential(
            nn.LayerNorm(6 * width),
            nn.Linear(6 * width, architecture.feedforward_width),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, width),
            nn.LayerNorm(width),
        )

        self.operation = nn.Embedding(architecture.operation_tokens, width)
        self.argument = nn.Embedding(architecture.item_tokens + 1, width)
        self.target_x = nn.Embedding(architecture.board_size + 1, width)
        self.target_y = nn.Embedding(architecture.board_size + 1, width)
        self.operation_cross = nn.MultiheadAttention(
            width, architecture.attention_heads, batch_first=True
        )
        self.operation_norm = nn.LayerNorm(width)
        self.operation_head = nn.Linear(width, 1)

        self.argument_features = _FactorizedSequential(
            nn.LayerNorm(5),
            nn.Linear(5, width),
            nn.SiLU(),
            nn.LayerNorm(width),
        )
        self.argument_head = _FactorizedSequential(
            nn.LayerNorm(width),
            nn.Linear(width, width),
            nn.SiLU(),
            nn.Linear(width, 1),
        )
        self.route_features = _FactorizedSequential(
            nn.LayerNorm(8),
            nn.Linear(8, width),
            nn.SiLU(),
            nn.LayerNorm(width),
        )
        self.target_sentinel = nn.Parameter(torch.empty(width).normal_(std=0.02))
        self.target_query = nn.Linear(width, width, bias=False)
        self.target_bias = nn.Linear(width, 1, bias=False)

        self.task_condition = _FactorizedSequential(
            nn.LayerNorm(4 * width),
            nn.Linear(4 * width, architecture.feedforward_width),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, width),
            nn.LayerNorm(width),
        )
        self.quantity_embedding = nn.Embedding(
            architecture.maximum_quantity + 1, width
        )
        self.time_embedding = nn.Embedding(architecture.time_tokens, width)
        self.quantity_head = nn.Linear(width, architecture.maximum_quantity)
        self.earliest_head = nn.Linear(width, architecture.time_tokens)
        self.deadline_head = nn.Linear(width, architecture.time_tokens)
        self.mode_head = nn.Linear(width, 2)
        self.outcome_head = _FactorizedSequential(
            nn.LayerNorm(width),
            nn.Linear(width, width),
            nn.SiLU(),
            nn.Linear(width, 3),
        )
        self._initialize_actor_heads()

    def _initialize_actor_heads(self) -> None:
        """Begin neutral over exact masks while preserving rich representations."""
        for head in (
            self.mode_head,
            self.operation_head,
            self.target_query,
            self.target_bias,
            self.quantity_head,
            self.earliest_head,
            self.deadline_head,
        ):
            nn.init.zeros_(head.weight)
            if head.bias is not None:
                nn.init.zeros_(head.bias)
        final_argument = cast(nn.Linear, self.argument_head[-1])
        nn.init.zeros_(final_argument.weight)
        nn.init.zeros_(final_argument.bias)

    def _validate_inputs(
        self, inputs: FactorizedTaskDecisionInputs, *, values: bool
    ) -> None:
        architecture = self.architecture
        inputs.validate(
            context_width=architecture.context_width,
            root_features=architecture.root_features,
            prefix_capacity=architecture.history_window,
            task_fields=architecture.task_fields,
            time_tokens=architecture.time_tokens,
            board_size=architecture.board_size,
            unit_limit=architecture.unit_limit,
            economic_state_width=self.layout.width,
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
                raise ValueError("factorized task prefix contains an invalid token")

    def _state_encoding(
        self, inputs: FactorizedTaskDecisionInputs
    ) -> tuple[Tensor, Tensor, Tensor]:
        """Encode shared context plus all 100 compact tile states once."""
        batch = inputs.batch_size
        state_values = inputs.economic_state
        inventory_start = self.layout.inventories + inputs.current_unit * 12
        inventory = state_values.gather(
            1, inventory_start[:, None] + self._item_indices
        )
        global_values = torch.cat(
            (
                state_values[:, :14],
                inventory,
                state_values[:, self.layout.shed : self.layout.shed + 12],
                state_values[:, self.layout.seeds : self.layout.seeds + 5],
            ),
            dim=1,
        )
        economic = cast(Tensor, self.economic_global(_scaled_counts(global_values)))
        raw_tiles = state_values[:, self.layout.tiles :].reshape(
            batch, -1, self.layout.tile_fields
        )
        scaled_target_counts = _scaled_counts(inputs.target_counts)
        conflicts = scaled_target_counts[..., None]
        tile_values = torch.cat((_scaled_counts(raw_tiles), conflicts), dim=2)
        tiles = cast(Tensor, self.tile_features(tile_values))
        tile_mean = tiles.mean(dim=1)
        tile_max = tiles.amax(dim=1)
        prefix = self.prefix(
            inputs.prefix_fields,
            inputs.prefix_mask,
            inputs.prefix_length,
            owner=inputs.current_unit,
        )
        state = cast(
            Tensor,
            self.state(
                torch.cat(
                    (
                        self.context(inputs.context.float()),
                        self.root(inputs.root_features.float()),
                        prefix,
                        economic,
                        tile_mean,
                        tile_max,
                    ),
                    dim=1,
                )
            ),
        )
        return state, tiles, scaled_target_counts

    def _operation_logits(self, state: Tensor, tiles: Tensor) -> Tensor:
        operations = self.operation.weight[None].expand(state.shape[0], -1, -1)
        queries = operations + state[:, None]
        informed, _weights = self.operation_cross(
            queries, tiles, tiles, need_weights=False
        )
        hidden = self.operation_norm(queries + informed)
        return cast(Tensor, self.operation_head(hidden).squeeze(-1))

    def _resource_conflicts(
        self,
        inputs: FactorizedTaskDecisionInputs,
        operation: Tensor,
        argument: Tensor,
    ) -> Tensor:
        """Gather the selected operation-resource reservation count."""
        if operation.shape != argument.shape or operation.shape[0] != inputs.batch_size:
            raise ValueError("factorized resource keys must retain the planner batch")
        resource = torch.full_like(argument, -1)
        resource = torch.where(
            operation == int(TaskOperation.PLANT), argument, resource
        )
        resource = torch.where(
            operation == int(TaskOperation.PICKUP), 5 + argument, resource
        )
        resource = torch.where(
            operation == int(TaskOperation.PLACE),
            17 + argument,
            resource,
        )
        resource = torch.where(
            operation == int(TaskOperation.FERTILIZE),
            17 + 8,
            resource,
        )
        resource = torch.where(
            operation == int(TaskOperation.FEED),
            17,
            resource,
        )
        valid = resource >= 0
        safe = resource.clamp(0, FACTORIZED_RESOURCE_COUNT - 1)
        values = inputs.resource_counts.gather(
            1, safe.reshape(inputs.batch_size, -1)
        ).reshape_as(safe)
        return torch.where(valid, values, torch.zeros_like(values))

    def _argument_tokens(
        self,
        inputs: FactorizedTaskDecisionInputs,
        state: Tensor,
        operation: Tensor,
        operation_embedding: Tensor,
    ) -> tuple[Tensor, Tensor]:
        batch = inputs.batch_size
        arguments = self._argument_indices.expand(batch, -1)
        is_none = self._none_argument_mask.expand(batch, -1)
        if inputs.economic_state.device.type == "cuda" and not torch.is_grad_enabled():
            counts, argument_mask = factorized_argument_inputs(
                inputs, operation, self.layout
            )
            dynamic = torch.cat(
                (_scaled_counts(counts), is_none.float()[..., None]),
                dim=2,
            )
        else:
            state_values = inputs.economic_state
            safe = self._safe_argument_indices.expand(batch, -1)
            inventory_start = self.layout.inventories + inputs.current_unit * 12
            carried = state_values.gather(
                1, inventory_start[:, None] + safe
            )
            shed = state_values.gather(1, self.layout.shed + safe)
            crop_safe = self._crop_argument_indices.expand(batch, -1)
            seeds = state_values.gather(1, self.layout.seeds + crop_safe)
            seeds = torch.where(
                arguments < 5, seeds, torch.zeros_like(seeds)
            )
            operations = operation[:, None].expand_as(arguments)
            conflicts = self._resource_conflicts(
                inputs,
                operations,
                arguments,
            )
            dynamic = torch.stack(
                (
                    _scaled_counts(shed),
                    _scaled_counts(carried),
                    _scaled_counts(seeds),
                    _scaled_counts(conflicts),
                    is_none.float(),
                ),
                dim=2,
            )
            argument_mask = factorized_argument_mask(
                inputs,
                operation,
                arguments=self._argument_indices,
            )
        tokens = cast(
            Tensor,
            self.argument(arguments)
            + self.argument_features(dynamic)
            + operation_embedding[:, None]
            + state[:, None],
        )
        return tokens, argument_mask

    def _argument_logits(
        self,
        inputs: FactorizedTaskDecisionInputs,
        state: Tensor,
        operation: Tensor,
        operation_embedding: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        tokens, argument_mask = self._argument_tokens(
            inputs, state, operation, operation_embedding
        )
        return (
            cast(Tensor, self.argument_head(tokens).squeeze(-1)),
            tokens,
            argument_mask,
        )

    def _currently_legal(
        self,
        inputs: FactorizedTaskDecisionInputs,
        operation: Tensor,
        argument: Tensor,
    ) -> Tensor:
        """Mirror native immediate legality as a soft target feature."""
        batch = inputs.batch_size
        board_size = self.architecture.board_size
        state = inputs.economic_state
        raw = state[:, self.layout.tiles :].reshape(
            batch, -1, self.layout.tile_fields
        )
        kind = raw[..., 0]
        crop = raw[..., 1]
        planted_day = raw[..., 2]
        watered = raw[..., 3]
        yield_units = raw[..., 5]
        structure = raw[..., 6]
        has_animal = raw[..., 7]
        fed = raw[..., 9]
        cared = raw[..., 10]
        fertilizer_available = raw[..., 11]
        target_x = self._target_x_indices
        target_y = self._target_y_indices
        half = board_size // 2
        adjacent = (
            ((target_x == half - 1) | (target_x == half))
            & ((target_y == half - 1) | (target_y == half))
        )[None]
        safe_argument = argument.clamp(0, 11)
        inventory_start = self.layout.inventories + inputs.current_unit * 12
        carried = state.gather(
            1, (inventory_start + safe_argument)[:, None]
        ).squeeze(1)
        fertilizer = state.gather(
            1, (inventory_start + 8)[:, None]
        ).squeeze(1)
        wheat = state.gather(1, inventory_start[:, None]).squeeze(1)
        shed = state.gather(
            1, (self.layout.shed + safe_argument)[:, None]
        ).squeeze(1)
        seed = state.gather(
            1,
            (self.layout.seeds + safe_argument.clamp_max(4))[:, None],
        ).squeeze(1)
        room = (state[:, 5] - state[:, 8]).clamp_min(0)
        animal_place = (
            (argument[:, None] >= 9)
            & (argument[:, None] < 12)
            & (kind == 4)
            & (has_animal == 0)
            & (structure == (argument[:, None] != 9))
        )
        unlocked = kind != 1
        first_yield = torch.where(crop <= 1, 2, torch.where(crop == 2, 8, 10))
        day = state[:, 0, None]
        op = operation[:, None]
        legal = (
            (op == int(TaskOperation.END))
            | (op == int(TaskOperation.WAIT))
            | (op == int(TaskOperation.POSITION))
        ).expand_as(kind).clone()
        legal |= (
            (op == int(TaskOperation.PICKUP))
            & adjacent
            & (argument[:, None] >= 0)
            & (argument[:, None] < 12)
            & (shed[:, None] > 0)
        )
        legal |= (op == int(TaskOperation.DROP)) & adjacent
        legal |= (
            (op == int(TaskOperation.PLACE))
            & (argument[:, None] >= 0)
            & (argument[:, None] < 12)
            & (carried[:, None] > 0)
            & (animal_place | (adjacent & (room[:, None] > 0)))
        )
        legal |= (
            (op == int(TaskOperation.PLANT))
            & unlocked
            & (argument[:, None] >= 0)
            & (argument[:, None] < 5)
            & (kind == 0)
            & (seed[:, None] > 0)
        )
        legal |= (
            (op == int(TaskOperation.WATER))
            & unlocked
            & (kind == 3)
            & (watered == 0)
        )
        legal |= (
            (op == int(TaskOperation.HARVEST))
            & unlocked
            & (yield_units > 0)
            & (
                ((kind == 3) & (day - planted_day >= first_yield))
                | ((kind == 4) & (has_animal != 0))
            )
        )
        legal |= (
            (op == int(TaskOperation.FERTILIZE))
            & unlocked
            & (kind == 3)
            & (fertilizer[:, None] > 0)
        )
        legal |= (
            (op == int(TaskOperation.DIG))
            & unlocked
            & (kind != 0)
            & ~((kind == 4) & (has_animal != 0))
        )
        legal |= (
            ((op == int(TaskOperation.BUILD_COOP)) | (op == int(TaskOperation.BUILD_PASTURE)))
            & unlocked
            & (kind == 0)
        )
        legal |= (
            (op == int(TaskOperation.FEED))
            & unlocked
            & (kind == 4)
            & (has_animal != 0)
            & (fed == 0)
            & (wheat[:, None] > 0)
        )
        legal |= (
            (op == int(TaskOperation.COLLECT_FERTILIZER))
            & unlocked
            & (kind == 4)
            & (has_animal != 0)
            & (fertilizer_available != 0)
        )
        legal |= (
            (op == int(TaskOperation.CARE))
            & unlocked
            & (kind == 4)
            & (has_animal != 0)
            & (cared == 0)
        )
        return legal

    def _target_tokens(
        self,
        inputs: FactorizedTaskDecisionInputs,
        state: Tensor,
        tiles: Tensor,
        operation: Tensor,
        argument: Tensor,
        scaled_target_counts: Tensor,
    ) -> tuple[Tensor, Tensor]:
        batch = inputs.batch_size
        tile_count = tiles.shape[1]
        resource = self._resource_conflicts(inputs, operation, argument)
        if inputs.economic_state.device.type == "cuda" and not torch.is_grad_enabled():
            route, target_mask = factorized_route_inputs(
                inputs,
                operation,
                argument,
                scaled_target_counts,
                _scaled_counts(resource).contiguous(),
                self.layout,
                self.architecture.time_tokens,
            )
        else:
            target_x = self._target_x_indices
            target_y = self._target_y_indices
            distance = (
                (inputs.current_x[:, None] - target_x).abs()
                + (inputs.current_y[:, None] - target_y).abs()
            )
            official = operation >= int(TaskOperation.PICKUP)
            arrival = inputs.available_at[:, None] + distance
            completion = arrival + official[:, None]
            remaining = (inputs.day_end[:, None] - completion).clamp_min(0)
            legality = self._currently_legal(inputs, operation, argument)
            denominator = float(max(1, self.architecture.time_tokens - 1))
            route = torch.stack(
                (
                    distance.float() / denominator,
                    arrival.float() / denominator,
                    completion.float() / denominator,
                    remaining.float() / denominator,
                    legality.float(),
                    scaled_target_counts,
                    _scaled_counts(resource)[:, None].expand(-1, tile_count),
                    official[:, None].float().expand(-1, tile_count),
                ),
                dim=2,
            )
            target_mask = factorized_target_mask(
                inputs,
                operation,
                argument,
                target_x=self._target_x_indices,
                target_y=self._target_y_indices,
            )
        targeted = (
            tiles
            + self.target_x(self._target_x_indices)[None]
            + self.target_y(self._target_y_indices)[None]
            + self.route_features(route)
        )
        sentinel = self.target_sentinel[None, None].expand(batch, 1, -1)
        return torch.cat((targeted, sentinel), dim=1), target_mask

    def _target_logits(
        self,
        inputs: FactorizedTaskDecisionInputs,
        state: Tensor,
        tiles: Tensor,
        operation: Tensor,
        argument: Tensor,
        operation_embedding: Tensor,
        argument_embedding: Tensor,
        scaled_target_counts: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        tokens, target_mask = self._target_tokens(
            inputs,
            state,
            tiles,
            operation,
            argument,
            scaled_target_counts,
        )
        query = (
            self.target_query(
                state + operation_embedding + argument_embedding
            )
            / math.sqrt(self.architecture.model_width)
            + self.target_bias.weight
        )
        logits = torch.bmm(tokens, query[:, :, None]).squeeze(-1)
        return logits, tokens, target_mask

    def _conditioned(
        self,
        state: Tensor,
        operation: Tensor,
        argument: Tensor,
        operation_embedding: Tensor,
        argument_embedding: Tensor,
        target_tokens: Tensor,
        target: Tensor,
    ) -> Tensor:
        target_index = target.clamp(
            0, target_tokens.shape[1] - 1
        )[:, None, None]
        selected_target = target_tokens.gather(
            1,
            target_index.expand(-1, 1, target_tokens.shape[2]),
        ).squeeze(1)
        return cast(
            Tensor,
            self.task_condition(
                torch.cat(
                    (
                        state,
                        operation_embedding,
                        argument_embedding,
                        selected_target,
                    ),
                    dim=1,
                )
            ),
        )

    def _catalog_tokens(
        self, catalog: TaskCatalog, candidate: Tensor
    ) -> tuple[Tensor, Tensor, Tensor]:
        safe = candidate.clamp(0, catalog.candidate_count - 1)
        operation = catalog.operations[safe]
        raw_argument = catalog.arguments[safe]
        argument = torch.where(
            raw_argument >= 0,
            raw_argument,
            torch.full_like(raw_argument, NONE_ARGUMENT),
        )
        coordinates = catalog.targets[safe]
        target = torch.where(
            coordinates[:, 0] >= 0,
            coordinates[:, 1] * self.architecture.board_size + coordinates[:, 0],
            torch.full_like(coordinates[:, 0], self.architecture.board_size**2),
        )
        return operation, argument, target

    def _candidate(self, operation: Tensor, argument: Tensor, target: Tensor) -> Tensor:
        candidate = self.candidate_lookup[operation, argument, target]
        if candidate.device.type == "cpu" and bool(torch.any(candidate < 0)):
            raise RuntimeError("typed task selection is absent from the native catalog")
        return candidate

    def rollout(
        self,
        inputs: FactorizedTaskDecisionInputs,
        catalog: TaskCatalog,
        *,
        sample: bool,
        generator: torch.Generator | None,
        uniforms: Tensor | None = None,
        validate_inputs: bool,
        compute_entropy: bool,
    ) -> TaskPolicyOutput:
        """Sample one task without constructing the 1,890-candidate surface."""
        if validate_inputs:
            self._validate_inputs(inputs, values=True)
        state, tiles, scaled_target_counts = self._state_encoding(inputs)
        if uniforms is not None and (
            uniforms.shape
            != (FACTORIZED_TASK_FACTOR_COUNT, inputs.batch_size)
            or uniforms.dtype != torch.float32
            or uniforms.device != state.device
            or not sample
            or compute_entropy
            or torch.is_grad_enabled()
        ):
            raise ValueError("factorized task uniforms require inference sampling")
        fused_uniforms = uniforms if uniforms is not None else (
            torch.rand(
                (FACTORIZED_TASK_FACTOR_COUNT, inputs.batch_size),
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

        def uniform(index: int) -> Tensor | None:
            return None if fused_uniforms is None else fused_uniforms[index]

        fused_inference = state.device.type == "cuda" and not torch.is_grad_enabled()
        mode, mode_log, mode_entropy = _choose_statistics(
            self.mode_head(state),
            inputs.mode_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=uniform(0),
        )
        rewrite = mode == int(SuffixMode.REWRITE)
        operation_mask = (
            factorized_operation_inputs(
                inputs, self.architecture.operation_tokens
            )
            if fused_inference
            else factorized_operation_mask(inputs)
        )
        operation_mask = torch.where(
            rewrite[:, None],
            operation_mask,
            self._operation_indices == int(TaskOperation.END),
        )
        operation, operation_log, operation_entropy = _choose_statistics(
            self._operation_logits(state, tiles),
            operation_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=uniform(1),
        )
        operation_embedding = self.operation(operation)
        argument_logits, _argument_tokens, argument_mask = self._argument_logits(
            inputs, state, operation, operation_embedding
        )
        argument_mask = torch.where(
            rewrite[:, None],
            argument_mask,
            self._none_argument_mask,
        )
        argument, argument_log, argument_entropy = _choose_statistics(
            argument_logits,
            argument_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=uniform(2),
        )
        argument_embedding = self.argument(argument)
        target_logits, target_tokens, target_mask = self._target_logits(
            inputs,
            state,
            tiles,
            operation,
            argument,
            operation_embedding,
            argument_embedding,
            scaled_target_counts,
        )
        target_mask = torch.where(
            rewrite[:, None],
            target_mask,
            self._target_token_indices == self.architecture.board_size**2,
        )
        target, target_log, target_entropy = _choose_statistics(
            target_logits,
            target_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=uniform(3),
        )
        candidate = self._candidate(operation, argument, target)
        candidate = torch.where(rewrite, candidate, torch.zeros_like(candidate))
        if fused_inference:
            (
                quantity_mask,
                earliest_mask,
                arrival,
                active_task,
                requires_quantity,
            ) = factorized_temporal_inputs(
                inputs,
                operation,
                target,
                rewrite,
                self.architecture.maximum_quantity,
                self.architecture.time_tokens,
            )
        else:
            is_end = operation == int(TaskOperation.END)
            active_task = rewrite & ~is_end
            requires_quantity = (
                (operation == int(TaskOperation.PICKUP))
                | (operation == int(TaskOperation.PLACE))
            ) & rewrite
            quantity_mask = requires_quantity[:, None] | (
                self._quantity_indices == 0
            )
            arrival = factorized_arrival(inputs, operation, target)
            operation_turns = (
                operation >= int(TaskOperation.PICKUP)
            ).long()[:, None]
            times = self._time_indices
            earliest_mask = (
                active_task[:, None]
                & (times >= inputs.available_at[:, None])
                & (times <= inputs.day_end[:, None])
            )
            earliest_mask &= (
                (operation[:, None] != int(TaskOperation.WAIT))
                | (times > inputs.available_at[:, None])
            )
            earliest_mask &= (
                torch.maximum(arrival[:, None], times) + operation_turns
                <= inputs.day_end[:, None]
            )
            earliest_mask |= ~active_task[:, None] & (times == 0)
        conditioned = self._conditioned(
            state,
            operation,
            argument,
            operation_embedding,
            argument_embedding,
            target_tokens,
            target,
        )
        quantity_index, quantity_log, quantity_entropy = _choose_statistics(
            self.quantity_head(conditioned),
            quantity_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=uniform(4),
        )
        quantity = torch.where(
            requires_quantity,
            quantity_index + 1,
            torch.zeros_like(quantity_index),
        )
        quantity_hidden = conditioned + self.quantity_embedding(quantity)
        earliest, earliest_log, earliest_entropy = _choose_statistics(
            self.earliest_head(quantity_hidden),
            earliest_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=uniform(5),
        )
        if fused_inference:
            deadline_mask = factorized_deadline_mask(
                inputs,
                operation,
                earliest,
                arrival,
                active_task,
                self.architecture.time_tokens,
            )
        else:
            deadline_mask = (
                active_task[:, None]
                & (
                    self._time_indices
                    >= torch.maximum(arrival[:, None], earliest[:, None])
                    + operation_turns
                )
                & (self._time_indices <= inputs.day_end[:, None])
            )
            deadline_mask |= ~active_task[:, None] & (
                self._time_indices == 0
            )
        deadline_hidden = quantity_hidden + self.time_embedding(earliest)
        deadline, deadline_log, deadline_entropy = _choose_statistics(
            self.deadline_head(deadline_hidden),
            deadline_mask,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
            uniform=uniform(6),
        )
        actions = TaskActions(mode, candidate, quantity, earliest, deadline)
        factors = torch.zeros(
            (inputs.batch_size, FACTORIZED_TASK_FACTOR_COUNT),
            dtype=torch.bool,
            device=state.device,
        )
        factors[:, 0] = inputs.mode_mask.bool().sum(dim=1) > 1
        factors[:, 1] = rewrite & (operation_mask.sum(dim=1) > 1)
        factors[:, 2] = rewrite & (argument_mask.sum(dim=1) > 1)
        factors[:, 3] = rewrite & (target_mask.sum(dim=1) > 1)
        factors[:, 4] = requires_quantity & (self.architecture.maximum_quantity > 1)
        factors[:, 5] = active_task & (earliest_mask.sum(dim=1) > 1)
        factors[:, 6] = active_task & (deadline_mask.sum(dim=1) > 1)
        masks = FactorizedTaskMasks(
            mode=inputs.mode_mask.bool(),
            operation=operation_mask,
            argument=argument_mask,
            target=target_mask,
            quantity=quantity_mask,
            earliest=earliest_mask,
            deadline=deadline_mask,
            factors=factors,
        )
        factor_log = torch.stack(
            (
                mode_log,
                operation_log,
                argument_log,
                target_log,
                quantity_log,
                earliest_log,
                deadline_log,
            ),
            dim=1,
        ).masked_fill(~factors, 0.0)
        factor_entropy = (
            torch.stack(
                (
                    mode_entropy,
                    operation_entropy,
                    argument_entropy,
                    target_entropy,
                    quantity_entropy,
                    earliest_entropy,
                    deadline_entropy,
                ),
                dim=1,
            ).masked_fill(~factors, 0.0)
            if compute_entropy
            else torch.zeros_like(factor_log)
        )
        outcome_logits = self.outcome_head(state)
        return TaskPolicyOutput(
            actions=actions,
            masks=masks,
            joint_log_probability=factor_log.sum(dim=1),
            factor_log_probability=factor_log,
            entropy=factor_entropy.sum(dim=1),
            factor_entropy=factor_entropy,
            outcome_logits=outcome_logits,
            value=_outcome_values(outcome_logits),
        )

    def evaluate_actions(
        self,
        inputs: FactorizedTaskDecisionInputs,
        catalog: TaskCatalog,
        actions: TaskActions,
        masks: FactorizedTaskMasks,
        *,
        validate: bool,
        validate_inputs: bool,
    ) -> TaskPolicyOutput:
        """Evaluate teacher-forced typed factors from compact state."""
        if validate_inputs:
            self._validate_inputs(inputs, values=True)
        actions.validate(inputs.batch_size)
        if validate:
            masks.validate(
                inputs.batch_size,
                self.architecture.operation_tokens,
                self.architecture.item_tokens + 1,
                self.architecture.board_size**2 + 1,
                self.architecture.maximum_quantity,
                self.architecture.time_tokens,
            )
            expected = factorized_conditional_masks(
                inputs,
                catalog,
                actions,
                maximum_quantity=self.architecture.maximum_quantity,
                time_tokens=self.architecture.time_tokens,
            )
            for name in masks.__dataclass_fields__:
                if not torch.equal(
                    getattr(masks, name).bool(), getattr(expected, name).bool()
                ):
                    raise ValueError(
                        f"stored factorized task {name} mask differs from compact state"
                    )
        state, tiles, scaled_target_counts = self._state_encoding(inputs)
        operation, argument, target = self._catalog_tokens(
            catalog, actions.candidate
        )
        operation_embedding = self.operation(operation)
        argument_embedding = self.argument(argument)
        argument_logits, _argument_tokens, _argument_mask = self._argument_logits(
            inputs, state, operation, operation_embedding
        )
        target_logits, target_tokens, _target_mask = self._target_logits(
            inputs,
            state,
            tiles,
            operation,
            argument,
            operation_embedding,
            argument_embedding,
            scaled_target_counts,
        )
        conditioned = self._conditioned(
            state,
            operation,
            argument,
            operation_embedding,
            argument_embedding,
            target_tokens,
            target,
        )
        quantity_hidden = conditioned + self.quantity_embedding(
            actions.quantity.clamp(0, self.architecture.maximum_quantity)
        )
        logits = (
            self.mode_head(state),
            self._operation_logits(state, tiles),
            argument_logits,
            target_logits,
            self.quantity_head(conditioned),
            self.earliest_head(quantity_hidden),
            self.deadline_head(
                quantity_hidden
                + self.time_embedding(
                    actions.earliest.clamp(0, self.architecture.time_tokens - 1)
                )
            ),
        )
        selections = (
            actions.mode,
            operation,
            argument,
            target,
            (actions.quantity - 1).clamp_min(0),
            actions.earliest,
            actions.deadline,
        )
        factor_masks = (
            masks.mode,
            masks.operation,
            masks.argument,
            masks.target,
            masks.quantity,
            masks.earliest,
            masks.deadline,
        )
        logs: list[Tensor] = []
        entropies: list[Tensor] = []
        for index, (factor_logits, factor_mask, selection) in enumerate(
            zip(logits, factor_masks, selections, strict=True)
        ):
            log_probability, entropy = _masked_statistics(
                factor_logits,
                factor_mask,
                selection,
                masks.factors[:, index].bool(),
                validate=validate,
            )
            logs.append(log_probability)
            entropies.append(entropy)
        factor_log = torch.stack(logs, dim=1)
        factor_entropy = torch.stack(entropies, dim=1)
        outcome_logits = self.outcome_head(state)
        return TaskPolicyOutput(
            actions=actions,
            masks=masks,
            joint_log_probability=factor_log.sum(dim=1),
            factor_log_probability=factor_log,
            entropy=factor_entropy.sum(dim=1),
            factor_entropy=factor_entropy,
            outcome_logits=outcome_logits,
            value=_outcome_values(outcome_logits),
        )


__all__ = ["FactorizedTaskPolicy"]
