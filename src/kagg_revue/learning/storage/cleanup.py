"""Exact inode-aware checkpoint cleanup with explicit retained run dependencies."""

import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.storage.artifacts import resolve
from kagg_revue.learning.storage.roles import full_members, required_members

_SUFFIXES = {".pt", ".pth", ".ckpt", ".safetensors"}


def plan(runs: tuple[Path, ...], report: Path) -> dict[str, Any]:
    """Enumerate checkpoint files only, preserving data, logs, sources and submission packages."""
    keep: set[Path] = set()
    summaries = []
    for directory in runs:
        state = json.loads((directory / "state.json").read_text())
        config = Experiment.model_validate(state["protocol"])
        if not state.get("storage_history"):
            raise ValueError(f"migrate and qualify retained run before cleanup: {directory}")
        revision = directory / state["storage_history"][-1]["revision"]
        qualification = json.loads((revision / "verification.json").read_text())
        if (
            not qualification["passed"]
            or qualification["completed_update"] != state["completed_update"]
            or qualification["source_sha256"] != state["source"]
        ):
            raise ValueError("cleanup qualification no longer matches the stopped run")
        names = required_members(config, state) | full_members(config, state)
        keep.update(resolve(directory, state, name) for name in names)
        summaries.append(
            {
                "run": str(directory),
                "latest": state["latest"],
                "full_checkpoints": sorted(full_members(config, state)),
                "pool_members": len(state["pool"]),
                "retained_policies": len(names),
            }
        )
    candidates = []
    inodes: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for base, directories, files in os.walk("outputs", followlinks=False):
        directories[:] = [name for name in directories if not (Path(base) / name).is_symlink()]
        for name in files:
            path = Path(base) / name
            if path.suffix not in _SUFFIXES or path.is_symlink():
                continue
            stat = path.stat()
            entry = {
                "path": str(path),
                "device": stat.st_dev,
                "inode": stat.st_ino,
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "links": stat.st_nlink,
                "allocated_bytes": stat.st_blocks * 512,
                "keep": path.resolve() in keep,
            }
            inodes[(stat.st_dev, stat.st_ino)].append(entry)
            if not entry["keep"]:
                candidates.append(entry)
    unique = sum(entries[0]["allocated_bytes"] for entries in inodes.values())
    reclaim = sum(
        entries[0]["allocated_bytes"]
        for entries in inodes.values()
        if not any(entry["keep"] for entry in entries) and len(entries) == entries[0]["links"]
    )
    result = {
        "created_at": time.time(),
        "runs": summaries,
        "scope": "Only standalone checkpoint files under outputs; source datasets, metadata, "
        "source archives and submission packages are retained.",
        "retained_paths": sorted(str(path.relative_to(Path.cwd())) for path in keep),
        "candidate_count": len(candidates),
        "unique_allocated_bytes_before": unique,
        "estimated_reclaimable_bytes": reclaim,
        "candidates": candidates,
    }
    write_json(report / "cleanup-plan.json", result)
    return result


def apply(planned: dict[str, Any], report: Path) -> dict[str, Any]:
    """Delete precisely the recorded unchanged files while both retained runs are locked."""
    reclaimed = 0
    count = 0
    started = time.time()
    for entry in planned["candidates"]:
        path = Path(entry["path"])
        stat = path.lstat()
        if (
            path.is_symlink()
            or path.parts[:1] != ("outputs",)
            or ".." in path.parts
            or path.suffix not in _SUFFIXES
            or (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)
            != (entry["device"], entry["inode"], entry["size"], entry["mtime_ns"])
        ):
            raise ValueError(f"cleanup candidate changed since inventory: {path}")
        if stat.st_nlink == 1:
            reclaimed += stat.st_blocks * 512
        path.unlink()
        count += 1
    for name in planned["retained_paths"]:
        if not Path(name).is_file():
            raise ValueError(f"cleanup lost a protected recovery dependency: {name}")
    result = {
        "started_at": started,
        "finished_at": time.time(),
        "deleted_files": count,
        "released_allocated_bytes": reclaimed,
        "runs": planned["runs"],
        "retained_paths": planned["retained_paths"],
        "note": "Allocated blocks released at final hardlink removal; filesystem shared "
        "extents and concurrent activity can affect df measurements.",
    }
    write_json(report / "cleanup-result.json", result)
    return result
