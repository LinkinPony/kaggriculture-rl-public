"""Compare Hopper attention kernels at the production entity tensor shapes."""

import gc
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from torch import Tensor
from torch.nn import functional as F
from torch.nn.attention.flex_attention import FlexKernelOptions, flex_attention

from kagg_revue.artifacts.io import write_json


def aligned_attention(query: Tensor, key: Tensor, value: Tensor, valid: Tensor) -> Tensor:
    """Benchmark masking through a fixed extra coordinate and 64-wide heads."""
    width = query.shape[-1]
    query = F.pad(torch.cat((query, torch.ones_like(query[..., :1])), -1), (0, 63 - width))
    penalty = torch.where(valid[:, None, :, None], 0.0, torch.finfo(key.dtype).min).to(key.dtype)
    penalty = penalty.expand(-1, key.shape[1], -1, -1)
    key = F.pad(torch.cat((key, penalty), -1), (0, 63 - width))
    value = F.pad(value, (0, 64 - width))
    result = F.scaled_dot_product_attention(query, key, value, scale=width**-0.5)
    return result[..., :width] * valid.any(-1)[:, None, None, None]


def sdpa(query: Tensor, key: Tensor, value: Tensor, valid: Tensor) -> Tensor:
    """Use PyTorch's native masked SDPA backend selection."""
    return F.scaled_dot_product_attention(query, key, value, valid[:, None, None, :])


def attention(
    options: FlexKernelOptions, *, contiguous: bool = False, pad_head: bool = False
) -> Callable[..., Tensor]:
    """Close over static kernel controls without changing the attention equation."""

    def operation(query: Tensor, key: Tensor, value: Tensor, valid: Tensor) -> Tensor:
        width = query.shape[-1]
        if pad_head:
            padding = 2 ** (width - 1).bit_length() - width
            query, key, value = (F.pad(item, (0, padding)) for item in (query, key, value))
        if contiguous:
            query, key, value = (item.contiguous() for item in (query, key, value))

        def mask(score: Tensor, batch: Tensor, head: Tensor, q: Tensor, k: Tensor) -> Tensor:
            return torch.where(valid[batch, k], score, -float("inf"))

        return flex_attention(
            query, key, value, score_mod=mask, scale=width**-0.5, kernel_options=options
        )[..., :width]

    return operation


def measure(options: dict[str, Any]) -> None:
    """Check outputs and Q/K/V derivatives before timing warmed kernel variants."""
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise ValueError("H200 experiments require CUDA_VISIBLE_DEVICES=1")
    if "H200" not in torch.cuda.get_device_name(0):
        raise ValueError("this benchmark is specific to H200")
    torch.set_num_threads(2)
    torch.manual_seed(73001)
    torch.compiler.config.recompile_limit = 128
    backward = options.get("backward", True)
    rows = []
    for width in options["widths"]:
        torch.backends.cuda.enable_cudnn_sdp(True)
        torch.backends.cuda.enable_flash_sdp(True)
        torch.backends.cuda.enable_mem_efficient_sdp(True)
        torch.backends.cuda.enable_math_sdp(True)
        batch, tokens, heads = options["batch"], options["tokens"], options["heads"]
        base = torch.randn(batch, tokens, 3, heads, width, device="cuda", dtype=torch.bfloat16)
        inputs = tuple(x.detach().requires_grad_(backward) for x in base.permute(2, 0, 3, 1, 4))
        valid = torch.rand(batch, tokens, device="cuda") > 0.3
        valid[:, :201] = True
        gradient = torch.randn_like(inputs[0])
        expected = F.scaled_dot_product_attention(
            inputs[0], inputs[1], inputs[2], attn_mask=valid[:, None, None, :]
        )
        reference = (
            expected.detach(),
            *(torch.autograd.grad(expected, inputs, gradient) if backward else ()),
        )
        for variant in options["variants"]:
            torch.backends.cuda.enable_cudnn_sdp(variant["name"] != "aligned_flash")
            torch.backends.cuda.enable_flash_sdp(variant["name"] != "cudnn")
            torch.backends.cuda.enable_mem_efficient_sdp(variant["name"] != "cudnn")
            torch.backends.cuda.enable_math_sdp(variant["name"] != "cudnn")
            kernel = cast(FlexKernelOptions, variant["options"])
            function = torch.compile(
                aligned_attention
                if variant["name"].startswith("aligned")
                else sdpa
                if variant["name"] in {"sdpa", "cudnn"}
                else attention(
                    kernel,
                    contiguous=variant.get("contiguous", False),
                    pad_head=variant.get("pad_head", False),
                ),
                fullgraph=True,
                dynamic=False,
            )
            try:
                result = function(*inputs, valid)
                derivatives = torch.autograd.grad(result, inputs, gradient) if backward else ()
                errors = [
                    float((a.detach().float() - b.float()).norm() / b.float().norm())
                    for a, b in zip((result, *derivatives), reference, strict=True)
                ]
                if not all(torch.isfinite(x).all() for x in (result, *derivatives)):
                    raise ValueError("attention produced nonfinite values")
                if max(errors) > 0.015:
                    raise ValueError(f"BF16 attention relative L2 error exceeds 0.015: {errors}")
                for _ in range(3):
                    result = function(*inputs, valid)
                    if backward:
                        torch.autograd.grad(result, inputs, gradient)
                torch.cuda.synchronize()
                timings = []
                for _ in range(3):
                    start = torch.cuda.Event(enable_timing=True)  # type: ignore[no-untyped-call]
                    end = torch.cuda.Event(enable_timing=True)  # type: ignore[no-untyped-call]
                    start.record()
                    for _ in range(options["repeats"]):
                        result = function(*inputs, valid)
                        if backward:
                            torch.autograd.grad(result, inputs, gradient)
                    end.record()
                    end.synchronize()
                    timings.append(start.elapsed_time(end) / options["repeats"])
                row = {
                    "name": variant["name"],
                    "width": width,
                    "options": kernel,
                    "milliseconds": timings,
                    "relative_l2_errors": errors,
                    "passed": True,
                }
                del result, derivatives
            except Exception as error:
                row = {
                    "name": variant["name"],
                    "width": width,
                    "passed": False,
                    "error": str(error),
                }
            rows.append(row)
            write_json(Path(options["output"]), {"options": options, "results": rows})
            print(json.dumps(row), flush=True)
            del function
            gc.collect()
        del reference, expected, gradient, inputs, base, valid
        gc.collect()
        torch.cuda.empty_cache()


@hydra.main(version_base=None, config_path="../../../../configs", config_name="hopper_kernels")
def main(configuration: DictConfig) -> None:
    """Run only on the GPU exposed by the benchmark launch environment."""
    options = OmegaConf.to_container(configuration.benchmark, resolve=True)
    assert isinstance(options, dict)
    measure(cast(dict[str, Any], options))


if __name__ == "__main__":
    main()
