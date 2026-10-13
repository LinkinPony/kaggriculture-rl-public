"""Paired changes against the same reacting opponents, worlds and seats."""

from typing import Any

import numpy as np


def paired_changes(
    rows: list[dict[str, Any]], baseline: str, candidate: str
) -> list[dict[str, Any]]:
    """Resample world seeds after pairing controls; distinguish own cash from margin."""
    keyed = {(r["variant"], r["opponent"], r["seed"], r["seat"]): r for r in rows}
    if len(keyed) != len(rows):
        raise ValueError("duplicate physical game identities")
    panel = {(r["opponent"], r["seed"], r["seat"]) for r in rows if r["variant"] == baseline}
    if not panel or panel != {
        (r["opponent"], r["seed"], r["seat"]) for r in rows if r["variant"] == candidate
    }:
        raise ValueError("candidate and control panels must match exactly")
    result = []
    opponents = sorted({opponent for opponent, _, _ in panel})
    for opponent in [*opponents, "all"]:
        keys = sorted(key for key in panel if opponent == "all" or key[0] == opponent)
        seeds = sorted({key[1] for key in keys})
        if any({key[2] for key in keys if key[1] == seed} != {0, 1} for seed in seeds):
            raise ValueError("paired comparisons require both seats")
        metrics: dict[str, Any] = {}
        for metric in ("cash", "opponent_cash", "margin", "points"):

            def value(row: dict[str, Any], field: str = metric) -> float:
                return float((row["outcome"] + 1) / 2 if field == "points" else row[field])

            deltas = {
                key: value(keyed[candidate, *key]) - value(keyed[baseline, *key]) for key in keys
            }
            means = np.array(
                [
                    np.mean([delta for key, delta in deltas.items() if key[1] == seed])
                    for seed in seeds
                ]
            )
            rng = np.random.default_rng(920001)
            samples = means[rng.integers(0, len(seeds), (10000, len(seeds)))].mean(1)
            metrics[metric] = {
                "mean_change": float(means.mean()),
                "seed_bootstrap_95": np.quantile(samples, [0.025, 0.975]).tolist(),
                "positive_seeds": int(np.sum(means > 0)),
                "zero_seeds": int(np.sum(means == 0)),
                "negative_seeds": int(np.sum(means < 0)),
            }
        result.append({"opponent": opponent, "games_per_variant": len(keys), "metrics": metrics})
    return result
