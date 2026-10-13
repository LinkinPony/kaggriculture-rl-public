"""Atomic LayerNorm forward/backward boundaries for compiled causal decoders."""

from typing import Any, cast

import torch
from torch import Tensor, nn


@torch.library.custom_op("kagg_revue::decoder_layer_norm", mutates_args=())
def _forward(
    values: Tensor, weight: Tensor, bias: Tensor, epsilon: float
) -> tuple[Tensor, Tensor, Tensor]:
    """Keep adjacent decoder reductions out of Inductor's unsafe fusion."""
    return torch.native_layer_norm(values, [weight.numel()], weight, bias, epsilon)


@_forward.register_fake
def _forward_fake(
    values: Tensor, weight: Tensor, bias: Tensor, epsilon: float
) -> tuple[Tensor, Tensor, Tensor]:
    shape = (*values.shape[:-1], 1)
    return torch.empty_like(values), weight.new_empty(shape), weight.new_empty(shape)


@torch.library.custom_op("kagg_revue::decoder_layer_norm_backward", mutates_args=())
def _backward(
    gradient: Tensor,
    values: Tensor,
    weight: Tensor,
    bias: Tensor,
    mean: Tensor,
    inverse_std: Tensor,
) -> tuple[Tensor, Tensor, Tensor]:
    """Use native derivatives with saved forward statistics and separate outputs."""
    return cast(
        tuple[Tensor, Tensor, Tensor],
        torch.ops.aten.native_layer_norm_backward(
            gradient, values, [weight.numel()], mean, inverse_std, weight, bias, [True, True, True]
        ),
    )


@_backward.register_fake
def _backward_fake(
    gradient: Tensor,
    values: Tensor,
    weight: Tensor,
    bias: Tensor,
    mean: Tensor,
    inverse_std: Tensor,
) -> tuple[Tensor, Tensor, Tensor]:
    return torch.empty_like(values), torch.empty_like(weight), torch.empty_like(bias)


def _setup(
    ctx: Any, inputs: tuple[Tensor, Tensor, Tensor, float], output: tuple[Tensor, Tensor, Tensor]
) -> None:
    values, weight, bias, _ = inputs
    _, mean, inverse_std = output
    ctx.save_for_backward(values, weight, bias, mean, inverse_std)
    ctx.mark_non_differentiable(mean, inverse_std)


def _gradient(
    ctx: Any, gradient: Tensor, _mean: Tensor, _inverse_std: Tensor
) -> tuple[Tensor, Tensor, Tensor, None]:
    values, weight, bias, mean, inverse_std = ctx.saved_tensors
    return (*_backward(gradient, values, weight, bias, mean, inverse_std), None)


_forward.register_autograd(_gradient, setup_context=_setup)


class LayerNorm(nn.LayerNorm):
    """Preserve LayerNorm parameters while preventing cross-normalization fusion.

    The installed Inductor/Triton emits a decoder kernel whose second reduction
    reads a temporary before its first reduction writes it. An opaque native
    operator gives each normalization its own initialized outputs and saved
    statistics. This applies equally to BC, PPO likelihoods and CUDA-graph acts.
    """

    def forward(self, input: Tensor) -> Tensor:
        """Run the same native normalization and analytical derivative every time."""
        assert self.weight is not None and self.bias is not None
        return cast(Tensor, _forward(input, self.weight, self.bias, self.eps)[0])
