"""Read authenticated complete replays from daily ZIPs or individual downloads."""

import gzip
import hashlib
import zipfile
from pathlib import Path
from typing import Any


def read_replay(task: dict[str, Any]) -> bytes:
    """Check pinned source identity before returning the original JSON bytes."""
    path = Path(task["path"])
    if task.get("storage") == "gzip":
        compressed = path.read_bytes()
        if hashlib.sha256(compressed).hexdigest() != task["compressed_sha256"]:
            raise ValueError("downloaded replay changed after the collection snapshot")
        raw = gzip.decompress(compressed)
    else:
        with zipfile.ZipFile(path) as archive:
            info = archive.getinfo(task["member"])
            if "member_crc32" in task and (
                task["member_crc32"] != info.CRC or info.file_size != task["raw_bytes"]
            ):
                raise ValueError("daily replay member changed after the collection snapshot")
            raw = archive.read(info)
    if "raw_sha256" in task and hashlib.sha256(raw).hexdigest() != task["raw_sha256"]:
        raise ValueError("raw replay differs from its authenticated download")
    return raw
