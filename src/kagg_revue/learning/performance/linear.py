"""Measure Hopper FP8 linear layers at the recurrent learner's real dimensions."""

import copy
import gc
import json
import statistics
from pathlib import Path
from typing import Any, cast

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json


def measure(options: dict[str, Any]) -> None:
    """Include dynamic quantization and all three GEMMs in the training measurement."""
    from torchao.float8 import Float8LinearConfig  # type: ignore[import-not-found]
    from torchao.float8.float8_linear import Float8Linear  # type: ignore[import-not-found]

    torch.set_num_threads(2)
    torch.manual_seed(73001)
    torch.compiler.config.recompile_limit = 128
    results = []
    for rows, inputs, outputs in options["shapes"]:
        layer = torch.nn.Linear(inputs, outputs, device="cuda")
        values = torch.randn(rows, inputs, device="cuda", requires_grad=True)
        gradient = torch.randn(rows, outputs, device="cuda", dtype=torch.bfloat16)
        reference = None
        for recipe in options["recipes"]:
            candidate = copy.deepcopy(layer)
            if recipe != "bf16":
                config = Float8LinearConfig.from_recipe_name(recipe)
                candidate = Float8Linear.from_float(candidate, config=config)
            compiled = torch.compile(candidate, fullgraph=True, dynamic=False)

            def operation(
                module: Any = compiled,
                data: torch.Tensor = values,
                weight: torch.Tensor = candidate.weight,
                grad: torch.Tensor = gradient,
            ) -> tuple[torch.Tensor, ...]:
                with torch.autocast("cuda", dtype=torch.bfloat16):
                    output = module(data)
                gradients = torch.autograd.grad(output, (data, weight), grad)
                return output.detach(), *(item.detach() for item in gradients)

            try:
                actual = operation()
                if reference is None:
                    reference = actual
                errors = [
                    float((a.float() - b.float()).norm() / b.float().norm().clamp_min(1e-6))
                    for a, b in zip(actual, reference, strict=True)
                ]
                finite = all(bool(torch.isfinite(item).all()) for item in actual)
                del actual
                for _ in range(3):
                    operation()
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
                result = {
                    "shape": [rows, inputs, outputs],
                    "recipe": recipe,
                    "finite": finite,
                    "forward_input_gradient_weight_gradient_relative_l2": errors,
                    "milliseconds": timings,
                    "median_ms": statistics.median(timings),
                }
            except Exception as error:
                result = {"shape": [rows, inputs, outputs], "recipe": recipe, "error": str(error)}
            results.append(result)
            write_json(Path(options["output"]), {"options": options, "results": results})
            print(json.dumps(result), flush=True)
            del compiled, candidate, operation
            gc.collect()
        del reference, layer, values, gradient
        gc.collect()
        torch.cuda.empty_cache()


@hydra.main(version_base=None, config_path="../../../../configs", config_name="hopper_linear")
def main(configuration: DictConfig) -> None:
    """Use an isolated optional torchao install without changing the training environment."""
    options = OmegaConf.to_container(configuration.benchmark, resolve=True)
    assert isinstance(options, dict)
    measure(cast(dict[str, Any], options))


if __name__ == "__main__":
    main()
