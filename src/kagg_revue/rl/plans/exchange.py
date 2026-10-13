"""Persistent pinned-host and fixed-device buffers for plan inference."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.plans import PlanInputs
from kagg_revue.policy.plans.observation import (
    BOARD_SHAPE,
    ECONOMIC_STATE_FEATURES,
    GLOBAL_FEATURES,
    UNIT_SHAPE,
)


@dataclass(frozen=True)
class _StagingBuffer:
    host: Tensor
    device: Tensor


class PlanTensorExchange:
    """Reuse fixed CUDA addresses while native code writes pinned arrays."""

    def __init__(
        self,
        device: torch.device,
        *,
        decision_capacity: int,
        inference_capacity: int,
    ) -> None:
        """Allocate lazily within authenticated decision/inference capacities."""
        if device.type != "cuda":
            raise ValueError("structured-plan tensor exchange requires CUDA")
        if decision_capacity < 1 or inference_capacity < 1:
            raise ValueError("structured-plan tensor capacities must be positive")
        self._device = device
        self._decision_capacity = decision_capacity
        self._inference_capacity = inference_capacity
        self._native: dict[str, Tensor] = {}
        self._staging: dict[str, _StagingBuffer] = {}

    @staticmethod
    def _torch_dtype(dtype: np.dtype[Any] | type[np.generic]) -> torch.dtype:
        normalized = np.dtype(dtype)
        result = {
            np.dtype(np.float16): torch.float16,
            np.dtype(np.float32): torch.float32,
            np.dtype(np.int32): torch.int32,
            np.dtype(np.int64): torch.int64,
            np.dtype(np.bool_): torch.bool,
        }.get(normalized)
        if result is None:
            raise TypeError(f"unsupported structured-plan staging dtype: {normalized}")
        return result

    def _native_buffer(
        self,
        name: str,
        trailing_shape: tuple[int, ...],
        dtype: np.dtype[Any] | type[np.generic],
    ) -> Tensor:
        expected = (self._decision_capacity, *trailing_shape)
        value = self._native.get(name)
        torch_dtype = self._torch_dtype(dtype)
        if value is None:
            value = torch.empty(
                expected,
                dtype=torch_dtype,
                device="cpu",
                pin_memory=True,
            )
            self._native[name] = value
        elif value.shape != expected or value.dtype != torch_dtype:
            raise ValueError("structured-plan native staging ABI changed")
        return value

    def native_observations(self, batch: int) -> dict[str, NDArray[Any]]:
        """Expose pinned exact-size views to the native compact-into encoder."""
        if not 0 <= batch <= self._decision_capacity:
            raise ValueError("structured-plan ready batch exceeds native capacity")
        values = {
            "board": self._native_buffer("board", BOARD_SHAPE, np.float16),
            "units": self._native_buffer("units", UNIT_SHAPE, np.float16),
            "global_features": self._native_buffer(
                "global_features",
                (GLOBAL_FEATURES,),
                np.float32,
            ),
            "unit_counts": self._native_buffer("unit_counts", (), np.int64),
            "economic_state": self._native_buffer(
                "economic_state",
                (ECONOMIC_STATE_FEATURES,),
                np.int32,
            ),
        }
        return {
            name: value[:batch].numpy()
            for name, value in values.items()
        }

    def _staging_buffer(
        self,
        name: str,
        trailing_shape: tuple[int, ...],
        dtype: np.dtype[Any] | type[np.generic],
    ) -> _StagingBuffer:
        expected = (self._inference_capacity, *trailing_shape)
        value = self._staging.get(name)
        torch_dtype = self._torch_dtype(dtype)
        if value is None:
            host = torch.empty(
                expected,
                dtype=torch_dtype,
                device="cpu",
                pin_memory=True,
            )
            value = _StagingBuffer(
                host=host,
                device=torch.empty(expected, dtype=torch_dtype, device=self._device),
            )
            self._staging[name] = value
        elif value.host.shape != expected or value.host.dtype != torch_dtype:
            raise ValueError("structured-plan inference staging ABI changed")
        return value

    @staticmethod
    def _contiguous_rows(rows: slice | NDArray[np.int64]) -> slice | None:
        if isinstance(rows, slice):
            return rows
        if rows.size == 0:
            return slice(0, 0)
        start = int(rows[0])
        if np.array_equal(rows, np.arange(start, start + rows.size, dtype=np.int64)):
            return slice(start, start + rows.size)
        return None

    @staticmethod
    def _row_count(rows: slice | NDArray[np.int64], source_rows: int) -> int:
        if isinstance(rows, np.ndarray):
            return int(rows.size)
        start, stop, step = rows.indices(source_rows)
        return len(range(start, stop, step))

    def _stage_array(
        self,
        name: str,
        source: NDArray[Any],
        rows: slice | NDArray[np.int64],
    ) -> Tensor:
        batch = self._row_count(rows, source.shape[0])
        if batch > self._inference_capacity:
            raise ValueError("structured-plan inference batch exceeds staging capacity")
        staging = self._staging_buffer(name, source.shape[1:], source.dtype)
        np.copyto(staging.host[:batch].numpy(), source[rows])
        staging.device[:batch].copy_(staging.host[:batch], non_blocking=True)
        return staging.device[:batch]

    def _stage_native(
        self,
        name: str,
        source: NDArray[Any],
        rows: slice | NDArray[np.int64],
    ) -> Tensor:
        batch = self._row_count(rows, source.shape[0])
        if batch > self._inference_capacity:
            raise ValueError("structured-plan inference batch exceeds staging capacity")
        staging = self._staging_buffer(f"input_{name}", source.shape[1:], source.dtype)
        contiguous = self._contiguous_rows(rows)
        native = self._native.get(name)
        if (
            contiguous is not None
            and native is not None
            and np.shares_memory(source, native.numpy())
        ):
            selected = native[contiguous]
            staging.device[:batch].copy_(selected, non_blocking=True)
        else:
            np.copyto(staging.host[:batch].numpy(), source[rows])
            staging.device[:batch].copy_(staging.host[:batch], non_blocking=True)
        return staging.device[:batch]

    def inputs(
        self,
        panel: Mapping[str, Any],
        rich: Mapping[str, NDArray[Any]],
        events: NDArray[np.float32],
        rows: slice | NDArray[np.int64],
    ) -> PlanInputs:
        """Asynchronously upload one inference row selection into fixed buffers."""
        return PlanInputs(
            board=self._stage_native("board", rich["board"], rows),
            units=self._stage_native("units", rich["units"], rows),
            global_features=self._stage_native(
                "global_features",
                rich["global_features"],
                rows,
            ),
            economic_state=self._stage_native(
                "economic_state",
                rich["economic_state"],
                rows,
            ),
            features=self._stage_array(
                "features",
                np.asarray(panel["features"], dtype=np.float32),
                rows,
            ),
            journal=self._stage_array(
                "journal",
                np.asarray(panel["journal"], dtype=np.float32),
                rows,
            ),
            events=self._stage_array("events", events, rows),
            active_lines=self._stage_array(
                "active_lines",
                np.asarray(panel["active_lines"], dtype=np.int64),
                rows,
            ),
            active_line_mask=self._stage_array(
                "active_line_mask",
                np.asarray(panel["active_line_mask"], dtype=np.bool_),
                rows,
            ),
            global_plan=self._stage_array(
                "global_plan",
                np.asarray(panel["global_plan"], dtype=np.int64),
                rows,
            ),
        )


__all__ = ["PlanTensorExchange"]
