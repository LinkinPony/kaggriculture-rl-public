"""Causal unit context: each unit sees what earlier units chose in the same turn."""

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.grounded.normalization import LayerNorm


class UnitContext(nn.Module):
    """Attend from units to the committed actions (claims) of earlier unit slots.

    A learned sink claim keeps attention defined for the first unit. The output projection
    starts at zero, so a parallel-unit checkpoint expands without changing its policy.
    """

    def __init__(self, width: int, heads: int) -> None:
        """Allocate one claim MLP and one multi-head cross-attention block."""
        super().__init__()
        self.heads = heads
        self.claim = nn.Sequential(
            LayerNorm(width), nn.Linear(width, 2 * width), nn.GELU(), nn.Linear(2 * width, width)
        )
        self.query_norm = LayerNorm(width)
        self.claim_norm = LayerNorm(width)
        self.query = nn.Linear(width, width)
        self.key_value = nn.Linear(width, 2 * width)
        self.sink = nn.Parameter(torch.zeros(width))
        self.output = nn.Linear(width, width)
        nn.init.zeros_(self.output.weight)
        nn.init.zeros_(self.output.bias)

    def claims(self, summary: Tensor) -> Tensor:
        """Encode unit summaries that already include their chosen tile and operation."""
        encoded: Tensor = summary + self.claim(summary)
        return encoded

    def forward(self, hidden: Tensor, claims: Tensor, visible: Tensor) -> Tensor:
        """Return residuals for (n, k, w) units given (n, m, w) claims and (n, k, m) masks."""
        n, k, width = hidden.shape
        size = width // self.heads
        sink = self.sink.to(claims.dtype).expand(n, 1, width)
        memory = self.claim_norm(torch.cat((sink, claims), 1))
        visible = F.pad(visible, (1, 0), value=True)
        query = self.query(self.query_norm(hidden)).view(n, k, self.heads, size).transpose(1, 2)
        key, value = self.key_value(memory).view(n, -1, 2, self.heads, size).permute(2, 0, 3, 1, 4)
        attended = F.scaled_dot_product_attention(
            query, key.to(query.dtype), value.to(query.dtype), attn_mask=visible[:, None]
        )
        residual: Tensor = self.output(attended.transpose(1, 2).reshape(n, k, width))
        return residual
