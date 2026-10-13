"""Fused inference-only pooling for the compact task-prefix encoder."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor


@triton.jit
def _prefix_pool_kernel(
    fields,
    mask,
    embeddings,
    positions,
    offsets,
    limits,
    owners,
    output,
    WIDTH: tl.constexpr,
    ACTIVE: tl.constexpr,
    CAPACITY: tl.constexpr,
    FILTER_OWNER: tl.constexpr,
    RECORD_BLOCK: tl.constexpr,
    WIDTH_BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    record = tl.arange(0, RECORD_BLOCK)[:, None]
    width = (
        tl.program_id(1) * WIDTH_BLOCK
        + tl.arange(0, WIDTH_BLOCK)[None, :]
    )
    width_present = width < WIDTH
    present = (record < ACTIVE) & (record < CAPACITY)
    present &= tl.load(
        mask + row * CAPACITY + record,
        mask=record < CAPACITY,
        other=0,
    ) != 0
    hidden = tl.load(
        positions + record * WIDTH + width,
        mask=present & width_present,
        other=0.0,
    ).to(tl.float32)
    status = tl.zeros((RECORD_BLOCK, 1), dtype=tl.int32)
    record_owner = tl.zeros((RECORD_BLOCK, 1), dtype=tl.int32)
    for field in tl.static_range(0, 9):
        token = tl.load(
            fields + (row * CAPACITY + record) * 9 + field,
            mask=present,
            other=0,
        ).to(tl.int32)
        limit = tl.load(limits + field)
        token = tl.minimum(tl.maximum(token, 0), limit)
        token += tl.load(offsets + field)
        hidden += tl.load(
            embeddings + token * WIDTH + width,
            mask=present & width_present,
            other=0.0,
        ).to(tl.float32)
        if field == 0:
            record_owner = token - tl.load(offsets + field)
        if field == 8:
            status = token - tl.load(offsets + field)
    count = tl.sum(present.to(tl.float32), axis=0)
    total = tl.sum(tl.where(present, hidden, 0.0), axis=0)
    current = present & (status == 0)
    if FILTER_OWNER:
        current &= record_owner == tl.load(owners + row)
    current_count = tl.sum(current.to(tl.float32), axis=0)
    current_total = tl.sum(tl.where(current, hidden, 0.0), axis=0)
    recent_record = tl.maximum(count.to(tl.int32) - 1, 0)
    recent = tl.sum(
        tl.where(
            present & (record == recent_record),
            hidden,
            0.0,
        ),
        axis=0,
    )
    base = row * 3 * WIDTH + width
    tl.store(
        output + base,
        total / tl.maximum(count, 1.0),
        mask=width_present,
    )
    tl.store(
        output + base + WIDTH,
        current_total / tl.maximum(current_count, 1.0),
        mask=width_present,
    )
    tl.store(
        output + base + 2 * WIDTH,
        recent,
        mask=width_present,
    )


def pooled_prefix_components(
    fields: Tensor,
    mask: Tensor,
    embeddings: Tensor,
    positions: Tensor,
    offsets: Tensor,
    limits: Tensor,
    active: int,
    owner: Tensor | None = None,
) -> Tensor:
    """Return mean, active mean, and recent vectors without materialization."""
    batch, capacity, field_count = fields.shape
    width = embeddings.shape[1]
    if (
        fields.device.type != "cuda"
        or fields.shape != (batch, capacity, 9)
        or field_count != 9
        or mask.shape != (batch, capacity)
        or positions.shape != (capacity, width)
        or offsets.shape != (9,)
        or limits.shape != (9,)
        or active < 0
        or active > capacity
        or (owner is not None and owner.shape != (batch,))
    ):
        raise ValueError("fused task prefix inputs have the wrong shape")
    owner_values = offsets if owner is None else owner
    values = (
        fields,
        mask,
        embeddings,
        positions,
        offsets,
        limits,
        owner_values,
    )
    if any(value.device != fields.device or not value.is_contiguous() for value in values):
        raise ValueError("fused task prefix inputs must be contiguous CUDA tensors")
    output = torch.empty(
        (batch, 3, width), dtype=torch.float32, device=fields.device
    )
    record_block = triton.next_power_of_2(max(1, active))
    width_block = 16
    _prefix_pool_kernel[(batch, triton.cdiv(width, width_block))](
        fields,
        mask,
        embeddings,
        positions,
        offsets,
        limits,
        owner_values,
        output,
        WIDTH=width,
        ACTIVE=active,
        CAPACITY=capacity,
        FILTER_OWNER=owner is not None,
        RECORD_BLOCK=record_block,
        WIDTH_BLOCK=width_block,
        num_warps=4,
    )
    return output


__all__ = ["pooled_prefix_components"]
