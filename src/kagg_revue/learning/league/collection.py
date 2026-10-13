"""Captured neural policies share one turn barrier across native game batches."""

import time
from typing import Any

import numpy as np
import torch

from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.distributed import rank_world
from kagg_revue.learning.league.batches import LeagueBatch
from kagg_revue.learning.league.config import League
from kagg_revue.learning.optimization.objectives import terminal_rewards
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.inference import ActorRuntime


def schedule(
    config: League, update: int, rank: int, world: int
) -> tuple[list[int], np.ndarray[Any, np.dtype[np.int64]]]:
    """Assign unique seeds and alternate which member occupies each physical seat."""
    start = config.experiment.train_seed + (update - 1) * config.experiment.games
    seeds, owners = [], []
    offset = 0
    for left, right, games in config.matchups():
        per_pair = games // world
        for local in range(per_pair):
            seeds.append(start + offset + rank * per_pair + local)
            owners.append((left, right) if local % 2 == 0 else (right, left))
        offset += games
    return seeds, np.asarray(owners, dtype=np.int64)


def collect(
    config: League,
    settings: RuntimeSettings,
    runtimes: list[ActorRuntime],
    update: int,
    *,
    concurrent_inference: bool = True,
) -> tuple[list[Rollout], dict[str, Any]]:
    """Record only the owning policy's actions and behavior likelihoods on each tape."""
    rank, world = rank_world()
    seeds, owners = schedule(config, update, rank, world)
    layout = runtimes[0].policy.layout
    device = runtimes[0].device
    batch = LeagueBatch(config, settings, seeds, owners)
    positions = [np.flatnonzero(owners.ravel() == index) for index in range(len(config.members))]
    count = len(positions[0])
    if any(len(p) != count for p in positions) or any(len(r.host) != count for r in runtimes):
        raise ValueError("league policies require equal complete-trajectory batches")
    host = torch.empty(
        (2 * len(seeds), layout.observation.features),
        dtype=torch.float16,
        pin_memory=device.type == "cuda",
    )
    selected = np.empty((2 * len(seeds), layout.factors), np.int64)
    observations = [
        torch.empty(
            (layout.decisions, count, layout.observation.features),
            dtype=torch.float16,
            device=device,
        )
        for _ in config.members
    ]
    actions = [
        torch.empty((layout.decisions, count, layout.factors), dtype=torch.int16, device=device)
        for _ in config.members
    ]
    probabilities = [torch.empty_like(tape, dtype=torch.float32) for tape in actions]
    streams = (
        [torch.cuda.Stream(device=device) for _ in runtimes]  # type: ignore[no-untyped-call]
        if concurrent_inference and device.type == "cuda"
        else []
    )
    encoding = inference = advance = 0.0
    started = time.perf_counter()
    for decision, span in enumerate(layout.spans):
        phase = time.perf_counter()
        batch.observe_selfplay_into(host.numpy())
        for index, runtime in enumerate(runtimes):
            np.take(host.numpy(), positions[index], axis=0, out=runtime.host.numpy())
        encoding += time.perf_counter() - phase
        phase = time.perf_counter()
        current = torch.cuda.current_stream(device) if device.type == "cuda" else None
        for index, runtime in enumerate(runtimes):
            if streams:
                # Parameters and tape allocations belong to the caller's stream.
                # Each policy owns a separate graph pool and stable I/O buffers.
                assert current is not None
                streams[index].wait_stream(current)
            with torch.cuda.stream(streams[index] if streams else None):
                chosen, likelihood = runtime.act(decision, synchronize=False)
                observations[index][decision].copy_(runtime.observations)
                actions[index][decision].copy_(chosen)
                probabilities[index][decision].copy_(likelihood)
        for stream in streams:
            assert current is not None
            current.wait_stream(stream)
        if device.type == "cuda":
            torch.cuda.current_stream(device).synchronize()
        inference += time.perf_counter() - phase
        phase = time.perf_counter()
        for index, runtime in enumerate(runtimes):
            selected[positions[index]] = runtime.selected.numpy()
        batch.advance_programs(selected, span, layout.capacity)
        advance += time.perf_counter() - phase
    if (
        batch.completed_games != len(seeds)
        or batch.transitions != len(seeds) * layout.observation.turns
    ):
        raise ValueError("league failed to finish all physical games")
    cash = batch.cash()
    rewards = terminal_rewards(
        cash,
        cash_weight=settings.ppo.cash_weight,
        cash_scale=settings.ppo.cash_scale,
        win_weight=settings.ppo.win_weight,
        cash_margin=settings.ppo.cash_margin,
    )
    timing = {
        "rollout_seconds": time.perf_counter() - started,
        "encoding_seconds": encoding,
        "inference_seconds": inference,
        "native_seconds": advance,
    }
    tape = []
    for index, positions_i in enumerate(positions):
        cash_i = cash.reshape(-1)[positions_i]
        cash_other = cash.reshape(-1)[positions_i ^ 1]
        opponent_names = tuple(config.participants[owners.ravel()[p ^ 1]] for p in positions_i)
        tape.append(
            Rollout(
                observations[index].flatten(0, 1),
                actions[index].flatten(0, 1),
                probabilities[index].flatten(0, 1),
                torch.arange(layout.decisions, device=device).repeat_interleave(count),
                torch.tensor(
                    rewards.reshape(-1)[positions_i], dtype=torch.float32, device=device
                ).repeat(layout.decisions),
                np.stack((cash_i, cash_other), axis=1),
                timing,
                torch.tensor(
                    np.where(owners.ravel()[positions_i ^ 1] == index, 0.5, 1.0),
                    dtype=torch.float32,
                    device=device,
                ).repeat(layout.decisions),
                opponent_names,
                runtimes[index].temperature,
            )
        )
    pairs = {}
    offset = 0
    for left, right, games in config.matchups():
        per_pair = games // world
        region = slice(offset, offset + per_pair)
        offset += per_pair
        left_cash = np.where(owners[region, 0] == left, cash[region, 0], cash[region, 1])
        right_cash = np.where(owners[region, 0] == left, cash[region, 1], cash[region, 0])
        margin = left_cash - right_cash
        pairs[f"{config.participants[left]}_vs_{config.participants[right]}"] = {
            "games": per_pair,
            "wins": int((margin > 0).sum()),
            "draws": int((margin == 0).sum()),
            "losses": int((margin < 0).sum()),
            "cash_left_sum": float(left_cash.sum()),
            "cash_right_sum": float(right_cash.sum()),
            "absolute_cash_difference_sum": float(np.abs(margin).sum()),
        }
    return tape, {"rank": rank, "physical_games": len(seeds), "pairs": pairs, **timing}
