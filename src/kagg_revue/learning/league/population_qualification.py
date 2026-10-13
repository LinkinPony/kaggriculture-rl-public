"""Real-checkpoint qualification of member retirement and native script training."""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import orjson
import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.league.population import PopulationChange, proposed, qualification_copy
from kagg_revue.learning.league.recovery import BOOTSTRAP, LeagueRecovery, recover
from kagg_revue.learning.league.revision import read_state, stopped_state
from kagg_revue.learning.league.verification import _finite
from kagg_revue.opponents.artifacts import identity as script_identity


def equal_state(left: Any, right: Any) -> bool:
    """Compare nested optimizer and RNG states exactly, including every tensor bit."""
    if isinstance(left, torch.Tensor):
        return isinstance(right, torch.Tensor) and torch.equal(left, right)
    if isinstance(left, dict):
        return (
            isinstance(right, dict)
            and left.keys() == right.keys()
            and all(equal_state(value, right[key]) for key, value in left.items())
        )
    if isinstance(left, (tuple, list)):
        return (
            type(left) is type(right)
            and len(left) == len(right)
            and all(equal_state(a, b) for a, b in zip(left, right, strict=True))
        )
    return bool(left == right)


def qualify(change: PopulationChange) -> dict[str, Any]:
    """Train two complete rounds, recover from archived native code, and train a third."""
    original = stopped_state(change.run)
    before_sha = digest(change.run / "league.json")
    identity = artifacts.source_identity()
    config = proposed(original, change)
    scripts = config.experiment.script_population
    assert scripts is not None
    script_runtime = script_identity(scripts)
    qualification_copy(change)
    boundary = original["completed_update"]
    before = torch.load(change.run / original["latest"], map_location="cpu", weights_only=False)
    migrated = torch.load(
        change.destination / original["latest"], map_location="cpu", weights_only=False
    )
    if (
        set(migrated["models"]) != set(config.members)
        or not equal_state(before["rng"], migrated["rng"])
        or any(
            not equal_state(before["models"][name], migrated["models"][name])
            or not equal_state(before["members"][name], migrated["members"][name])
            for name in config.members
        )
    ):
        raise ValueError(
            "membership filtering changed retained weights, optimizers, RNG or BC origins"
        )
    del migrated
    started = time.time()
    temporary = Path("tmp").resolve()
    temporary.mkdir(exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-c",
            BOOTSTRAP,
            str(change.destination / "league.json"),
            orjson.dumps(boundary + 2).decode(),
        ],
        check=True,
        env={
            **os.environ,
            "TMPDIR": str(temporary),
            "TORCHINDUCTOR_CACHE_DIR": str(temporary / "torchinductor"),
            "TRITON_CACHE_DIR": str(temporary / "triton"),
        },
    )
    if read_state(change.destination)["completed_update"] != boundary + 2:
        raise ValueError("qualification failed to train two complete updates")
    recover(LeagueRecovery(run=change.destination, stop_after_update=boundary + 3))
    final = read_state(change.destination)
    if final["completed_update"] != boundary + 3:
        raise ValueError("archived recovery failed to complete the third update")
    after = torch.load(change.destination / final["latest"], map_location="cpu", weights_only=False)
    if (
        not _finite(after)
        or set(after["models"]) != set(config.members)
        or len(after["rng"]["workers"]) != 2
    ):
        raise ValueError("trained checkpoint has invalid tensors, membership or GPU RNG states")
    changed = {
        name: {
            role: not equal_state(before["models"][name][role], after["models"][name][role])
            for role in ("actor", "critic", "actor_optimizer", "critic_optimizer")
        }
        for name in config.members
    }
    if not all(all(roles.values()) for roles in changed.values()):
        raise ValueError("qualification must actually update both actors, critics and optimizers")
    rows = [
        orjson.loads(line)
        for line in (change.destination / "metrics.jsonl").read_bytes().splitlines()
    ]
    rows = [row for row in rows if row["update"] > boundary]
    if len(rows) != 3:
        raise ValueError("qualification requires three complete metric records")
    for row in rows:
        if (
            len(row["pairs"]) != len(config.matchups())
            or row["physical_games"] != config.experiment.games
            or set(row["member_populations"]) != set(config.members)
        ):
            raise ValueError("full-size native rollout membership or physical game budget differs")
        for name in config.members:
            panels = row["member_populations"][name]
            if panels["self_play"][
                "training_trajectories"
            ] != 2 * config.selfplay_games_per_member or any(
                panels[script]["games"] != config.games_per_script_per_member
                for script in config.script_names
            ):
                raise ValueError("self-play or five-script trajectory accounting differs")
            for worker in row["workers"]:
                optimization = worker["optimization"][name]
                if optimization["actor_steps"] < 1 or optimization["critic_steps"] < 1:
                    raise ValueError("a retained model skipped all optimization steps")
    evaluation = orjson.loads(
        (change.destination / "evaluation" / f"update-{boundary:06d}.json").read_bytes()
    )
    if (
        len(evaluation["pairs"]) != len(config.matchups())
        or evaluation["physical_games"] != config.experiment.games
    ):
        raise ValueError("held-out evaluation is missing a native script or neural pairing")
    if digest(change.run / "league.json") != before_sha or artifacts.source_identity() != identity:
        raise ValueError("formal checkpoint or implementation changed during qualification")
    report = {
        "passed": True,
        "run_id": original["run_id"],
        "completed_update": boundary,
        "checkpoint_sha256": original["checkpoints"][original["latest"]],
        "source_state_sha256": before_sha,
        "source_sha256": identity["source_sha256"],
        "native_sha256": identity["native_sha256"],
        "script_runtime": script_runtime,
        "protocol": config.protocol(),
        "destination": str(change.destination),
        "migration_preserves_weights_optimizers_rng_bc_exactly": True,
        "models_changed": changed,
        "finite_models_optimizers_and_rng": True,
        "archived_restart_completed": boundary + 3,
        "baseline_evaluation_games": evaluation["physical_games"],
        "rounds": [
            {
                "update": row["update"],
                "seconds": row["update_seconds"],
                "pairs": row["pairs"],
                "member_populations": row["member_populations"],
                "workers": row["workers"],
            }
            for row in rows
        ],
        "seconds": time.time() - started,
    }
    write_json(change.report, report)
    return report
