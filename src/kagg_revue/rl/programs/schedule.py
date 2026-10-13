"""Stable update and rollout-seed schedule for conditional-program PPO."""

from __future__ import annotations


def update_range(first_update: int, target_update: int) -> range:
    """Return the remaining inclusive updates up to one absolute target."""
    if first_update < 1 or target_update < first_update:
        raise ValueError("conditional-program target must include the first update")
    return range(first_update, target_update + 1)


def rollout_seed_offset(
    rollout_seed_start: int,
    update: int,
    seeds_per_update: int,
) -> int:
    """Return the stable first seed assigned to an absolute update."""
    if rollout_seed_start < 0 or update < 1 or seeds_per_update < 1:
        raise ValueError("conditional-program rollout seed schedule is invalid")
    return rollout_seed_start + (update - 1) * seeds_per_update


__all__ = ["rollout_seed_offset", "update_range"]
