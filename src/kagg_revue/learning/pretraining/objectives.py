"""Supervised likelihood with explicit, globally normalized action-domain weights."""

import torch
import torch.distributed as dist
from torch import Tensor

from kagg_revue.learning.pretraining.config import GroupedLoss
from kagg_revue.learning.pretraining.statistics import DOMAINS, domain_slices


class SupervisedLoss:
    """Share one BC objective across recurrent, flat and independent-row execution."""

    def __init__(self, config: GroupedLoss | None, units: int) -> None:
        """Keep an omitted configuration equivalent to the historical equal-row loss."""
        self.config = config
        self.units = units

    def scales(self, fields: Tensor, eligible: Tensor) -> Tensor:
        """Count full-batch fields before chunking; account for averaged rank gradients."""
        if self.config is None:
            return fields.new_zeros(len(DOMAINS))
        active = fields.float() * eligible[..., None]
        counts = torch.stack(
            [active[..., section].sum() for section in domain_slices(self.units, compact=False)]
        )
        world = 1
        if dist.is_initialized():
            dist.all_reduce(counts)
            world = dist.get_world_size()
        relative = [getattr(self.config.weights, name) for name in DOMAINS]
        if self.config.normalization == "field_mean":
            multipliers = counts.new_tensor(relative)
            mass = (multipliers * counts).sum()
            return multipliers * world / torch.where(mass > 0, mass, torch.ones_like(mass))
        weights = counts.new_tensor([value / sum(relative) for value in relative])
        # Clamp SUM counts, not rank means: one field on two ranks still has mass one.
        return weights * world / counts.clamp_min(1)

    def __call__(
        self,
        likelihood: Tensor,
        fields: Tensor,
        eligible: Tensor,
        mass: Tensor,
        scales: Tensor,
        *,
        compact: bool = False,
    ) -> Tensor:
        """Reduce a chunk using the same full-batch denominators on every call."""
        if self.config is None:
            per_row = -(likelihood * fields).sum(-1) / fields.sum(-1).clamp_min(1)
            return (per_row * eligible).sum() / mass
        terms = -likelihood.float() * fields.float() * eligible[..., None]
        sums = torch.stack(
            [terms[..., section].sum() for section in domain_slices(self.units, compact=compact)]
        )
        return (sums * scales).sum()
