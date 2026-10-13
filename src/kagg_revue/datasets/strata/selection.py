"""Identify repeated execution windows using only training-partition exemplars."""

from collections import Counter, defaultdict
from typing import Any

import numpy as np
from numpy.typing import NDArray

from kagg_revue.datasets.behavior.extraction import fingerprint


def classify(
    rows: list[dict[str, Any]],
    hashes: NDArray[np.uint64],
    splits: dict[str, str],
    *,
    window: int = 24,
    minimum_support: int = 3,
    market_agreement: float = 0.9,
    market_stability: float = 0.8,
) -> tuple[NDArray[np.bool_], list[dict[str, Any]]]:
    """Assign A to stable unit templates with stable conditional market requests.

    All other windows form B+C; this does not claim to identify RL. Reference
    windows must come from at least three other complete episodes. Both seats
    of the current episode are excluded when classifying a training window.
    Held-out actions never fit a prototype or its market-mode frequencies.
    """
    selected = np.zeros(hashes.shape[:2], dtype=np.bool_)
    diagnostics = []
    for start in range(0, hashes.shape[1], window):
        stop = min(start + window, hashes.shape[1])
        keys = [fingerprint(trace[start:stop, 1].tolist()) for trace in hashes]
        references: dict[int, list[int]] = defaultdict(list)
        for index, (row, key) in enumerate(zip(rows, keys, strict=True)):
            if splits[row["episode_id"]] == "train":
                references[key].append(index)
        valid = 0
        for index, (row, key) in enumerate(zip(rows, keys, strict=True)):
            candidates = [
                ref for ref in references[key] if rows[ref]["episode_id"] != row["episode_id"]
            ]
            support = len({rows[ref]["episode_id"] for ref in candidates})
            if support < minimum_support:
                continue
            agree, stability = 0, 0.0
            for step in range(start, stop):
                counts = Counter(int(hashes[ref, step, 3]) for ref in candidates)
                mode = min(counts, key=lambda value: (-counts[value], value))
                agree += int(hashes[index, step, 3]) == mode
                stability += counts[mode] / len(candidates)
            if agree / (stop - start) >= market_agreement and (
                stability / (stop - start) >= market_stability
            ):
                selected[index, start:stop] = True
                valid += 1
        diagnostics.append({"start": start, "stop": stop, "a_trajectories": valid})
    return selected, diagnostics
