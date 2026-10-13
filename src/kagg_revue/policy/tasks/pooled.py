"""Launch-efficient encoders for the pooled unit-task policy."""

from __future__ import annotations

from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.tasks.gpu.prefix import pooled_prefix_components
from kagg_revue.policy.tasks.schema import TaskTapeArchitecture


class PooledTaskPrefixEncoder(nn.Module):
    """Encode full task history with typed pooling instead of quadratic attention."""

    field_offsets: Tensor
    field_limits: Tensor

    def __init__(self, architecture: TaskTapeArchitecture) -> None:
        """Create one offset embedding table and a compact summary projection."""
        super().__init__()
        width = architecture.model_width
        sizes = (
            architecture.unit_limit,
            architecture.operation_tokens,
            architecture.item_tokens + 1,
            architecture.board_size + 1,
            architecture.board_size + 1,
            architecture.maximum_quantity + 1,
            architecture.time_tokens,
            architecture.time_tokens,
            architecture.status_tokens,
        )
        offsets: list[int] = []
        total = 0
        for size in sizes:
            offsets.append(total)
            total += size
        self.architecture = architecture
        self.fields = nn.Embedding(total, width)
        prefix_capacity = (
            architecture.history_window
            if architecture.architecture_version == "factorized-v3"
            else architecture.prefix_capacity
        )
        self.position = nn.Embedding(prefix_capacity, width)
        self.begin = nn.Parameter(torch.empty(width).normal_(std=0.02))
        self.register_buffer(
            "field_offsets",
            torch.tensor(offsets, dtype=torch.long),
        )
        self.register_buffer(
            "field_limits",
            torch.tensor(sizes, dtype=torch.long) - 1,
        )
        self.output = nn.Sequential(
            nn.LayerNorm(4 * width),
            nn.Linear(4 * width, width),
            nn.SiLU(),
            nn.LayerNorm(width),
        )

    def forward(
        self,
        fields: Tensor,
        mask: Tensor,
        active_length: int | None = None,
        owner: Tensor | None = None,
    ) -> Tensor:
        """Pool all, active, and most-recent task records into one state token."""
        active = (
            int(mask.sum(dim=1).max().detach().cpu())
            if active_length is None
            else active_length
        )
        if active < 0 or active > fields.shape[1]:
            raise ValueError("unit-task active prefix length is outside its tensor")
        batch = fields.shape[0]
        begin = self.begin[None].expand(batch, -1)
        if active == 0:
            zeros = torch.zeros_like(begin)
            return cast(Tensor, self.output(torch.cat((begin, zeros, zeros, zeros), dim=1)))

        if fields.device.type == "cuda" and not torch.is_grad_enabled():
            pooled = pooled_prefix_components(
                fields,
                mask,
                self.fields.weight,
                self.position.weight,
                self.field_offsets,
                self.field_limits,
                active,
                owner,
            )
            return cast(
                Tensor,
                self.output(
                    torch.cat((begin, pooled.reshape(batch, -1)), dim=1)
                ),
            )

        values = fields[:, :active].long()
        valid = mask[:, :active].bool()
        tokens = torch.minimum(values.clamp_min(0), self.field_limits)
        tokens = tokens + self.field_offsets
        hidden = self.fields(tokens).sum(dim=2)
        positions = torch.arange(active, device=fields.device)
        hidden = hidden + self.position(positions)[None]

        valid_values = valid[..., None].to(hidden.dtype)
        mean = (hidden * valid_values).sum(dim=1) / valid_values.sum(
            dim=1
        ).clamp_min(1.0)
        current = valid & (values[..., 8] == 0)
        if owner is not None:
            if owner.shape != (batch,):
                raise ValueError("task prefix owner must match its batch")
            current &= values[..., 0] == owner[:, None]
        current_values = current[..., None].to(hidden.dtype)
        current_mean = (hidden * current_values).sum(dim=1) / current_values.sum(
            dim=1
        ).clamp_min(1.0)
        counts = valid.sum(dim=1)
        rows = torch.arange(batch, device=fields.device)
        recent = hidden[rows, (counts - 1).clamp_min(0)]
        recent = recent * (counts > 0)[:, None]
        return cast(
            Tensor,
            self.output(torch.cat((begin, mean, current_mean, recent), dim=1)),
        )


class PooledCandidateEncoder(nn.Module):
    """Map exact dynamic facts with a score-factorizable linear projection."""

    def __init__(self, architecture: TaskTapeArchitecture) -> None:
        """Create the factorized feature projection."""
        super().__init__()
        self.projection = nn.Linear(
            architecture.candidate_features,
            architecture.model_width,
            bias=False,
        )

    def forward(self, features: Tensor) -> Tensor:
        """Return one dynamic embedding for each compiler candidate."""
        return cast(Tensor, self.projection(features))


__all__ = ["PooledCandidateEncoder", "PooledTaskPrefixEncoder"]
