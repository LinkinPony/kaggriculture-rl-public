"""Experimental zero residuals; not a production encoder or feature extractor."""

from typing import cast

import torch
from torch import Tensor, nn


class ResidualProbe(nn.Module):
    """Inject synthetic supplementary fields before the first entity block.

    The proposal preserves the original 286 entity positions. Hooks are used
    only to test that insertion point on an unchanged, authenticated v4 model.
    """

    dimensions = {"global_state": 24, "board": 20, "units": 16, "products": 96}

    def __init__(self, width: int, cells: int, units: int) -> None:
        """Create independently trainable, bias-free, initially zero projections."""
        super().__init__()
        self.counts = (1, 2 * cells, 2 * units, 9)
        self.projections = nn.ModuleDict(
            {name: nn.Linear(size, width, bias=False) for name, size in self.dimensions.items()}
        )
        for parameter in self.parameters():
            nn.init.zeros_(parameter)
        self.values: Tensor | None = None

    @property
    def features(self) -> int:
        """Return the flat width of the proposed supplementary block."""
        return sum(
            count * size for count, size in zip(self.counts, self.dimensions.values(), strict=True)
        )

    def hook(self, module: nn.Module, inputs: tuple[Tensor, Tensor]) -> tuple[Tensor, Tensor]:
        """Add residuals to existing entities, preserving shops and history tokens."""
        del module
        value, valid = inputs
        assert self.values is not None
        offset = 0
        additions = []
        for (name, size), count in zip(self.dimensions.items(), self.counts, strict=True):
            stop = offset + count * size
            fields = self.values[:, offset:stop].reshape(len(value), count, size)
            additions.append(cast(Tensor, self.projections[name](fields.float())))
            offset = stop
        used = sum(self.counts)
        additions.append(torch.zeros_like(value[:, used:]))
        return value + torch.cat(additions, 1) * valid[..., None], valid
