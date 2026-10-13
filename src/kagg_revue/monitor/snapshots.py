"""Bounded reads of live monitoring snapshots and configuration."""

import json
from pathlib import Path
from typing import Any

# PFSP snapshots grow with the opponent pool; use the same budget as monitor reports.
_MAX_SNAPSHOT_BYTES = 20 * 1024 * 1024


def read_snapshot(path: Path) -> dict[str, Any]:
    """Read one JSON object without loading oversized files or the model ledger."""
    try:
        with path.open("rb") as stream:
            data = stream.read(_MAX_SNAPSHOT_BYTES + 1)
        if len(data) > _MAX_SNAPSHOT_BYTES:
            return {}
        value = json.loads(data)
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}
