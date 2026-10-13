"""H200 rollout weight packing for the factorized task policy."""

from __future__ import annotations

from copy import deepcopy

import torch
from torch import nn

from kagg_revue.policy.tasks.model import UnitTaskPolicy


def _pack_bfloat16_gemm_weights(policy: UnitTaskPolicy) -> None:
    """Store weights that autocast consumes as BF16 in their final format."""
    with torch.no_grad():
        for module in policy.modules():
            if isinstance(module, nn.Linear):
                module.to(dtype=torch.bfloat16)
            if isinstance(module, nn.MultiheadAttention):
                if module.in_proj_weight is not None:
                    module.in_proj_weight.data = (
                        module.in_proj_weight.data.bfloat16()
                    )
                if module.in_proj_bias is not None:
                    module.in_proj_bias.data = (
                        module.in_proj_bias.data.bfloat16()
                    )


def create_h200_rollout_policy(
    source: UnitTaskPolicy,
) -> UnitTaskPolicy:
    """Clone one factorized policy with inference-only GEMM weight packing."""
    parameter = next(source.parameters())
    if (
        source.factorized is None
        or parameter.device.type != "cuda"
        or "H200" not in torch.cuda.get_device_name(parameter.device)
    ):
        raise ValueError("task rollout packing requires factorized-v3 on H200")
    result = deepcopy(source).eval()
    _pack_bfloat16_gemm_weights(result)
    return result


def refresh_h200_rollout_policy(
    target: UnitTaskPolicy,
    source: UnitTaskPolicy,
) -> None:
    """Refresh packed storage from FP32 master weights without moving addresses."""
    target_state = target.state_dict()
    source_state = source.state_dict()
    if target_state.keys() != source_state.keys():
        raise RuntimeError("packed task rollout policy structure changed")
    with torch.no_grad():
        for name, target_value in target_state.items():
            source_value = source_state[name]
            if (
                target_value.shape != source_value.shape
                or target_value.device != source_value.device
            ):
                raise RuntimeError(
                    f"packed task rollout tensor changed at {name}"
                )
            target_value.copy_(source_value)


__all__ = [
    "create_h200_rollout_policy",
    "refresh_h200_rollout_policy",
]
