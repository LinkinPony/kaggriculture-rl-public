"""Real-checkpoint self-play qualification, including an archived restart."""

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import hydra
import orjson
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.league.config import MEMBERS
from kagg_revue.learning.league.recovery import BOOTSTRAP, LeagueRecovery, recover
from kagg_revue.learning.league.revision import (
    changed_config,
    qualification_copy,
    read_state,
    stopped_state,
)
from kagg_revue.learning.league.verification import _finite
from kagg_revue.learning.recovery.cli import Recovery


class Integration(Recovery):
    """Name a formal source and a separate, disposable-weight qualification run."""

    destination: Path
    output: Path
    selfplay_games_per_member: int = 32


def qualify(config: Integration) -> dict[str, Any]:
    """Train two rounds, restart from archive, and validate a third full PPO update."""
    Recovery(run=config.destination)
    original = stopped_state(config.run)
    before_sha = digest(config.run / "league.json")
    identity = artifacts.source_identity()
    proposed = changed_config(original, config.selfplay_games_per_member)
    qualification_copy(config.run, config.destination, config.selfplay_games_per_member)
    boundary = original["completed_update"]
    started = time.time()
    # Keep the training supervisor separate from this verification coordinator:
    # archived recovery requires the previous supervisor PID to have exited.
    subprocess.run(
        [
            sys.executable,
            "-c",
            BOOTSTRAP,
            str(config.destination / "league.json"),
            orjson.dumps(boundary + 2).decode(),
        ],
        check=True,
    )
    intermediate = read_state(config.destination)
    if intermediate["completed_update"] != boundary + 2:
        raise ValueError("qualification stopped before both initial updates completed")
    recover(LeagueRecovery(run=config.destination, stop_after_update=boundary + 3))
    final = read_state(config.destination)
    if final["completed_update"] != boundary + 3:
        raise ValueError("archived continuation did not finish the requested update")
    before = torch.load(config.run / original["latest"], map_location="cpu", weights_only=False)
    after = torch.load(config.destination / final["latest"], map_location="cpu", weights_only=False)
    if (
        not _finite(after)
        or after["members"] != before["members"]
        or len(after["rng"]["workers"]) != 2
    ):
        raise ValueError("joint models, optimizer state, membership or RNG failed validation")
    changed = {}
    for name in MEMBERS:
        changed[name] = {
            role: any(
                not torch.equal(value, after["models"][name][role][key])
                for key, value in before["models"][name][role].items()
            )
            for role in ("actor", "critic")
        }
    if not all(all(roles.values()) for roles in changed.values()):
        raise ValueError("qualification must actually train every actor and critic")
    rows = [
        orjson.loads(line)
        for line in (config.destination / "metrics.jsonl").read_bytes().splitlines()
    ]
    rows = [row for row in rows if row["update"] > boundary]
    if len(rows) != 3:
        raise ValueError("qualification requires three complete metric records")
    for row in rows:
        if len(row["pairs"]) != 6 or row["physical_games"] != proposed.experiment.games:
            raise ValueError("self-play or mutual games are missing from the full-size rollout")
        for name in MEMBERS:
            panel = row["member_populations"][name]["self_play"]
            if (
                panel["games"] != proposed.selfplay_games_per_member
                or panel["training_trajectories"] != 2 * panel["games"]
            ):
                raise ValueError("self-play must retain both seats while counting games once")
    evaluation = orjson.loads(
        (config.destination / "evaluation" / f"update-{boundary:06d}.json").read_bytes()
    )
    if (
        len(evaluation["pairs"]) != 6
        or evaluation["physical_games"] != 2 * proposed.experiment.games
    ):
        raise ValueError("held-out evaluation must cover mutual matches and self-play")
    if digest(config.run / "league.json") != before_sha or artifacts.source_identity() != identity:
        raise ValueError("formal source checkpoint or implementation changed during qualification")
    report = {
        "passed": True,
        "run_id": original["run_id"],
        "completed_update": boundary,
        "checkpoint_sha256": original["checkpoints"][original["latest"]],
        "source_state_sha256": before_sha,
        "source_sha256": identity["source_sha256"],
        "native_sha256": identity["native_sha256"],
        "protocol": proposed.protocol(),
        "destination": str(config.destination),
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
                "peak_bytes": max(worker["peak_allocated_bytes"] for worker in row["workers"]),
            }
            for row in rows
        ],
        "seconds": time.time() - started,
    }
    write_json(config.output, report)
    return report


@hydra.main(version_base=None, config_path="../../../../configs", config_name="league_integration")
def main(configuration: DictConfig) -> None:
    """Qualify an explicitly requested composition before switching the formal run."""
    config = Integration.model_validate(
        OmegaConf.to_container(configuration.integration, resolve=True)
    )
    report = qualify(config)
    print(
        orjson.dumps({"passed": report["passed"], "output": str(config.output)}).decode(),
        flush=True,
    )


if __name__ == "__main__":
    main()
