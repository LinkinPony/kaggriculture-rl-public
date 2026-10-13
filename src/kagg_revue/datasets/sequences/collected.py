"""Freeze several teachers by the earliest authenticated replay download time."""

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import AwareDatetime, Field

from kagg_revue.artifacts.io import digest
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.exclusions import EXCLUDED_SUBMISSIONS
from kagg_revue.datasets.sequences.cohort import _publish
from kagg_revue.datasets.sequences.window import _timestamp


class CollectionSettings(FrozenSettings):
    """Select all available downloads since a fixed inclusive UTC boundary."""

    output: Path
    sources: dict[str, Path] = Field(min_length=1)
    collected_since: AwareDatetime


def _snapshot(source: Path, target: Path) -> dict[str, Any]:
    """Read immutable source bytes, preserving the original before filtering."""
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
    result: dict[str, Any] = json.loads(target.read_text())
    return result


def _provenance_path(config: CollectionSettings, source: Path) -> Path:
    """Give repeated references to the same provenance file one immutable copy."""
    key = hashlib.sha256(str(source).encode()).hexdigest()
    return config.output / "acquisition-sources" / f"{key}.json"


def _download_dates(
    config: CollectionSettings, snapshots: dict[str, dict[str, Any]]
) -> tuple[dict[int, datetime], set[int], dict[str, Any]]:
    """Authenticate gzip provenance and prove reused daily archives predate the cutoff.

    A daily archive verification date is an upper bound on acquisition, not its
    download timestamp. It only proves exclusion when strictly before the cutoff.
    """
    dates: dict[int, datetime] = {}
    older: set[int] = set()
    evidence: dict[str, Any] = {}
    for manifest in snapshots.values():
        for row in manifest["replays"]:
            key = row["episode_id"]
            if row.get("storage") == "daily_zip":
                source = Path(row["path"]).parent / "manifest.json"
                record = evidence.get(str(source))
                if record is None:
                    target = _provenance_path(config, source)
                    original = _snapshot(source, target)
                    record = {
                        "kind": "daily_archive_verified_before_cutoff",
                        "path": str(target),
                        "sha256": digest(target),
                        "verified_at_utc": original["verified_at_utc"],
                        "archives": [r["path"] for r in original["daily_archives"]],
                    }
                    evidence[str(source)] = record
                if (
                    row["path"] not in record["archives"]
                    or _timestamp(record["verified_at_utc"]) >= config.collected_since
                ):
                    raise ValueError("daily replay lacks a provable pre-cutoff acquisition date")
                older.add(key)
                continue
            source = Path(row["source"])
            target = _provenance_path(config, source)
            provenance = _snapshot(source, target)
            if (
                provenance["episode_id"] != key
                or provenance["compressed_sha256"] != row["sha256"]
                or provenance["retrieved_utc"] != row["retrieved_utc"]
            ):
                raise ValueError("download timestamp or identity differs from source provenance")
            timestamp = _timestamp(provenance["retrieved_utc"])
            if timestamp > _timestamp(manifest["updated_utc"]):
                raise ValueError("download is newer than its frozen collector snapshot")
            dates[key] = min(dates.get(key, timestamp), timestamp)
            evidence[str(source)] = {
                "kind": "individual_replay_download",
                "path": str(target),
                "sha256": digest(target),
                "episode_id": key,
                "retrieved_utc": timestamp.isoformat(),
            }
    return dates, older, evidence


def freeze(config: CollectionSettings) -> dict[str, Any]:
    """Deduplicate by first recorded download across all configured collectors."""
    _publish(config.output / "configuration.json", config.model_dump(mode="json"))
    snapshots = {}
    for name, source in config.sources.items():
        if not name or Path(name).name != name or name in {".", ".."}:
            raise ValueError("collector names must be simple directory names")
        snapshots[name] = _snapshot(source, config.output / name / "collector-original.json")
    if len({m["team_id"] for m in snapshots.values()}) != len(snapshots):
        raise ValueError("collector snapshots must identify distinct teams")
    dates, older, evidence = _download_dates(config, snapshots)
    admitted = {key for key, date in dates.items() if date >= config.collected_since} - older
    excluded = EXCLUDED_SUBMISSIONS | {
        s for m in snapshots.values() for s in m.get("excluded_submissions", [])
    }
    blocked = {e for m in snapshots.values() for e in m.get("excluded_episode_ids", [])}
    for manifest in snapshots.values():
        blocked.update(
            e["id"]
            for e in manifest["episodes"]
            if any(a["submissionId"] in excluded for a in e["agents"])
        )
    admitted -= blocked
    reports = []
    selected_ids: set[int] = set()
    for name, manifest in snapshots.items():
        replays = [r for r in manifest["replays"] if r["episode_id"] in admitted]
        ids = {r["episode_id"] for r in replays}
        episodes = [e for e in manifest["episodes"] if e["id"] in ids]
        if not ids or len(ids) != len(replays) or {e["id"] for e in episodes} != ids:
            raise ValueError("each selected teacher needs unique, available episodes")
        active = {s["id"] for s in manifest["submissions"]}
        counts = Counter(
            a["submissionId"]
            for e in episodes
            for a in e["agents"]
            if a.get("teamId") == manifest["team_id"] and a["submissionId"] in active
        )
        selected = {
            **{k: manifest[k] for k in ("team_id", "team_name", "updated_utc", "configuration")},
            "schema": "watched-team-replays-v1",
            "scope": "Earliest authenticated download across configured collectors; all outcomes.",
            "submissions": [s for s in manifest["submissions"] if s["id"] in counts],
            "episodes": episodes,
            "replays": replays,
            "excluded_submissions": sorted(excluded),
            "excluded_episode_ids": sorted(blocked),
            "pending_episode_ids": [],
            "collection_window": {"collected_since_inclusive": config.collected_since.isoformat()},
        }
        target = config.output / name / "selected.json"
        _publish(target, selected)
        selected_ids.update(ids)
        reports.append(
            {
                "name": name,
                "team_name": manifest["team_name"],
                "collector_snapshot_utc": manifest["updated_utc"],
                "original_sha256": digest(config.output / name / "collector-original.json"),
                "selected_manifest": str(target),
                "selected_sha256": digest(target),
                "episodes": len(ids),
                "teacher_trajectories": sum(counts.values()),
                "submissions": dict(sorted(counts.items())),
                "pending_at_snapshot": len(manifest.get("pending_episode_ids", [])),
            }
        )
    # JSON objects stringify integer keys; normalize before immutable comparisons.
    report: dict[str, Any] = json.loads(
        json.dumps(
            {
                "configuration": config.model_dump(mode="json"),
                "sources": reports,
                "unique_episodes": len(selected_ids),
                "teacher_trajectories": sum(r["teacher_trajectories"] for r in reports),
                "earliest_download_utc": {
                    key: dates[key].isoformat() for key in sorted(selected_ids)
                },
                "preexisting_daily_episode_ids": sorted(older),
                "acquisition_evidence": evidence,
            }
        )
    )
    _publish(config.output / "selection.json", report)
    return report


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="sequences_watch4_collected_20260925",
)
def main(configuration: DictConfig) -> None:
    """Freeze the acquisition-time cohort before encoding complete BC trajectories."""
    config = CollectionSettings.model_validate(
        OmegaConf.to_container(configuration.collection, resolve=True)
    )
    report = freeze(config)
    print(
        json.dumps({k: report[k] for k in ("unique_episodes", "teacher_trajectories", "sources")})
    )


if __name__ == "__main__":
    main()
