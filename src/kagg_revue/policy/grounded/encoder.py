"""Spatial and causal production context for the deeper grounded architecture."""

from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.native.derived import VERSION as DERIVED_VERSION
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.supplement import Supplement
from kagg_revue.policy.spatial.encoder import Block, EntityEncoder


class ContextEncoder(EntityEncoder):
    """Mix local farm neighborhoods and four public history scales with entities."""

    def __init__(self, layout: ContractLayout, width: int, depth: int) -> None:
        """Bind v2 native context while retaining the established token ordering."""
        base = layout.observation
        agronomy = base.version in {"grounded-production-context-v4", DERIVED_VERSION}
        if base.version not in {
            "grounded-production-context-v2",
            "grounded-production-context-v4",
            DERIVED_VERSION,
        }:
            raise ValueError("context encoder requires native production context v2 or v4")
        dimensions = (
            base.agronomy_board_features,
            base.agronomy_product_features,
            base.agronomy_global_features,
            base.agronomy_unit_features,
        )
        if dimensions != ((36, 49, 22, 16) if agronomy else (0, 0, 0, 0)):
            raise ValueError("agronomy dimensions differ from the versioned contract")
        expected = (
            2 * layout.cells * (8 + base.agronomy_board_features)
            + 9 * (8 + base.agronomy_product_features)
            + 16
            + 4 * 28
            + base.agronomy_global_features
            + 2 * base.units * base.agronomy_unit_features
        )
        if layout.observation.context_features != expected:
            raise ValueError("native context dimensions differ from the encoder contract")
        super().__init__(layout, width, depth)
        base = layout.observation
        # With agronomy, each unit also reads the rich board row of the tile it stands on.
        self.tile_context = (8 + base.agronomy_board_features) if agronomy else 0
        self.board = nn.Linear(
            base.board_features // (2 * layout.cells) + 8 + base.agronomy_board_features, width
        )
        self.units = nn.Linear(
            base.unit_features + 46 + base.agronomy_unit_features + self.tile_context, width
        )
        self.products = nn.Linear(base.product_features + 8 + base.agronomy_product_features, width)
        self.global_state = nn.Sequential(
            nn.Linear(
                base.global_features + base.history_features + 16 + base.agronomy_global_features,
                width,
            ),
            nn.GELU(),
            nn.Linear(width, width),
        )
        self.kind = nn.Parameter(torch.zeros(8, width))
        self.local = nn.Sequential(
            nn.Conv2d(width, width, 3, padding=1, groups=width),
            nn.GELU(),
            nn.Conv2d(width, width, 1),
        )
        self.history = nn.Linear(28, width)
        self.history_position = nn.Parameter(torch.zeros(4, width))
        self.supplement = Supplement(layout, width) if base.version == DERIVED_VERSION else None
        if layout.network.gated:
            from kagg_revue.policy.memory.blocks import EntityBlock

            self.blocks = nn.ModuleList(
                EntityBlock(width, layout.network.heads, layout.network.expansion)
                for _ in range(depth)
            )
            return
        # Keep the initial residual variance bounded as attention depth grows.
        with torch.no_grad():
            for block in self.blocks:
                assert isinstance(block, Block)
                block.output.weight.mul_((2 * depth) ** -0.5)
                readout = block.feedforward[-1]
                assert isinstance(readout, nn.Linear)
                readout.weight.mul_((2 * depth) ** -0.5)

    def tokens(self, observations: Tensor) -> tuple[Tensor, Tensor]:
        """Read only native seat-visible features; private unknowns have explicit flags."""
        layout, base = self.layout, self.layout.observation
        n, cells, width = observations.shape[0], layout.cells, self.board.out_features
        unit_start = base.board_features
        global_start = unit_start + base.units * base.unit_features
        extra_start = global_start + base.global_features
        product_start = extra_start + base.units * base.unit_features
        history_start = product_start + 9 * base.product_features
        context_start = history_start + base.history_features
        product_context = context_start + 2 * cells * 8
        global_context = product_context + 9 * 8
        history_context = global_context + 16
        boards = observations[:, :unit_start].reshape(n, 2, -1, cells).transpose(2, 3)
        rich_boards = observations[:, context_start:product_context].reshape(n, 2, cells, 8)
        agronomy_start = history_context + 4 * 28
        agronomy_product = agronomy_start + 2 * cells * base.agronomy_board_features
        if base.agronomy_board_features:
            rich_boards = torch.cat(
                (
                    rich_boards,
                    observations[:, agronomy_start:agronomy_product].reshape(
                        n, 2, cells, base.agronomy_board_features
                    ),
                ),
                -1,
            )
        boards = self.board(torch.cat((boards, rich_boards), -1).float())
        spatial = boards.reshape(n * 2, layout.board_size, layout.board_size, width)
        spatial = self.local(spatial.permute(0, 3, 1, 2)).permute(0, 2, 3, 1)
        boards = boards + spatial.reshape(n, 2, cells, width)
        own = observations[:, unit_start:global_start].reshape(n, base.units, -1)
        other = observations[:, extra_start:product_start].reshape(n, base.units, -1)
        support = observations[:, -base.support_features :].reshape(n, base.units, 44)
        own_flags = own[..., :1].expand(-1, -1, 2)
        own_inputs = torch.cat((own, support, own_flags), -1)
        other_inputs = torch.cat(
            (other, torch.zeros_like(support), torch.zeros_like(own_flags)), -1
        )
        agronomy_global = agronomy_product + 9 * base.agronomy_product_features
        agronomy_units = agronomy_global + base.agronomy_global_features
        if base.agronomy_unit_features:
            unit_context = observations[
                :, agronomy_units : agronomy_units + 2 * base.units * base.agronomy_unit_features
            ].reshape(n, 2, base.units, base.agronomy_unit_features)
            sides = []
            for side, units in enumerate((own, other)):
                # Gather the standing tile's rich row; absent units read zeros.
                position = (units[..., 2:4].float() * (layout.board_size - 1)).round().long()
                index = (position[..., 1] * layout.board_size + position[..., 0]).clamp(
                    0, cells - 1
                )
                standing = torch.gather(
                    rich_boards[:, side],
                    1,
                    index[..., None].expand(-1, -1, rich_boards.shape[-1]),
                )
                sides.append(
                    torch.cat((unit_context[:, side], standing * (units[..., :1] > 0)), -1)
                )
            own_inputs = torch.cat((own_inputs, sides[0]), -1)
            other_inputs = torch.cat((other_inputs, sides[1]), -1)
        global_state = observations[:, global_start:extra_start]
        products = observations[:, product_start:history_start].reshape(n, 9, -1)
        products = torch.cat(
            (products, observations[:, product_context:global_context].reshape(n, 9, 8)), -1
        )
        if base.agronomy_product_features:
            products = torch.cat(
                (
                    products,
                    observations[
                        :, agronomy_product : agronomy_product + 9 * base.agronomy_product_features
                    ].reshape(n, 9, base.agronomy_product_features),
                ),
                -1,
            )
        shops = global_state[:, -64:].reshape(n, 8, 8)
        history = observations[:, history_start:context_start]
        context = observations[:, global_context:history_context]
        if base.agronomy_global_features:
            context = torch.cat((context, observations[:, agronomy_global:agronomy_units]), -1)
        histories = observations[:, history_context : history_context + 4 * 28].reshape(n, 4, 28)
        coordinate = self.coordinate(self.coordinates)
        tokens = [
            self.global_state(torch.cat((global_state, history, context), -1).float())[:, None]
            + self.kind[0],
            boards[:, 0] + coordinate + self.kind[1],
            boards[:, 1] + coordinate + self.kind[2],
        ]
        for side, units in enumerate((own_inputs, other_inputs)):
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
                self.history(histories.float()) + self.history_position + self.kind[7],
            )
        )
        valid = torch.cat(
            (
                torch.ones((n, 1 + 2 * cells), dtype=torch.bool, device=observations.device),
                own[..., 0] > 0,
                other[..., 0] > 0,
                torch.ones((n, 9), dtype=torch.bool, device=observations.device),
                shops.sum(-1) > 0,
                histories[..., 24] > 0,
            ),
            -1,
        )
        value = torch.cat(tokens, 1)
        if self.supplement is not None:
            value = self.supplement(value, observations, valid)
        for block in self.blocks:
            value = block(value, valid)
        return cast(Tensor, self.norm(value)), valid

    def forward(self, observations: Tensor) -> Tensor:
        """Return encoded entities for the stateless policy interface."""
        return self.tokens(observations)[0]
