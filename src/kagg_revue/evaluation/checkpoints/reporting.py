"""Equal-family paired-seed estimates with simultaneous candidate comparisons."""

import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from kagg_revue.artifacts.io import write_json


def read_games(directory: Path) -> list[dict[str, Any]]:
    """Read only fully committed batches; incomplete batches are never counted."""
    return [
        row
        for path in sorted((directory / "batches").glob("*.json"))
        for row in json.loads(path.read_text())["games"]
    ]


def panel_values(
    manifest: dict[str, Any], rows: list[dict[str, Any]], candidates: list[str]
) -> tuple[NDArray[np.float64], dict[str, NDArray[np.float64]], list[int]]:
    """Keep both seats and all opponent families inside each environment-seed cluster."""
    groups = {row["name"]: row["group"] for row in manifest["opponents"]}
    groups.update({name: "scripts" for name in manifest["scripts"]})
    opponents = sorted(groups)
    seeds = sorted({row["seed"] for row in rows})
    if not seeds or not candidates:
        raise ValueError("panel requires nonempty candidates and completed games")
    indexed = {}
    for row in rows:
        key = row["candidate"], row["opponent"], row["seed"], row["seat"]
        if key in indexed or row["outcome"] not in (-1, 0, 1):
            raise ValueError("duplicate identity or non-WDL game")
        if row["group"] != groups.get(row["opponent"]):
            raise ValueError("opponent group differs from the frozen protocol")
        indexed[key] = (row["outcome"] + 1) / 2
    expected = {
        (candidate, opponent, seed, seat)
        for candidate in candidates
        for opponent in opponents
        for seed in seeds
        for seat in (0, 1)
    }
    if set(indexed) != expected:
        raise ValueError("panel is incomplete or contains out-of-panel games")
    values = np.array(
        [
            [
                [[indexed[candidate, opponent, seed, seat] for seat in (0, 1)] for seed in seeds]
                for opponent in opponents
            ]
            for candidate in candidates
        ],
        dtype=np.float64,
    ).mean(axis=3)
    weights = manifest["group_weights"]
    if not np.isclose(sum(weights.values()), 1.0):
        raise ValueError("opponent-family weights must sum to one")
    family = {
        group: values[
            :, [i for i, opponent in enumerate(opponents) if groups[opponent] == group]
        ].mean(axis=1)
        for group in weights
    }
    combined = np.zeros((len(candidates), len(seeds)), dtype=np.float64)
    for group, weight in weights.items():
        combined += weight * family[group]
    return combined, family, seeds


def summarize(
    manifest: dict[str, Any], directory: Path, candidates: list[str], *, role: str
) -> dict[str, Any]:
    """Report paired differences without treating correlated games as independent trials."""
    rows = read_games(directory)
    values, family, seeds = panel_values(manifest, rows, candidates)
    means = values.mean(axis=1)
    indices = np.random.default_rng(9292026).integers(len(seeds), size=(8192, len(seeds)))
    bootstrap = np.stack([v[indices].mean(axis=1) for v in values], axis=1)
    winner = int(means.argmax())
    centered = bootstrap - means[None, :]
    # The range is the maximum absolute error over every candidate-pair difference.
    # This yields a simultaneous interval even when the displayed leader is selected.
    radius = float(np.quantile(centered.max(axis=1) - centered.min(axis=1), 0.95))
    records = []
    for i, name in enumerate(candidates):
        own = [row for row in rows if row["candidate"] == name]
        records.append(
            {
                "candidate": name,
                "composite_score": float(means[i]),
                "score_ci95": np.quantile(bootstrap[:, i], [0.025, 0.975]).tolist(),
                "family_scores": {group: float(v[i].mean()) for group, v in family.items()},
                "games": len(own),
                "wins": sum(row["outcome"] > 0 for row in own),
                "draws": sum(row["outcome"] == 0 for row in own),
                "losses": sum(row["outcome"] < 0 for row in own),
                "raw_win_rate": float(np.mean([row["outcome"] > 0 for row in own])),
                "mean_cash_margin": float(
                    np.mean([row["cash"] - row["opponent_cash"] for row in own])
                ),
                "leader_minus_candidate": float(means[winner] - means[i]),
                "leader_difference_simultaneous_ci95": [
                    float(means[winner] - means[i] - radius),
                    float(means[winner] - means[i] + radius),
                ]
                if i != winner
                else [0.0, 0.0],
            }
        )
    result = {
        "role": role,
        "candidate_order": candidates,
        "leader": candidates[winner],
        "seeds": seeds,
        "independent_environment_seeds": len(seeds),
        "total_games": len(rows),
        "group_weights": manifest["group_weights"],
        "results": sorted(records, key=lambda r: -r["composite_score"]),
        "simultaneous_pairwise_radius": radius,
        "bootstrap_resamples": len(indices),
        "scope": manifest["scope"],
    }
    write_json(directory / "report.json", result)
    return result


def round_robin(directory: Path, candidates: list[str]) -> dict[str, Any]:
    """Count each physical duel once and invert its result for the opposing candidate."""
    rows = read_games(directory)
    matrix: dict[str, dict[str, list[float]]] = {name: {} for name in candidates}
    identities = set()
    for row in rows:
        left, right = row["candidate"], row["opponent"]
        identity = left, right, row["seed"], row["seat"]
        if identity in identities or left == right:
            raise ValueError("round robin repeats a game or plays itself")
        identities.add(identity)
        score = (row["outcome"] + 1) / 2
        matrix[left].setdefault(right, []).append(score)
        matrix[right].setdefault(left, []).append(1 - score)
    if any(set(matrix[name]) != set(candidates) - {name} for name in candidates):
        raise ValueError("round robin does not cover every candidate pair")
    counts = {len(games) for opponents in matrix.values() for games in opponents.values()}
    if len(counts) != 1:
        raise ValueError("round-robin pairs have unequal samples")
    scores = {
        name: {opponent: float(np.mean(games)) for opponent, games in opponents.items()}
        for name, opponents in matrix.items()
    }
    rankings: list[dict[str, Any]] = [
        {"candidate": name, "score": float(np.mean(list(opponents.values())))}
        for name, opponents in scores.items()
    ]
    result = {
        "physical_games": len(rows),
        "games_per_pair": counts.pop(),
        "scores": scores,
        "ranking": sorted(rankings, key=lambda row: -row["score"]),
    }
    write_json(directory / "report.json", result)
    return result
