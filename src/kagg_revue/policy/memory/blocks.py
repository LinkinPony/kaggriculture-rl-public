"""Pre-normalized GRU-gated residual transformations."""

from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F


class Gate(nn.Module):
    """Fuse a skip stream and candidate using the GTrXL GRU equations."""

    def __init__(self, width: int) -> None:
        """Start the update gate biased toward retaining the skip stream."""
        super().__init__()
        self.input = nn.Linear(width, 3 * width, bias=False)
        self.reset_update = nn.Linear(width, 2 * width, bias=False)
        self.candidate = nn.Linear(width, width, bias=False)
        self.bias = nn.Parameter(torch.full((width,), 2.0))

    def forward(self, skip: Tensor, update: Tensor) -> Tensor:
        """Apply reset, update and candidate transforms independently at each token."""
        yr, yz, yh = self.input(update).chunk(3, -1)
        xr, xz = self.reset_update(skip).chunk(2, -1)
        reset = torch.sigmoid(yr + xr)
        mix = torch.sigmoid(yz + xz - self.bias)
        candidate = torch.tanh(yh + self.candidate(reset * skip))
        return (1 - mix) * skip + mix * candidate


class EntityBlock(nn.Module):
    """Attend over visible entities with two independent GRU residual gates."""

    def __init__(self, width: int, heads: int, expansion: int) -> None:
        """Allocate pre-normalized attention and feedforward branches."""
        super().__init__()
        self.heads = heads
        self.norm = nn.LayerNorm(width)
        self.qkv = nn.Linear(width, 3 * width)
        self.output = nn.Linear(width, width)
        self.attention_gate = Gate(width)
        self.feedforward = nn.Sequential(
            nn.LayerNorm(width),
            nn.Linear(width, expansion * width),
            nn.GELU(),
            nn.Linear(expansion * width, width),
        )
        self.feedforward_gate = Gate(width)

    def forward(self, values: Tensor, valid: Tensor) -> Tensor:
        """Mask absent entities without imposing a temporal order on the scene."""
        batch, tokens, width = values.shape
        qkv = self.qkv(self.norm(values)).view(batch, tokens, 3, self.heads, width // self.heads)
        query, key, content = qkv.permute(2, 0, 3, 1, 4).unbind(0)
        mixed = F.scaled_dot_product_attention(query, key, content, valid[:, None, None, :])
        update = self.output(mixed.transpose(1, 2).reshape(batch, tokens, width))
        hidden = self.attention_gate(values, F.relu(update))
        return cast(Tensor, self.feedforward_gate(hidden, F.relu(self.feedforward(hidden))))
