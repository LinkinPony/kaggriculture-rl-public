"""Predeclared common-seed panels and complete mirrored round robins."""

from itertools import combinations
from typing import Any

from kagg_revue.evaluation.checkpoints.config import Task


def panel(
    manifest: dict[str, Any], candidates: list[str], phase: str, games: int, seed: int, rng: int
) -> list[Task]:
    """Use 64-game batches and identical seeds for every candidate and opponent."""
    if games % 64:
        raise ValueError("panel size must be a multiple of 64 physical games")
    tasks = []
    opponents = [(row["name"], row["group"], "neural") for row in manifest["opponents"]] + [
        (name, "scripts", "script") for name in manifest["scripts"]
    ]
    for opponent_index, (opponent, group, kind) in enumerate(opponents):
        for offset in range(games // 64):
            for candidate in candidates:
                tasks.append(
                    Task(
                        name=f"{phase}-{opponent}-{candidate}-{offset:03d}",
                        phase=phase,
                        candidate=candidate,
                        opponent=opponent,
                        group=group,
                        kind=kind,
                        seed=seed + 32 * offset,
                        sampling_seed=rng + 1000 * opponent_index + offset,
                    )
                )
    return tasks


def duels(candidates: list[str], phase: str, games: int, seed: int, rng: int) -> list[Task]:
    """Record each candidate pair once, with 32 physical games per atomic batch."""
    if games % 32:
        raise ValueError("duel size must be a multiple of 32 physical games")
    return [
        Task(
            name=f"{phase}-{left}-{right}-{offset:03d}",
            phase=phase,
            candidate=left,
            opponent=right,
            group="current",
            kind="neural",
            seed=seed + 16 * offset,
            sampling_seed=rng + offset,
        )
        for left, right in combinations(candidates, 2)
        for offset in range(games // 32)
    ]
