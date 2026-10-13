"""Fixed-address staging and device behavior storage for effect rollout."""

from __future__ import annotations

from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.effects.data import EffectTensorState
from kagg_revue.policy.effects.schema import EffectArchitecture, EffectSelection

_DISTRIBUTION_CHUNK_ELEMENTS = 4 * 1024 * 1024


def _elements(shape: torch.Size) -> int:
    """Return the element count for one static tensor shape."""
    return int(np.prod(tuple(shape), dtype=np.int64))


class PinnedEffectDecisionStaging:
    """Let native code fill packed pinned buffers consumed by CUDA Graphs."""

    def __init__(
        self,
        architecture: EffectArchitecture,
        rows: int,
        candidate_capacity: int,
        device: torch.device,
    ) -> None:
        """Allocate candidate-bucketed state with fixed secondary axes."""
        if device.type != "cuda" or rows < 1 or candidate_capacity < 1:
            raise ValueError("effect decision staging requires positive CUDA shapes")
        unit_limit = architecture.unit_limit
        market_limit = architecture.maximum_market_orders
        action_fields = architecture.action_field_count
        specifications = {
            "candidate_fields": (
                torch.Size((rows, candidate_capacity, architecture.candidate_field_count)),
                torch.long,
            ),
            "candidate_features": (
                torch.Size((rows, candidate_capacity, architecture.candidate_feature_count)),
                torch.float32,
            ),
            "candidate_mask": (
                torch.Size((rows, candidate_capacity)),
                torch.bool,
            ),
            "jobs": (
                torch.Size((rows, unit_limit, architecture.job_field_count)),
                torch.long,
            ),
            "job_mask": (torch.Size((rows, unit_limit)), torch.bool),
            "work_prefix": (
                torch.Size((rows, unit_limit, action_fields)),
                torch.long,
            ),
            "work_mask": (torch.Size((rows, unit_limit)), torch.bool),
            "market_prefix": (
                torch.Size((rows, market_limit, action_fields)),
                torch.long,
            ),
            "market_mask": (torch.Size((rows, market_limit)), torch.bool),
            "previous_action": (
                torch.Size((rows, unit_limit + market_limit, action_fields)),
                torch.long,
            ),
            "previous_mask": (
                torch.Size((rows, unit_limit + market_limit)),
                torch.bool,
            ),
            "phase": (torch.Size((rows,)), torch.long),
            "work_limit": (torch.Size((rows,)), torch.long),
            "model_rows": (torch.Size((rows,)), torch.long),
        }
        self._device_packs: dict[torch.dtype, Tensor] = {}
        self._host_packs: dict[torch.dtype, Tensor] = {}
        self._device_values: dict[str, Tensor] = {}
        self._host_values: dict[str, Tensor] = {}
        for dtype in (torch.long, torch.float32, torch.bool):
            fields = [
                (name, shape)
                for name, (shape, field_dtype) in specifications.items()
                if field_dtype == dtype
            ]
            pack_size = sum(_elements(shape) for _name, shape in fields)
            device_pack = torch.empty(pack_size, dtype=dtype, device=device)
            host_pack = torch.empty(
                pack_size,
                dtype=dtype,
                device="cpu",
                pin_memory=True,
            )
            self._device_packs[dtype] = device_pack
            self._host_packs[dtype] = host_pack
            offset = 0
            for name, shape in fields:
                elements = _elements(shape)
                self._device_values[name] = device_pack.narrow(0, offset, elements).view(shape)
                self._host_values[name] = host_pack.narrow(0, offset, elements).view(shape)
                offset += elements
        values = self._device_values
        self.state = EffectTensorState(
            candidate_fields=values["candidate_fields"],
            candidate_features=values["candidate_features"],
            candidate_mask=values["candidate_mask"],
            jobs=values["jobs"],
            job_mask=values["job_mask"],
            work_prefix=values["work_prefix"],
            work_mask=values["work_mask"],
            market_prefix=values["market_prefix"],
            market_mask=values["market_mask"],
            previous_action=values["previous_action"],
            previous_mask=values["previous_mask"],
            phase=values["phase"],
            work_limit=values["work_limit"],
        )

    @property
    def model_rows(self) -> Tensor:
        """Return the graph-static mapping into the full turn context."""
        return self._device_values["model_rows"]

    def install(self, prepared_batch: Any) -> None:
        """Pack a prepared native observation and enqueue three coarse uploads."""
        host = self._host_values
        prepared_batch.write_prepared(
            host["candidate_fields"].numpy(),
            host["candidate_features"].numpy(),
            host["candidate_mask"].numpy(),
            host["jobs"].numpy(),
            host["job_mask"].numpy(),
            host["work_prefix"].numpy(),
            host["work_mask"].numpy(),
            host["market_prefix"].numpy(),
            host["market_mask"].numpy(),
            host["previous_action"].numpy(),
            host["previous_mask"].numpy(),
            host["phase"].numpy(),
            host["work_limit"].numpy(),
            host["model_rows"].numpy(),
        )
        for dtype, target in self._device_packs.items():
            target.copy_(self._host_packs[dtype], non_blocking=True)


class EffectBehaviorTape:
    """Keep behavior statistics and compact distributions on the rollout device."""

    def __init__(
        self,
        capacity: int,
        device: torch.device,
        *,
        retain_distributions: bool = True,
    ) -> None:
        """Allocate fixed CUDA storage and one reusable pinned destination."""
        if capacity < 1 or device.type != "cuda":
            raise ValueError("effect behavior tape requires positive CUDA capacity")
        self._device = torch.empty((capacity, 2), dtype=torch.float32, device=device)
        self._host = torch.empty(
            (capacity, 2),
            dtype=torch.float32,
            device="cpu",
            pin_memory=True,
        )
        self._size = 0
        self._retain_distributions = retain_distributions
        self._distribution_chunks: dict[int, list[Tensor]] = {}
        self._distribution_sizes: dict[int, int] = {}
        self._distribution_events: list[tuple[int, int, int, int]] = []

    @property
    def capacity(self) -> int:
        """Return the maximum number of recorded policy factors."""
        return int(self._device.shape[0])

    @property
    def retain_distributions(self) -> bool:
        """Return whether exact candidate distributions are being retained."""
        return self._retain_distributions

    def reset(self) -> None:
        """Start another rollout without changing any storage address."""
        self._size = 0
        self._distribution_sizes.clear()
        self._distribution_events.clear()

    @staticmethod
    def _distribution_chunk_rows(width: int) -> int:
        """Bound one allocation while keeping rollout copies coarse."""
        return max(1, _DISTRIBUTION_CHUNK_ELEMENTS // width)

    def _append_distribution(self, values: Tensor, live_rows: int) -> int:
        """Append one graph-width distribution without rollout-wide padding."""
        if values.ndim != 2 or values.shape[0] < live_rows:
            raise ValueError("effect behavior distribution rows do not align")
        if values.device != self._device.device or values.dtype != torch.float32:
            raise ValueError("effect behavior distribution changed its device ABI")
        width = int(values.shape[1])
        if width < 1:
            raise ValueError("effect behavior distribution width must be positive")
        chunk_rows = self._distribution_chunk_rows(width)
        chunks = self._distribution_chunks.setdefault(width, [])
        start = self._distribution_sizes.get(width, 0)
        destination = start
        source = 0
        while source < live_rows:
            chunk_index, chunk_offset = divmod(destination, chunk_rows)
            if chunk_index == len(chunks):
                chunks.append(
                    torch.empty(
                        (chunk_rows, width),
                        dtype=torch.float32,
                        device=self._device.device,
                    )
                )
            chunk = chunks[chunk_index]
            copied = min(live_rows - source, chunk_rows - chunk_offset)
            chunk[chunk_offset : chunk_offset + copied].copy_(values[source : source + copied])
            source += copied
            destination += copied
        self._distribution_sizes[width] = start + live_rows
        return start

    def append(self, selection: EffectSelection, live_rows: int) -> int:
        """Append graph outputs asynchronously and return their native index."""
        stop = self._size + live_rows
        if live_rows < 1 or stop > self._device.shape[0]:
            raise RuntimeError("effect behavior tape exceeded its configured capacity")
        target = self._device[self._size : stop]
        target[:, 0].copy_(selection.log_probability[:live_rows])
        target[:, 1].copy_(selection.value[:live_rows])
        offset = self._size
        if self._retain_distributions:
            distribution_offset = self._append_distribution(
                selection.candidate_log_probabilities,
                live_rows,
            )
            self._distribution_events.append(
                (
                    offset,
                    live_rows,
                    int(selection.candidate_log_probabilities.shape[1]),
                    distribution_offset,
                )
            )
        self._size = stop
        return offset

    def export(self) -> dict[str, Any] | NDArray[np.float32]:
        """Perform the only behavior D2H transfers at the rollout boundary."""
        if self._size < 1:
            raise RuntimeError("effect behavior tape is empty")
        self._host[: self._size].copy_(self._device[: self._size], non_blocking=True)
        if not self._retain_distributions:
            torch.cuda.current_stream(self._device.device).synchronize()
            return self._host.numpy()[: self._size].copy()
        distribution_hosts: dict[int, Tensor] = {}
        for width, size in sorted(self._distribution_sizes.items()):
            host = torch.empty(
                (size, width),
                dtype=torch.float32,
                device="cpu",
                pin_memory=True,
            )
            chunk_rows = self._distribution_chunk_rows(width)
            for chunk_index, chunk in enumerate(self._distribution_chunks[width]):
                start = chunk_index * chunk_rows
                if start >= size:
                    break
                stop = min(size, start + chunk_rows)
                host[start:stop].copy_(chunk[: stop - start], non_blocking=True)
            distribution_hosts[width] = host
        distribution_width = np.empty(self._size, dtype=np.int32)
        distribution_row = np.empty(self._size, dtype=np.int64)
        for offset, rows, width, source in self._distribution_events:
            stop = offset + rows
            distribution_width[offset:stop] = width
            distribution_row[offset:stop] = np.arange(source, source + rows)
        torch.cuda.current_stream(self._device.device).synchronize()
        return {
            "statistics": self._host.numpy()[: self._size].copy(),
            "distribution_width": distribution_width,
            "distribution_row": distribution_row,
            "candidate_log_probabilities": {
                width: host.numpy().copy() for width, host in distribution_hosts.items()
            },
        }


class PinnedEffectMaskStaging:
    """Stage only the changing mask for repeated ranked-work selection."""

    def __init__(
        self, rows: int, candidates: int, device: torch.device, *, prefix_capacity: int = 0
    ) -> None:
        """Allocate fixed host/device mask and row-map buffers."""
        if device.type != "cuda" or rows < 1 or candidates < 1:
            raise ValueError("effect mask staging requires positive CUDA shapes")
        self.candidate_mask = torch.empty((rows, candidates), dtype=torch.bool, device=device)
        self.model_rows = torch.empty((rows,), dtype=torch.long, device=device)
        self._candidate_mask = torch.empty(
            (rows, candidates),
            dtype=torch.bool,
            device="cpu",
            pin_memory=True,
        )
        self._model_rows = torch.empty((rows,), dtype=torch.long, device="cpu", pin_memory=True)
        self.prefix = torch.empty((rows, prefix_capacity, 6), dtype=torch.long, device=device)
        self.prefix_mask = torch.empty((rows, prefix_capacity), dtype=torch.bool, device=device)
        self._prefix = torch.empty(self.prefix.shape, dtype=torch.long, pin_memory=True)
        self._prefix_mask = torch.empty(self.prefix_mask.shape, dtype=torch.bool, pin_memory=True)

    def install(self, prepared_batch: Any) -> None:
        """Fill the exact native mask and enqueue its two compact uploads."""
        prepared_batch.write_prepared_mask(
            self._candidate_mask.numpy(),
            self._model_rows.numpy(),
        )
        if self.prefix.shape[1]:
            prepared_batch.write_prepared_prefix(self._prefix.numpy(), self._prefix_mask.numpy())
            self.prefix.copy_(self._prefix, non_blocking=True)
            self.prefix_mask.copy_(self._prefix_mask, non_blocking=True)
        self.candidate_mask.copy_(self._candidate_mask, non_blocking=True)
        self.model_rows.copy_(self._model_rows, non_blocking=True)


class PinnedEffectSelectionStaging:
    """Synchronize only the selected candidate needed by native transition."""

    def __init__(self, selection: EffectSelection) -> None:
        """Allocate one stable pinned index vector."""
        self._selection = selection
        self._indices = torch.empty(
            selection.indices.shape,
            dtype=selection.indices.dtype,
            device="cpu",
            pin_memory=True,
        )

    def copy_selected(
        self,
        live_rows: int,
        behavior_tape: EffectBehaviorTape,
    ) -> tuple[NDArray[np.int64], int]:
        """Return native selections while retaining behavior scalars on CUDA."""
        if live_rows < 1 or live_rows > self._selection.indices.shape[0]:
            raise ValueError("effect graph output row count is invalid")
        self._indices.copy_(self._selection.indices, non_blocking=True)
        offset = behavior_tape.append(self._selection, live_rows)
        torch.cuda.current_stream(self._selection.indices.device).synchronize()
        return self._indices.numpy()[:live_rows], offset


__all__ = [
    "EffectBehaviorTape",
    "PinnedEffectDecisionStaging",
    "PinnedEffectMaskStaging",
    "PinnedEffectSelectionStaging",
]
