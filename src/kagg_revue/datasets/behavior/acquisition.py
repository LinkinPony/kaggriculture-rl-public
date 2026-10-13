"""Preserve the official index and authenticate reused or downloaded archives."""

import csv
import io
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.bc.replay import archive_identity, daily_episode_metadata


def acquire(raw: Path, reuse: list[Path], days: int) -> tuple[dict[str, Any], list[Any]]:
    """Download missing latest dates and keep all original data in data/external."""
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
    with zipfile.ZipFile(index) as archive:
        dates = sorted(
            csv.DictReader(io.StringIO(archive.read("manifest.csv").decode())),
            key=lambda x: x["date"],
        )[-days:]
    if len(dates) != days:
        raise ValueError("official index has fewer dates than requested")
    records, tasks = [], []
    seen: set[str] = set()
    for row in dates:
        filename = f"{row['daily_dataset_slug']}.zip"
        candidates = [raw / filename, *(directory / filename for directory in reuse)]
        source = next((p for p in candidates if p.exists()), None)
        if source is None:
            subprocess.run(
                [
                    "kaggle",
                    "datasets",
                    "download",
                    "-d",
                    f"kaggle/{row['daily_dataset_slug']}",
                    "-p",
                    str(raw),
                    "--quiet",
                ],
                check=True,
            )
            source = raw / filename
        identity = archive_identity(source)
        metadata = daily_episode_metadata(source)
        if len(metadata) != int(row["episode_count"]) or identity["uncompressed_bytes"] != int(
            row["total_bytes"]
        ):
            raise ValueError(f"index count or size mismatch: {source}")
        for key, item in metadata.items():
            if key in seen or not str(item["create_time"]).startswith(row["date"]):
                raise ValueError(f"duplicate episode or incorrect UTC date: {key}")
            seen.add(key)
            tasks.append((str(source), key, row["date"], item))
        records.append({**identity, **row, "reused": source.parent != raw})
    manifest = {
        "schema": "daily-behavior-source-v1",
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "source_index": {
            "path": str(index),
            "sha256": digest(index),
            "url": "https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index",
        },
        "selection": "latest index dates; every episode, both seats",
        "license": "CC0-1.0",
        "daily_archives": records,
    }
    write_json(raw / "manifest.json", manifest)
    return manifest, tasks
