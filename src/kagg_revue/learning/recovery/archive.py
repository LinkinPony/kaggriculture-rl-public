"""Reconstruct an experiment's verified implementation without changing the worktree."""

import hashlib
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import digest


def materialize(directory: Path, state: dict[str, Any], target: Path) -> dict[str, Any]:
    """Verify every source member and the native binary before creating an import root."""
    source_directory = (directory / state.get("source_directory", ".")).resolve()
    if not source_directory.is_relative_to(directory.resolve()):
        raise ValueError("source archive must remain inside the authenticated run")
    source = json.loads((source_directory / "source.json").read_text())
    files = source["files"]
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    if (
        fingerprint != state["source"]
        or source["source_sha256"] != fingerprint
        or source["native_sha256"] != state["native"]
        or source["torch_version"] != torch.__version__
    ):
        raise ValueError("recovery requires the archived source, native and original Torch build")
    with tarfile.open(source_directory / "source.tar.gz") as archive:
        members = archive.getmembers()
        if len(members) != len(files) or {member.name for member in members} != files.keys():
            raise ValueError("source archive members differ from the declared implementation")
        for member in members:
            path = Path(member.name)
            if (
                not member.isfile()
                or path.is_absolute()
                or ".." in path.parts
                or not (path.parts[:1] in (("src",), ("configs",)) or str(path) == "pyproject.toml")
            ):
                raise ValueError("source archive contains an unsupported path or file kind")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("source archive member has no regular file content")
            content = stream.read()
            if hashlib.sha256(content).hexdigest() != files[member.name]:
                raise ValueError(f"archived implementation changed: {member.name}")
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
    binary = (directory / state["native_artifact"]).resolve()
    if not binary.is_relative_to(directory.resolve()) or digest(binary) != state["native"]:
        raise ValueError("recovery native binary is missing or differs from the run identity")
    shutil.copy2(binary, target / "src/kagg_revue/native" / binary.name)
    if "script_runtime" in state:
        from kagg_revue.opponents.artifacts import materialize as materialize_scripts

        materialize_scripts(directory, state["script_runtime"], target)
    return {
        "source_sha256": fingerprint,
        "native_sha256": state["native"],
        "source_files": len(files),
        "torch_version": torch.__version__,
    }
