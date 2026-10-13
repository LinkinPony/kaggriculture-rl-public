"""Apply explicit submission exclusions to discovery, manifests and archived files."""

import fcntl
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.exclusions import EXCLUDED_SUBMISSIONS
from kagg_revue.datasets.watching.config import WatchSettings


def excluded_episode(episode: dict[str, Any], submissions: tuple[int, ...]) -> bool:
    """Exclude a whole match if either seat uses an explicitly excluded submission."""
    excluded = EXCLUDED_SUBMISSIONS | set(submissions)
    return any(a.get("submissionId") in excluded for a in episode.get("agents", []))


def apply_exclusions(config: WatchSettings, manifest: dict[str, Any]) -> None:
    """Remove excluded membership and retain ID-only tombstones against rediscovery."""
    excluded = tuple(sorted(EXCLUDED_SUBMISSIONS | set(config.excluded_submissions)))
    catalogs = [manifest]
    if "outside_scope" in manifest:
        catalogs.append(manifest["outside_scope"])
    blocked = set(manifest.get("excluded_episode_ids", []))
    blocked.update(
        r["id"]
        for catalog in catalogs
        for r in catalog.get("episodes", [])
        if excluded_episode(r, excluded)
    )
    blocked.update(
        r["episode_id"]
        for catalog in catalogs
        for r in catalog.get("replays", [])
        if excluded_episode(r, excluded)
    )
    for catalog in catalogs:
        catalog["submissions"] = [
            r for r in catalog.get("submissions", []) if r["id"] not in excluded
        ]
        for row in catalog["submissions"]:
            if "evidence_episode_ids" in row:
                row["evidence_episode_ids"] = [
                    k for k in row["evidence_episode_ids"] if k not in blocked
                ]
        catalog["episodes"] = [r for r in catalog.get("episodes", []) if r["id"] not in blocked]
        catalog["replays"] = [
            r for r in catalog.get("replays", []) if r["episode_id"] not in blocked
        ]
        if "undated_submission_ids" in catalog:
            catalog["undated_submission_ids"] = [
                k for k in catalog["undated_submission_ids"] if k not in excluded
            ]
    manifest["excluded_submissions"] = list(excluded)
    manifest["excluded_episode_ids"] = sorted(blocked)
    if "download_attempts" in manifest:
        manifest["download_attempts"] = {
            k: v for k, v in manifest["download_attempts"].items() if int(k) not in blocked
        }
    for field in ("failures", "discovery_errors"):
        if field in manifest:
            manifest[field] = [
                r
                for r in manifest[field]
                if r.get("episode_id") not in blocked and r.get("submission_id") not in excluded
            ]
    available = {r["episode_id"] for r in manifest["replays"]}
    manifest["pending_episode_ids"] = [
        r["id"] for r in manifest["episodes"] if r["id"] not in available
    ]


def purge(config: WatchSettings, report: Path) -> dict[str, Any]:
    """Delete explicitly excluded replay payloads while holding the collector lock."""
    with (config.raw / "collector.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = config.raw / "manifest.json"
        manifest = json.loads(path.read_text())
        if manifest["team_id"] != config.team_id:
            raise ValueError("archive belongs to a different team")
        before_sha256 = digest(path)
        before = {key: len(manifest[key]) for key in ("submissions", "episodes", "replays")}
        apply_exclusions(config, manifest)
        blocked = set(manifest["excluded_episode_ids"])
        candidates = [
            p
            for p in (config.raw / "replays").iterdir()
            if p.is_file()
            and p.name.split(".")[0].isdigit()
            and int(p.name.split(".")[0]) in blocked
        ]
        for key in config.excluded_submissions:
            candidates.extend(config.raw.glob(f"snapshots/*/submissions/{key}.json"))
            candidates.extend(config.raw.glob(f"snapshots/*/submissions/{key}.source.json"))
        candidates = sorted(set(candidates))
        deletions = [
            {"path": str(p), "bytes": p.stat().st_size, "sha256": digest(p)}
            for p in sorted(candidates)
        ]
        receipt = {
            "schema": "watched-submission-exclusion-v1",
            "created_utc": datetime.now(UTC).isoformat(),
            "excluded_submissions": list(config.excluded_submissions),
            "excluded_episode_ids": sorted(blocked),
            "manifest_before_sha256": before_sha256,
            "before": before,
            "after": {key: len(manifest[key]) for key in before},
            "deleted_files": deletions,
            "authorization": "User explicitly requested removing the submission, deleting existing "
            "collected data and stopping future tracking.",
        }
        write_json(report, {**receipt, "state": "prepared"})
        manifest["configuration"] = config.model_dump(mode="json")
        manifest["updated_utc"] = datetime.now(UTC).isoformat()
        write_json(path, manifest)
        for candidate in candidates:
            candidate.unlink()
        receipt.update(state="complete", manifest_after_sha256=digest(path))
        write_json(report, receipt)
        return receipt
