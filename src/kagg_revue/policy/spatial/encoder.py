"""Separate spatial, unit, product and shop tokens with actor-safe public history."""

from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.attention import masked_attention


class Block(nn.Module):
    """Pre-normalized entity attention with a padding mask and residual MLP."""

    def __init__(self, width: int, heads: int, expansion: int) -> None:
        """Construct attention and feedforward parameters at the requested width."""
        super().__init__()
        self.heads = heads
        self.norm = nn.LayerNorm(width)
        self.qkv = nn.Linear(width, 3 * width)
        self.output = nn.Linear(width, width)
        self.feedforward = nn.Sequential(
            nn.LayerNorm(width),
            nn.Linear(width, expansion * width),
            nn.GELU(),
            nn.Linear(expansion * width, width),
        )

    def forward(self, value: Tensor, valid: Tensor) -> Tensor:
        """Attend only to observed entities, including always-present board tokens."""
        batch, tokens, width = value.shape
        qkv = self.qkv(self.norm(value)).view(batch, tokens, 3, self.heads, width // self.heads)
        query, key, content = qkv.permute(2, 0, 3, 1, 4).unbind(0)
        # H200: native SDPA wins for 64-wide inference heads, while explicit
        # 64x64 Flex tiles slightly improve large forward/backward batches.
        tiled = query.shape[-1] != 64 or (
            torch.is_grad_enabled() and batch >= 4096 and tokens == 286
        )
        if query.is_cuda and torch.compiler.is_compiling() and batch >= 80 and tiled:
            mixed = masked_attention(query, key, content, valid)
        else:
            mixed = F.scaled_dot_product_attention(query, key, content, valid[:, None, None, :])
        value = value + self.output(mixed.transpose(1, 2).reshape(batch, tokens, width))
        return cast(Tensor, value + self.feedforward(value))


class EntityEncoder(nn.Module):
    """Encode both farms independently and retain each unit as an attention token."""

    def __init__(self, layout: ContractLayout, width: int, depth: int) -> None:
        """Bind the immutable native feature layout and entity roles."""
        super().__init__()
        self.layout = layout
        base = layout.observation
        channels = base.board_features // (2 * layout.cells)
        self.board = nn.Linear(channels, width)
        self.units = nn.Linear(base.unit_features, width)
        self.global_state = nn.Sequential(
            nn.Linear(base.global_features + base.history_features, width),
            nn.GELU(),
            nn.Linear(width, width),
        )
        self.products = nn.Linear(base.product_features, width)
        self.shops = nn.Linear(8, width)
        self.coordinate = nn.Linear(2, width, bias=False)
        self.kind = nn.Parameter(torch.zeros(7, width))
        self.unit_position = nn.Parameter(torch.zeros(base.units, width))
        self.product_position = nn.Parameter(torch.zeros(9, width))
        self.shop_position = nn.Parameter(torch.zeros(8, width))
        y, x = torch.meshgrid(
            torch.linspace(-1, 1, layout.board_size),
            torch.linspace(-1, 1, layout.board_size),
            indexing="ij",
        )
        self.register_buffer("coordinates", torch.stack((x, y), -1).reshape(layout.cells, 2))
        self.blocks = nn.ModuleList(
            Block(width, layout.network.heads, layout.network.expansion) for _ in range(depth)
        )
        self.norm = nn.LayerNorm(width)

    def forward(self, observations: Tensor) -> Tensor:
        """Preserve both sides and encode causal public changes as global context."""
        base = self.layout.observation
        n = observations.shape[0]
        unit_start = base.board_features
        global_start = unit_start + base.units * base.unit_features
        extra_start = global_start + base.global_features
        product_start = extra_start + base.units * base.unit_features
        history_start = product_start + 9 * base.product_features
        board = observations[:, :unit_start].reshape(n, 2, -1, self.layout.cells).transpose(2, 3)
        own_units = observations[:, unit_start:global_start].reshape(n, base.units, -1)
        other_units = observations[:, extra_start:product_start].reshape(n, base.units, -1)
        global_state = observations[:, global_start:extra_start]
        products = observations[:, product_start:history_start].reshape(n, 9, -1)
        shops = global_state[:, -64:].reshape(n, 8, 8)
        history = observations[:, history_start : history_start + base.history_features]
        coordinate = self.coordinate(self.coordinates)
        tokens = [
            self.global_state(torch.cat((global_state, history), -1).float())[:, None]
            + self.kind[0],
            self.board(board[:, 0].float()) + coordinate + self.kind[1],
            self.board(board[:, 1].float()) + coordinate + self.kind[2],
        ]
        for side, units in enumerate((own_units, other_units)):
            tokens.append(
                self.units(units.float())
                + self.unit_position
                + self.kind[3 + side]
                + self.coordinate(units[..., 2:4].float() * 2 - 1)
            )
        tokens.extend(
            (
                self.products(products.float()) + self.product_position + self.kind[5],
                self.shops(shops.float()) + self.shop_position + self.kind[6],
            )
        )
        valid = torch.cat(
            (
                torch.ones(
                    (n, 1 + 2 * self.layout.cells), dtype=torch.bool, device=observations.device
                ),
                own_units[..., 0] > 0,
                other_units[..., 0] > 0,
                torch.ones((n, 9), dtype=torch.bool, device=observations.device),
                shops.sum(-1) > 0,
            ),
            -1,
        )
        value = torch.cat(tokens, 1)
        for block in self.blocks:
            value = block(value, valid)
        return cast(Tensor, self.norm(value))
