"""Bounded-memory SHA256 identities and atomic JSON publication."""

import hashlib
import json
from pathlib import Path
from typing import Any


def digest(path: Path) -> str:
    """Hash an artifact with bounded memory."""
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            result.update(block)
    return result.hexdigest()


def write_json(path: Path, value: Any) -> None:
    """Atomically publish a small human-readable record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)
