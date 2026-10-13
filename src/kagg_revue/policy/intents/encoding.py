"""Typed encoders for complete intent-ledger augmented states."""

from __future__ import annotations

from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.intents.data import IntentTensorState
from kagg_revue.policy.intents.schema import IntentArchitecture
from kagg_revue.policy.transformer import RMSNorm


def _scaled(values: Tensor) -> Tensor:
    floats = values.float()
    return torch.sign(floats) * torch.log1p(floats.abs()).clamp_max(32.0) / 16.0


def _masked_mean(values: Tensor, mask: Tensor) -> Tensor:
    if values.shape[:-1] != mask.shape:
        raise ValueError("intent entity mask does not align with encoded values")
    if values.shape[-2] == 0:
        return values.new_zeros((*values.shape[:-2], values.shape[-1]))
    weights = mask.to(values.dtype)[..., None]
    return (values * weights).sum(dim=-2) / weights.sum(dim=-2).clamp_min(1.0)


class TypedEmbeddings(nn.Module):
    """Shared categorical identities used by ledger and candidates."""

    def __init__(self, architecture: IntentArchitecture) -> None:
        """Create distinct embeddings for every semantic field."""
        super().__init__()
        width = architecture.model_width
        self.architecture = architecture
        self.choice = nn.Embedding(architecture.choice_count, width)
        self.target = nn.Embedding(architecture.tile_count + 1, width)
        self.item = nn.Embedding(architecture.item_count + 2, width)
        self.unit = nn.Embedding(architecture.unit_limit + 1, width)
        self.shortfall_item = nn.Embedding(architecture.item_count + 2, width)
        self.asset = nn.Embedding(architecture.asset_kind_count, width)
        self.maintenance = nn.Embedding(architecture.maintenance_count, width)
        self.product = nn.Embedding(architecture.product_collection_count, width)
        self.fertilizer = nn.Embedding(architecture.fertilizer_collection_count, width)
        self.priority = nn.Embedding(architecture.priority_count + 1, width)
        self.work = nn.Embedding(architecture.work_kind_count, width)
        self.role = nn.Embedding(architecture.position_role_count, width)
        self.directive = nn.Embedding(architecture.directive_operation_count, width)
        self.market = nn.Embedding(architecture.market_order_count, width)
        self.phase = nn.Embedding(architecture.phase_count, width)
        self.status = nn.Embedding(architecture.status_count, width)
        self.reason = nn.Embedding(architecture.block_reason_count, width)
        self.binary = nn.Embedding(2, width)
        self.bound = nn.Embedding(2, width)

    @staticmethod
    def safe(values: Tensor, count: int) -> Tensor:
        """Clamp an enum tensor to its checkpoint-bound range."""
        return values.long().clamp(0, count - 1)

    def target_id(self, values: Tensor) -> Tensor:
        """Reserve index zero for native negative target sentinels."""
        return (values.long() + 1).clamp(0, self.architecture.tile_count)

    def item_id(self, values: Tensor) -> Tensor:
        """Reserve index zero for native negative item sentinels."""
        return (values.long() + 1).clamp(0, self.architecture.item_count + 1)

    def priority_id(self, values: Tensor) -> Tensor:
        """Reserve index zero for absent work priorities."""
        return (values.long() + 1).clamp(0, self.architecture.priority_count)

    def unit_id(self, values: Tensor) -> Tensor:
        """Map one-based native unit identities, preserving zero as absent."""
        return values.long().clamp(0, self.architecture.unit_limit)


class IntentCandidateEncoder(nn.Module):
    """Encode complete canonical successor identities without aliases."""

    def __init__(self, architecture: IntentArchitecture, typed: TypedEmbeddings) -> None:
        """Create typed, numeric, and native-feature candidate projections."""
        super().__init__()
        self.architecture = architecture
        self.typed = typed
        width = architecture.model_width
        self.numeric = nn.Linear(1, width, bias=False)
        self.features = nn.Sequential(
            nn.Linear(architecture.candidate_feature_count, width),
            nn.SiLU(),
            nn.Linear(width, width, bias=False),
        )
        self.norm = RMSNorm(width)
        self.feedforward = nn.Sequential(
            nn.Linear(width, architecture.feedforward_width, bias=False),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, width, bias=False),
        )

    def forward(
        self,
        fields: Tensor,
        features: Tensor,
        tile_context: Tensor,
    ) -> Tensor:
        """Return one key token for every padded candidate."""
        if fields.shape[-1] != self.architecture.candidate_field_count:
            raise ValueError("intent candidate integer width differs from the ABI")
        typed = self.typed
        target = fields[..., 1].long()
        has_target = target >= 0
        gathered_tile = tile_context.gather(
            1,
            target.clamp(0, self.architecture.tile_count - 1)[..., None].expand(
                -1, -1, tile_context.shape[-1]
            ),
        )
        hidden = (
            typed.choice(typed.safe(fields[..., 0], self.architecture.choice_count))
            + typed.target(typed.target_id(fields[..., 1]))
            + typed.item(typed.item_id(fields[..., 2]))
            + typed.maintenance(typed.safe(fields[..., 3], self.architecture.maintenance_count))
            + typed.product(typed.safe(fields[..., 4], self.architecture.product_collection_count))
            + typed.fertilizer(
                typed.safe(fields[..., 5], self.architecture.fertilizer_collection_count)
            )
            + typed.priority(typed.priority_id(fields[..., 6]))
            + typed.unit(typed.unit_id(fields[..., 8]))
            + typed.directive(
                typed.safe(fields[..., 9], self.architecture.directive_operation_count)
            )
            + self.numeric(_scaled(fields[..., 7])[..., None])
            + self.features(features.float())
            + gathered_tile * has_target[..., None]
        )
        hidden = self.norm(hidden)
        return cast(Tensor, hidden + self.feedforward(hidden))


class IntentStateEncoder(nn.Module):
    """Encode the absolute ledger, status, work, and market prefix."""

    def __init__(self, architecture: IntentArchitecture, typed: TypedEmbeddings) -> None:
        """Create tile-aware encoders for every augmented-state component."""
        super().__init__()
        self.architecture = architecture
        self.typed = typed
        width = architecture.model_width
        self.context = nn.Sequential(
            RMSNorm(architecture.context_width),
            nn.Linear(architecture.context_width, width, bias=False),
            nn.SiLU(),
        )
        self.tile = nn.Embedding(architecture.tile_count, width)
        self.market_position = nn.Embedding(architecture.maximum_market_orders, width)
        self.numeric = nn.Linear(2, width, bias=False)
        self.entity_norm = RMSNorm(width)
        self.output = nn.Sequential(
            RMSNorm(6 * width),
            nn.Linear(6 * width, architecture.feedforward_width, bias=False),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, width, bias=False),
            RMSNorm(width),
        )

    def encode_ledger_entities(
        self,
        fields: Tensor,
        status: Tensor,
        work_priorities: Tensor,
        tile_context: Tensor,
        targets: Tensor,
    ) -> Tensor:
        """Encode individual tile-ledger rows before their mean reduction."""
        typed = self.typed
        work_kinds = torch.arange(work_priorities.shape[-1], device=fields.device)
        work_priority = self.entity_norm(
            typed.work(work_kinds)[None, None] + typed.priority(typed.priority_id(work_priorities))
        ).mean(dim=2)
        hidden = (
            self.tile(targets)
            + tile_context
            + typed.binary(typed.safe(fields[..., 0], 2))
            + typed.asset(typed.safe(fields[..., 1], self.architecture.asset_kind_count))
            + typed.item(typed.item_id(fields[..., 2]))
            + typed.maintenance(typed.safe(fields[..., 3], self.architecture.maintenance_count))
            + typed.product(typed.safe(fields[..., 4], self.architecture.product_collection_count))
            + typed.fertilizer(
                typed.safe(fields[..., 5], self.architecture.fertilizer_collection_count)
            )
            + typed.priority(typed.priority_id(fields[..., 6]))
            + typed.bound(typed.safe(fields[..., 7], 2))
            + typed.status(typed.safe(status[..., 0], self.architecture.status_count))
            + typed.reason(typed.safe(status[..., 1], self.architecture.block_reason_count))
            + typed.shortfall_item(typed.item_id(status[..., 2]))
            + work_priority
            + self.numeric(
                torch.stack(
                    (
                        _scaled(status[..., 3]),
                        (work_priorities >= 0).float().mean(dim=-1),
                    ),
                    dim=-1,
                )
            )
        )
        return cast(Tensor, self.entity_norm(hidden))

    def _ledger(self, state: IntentTensorState, tile_context: Tensor) -> Tensor:
        targets = torch.arange(self.architecture.tile_count, device=state.ledger.device)[
            None
        ].expand(state.batch_size, -1)
        return self.encode_ledger_entities(
            state.ledger,
            state.status,
            state.work_priorities,
            tile_context,
            targets,
        ).mean(dim=1)

    def encode_work_entities(self, fields: Tensor) -> Tensor:
        """Encode work rows before their masked commutative reduction."""
        if fields.shape[-1] != self.architecture.work_field_count:
            raise ValueError("intent work integer width differs from the ABI")
        typed = self.typed
        hidden = (
            typed.work(typed.safe(fields[..., 0], self.architecture.work_kind_count))
            + typed.target(typed.target_id(fields[..., 1]))
            + typed.item(typed.item_id(fields[..., 2]))
            + typed.priority(typed.priority_id(fields[..., 4]))
            + typed.status(typed.safe(fields[..., 5], self.architecture.status_count))
            + typed.reason(typed.safe(fields[..., 6], self.architecture.block_reason_count))
            + typed.unit(typed.unit_id(fields[..., 8]))
            + self.numeric(torch.stack((_scaled(fields[..., 3]), _scaled(fields[..., 7])), dim=-1))
        )
        return cast(Tensor, self.entity_norm(hidden))

    def summarize_work(self, fields: Tensor, mask: Tensor) -> Tensor:
        """Return the exact masked work mean used by the state encoder."""
        if fields.shape[-2] == 0:
            return self.tile.weight.new_zeros((*fields.shape[:-2], self.architecture.model_width))
        return _masked_mean(self.encode_work_entities(fields), mask)

    def _work(self, state: IntentTensorState) -> Tensor:
        return self.summarize_work(state.work_orders, state.work_mask)

    def encode_position_entities(self, fields: Tensor) -> Tensor:
        """Encode position rows before their fixed-width mean reduction."""
        typed = self.typed
        hidden = (
            typed.binary(typed.safe(fields[..., 0], 2))
            + typed.target(typed.target_id(fields[..., 1]))
            + typed.priority(typed.priority_id(fields[..., 2]))
            + typed.role(typed.safe(fields[..., 3], self.architecture.position_role_count))
        )
        return cast(Tensor, self.entity_norm(hidden))

    def _positions(self, state: IntentTensorState) -> Tensor:
        return self.encode_position_entities(state.positions).mean(dim=1)

    def encode_market_entities(self, fields: Tensor, positions: Tensor) -> Tensor:
        """Encode market rows at their explicit prefix positions."""
        typed = self.typed
        hidden = (
            typed.market(typed.safe(fields[..., 0], self.architecture.market_order_count))
            + typed.item(typed.item_id(fields[..., 1]))
            + self.market_position(
                positions.clamp_max(self.architecture.maximum_market_orders - 1)
            )
            + self.numeric(
                torch.stack(
                    (
                        _scaled(fields[..., 2]),
                        torch.zeros_like(fields[..., 2], dtype=torch.float32),
                    ),
                    dim=-1,
                )
            )
        )
        return cast(Tensor, self.entity_norm(hidden))

    def _market(self, state: IntentTensorState) -> Tensor:
        fields = state.market_prefix
        if fields.shape[1] == 0:
            return self.tile.weight.new_zeros((fields.shape[0], self.architecture.model_width))
        positions = torch.arange(fields.shape[1], device=fields.device)[None]
        return _masked_mean(
            self.encode_market_entities(fields, positions),
            state.market_mask,
        )

    def forward(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: IntentTensorState,
    ) -> Tensor:
        """Fuse one turn-static context with the complete dynamic prefix."""
        return self.forward_with_work_summary(
            context,
            tile_context,
            state,
            self._work(state),
        )

    def forward_with_work_summary(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: IntentTensorState,
        work_summary: Tensor,
    ) -> Tensor:
        """Fuse dynamic state with a pre-reduced work embedding."""
        return self.forward_prepared(
            cast(Tensor, self.context(context)),
            tile_context,
            state,
            work_summary,
        )

    def forward_prepared(
        self,
        encoded_context: Tensor,
        tile_context: Tensor,
        state: IntentTensorState,
        work_summary: Tensor,
    ) -> Tensor:
        """Fuse state after turn-static context projections are cached."""
        expected = (state.batch_size, self.architecture.model_width)
        if work_summary.shape != expected or encoded_context.shape != expected:
            raise ValueError("intent work summary differs from the policy architecture")
        return self.forward_summarized(
            encoded_context,
            state.phase,
            self._ledger(state, tile_context),
            work_summary,
            self._positions(state),
            self._market(state),
        )

    def forward_summarized(
        self,
        encoded_context: Tensor,
        phase_ids: Tensor,
        ledger_summary: Tensor,
        work_summary: Tensor,
        position_summary: Tensor,
        market_summary: Tensor,
    ) -> Tensor:
        """Fuse exact cached reductions for a device-resident transaction."""
        phase = self.typed.phase(self.typed.safe(phase_ids, self.architecture.phase_count))
        components = (
            encoded_context,
            ledger_summary,
            work_summary,
            position_summary,
            market_summary,
            phase,
        )
        return cast(Tensor, self.output(torch.cat(components, dim=-1)))


__all__ = ["IntentCandidateEncoder", "IntentStateEncoder", "TypedEmbeddings"]
