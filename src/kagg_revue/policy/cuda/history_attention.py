"""Prefix-bounded single-query attention for rollout history caches."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor


@triton.jit
def _history_attention_kernel(
    query,
    current_key,
    current_value,
    key_cache,
    value_cache,
    position,
    output,
    QUERY_BATCH_STRIDE: tl.constexpr,
    QUERY_HEAD_STRIDE: tl.constexpr,
    QUERY_WIDTH_STRIDE: tl.constexpr,
    KEY_BATCH_STRIDE: tl.constexpr,
    KEY_HEAD_STRIDE: tl.constexpr,
    KEY_WIDTH_STRIDE: tl.constexpr,
    VALUE_BATCH_STRIDE: tl.constexpr,
    VALUE_HEAD_STRIDE: tl.constexpr,
    VALUE_WIDTH_STRIDE: tl.constexpr,
    HEADS: tl.constexpr,
    HEAD_WIDTH: tl.constexpr,
    MAX_HISTORY: tl.constexpr,
    BLOCK_D: tl.constexpr,
    BLOCK_N: tl.constexpr,
    SCALE: tl.constexpr,
):
    row = tl.program_id(0)
    batch = row // HEADS
    head = row % HEADS
    width = tl.arange(0, BLOCK_D)
    width_mask = width < HEAD_WIDTH
    query_offset = (
        batch * QUERY_BATCH_STRIDE
        + head * QUERY_HEAD_STRIDE
        + width * QUERY_WIDTH_STRIDE
    )
    key_offset = (
        batch * KEY_BATCH_STRIDE
        + head * KEY_HEAD_STRIDE
        + width * KEY_WIDTH_STRIDE
    )
    value_offset = (
        batch * VALUE_BATCH_STRIDE
        + head * VALUE_HEAD_STRIDE
        + width * VALUE_WIDTH_STRIDE
    )
    query_values = tl.load(query + query_offset, mask=width_mask, other=0.0)
    next_key = tl.load(current_key + key_offset, mask=width_mask, other=0.0)
    next_value = tl.load(
        current_value + value_offset,
        mask=width_mask,
        other=0.0,
    )
    write_position = tl.load(position)
    cache_row = row * MAX_HISTORY * HEAD_WIDTH
    write_offset = cache_row + write_position * HEAD_WIDTH + width
    tl.store(key_cache + write_offset, next_key, mask=width_mask)
    tl.store(value_cache + write_offset, next_value, mask=width_mask)

    visible = write_position + 1
    maximum = -float("inf")
    denominator = 0.0
    accumulator = tl.zeros((BLOCK_D,), dtype=tl.float32)
    start = 0
    while start < visible:
        history = start + tl.arange(0, BLOCK_N)
        history_mask = history < visible
        offsets = (
            cache_row
            + history[:, None] * HEAD_WIDTH
            + width[None, :]
        )
        mask = history_mask[:, None] & width_mask[None, :]
        keys = tl.load(key_cache + offsets, mask=mask, other=0.0)
        values = tl.load(value_cache + offsets, mask=mask, other=0.0)
        current = history == write_position
        keys = tl.where(current[:, None], next_key[None, :], keys)
        values = tl.where(current[:, None], next_value[None, :], values)
        scores = tl.sum(
            keys.to(tl.float32) * query_values[None, :].to(tl.float32),
            axis=1,
        ) * SCALE
        scores = tl.where(history_mask, scores, -float("inf"))
        block_maximum = tl.max(scores, axis=0)
        next_maximum = tl.maximum(maximum, block_maximum)
        correction = tl.exp(maximum - next_maximum)
        weights = tl.exp(scores - next_maximum)
        denominator = denominator * correction + tl.sum(weights, axis=0)
        accumulator = accumulator * correction + tl.sum(
            weights[:, None] * values.to(tl.float32),
            axis=0,
        )
        maximum = next_maximum
        start += BLOCK_N
    tl.store(
        output + row * HEAD_WIDTH + width,
        accumulator / denominator,
        mask=width_mask,
    )


def history_attention_step(
    query: Tensor,
    current_key: Tensor,
    current_value: Tensor,
    key_cache: Tensor,
    value_cache: Tensor,
    position: Tensor,
) -> Tensor:
    """Append one KV pair and attend only through the device-resident prefix."""
    if query.device.type != "cuda":
        raise ValueError("rollout history attention requires CUDA tensors")
    if query.ndim != 4 or query.shape[2] != 1:
        raise ValueError("rollout history attention requires one query token")
    if current_key.shape != query.shape or current_value.shape != query.shape:
        raise ValueError("rollout history QKV tensors must have matching shapes")
    batch, heads, _, head_width = query.shape
    expected_cache = (batch, heads, key_cache.shape[2], head_width)
    if key_cache.shape != expected_cache or value_cache.shape != expected_cache:
        raise ValueError("rollout history caches have incompatible shapes")
    tensors = (current_key, current_value, key_cache, value_cache, position)
    if any(tensor.device != query.device for tensor in tensors):
        raise ValueError("rollout history tensors must share one CUDA device")
    if any(tensor.dtype != query.dtype for tensor in tensors[:-1]):
        raise ValueError("rollout history QKV tensors must share one dtype")
    if not key_cache.is_contiguous() or not value_cache.is_contiguous():
        raise ValueError("rollout history caches must be contiguous")
    if position.shape != (1,) or position.dtype not in {torch.int32, torch.int64}:
        raise ValueError("rollout history position must be one integer device value")
    output = torch.empty(
        query.shape,
        dtype=query.dtype,
        device=query.device,
    )
    block_d = triton.next_power_of_2(head_width)
    block_n = 64 if head_width <= 64 else 16
    _history_attention_kernel[(batch * heads,)](
        query,
        current_key,
        current_value,
        key_cache,
        value_cache,
        position,
        output,
        QUERY_BATCH_STRIDE=query.stride(0),
        QUERY_HEAD_STRIDE=query.stride(1),
        QUERY_WIDTH_STRIDE=query.stride(3),
        KEY_BATCH_STRIDE=current_key.stride(0),
        KEY_HEAD_STRIDE=current_key.stride(1),
        KEY_WIDTH_STRIDE=current_key.stride(3),
        VALUE_BATCH_STRIDE=current_value.stride(0),
        VALUE_HEAD_STRIDE=current_value.stride(1),
        VALUE_WIDTH_STRIDE=current_value.stride(3),
        HEADS=heads,
        HEAD_WIDTH=head_width,
        MAX_HISTORY=key_cache.shape[2],
        BLOCK_D=block_d,
        BLOCK_N=block_n,
        SCALE=head_width**-0.5,
        num_warps=4,
    )
    return output


__all__ = ["history_attention_step"]
