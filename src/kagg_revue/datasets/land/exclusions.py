"""Remove explicitly deleted replay IDs from a previously merged analysis snapshot."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.land.reporting import render


def prune(raw: Path, analysis: Path, ids: set[int], receipt: Path) -> dict[str, Any]:
    """Revise catalog membership and cached statistics after an authorized deletion."""
    manifest_path = raw / "merged-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    catalog_path = Path(manifest["catalog"]["path"])
    if digest(catalog_path) != manifest["catalog"]["sha256"]:
        raise ValueError("catalog differs from its saved identity")
    catalog = json.loads(catalog_path.read_text())
    removed = [r for r in catalog if int(r["episode_id"]) in ids]
    if not removed:
        raise ValueError("none of the excluded IDs remain in this catalog")
    if any(r["source"] == "daily" for r in removed):
        raise ValueError("daily ZIP membership requires a separate archive-preserving revision")
    deleted_paths = {location["path"] for r in removed for location in r["locations"]}
    if any(Path(p).exists() for p in deleted_paths):
        raise ValueError("excluded replay payloads must already have been removed")
    remaining = [r for r in catalog if int(r["episode_id"]) not in ids]
    progress_path = analysis / "episodes.jsonl"
    progress = [json.loads(line) for line in progress_path.read_text().splitlines()]
    progress = [r for r in progress if int(r["episode_id"]) not in ids]
    if {r["episode_id"] for r in progress} != {r["episode_id"] for r in remaining}:
        raise ValueError("cached analysis and revised source catalog differ")
    revision = {
        "schema": "merged-replay-exclusion-v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "excluded_episode_ids": sorted(ids),
        "before_episodes": len(catalog),
        "after_episodes": len(remaining),
        "catalog_before_sha256": digest(catalog_path),
        "manifest_before_sha256": digest(manifest_path),
        "removed_records": removed,
        "authorization": "User explicitly requested deleting submission 56414341's existing data.",
    }
    write_json(receipt, {**revision, "state": "prepared"})
    write_json(catalog_path, remaining)
    manifest["catalog"]["sha256"] = digest(catalog_path)
    manifest["unique_episodes"] = len(remaining)
    manifest["local_supplement_episodes"] = sum(
        r["source"] == "local_supplement" for r in remaining
    )
    manifest["files"] = [r for r in manifest["files"] if r["path"] not in deleted_paths]
    manifest.setdefault("exclusion_revisions", []).append(
        {"path": str(receipt), "episode_ids": sorted(ids)}
    )
    write_json(manifest_path, manifest)
    progress_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in progress))
    identity_path = analysis / "identity.json"
    identity = json.loads(identity_path.read_text())
    identity["catalog_sha256"] = digest(catalog_path)
    write_json(identity_path, identity)
    metadata_path = raw / "date-rating-evidence.json"
    if metadata_path.exists():
        evidence = json.loads(metadata_path.read_text())
        evidence["episodes"] = {
            key: value for key, value in evidence["episodes"].items() if int(key) not in ids
        }
        evidence["excluded_episode_ids"] = sorted(ids)
        write_json(metadata_path, evidence)
    report = render(analysis, manifest, progress)
    verification_path = analysis / "verification.json"
    if verification_path.exists():
        verification = json.loads(verification_path.read_text())
        checked = [
            r
            for r in verification["independent_coordinate_scan"]
            if int(r["episode_id"]) not in ids
        ]
        verification.update(
            catalog_sha256=digest(catalog_path),
            report_sha256=digest(analysis / "report.json"),
            unique_episodes=report["all"]["episodes"],
            trajectories=report["all"]["trajectories"],
            independent_coordinate_scan=checked,
            independent_coordinate_scan_trajectories=len(checked),
            exclusion_revision=str(receipt),
        )
        write_json(verification_path, verification)
    revision.update(
        state="complete",
        catalog_after_sha256=digest(catalog_path),
        manifest_after_sha256=digest(manifest_path),
        report_sha256=digest(analysis / "report.json"),
    )
    write_json(receipt, revision)
    return revision
