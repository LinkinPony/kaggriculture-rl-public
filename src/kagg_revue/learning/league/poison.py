"""Expose reads of unwritten compiler temporaries in an isolated diagnostic."""

import importlib.util
from pathlib import Path
from typing import Any, cast

import torch
from torch._inductor.codecache import PyCodeCache
from torch._inductor.select_algorithm import extern_kernels


def install(output: Path) -> None:
    """Poison newly allocated float buffers and capture the first corrupt GEMM."""
    for module in PyCodeCache.modules:
        original = getattr(module, "empty_strided_cuda", None)
        if original is None:
            continue

        def allocate(*args: Any, _original: Any = original, **kwargs: Any) -> torch.Tensor:
            result = _original(*args, **kwargs)
            if result.is_floating_point():
                result.fill_(float("nan"))
            return cast(torch.Tensor, result)

        cast(Any, module).empty_strided_cuda = allocate
    original_addmm = cast(Any, extern_kernels).addmm
    count = 0

    def addmm(*args: Any, **kwargs: Any) -> Any:
        nonlocal count
        count += 1
        finite = [bool(value.isfinite().all()) for value in args]
        if not all(finite):
            torch.save({"call": count, "finite": finite, "args": args}, output)
            raise ValueError(f"nonfinite GEMM inputs at call {count}: {finite}")
        result = original_addmm(*args, **kwargs)
        if not bool(result.isfinite().all()):
            torch.save({"call": count, "args": args, "result": result}, output)
            raise ValueError(f"nonfinite GEMM output at call {count}")
        return result

    cast(Any, extern_kernels).addmm = addmm


def reproduce(path: str, output: str) -> None:
    """Run the failing generated reduction with finite synthetic inputs alone."""
    torch.set_num_threads(2)
    torch.cuda.set_device(0)
    spec = importlib.util.spec_from_file_location("diagnostic_generated", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    name = (
        "triton_red_fused__to_copy_add_embedding_native_layer_norm_"
        "native_layer_norm_backward_select_slice_view_63"
    )
    kernel = getattr(module, name)
    torch.manual_seed(63001)
    h = torch.randn(512, 192, device="cuda")
    actions = torch.zeros(512, 276, device="cuda", dtype=torch.int64)
    em = torch.randn(23, 192, device="cuda")
    residual = torch.randn_like(h).bfloat16()
    eq = torch.randn(153, 192, device="cuda")
    weight = torch.randn(192, device="cuda")
    bias = torch.randn(192, device="cuda")
    cases = []
    for poison in (0.0, float("nan"), 123.0):
        buffer = torch.full_like(h, poison)
        outputs = [
            torch.empty_like(h),
            torch.empty_like(h, dtype=torch.bfloat16),
            torch.empty_like(h, dtype=torch.bfloat16),
            torch.empty(512, 1, device="cuda"),
            torch.empty(512, 1, device="cuda"),
        ]
        kernel.run(
            buffer,
            h,
            actions,
            em,
            residual,
            eq,
            weight,
            bias,
            weight,
            bias,
            *outputs,
            512,
            192,
            stream=torch.cuda.current_stream().cuda_stream,
        )
        reference = torch.nn.functional.layer_norm(
            h + em[0] + residual + eq[0], (192,), weight, bias
        ).bfloat16()
        cases.append(
            {
                "fill": poison,
                "finite": bool(outputs[2].isfinite().all()),
                "max_error": (outputs[2] - reference).abs().max().item(),
            }
        )
    from kagg_revue.artifacts.io import write_json

    write_json(Path(output), {"kernel": name, "cases": cases})
    print(cases, flush=True)
