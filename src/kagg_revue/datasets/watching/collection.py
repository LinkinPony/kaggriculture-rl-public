"""Discover new public submissions and incrementally download their replays."""

from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import write_json
from kagg_revue.datasets.ranked.downloads import download_missing
from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.daily import reuse_daily
from kagg_revue.datasets.watching.discovery import discover
from kagg_revue.datasets.watching.records import (
    cached_record,
    event,
    load_manifest,
    save_manifest,
    utc_now,
)


def collect(config: WatchSettings) -> dict[str, Any]:
    """Run one resumable acquisition cycle without discarding failed or old IDs."""
    manifest = load_manifest(config)
    errors = discover(config, manifest)
    reuse_daily(config, manifest)
    episodes = {row["id"]: row for row in manifest["episodes"]}
    completed = {row["episode_id"]: row for row in manifest["replays"]}
    # Previously published bytes are immutable. Check their presence cheaply; newly
    # found or interrupted downloads receive full hashing before manifest inclusion.
    for key, row in list(completed.items()):
        path = Path(row.get("path", config.raw / "replays" / f"{key}.json.gz"))
        if not path.exists():
            del completed[key]
        elif path.stat().st_size != row.get("archive_bytes", row["bytes"]):
            raise ValueError(f"archived replay size differs: {key}")
    pending = sorted(episodes.keys() - completed.keys())
    attempts = manifest.setdefault("download_attempts", {})
    pending.sort(key=lambda key: (key not in config.seed_episodes, attempts.get(str(key), 0), key))
    selected = pending[: config.downloads_per_cycle]
    for key in selected:
        attempts[str(key)] = attempts.get(str(key), 0) + 1
    save_manifest(config, manifest)
    cached = {}
    invalid = set()
    for key in selected:
        try:
            row = cached_record(config.raw, episodes[key])
            if row is not None:
                cached[key] = row
        except Exception as error:
            invalid.add(key)
            errors.append({"stage": "cache", "episode_id": key, "error_type": type(error).__name__})
    event(
        config.raw,
        {
            "event": "discovered",
            "submissions": len(manifest["submissions"]),
            "episodes": len(episodes),
            "available": len(completed),
            "selected": len(selected),
            "errors": errors,
        },
    )
    downloaded, failures = download_missing(
        config.raw,
        [episodes[key] for key in selected if key not in invalid],
        cached,
        config.workers,
        config.request_interval,
        config.maximum_backoffs,
    )
    for row in downloaded:
        key = row["episode_id"]
        record = cached_record(config.raw, episodes[key])
        if record is None:
            raise ValueError(f"download was not durably published: {key}")
        # Explicit episode seeds must also match the requested team, even when the
        # public listing no longer contains the episode and cannot confirm ownership.
        if not episodes[key].get("agents") and config.team_name not in record["team_names"]:
            errors.append({"stage": "identity", "episode_id": key})
            continue
        completed[key] = record
    manifest["replays"] = sorted(completed.values(), key=lambda row: row["episode_id"])
    manifest["failures"] = [
        {key: value for key, value in failure.items() if key != "error"} for failure in failures
    ]
    manifest["discovery_errors"] = errors
    save_manifest(config, manifest)
    summary = {
        "event": "cycle_complete",
        "completed_utc": utc_now(),
        "submissions": len(manifest["submissions"]),
        "episodes": len(episodes),
        "downloaded_this_cycle": len(downloaded),
        "available": len(completed),
        "reused_daily": sum(r.get("storage") == "daily_zip" for r in completed.values()),
        "pending": len(manifest["pending_episode_ids"]),
        "failures": len(failures),
        "discovery_errors": len(errors),
        "bytes": sum(row["bytes"] for row in completed.values()),
    }
    write_json(config.raw / "last-cycle.json", summary)
    event(config.raw, summary)
    return summary
