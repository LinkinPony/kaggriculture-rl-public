"""Check relative-score derivatives and measure real recurrent attention shapes."""

import json
import math
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any, cast

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from torch import Tensor
from torch.nn import functional as F

from kagg_revue.artifacts.io import write_json
from kagg_revue.policy.memory.attention import relative_attention


def _operation(
    function: Callable[..., Tensor],
    inputs: tuple[Tensor, ...],
    steps: Tensor,
    key_steps: Tensor,
    gradient: Tensor,
    backward: bool,
) -> tuple[Tensor, ...]:
    with torch.set_grad_enabled(backward):
        value = function(*inputs, steps, key_steps)
        return (value, *torch.autograd.grad(value, inputs, gradient)) if backward else (value,)


def dense_attention(
    query: Tensor, key: Tensor, value: Tensor, relative: Tensor, steps: Tensor, key_steps: Tensor
) -> Tensor:
    """Use the original gathered additive bias as the numerical reference."""
    distance = steps[:, None] - key_steps[None]
    window = relative.shape[-1] - 1
    allowed = (key_steps[None] >= 0) & (distance >= 0) & (distance <= window)
    indices = distance.clamp(0, window)[None, None].expand(*query.shape[:2], -1, -1)
    bias = relative.gather(-1, indices) / math.sqrt(query.shape[-1])
    return F.scaled_dot_product_attention(
        query, key, value, attn_mask=bias.masked_fill(~allowed[None, None], -float("inf"))
    )


def benchmark(options: dict[str, Any]) -> None:
    """Time forward/backward separately from compilation; compare all four input gradients."""
    torch.set_num_threads(2)
    torch.manual_seed(73001)
    torch.compiler.config.recompile_limit = 128
    results = []
    for shape in options["shapes"]:
        batch, turns = shape["batch"], shape["turns"]
        heads, width, tokens, window = 8, 32, 4, 384
        length, memory = turns * tokens, window * tokens
        inputs = tuple(
            torch.randn(*size, device="cuda", dtype=torch.bfloat16, requires_grad=True)
            for size in (
                (batch, heads, length, width),
                (batch, heads, memory + length, width),
                (batch, heads, memory + length, width),
                (batch, heads, length, window + 1),
            )
        )
        steps = torch.arange(window, window + turns, device="cuda").repeat_interleave(tokens)
        key_steps = torch.arange(window + turns, device="cuda").repeat_interleave(tokens)
        gradient = torch.randn_like(inputs[0])
        functions: dict[str, Callable[..., Tensor]] = {
            "dense": torch.compile(dense_attention, fullgraph=True, dynamic=False),
            "fused": torch.compile(relative_attention, fullgraph=True, dynamic=False),
        }
        reference = None
        for name, function in functions.items():
            for backward in (False, True) if turns > 1 else (False,):
                operation = partial(
                    _operation, function, inputs, steps, key_steps, gradient, backward
                )

                values = operation()
                if name == "dense" and backward:
                    reference = tuple(value.detach().clone() for value in values)
                errors = []
                if name == "fused" and backward:
                    assert reference is not None
                    errors = [
                        float((a.detach().float() - b.float()).norm() / b.float().norm())
                        for a, b in zip(values, reference, strict=True)
                    ]
                    if max(errors) > 0.02:
                        raise ValueError(f"relative attention derivative mismatch: {errors}")
                if not all(torch.isfinite(value).all() for value in values):
                    raise ValueError("relative attention returned nonfinite values")
                for _ in range(3):
                    operation()
                torch.cuda.synchronize()
                timings = []
                for _ in range(3):
                    start = torch.cuda.Event(enable_timing=True)  # type: ignore[no-untyped-call]
                    end = torch.cuda.Event(enable_timing=True)  # type: ignore[no-untyped-call]
                    start.record()
                    for _ in range(options["repeats"]):
                        operation()
                    end.record()
                    end.synchronize()
                    timings.append(start.elapsed_time(end) / options["repeats"])
                row = {
                    "name": name,
                    "shape": shape,
                    "backward": backward,
                    "milliseconds": timings,
                    "relative_l2_errors": errors,
                }
                results.append(row)
                write_json(Path(options["output"]), {"options": options, "results": results})
                print(json.dumps(row), flush=True)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="hopper_temporal")
def main(configuration: DictConfig) -> None:
    """Exercise the temporal bias gradient as well as query, key and value gradients."""
    options = OmegaConf.to_container(configuration.benchmark, resolve=True)
    assert isinstance(options, dict)
    benchmark(cast(dict[str, Any], options))


if __name__ == "__main__":
    main()
