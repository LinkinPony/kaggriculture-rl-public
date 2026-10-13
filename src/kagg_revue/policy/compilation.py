"""Measured device-specific compiler choices for recurrent network components."""

from typing import Any

import torch


def options(device: torch.device) -> dict[str, Any]:
    """Select Hopper layouts and arithmetic without changing parameter storage."""
    result: dict[str, Any] = {"triton.cudagraphs": False}
    if device.type == "cuda" and torch.cuda.get_device_capability(device)[0] == 9:
        # H200 fixed-rollout measurements include forward, backward and optimizer
        # updates. NHWC convolution and 1x1 GEMMs avoid costly native depthwise
        # backward paths; fast exp permits the accepted small rounding differences.
        result.update(
            use_fast_math=True,
            force_layout_optimization=True,
            conv_1x1_as_mm=True,
        )
        # Shapes are bounded and warmed before CUDA graph capture.
        torch.backends.cudnn.benchmark = True
    return result
