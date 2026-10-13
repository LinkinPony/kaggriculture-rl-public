"""Freeze a deduplicated replay catalog while preserving original source files."""

import csv
import io
import json
import os
import re
import subprocess
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.behavior.acquisition import acquire

DAILY = re.compile(r"kaggriculture-episodes-(\d{4}-\d{2}-\d{2})\.zip$")
REPLAY = re.compile(r"(?:episode-)?(\d+)(?:-replay)?\.json(?:\.gz)?$")


def discover(root: Path) -> tuple[list[Path], list[tuple[str, Path]]]:
    """List repository raw inputs without following directory symlinks."""
    archives, replays = [], []
    for directory, children, files in os.walk(root, followlinks=False):
        children[:] = sorted(c for c in children if not (Path(directory) / c).is_symlink())
        for filename in sorted(files):
            path = Path(directory) / filename
            if path.is_symlink():
                continue
            if DAILY.fullmatch(filename):
                archives.append(path)
            match = REPLAY.fullmatch(filename)
            if match and (path.parent.name in {"replays", "incomplete"} or "-replay" in filename):
                replays.append((match[1], path))
    return archives, replays


def collect(root: Path, raw: Path, include_public: bool) -> dict[str, Any]:
    """Merge all local daily dates through the latest index, plus local replays."""
    manifest_path = raw / "merged-manifest.json"
    if manifest_path.exists():
        result: dict[str, Any] = json.loads(manifest_path.read_text())
        if result["include_public"] != include_public or result["root"] != str(root):
            raise ValueError("existing frozen catalog uses different collection settings")
        if digest(Path(result["catalog"]["path"])) != result["catalog"]["sha256"]:
            raise ValueError("frozen catalog changed")
        for source in result["files"]:
            if digest(Path(source["path"])) != source["sha256"]:
                raise ValueError(f"frozen input changed: {source['path']}")
        return result
    archives, public = discover(root)
    raw.mkdir(parents=True, exist_ok=True)
    index = raw / "kaggriculture-episodes-index.zip"
    if not index.exists():
        subprocess.run(
            [
                "kaggle",
                "datasets",
                "download",
                "-d",
                "kaggle/kaggriculture-episodes-index",
                "-p",
                str(raw),
                "--quiet",
            ],
            check=True,
        )
    with zipfile.ZipFile(index) as zipped:
        dates = sorted(
            csv.DictReader(io.StringIO(zipped.read("manifest.csv").decode())),
            key=lambda row: row["date"],
        )
    first = min((p.stem[-10:] for p in archives), default=dates[-1]["date"])
    selected = [row for row in dates if row["date"] >= first]
    expected_days = (date.fromisoformat(dates[-1]["date"]) - date.fromisoformat(first)).days + 1
    if len(selected) != expected_days:
        raise ValueError("daily index has gaps in the local-to-latest date range")
    daily, tasks = acquire(raw, sorted({p.parent for p in archives}), len(selected))
    catalog: dict[str, Any] = {}
    files = {
        item["path"]: {key: item[key] for key in ("path", "sha256")}
        for item in daily["daily_archives"]
    }
    files[str(index)] = {"path": str(index), "sha256": digest(index)}
    daily_copies = 0
    daily_by_date = {item["date"]: item for item in daily["daily_archives"]}
    for path in archives:
        if str(path) in files:
            continue
        sha256 = digest(path)
        if sha256 != daily_by_date[path.stem[-10:]]["sha256"]:
            raise ValueError(f"local copies of the same daily archive differ: {path}")
        files[str(path)] = {"path": str(path), "sha256": sha256}
        daily_copies += 1
    for path, episode_id, day, metadata in tasks:
        catalog[episode_id] = {
            "episode_id": episode_id,
            "date": day,
            "source": "daily",
            "path": path,
            "member": f"{episode_id}.json",
            "create_time": metadata["create_time"],
            "locations": [{"path": path, "member": f"{episode_id}.json"}],
        }
    public_duplicates = 0
    for episode_id, path in public if include_public else []:
        files[str(path)] = {"path": str(path), "sha256": digest(path)}
        location = {"path": str(path), "member": None}
        if episode_id in catalog:
            catalog[episode_id]["locations"].append(location)
            public_duplicates += 1
        else:
            catalog[episode_id] = {
                "episode_id": episode_id,
                "date": "unknown",
                "source": "local_supplement",
                **location,
                "create_time": None,
                "locations": [location],
            }
    catalog_path = raw / "catalog.json"
    write_json(catalog_path, sorted(catalog.values(), key=lambda row: int(row["episode_id"])))
    result = {
        "schema": "daily-land-merged-source-v1",
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "root": str(root),
        "include_public": include_public,
        "daily_manifest": {
            "path": str(raw / "manifest.json"),
            "sha256": digest(raw / "manifest.json"),
        },
        "source_index": daily["source_index"],
        "daily_dates": [r["date"] for r in selected],
        "daily_episodes": len(tasks),
        "unique_episodes": len(catalog),
        "local_supplement_episodes": len(catalog) - len(tasks),
        "duplicate_daily_archives": daily_copies,
        "duplicate_local_replays": public_duplicates,
        "catalog": {"path": str(catalog_path), "sha256": digest(catalog_path)},
        "files": list(files.values()),
        "scope": "All local official daily archives plus missing dates through the latest index; "
        "optionally merge existing individual replays by EpisodeId, preferring daily. "
        "Original archives and replays remain in place; catalog records source locations. "
        "Earlier index days absent locally are not backfilled. Public replay dates are "
        "unknown unless provided by daily metadata; no date is inferred from file mtime.",
    }
    write_json(manifest_path, result)
    return result
