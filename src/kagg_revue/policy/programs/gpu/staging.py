"""Pinned host staging for native conditional-program CUDA graphs."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.programs.encoding import ProgramPreparedContext
from kagg_revue.policy.programs.grammar import (
    NativeProgramMasks,
    ProgramDecisionInputs,
    ProgramPrefixState,
)

_INPUT_FIELDS = {
    "root_features": "root_features",
    "option_features": "option_features",
    "target_reservations": "target_reservations",
}
_SCALAR_FIELDS = {
    "phase": 0,
    "unit_index": 1,
    "market_slot": 2,
    "unit_count": 3,
    "current_x": 4,
    "current_y": 5,
    "forced": 6,
}
_MASK_FIELDS = {
    "control": "control_mask",
    "direction": "direction_mask",
    "task": "task_mask",
    "task_argument": "task_argument_mask",
    "task_target": "task_target_mask",
    "task_quantity_mode": "task_quantity_mode_mask",
    "task_quantity_max": "task_quantity_max",
    "raw_operation": "raw_operation_mask",
    "raw_argument": "raw_argument_mask",
    "raw_quantity_mode": "raw_quantity_mode_mask",
    "raw_quantity_max": "raw_quantity_max",
    "market_order": "market_order_mask",
    "market_item": "market_item_mask",
    "market_quantity_mode": "market_quantity_mode_mask",
    "market_quantity_max": "market_quantity_max",
}


def _pinned_like(value: Tensor) -> Tensor:
    """Allocate a dtype-identical pinned CPU tensor."""
    return torch.empty(
        value.shape,
        dtype=value.dtype,
        device="cpu",
        pin_memory=True,
    )


def _stage_rows(
    target: Tensor,
    source: object,
    rows: NDArray[np.int64],
) -> None:
    """Copy selected native rows into one persistent pinned tensor."""
    values = np.asarray(source)
    if values.ndim != target.ndim or values.shape[1:] != target.shape[1:]:
        raise ValueError("native program staging tensor shape changed")
    if rows.shape != (target.shape[0],):
        raise ValueError("native program staging row shape changed")
    destination = target.numpy()
    if values.shape[0] == rows.size and np.array_equal(rows, np.arange(rows.size, dtype=np.int64)):
        np.copyto(destination, values, casting="unsafe")
    else:
        np.take(values, rows, axis=0, out=destination)


class PinnedProgramDecisionStaging:
    """Copy native grammar outputs to graph-owned CUDA tensors asynchronously."""

    def __init__(
        self,
        inputs: ProgramDecisionInputs,
        masks: NativeProgramMasks,
        prefix: ProgramPrefixState,
        prepared: ProgramPreparedContext,
    ) -> None:
        """Bind graph-static destinations and allocate reusable pinned storage."""
        self._inputs = inputs
        self._masks = masks
        self._prefix = prefix
        self._prepared = prepared
        self._input_host = {
            name: _pinned_like(getattr(inputs, name)) for name in (*_INPUT_FIELDS, *_SCALAR_FIELDS)
        }
        self._mask_host = {name: _pinned_like(getattr(masks, name)) for name in _MASK_FIELDS}
        rows = inputs.phase.shape[0]
        self._index_host = torch.empty(
            rows,
            dtype=torch.long,
            device="cpu",
            pin_memory=True,
        )
        self._index_device = torch.empty(
            rows,
            dtype=torch.long,
            device=inputs.context.device,
        )

    @staticmethod
    def _gather(
        source: Tensor,
        indices: Tensor,
        target: Tensor,
    ) -> None:
        if (
            source.ndim != target.ndim
            or source.shape[1:] != target.shape[1:]
            or source.dtype != target.dtype
        ):
            raise ValueError("native program graph gather shape changed")
        torch.index_select(source, 0, indices, out=target)

    def install(
        self,
        raw: Mapping[str, object],
        raw_rows: NDArray[np.int64],
        model_rows: NDArray[np.int64],
        prepared: ProgramPreparedContext,
        prefix: ProgramPrefixState,
    ) -> None:
        """Enqueue one native decision batch without pageable CUDA copies."""
        scalars = np.asarray(raw["scalars"])
        if scalars.ndim != 2 or scalars.shape[1] != len(_SCALAR_FIELDS):
            raise ValueError("native program staging scalars changed")
        for name, raw_name in _INPUT_FIELDS.items():
            host = self._input_host[name]
            _stage_rows(host, raw[raw_name], raw_rows)
            getattr(self._inputs, name).copy_(host, non_blocking=True)
        for name, column in _SCALAR_FIELDS.items():
            host = self._input_host[name]
            _stage_rows(host, scalars[:, column], raw_rows)
            getattr(self._inputs, name).copy_(host, non_blocking=True)
        for name, raw_name in _MASK_FIELDS.items():
            host = self._mask_host[name]
            _stage_rows(host, raw[raw_name], raw_rows)
            getattr(self._masks, name).copy_(host, non_blocking=True)

        if model_rows.shape != self._index_host.shape:
            raise ValueError("native program model row shape changed")
        np.copyto(self._index_host.numpy(), model_rows, casting="unsafe")
        self._index_device.copy_(self._index_host, non_blocking=True)
        self._gather(prepared.context, self._index_device, self._prepared.context)
        self._gather(
            prepared.target_keys,
            self._index_device,
            self._prepared.target_keys,
        )
        self._gather(prefix.hidden, self._index_device, self._prefix.hidden)

    @property
    def model_rows(self) -> Tensor:
        """Expose the graph's current padded-to-model row mapping."""
        return self._index_device


class PinnedProgramOutputStaging:
    """Return compiler-required graph actions through one D2H transfer."""

    def __init__(self, actions: Tensor) -> None:
        """Allocate the persistent pinned action buffer."""
        self._actions = actions
        self._host_actions = _pinned_like(actions)

    def enqueue(self, rows: int) -> None:
        """Enqueue compiler-required actions into pinned host memory."""
        if rows < 1 or rows > self._actions.shape[0]:
            raise ValueError("program graph output row count is invalid")
        self._host_actions[:rows].copy_(self._actions[:rows], non_blocking=True)

    def host_actions(self, rows: int) -> NDArray[np.int64]:
        """Expose actions after the producing stream has completed."""
        return self._host_actions.numpy()[:rows]

    def copy(self, rows: int) -> NDArray[np.int64]:
        """Synchronize only the actions required by the native compiler."""
        self.enqueue(rows)
        torch.cuda.current_stream(self._actions.device).synchronize()
        return self.host_actions(rows)


__all__ = [
    "PinnedProgramDecisionStaging",
    "PinnedProgramOutputStaging",
]
