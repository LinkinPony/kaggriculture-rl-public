"""Deterministic output archives with explicit file identities."""

import gzip
import tarfile
from pathlib import Path

from kagg_revue.artifacts.io import digest as sha256_file


def _file_rows(root: Path) -> list[dict[str, object]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
        if path.name != "manifest.json"
    ]


def _tar_filter(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.mode = 0o755 if info.isdir() else 0o644
    return info


def _archive(package_root: Path, destination: Path) -> None:
    with (
        destination.open("wb") as raw,
        gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed,
        tarfile.open(fileobj=compressed, mode="w") as archive,
    ):
        for path in sorted(package_root.rglob("*")):
            archive.add(
                path,
                arcname=path.relative_to(package_root).as_posix(),
                recursive=False,
                filter=_tar_filter,
            )
