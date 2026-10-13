"""Durable export queue with fixed half-hour slots and a final completed-run capture."""

import json
import logging
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import write_json
from kagg_revue.deployment.publishing import sources
from kagg_revue.deployment.publishing.config import Publishing

LOGGER = logging.getLogger(__name__)


def enqueue(config: Publishing, registry: dict[str, Any], now: float) -> None:
    """Pin at most one committed checkpoint per run and wall-clock interval."""
    from kagg_revue.deployment.snapshots import capture

    known = registry.setdefault("runs", {})
    candidates = set(config.runs) | {Path(name) for name in known}
    if config.discover_active:
        candidates.update(sources.discover())
    slot = int(now // config.interval_seconds)
    for run in sorted(candidates):
        try:
            status, state = sources.read(run)
            active = sources.alive(status)
            record = known.setdefault(str(run), {})
            if record.get("run_id") not in (None, state["run_id"]):
                raise ValueError("a tracked run directory was replaced by another lineage")
            record["run_id"] = state["run_id"]
            final = status["status"] in {"complete", "stopped", "failed"}
            if not active and not final:
                continue
            checkpoint = state["members"][state["latest"]]
            if active and record.get("slot") == slot:
                continue
            if final and record.get("final_checkpoint") == checkpoint:
                continue
            stamp = datetime.fromtimestamp(slot * config.interval_seconds, UTC).strftime(
                "%Y%m%dT%H%M%SZ"
            )
            name = f"{run.name}--{stamp}--{'final' if final else 'active'}--{checkpoint[:12]}"
            job = config.output_dir / "jobs" / name
            specification = job / "job.json"
            if not specification.is_file():
                job.mkdir(parents=True, exist_ok=True)
                snapshot = job / "input"
                if snapshot.exists():
                    shutil.rmtree(snapshot)  # Interrupted capture with no published job.
                member = capture(run, state, snapshot)
                write_json(
                    specification,
                    {
                        "run": str(run),
                        "member": member,
                        "checkpoint_sha256": checkpoint,
                        "captured_utc": datetime.fromtimestamp(now, UTC).isoformat(),
                        "training_status": status["status"],
                        "configuration": config.model_dump(mode="json"),
                    },
                )
            record.update(slot=slot, last_job=name, last_seen_at=now)
            if final:
                record["final_checkpoint"] = checkpoint
            LOGGER.info("Queued %s: %s", run.name, state["latest"])
        except Exception:
            # A retention race is retried on the next poll, without pausing training.
            LOGGER.exception("Cannot capture %s; will retry", run)
    registry["updated_at"] = time.time()
    write_json(config.output_dir / "registry.json", registry)


def pending(config: Publishing, now: float) -> list[Path]:
    """Return persistent unfinished jobs whose retry delay has elapsed."""
    root = config.output_dir / "jobs"
    if not root.exists():
        return []
    result = []
    for job in sorted(root.iterdir()):
        if not (job / "job.json").is_file() or (job / "uploaded.json").is_file():
            continue
        failure = job / "failure.json"
        failed = json.loads(failure.read_text()) if failure.is_file() else {}
        if failed.get("retry_at", 0) > now:
            continue
        specification = json.loads((job / "job.json").read_text())
        result.append((failed.get("time", 0), specification.get("captured_utc", ""), job))
    return [job for _, _, job in sorted(result)]
