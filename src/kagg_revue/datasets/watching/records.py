"""Preserve acquisition history and validate completed replay artifacts."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.ranked.metadata import replay_header
from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.exclusions import apply_exclusions
from kagg_revue.datasets.watching.scope import apply_scope


def utc_now() -> str:
    """Return an explicit UTC acquisition timestamp."""
    return datetime.now(UTC).isoformat()


def event(raw: Path, record: dict[str, Any]) -> None:
    """Append an acquisition event without rewriting earlier history."""
    record = {"recorded_utc": utc_now(), **record}
    with (raw / "history.jsonl").open("a") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps(record, ensure_ascii=False), flush=True)


def load_manifest(config: WatchSettings) -> dict[str, Any]:
    """Restore all known IDs, including submissions that are no longer public."""
    path = config.raw / "manifest.json"
    manifest: dict[str, Any] = (
        json.loads(path.read_text())
        if path.exists()
        else {
            "schema": "watched-team-replays-v1",
            "created_utc": utc_now(),
            "team_id": config.team_id,
            "team_name": config.team_name,
            "submissions": [],
            "episodes": [],
            "replays": [],
        }
    )
    if manifest["team_id"] != config.team_id:
        raise ValueError("archive belongs to a different team")
    manifest["configuration"] = config.model_dump(mode="json")
    apply_exclusions(config, manifest)
    apply_scope(config, manifest)
    manifest["scope"] = (
        "All completed public episodes exposed by the team's public submissions and "
        "previously discovered submissions, plus explicit seed episodes. No outcome or "
        "score filtering except explicit submission exclusions, applied to either seat. "
        "Kaggle episode listings have no pagination; unavailable historical "
        "submissions and unlisted episodes cannot be guaranteed. Raw artifacts are retained. "
        "Configured submitted_since is a fixed inclusive submission timestamp cutoff; "
        "outside_scope preserves earlier records, outside the active dataset. Daily ZIP "
        "members remain in the dataset through reusable file references."
    )
    return manifest


def cached_record(raw: Path, episode: dict[str, Any]) -> dict[str, Any] | None:
    """Authenticate a replay and enrich its durable record with source metadata."""
    episode_id = episode["id"]
    path = raw / "replays" / f"{episode_id}.json.gz"
    source = path.with_suffix(".source.json")
    if not path.exists():
        return None
    if not source.exists():
        # A kill between the replay rename and provenance publication is recoverable:
        # preserve the bytes, then let the downloader retrieve the missing source again.
        path.rename(path.with_name(f"{path.name}.unverified-{datetime.now(UTC):%Y%m%dT%H%M%S%f}"))
        return None
    provenance = json.loads(source.read_text())
    if digest(path) != provenance["compressed_sha256"]:
        raise ValueError(f"cached replay hash differs: {episode_id}")
    header = replay_header(path)
    return {
        "episode_id": episode_id,
        "path": str(path),
        "sha256": provenance["compressed_sha256"],
        "bytes": path.stat().st_size,
        "retrieved_utc": provenance["retrieved_utc"],
        "source": str(source),
        "url": provenance["url"],
        "team_names": header["info"]["TeamNames"],
        "statuses": header["statuses"],
        "end_time": episode.get("endTime"),
        "agents": episode.get("agents", []),
    }


def save_manifest(config: WatchSettings, manifest: dict[str, Any]) -> None:
    """Publish counts and pending IDs together with the complete source catalog."""
    apply_exclusions(config, manifest)
    apply_scope(config, manifest)
    available = {row["episode_id"] for row in manifest["replays"]}
    manifest["pending_episode_ids"] = [
        row["id"] for row in manifest["episodes"] if row["id"] not in available
    ]
    manifest["updated_utc"] = utc_now()
    write_json(config.raw / "manifest.json", manifest)
