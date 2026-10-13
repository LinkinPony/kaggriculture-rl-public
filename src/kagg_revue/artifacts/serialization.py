"""Atomic Torch archives with bounded direct writes under page-cache pressure."""

import errno
import hashlib
import io
import mmap
import os
from pathlib import Path
from typing import Any

import torch

_ALIGNMENT = 4096
_CHUNK = 4 * 1024 * 1024
_UNSUPPORTED = {errno.EINVAL, errno.ENOTSUP, errno.ENOSYS}


def _direct(path: Path, data: memoryview) -> None:
    """Write aligned blocks without populating the filesystem page cache."""
    if not hasattr(os, "O_DIRECT"):
        raise OSError(errno.ENOTSUP, "direct writes are unavailable")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_DIRECT, 0o666)
    try:
        with mmap.mmap(-1, _CHUNK) as block, memoryview(block) as target:
            for offset in range(0, len(data), _CHUNK):
                size = min(_CHUNK, len(data) - offset)
                padded = (size + _ALIGNMENT - 1) // _ALIGNMENT * _ALIGNMENT
                target[:size] = data[offset : offset + size]
                target[size:padded] = b"\0" * (padded - size)
                written = 0
                while written < padded:
                    count = os.write(descriptor, target[written:padded])
                    if count <= 0 or count % _ALIGNMENT:
                        raise OSError(errno.EIO, "unaligned or empty direct write")
                    written += count
            os.ftruncate(descriptor, len(data))
    finally:
        os.close(descriptor)


def save(payload: Any, path: Path) -> str:
    """Preserve Torch's CRC32 archive and publish only after the full write succeeds.

    One in-memory archive avoids thousands of file writes interleaved with GPU
    copies. Direct I/O avoids pathological kernel reclaim while writing large
    checkpoints; unsupported filesystems retain the ordinary buffered fallback.
    The caller continues to authenticate the complete published archive with SHA256.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial")
    try:
        with io.BytesIO() as buffer:
            torch.save(payload, buffer)
            with buffer.getbuffer() as data:
                checksum = hashlib.sha256(data).hexdigest()
                try:
                    _direct(temporary, data)
                except OSError as error:
                    if error.errno not in _UNSUPPORTED:
                        raise
                    with temporary.open("wb") as stream:
                        stream.write(data)
        temporary.replace(path)
        return checksum
    finally:
        temporary.unlink(missing_ok=True)
