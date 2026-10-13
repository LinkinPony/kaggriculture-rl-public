"""Audit committed recurrent BC and RL artifacts without touching training state."""

import copy
import json
import math
from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import digest
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.pool import snapshot
from kagg_revue.learning.matchmaking.scheduler import Matchmaker
from kagg_revue.learning.matchmaking.verification import finite


def verify(directory: Path, initial: dict[str, Any]) -> dict[str, Any]:
    """Authenticate BC coverage, causal model updates, WDL returns and PFSP replay."""
    final = json.loads((directory / "state.json").read_text())
    config = Experiment.model_validate(final["protocol"])
    assert config.demonstrations is not None and config.memory_turns == 384
    assert final["completed_update"] >= 2
    manifest = json.loads(config.demonstrations.manifest.read_text())
    training = [row for row in manifest["shards"] if row["split"] == "train"]
    progress = final["pretraining"]
    trajectories = sum(len(row["task"]["seats"]) for row in training)
    batch_trajectories = (
        config.demonstrations.batch_rows // manifest["layout"]["observation"]["turns"]
    )
    expected_steps = math.ceil(trajectories / batch_trajectories) * config.demonstrations.epochs
    expected_rows = sum(row["usable_rows"] for row in training) * config.demonstrations.epochs
    assert progress["cursor"] == progress["optimizer_steps"] == expected_steps
    assert progress["rows"] == expected_rows
    bc_name = final["rl_initial"]
    name = final["latest"]
    for member in (bc_name, name):
        assert digest(directory / member) == final["members"][member]
    bc = torch.load(directory / bc_name, map_location="cpu", weights_only=False)
    latest = torch.load(directory / name, map_location="cpu", weights_only=False)
    assert finite(bc) and finite(latest)
    assert bc["pretraining"] == progress
    assert latest["update"] == final["completed_update"]
    assert latest["lineage"]["run_id"] == final["run_id"]
    assert latest.get("pfsp") == final.get("pfsp")
    assert all(int(row["step"]) == expected_steps for row in bc["optimizer"]["state"].values())
    changed = {
        group: any(
            not torch.equal(value, latest["model"][key])
            for key, value in bc["model"].items()
            if key.startswith(group)
        )
        for group in ("encoder.", "memory.temporal.", "memory.gate.")
    }
    assert all(changed.values())
    rows = final["records"]
    assert [row["update"] for row in rows] == list(range(1, final["completed_update"] + 1))
    for row in rows:
        for worker in row["workers"]:
            assert worker["cash_reward_weight"] == 0 and worker["win_reward_weight"] == 1
            assert set(worker["reward_values"]) <= {-1.0, 0.0, 1.0}
            assert worker["optimization"]["memory_turns"] == 384
    optimizer_steps = {}
    for key, metric in (("actor_optimizer", "actor_steps"), ("critic_optimizer", "critic_steps")):
        expected = sum(row["workers"][0]["optimization"][metric] for row in rows)
        actual = {int(state["step"]) for state in latest[key]["state"].values()}
        assert actual == {expected} and expected > 0
        optimizer_steps[key] = expected
    first_name = (
        initial["latest"]
        if initial["completed_update"]
        else next(
            member
            for member in sorted(final["members"])
            if member.startswith("checkpoints/update-")
        )
    )
    first = torch.load(directory / first_name, map_location="cpu", weights_only=False)
    assert first["update"] < latest["update"]
    assert any(
        not torch.equal(value, latest["critic"][key])
        for key, value in first["critic"].items()
        if key.startswith("memory.temporal.")
    )
    workers = latest["rng"]["workers"]
    assert len(workers) == 2
    assert not torch.equal(workers[0]["cuda"], workers[1]["cuda"])
    assert all(
        not torch.equal(before["cuda"], after["cuda"])
        for before, after in zip(first["rng"]["workers"], workers, strict=True)
    )
    if config.population.pfsp is not None:
        _replay(config, initial, final)
    else:
        _selfplay(config, initial, final, latest)
    return {
        "run_id": final["run_id"],
        "checkpoint": str(directory / name),
        "checkpoint_sha256": final["members"][name],
        "completed_update": final["completed_update"],
        "bc_epochs": config.demonstrations.epochs,
        "bc_optimizer_steps": expected_steps,
        "bc_supervised_rows": expected_rows,
        "bc_metrics": progress["records"],
        "all_checkpoint_tensors_finite": True,
        "actor_updated_groups": changed,
        "critic_memory_updated": True,
        "optimizer_steps": optimizer_steps,
        "independent_rank_rngs_advanced": True,
        "pure_terminal_wdl": True,
        "pfsp_exact_replay": config.population.pfsp is not None,
        "pure_selfplay": config.population.fraction == 0 and config.script_population is None,
        "kl_control": config.kl_control,
        "target_kl": config.target_kl,
        "actor_learning_rate": config.actor_learning_rate,
        "external_opponents": len(final.get("external_opponents", {})),
        "physical_games": sum(row["physical_games"] for row in rows),
        "continuation_physical_games": sum(
            row["physical_games"] for row in rows[initial["completed_update"] :]
        ),
    }


def _selfplay(
    config: Experiment,
    initial: dict[str, Any],
    final: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    """Verify disabled opponents and preserved Adam steps under KL early stopping."""
    assert config.population.fraction == 0 and config.script_population is None
    assert config.kl_control == "early_stop" and config.target_kl == 0.05
    assert config.actor_learning_rate == 7.5e-6
    assert final.get("pfsp") == initial.get("pfsp")
    assert final.get("external_opponents") == initial.get("external_opponents")
    for row in final["records"][initial["completed_update"] :]:
        assert row["opponent"] is None and row["history_score"] is None and "pfsp" not in row
        assert set(row["populations"]) == {"self_play"}
        assert row["populations"]["self_play"]["games"] == config.games
        assert row["populations"]["self_play"]["training_trajectories"] == 2 * config.games
        for worker in row["workers"]:
            optimization = worker["optimization"]
            assert optimization["kl_control"] == "early_stop"
            assert optimization["target_kl"] == config.target_kl
            assert optimization["actor_learning_rate"] == config.actor_learning_rate
            assert optimization["rejected_actor_steps"] == 0
            assert optimization["attempted_actor_steps"] == optimization["actor_steps"] > 0
            assert optimization["critic_steps"] > 0
    for key, rate in (
        ("actor_optimizer", config.actor_learning_rate),
        ("critic_optimizer", config.critic_learning_rate),
    ):
        assert all(group["lr"] == rate for group in payload[key]["param_groups"])


def _replay(config: Experiment, initial: dict[str, Any], final: dict[str, Any]) -> None:
    simulation = copy.deepcopy(initial)
    scheduler = Matchmaker(config, simulation)
    world = len(config.execution.devices) if config.execution else 1
    for row in final["records"][initial["completed_update"] :]:
        update = row["update"]
        match = scheduler.select(update, world)
        opponent = row["opponent"]["path"] if row["opponent"] else ""
        assert match.report == row["pfsp"] and match.history == opponent
        scheduler.observe(match, update, row["populations"])
        name = f"checkpoints/update-{update:06d}.pt"
        if name in final["members"]:
            simulation["members"][name] = final["members"][name]
            if update % config.population.snapshot_interval == 0:
                snapshot(config, simulation, name)
    assert simulation["pfsp"] == final["pfsp"]
    assert simulation["pool"] == final["pool"]
