"""Transformer factor queries for conditional portfolio decoding."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.transformer import DecoderBlock, RMSNorm

if TYPE_CHECKING:
    from kagg_revue.policy.plans.schema import StructuredPlanArchitecture


class StructuredPlanFactorDecoder(nn.Module):
    """Produce one state-conditioned hidden vector per action factor."""

    def __init__(self, architecture: StructuredPlanArchitecture) -> None:
        """Create causal factor queries and deep state cross-attention."""
        super().__init__()
        width = architecture.model_width
        self.queries = nn.Parameter(
            torch.empty(architecture.factor_width, width).normal_(std=0.02)
        )
        self.blocks = nn.ModuleList(
            DecoderBlock(
                width,
                architecture.attention_heads,
                architecture.feedforward_width,
                architecture.factor_width,
                strategy=bool(architecture.strategy_tokens),
            )
            for _ in range(architecture.action_layers)
        )
        self.output_norm = RMSNorm(width)

    def forward(
        self,
        memory: Tensor,
        memory_mask: Tensor,
        strategy: Tensor | None,
    ) -> Tensor:
        """Decode fixed causal factor identities against current state memory."""
        batch = memory.shape[0]
        hidden = self.queries[None].expand(batch, -1, -1)
        valid = torch.ones(hidden.shape[:2], dtype=torch.bool, device=hidden.device)
        strategy_mask = (
            torch.ones(strategy.shape[:2], dtype=torch.bool, device=strategy.device)
            if strategy is not None
            else None
        )
        for block in self.blocks:
            hidden = block(
                hidden,
                valid,
                memory,
                memory_mask,
                strategy,
                strategy_mask,
            )
        return cast(Tensor, self.output_norm(hidden))


__all__ = ["StructuredPlanFactorDecoder"]
