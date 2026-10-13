"""Thread-safe CUDA Graph capture shared by concurrent rollout streams."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager

import torch

_CAPTURE_LOCK = threading.RLock()


@contextmanager
def serialized_graph_build() -> Iterator[None]:
    """Protect warmup, synchronization, and capture for one lazy graph."""
    with _CAPTURE_LOCK:
        yield


@contextmanager
def serialized_graph_capture(graph: torch.cuda.CUDAGraph) -> Iterator[None]:
    """Serialize capture while permitting other threads to execute CUDA work."""
    device = torch.cuda.current_device()
    capture_stream = torch.cuda.Stream(device=device)  # type: ignore[no-untyped-call]
    with (
        _CAPTURE_LOCK,
        torch.cuda.device(device),
        torch.cuda.graph(
            graph,
            stream=capture_stream,
            capture_error_mode="thread_local",
        ),
    ):
        yield


def capture_safe_graph_replay(graph: torch.cuda.CUDAGraph) -> None:
    """Enqueue a replay outside any concurrent process-local capture call."""
    with _CAPTURE_LOCK:
        graph.replay()


def clear_cublas_workspaces() -> None:
    """Release persistent H200 BLAS workspaces after all graphs are dead."""
    clear = getattr(torch._C, "_cuda_clearCublasWorkspaces", None)
    if not callable(clear):
        raise RuntimeError("this H200 runtime cannot release cuBLAS workspaces")
    clear()


__all__ = [
    "capture_safe_graph_replay",
    "clear_cublas_workspaces",
    "serialized_graph_build",
    "serialized_graph_capture",
]
