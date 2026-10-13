"""Compress a visible scene into summaries and fuse causal memory back into entities."""

from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.contracts import NetworkShape
from kagg_revue.policy.memory.blocks import Gate
from kagg_revue.policy.memory.temporal import InferenceState, MemoryState, TemporalMemory


class SceneMemory(nn.Module):
    """Retain entity detail while augmenting it with learned temporal context."""

    def __init__(self, width: int, shape: NetworkShape) -> None:
        """Allocate learned summary queries and entity-specific memory readout."""
        super().__init__()
        hidden = shape.memory_width
        self.heads = shape.heads
        self.width = hidden
        self.summaries = shape.memory_tokens
        self.summary_queries = nn.Parameter(torch.randn(shape.memory_tokens, hidden) * hidden**-0.5)
        self.pool_norm = nn.LayerNorm(width)
        self.pool_keys = nn.Linear(width, hidden)
        self.pool_values = nn.Linear(width, hidden)
        self.temporal = TemporalMemory(
            hidden, shape.memory_layers, shape.heads, shape.memory_turns, shape.memory_tokens
        )
        self.query_norm = nn.LayerNorm(width)
        self.query = nn.Linear(width, hidden)
        self.key_value = nn.Linear(hidden, 2 * hidden)
        self.output = nn.Linear(hidden, width)
        self.gate = Gate(width)
        self.norm = nn.LayerNorm(width)

    def forward(
        self, entities: Tensor, valid: Tensor, state: MemoryState, steps: Tensor
    ) -> tuple[Tensor, MemoryState]:
        """Accept time-major scene tensors with a shared contiguous turn clock."""
        turns, batch, count, width = entities.shape
        flat = entities.flatten(0, 1)
        summaries = self._pool(flat, valid.flatten(0, 1))
        summaries = summaries.reshape(turns, batch, self.summaries, self.width).transpose(0, 1)
        context, next_state = self.temporal(summaries, state, steps)
        context = context.transpose(0, 1).reshape(turns * batch, self.summaries, self.width)
        return self._fuse(flat, context).reshape(turns, batch, count, width), next_state

    def step(
        self, entities: Tensor, valid: Tensor, state: InferenceState, step: Tensor
    ) -> tuple[Tensor, InferenceState]:
        """Use projected temporal caches only inside one fixed-weight episode."""
        context, next_state = self.temporal.step(self._pool(entities, valid), state, step)
        return self._fuse(entities, context), next_state

    def _pool(self, flat: Tensor, valid: Tensor) -> Tensor:
        normalized = self.pool_norm(flat)
        keys = self.pool_keys(normalized)
        scores = (self.summary_queries @ keys.transpose(1, 2)) * self.width**-0.5
        scores = scores.masked_fill(~valid[:, None], -float("inf"))
        return cast(Tensor, scores.softmax(-1) @ self.pool_values(normalized))

    def _fuse(self, flat: Tensor, context: Tensor) -> Tensor:
        count = flat.shape[1]
        query = self.query(self.query_norm(flat)).reshape(
            -1, count, self.heads, self.width // self.heads
        )
        kv = self.key_value(context).reshape(
            -1, self.summaries, 2, self.heads, self.width // self.heads
        )
        key, value = kv.permute(2, 0, 3, 1, 4).unbind(0)
        mixed = F.scaled_dot_product_attention(query.transpose(1, 2), key, value)
        update = self.output(mixed.transpose(1, 2).reshape(-1, count, self.width))
        return cast(Tensor, self.norm(self.gate(flat, F.relu(update))))
