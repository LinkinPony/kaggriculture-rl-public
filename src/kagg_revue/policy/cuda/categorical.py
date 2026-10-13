"""Fused fixed-vocabulary categorical sampling for rollout CUDA Graphs."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from torch import Tensor


@triton.jit
def _sample_action_kernel(
    logits,
    legal,
    active,
    uniform,
    selected,
    log_probability,
    factors,
    CATEGORIES: tl.constexpr,
    BLOCK: tl.constexpr,
    USE_ACTIVE: tl.constexpr,
    TRACK_LOG_PROBABILITY: tl.constexpr,
    TRACK_FACTORS: tl.constexpr,
    ZERO_NON_FACTORS: tl.constexpr,
    LOGIT_ROW_STRIDE: tl.constexpr,
):
    row = tl.program_id(0)
    category = tl.arange(0, BLOCK)
    in_range = category < CATEGORIES
    allowed = tl.load(
        legal + row * CATEGORIES + category,
        mask=in_range,
        other=False,
    )
    row_active = True
    if USE_ACTIVE:
        row_active = tl.load(active + row)
        allowed |= (~row_active) & (category == 0)
    values = tl.load(
        logits + row * LOGIT_ROW_STRIDE + category,
        mask=in_range,
        other=-float("inf"),
    ).to(tl.float32)
    values = tl.where(allowed, values, -float("inf"))
    maximum = tl.max(values, axis=0)
    weights = tl.exp(values - maximum)
    total = tl.sum(weights, axis=0)
    threshold = tl.load(uniform + row).to(tl.float32) * total
    cumulative = tl.cumsum(weights, axis=0)
    candidate = tl.where(allowed & (cumulative > threshold), category, BLOCK)
    chosen = tl.min(candidate, axis=0)
    last_allowed = tl.max(tl.where(allowed, category, 0), axis=0)
    chosen = tl.where(chosen == BLOCK, last_allowed, chosen)
    tl.store(selected + row, chosen)
    legal_count = tl.sum(allowed.to(tl.int32), axis=0)
    factor = row_active & (legal_count > 1)
    if TRACK_LOG_PROBABILITY:
        chosen_logit = tl.sum(
            tl.where(category == chosen, values, 0.0),
            axis=0,
        )
        chosen_log_probability = chosen_logit - maximum - tl.log(total)
        if ZERO_NON_FACTORS:
            chosen_log_probability = tl.where(factor, chosen_log_probability, 0.0)
        tl.store(log_probability + row, chosen_log_probability)
    if TRACK_FACTORS:
        tl.store(factors + row, factor)


@triton.jit
def _sample_quantity_kernel(
    logits,
    tokens,
    has_quantity,
    uniform,
    quantities,
    log_probability,
    CATEGORIES: tl.constexpr,
    BLOCK: tl.constexpr,
    TRACK_LOG_PROBABILITY: tl.constexpr,
):
    row = tl.program_id(0)
    category = tl.arange(0, BLOCK)
    in_range = category < CATEGORIES
    token = tl.load(tokens + row)
    active = tl.load(has_quantity + token)
    values = tl.load(
        logits + row * CATEGORIES + category,
        mask=in_range & active,
        other=-float("inf"),
    ).to(tl.float32)
    values = tl.where((~active) & (category == 0), 0.0, values)
    maximum = tl.max(values, axis=0)
    weights = tl.exp(values - maximum)
    total = tl.sum(weights, axis=0)
    threshold = tl.load(uniform + row).to(tl.float32) * total
    cumulative = tl.cumsum(weights, axis=0)
    candidate = tl.where(in_range & (cumulative > threshold), category, BLOCK)
    chosen = tl.min(candidate, axis=0)
    chosen = tl.where(chosen == BLOCK, CATEGORIES - 1, chosen)
    tl.store(quantities + row, tl.where(active, chosen + 1, 0))
    if TRACK_LOG_PROBABILITY:
        chosen_logit = tl.sum(
            tl.where(category == chosen, values, 0.0),
            axis=0,
        )
        quantity_log_probability = chosen_logit - maximum - tl.log(total)
        action_log_probability = tl.load(log_probability + row)
        tl.store(
            log_probability + row,
            action_log_probability + tl.where(active, quantity_log_probability, 0.0),
        )


def _validate_common(logits: Tensor, uniform: Tensor, output: Tensor) -> None:
    if logits.device.type != "cuda" or logits.stride(1) != 1:
        raise ValueError("fused categorical logits must have contiguous categories")
    if logits.ndim != 2 or logits.shape[1] < 1:
        raise ValueError("fused categorical logits need a fixed nonempty vocabulary")
    if uniform.shape != logits.shape[:1] or uniform.dtype != torch.float32:
        raise ValueError("fused categorical uniforms must be float32 with one value per row")
    if output.shape != logits.shape[:1] or output.dtype != torch.int64:
        raise ValueError("fused categorical outputs must be int64 with one value per row")
    if uniform.device != logits.device or output.device != logits.device:
        raise ValueError("fused categorical tensors must share one CUDA device")


def sample_action(
    logits: Tensor,
    legal: Tensor,
    active: Tensor,
    uniform: Tensor,
    output: Tensor,
    log_probability: Tensor | None,
) -> None:
    """Sample legal action tokens and optionally write selected log probabilities."""
    _validate_common(logits, uniform, output)
    batch, categories = logits.shape
    if legal.shape != logits.shape or legal.dtype != torch.bool:
        raise ValueError("fused action legality must align with logits")
    if active.shape != (batch,) or active.dtype != torch.bool:
        raise ValueError("fused action activity must have one boolean per row")
    if legal.device != logits.device or active.device != logits.device:
        raise ValueError("fused action inputs must share one CUDA device")
    if log_probability is not None and (
        log_probability.shape != (batch,)
        or log_probability.dtype != torch.float32
        or log_probability.device != logits.device
    ):
        raise ValueError("fused action log probabilities have the wrong ABI")
    _sample_action_kernel[(batch,)](
        logits,
        legal,
        active,
        uniform,
        output,
        output if log_probability is None else log_probability,
        output,
        CATEGORIES=categories,
        BLOCK=triton.next_power_of_2(categories),
        USE_ACTIVE=True,
        TRACK_LOG_PROBABILITY=log_probability is not None,
        TRACK_FACTORS=False,
        ZERO_NON_FACTORS=False,
        LOGIT_ROW_STRIDE=logits.stride(0),
        num_warps=4,
    )


def sample_masked(
    logits: Tensor,
    legal: Tensor,
    uniform: Tensor,
) -> tuple[Tensor, Tensor]:
    """Sample a nonempty masked categorical and return its exact log probability."""
    batch = logits.shape[0]
    selected = torch.empty(batch, dtype=torch.int64, device=logits.device)
    log_probability = torch.empty(batch, dtype=torch.float32, device=logits.device)
    _validate_common(logits, uniform, selected)
    if legal.shape != logits.shape or legal.dtype != torch.bool:
        raise ValueError("fused categorical legality must align with logits")
    if legal.device != logits.device:
        raise ValueError("fused categorical inputs must share one CUDA device")
    categories = logits.shape[1]
    _sample_action_kernel[(batch,)](
        logits,
        legal,
        legal,
        uniform,
        selected,
        log_probability,
        selected,
        CATEGORIES=categories,
        BLOCK=triton.next_power_of_2(categories),
        USE_ACTIVE=False,
        TRACK_LOG_PROBABILITY=True,
        TRACK_FACTORS=False,
        ZERO_NON_FACTORS=False,
        LOGIT_ROW_STRIDE=logits.stride(0),
        num_warps=4,
    )
    return selected, log_probability


def sample_masked_factor(
    logits: Tensor,
    legal: Tensor,
    active: Tensor,
    uniform: Tensor,
) -> tuple[Tensor, Tensor, Tensor]:
    """Sample one program factor and return exact log probability and activity."""
    batch, categories = logits.shape
    selected = torch.empty(batch, dtype=torch.int64, device=logits.device)
    log_probability = torch.empty(
        batch,
        dtype=torch.float32,
        device=logits.device,
    )
    factors = torch.empty(batch, dtype=torch.bool, device=logits.device)
    _validate_common(logits, uniform, selected)
    if legal.shape != logits.shape or legal.dtype != torch.bool:
        raise ValueError("fused program legality must align with logits")
    if active.shape != (batch,) or active.dtype != torch.bool:
        raise ValueError("fused program activity must have one boolean per row")
    if legal.device != logits.device or active.device != logits.device:
        raise ValueError("fused program categorical inputs must share one CUDA device")
    _sample_action_kernel[(batch,)](
        logits,
        legal,
        active,
        uniform,
        selected,
        log_probability,
        factors,
        CATEGORIES=categories,
        BLOCK=triton.next_power_of_2(categories),
        USE_ACTIVE=True,
        TRACK_LOG_PROBABILITY=True,
        TRACK_FACTORS=True,
        ZERO_NON_FACTORS=True,
        LOGIT_ROW_STRIDE=logits.stride(0),
        num_warps=4,
    )
    return selected, log_probability, factors


def sample_quantity(
    logits: Tensor,
    tokens: Tensor,
    has_quantity: Tensor,
    uniform: Tensor,
    output: Tensor,
    log_probability: Tensor | None,
) -> None:
    """Sample positive quantities only for tokens whose ABI requires one."""
    _validate_common(logits, uniform, output)
    batch, categories = logits.shape
    if tokens.shape != (batch,) or tokens.dtype != torch.int64:
        raise ValueError("fused quantity tokens must be int64 with one value per row")
    if has_quantity.ndim != 1 or has_quantity.dtype != torch.bool:
        raise ValueError("fused quantity mask must be a one-dimensional boolean tensor")
    if tokens.device != logits.device or has_quantity.device != logits.device:
        raise ValueError("fused quantity inputs must share one CUDA device")
    if log_probability is not None and (
        log_probability.shape != (batch,)
        or log_probability.dtype != torch.float32
        or log_probability.device != logits.device
    ):
        raise ValueError("fused quantity log probabilities have the wrong ABI")
    _sample_quantity_kernel[(batch,)](
        logits,
        tokens,
        has_quantity,
        uniform,
        output,
        output if log_probability is None else log_probability,
        CATEGORIES=categories,
        BLOCK=triton.next_power_of_2(categories),
        TRACK_LOG_PROBABILITY=log_probability is not None,
        num_warps=4,
    )


__all__ = [
    "sample_action",
    "sample_masked",
    "sample_masked_factor",
    "sample_quantity",
]
