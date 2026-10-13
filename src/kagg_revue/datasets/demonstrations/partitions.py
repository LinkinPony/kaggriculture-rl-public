"""Stable whole-episode partitions with duplicate and seed grouping."""

import hashlib
import json
import zipfile
from typing import Any

from kagg_revue.bc.replay import daily_episode_metadata
from kagg_revue.datasets.demonstrations.config import Preparation, Source


def _info(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    """Read the leading replay metadata without decompressing an entire trajectory."""
    with archive.open(member) as stream:
        prefix = b""
        for _ in range(64):
            chunk = stream.read(16384)
            prefix += chunk
            text = prefix.decode("utf-8", errors="ignore")
            position = text.find('"info":')
            if position >= 0:
                try:
                    value, _ = json.JSONDecoder().raw_decode(text[position + 7 :].lstrip())
                    if not isinstance(value, dict) or not isinstance(value.get("seed"), int):
                        raise ValueError("replay header lacks an integer environment seed")
                    return value
                except json.JSONDecodeError:
                    pass
            if not chunk:
                break
    raise ValueError(f"replay header cannot be read within the metadata bound: {member}")


def tasks(config: Preparation) -> tuple[list[tuple[Source, list[str]]], dict[str, Any]]:
    """Assign every seed to one fixed partition before any label is inspected."""
    result: list[tuple[Source, list[str]]] = []
    assignments, duplicates = [], []
    episode_ids: set[str] = set()
    for source in config.sources:
        members = sorted(
            (f"{key}.json" for key in daily_episode_metadata(source.archive)),
            key=lambda member: hashlib.sha256(member.encode()).digest(),
        )
        if config.maximum_episodes_per_source is not None:
            members = members[: config.maximum_episodes_per_source]
        groups: dict[str, list[str]] = {}
        with zipfile.ZipFile(source.archive) as archive:
            for member in members:
                if member in episode_ids:
                    duplicates.append({"date": source.date, "member": member})
                    continue
                episode_ids.add(member)
                info = _info(archive, member)
                split: str = source.split
                if config.partition == "episode-seed":
                    key = f"{config.partition_seed}:{info['seed']}".encode()
                    bucket = int.from_bytes(hashlib.sha256(key).digest()[:8], "big") % 10000
                    split = (
                        "train"
                        if bucket < 9000
                        else "selection"
                        if bucket < 9500
                        else "confirmation"
                    )
                groups.setdefault(split, []).append(member)
                assignments.append(
                    {"date": source.date, "member": member, "seed": info["seed"], "split": split}
                )
        for split, selected in sorted(groups.items()):
            assigned = source.model_copy(update={"split": split})
            for start in range(0, len(selected), config.episodes_per_shard):
                result.append((assigned, selected[start : start + config.episodes_per_shard]))
    return result, {
        "method": config.partition,
        "seed": config.partition_seed,
        "assignments": assignments,
        "duplicate_episode_ids_excluded": duplicates,
    }
