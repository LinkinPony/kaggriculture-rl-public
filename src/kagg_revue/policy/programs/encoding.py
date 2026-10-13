"""Shared state, option, tile, and action-prefix encoders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.programs.grammar import (
    ProgramActions,
    ProgramActionSequence,
    ProgramDecisionInputs,
    ProgramPrefixState,
    ProgramSequenceInputs,
)
from kagg_revue.policy.programs.schema import ProgramArchitecture


def scaled_counts(values: Tensor) -> Tensor:
    """Compress unbounded signed counts without hard value buckets."""
    floats = values.float()
    return torch.sign(floats) * torch.log1p(floats.abs()).clamp_max(32.0) / 16.0


@dataclass(frozen=True)
class ProgramPreparedContext:
    """Turn-static program features reused by every microdecision."""

    context: Tensor
    target_keys: Tensor


class OptionEncoder(nn.Module):
    """Encode the compiler-owned persistent option record."""

    def __init__(self, architecture: ProgramArchitecture) -> None:
        """Create typed embeddings for the stable native option fields."""
        super().__init__()
        width = architecture.model_width
        self.architecture = architecture
        self.task = nn.Embedding(architecture.task_count + 1, width)
        self.target = nn.Embedding(architecture.tile_count + 1, width)
        self.argument = nn.Embedding(architecture.argument_count + 1, width)
        self.quantity_mode = nn.Embedding(architecture.quantity_mode_count + 1, width)
        self.phase = nn.Embedding(7, width)
        self.x = nn.Embedding(architecture.board_size + 1, width)
        self.y = nn.Embedding(architecture.board_size + 1, width)
        self.numeric = nn.Linear(5, width, bias=False)
        self.norm = nn.LayerNorm(width)

    def forward(self, fields: Tensor) -> Tensor:
        """Return one option token for each decision row."""
        if fields.ndim < 2 or fields.shape[-1] != 12:
            raise ValueError("conditional-program option fields must have width 12")
        numeric = torch.stack(
            (
                fields[..., 0].float(),
                scaled_counts(fields[..., 5]),
                scaled_counts(fields[..., 7]),
                fields[..., 8].float(),
                scaled_counts(fields[..., 11]),
            ),
            dim=-1,
        )
        hidden = (
            self.task(fields[..., 1].clamp(0, self.architecture.task_count))
            + self.target(fields[..., 2].clamp(0, self.architecture.tile_count))
            + self.argument(fields[..., 3].clamp(0, self.architecture.argument_count))
            + self.quantity_mode(
                fields[..., 4].clamp(0, self.architecture.quantity_mode_count)
            )
            + self.phase(fields[..., 6].clamp(0, 6))
            + self.x(fields[..., 9].clamp(0, self.architecture.board_size))
            + self.y(fields[..., 10].clamp(0, self.architecture.board_size))
            + self.numeric(numeric)
        )
        return cast(Tensor, self.norm(hidden))


class ProgramStateEncoder(nn.Module):
    """Fuse the causal turn, shadow state, and policy-owned action prefix."""

    def __init__(self, architecture: ProgramArchitecture) -> None:
        """Create state/token projections and the recurrent prefix cell."""
        super().__init__()
        width = architecture.model_width
        self.architecture = architecture
        self.context = nn.Sequential(
            nn.LayerNorm(architecture.context_width),
            nn.Linear(architecture.context_width, width),
            nn.SiLU(),
        )
        self.root = nn.Sequential(
            nn.Linear(architecture.root_feature_count, width),
            nn.SiLU(),
            nn.Linear(width, width),
        )
        self.option = OptionEncoder(architecture)
        self.phase = nn.Embedding(2, width)
        self.unit = nn.Embedding(architecture.unit_limit + 1, width)
        self.market_slot = nn.Embedding(architecture.maximum_market_orders + 1, width)
        self.x = nn.Embedding(architecture.board_size, width)
        self.y = nn.Embedding(architecture.board_size, width)
        self.scalars = nn.Linear(2, width, bias=False)
        self.state = nn.Sequential(
            nn.LayerNorm(6 * width),
            nn.Linear(6 * width, architecture.feedforward_width),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, width),
            nn.LayerNorm(width),
        )
        self.tile = nn.Sequential(
            nn.LayerNorm(architecture.context_width),
            nn.Linear(architecture.context_width, width),
            nn.LayerNorm(width),
        )
        self.reservation = nn.Linear(1, width, bias=False)
        self.prefix_initial = nn.Sequential(
            nn.LayerNorm(architecture.context_width),
            nn.Linear(architecture.context_width, width),
            nn.Tanh(),
        )
        self.prefix_cell = nn.GRUCell(width, width)
        self.action_phase = nn.Embedding(2, width)
        self.action_control = nn.Embedding(architecture.control_count, width)
        self.action_task = nn.Embedding(architecture.task_count, width)
        self.action_target = nn.Embedding(architecture.tile_count + 1, width)
        self.action_argument = nn.Embedding(architecture.argument_count, width)
        self.action_direction = nn.Embedding(architecture.direction_count, width)
        self.action_raw = nn.Embedding(architecture.raw_operation_count, width)
        self.action_quantity_mode = nn.Embedding(architecture.quantity_mode_count, width)
        self.action_market = nn.Embedding(architecture.market_order_count, width)
        self.action_exact = nn.Linear(1, width, bias=False)
        self.action_norm = nn.LayerNorm(width)

    def initial_prefix(self, context: Tensor) -> ProgramPrefixState:
        """Initialize one causal action-prefix state for a new turn."""
        return ProgramPrefixState(cast(Tensor, self.prefix_initial(context)))

    def encode_context(self, context: Tensor) -> Tensor:
        """Project one turn-static causal context token."""
        return cast(Tensor, self.context(context))

    def encode_tiles(self, tile_tokens: Tensor) -> Tensor:
        """Project turn-static lossless board tokens."""
        return cast(Tensor, self.tile(tile_tokens))

    def encode_reservations(self, reservations: Tensor) -> Tensor:
        """Project the decision-varying target reservation counts."""
        scaled = scaled_counts(reservations)[:, :, None]
        return cast(Tensor, self.reservation(scaled))

    def decision_state(
        self,
        inputs: ProgramDecisionInputs,
        prefix: ProgramPrefixState,
        context: Tensor,
    ) -> Tensor:
        """Fuse dynamic compiler state with one prepared context token."""
        width = self.architecture.model_width
        if prefix.hidden.shape != (inputs.batch_size, width):
            raise ValueError("conditional-program prefix state has the wrong shape")
        if context.shape != (inputs.batch_size, width):
            raise ValueError("conditional-program prepared context has the wrong shape")
        return self._decision_state(
            inputs.root_features,
            inputs.option_features,
            inputs.phase,
            inputs.unit_index,
            inputs.market_slot,
            inputs.unit_count,
            inputs.current_x,
            inputs.current_y,
            inputs.forced,
            prefix.hidden,
            context,
        )

    def sequence_states(
        self,
        inputs: ProgramSequenceInputs,
        prefix_hidden: Tensor,
        context: Tensor,
    ) -> Tensor:
        """Encode every teacher-forced decision in one dense launch surface."""
        expected = (
            inputs.batch_size,
            inputs.decision_capacity,
            self.architecture.model_width,
        )
        if prefix_hidden.shape != expected or context.shape != (
            inputs.batch_size,
            self.architecture.model_width,
        ):
            raise ValueError("conditional-program sequence state has the wrong shape")
        return self._decision_state(
            inputs.root_features,
            inputs.option_features,
            inputs.phase,
            inputs.unit_index,
            inputs.market_slot,
            inputs.unit_count,
            inputs.current_x,
            inputs.current_y,
            inputs.forced,
            prefix_hidden,
            context[:, None].expand_as(prefix_hidden),
        )

    def _decision_state(
        self,
        root_features: Tensor,
        option_features: Tensor,
        phase: Tensor,
        unit_index: Tensor,
        market_slot: Tensor,
        unit_count: Tensor,
        current_x: Tensor,
        current_y: Tensor,
        forced: Tensor,
        prefix_hidden: Tensor,
        context: Tensor,
    ) -> Tensor:
        """Fuse dynamic compiler fields across arbitrary leading dimensions."""
        continuous = torch.stack(
            (
                forced.float(),
                unit_count.float() / self.architecture.unit_limit,
            ),
            dim=-1,
        )
        components = (
            context,
            self.root(root_features.float()),
            self.option(option_features),
            self.phase(phase.clamp(0, 1)),
            self.unit((unit_index + 1).clamp(0, self.architecture.unit_limit))
            + self.market_slot(
                (market_slot + 1).clamp(0, self.architecture.maximum_market_orders)
            )
            + self.x(current_x.clamp(0, self.architecture.board_size - 1))
            + self.y(current_y.clamp(0, self.architecture.board_size - 1))
            + self.scalars(continuous),
            prefix_hidden,
        )
        return cast(Tensor, self.state(torch.cat(components, dim=-1)))

    def forward(
        self, inputs: ProgramDecisionInputs, prefix: ProgramPrefixState
    ) -> tuple[Tensor, Tensor]:
        """Encode one decision state and all lossless own-board targets."""
        context = self.encode_context(inputs.context)
        state = self.decision_state(inputs, prefix, context)
        tiles = self.encode_tiles(inputs.tile_tokens) + self.encode_reservations(
            inputs.target_reservations
        )
        return state, tiles

    def _action_tokens(
        self,
        actions: ProgramActions | ProgramActionSequence,
        phase: Tensor,
    ) -> Tensor:
        """Embed teacher-forced actions with arbitrary leading dimensions."""
        architecture = self.architecture
        exact = scaled_counts(actions.exact_quantity)[..., None]
        token = (
            self.action_phase(phase.clamp(0, 1))
            + self.action_control(actions.control.clamp(0, architecture.control_count - 1))
            + self.action_task(actions.task.clamp(0, architecture.task_count - 1))
            + self.action_target((actions.target + 1).clamp(0, architecture.tile_count))
            + self.action_argument(actions.argument.clamp(0, architecture.argument_count - 1))
            + self.action_direction(actions.direction.clamp(0, architecture.direction_count - 1))
            + self.action_raw(actions.raw_operation.clamp(0, architecture.raw_operation_count - 1))
            + self.action_quantity_mode(
                actions.quantity_mode.clamp(0, architecture.quantity_mode_count - 1)
            )
            + self.action_market(actions.market_order.clamp(0, architecture.market_order_count - 1))
            + self.action_exact(exact)
        )
        return cast(Tensor, self.action_norm(token))

    def sequence_prefixes(
        self,
        prefix: ProgramPrefixState,
        actions: ProgramActionSequence,
        phase: Tensor,
    ) -> Tensor:
        """Evaluate the teacher-forced prefix recurrence as one fused GRU."""
        tokens = self._action_tokens(actions, phase)
        if tokens.ndim != 3 or prefix.hidden.shape != (
            tokens.shape[0],
            tokens.shape[2],
        ):
            raise ValueError("conditional-program prefix sequence has the wrong shape")
        outputs, _last = torch._VF.gru(
            tokens,
            prefix.hidden[None],
            [
                self.prefix_cell.weight_ih,
                self.prefix_cell.weight_hh,
                self.prefix_cell.bias_ih,
                self.prefix_cell.bias_hh,
            ],
            True,
            1,
            0.0,
            self.training,
            False,
            True,
        )
        return torch.cat((prefix.hidden[:, None], outputs[:, :-1]), dim=1)

    def update_prefix(
        self,
        prefix: ProgramPrefixState,
        actions: ProgramActions,
        phase: Tensor,
        active: Tensor | None = None,
    ) -> ProgramPrefixState:
        """Append one canonicalized structured action to the recurrent prefix."""
        token = self._action_tokens(actions, phase)
        updated = cast(Tensor, self.prefix_cell(token, prefix.hidden))
        if active is not None:
            updated = torch.where(active[:, None], updated, prefix.hidden)
        return ProgramPrefixState(updated)


__all__ = [
    "ProgramPreparedContext",
    "ProgramStateEncoder",
    "scaled_counts",
]
