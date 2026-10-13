"""Pinned host staging for native intent observations and CUDA graphs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.intents.data import IntentTensorState
from kagg_revue.policy.intents.schema import IntentSelection

_NATIVE_FIELDS = {
    "candidate_fields": "candidate_fields",
    "candidate_features": "candidate_features",
    "candidate_mask": "candidate_mask",
    "ledger": "ledger",
    "status": "status",
    "work_priorities": "work_priorities",
    "work_orders": "work_orders",
    "work_mask": "work_mask",
    "positions": "positions",
    "market_prefix": "market_prefix",
    "phase": "phase",
}


def _pinned_like(value: Tensor) -> Tensor:
    return torch.empty(
        value.shape,
        dtype=value.dtype,
        device="cpu",
        pin_memory=True,
    )


def _stage_padded_rows(target: Tensor, source: object, live_rows: int) -> None:
    """Pad a native tensor's rows and optional width without allocations."""
    values = np.asarray(source)
    if values.ndim != target.ndim or values.shape[0] != live_rows:
        raise ValueError("native intent staging rank or row count changed")
    if any(
        source_width > target_width
        for source_width, target_width in zip(values.shape[1:], target.shape[1:], strict=True)
    ):
        raise ValueError("native intent observation exceeds its graph bucket")
    destination = target.numpy()
    destination.fill(0)
    slices = (slice(0, live_rows),) + tuple(slice(0, width) for width in values.shape[1:])
    np.copyto(destination[slices], values, casting="unsafe")
    if live_rows < target.shape[0]:
        source_slices = (live_rows - 1,) + tuple(slice(0, width) for width in values.shape[1:])
        padding_slices = (slice(live_rows, None),) + tuple(
            slice(0, width) for width in values.shape[1:]
        )
        destination[padding_slices] = destination[source_slices]


class PinnedIntentDecisionStaging:
    """Stage variable native tensors into one fixed graph specialization."""

    def __init__(
        self,
        state: IntentTensorState,
        model_rows: Tensor,
        device_packs: dict[torch.dtype, Tensor],
    ) -> None:
        """Allocate persistent pinned mirrors for graph-owned CUDA tensors."""
        self._state = state
        self._model_rows = model_rows
        self._device_packs = device_packs
        self._host_packs = {
            dtype: torch.empty(
                pack.shape,
                dtype=dtype,
                device="cpu",
                pin_memory=True,
            )
            for dtype, pack in device_packs.items()
        }
        self._host = {
            name: self._host_view(getattr(state, name)) for name in state.__dataclass_fields__
        }
        self._model_rows_host = self._host_view(model_rows)

    def _host_view(self, value: Tensor) -> Tensor:
        """Mirror one packed device view at the same element offset."""
        return (
            self._host_packs[value.dtype]
            .narrow(
                0,
                value.storage_offset(),
                value.numel(),
            )
            .view(value.shape)
        )

    def _upload(self) -> None:
        """Copy all intent fields in three contiguous asynchronous transfers."""
        for dtype, device in self._device_packs.items():
            device.copy_(self._host_packs[dtype], non_blocking=True)

    @property
    def model_rows(self) -> Tensor:
        """Expose the padded global-row mapping captured by the graph."""
        return self._model_rows

    def install(
        self,
        raw: Mapping[str, object] | None,
        candidate_mask: NDArray[np.bool_] | None,
        active_rows: NDArray[np.int64],
        prepared_batch: Any | None = None,
    ) -> None:
        """Enqueue one native observation without transient CUDA tensors."""
        live_rows = int(active_rows.size)
        if live_rows < 1 or live_rows > self._model_rows.shape[0]:
            raise ValueError("intent graph received an invalid active row count")
        if prepared_batch is not None:
            hosts = self._host
            prepared_batch.write_prepared(
                hosts["candidate_fields"].numpy(),
                hosts["candidate_features"].numpy(),
                hosts["candidate_mask"].numpy(),
                hosts["ledger"].numpy(),
                hosts["status"].numpy(),
                hosts["work_priorities"].numpy(),
                hosts["work_orders"].numpy(),
                hosts["work_mask"].numpy(),
                hosts["positions"].numpy(),
                hosts["market_prefix"].numpy(),
                hosts["market_mask"].numpy(),
                hosts["phase"].numpy(),
                self._model_rows_host.numpy(),
            )
            self._upload()
            return
        if raw is None or candidate_mask is None:
            raise ValueError("eager intent staging requires a native observation")
        for name, raw_name in _NATIVE_FIELDS.items():
            source: object = candidate_mask if name == "candidate_mask" else raw[raw_name]
            host = self._host[name]
            _stage_padded_rows(host, source, live_rows)

        counts = np.asarray(raw["market_counts"], dtype=np.int64)
        if counts.shape != (live_rows,):
            raise ValueError("native intent market counts changed shape")
        market_mask = self._host["market_mask"]
        mask_values = market_mask.numpy()
        mask_values.fill(False)
        widths = np.arange(mask_values.shape[1], dtype=np.int64)
        mask_values[:live_rows] = widths[None] < counts[:, None]
        if live_rows < mask_values.shape[0]:
            mask_values[live_rows:] = mask_values[live_rows - 1]
        rows = self._model_rows_host.numpy()
        rows[:live_rows] = active_rows
        if live_rows < rows.size:
            rows[live_rows:] = active_rows[-1]
        self._upload()


class PinnedIntentOutputStaging:
    """Copy the three rollout-required policy outputs with one synchronization."""

    def __init__(self, selection: IntentSelection) -> None:
        """Allocate stable pinned output buffers."""
        self._selection = selection
        self._indices = _pinned_like(selection.indices)
        self._log_probability = _pinned_like(selection.log_probability)
        self._value = _pinned_like(selection.value)

    def copy(
        self, live_rows: int
    ) -> tuple[NDArray[np.int64], NDArray[np.float32], NDArray[np.float32]]:
        """Return owned host arrays after one stream synchronization."""
        if live_rows < 1 or live_rows > self._selection.indices.shape[0]:
            raise ValueError("intent graph output row count is invalid")
        self._indices.copy_(self._selection.indices, non_blocking=True)
        self._log_probability.copy_(self._selection.log_probability, non_blocking=True)
        self._value.copy_(self._selection.value, non_blocking=True)
        torch.cuda.current_stream(self._selection.indices.device).synchronize()
        return (
            self._indices.numpy()[:live_rows].copy(),
            self._log_probability.numpy()[:live_rows].copy(),
            self._value.numpy()[:live_rows].copy(),
        )

    def copy_selected(
        self,
        live_rows: int,
        behavior_tape: IntentBehaviorTape,
    ) -> tuple[NDArray[np.int64], int]:
        """Synchronize only native selections while behavior stays on device."""
        if live_rows < 1 or live_rows > self._selection.indices.shape[0]:
            raise ValueError("intent graph output row count is invalid")
        self._indices.copy_(self._selection.indices, non_blocking=True)
        offset = behavior_tape.append(
            self._selection.log_probability,
            self._selection.value,
            live_rows,
        )
        torch.cuda.current_stream(self._selection.indices.device).synchronize()
        return self._indices.numpy()[:live_rows].copy(), offset


class IntentBehaviorTape:
    """Packed device behavior retained until one bulk rollout export."""

    def __init__(self, capacity: int, device: torch.device) -> None:
        """Allocate fixed device and pinned-host storage for two scalar fields."""
        if capacity < 1 or device.type != "cuda":
            raise ValueError("intent behavior tape requires positive CUDA capacity")
        self._device = torch.empty((capacity, 2), dtype=torch.float32, device=device)
        self._host = torch.empty(
            (capacity, 2),
            dtype=torch.float32,
            device="cpu",
            pin_memory=True,
        )
        self._size = 0

    @property
    def capacity(self) -> int:
        """Return the allocated pseudo-step capacity."""
        return int(self._device.shape[0])

    def reset(self) -> None:
        """Start a new rollout without reallocating tape storage."""
        self._size = 0

    def append(self, log_probability: Tensor, value: Tensor, live_rows: int) -> int:
        """Append graph outputs asynchronously and return their stable row offset."""
        stop = self._size + live_rows
        if live_rows < 1 or stop > self._device.shape[0]:
            raise RuntimeError("intent behavior tape exceeded its configured capacity")
        target = self._device[self._size : stop]
        target[:, 0].copy_(log_probability[:live_rows])
        target[:, 1].copy_(value[:live_rows])
        offset = self._size
        self._size = stop
        return offset

    def append_dense(self, log_probability: Tensor, value: Tensor) -> int:
        """Append one step-major fixed transaction trace without host sizing."""
        if log_probability.shape != value.shape or log_probability.ndim != 2:
            raise ValueError("intent dense behavior trace changed shape")
        elements = log_probability.numel()
        stop = self._size + elements
        if stop > self._device.shape[0]:
            raise RuntimeError("intent behavior tape exceeded its configured capacity")
        target = self._device[self._size : stop].view(*log_probability.shape, 2)
        target[..., 0].copy_(log_probability)
        target[..., 1].copy_(value)
        offset = self._size
        self._size = stop
        return offset

    def export(self) -> NDArray[np.float32]:
        """Perform one bulk D2H transfer after the dependent rollout completes."""
        if self._size < 1:
            raise RuntimeError("intent behavior tape is empty")
        self._host[: self._size].copy_(self._device[: self._size], non_blocking=True)
        torch.cuda.current_stream(self._device.device).synchronize()
        return self._host.numpy()[: self._size].copy()


class PinnedIntentTransactionStaging:
    """Fixed native-root staging for one complete device transaction."""

    def __init__(
        self,
        *,
        batch: int,
        cells: int,
        work_capacity: int,
        work_field_count: int,
        market_capacity: int,
        economic_width: int,
        device: torch.device,
    ) -> None:
        """Allocate pinned mirrors and their stable CUDA destinations."""
        specifications = {
            "ledger": ((batch, cells, 8), torch.long),
            "status": ((batch, cells, 4), torch.long),
            "work_orders": ((batch, work_capacity, work_field_count), torch.long),
            "work_mask": ((batch, work_capacity), torch.bool),
            "positions": ((batch, 2, 4), torch.long),
            "market_prefix": ((batch, market_capacity, 3), torch.long),
            "market_mask": ((batch, market_capacity), torch.bool),
            "economic": ((batch, economic_width), torch.int32),
            "inactive_status": ((batch, cells, 2), torch.long),
            "asset_risk": ((batch, cells), torch.bool),
        }
        self.host = {
            name: torch.empty(shape, dtype=dtype, device="cpu", pin_memory=True)
            for name, (shape, dtype) in specifications.items()
        }
        self.device = {
            name: torch.empty(shape, dtype=dtype, device=device)
            for name, (shape, dtype) in specifications.items()
        }

    def install(
        self,
        raw: Mapping[str, object],
        auxiliary: Mapping[str, object],
        economic: NDArray[np.int32],
    ) -> None:
        """Pad one native root and enqueue its coarse H2D transfer."""
        batch = self.host["ledger"].shape[0]
        for name in ("ledger", "status", "work_orders", "work_mask", "positions"):
            _stage_padded_rows(self.host[name], raw[name], batch)
        _stage_padded_rows(self.host["market_prefix"], raw["market_prefix"], batch)
        market_counts = np.asarray(raw["market_counts"], dtype=np.int64)
        market_mask = self.host["market_mask"].numpy()
        market_mask[:] = (
            np.arange(market_mask.shape[1], dtype=np.int64)[None] < market_counts[:, None]
        )
        _stage_padded_rows(self.host["economic"], economic, batch)
        _stage_padded_rows(self.host["inactive_status"], auxiliary["inactive_status"], batch)
        _stage_padded_rows(self.host["asset_risk"], auxiliary["asset_risk"], batch)
        for name, target in self.device.items():
            target.copy_(self.host[name], non_blocking=True)


__all__ = [
    "IntentBehaviorTape",
    "PinnedIntentDecisionStaging",
    "PinnedIntentOutputStaging",
    "PinnedIntentTransactionStaging",
]
