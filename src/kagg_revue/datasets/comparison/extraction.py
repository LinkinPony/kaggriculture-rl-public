"""Extract compact replay diagnostics while preserving both dataset memberships."""

import hashlib
from typing import Any

import numpy as np

from kagg_revue.datasets.behavior.extraction import extract_episode


def extract(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Reuse action-aligned daily diagnostics without retaining large hash matrices."""
    rows = extract_episode((task["path"], str(task["episode_id"]), task["date"], task))
    result = []
    for row in rows:
        selected = task["memberships"].get(str(row["seat"]))
        if not selected:
            continue
        if row["name"] != selected["name"] or row["seed"] != task["seed"] or not row["complete"]:
            raise ValueError("selected dataset identity differs from the raw replay")
        hashes = np.asarray(row.pop("hashes"), dtype="<u8")
        row.pop("early")
        row["prefixes"] = {
            f"{name}:{turns}": hashlib.sha256(hashes[:turns, channel].tobytes()).hexdigest()
            for channel, name in ((0, "raw"), (1, "units"), (3, "market"))
            for turns in (1, 24, 72, 144, 719)
        }
        row["datasets"] = selected["datasets"]
        row["split"] = task["split"]
        result.append(row)
    return result
