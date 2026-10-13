"""Rank public submissions by decisive games against shared opponents."""

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import numpy as np

from kagg_revue.datasets.sequences.window import _timestamp

Outcome = tuple[int, int, float]


def outcomes(
    manifests: Iterable[dict[str, Any]], since: datetime, excluded: set[int]
) -> list[Outcome]:
    """Deduplicate completed public games; a tie carries no Bradley-Terry evidence."""
    games: dict[int, Outcome] = {}
    for manifest in manifests:
        for episode in manifest["episodes"]:
            agents = episode["agents"]
            if (
                episode.get("state") != "COMPLETED"
                or episode.get("type") != "EPISODE_TYPE_PUBLIC"
                or len(agents) != 2
                or _timestamp(episode["createTime"]) < since
                or any(agent["submissionId"] in excluded for agent in agents)
                or agents[0]["reward"] == agents[1]["reward"]
            ):
                continue
            first, second = agents
            games[episode["id"]] = (
                first["submissionId"],
                second["submissionId"],
                float(first["reward"] > second["reward"]),
            )
    return [games[key] for key in sorted(games)]


def ratings(
    games: list[Outcome], precision: float, *, tolerance: float = 1e-7, iterations: int = 20000
) -> dict[int, tuple[float, float]]:
    """Fit logit strengths under a zero-mean Gaussian prior with damped Newton steps.

    The returned deviation uses the diagonal of the posterior curvature, so it
    ignores covariance between submissions that met the same opponents.
    """
    players = sorted({game[0] for game in games} | {game[1] for game in games})
    index = {player: position for position, player in enumerate(players)}
    first = np.array([index[game[0]] for game in games])
    second = np.array([index[game[1]] for game in games])
    result = np.array([game[2] for game in games])
    strength = np.zeros(len(players))
    for _ in range(iterations):
        probability = 1 / (1 + np.exp(strength[second] - strength[first]))
        residual = result - probability
        weight = probability * (1 - probability)
        gradient = -precision * strength
        np.add.at(gradient, first, residual)
        np.add.at(gradient, second, -residual)
        curvature = np.full(len(players), precision)
        np.add.at(curvature, first, weight)
        np.add.at(curvature, second, weight)
        step = gradient / curvature
        strength += 0.5 * step
        if np.abs(step).max() < tolerance:
            break
    else:
        raise ValueError("submission strength fit did not converge")
    return {
        player: (float(strength[position]), float(curvature[position] ** -0.5))
        for player, position in index.items()
    }


def select(
    candidates: dict[int, dict[str, Any]],
    strength: dict[int, tuple[float, float]],
    margin: float,
    uncertainty: float,
) -> tuple[dict[int, list[str]], float]:
    """Keep versions near the strongest; add a qualifying team's unresolved newest one.

    A newly submitted version has met few strong opponents, so its estimate is
    wide. It is retained only when its upper bound still reaches the threshold.
    """
    rated = {key: row for key, row in candidates.items() if key in strength}
    if not rated:
        raise ValueError("no rated candidate submission")
    threshold = max(strength[key][0] for key in rated) - margin
    chosen = {key: ["within_margin"] for key in rated if strength[key][0] >= threshold}
    for team in sorted({rated[key]["team"] for key in chosen}):
        newest = max(
            (key for key in rated if rated[key]["team"] == team),
            key=lambda key: _timestamp(rated[key]["dateSubmitted"]),
        )
        rating, deviation = strength[newest]
        if newest not in chosen and rating + uncertainty * deviation >= threshold:
            chosen[newest] = ["newest_unresolved"]
    return chosen, threshold
