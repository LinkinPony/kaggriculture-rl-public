"""Deduplicate daily and actual BC sources without fetching individual episodes."""

import hashlib
from pathlib import Path
from typing import Any

import orjson
from pydantic import Field

from kagg_revue.artifacts.io import digest
from kagg_revue.bc.replay import daily_episode_metadata
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.ranked.metadata import replay_header


class Analysis(FrozenSettings):
    """Bind immutable raw archives, historical teacher evidence and EDA scope."""

    daily_manifest: Path
    baseline_catalog: Path
    teacher_screening: Path
    output: Path
    workers: int = Field(default=16, ge=1, le=32)
    horizon: int = Field(default=144, ge=144, le=719)
    partition_seed: int = 62001


def partition(seed: int, root: int) -> str:
    """Retain the existing whole-world split, keeping both seats together."""
    bucket = int.from_bytes(hashlib.sha256(f"{root}:{seed}".encode()).digest()[:8], "big") % 10000
    return "train" if bucket < 9000 else "selection" if bucket < 9500 else "confirmation"


def tasks(config: Analysis) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Keep baseline seat membership while adding all three daily populations."""
    baseline = orjson.loads(config.baseline_catalog.read_bytes())
    selected = {}
    for row in baseline:
        selected[row["episode_id"]] = {
            **row,
            "baseline_seats": row["seats"],
            "daily": False,
            "horizon": config.horizon,
        }
    daily = orjson.loads(config.daily_manifest.read_bytes())
    evidence = orjson.loads(config.teacher_screening.read_bytes())["ranking_evidence"]
    aliases = evidence["aliases"]
    for source in daily["daily_archives"]:
        path = Path(source["path"])
        if digest(path) != source["sha256"]:
            raise ValueError("daily archive identity changed")
        for episode, metadata in daily_episode_metadata(path).items():
            episode_id = int(episode)
            header = replay_header(path, f"{episode}.json")
            info = header["info"]
            split = partition(info["seed"], config.partition_seed)
            previous = selected.get(episode_id)
            if previous and (previous["seed"] != info["seed"] or previous["split"] != split):
                raise ValueError("daily overlap changes the BC world or partition")
            selected[episode_id] = {
                "episode_id": episode_id,
                "path": str(path),
                "member": f"{episode}.json",
                "date": source["date"],
                "seed": info["seed"],
                "split": split,
                "daily": True,
                "baseline_seats": previous["baseline_seats"] if previous else [],
                "historical_teacher_seats": [
                    {"seat": seat, "team_id": aliases[name], "name": name}
                    for seat, name in enumerate(info["TeamNames"])
                    if name in aliases
                ],
                "average_match_rating": metadata["average_score"],
                "horizon": config.horizon,
            }
    result = sorted(selected.values(), key=lambda row: row["episode_id"])
    sources = {str(path): digest(path) for path in sorted({Path(r["path"]) for r in result})}
    return result, {
        "daily": daily,
        "baseline_catalog_sha256": digest(config.baseline_catalog),
        "teacher_screening_sha256": digest(config.teacher_screening),
        "teacher_evidence": evidence,
        "raw_source_sha256": sources,
        "episodes": len(result),
        "baseline_episodes": len(baseline),
        "daily_episodes": sum(r["daily"] for r in result),
        "overlap_episodes": sum(bool(r["baseline_seats"]) and r["daily"] for r in result),
        "scope": "Existing BC selected seats plus all daily seats; no new submission listings "
        "or individual replay downloads. Historical teacher membership is snapshot evidence, "
        "not a current ranking or a submission identity.",
    }
