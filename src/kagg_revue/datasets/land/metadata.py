"""Recover episode dates and historical ratings from existing raw metadata."""

import hashlib
import json
import math
import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.bc.replay import daily_episode_metadata


def episode_records(value: Any) -> Iterator[dict[str, Any]]:
    """Find episode metadata without treating submission scores as episode ratings."""
    if isinstance(value, dict):
        if (
            ("id" in value or "episode_id" in value)
            and "agents" in value
            and ("createTime" in value or "create_time" in value)
        ):
            yield value
        else:
            for child in value.values():
                yield from episode_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from episode_records(child)


def scores(agents: list[dict[str, Any]], key: str) -> list[float] | None:
    """Require both recorded player ratings; never substitute terminal rewards."""
    if len(agents) != 2:
        return None
    values = [agent.get(key) for agent in sorted(agents, key=lambda a: a.get("index", 0))]
    result = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        result.append(float(value))
    return result if all(math.isfinite(v) for v in result) else None


def snapshot(root: Path, raw: Path, ids: set[str]) -> dict[str, Any]:
    """Freeze selected episode fields and the identities of their metadata sources."""
    path = raw / "date-rating-evidence.json"
    if path.exists():
        result: dict[str, Any] = json.loads(path.read_text())
        return result
    selected: dict[str, Any] = {}
    identities = {}
    skipped_large_files = []
    for directory, children, names in os.walk(root, followlinks=False):
        children[:] = sorted(
            c
            for c in children
            if c not in {"replays", "logs-0", "logs-1", "site-packages", "notebooks"}
            and not (Path(directory) / c).is_symlink()
        )
        for name in sorted(names):
            source = Path(directory) / name
            if (
                source.is_symlink()
                or not name.endswith(".json")
                or name.endswith(("-replay.json", ".source.json", "-source.json"))
                or source.is_relative_to(raw)
            ):
                continue
            if source.stat().st_size > 20_000_000:
                skipped_large_files.append(str(source))
                continue
            content = source.read_bytes()
            if b'"createTime"' not in content and b'"create_time"' not in content:
                continue
            for episode in episode_records(json.loads(content)):
                episode_id = str(episode.get("id", episode.get("episode_id")))
                if episode_id not in ids:
                    continue
                created = episode.get("createTime", episode.get("create_time"))
                if not isinstance(created, str):
                    raise ValueError(f"missing creation timestamp: {episode_id}")
                timestamp = datetime.fromisoformat(created.replace("Z", "+00:00"))
                day = (
                    timestamp.replace(tzinfo=UTC).date().isoformat()
                    if timestamp.tzinfo is None
                    else timestamp.astimezone(UTC).date().isoformat()
                )
                previous = selected.get(episode_id)
                if previous and previous["date"] != day:
                    raise ValueError(f"metadata dates disagree for episode {episode_id}")
                initial = scores(episode["agents"], "initialScore")
                updated = scores(episode["agents"], "updatedScore")
                if (
                    previous
                    and previous["updated_scores"]
                    and updated
                    and previous["updated_scores"] != updated
                ):
                    raise ValueError(f"historical ratings disagree for episode {episode_id}")
                if previous and (previous["updated_scores"] or not updated):
                    continue
                identities[str(source)] = hashlib.sha256(content).hexdigest()
                selected[episode_id] = {
                    "episode_id": episode_id,
                    "date": day,
                    "create_time": created,
                    "initial_scores": initial,
                    "updated_scores": updated,
                    "source": str(source),
                    "source_sha256": identities[str(source)],
                }
    result = {
        "schema": "episode-date-rating-evidence-v1",
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "episodes": selected,
        "sources": identities,
        "skipped_large_files": skipped_large_files,
        "scope": "Existing local raw episode metadata only; exact episode IDs. No dates from "
        "file mtimes, and no historical ratings inferred from cash or leaderboard snapshots.",
    }
    write_json(path, result)
    return result


def enrich(root: Path, raw: Path, analysis: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Attach official daily ratings and available API metadata to frozen replay IDs."""
    manifest = json.loads((raw / "merged-manifest.json").read_text())
    catalog = json.loads(Path(manifest["catalog"]["path"]).read_text())
    if digest(Path(manifest["catalog"]["path"])) != manifest["catalog"]["sha256"]:
        raise ValueError("source catalog changed")
    daily = json.loads((raw / "manifest.json").read_text())
    metadata: dict[str, Any] = {}
    for archive in daily["daily_archives"]:
        metadata.update(daily_episode_metadata(Path(archive["path"])))
    evidence = snapshot(root, raw, {row["episode_id"] for row in catalog})
    land = {
        item["episode_id"]: item["rows"]
        for item in (
            json.loads(line) for line in (analysis / "episodes.jsonl").read_text().splitlines()
        )
    }
    rows = []
    comparisons = []
    for task in catalog:
        episode_id = task["episode_id"]
        api = evidence["episodes"].get(episode_id)
        day = task["date"] if task["date"] != "unknown" else api["date"] if api else "unknown"
        if api and day != api["date"]:
            raise ValueError(f"daily/API dates disagree: {episode_id}")
        rating = minimum = None
        kind = "missing"
        rating_source = None
        if episode_id in metadata:
            rating = float(metadata[episode_id]["average_score"])
            minimum = float(metadata[episode_id]["minimum_score"])
            kind = "daily_avg_score"
            rating_source = task["path"] + ":manifest.csv"
        if api and api["updated_scores"]:
            average = sum(api["updated_scores"]) / 2
            if rating is None:
                rating, minimum = average, min(api["updated_scores"])
                kind, rating_source = "api_mean_updated_score", api["source"]
            else:
                comparisons.append(
                    {
                        "episode_id": episode_id,
                        "daily_avg_score": rating,
                        "api_mean_updated_score": average,
                        "delta": rating - average,
                    }
                )
        trajectories = land[episode_id]
        rows.append(
            {
                "episode_id": episode_id,
                "date": day,
                "source": task["source"],
                "date_source": task["path"] + ":manifest.csv"
                if task["date"] != "unknown"
                else api["source"]
                if api
                else None,
                "average_rating": rating,
                "minimum_rating": minimum,
                "rating_kind": kind,
                "rating_source": rating_source,
                "se_unlocked": any(r["se_unlocked"] for r in trajectories),
                "se_productive": any(r["se_productive"] for r in trajectories),
                "se_productive_trajectories": sum(r["se_productive"] for r in trajectories),
            }
        )
    return rows, {
        "evidence_path": str(raw / "date-rating-evidence.json"),
        "evidence_sha256": digest(raw / "date-rating-evidence.json"),
        "daily_api_rating_comparisons": comparisons,
        "skipped_large_metadata_files": evidence["skipped_large_files"],
    }
