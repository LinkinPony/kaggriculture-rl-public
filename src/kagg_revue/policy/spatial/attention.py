"""Compiled key-masked attention with unchanged softmax and padding semantics."""

import torch
from torch import Tensor
from torch.nn.attention.flex_attention import FlexKernelOptions, flex_attention


def masked_attention(query: Tensor, key: Tensor, value: Tensor, valid: Tensor) -> Tensor:
    """Fuse the per-example key mask into the tiled attention score calculation."""

    def mask(score: Tensor, batch: Tensor, head: Tensor, q: Tensor, k: Tensor) -> Tensor:
        return torch.where(valid[batch, k], score, -float("inf"))

    options: FlexKernelOptions = {"BACKEND": "TRITON"}
    if query.shape[-1] == 64:
        # Measured H200 training tiles. Every scene has an unmasked global token.
        options.update({"ROWS_GUARANTEED_SAFE": True, "BLOCK_M": 64, "BLOCK_N": 64})
    return flex_attention(query, key, value, score_mod=mask, kernel_options=options)
