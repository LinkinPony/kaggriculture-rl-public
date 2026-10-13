"""Bounded autograd CUDA Graph buckets over the shared PyTorch policy."""

from collections.abc import Iterable
from typing import Literal, cast

import torch
from torch import Tensor, nn


class Replay(nn.Module):
    """Give each graph bucket its own forward method while sharing all parameters."""

    def __init__(self, policy: nn.Module, precision: Literal["bf16", "fp32"] = "fp32") -> None:
        """Apply identical mixed precision to eager and graphed forward execution."""
        super().__init__()
        self.policy = policy
        self.precision = precision

    def forward(self, observations: Tensor, steps: Tensor, actions: Tensor) -> Tensor:
        """Keep master parameters in FP32 and cast eligible neural operators only."""
        with torch.autocast(
            observations.device.type,
            dtype=torch.bfloat16,
            enabled=observations.is_cuda and self.precision == "bf16",
            cache_enabled=False,
        ):
            return cast(Tensor, self.policy(observations, steps, actions))


class GraphReplay:
    """Capture forward and backward once for each permitted learner row count."""

    def __init__(
        self, policy: nn.Module, widths: set[int], precision: Literal["bf16", "fp32"] = "fp32"
    ) -> None:
        """Bound graph memory by the exact full and remainder microbatch shapes."""
        self.policy = policy
        self.widths = widths
        self.precision = precision
        self.graphs: dict[int, nn.Module] = {}

    def __call__(self, observations: Tensor, steps: Tensor, actions: Tensor) -> Tensor:
        """Replay one autograd node, copying only the current microbatch inputs."""
        count = len(steps)
        if count not in self.widths:
            raise ValueError(f"unplanned learner graph width: {count}")
        if count not in self.graphs:
            inputs = tuple(value.detach().clone() for value in (observations, steps, actions))
            wrapper = Replay(self.policy, self.precision).eval()
            # Buckets share parameters whose autograd nodes outlive earlier captures.
            # Captures are serialized within each learner process.
            torch.autograd.graph.set_override_stale_capture_stream(True)
            try:
                self.graphs[count] = cast(
                    nn.Module,
                    torch.cuda.make_graphed_callables(wrapper, inputs, allow_unused_input=True),
                )
            finally:
                torch.autograd.graph.set_override_stale_capture_stream(False)
        return cast(Tensor, self.graphs[count](observations, steps, actions))


class GradientBuffers:
    """Accumulate into storage independent from a graph's reusable gradient outputs."""

    def __init__(self, parameters: Iterable[nn.Parameter]) -> None:
        """Allocate once for exactly the trainable optimizer parameter set."""
        self.parameters = list(parameters)
        self.buffers = [torch.zeros_like(parameter) for parameter in self.parameters]

    def zero(self) -> None:
        """Prevent AccumulateGrad from adopting and aliasing graph output storage."""
        for parameter, buffer in zip(self.parameters, self.buffers, strict=True):
            parameter.grad = buffer
        torch._foreach_zero_(self.buffers)
