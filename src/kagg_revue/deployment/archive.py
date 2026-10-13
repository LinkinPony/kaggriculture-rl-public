"""Inspect an exact new-run archive before extracting executable package members."""

import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from kagg_revue.artifacts.io import digest


def unpack(path: Path, expected: str, destination: Path) -> dict[str, Any]:
    """Verify archive identity, safe members and all declared file contents."""
    if digest(path) != expected:
        raise ValueError("deployment archive hash differs from the declared candidate")
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        if len({member.name for member in members}) != len(members):
            raise ValueError("deployment archive repeats a member")
        contents = {}
        for member in members:
            relative = PurePosixPath(member.name)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or not (member.isfile() or member.isdir())
            ):
                raise ValueError("unsafe deployment archive member")
            if member.isfile():
                stream = archive.extractfile(member)
                assert stream is not None
                contents[member.name] = stream.read()
    manifest: dict[str, Any] = json.loads(contents["manifest.json"])
    if manifest["schema_version"] not in {
        "random-root-grounded-submission-v1",
        "checkpoint-root-grounded-submission-v1",
    }:
        raise ValueError("archive has an unsupported policy-root deployment schema")
    files = sorted(
        [
            {"path": name, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}
            for name, data in contents.items()
            if name != "manifest.json"
        ],
        key=lambda item: str(item["path"]),
    )
    if files != sorted(manifest["files"], key=lambda item: item["path"]):
        raise ValueError("archive contents differ from the embedded file manifest")
    for name, data in contents.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return manifest
