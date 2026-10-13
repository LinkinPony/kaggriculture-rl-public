"""CPU qualification of archived recovery, optimizer tensors and PFSP identities."""

import copy
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.scheduler import Matchmaker
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.learning.storage.roles import full_members, required_members


def _optimizer(module: torch.nn.Module, saved: dict[str, Any]) -> dict[str, Any]:
    optimizer = torch.optim.AdamW(module.parameters())
    optimizer.load_state_dict(saved)
    steps = set()
    for parameter, values in optimizer.state.items():
        for key in ("exp_avg", "exp_avg_sq"):
            if values[key].shape != parameter.shape or not torch.isfinite(values[key]).all():
                raise ValueError("restored optimizer moment differs from its parameter shape")
        steps.add(int(values["step"].item()))
    return {"parameters": len(optimizer.state), "steps": sorted(steps)}


def verify(directory: Path, previous: Path, output: Path) -> dict[str, Any]:
    """Load the exact archived policy/critic and both Adam states without taking a step."""
    torch.set_num_threads(1)
    stored = json.loads((directory / "state.json").read_text())
    old = json.loads(previous.read_text())
    config = Experiment.model_validate(stored["protocol"])
    state = artifacts.restore(config.model_copy(update={"resume": True}))
    for key in ("run_id", "pool", "pfsp", "latest", "completed_update", "pretraining"):
        if state.get(key) != old.get(key):
            raise ValueError(f"storage migration changed training state: {key}")
    checkpoints = []
    for name in sorted(full_members(config, state)):
        path = artifacts.member_path(config, state, name)
        if digest(path) != old["members"][name]:
            raise ValueError("recovery checkpoint bytes changed during storage migration")
        actor, payload = artifacts.load_member(config, state, name, torch.device("cpu"))
        critic: torch.nn.Module
        if getattr(config, "memory_turns", 0):
            from kagg_revue.learning.sequences.critic import MemoryCritic

            critic = MemoryCritic(actor.layout)
        else:
            critic = PrefixCritic(actor.layout)
        critic.load_state_dict(payload["critic"])
        tensors = [*actor.state_dict().values(), *critic.state_dict().values()]
        if any(not torch.isfinite(value).all() for value in tensors):
            raise ValueError("nonfinite actor or critic in the recovery checkpoint")
        rng = payload["rng"]
        world = len(config.execution.devices) if config.execution else 1
        if len(rng.get("workers", [rng])) != world:
            raise ValueError("recovery checkpoint lost a worker RNG stream")
        if name == state["latest"] and payload.get("pfsp") != state.get("pfsp"):
            raise ValueError("latest optimizer checkpoint PFSP differs from the ledger")
        checkpoints.append(
            {
                "path": name,
                "sha256": digest(path),
                "update": payload["update"],
                "model_tensors": len(tensors),
                "actor_optimizer": _optimizer(actor, payload["actor_optimizer"]),
                "critic_optimizer": _optimizer(critic, payload["critic_optimizer"]),
                "rng_workers": world,
            }
        )
    world = len(config.execution.devices) if config.execution else 1
    update = state["completed_update"] + 1
    selection = Matchmaker(config, copy.deepcopy(state)).select(update, world)
    expected = Matchmaker(config, copy.deepcopy(old)).select(update, world)
    if selection != expected:
        raise ValueError("storage migration changed the next PFSP draw")
    result = {
        "passed": True,
        "run": str(directory),
        "completed_update": state["completed_update"],
        "checkpoints": checkpoints,
        "required_policies": len(required_members(config, state)),
        "pool_members": len(state["pool"]),
        "next_pfsp_draw": asdict(selection),
        "source_sha256": state["source"],
        "scope": "Archived CPU restore, exact recovery bytes, actor/critic/Adam loads, RNG "
        "presence and exact next PFSP draw; no optimizer update executed.",
    }
    write_json(output, result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))))
