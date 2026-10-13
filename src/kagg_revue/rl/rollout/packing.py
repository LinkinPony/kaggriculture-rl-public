"""Lossless host packing for rollout tensors expanded only by PPO collation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class PackedBoolArray:
    """An ndarray-like boolean tensor packed along its final dimension."""

    data: NDArray[np.uint8]
    logical_shape: tuple[int, ...]

    def __post_init__(self) -> None:
        """Validate and freeze the exact packed representation."""
        if not self.logical_shape or self.logical_shape[-1] < 1:
            raise ValueError("packed boolean arrays need a nonempty final dimension")
        expected = (
            *self.logical_shape[:-1],
            (self.logical_shape[-1] + 7) // 8,
        )
        if self.data.dtype != np.uint8 or self.data.shape != expected:
            raise ValueError("packed boolean payload differs from its logical shape")
        self.data.flags.writeable = False

    @classmethod
    def pack(cls, value: NDArray[np.bool_]) -> PackedBoolArray:
        """Pack one contiguous logical boolean tensor without losing any bits."""
        logical = np.asarray(value, dtype=np.bool_)
        if logical.ndim < 1 or logical.shape[-1] < 1:
            raise ValueError("cannot pack an empty boolean token dimension")
        data = np.packbits(logical, axis=-1, bitorder="little")
        return cls(np.ascontiguousarray(data), tuple(logical.shape))

    @property
    def shape(self) -> tuple[int, ...]:
        """Return the unpacked logical shape."""
        return self.logical_shape

    @property
    def ndim(self) -> int:
        """Return the logical rank."""
        return len(self.logical_shape)

    @property
    def dtype(self) -> np.dtype[np.bool_]:
        """Return the logical dtype."""
        return np.dtype(np.bool_)

    @property
    def nbytes(self) -> int:
        """Return the physical payload size."""
        return int(self.data.nbytes)

    def unpack(self, leading_width: int | None = None) -> NDArray[np.bool_]:
        """Expand the payload, optionally narrowing its penultimate dimension."""
        source = self.data
        logical_shape = self.logical_shape
        if leading_width is not None:
            if self.ndim < 2 or not 0 <= leading_width <= logical_shape[-2]:
                raise ValueError("packed boolean leading width is out of range")
            source = source[..., :leading_width, :]
            logical_shape = (*logical_shape[:-2], leading_width, logical_shape[-1])
        unpacked = np.unpackbits(
            source,
            axis=-1,
            count=logical_shape[-1],
            bitorder="little",
        )
        return np.asarray(unpacked, dtype=np.bool_).reshape(logical_shape)

    def __getitem__(self, index: Any) -> NDArray[np.bool_]:
        """Materialize an indexed diagnostic view."""
        return np.asarray(self.unpack()[index], dtype=np.bool_)

    def __array__(
        self,
        dtype: np.dtype[Any] | None = None,
        copy: bool | None = None,
    ) -> NDArray[Any]:
        """Materialize the logical ndarray for generic NumPy consumers."""
        value = self.unpack()
        if dtype is not None:
            value = value.astype(dtype, copy=False)
        if copy:
            value = value.copy()
        return value


__all__ = ["PackedBoolArray"]
