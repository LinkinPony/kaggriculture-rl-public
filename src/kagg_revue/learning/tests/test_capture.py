"""Regression checks for graph workspace ownership across stream-pool wraparound."""

import gc

import pytest
import torch

from kagg_revue.policy.capture import GraphCapture


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA graph lifecycle regression")
def test_temporary_graphs_cannot_release_a_live_graph_workspace() -> None:
    """Replay a surviving GEMM after more than one pooled stream cycle is destroyed."""
    device = torch.device("cuda:0")
    left = torch.ones((32768, 640), device=device, dtype=torch.bfloat16)
    right = torch.ones((640, 640), device=device, dtype=torch.bfloat16)
    survivor = GraphCapture(device)
    with torch.cuda.stream(survivor.stream):
        left @ right
        with torch.cuda.graph(survivor.graph, stream=survivor.stream):
            output = left @ right
    for _ in range(40):
        pooled = torch.cuda.Stream()  # type: ignore[no-untyped-call]
        temporary = GraphCapture(device)
        assert survivor.stream.cuda_stream not in (
            temporary.stream.cuda_stream,
            pooled.cuda_stream,
        )
        with torch.cuda.stream(temporary.stream):
            left @ right
            with torch.cuda.graph(temporary.graph, stream=temporary.stream):
                discarded = left @ right
            temporary.graph.replay()
        del temporary, discarded
    gc.collect()
    torch.cuda.empty_cache()
    survivor.graph.replay()
    torch.cuda.synchronize(device)
    torch.testing.assert_close(output, torch.full_like(output, 640), rtol=0, atol=0)
    survivor.close()
    survivor.close()
