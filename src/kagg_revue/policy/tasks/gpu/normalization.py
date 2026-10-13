"""H200 inference normalization for the factorized task policy."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor


@triton.jit
def _layer_norm_kernel(
    values,
    weight,
    bias,
    output,
    WIDTH: tl.constexpr,
    EPSILON: tl.constexpr,
    BLOCK: tl.constexpr,
):
    row = tl.program_id(0)
    column = tl.arange(0, BLOCK)
    present = column < WIDTH
    value = tl.load(
        values + row * WIDTH + column,
        mask=present,
        other=0.0,
    ).to(tl.float32)
    mean = tl.sum(value, axis=0) / WIDTH
    centered = tl.where(present, value - mean, 0.0)
    variance = tl.sum(centered * centered, axis=0) / WIDTH
    normalized = centered * tl.rsqrt(variance + EPSILON)
    scale = tl.load(weight + column, mask=present, other=0.0).to(
        tl.float32
    )
    offset = tl.load(bias + column, mask=present, other=0.0).to(
        tl.float32
    )
    tl.store(
        output + row * WIDTH + column,
        normalized * scale + offset,
        mask=present,
    )


def h200_layer_norm(
    values: Tensor,
    weight: Tensor,
    bias: Tensor,
    epsilon: float,
) -> Tensor:
    """Apply last-axis LayerNorm with one H200 kernel in inference."""
    width = values.shape[-1]
    if (
        values.device.type != "cuda"
        or not values.is_contiguous()
        or values.numel() == 0
        or width < 1
        or weight.shape != (width,)
        or bias.shape != (width,)
        or weight.device != values.device
        or bias.device != values.device
        or epsilon <= 0.0
    ):
        raise ValueError("H200 task LayerNorm received incompatible tensors")
    if "H200" not in torch.cuda.get_device_name(values.device):
        raise ValueError("factorized task LayerNorm is specialized for H200")
    output = torch.empty_like(values)
    rows = values.numel() // width
    _layer_norm_kernel[(rows,)](
        values,
        weight,
        bias,
        output,
        WIDTH=width,
        EPSILON=epsilon,
        BLOCK=triton.next_power_of_2(width),
        num_warps=4 if width >= 128 else 1,
    )
    return output


__all__ = ["h200_layer_norm"]
