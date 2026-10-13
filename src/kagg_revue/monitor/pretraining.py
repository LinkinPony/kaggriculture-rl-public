"""Read BC progress, split coverage and recent batches without loading model weights."""

import json
import math
from pathlib import Path
from typing import Any

from kagg_revue.monitor.snapshots import read_snapshot


def is_bc_run(run_dir: Path) -> bool:
    """Identify fixed BC-only learning runs independently of whether an epoch has finished."""
    return run_dir.parent.name == "learning" and bool(
        read_snapshot(run_dir / "resolved-config.json").get("pretraining_only")
    )


def metrics_path(run_dir: Path) -> Path:
    """Keep BC epochs and PPO updates on separate histories throughout the run lifetime."""
    return run_dir / ("pretraining/metrics.jsonl" if is_bc_run(run_dir) else "metrics.jsonl")


def _recent_batches(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("rb") as stream:
            stream.seek(0, 2)
            offset = max(0, stream.tell() - 65536)
            stream.seek(offset)
            lines = stream.read().splitlines()
        records = []
        for line in lines[1 if offset else 0 :]:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                records.append(row)
        return records[-12:]
    except OSError:
        return []


def details(run_dir: Path) -> dict[str, Any]:
    """Expose recoverable and live cursors distinctly, with authenticated epoch summaries."""
    if not is_bc_run(run_dir):
        return {}
    config = read_snapshot(run_dir / "resolved-config.json")
    progress = read_snapshot(run_dir / "pretraining/progress.json")
    live = read_snapshot(run_dir / "learning-progress.json")
    source = config.get("demonstrations") or {}
    qualification = read_snapshot(run_dir / "demonstration-qualification.json")
    coverage = qualification.get("coverage", {})
    records = progress.get("records", [])
    batches = _recent_batches(run_dir / "pretraining/batches.jsonl")
    cursor = max(live.get("cursor", 0), progress.get("cursor", 0))
    training_rows = coverage.get("train", {}).get("usable_rows")
    return {
        "epochs": source.get("epochs"),
        "completed_epochs": len(records),
        "cursor": cursor,
        "checkpoint_cursor": progress.get("cursor", 0),
        "batches_per_epoch": live.get("batches_per_epoch")
        or (
            math.ceil(coverage.get("train", {}).get("context_rows", 0) / source["batch_rows"])
            if source.get("batch_rows")
            else None
        ),
        "rows": max(live.get("rows", 0), progress.get("rows", 0)),
        "optimizer_steps": max(live.get("optimizer_steps", 0), progress.get("optimizer_steps", 0)),
        "total_training_rows": training_rows * source.get("epochs", 0) if training_rows else None,
        "learning_rate": source.get("learning_rate"),
        "batch_rows": source.get("batch_rows"),
        "early_stopping": source.get("early_stopping"),
        "devices": config.get("execution", {}).get("devices", [config.get("device")]),
        "precision": config.get("precision"),
        "initial_weights": config.get("initial_weights"),
        "manifest": source.get("manifest"),
        "dataset_sha256": source.get("sha256"),
        "all_array_hashes_verified": qualification.get("all_array_hashes_verified", False),
        "coverage": coverage,
        "teachers": qualification.get("selected_teacher_trajectories", {}),
        "records": records,
        "batches": batches,
        "confirmation": read_snapshot(run_dir / "pretraining/confirmation.json"),
        "current_epoch_nll": live.get("epoch_nll"),
        "updated_at": live.get("updated_at"),
    }
