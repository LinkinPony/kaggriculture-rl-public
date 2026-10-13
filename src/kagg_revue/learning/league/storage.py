"""Atomic member commits, shared source provenance, and bounded recovery state."""

import copy
import json
import time
import uuid
from pathlib import Path
from typing import Any

import orjson
import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.distributed import barrier, rank_world, rng_snapshot
from kagg_revue.learning.league.config import League
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.pretraining.config import Demonstrations
from kagg_revue.policy.checkpoints import save_policy


def create(config: League) -> dict[str, Any]:
    """Create independent member ledgers with identical fresh actor roots."""
    root = config.experiment.output_dir
    path = root / "league.json"
    if path.exists():
        raise FileExistsError("fresh league requires a new run")
    member_states = {}
    for name in config.members:
        recipe = config.member(name)
        member_states[name] = artifacts.create(recipe, runtime_settings(recipe))
    state = {
        "schema": "three-specialist-league-v1",
        "run_id": uuid.uuid4().hex,
        "created_at": time.time(),
        "protocol": config.protocol(),
        "source": member_states[config.members[0]]["source"],
        "phase": "bc",
        "completed_update": 0,
        "latest": None,
        "checkpoints": {},
        "members": {
            name: {
                "run_id": member_states[name]["run_id"],
                "initial_sha256": member_states[name]["members"]["initial.pt"],
            }
            for name in config.members
        },
    }
    write_json(root / "league.json", state)
    write_json(root / "resolved-config.json", config.protocol())
    return state


def restore(config: League) -> dict[str, Any]:
    """Require the same source, recipe, dataset roles and latest joint checkpoint."""
    root = config.experiment.output_dir
    state: dict[str, Any] = orjson.loads((root / "league.json").read_bytes())
    if state["schema"] != "three-specialist-league-v1" or state["protocol"] != config.protocol():
        raise ValueError("league continuation must preserve the complete protocol")
    if artifacts.source_identity()["source_sha256"] != state["source"]:
        raise ValueError("league source changed; use the archived recovery entry point")
    if tuple(state["members"]) != config.members:
        raise ValueError("active membership differs from the frozen protocol")
    if state["phase"] == "bc":
        config.sources()
    for name in config.members:
        archived = orjson.loads((root / name / "state.json").read_bytes())
        committed = None
        if state["phase"] != "bc":
            origin = state["members"][name]
            if (
                origin.get("bc_epochs") != config.bc_epochs
                or archived.get("rl_initial") != origin.get("bc_path")
                or len(archived.get("pretraining", {}).get("records", [])) != config.bc_epochs
            ):
                raise ValueError("PPO continuation requires every committed BC epoch and endpoint")
            committed = Demonstrations.model_validate(archived["protocol"]["demonstrations"])
        recipe = config.member(name, committed=committed)
        child = artifacts.restore(recipe)
        if child["run_id"] != state["members"][name]["run_id"]:
            raise ValueError("league member lineage changed")
    if state["latest"] and digest(root / state["latest"]) != state["checkpoints"][state["latest"]]:
        raise ValueError("joint league checkpoint fingerprint changed")
    return state


def save(
    config: League,
    state: dict[str, Any],
    learners: list[Learner],
    update: int,
    pending: list[dict[str, Any]],
) -> None:
    """Publish all policies, optimizers and both GPU RNGs in one atomic file."""
    rank, _ = rank_world()
    rng = rng_snapshot(learners[0].device)
    if rank == 0:
        root = config.experiment.output_dir
        previous = state["latest"]
        name = f"checkpoints/update-{update:06d}.pt"
        path = root / name
        path.parent.mkdir(exist_ok=True)
        payload = {
            "schema": state["schema"],
            "run_id": state["run_id"],
            "update": update,
            "parent_sha256": state["checkpoints"].get(previous),
            "rng": rng,
            "members": state["members"],
            "records": pending,
            "models": {
                member: {
                    "actor": learner.policy.state_dict(),
                    "critic": learner.critic.state_dict(),
                    "actor_optimizer": learner.actor_optimizer.state_dict(),
                    "critic_optimizer": learner.critic_optimizer.state_dict(),
                }
                for member, learner in zip(config.members, learners, strict=True)
            },
        }
        torch.save(payload, path.with_suffix(".partial"))
        path.with_suffix(".partial").replace(path)
        state["checkpoints"][name] = digest(path)
        state.update(latest=name, completed_update=update, phase="rl")
        keep = config.experiment.checkpoint_keep_recent or 8
        recent = sorted(old for old in state["checkpoints"] if old.startswith("checkpoints/"))
        retired = [old for old in recent[:-keep] if old != "checkpoints/update-000000.pt"]
        retired_hashes = {old: state["checkpoints"].pop(old) for old in retired}
        write_json(root / "league.json", state)
        status_path = root / "run-status.json"
        status = orjson.loads(status_path.read_bytes())
        status.update(phase="rl", completed_update=update)
        write_json(status_path, status)
        if retired_hashes:
            with (root / "retired.jsonl").open("a") as stream:
                stream.write(json.dumps({"update": update, "checkpoints": retired_hashes}) + "\n")
            for old in retired:
                (root / old).unlink()
    barrier()
    if rank != 0:
        state.clear()
        state.update(orjson.loads((config.experiment.output_dir / "league.json").read_bytes()))


def load_latest(config: League, state: dict[str, Any], learners: list[Learner]) -> None:
    """Restore all active members together, without allowing mixed update numbers."""
    root = config.experiment.output_dir
    if digest(root / state["latest"]) != state["checkpoints"][state["latest"]]:
        raise ValueError("joint checkpoint hash differs")
    payload = torch.load(root / state["latest"], map_location="cpu", weights_only=False)
    if (
        payload["run_id"] != state["run_id"]
        or payload["update"] != state["completed_update"]
        or payload["members"] != state["members"]
        or set(payload["models"]) != set(config.members)
    ):
        raise ValueError("joint checkpoint membership or round differs")
    for name, learner in zip(config.members, learners, strict=True):
        saved = payload["models"][name]
        learner.policy.load_state_dict(saved["actor"])
        learner.critic.load_state_dict(saved["critic"])
        learner.restore_optimizers(saved["actor_optimizer"], saved["critic_optimizer"])
    rank, world = rank_world()
    workers = payload["rng"]["workers"]
    if len(workers) != world:
        raise ValueError("league recovery must preserve GPU worker count")
    torch.set_rng_state(workers[rank]["cpu"])
    torch.cuda.set_rng_state(workers[rank]["cuda"], learners[0].device)
    if rank == 0:
        reconcile_metrics(root, state["completed_update"], payload["records"])


def reconcile_metrics(root: Path, completed: int, committed: list[dict[str, Any]]) -> None:
    """Discard incomplete-round display rows and recover any final committed log tail."""
    path = root / "metrics.jsonl"
    records = {}
    if path.exists():
        for line in path.read_bytes().splitlines():
            try:
                row = orjson.loads(line)
            except orjson.JSONDecodeError:
                break
            if row["update"] <= completed:
                records[row["update"]] = row
    records.update({row["update"]: row for row in committed})
    if sorted(records) != list(range(1, completed + 1)):
        raise ValueError("league metrics have a gap before the committed boundary")
    temporary = path.with_suffix(".partial")
    temporary.write_bytes(b"".join(orjson.dumps(records[i]) + b"\n" for i in sorted(records)))
    temporary.replace(path)


def export(config: League, state: dict[str, Any], learners: list[Learner], update: int) -> None:
    """Export standalone inference-compatible members without duplicating optimizer history."""
    rank, _ = rank_world()
    if rank == 0:
        for name, learner in zip(config.members, learners, strict=True):
            save_policy(
                config.experiment.output_dir / "exports" / f"update-{update:06d}" / f"{name}.pt",
                learner.policy,
                runtime_settings(config.experiment),
                update=update,
                lineage={
                    "run_id": state["run_id"],
                    "kind": "league_member",
                    "member": name,
                    "bc_origin": copy.deepcopy(state["members"][name]),
                },
            )
    barrier()
