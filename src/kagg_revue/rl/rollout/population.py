"""Balanced per-seed scheduling for mixed training populations."""

from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Mapping, Sequence

import numpy as np

from kagg_revue.rl.data import RolloutMatch
from kagg_revue.rl.rollout.batch import Job


def _validate_weights(weights: Mapping[str, float]) -> None:
    if not weights:
        raise ValueError("opponent weights cannot be empty")
    if any(not opponent_id for opponent_id in weights):
        raise ValueError("opponent identities cannot be empty")
    if any(not math.isfinite(weight) or weight <= 0.0 for weight in weights.values()):
        raise ValueError("opponent weights must be finite and positive")
    if not math.isclose(math.fsum(weights.values()), 1.0, abs_tol=1e-9):
        raise ValueError("opponent weights must sum to one")


def _weighted_counts(total: int, weights: Mapping[str, float]) -> dict[str, int]:
    """Apportion an exact integer panel with the largest-remainder method."""
    if total < 1:
        raise ValueError("weighted opponent panel cannot be empty")
    _validate_weights(weights)
    scaled = {opponent_id: total * weight for opponent_id, weight in weights.items()}
    counts = {opponent_id: math.floor(value) for opponent_id, value in scaled.items()}
    remainder = total - sum(counts.values())
    order = {opponent_id: index for index, opponent_id in enumerate(weights)}
    ranked = sorted(
        weights,
        key=lambda opponent_id: (
            -(scaled[opponent_id] - counts[opponent_id]),
            order[opponent_id],
        ),
    )
    for opponent_id in ranked[:remainder]:
        counts[opponent_id] += 1
    return counts


def _rank_counts(
    total: int,
    weights: Mapping[str, float],
    world_size: int,
) -> tuple[dict[str, int], ...]:
    """Distribute exact global opponent counts without unbalancing rank rows."""
    if world_size < 1 or total % world_size:
        raise ValueError("weighted opponent panel must divide evenly across ranks")
    global_counts = _weighted_counts(total, weights)
    per_rank = [
        {opponent_id: count // world_size for opponent_id, count in global_counts.items()}
        for _ in range(world_size)
    ]
    rank_totals = [sum(counts.values()) for counts in per_rank]
    cursor = 0
    for opponent_id, count in global_counts.items():
        for _ in range(count % world_size):
            minimum = min(rank_totals)
            candidates = [rank for rank, value in enumerate(rank_totals) if value == minimum]
            rank = min(candidates, key=lambda value: (value - cursor) % world_size)
            per_rank[rank][opponent_id] += 1
            rank_totals[rank] += 1
            cursor = (rank + 1) % world_size
    expected = total // world_size
    if any(value != expected for value in rank_totals):
        raise RuntimeError("weighted opponent allocation produced uneven rank panels")
    return tuple(per_rank)


def weighted_rollout_jobs(
    seeds: Sequence[int],
    weights: Mapping[str, float],
    *,
    rank: int,
    world_size: int,
    sampling_seed: int,
) -> tuple[Job, ...]:
    """Sample one lineage per seed and expand external lineages to paired seats.

    Counts are exact over the global seed panel and balanced across ranks. Seeds
    are shuffled within each rank before lineages are assigned, while jobs stay
    grouped by lineage so persistent rollout lanes retain a stable shape.
    """
    if not seeds:
        raise ValueError("rollout seed panel cannot be empty")
    if len(set(seeds)) != len(seeds):
        raise ValueError("rollout seed panel must be unique")
    if rank < 0 or rank >= world_size:
        raise ValueError("rollout rank is outside the distributed world")
    allocations = _rank_counts(len(seeds), weights, world_size)
    width = len(seeds) // world_size
    rank_seeds = [int(seed) for seed in seeds[rank * width : (rank + 1) * width]]
    random.Random(sampling_seed + rank * 10_000_019).shuffle(rank_seeds)
    jobs: list[Job] = []
    offset = 0
    for opponent_id, count in allocations[rank].items():
        assigned = rank_seeds[offset : offset + count]
        offset += count
        seats = (0,) if opponent_id == "self_play" else (0, 1)
        jobs.extend((seed, seat, opponent_id) for seed in assigned for seat in seats)
    if offset != len(rank_seeds):
        raise RuntimeError("weighted opponent allocation omitted rollout seeds")
    return tuple(jobs)


def opponent_outcome_metrics(
    matches: Sequence[RolloutMatch],
    trajectory_opponents: Sequence[str],
) -> dict[str, dict[str, int | float]]:
    """Summarize the direct outcome surface for every observed opponent."""
    trajectory_counts = Counter(trajectory_opponents)
    total_trajectories = sum(trajectory_counts.values())
    match_groups: dict[str, list[RolloutMatch]] = {}
    for match in matches:
        match_groups.setdefault(match.opponent_id, []).append(match)
    unknown = set(trajectory_counts) - set(match_groups)
    if unknown:
        raise ValueError(f"training trajectories lack corresponding matches: {sorted(unknown)}")
    summaries: dict[str, dict[str, int | float]] = {}
    for opponent_id in sorted(match_groups, key=lambda value: (value != "self_play", value)):
        group = match_groups[opponent_id]
        outcomes = [match.outcome for match in group]
        games = len(group)
        summaries[opponent_id] = {
            "games": games,
            "seeds": len({match.seed for match in group}),
            "training_trajectories": trajectory_counts[opponent_id],
            "training_fraction": (
                trajectory_counts[opponent_id] / total_trajectories
                if total_trajectories
                else 0.0
            ),
            "wins": sum(outcome > 0 for outcome in outcomes),
            "ties": sum(outcome == 0 for outcome in outcomes),
            "losses": sum(outcome < 0 for outcome in outcomes),
            "win_rate": sum(outcome > 0 for outcome in outcomes) / games,
            "tie_rate": sum(outcome == 0 for outcome in outcomes) / games,
            "loss_rate": sum(outcome < 0 for outcome in outcomes) / games,
            "mean_terminal_cash": float(
                np.mean([match.terminal_cash for match in group])
            ),
            "mean_opponent_cash": float(
                np.mean([match.opponent_cash for match in group])
            ),
            "mean_cash_difference": float(
                np.mean(
                    [match.terminal_cash - match.opponent_cash for match in group]
                )
            ),
        }
    return summaries


__all__ = ["opponent_outcome_metrics", "weighted_rollout_jobs"]
