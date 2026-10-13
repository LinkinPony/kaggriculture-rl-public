"""Padding removal that preserves typed and rotary entity positions."""

from __future__ import annotations

import torch
from torch import Tensor


def pack_entities(
    hidden: Tensor,
    valid: Tensor,
    positions: Tensor | None,
    capacity: int,
) -> tuple[Tensor, Tensor, Tensor | None]:
    """Pack valid entities into a host-bounded width without a device readback.

    The caller bounds capacity from native counts before graph replay. Embedding
    identities are already encoded; rotary positions travel with each entity.
    """
    width = hidden.shape[1]
    if capacity >= width:
        return hidden, valid, positions
    if capacity < 1:
        raise ValueError("packed effect entity capacity must be positive")
    indices = torch.arange(width, device=hidden.device)[None].expand(valid.shape)
    order = torch.where(valid, indices, indices + width).argsort(dim=1)[:, :capacity]
    packed = hidden.gather(1, order[..., None].expand(-1, -1, hidden.shape[-1]))
    position_values = indices if positions is None else positions[None].expand(valid.shape)
    return packed, valid.gather(1, order), position_values.gather(1, order)
