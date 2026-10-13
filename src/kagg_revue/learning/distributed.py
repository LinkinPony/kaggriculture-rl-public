"""Synchronous ranks, population-preserving seed shards, and complete RNG recovery."""

import os
from typing import Any

import torch
import torch.distributed as dist

from kagg_revue.learning.config import Experiment


def rank_world() -> tuple[int, int]:
    """Return the local rank geometry, including the single-device path."""
    return (dist.get_rank(), dist.get_world_size()) if dist.is_initialized() else (0, 1)


def seed_shard(
    config: Experiment,
    update: int,
    rank: int,
    world: int,
    *,
    counts: tuple[int, int] | None = None,
) -> list[int]:
    """Preserve the original self-play/history seed assignments across devices."""
    history = int(config.games * config.population.fraction)
    scripts = (
        int(config.games * config.script_population.fraction) if config.script_population else 0
    )
    if config.population.sampled_counts and counts is None:
        raise ValueError("sampled seed shards require the history and script counts")
    if counts is not None:
        history, scripts = counts
    selfplay = config.games - history - scripts
    if not 0 <= rank < world or selfplay % world or history % (2 * world) or scripts % (2 * world):
        raise ValueError("seed shards must balance populations and both historical seats")
    start = config.train_seed + (update - 1) * config.games
    return [
        *range(start + rank * selfplay // world, start + (rank + 1) * selfplay // world),
        *range(
            start + selfplay + rank * scripts // world,
            start + selfplay + (rank + 1) * scripts // world,
        ),
        *range(
            start + selfplay + scripts + rank * history // world,
            start + selfplay + scripts + (rank + 1) * history // world,
        ),
    ]


def bind_cpus(rank: int, world: int) -> list[int]:
    """Partition only the container's permitted CPU affinity, without oversubscription."""
    cpus = sorted(os.sched_getaffinity(0))
    assigned = cpus[rank * len(cpus) // world : (rank + 1) * len(cpus) // world]
    if not assigned:
        raise ValueError("every GPU worker requires at least one permitted CPU")
    os.sched_setaffinity(0, assigned)
    return assigned


def gather(value: Any) -> list[Any]:
    """Gather small control records; rollout tensors remain on their owning GPU."""
    _, world = rank_world()
    result: list[Any] = [None] * world
    if world == 1:
        result[0] = value
    else:
        dist.all_gather_object(result, value)
    return result


def rng_snapshot(device: torch.device) -> dict[str, Any]:
    """Save each worker's CPU and CUDA RNG at an atomic optimizer boundary."""
    local = {"cpu": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state(device)}
    workers = gather(local)
    return {**workers[0], "workers": workers, "world_size": len(workers)}


def restore_rng(
    payload: dict[str, Any],
    device: torch.device,
    config: Experiment,
    *,
    state: dict[str, Any] | None = None,
) -> None:
    """Restore all rank streams; derive new streams only at an explicit hardware upgrade."""
    rank, world = rank_world()
    saved = payload["rng"]
    workers = saved.get("workers")
    if workers is not None:
        if len(workers) != world:
            transition = ((state or {}).get("execution_history") or [{}])[-1]
            previous = transition.get("previous_protocol", {}).get("execution")
            if (
                not state
                or not config.execution
                or transition.get("execution") != config.execution.model_dump(mode="json")
                or len(config.execution.devices) != world
                or (len(previous["devices"]) if previous else 1) != len(workers)
                or transition.get("completed_update") != payload.get("update")
                or state["completed_update"] != payload.get("update")
                or transition.get("checkpoint_sha256") != state["members"][state["latest"]]
            ):
                raise ValueError("checkpoint RNG worker count differs from execution devices")
            if rank >= len(workers):
                torch.manual_seed(config.seed + 1000000007 * rank + int(payload["update"]))
                return
        saved = workers[rank]
    elif rank:
        # The old run had one stream. Record this one-time transition in its
        # hardware-upgrade ledger; subsequent checkpoints save exact rank RNGs.
        torch.manual_seed(config.seed + 1000000007 * rank + int(payload["update"]))
        return
    torch.set_rng_state(saved["cpu"].cpu())
    torch.cuda.set_rng_state(saved["cuda"].cpu(), device)


def any_stop(requested: bool, device: torch.device) -> bool:
    """Stop all ranks at the same update boundary, including a signal to one worker."""
    value = torch.tensor(int(requested), device=device)
    if dist.is_initialized():
        dist.all_reduce(value, op=dist.ReduceOp.MAX)
    return bool(value)


def barrier() -> None:
    """Wait for rank-zero artifact or evaluation work."""
    if dist.is_initialized():
        dist.barrier()
