"""Select complete daily teacher seats from explicit names or ranking evidence."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.datasets.openings.catalog import partition
from kagg_revue.datasets.ranked.metadata import replay_header


def catalog(
    entries: list[Any],
    teachers: tuple[str, ...],
    screening: Path | None,
    partition_seed: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Match exact replay names without inventing team IDs or ranking claims."""
    if teachers:
        aliases: dict[str, Any] = dict.fromkeys(teachers)
        evidence: dict[str, Any] = {
            "teacher_selection": {
                "method": "explicit-team-names",
                "names": list(teachers),
                "matching": "exact info.TeamNames; no inferred aliases or team IDs",
            }
        }
    elif screening is not None:
        ranking = json.loads(screening.read_text())["ranking_evidence"]
        aliases = ranking["aliases"]
        evidence = {"screening_sha256": digest(screening), "ranking_evidence": ranking}
    else:
        raise ValueError("teacher names or ranking evidence are required")
    tasks = []
    counts: Counter[str] = Counter()
    for source, episode, date, metadata in entries:
        info = replay_header(Path(source), f"{episode}.json")["info"]
        seats = [
            {
                "seat": seat,
                "name": name,
                **({"team_id": aliases[name]} if aliases[name] is not None else {}),
            }
            for seat, name in enumerate(info["TeamNames"])
            if name in aliases
        ]
        if not seats:
            continue
        counts.update(seat["name"] for seat in seats)
        tasks.append(
            {
                "episode_id": int(episode),
                "path": source,
                "member": f"{episode}.json",
                "date": date,
                "seats": seats,
                "seed": info["seed"],
                "split": partition(info["seed"], partition_seed),
                "create_time": str(metadata["create_time"]),
                "average_score": float(metadata["average_score"]),
                "minimum_score": float(metadata["minimum_score"]),
            }
        )
    missing = set(teachers) - counts.keys()
    if missing:
        raise ValueError(f"requested teachers absent from daily archives: {sorted(missing)}")
    evidence["selected_teacher_trajectories"] = dict(sorted(counts.items()))
    return tasks, evidence
