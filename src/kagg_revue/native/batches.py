"""Persistent neural self-play games and deterministic paired seat schedules."""

from typing import Any

from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.native import _revue_core as native

Job = tuple[int, int, str]


def create_selfplay_batch(settings: RuntimeSettings, seeds: list[int]) -> Any:
    """Create shared two-seat games with no external actor or teacher callbacks."""
    return native.SelfPlayBatch(
        settings.environment,
        seeds,
        [0] * len(seeds),
        settings.unit_limit,
        settings.workers,
        list(settings.quantities),
    )


def paired_jobs(count: int, seed_start: int, opponents: tuple[str, ...]) -> list[Job]:
    """Assign each seed to one opponent and both seats without counting seats twice."""
    if count % 2:
        raise ValueError("paired jobs require an even physical-game count")
    return [
        (seed_start + index // 2, index % 2, opponents[(index // 2) % len(opponents)])
        for index in range(count)
    ]
