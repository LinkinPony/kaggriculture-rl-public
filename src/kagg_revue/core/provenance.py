"""Source-tree identities shared by generated artifacts and reports."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def _source_tree_sha256(root: Path) -> str:
    paths = [root / "pyproject.toml"]
    for directory in (root / "src", root / "configs", root / "docs"):
        if directory.is_dir():
            paths.extend(
                path
                for path in directory.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts
            )
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def source_identity(root: Path) -> dict[str, object]:
    """Bind an artifact to the current revision and relevant source tree."""
    return {
        "commit": _git(root, "rev-parse", "HEAD"),
        "worktree_dirty": bool(_git(root, "status", "--short")),
        "source_tree_sha256": _source_tree_sha256(root),
    }


__all__ = ["source_identity"]
