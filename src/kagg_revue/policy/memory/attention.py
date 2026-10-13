"""Tiled relative-time attention without a dense query-by-memory bias tensor."""

import math

import torch
from torch import Tensor
from torch.nn.attention.flex_attention import flex_attention


def relative_attention(
    query: Tensor,
    key: Tensor,
    value: Tensor,
    relative: Tensor,
    steps: Tensor,
    key_steps: Tensor,
) -> Tensor:
    """Fuse relative-position lookup and whole-turn masking into tiled attention.

    The projected relative scores remain differentiable. In BF16, round their
    scaling before adding to FP32 attention scores, matching the dense SDPA bias.
    Every query can read its own turn, including all summaries from that turn.
    """
    window = relative.shape[-1] - 1
    scale = 1 / math.sqrt(query.shape[-1])

    def score_mod(score: Tensor, batch: Tensor, head: Tensor, q: Tensor, k: Tensor) -> Tensor:
        distance = steps[q] - key_steps[k]
        allowed = (key_steps[k] >= 0) & (distance >= 0) & (distance <= window)
        bias = (relative[batch, head, q, distance.clamp(0, window)] * scale).to(relative.dtype)
        return torch.where(allowed, score + bias, -float("inf"))

    return flex_attention(
        query,
        key,
        value,
        score_mod=score_mod,
        kernel_options={"BACKEND": "TRITON"},
    )
