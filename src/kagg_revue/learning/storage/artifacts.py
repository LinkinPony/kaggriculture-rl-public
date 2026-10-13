"""Preserve checkpoint identities while storing frozen policies without optimizers."""

import os
from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import digest
from kagg_revue.artifacts.serialization import save

_POLICY_FIELDS = ("layout", "model", "settings", "lineage", "update")


def local_path(directory: Path, name: str) -> Path:
    """Reject absolute paths and links escaping an experiment's artifact directory."""
    root = directory.resolve()
    path = (root / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(root) or path.suffix != ".pt":
        raise ValueError("checkpoint escapes the run directory")
    return path


def resolve(directory: Path, state: dict[str, Any], name: str) -> Path:
    """Authenticate physical bytes against their recorded storage representation."""
    if name not in state["members"]:
        raise ValueError("checkpoint is not an authenticated member of this random-root run")
    record = state.get("inference_artifacts", {}).get(name)
    if record is None:
        path, expected = local_path(directory, name), state["members"][name]
    else:
        if record["source_sha256"] != state["members"][name]:
            raise ValueError("inference artifact identity differs from its checkpoint")
        path, expected = local_path(directory, record["path"]), record["sha256"]
    if not path.is_file() or digest(path) != expected:
        raise ValueError("checkpoint is not an authenticated member of this random-root run")
    return path


def compact(
    directory: Path,
    state: dict[str, Any],
    names: set[str],
    *,
    shared: dict[str, tuple[Path, str]] | None = None,
) -> list[str]:
    """Stage verified actors; return original files deletable after ledger publication.

    The original checkpoint hash remains the PFSP and lineage identity. A distinct
    storage hash authenticates the reduced bytes. No original file is overwritten.
    """
    mappings = state.setdefault("inference_artifacts", {})
    originals = []
    for name in sorted(names):
        if name in mappings or name == "initial.pt" or name.startswith("anchors/"):
            continue
        identity = state["members"][name]
        relative = f"inference/{identity}.pt"
        destination = local_path(directory, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if shared is not None and identity in shared:
            source, checksum = shared[identity]
            if destination != source:
                if not destination.exists():
                    os.link(source, destination)
                if digest(destination) != checksum:
                    raise ValueError("shared inference artifact changed")
        else:
            source = resolve(directory, state, name)
            payload = torch.load(source, map_location="cpu", weights_only=False, mmap=True)
            if not any(key in payload for key in ("optimizer", "actor_optimizer", "critic")):
                continue
            actor = {key: payload[key] for key in _POLICY_FIELDS if key in payload}
            actor["storage"] = {"kind": "inference_only", "source_sha256": identity}
            checksum = save(actor, destination)
            verified = torch.load(destination, map_location="cpu", weights_only=False, mmap=True)
            if (
                set(verified["model"]) != set(payload["model"])
                or any(
                    not torch.equal(value, verified["model"][key])
                    for key, value in payload["model"].items()
                )
                or digest(destination) != checksum
            ):
                raise ValueError("inference compaction changed policy tensors or archive bytes")
            if shared is not None:
                shared[identity] = (destination, checksum)
        mappings[name] = {"path": relative, "sha256": checksum, "source_sha256": identity}
        originals.append(name)
    return originals


def import_member(
    directory: Path, state: dict[str, Any], name: str, source: Path, identity: str
) -> None:
    """Import authenticated actor bytes with independent provenance and storage hashes."""
    import shutil

    payload = torch.load(source, map_location="cpu", weights_only=False, mmap=True)
    relative = f"inference/{identity}.pt"
    destination = local_path(directory, relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    storage = payload.get("storage", {})
    if storage.get("kind") == "inference_only":
        if storage.get("source_sha256") != identity:
            raise ValueError("imported policy provenance differs from the source ledger")
        checksum = digest(source)
        if not destination.exists():
            try:
                os.link(source, destination)
            except OSError:
                partial = destination.with_suffix(".partial")
                shutil.copy2(source, partial)
                partial.replace(destination)
    else:
        actor = {key: payload[key] for key in _POLICY_FIELDS if key in payload}
        actor["storage"] = {"kind": "inference_only", "source_sha256": identity}
        checksum = save(actor, destination)
    if digest(destination) != checksum:
        raise ValueError("imported actor archive differs from the authenticated source")
    state["members"][name] = identity
    state.setdefault("inference_artifacts", {})[name] = {
        "path": relative,
        "sha256": checksum,
        "source_sha256": identity,
    }
