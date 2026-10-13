"""Compare equivalent BF16 GEMM implementations at the selected H200 learner shapes."""

import gc
import json
import os
from pathlib import Path
from typing import Any, cast

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.policy.compilation import options as compiler_options


def measure(options: dict[str, Any]) -> None:
    """Include input/weight gradients, checking each candidate against native cuBLAS."""
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise ValueError("H200 experiments require CUDA_VISIBLE_DEVICES=1")
    if "H200" not in torch.cuda.get_device_name(0):
        raise ValueError("this benchmark is specific to H200")
    torch.set_num_threads(2)
    torch.manual_seed(73001)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    torch.compiler.config.recompile_limit = 128
    device = torch.device("cuda:0")
    results: list[dict[str, Any]] = []
    for rows, inputs, outputs, dtype in options["shapes"]:
        layer = torch.nn.Linear(inputs, outputs, device=device)
        values = torch.randn(
            rows, inputs, device=device, dtype=getattr(torch, dtype), requires_grad=True
        )
        gradient = torch.randn(rows, outputs, device=device, dtype=torch.bfloat16)

        def operation(
            module: Any,
            data: torch.Tensor = values,
            model: torch.nn.Linear = layer,
            grad: torch.Tensor = gradient,
        ) -> tuple[torch.Tensor, ...]:
            with torch.autocast("cuda", dtype=torch.bfloat16):
                output = module(data)
            derivatives = torch.autograd.grad(output, (data, model.weight, model.bias), grad)
            return output.detach(), *(item.detach() for item in derivatives)

        reference = operation(layer)
        for variant in options["variants"]:
            controls = {**compiler_options(device), **variant["options"]}
            compiled = torch.compile(layer, fullgraph=True, dynamic=False, options=controls)
            try:
                actual = operation(compiled)
                errors = [
                    float((a.float() - b.float()).norm() / b.float().norm().clamp_min(1e-6))
                    for a, b in zip(actual, reference, strict=True)
                ]
                if not all(bool(torch.isfinite(item).all()) for item in actual):
                    raise ValueError("GEMM produced nonfinite output or gradients")
                if max(errors) > 0.015:
                    raise ValueError(f"relative L2 error exceeds 0.015: {errors}")
                del actual
                for _ in range(3):
                    operation(compiled)
                timings = []
                for _ in range(3):
                    start = torch.cuda.Event(enable_timing=True)  # type: ignore[no-untyped-call]
                    end = torch.cuda.Event(enable_timing=True)  # type: ignore[no-untyped-call]
                    start.record()
                    for _ in range(options["repeats"]):
                        operation(compiled)
                    end.record()
                    end.synchronize()
                    timings.append(start.elapsed_time(end) / options["repeats"])
                row = {
                    "shape": [rows, inputs, outputs],
                    "input_dtype": dtype,
                    "name": variant["name"],
                    "compiler": controls,
                    "milliseconds": timings,
                    "relative_l2_errors": errors,
                    "passed": True,
                }
            except Exception as error:
                row = {
                    "shape": [rows, inputs, outputs],
                    "name": variant["name"],
                    "passed": False,
                    "error": str(error),
                }
            results.append(row)
            write_json(Path(options["output"]), {"options": options, "results": results})
            print(json.dumps(row), flush=True)
            del compiled
            gc.collect()
        del reference, operation, layer, values, gradient
        gc.collect()
        torch.cuda.empty_cache()


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="hopper_compact_matmul"
)
def main(configuration: DictConfig) -> None:
    """Resolve bounded compiler candidates without changing the model or training process."""
    options = OmegaConf.to_container(configuration.benchmark, resolve=True)
    assert isinstance(options, dict)
    measure(cast(dict[str, Any], options))


if __name__ == "__main__":
    main()
