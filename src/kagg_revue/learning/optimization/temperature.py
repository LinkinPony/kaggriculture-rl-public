"""Fixed update-indexed temperature interpolation, independent of measured outcomes."""

import math


def log_cosine_temperature(
    update: int, *, greedy_updates: int, end_update: int, start: float, stop: float
) -> float:
    """Use greedy warmup, inclusive log-cosine endpoints, then the final temperature.

    Update numbering starts at one. The first stochastic update uses ``start``;
    ``end_update`` already uses ``stop``. Resuming needs only the saved completed
    update count, never an optimizer step count or accumulated floating-point phase.
    """
    if update < 1 or greedy_updates < 0 or end_update <= greedy_updates + 1:
        raise ValueError("the schedule requires a valid update and two stochastic endpoints")
    if not (math.isfinite(start) and math.isfinite(stop) and 0 < start <= stop):
        raise ValueError("temperature endpoints must be finite, positive and ordered")
    if update <= greedy_updates:
        return 0.0
    if update >= end_update:
        return stop
    progress = (update - greedy_updates - 1) / (end_update - greedy_updates - 1)
    blend = (1 - math.cos(math.pi * progress)) / 2
    return math.exp((1 - blend) * math.log(start) + blend * math.log(stop))
