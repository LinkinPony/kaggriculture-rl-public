"""Terminal-signal checks and reversible optimizer steps for PPO recovery."""

import copy
import math
from collections.abc import Callable
from dataclasses import dataclass

import torch
import torch.distributed as dist
from torch import Tensor


def has_return_variation(returns: Tensor) -> bool:
    """Check the whole distributed rollout, never individual minibatches or ranks."""
    if not returns.numel():
        raise ValueError("a rollout must contain terminal returns")
    bounds = torch.stack((returns.amin(), -returns.amax()))
    if dist.is_initialized():
        dist.all_reduce(bounds, op=dist.ReduceOp.MIN)
    if not bool(torch.isfinite(bounds).all()):
        raise ValueError("terminal returns must be finite")
    return bool(bounds.sum() < 0)


@dataclass(frozen=True)
class StepResult:
    """Actual post-step divergence and whether the transaction was committed."""

    accepted: bool
    attempts: int
    rejections: int
    divergence: float


def guarded_step(
    optimizer: torch.optim.Optimizer,
    measure: Callable[[], float],
    *,
    maximum: float,
    attempts: int,
    decay: float,
) -> StepResult:
    """Roll back parameters and Adam moments together when the KL limit is exceeded.

    The caller supplies synchronized gradients and a globally reduced KL probe.
    With decay 1, try exactly once and preserve the learning rate on rejection.
    Legacy backtracking reuses gradients from the restored parameters.
    Snapshot tensors remain on their existing device and are never aliased by a
    restored optimizer. The scale is checkpointed in optimizer parameter groups.
    """
    if attempts < 1 or not 0 < decay <= 1 or not math.isfinite(maximum) or maximum <= 0:
        raise ValueError("invalid optimizer backtracking bounds")
    if decay == 1:
        attempts = 1
    parameters = [parameter for group in optimizer.param_groups for parameter in group["params"]]
    before = [parameter.detach().clone() for parameter in parameters]
    state = copy.deepcopy(optimizer.state_dict())
    rates = [group["lr"] for group in optimizer.param_groups]
    scales = [group.get("guard_lr_scale", 1.0) for group in optimizer.param_groups]
    divergence = math.inf
    for attempt in range(attempts):
        optimizer.step()
        divergence = measure()
        if math.isfinite(divergence) and divergence <= maximum:
            return StepResult(True, attempt + 1, attempt, divergence)
        with torch.no_grad():
            for parameter, previous in zip(parameters, before, strict=True):
                parameter.copy_(previous)
        optimizer.load_state_dict(copy.deepcopy(state))
        if decay == 1:
            return StepResult(False, 1, 1, divergence)
        for group, rate, scale in zip(optimizer.param_groups, rates, scales, strict=True):
            group["lr"] = rate * decay ** (attempt + 1)
            group["guard_lr_scale"] = scale * decay ** (attempt + 1)
    return StepResult(False, attempts, attempts, divergence)
