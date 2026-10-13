"""Streaming writers for compact teacher-data NumPy ZIP shards."""

from __future__ import annotations

import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import IO

import numpy as np
from numpy.typing import NDArray


def _write_array(stream: IO[bytes], value: NDArray[np.generic]) -> None:
    np.lib.format.write_array(stream, value, allow_pickle=False)


def write_compressed_npz(
    path: Path,
    arrays: Mapping[str, NDArray[np.generic]],
    compression_level: int,
) -> None:
    """Atomically write an allow-pickle-free NPZ at an explicit zlib level."""
    if compression_level < 0 or compression_level > 9:
        raise ValueError("NPZ compression level must be in [0, 9]")
    temporary = path.with_suffix(".npz.tmp")
    with zipfile.ZipFile(
        temporary,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=compression_level,
        allowZip64=True,
    ) as archive:
        for name, value in arrays.items():
            with archive.open(f"{name}.npy", mode="w", force_zip64=True) as stream:
                _write_array(stream, np.asarray(value))
    temporary.replace(path)


__all__ = ["write_compressed_npz"]
