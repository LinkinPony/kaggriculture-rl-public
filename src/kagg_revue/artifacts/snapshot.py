"""Immutable host snapshots before live optimizer tensors can change again."""

import copy
from dataclasses import dataclass
from typing import Any

import torch


@dataclass
class Snapshot:
    """Private CPU storage and the completion event for ordered CUDA copies."""

    payload: dict[str, Any]
    ready: Any = None

    def wait(self) -> dict[str, Any]:
        """Make pinned destinations readable by a background serializer."""
        if self.ready is not None:
            self.ready.synchronize()
        return self.payload


def capture(payload: dict[str, Any], device: torch.device) -> Snapshot:
    """Copy each storage once, preserving aliases, strides and the caller's CUDA order.

    CUDA copies use the current training stream. Later optimizer work on that
    stream cannot overwrite their sources before the copies finish. Only the
    background writer waits for the completion event.
    """
    memo: dict[int, Any] = {}
    storages: dict[tuple[torch.device, int, int], torch.Tensor] = {}
    used_cuda = False

    def visit(value: Any) -> None:
        nonlocal used_cuda
        if isinstance(value, torch.Tensor):
            if id(value) in memo:
                return
            if value.layout != torch.strided or value.is_conj() or value.is_neg():
                raise ValueError("checkpoint snapshot requires ordinary dense tensor views")
            source = value.untyped_storage()
            key = (value.device, source.data_ptr(), source.nbytes())
            if key not in storages:
                if value.device.type != "cpu" and value.device != device:
                    raise ValueError("checkpoint tensor belongs to another accelerator")
                cuda = value.device.type == "cuda"
                used_cuda |= cuda
                host = torch.empty(source.nbytes(), dtype=torch.uint8, pin_memory=cuda)
                view = torch.empty(0, dtype=torch.uint8, device=value.device).set_(
                    source, 0, (source.nbytes(),), (1,)
                )
                host.copy_(view, non_blocking=cuda)
                storages[key] = host
            memo[id(value)] = torch.empty(0, dtype=value.dtype).set_(
                storages[key].untyped_storage(),
                value.storage_offset(),
                value.size(),
                value.stride(),
            )
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                visit(item)

    visit(payload)
    ready = None
    if used_cuda:
        ready = torch.cuda.Event()  # type: ignore[no-untyped-call]
        ready.record(torch.cuda.current_stream(device))
    return Snapshot(copy.deepcopy(payload, memo), ready)
