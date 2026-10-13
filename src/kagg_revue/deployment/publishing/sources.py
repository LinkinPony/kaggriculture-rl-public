"""Discover live registered trainers without importing Torch or touching their locks."""

import json
import logging
from pathlib import Path
from typing import Any

import psutil  # type: ignore[import-untyped]

LOGGER = logging.getLogger(__name__)


def alive(status: dict[str, Any]) -> bool:
    """Reject stale status files, dead workers and recycled PIDs."""
    if status.get("status") != "running":
        return False
    try:
        process = psutil.Process(int(status["pid"]))
        return bool(
            process.is_running()
            and process.status() != psutil.STATUS_ZOMBIE
            and process.create_time() <= float(status["started_at"]) + 1
            and "kagg_revue" in " ".join(process.cmdline())
        )
    except (psutil.Error, KeyError, ValueError):
        return False


def discover() -> list[Path]:
    """Read only immediate outputs/learning run directories, never shared storage."""
    root = Path("outputs/learning")
    if not root.is_dir():
        return []
    runs = []
    for directory in sorted(root.iterdir()):
        if not directory.is_dir() or directory.is_symlink():
            continue
        path = directory / "run-status.json"
        if not path.is_file():
            continue
        try:
            if alive(json.loads(path.read_text())):
                runs.append(directory)
        except (OSError, ValueError):
            LOGGER.exception("Cannot inspect training status: %s", directory)
    return runs


def read(run: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read one atomic ledger and bind the live status to the same run identity."""
    if run.is_symlink() or not run.resolve().is_relative_to(Path("outputs/learning").resolve()):
        raise ValueError("run directory escapes outputs/learning")
    status = json.loads((run / "run-status.json").read_text())
    state = json.loads((run / "state.json").read_text())
    if status.get("run_id") != state["run_id"] or state["protocol"]["output_dir"] != str(run):
        raise ValueError("run status and ledger identities differ")
    return status, state
