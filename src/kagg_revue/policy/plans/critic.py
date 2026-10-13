"""Detached-representation terminal W/D/L critic for portfolio PPO."""

from __future__ import annotations

from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.transformer import CrossBlock, RMSNorm


class StructuredPlanOutcomeHead(nn.Module):
    """Retain the old PPO outcome-head capacity over plan representations."""

    def __init__(
        self,
        width: int,
        global_features: int,
        attention_heads: int,
        economic_features: int,
        strategy_tokens: int,
    ) -> None:
        """Create critic-owned adapters matching the old outcome head."""
        super().__init__()
        self.network = nn.Sequential(
            RMSNorm(width),
            nn.Linear(width, width, bias=False),
            nn.SiLU(),
            nn.Linear(width, 3),
        )
        self.global_encoder = nn.Sequential(
            nn.Linear(global_features, width),
            nn.SiLU(),
            nn.Linear(width, width, bias=False),
            RMSNorm(width),
        )
        self.scene_query = nn.Parameter(torch.empty(width).normal_(std=0.02))
        self.scene_cross = CrossBlock(width, attention_heads)
        self.context_network = nn.Sequential(
            RMSNorm(3 * width),
            nn.Linear(3 * width, width, bias=False),
            nn.SiLU(),
            nn.Linear(width, 3),
        )
        context_output = cast(nn.Linear, self.context_network[-1])
        nn.init.zeros_(context_output.weight)
        nn.init.zeros_(context_output.bias)
        self.economic_network = nn.Sequential(
            nn.Linear(economic_features, width),
            nn.SiLU(),
            nn.Linear(width, 3),
        )
        economic_output = cast(nn.Linear, self.economic_network[-1])
        nn.init.zeros_(economic_output.weight)
        nn.init.zeros_(economic_output.bias)
        self.strategy_query: nn.Parameter | None
        self.strategy_cross: CrossBlock | None
        self.strategy_output: nn.Linear | None
        if strategy_tokens:
            self.strategy_query = nn.Parameter(torch.empty(width).normal_(std=0.02))
            self.strategy_cross = CrossBlock(width, attention_heads)
            self.strategy_output = nn.Linear(width, 3)
            nn.init.zeros_(self.strategy_output.weight)
            nn.init.zeros_(self.strategy_output.bias)
        else:
            self.register_parameter("strategy_query", None)
            self.strategy_cross = None
            self.strategy_output = None

    def forward(
        self,
        history: Tensor,
        global_features: Tensor,
        scene_memory: Tensor,
        scene_memory_mask: Tensor,
        economic_features: Tensor,
        strategy: Tensor | None,
    ) -> Tensor:
        """Predict terminal loss/tie/win logits from actor-visible context."""
        width = history.shape[-1]
        queries = self.scene_query.view(1, 1, width).expand(history.shape[0], 1, width)
        scene_context = self.scene_cross(
            queries,
            scene_memory,
            scene_memory_mask,
        )[:, 0]
        global_context = self.global_encoder(global_features)
        context = torch.cat((history, global_context, scene_context), dim=-1)
        result = self.network(history) + self.context_network(context)
        result = result + self.economic_network(economic_features)
        if self.strategy_cross is not None and self.strategy_output is not None:
            if self.strategy_query is None or strategy is None:
                raise ValueError("structured-plan critic strategy state is absent")
            strategy_mask = torch.ones(
                strategy.shape[:2],
                dtype=torch.bool,
                device=strategy.device,
            )
            strategy_query = self.strategy_query.view(1, 1, width).expand(
                history.shape[0],
                1,
                width,
            )
            strategy_context = self.strategy_cross(
                strategy_query,
                strategy,
                strategy_mask,
            )[:, 0]
            result = result + self.strategy_output(strategy_context)
        return cast(Tensor, result)


__all__ = ["StructuredPlanOutcomeHead"]
