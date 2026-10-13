"""Paired outcome differences with uncertainty over independent game seeds."""

from collections import defaultdict
from typing import Any

import numpy as np


def paired_scores(
    control: dict[str, Any], candidate: dict[str, Any], *, bootstrap_seed: int = 0
) -> dict[str, Any]:
    """Compare win/draw/loss scores, keeping both seats together when resampling.

    Scores are one for a win, one half for a draw and zero for a loss. Seed
    clusters also preserve common randomness across opponents. This interval
    describes this frozen panel only, not uncertainty about unseen opponents
    or repeated model selection. It is intended for held-out confirmation.
    """
    keys = ("seed", "seat", "opponent")
    before = {tuple(game[key] for key in keys): game for game in control["games"]}
    after = {tuple(game[key] for key in keys): game for game in candidate["games"]}
    if not before or before.keys() != after.keys():
        raise ValueError("score comparisons require identical nonempty seed/seat/opponent keys")
    if len(before) != len(control["games"]) or len(after) != len(candidate["games"]):
        raise ValueError("paired panels cannot contain duplicate game identities")
    clusters: dict[int, list[float]] = defaultdict(list)
    opponents: dict[str, list[float]] = defaultdict(list)
    deltas = []
    for key, left in before.items():
        right = after[key]
        if left["outcome"] not in (-1, 0, 1) or right["outcome"] not in (-1, 0, 1):
            raise ValueError("paired scores require direct terminal WDL outcomes")
        delta = (right["outcome"] - left["outcome"]) / 2
        clusters[int(key[0])].append(delta)
        opponents[str(key[2])].append(delta)
        deltas.append(delta)
    values = np.asarray(deltas)
    totals = np.array([sum(group) for group in clusters.values()])
    counts = np.array([len(group) for group in clusters.values()])
    rng = np.random.default_rng(bootstrap_seed)
    means = []
    # Bound memory even for large frozen panels.
    for _ in range(32):
        indices = rng.integers(len(totals), size=(128, len(totals)))
        means.extend((totals[indices].sum(1) / counts[indices].sum(1)).tolist())
    return {
        "games": len(values),
        "independent_seeds": len(clusters),
        "better": int((values > 0).sum()),
        "same": int((values == 0).sum()),
        "worse": int((values < 0).sum()),
        "mean_score_change": float(values.mean()),
        "seed_cluster_bootstrap_95_interval": np.quantile(means, [0.025, 0.975]).tolist(),
        "bootstrap_seed": bootstrap_seed,
        "opponents": {
            name: {"games": len(group), "mean_score_change": float(np.mean(group))}
            for name, group in opponents.items()
        },
    }


def paired_cash(control: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Cluster cash changes by environment seed, retaining both seats and opponents."""
    paired_scores(control, candidate)  # Validate complete unique matching identities.
    old = {(game["seed"], game["seat"], game["opponent"]): game for game in control["games"]}
    clusters: dict[int, list[float]] = defaultdict(list)
    for game in candidate["games"]:
        key = game["seed"], game["seat"], game["opponent"]
        clusters[game["seed"]].append(game["cash"] - old[key]["cash"])
    means = np.asarray([np.mean(values) for values in clusters.values()])
    indices = np.random.default_rng(0).integers(len(means), size=(4096, len(means)))
    return {
        "mean_cash_change": float(means.mean()),
        "independent_seeds": len(means),
        "seed_cluster_bootstrap_95_interval": np.quantile(
            means[indices].mean(1), [0.025, 0.975]
        ).tolist(),
    }
