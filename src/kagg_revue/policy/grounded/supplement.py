"""Zero-initialized v5b features on the unchanged v4 entity sequence."""

import torch
from torch import Tensor, nn

from kagg_revue.native.derived import legacy_layout
from kagg_revue.policy.contracts import ContractLayout


class Supplement(nn.Module):
    """Learn derived features without changing pretrained input projections."""

    def __init__(self, layout: ContractLayout, width: int) -> None:
        """Validate the complete schema and initialize every new contribution to zero."""
        super().__init__()
        base = layout.observation
        legacy_layout(base)
        self.start = base.features - base.support_features - base.derived_features
        self.shapes = (
            (1, base.derived_global_features),
            (2 * layout.cells, base.derived_board_features),
            (2 * base.units, base.derived_unit_features),
            (9, base.derived_product_features),
        )
        self.projections = nn.ModuleList(
            nn.Linear(size, width, bias=False) for _, size in self.shapes
        )
        for parameter in self.parameters():
            nn.init.zeros_(parameter)

    def forward(self, value: Tensor, observations: Tensor, valid: Tensor) -> Tensor:
        """Add only to existing entities; leave shop/history positions and masks intact."""
        offset = self.start
        additions = []
        for layer, (count, size) in zip(self.projections, self.shapes, strict=True):
            end = offset + count * size
            fields = observations[:, offset:end].reshape(len(value), count, size).float()
            additions.append(layer(fields))
            offset = end
        used = sum(count for count, _ in self.shapes)
        additions.append(torch.zeros_like(value[:, used:]))
        return value + torch.cat(additions, 1) * valid[..., None]
