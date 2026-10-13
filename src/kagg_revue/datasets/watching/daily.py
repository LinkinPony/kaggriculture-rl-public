"""Reference existing daily ZIP members without downloading another replay copy."""

import os
import re
import zipfile
from pathlib import Path
from typing import Any

from kagg_revue.datasets.watching.config import WatchSettings

DAILY = re.compile(r"kaggriculture-episodes-\d{4}-\d{2}-\d{2}\.zip$")


def reuse_daily(config: WatchSettings, manifest: dict[str, Any]) -> None:
    """Refresh local daily coverage each cycle, retaining every selected match."""
    root = config.daily_archive_root
    if root is None:
        return
    if not root.is_dir():
        raise ValueError(f"daily archive root is missing: {root}")
    episodes = {r["id"]: r for r in manifest["episodes"]}
    available = {r["episode_id"]: r for r in manifest["replays"] if r.get("storage") != "daily_zip"}
    covered: set[int] = set()
    sources = []
    for directory, children, files in os.walk(root, followlinks=False):
        children[:] = sorted(
            c
            for c in children
            if c not in {"replays", ".git"} and not (Path(directory) / c).is_symlink()
        )
        for name in sorted(files):
            path = Path(directory) / name
            if not DAILY.fullmatch(name) or path.is_symlink():
                continue
            stat = path.stat()
            used = []
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    if not re.fullmatch(r"\d+\.json", info.filename):
                        continue
                    key = int(info.filename[:-5])
                    if key not in episodes:
                        continue
                    covered.add(key)
                    if key in available:
                        continue
                    available[key] = {
                        "episode_id": key,
                        "storage": "daily_zip",
                        "path": str(path),
                        "member": info.filename,
                        "bytes": info.compress_size,
                        "archive_bytes": stat.st_size,
                        "archive_mtime_ns": stat.st_mtime_ns,
                        "member_crc32": info.CRC,
                        "raw_bytes": info.file_size,
                        "agents": episodes[key].get("agents", []),
                    }
                    used.append(key)
            if used:
                sources.append({"path": str(path), "episode_ids": sorted(used)})
    manifest["replays"] = sorted(available.values(), key=lambda r: r["episode_id"])
    manifest["daily_reuse"] = {
        "root": str(root),
        "covered_episode_ids": sorted(covered),
        "sources": sources,
        "reused_episode_ids": sorted(
            key for key, row in available.items() if row.get("storage") == "daily_zip"
        ),
    }
