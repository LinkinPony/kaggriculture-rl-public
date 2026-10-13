"""Numerical and timing checks for the league's real attention tensor shapes."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig
from torch import Tensor
from torch.nn import functional as F

from kagg_revue.artifacts.io import write_json
from kagg_revue.policy.spatial.attention import masked_attention


@hydra.main(version_base=None, config_path="../../../../configs", config_name="attention_benchmark")
def main(config: DictConfig) -> None:
    """Compare forward and analytical gradients against the existing SDPA backend."""
    torch.set_num_threads(2)
    torch.backends.cuda.enable_cudnn_sdp(False)
    torch.manual_seed(74019)
    compiled = torch.compile(masked_attention, fullgraph=True, dynamic=False)
    report = []
    for batch in config.batches:
        for width in config.widths:
            base = torch.randn(batch, 286, 3, 4, width, device="cuda", dtype=torch.bfloat16)
            inputs = tuple(x.detach().requires_grad_() for x in base.permute(2, 0, 3, 1, 4))
            valid = torch.rand(batch, 286, device="cuda") > 0.3
            valid[:, 0] = True
            gradient = torch.randn_like(inputs[0])
            functions: dict[str, Callable[..., Tensor]] = {
                "sdpa": lambda q, k, v, valid: F.scaled_dot_product_attention(
                    q, k, v, valid[:, None, None, :]
                ),
                "flex": compiled,
            }
            row: dict[str, Any] = {"batch": batch, "head_width": width}
            reference = None
            for name, function in functions.items():
                result = function(*inputs, valid)
                gradients = torch.autograd.grad(result, inputs, gradient)
                values = (result, *gradients)
                if reference is None:
                    reference = tuple(x.detach().clone() for x in values)
                errors = []
                for actual, expected in zip(values, reference, strict=True):
                    if not bool(actual.isfinite().all()):
                        raise ValueError("nonfinite masked attention")
                    errors.append(
                        float(
                            (actual.detach().float() - expected.float()).norm()
                            / expected.float().norm()
                        )
                    )
                if max(errors) > 0.015:
                    raise ValueError(f"attention forward/gradient disagreement: {errors}")
                for _ in range(3):
                    result = function(*inputs, valid)
                    torch.autograd.grad(result, inputs, gradient)
                torch.cuda.synchronize()
                start, end = (
                    torch.cuda.Event(enable_timing=True),  # type: ignore[no-untyped-call]
                    torch.cuda.Event(enable_timing=True),  # type: ignore[no-untyped-call]
                )
                start.record()
                for _ in range(20):
                    result = function(*inputs, valid)
                end.record()
                end.synchronize()
                forward_ms = start.elapsed_time(end) / 20
                start.record()
                for _ in range(20):
                    result = function(*inputs, valid)
                    torch.autograd.grad(result, inputs, gradient)
                end.record()
                end.synchronize()
                row[name] = {
                    "forward_ms": forward_ms,
                    "forward_backward_ms": start.elapsed_time(end) / 20,
                    "relative_l2_errors": errors,
                }
            report.append(row)
            write_json(Path(config.output), report)
            print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
