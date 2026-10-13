"""CUDA graph ownership independent of PyTorch's cyclic stream pool."""

import weakref

import torch


def _release(graph: torch.cuda.CUDAGraph, stream: torch.cuda.ExternalStream) -> None:
    """Release graph workspaces before making the stream handle available for reuse."""
    from cuda.bindings import runtime  # type: ignore[import-untyped]

    with torch.cuda.device(stream.device):
        torch.cuda.synchronize(stream.device)
        graph.reset()
        (error,) = runtime.cudaStreamDestroy(stream.cuda_stream)
        if error != runtime.cudaError_t.cudaSuccess:
            raise RuntimeError(f"CUDA capture stream destruction failed: {error}")


class GraphCapture:
    """Own a graph and a nonblocking stream for exactly the same lifetime.

    Pooled torch.cuda.Stream objects wrap after 32 allocations. In affected
    PyTorch builds, resetting any graph clears all cuBLAS workspaces on its
    capture stream, including those referenced by another live graph.
    """

    def __init__(self, device: torch.device) -> None:
        """Allocate outside the pool so temporary evaluation graphs cannot alias us."""
        from cuda.bindings import runtime

        with torch.cuda.device(device):
            error, pointer = runtime.cudaStreamCreateWithFlags(runtime.cudaStreamNonBlocking)
            if error != runtime.cudaError_t.cudaSuccess:
                raise RuntimeError(f"CUDA capture stream creation failed: {error}")
            self.stream = torch.cuda.ExternalStream(  # type: ignore[no-untyped-call]
                int(pointer), device=device
            )
            self.graph = torch.cuda.CUDAGraph()
        self._finalizer = weakref.finalize(self, _release, self.graph, self.stream)
        # Process teardown releases the CUDA context; Python module order is undefined.
        self._finalizer.atexit = False  # type: ignore[misc]

    def close(self) -> None:
        """Synchronize outstanding replays and release the graph before its stream."""
        self._finalizer()
