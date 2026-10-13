"""Qualification of PFSP choices, evidence persistence and complete optimizer continuation."""

import copy
from pathlib import Path
from typing import Any

import torch

from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.pool import snapshot
from kagg_revue.learning.matchmaking.scheduler import Matchmaker


def finite(value: Any) -> bool:
    """Check every tensor in a nested checkpoint, including optimizer moments."""
    if isinstance(value, torch.Tensor):
        return bool(torch.isfinite(value).all())
    if isinstance(value, dict):
        return all(finite(item) for item in value.values())
    if isinstance(value, list | tuple):
        return all(finite(item) for item in value)
    return True


def verify(
    config: Experiment, original: dict[str, Any], final: dict[str, Any], directory: Path
) -> dict[str, Any]:
    """Reconstruct every draw from pre-update evidence and verify full saved continuation."""
    simulation = copy.deepcopy(original)
    simulation["protocol"] = config.model_dump(mode="json")
    scheduler = Matchmaker(config, simulation)
    world = len(config.execution.devices) if config.execution else 1
    rows = final["records"][original["completed_update"] :]
    for row in rows:
        update = row["update"]
        match = scheduler.select(update, world)
        opponent = row["opponent"]["path"] if row["opponent"] else ""
        if match.report != row["pfsp"] or match.history != opponent:
            raise ValueError("PFSP draw differs from replayed pre-update evidence")
        scheduler.observe(match, update, row["populations"])
        name = f"checkpoints/update-{update:06d}.pt"
        if name in final["members"]:
            simulation["members"][name] = final["members"][name]
            if update % config.population.snapshot_interval == 0:
                snapshot(config, simulation, name)
    if simulation["pfsp"] != final["pfsp"] or simulation["pool"] != final["pool"]:
        raise ValueError("PFSP statistics or historical pool changed across checkpoint recovery")
    before = torch.load(directory / original["latest"], map_location="cpu", weights_only=False)
    after = torch.load(directory / final["latest"], map_location="cpu", weights_only=False)
    if after["pfsp"] != final["pfsp"] or not finite(after):
        raise ValueError("PFSP checkpoint is incomplete or contains nonfinite tensors")
    changed = {
        key: any(not torch.equal(tensor, after[key][name]) for name, tensor in before[key].items())
        for key in ("model", "critic")
    }
    if not all(changed.values()):
        raise ValueError("qualification did not update both the actor and critic")
    advances = {}
    for key in ("actor_optimizer", "critic_optimizer"):
        first, last = before[key]["state"], after[key]["state"]
        if set(first) != set(last):
            raise ValueError("optimizer parameter ownership changed")
        steps = {int(last[name]["step"] - first[name]["step"]) for name in first}
        if min(steps) <= 0:
            raise ValueError("qualification did not advance every optimizer parameter")
        advances[key] = sorted(steps)
    if len(after["rng"]["workers"]) != world:
        raise ValueError("qualification lost a rank RNG")
    return {
        "sampler_replay": True,
        "checkpoint_statistics_equal_ledger": True,
        "actor_and_critic_updated": changed,
        "optimizer_step_advances": advances,
        "all_checkpoint_tensors_finite": True,
        "rank_rngs": world,
    }
