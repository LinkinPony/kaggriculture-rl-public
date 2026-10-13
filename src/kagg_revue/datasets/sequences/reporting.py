"""Summarize authenticated teacher coverage and complete-sequence storage."""

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from kagg_revue.policy.contracts import ContractLayout


def summarize(directory: Path, manifest: dict[str, Any], layout: ContractLayout) -> dict[str, Any]:
    """Count actual retained teacher masks and validate every array's geometry."""
    teachers: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "trajectories": 0,
            "context_rows": 0,
            "usable_rows": 0,
            "dates": Counter(),
            "splits": Counter(),
        }
    )
    storage = 0
    observation = layout.observation
    for record in manifest["shards"]:
        arrays = {
            key: np.load(directory / record[key], mmap_mode="r")
            for key in ("observations", "actions", "eligible")
        }
        seats = record["task"]["seats"]
        mask = arrays["eligible"]
        shape = (observation.turns, len(seats))
        if (
            mask.shape != shape
            or mask.dtype != np.bool_
            or arrays["observations"].shape != (*shape, observation.features)
            or arrays["observations"].dtype != np.float16
            or arrays["actions"].shape != (*shape, layout.factors)
            or arrays["actions"].dtype != np.int16
            or int(mask.sum()) != record["usable_rows"]
            or mask.size != record["rows"]
        ):
            raise ValueError("stored sequence geometry or supervision counts differ")
        storage += sum((directory / record[key]).stat().st_size for key in arrays)
        for column, seat in enumerate(seats):
            teacher = teachers[seat.get("teacher_name", seat["name"])]
            teacher["trajectories"] += 1
            teacher["context_rows"] += shape[0]
            teacher["usable_rows"] += int(mask[:, column].sum())
            teacher["dates"][record["source_date"]] += 1
            teacher["splits"][record["split"]] += 1
    return {
        "source_episodes": manifest["sources"].get("episodes")
        or sum(int(r["episode_count"]) for r in manifest["sources"]["daily_archives"]),
        "source_dates": manifest["sources"].get("dates")
        or [r["date"] for r in manifest["sources"]["daily_archives"]],
        "encoded_episodes": len(manifest["shards"]),
        "excluded_episodes": len(manifest["exclusions"]),
        "trajectories": sum(t["trajectories"] for t in teachers.values()),
        "context_rows": sum(t["context_rows"] for t in teachers.values()),
        "usable_rows": sum(t["usable_rows"] for t in teachers.values()),
        "quantity_clipped_rows": sum(r["quantity_clipped_rows"] for r in manifest["shards"]),
        "array_bytes": storage,
        "teachers": dict(sorted(teachers.items())),
    }
