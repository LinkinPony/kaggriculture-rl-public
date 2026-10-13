"""Typed entity encoders for atomic-effect pointer policies."""

from __future__ import annotations

from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.effects.attention import pack_entities
from kagg_revue.policy.effects.data import EffectTensorState
from kagg_revue.policy.effects.schema import EffectArchitecture
from kagg_revue.policy.transformer import EncoderBlock, RMSNorm


def _scaled(values: Tensor) -> Tensor:
    floats = values.float()
    return torch.sign(floats) * torch.log1p(floats.abs()).clamp_max(32.0) / 16.0


class EffectEmbeddings(nn.Module):
    """Categorical identities shared by state and candidate encoders."""

    def __init__(self, architecture: EffectArchitecture) -> None:
        """Create embeddings directly from checkpoint-bound enum counts."""
        super().__init__()
        width = architecture.model_width
        self.architecture = architecture
        self.request = nn.Embedding(architecture.request_count, width)
        self.target = nn.Embedding(architecture.tile_count + 1, width)
        self.item = nn.Embedding(architecture.item_count + 1, width)
        self.unit = nn.Embedding(architecture.unit_limit + 1, width)
        self.resource = nn.Embedding(architecture.resource_count, width)
        self.phase = nn.Embedding(architecture.phase_count, width)
        self.entity_type = nn.Embedding(5, width)
        self.position = nn.Embedding(architecture.maximum_state_entities, width)

    @staticmethod
    def safe(values: Tensor, count: int) -> Tensor:
        """Clamp corrupt padded values away from embedding memory."""
        return values.long().clamp(min=0, max=count - 1)

    def request_id(self, values: Tensor) -> Tensor:
        """Return bounded request identifiers."""
        return self.safe(values, self.architecture.request_count)

    def target_id(self, values: Tensor) -> Tensor:
        """Map native -1 to padding zero and tiles to one-based IDs."""
        return (values.long() + 1).clamp(min=0, max=self.architecture.tile_count)

    def item_id(self, values: Tensor) -> Tensor:
        """Consume native one-based item IDs with zero as absence."""
        return values.long().clamp(min=0, max=self.architecture.item_count)

    def unit_id(self, values: Tensor) -> Tensor:
        """Consume native one-based unit IDs with zero as absence."""
        return values.long().clamp(min=0, max=self.architecture.unit_limit)


class EffectCandidateEncoder(nn.Module):
    """Encode complete work requests and market-order tuples in parallel."""

    def __init__(
        self,
        architecture: EffectArchitecture,
        typed: EffectEmbeddings,
    ) -> None:
        """Create typed, numerical, rule-fact, and target residuals."""
        super().__init__()
        self.architecture = architecture
        self.typed = typed
        width = architecture.model_width
        self.numeric = nn.Linear(5, width, bias=False)
        self.features = nn.Sequential(
            nn.Linear(architecture.candidate_feature_count, width),
            nn.SiLU(),
            nn.Linear(width, width, bias=False),
        )
        self.tile = nn.Sequential(
            RMSNorm(architecture.context_width),
            nn.Linear(architecture.context_width, width, bias=False),
        )
        self.output = nn.Sequential(
            RMSNorm(width),
            nn.Linear(width, architecture.feedforward_width, bias=False),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, width, bias=False),
            RMSNorm(width),
        )

    def project_tiles(self, tile_context: Tensor) -> Tensor:
        """Project turn-static tile context once for all candidate buckets."""
        return cast(Tensor, self.tile(tile_context))

    def forward_projected(
        self,
        fields: Tensor,
        features: Tensor,
        projected_tiles: Tensor,
    ) -> Tensor:
        """Encode candidates using an already projected tile context."""
        if fields.shape[-1] != self.architecture.candidate_field_count:
            raise ValueError("effect candidate integer width differs from its ABI")
        if features.shape != (*fields.shape[:-1], self.architecture.candidate_feature_count):
            raise ValueError("effect candidate rules features do not align")
        typed = self.typed
        target_ids = typed.target_id(fields[..., 1])
        gathered_tiles = projected_tiles.gather(
            1,
            (target_ids - 1).clamp_min(0)[..., None].expand(-1, -1, projected_tiles.shape[-1]),
        )
        gathered_tiles = gathered_tiles * (target_ids > 0)[..., None]
        return self._encode(fields, features, gathered_tiles, target_ids)

    def forward_flattened(
        self,
        fields: Tensor,
        features: Tensor,
        projected_tiles: Tensor,
        rows: Tensor,
    ) -> Tensor:
        """Encode only retained candidates, preserving their owning turn tiles."""
        target_ids = self.typed.target_id(fields[..., 1])
        indices = rows * projected_tiles.shape[1] + (target_ids - 1).clamp_min(0)
        tiles = projected_tiles.flatten(0, 1).index_select(0, indices)
        return self._encode(fields, features, tiles * (target_ids > 0)[..., None], target_ids)

    def _encode(
        self,
        fields: Tensor,
        features: Tensor,
        gathered_tiles: Tensor,
        target_ids: Tensor,
    ) -> Tensor:
        """Apply the shared typed and numerical candidate network."""
        typed = self.typed
        hidden = (
            typed.request(typed.request_id(fields[..., 0]))
            + typed.target(target_ids)
            + typed.item(typed.item_id(fields[..., 2]))
            + typed.unit(typed.unit_id(fields[..., 5]))
            + typed.resource(typed.safe(fields[..., 6], self.architecture.resource_count))
            + typed.item(typed.item_id(fields[..., 7]))
            + typed.position(typed.safe(fields[..., 10], self.architecture.maximum_state_entities))
            + self.numeric(
                torch.stack(
                    tuple(_scaled(fields[..., index]) for index in (3, 4, 8, 9, 10)),
                    dim=-1,
                )
            )
            + self.features(features.float())
            + gathered_tiles
        )
        return cast(Tensor, self.output(hidden))

    def forward(
        self,
        fields: Tensor,
        features: Tensor,
        tile_context: Tensor,
    ) -> Tensor:
        """Encode a padded candidate surface without scoring it."""
        return self.forward_projected(
            fields,
            features,
            self.project_tiles(tile_context),
        )


def _candidate_forward_projected(
    encoder: EffectCandidateEncoder,
    fields: Tensor,
    features: Tensor,
    projected_tiles: Tensor,
) -> Tensor:
    """Expose the candidate-only region as one compilable tensor program."""
    return encoder.forward_projected(fields, features, projected_tiles)


compiled_candidate_forward = torch.compile(
    _candidate_forward_projected,
    dynamic=True,
    fullgraph=True,
)


def _candidate_forward_flattened(
    encoder: EffectCandidateEncoder,
    fields: Tensor,
    features: Tensor,
    projected_tiles: Tensor,
    rows: Tensor,
) -> Tensor:
    """Expose the compact candidate region to the same compiler."""
    return encoder.forward_flattened(fields, features, projected_tiles, rows)


compiled_flat_candidate_forward = torch.compile(
    _candidate_forward_flattened,
    dynamic=True,
    fullgraph=True,
)


class EffectStateEncoder(nn.Module):
    """Fuse recurrent turn context with jobs and semantic action entities."""

    def __init__(
        self,
        architecture: EffectArchitecture,
        typed: EffectEmbeddings,
    ) -> None:
        """Create a bounded bidirectional entity Transformer."""
        super().__init__()
        self.architecture = architecture
        self.typed = typed
        width = architecture.model_width
        self.context = nn.Linear(architecture.context_width, width, bias=False)
        self.strategy = nn.Linear(architecture.context_width, width, bias=False)
        self.root_numeric = nn.Linear(1, width, bias=False)
        self.job_numeric = nn.Linear(4, width, bias=False)
        self.action_numeric = nn.Linear(2, width, bias=False)
        self.blocks = nn.ModuleList(
            EncoderBlock(
                width,
                architecture.attention_heads,
                architecture.feedforward_width,
                architecture.maximum_state_entities,
            )
            for _ in range(architecture.state_layers)
        )
        self.output = RMSNorm(width)

    def _jobs(self, fields: Tensor) -> Tensor:
        typed = self.typed
        positions = torch.arange(fields.shape[1], device=fields.device)[None]
        return cast(
            Tensor,
            typed.entity_type.weight[1]
            + typed.position(positions)
            + typed.request(typed.request_id(fields[..., 1]))
            + typed.target(typed.target_id(fields[..., 2]))
            + typed.item(typed.item_id(fields[..., 3]))
            + typed.unit(typed.unit_id(fields[..., 4]))
            + self.job_numeric(
                torch.stack(
                    tuple(_scaled(fields[..., index]) for index in (0, 5, 6, 7)),
                    dim=-1,
                )
            ),
        )

    def _actions(self, fields: Tensor, entity_type: int) -> Tensor:
        typed = self.typed
        positions = torch.arange(fields.shape[1], device=fields.device)[None]
        return cast(
            Tensor,
            typed.entity_type.weight[entity_type]
            + typed.position(positions)
            + typed.request(typed.request_id(fields[..., 0]))
            + typed.target(typed.target_id(fields[..., 1]))
            + typed.item(typed.item_id(fields[..., 2]))
            + typed.unit(typed.unit_id(fields[..., 5]))
            + self.action_numeric(
                torch.stack((_scaled(fields[..., 3]), _scaled(fields[..., 4])), dim=-1)
            ),
        )

    def _positions(self, state: EffectTensorState) -> Tensor | None:
        """Return padding-invariant positions for versioned entity groups."""
        if self.architecture.state_position_encoding == "packed_relative_v1":
            return None
        device = state.phase.device
        unit_limit = self.architecture.unit_limit
        market_limit = self.architecture.maximum_market_orders

        def group(width: int, start: int) -> Tensor:
            return torch.arange(width, device=device) + start

        return torch.cat(
            (
                torch.zeros(1, dtype=torch.long, device=device),
                group(state.jobs.shape[1], 1),
                group(state.work_prefix.shape[1], 1 + unit_limit),
                group(state.market_prefix.shape[1], 1 + 2 * unit_limit),
                group(
                    state.previous_action.shape[1],
                    1 + 2 * unit_limit + market_limit,
                ),
            )
        )

    def forward(
        self,
        context: Tensor,
        strategy: Tensor | None,
        state: EffectTensorState,
        *,
        entity_capacity: int | None = None,
    ) -> Tensor:
        """Return the root token after exact masked entity attention."""
        root = (
            self.context(context)
            + self.typed.entity_type.weight[0]
            + self.typed.phase(self.typed.safe(state.phase, self.architecture.phase_count))
            + self.root_numeric(_scaled(state.work_limit)[..., None])
        )
        if strategy is not None:
            if strategy.shape != context.shape:
                raise ValueError("effect strategy summary differs from turn context")
            root = root + self.strategy(strategy)
        entities = torch.cat(
            (
                root[:, None],
                self._jobs(state.jobs),
                self._actions(state.work_prefix, 2),
                self._actions(state.market_prefix, 3),
                self._actions(state.previous_action, 4),
            ),
            dim=1,
        )
        valid = torch.cat(
            (
                torch.ones((state.batch_size, 1), dtype=torch.bool, device=context.device),
                state.job_mask,
                state.work_mask,
                state.market_mask,
                state.previous_mask,
            ),
            dim=1,
        )
        if entities.shape[1] > self.architecture.maximum_state_entities:
            raise ValueError("effect semantic entity count exceeds the architecture")
        hidden = entities
        positions = self._positions(state)
        if entity_capacity is not None:
            hidden, valid, positions = pack_entities(hidden, valid, positions, entity_capacity)
        for block in self.blocks[:-1]:
            hidden = cast(EncoderBlock, block)(
                hidden,
                valid,
                causal=False,
                positions=positions,
            )
        hidden = cast(EncoderBlock, self.blocks[-1]).forward_root(
            hidden,
            valid,
            positions=positions,
        )
        return cast(Tensor, self.output(hidden[:, 0]))


__all__ = ["EffectCandidateEncoder", "EffectEmbeddings", "EffectStateEncoder"]
