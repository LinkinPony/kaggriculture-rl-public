"""Register an explicitly requested latest-BC handoff without changing saved weights."""

import fcntl
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Literal

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.verification import finite
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery


class Completion(Recovery):
    """Select the latest committed BC state for an already configured self-play run."""

    selection: Literal["latest"] = "latest"


def complete(config: Completion) -> None:
    """Preserve the BC artifact and protocol, recording the user's phase override."""
    directory = config.run
    with (
        (directory / "recovery.lock").open("a") as recovery_lock,
        (directory / "run.lock").open("a") as run_lock,
    ):
        for lock in (recovery_lock, run_lock):
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status = json.loads((directory / "run-status.json").read_text())
        try:
            os.kill(status["pid"], 0)
        except ProcessLookupError:
            pass
        else:
            raise RuntimeError("stop the training process before completing BC")
        state = json.loads((directory / "state.json").read_text())
        original = Experiment.model_validate(state["protocol"])
        progress = state.get("pretraining", {})
        if (
            status["status"] != "stopped"
            or original.output_dir != directory
            or original.demonstrations is None
            or state["schema"] != "random-root-league-v1"
            or state["initialization"] != "random"
            or state["input_weights"]
            or state["completed_update"]
            or "rl_initial" in state
            or not progress.get("cursor")
        ):
            raise ValueError("completion requires a normally stopped, unfinished own-run BC")
        if (
            original.population.fraction != 0
            or original.script_population is not None
            or original.cash_weight != 0
            or original.curriculum is not None
        ):
            raise ValueError("latest-BC handoff requires pure full-game self-play and terminal WDL")
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="verify-bc-completion-", dir="tmp") as name:
            materialize(directory, state, Path(name))
        selected = state["latest"]
        path = artifacts.member_path(original, state, selected)
        payload = torch.load(path, map_location="cpu", weights_only=False)
        world = len(original.execution.devices) if original.execution else 1
        steps = {int(row["step"]) for row in payload["optimizer"]["state"].values()}
        if (
            payload.get("pretraining") != progress
            or payload.get("lineage", {}).get("run_id") != state["run_id"]
            or not finite(payload)
            or steps != {progress["optimizer_steps"]}
            or len(payload["rng"].get("workers", [payload["rng"]])) != world
        ):
            raise ValueError("latest BC checkpoint, Adam, RNG or progress verification failed")
        revision = directory / "bc-completion" / "0001"
        revision.mkdir(parents=True, exist_ok=False)
        write_json(revision / "previous-state.json", state)
        transition = {
            "time": time.time(),
            "reason": "explicit_user_stop_bc_and_start_pure_selfplay_from_latest_weights",
            "selection": config.selection,
            "checkpoint": selected,
            "checkpoint_sha256": state["members"][selected],
            "cursor": progress["cursor"],
            "optimizer_steps": progress["optimizer_steps"],
            "supervised_rows": progress["rows"],
            "completed_epochs": len(progress["records"]),
            "last_completed_epoch": progress["records"][-1] if progress["records"] else None,
            "source_unchanged": state["source"],
            "protocol_unchanged": True,
            "bc_checkpoint_unchanged": True,
            "revision": str(revision.relative_to(directory)),
        }
        write_json(revision / "transition.json", transition)
        state.update(rl_initial=selected, bc_final=selected, pool=[selected])
        state["bc_completion"] = transition
        artifacts.write_ledger(directory, state)
        print(json.dumps(transition), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_bc_complete",
)
def main(configuration: DictConfig) -> None:
    """Finish only the explicitly named BC phase before ordinary archived recovery."""
    torch.set_num_threads(2)
    complete(Completion.model_validate(OmegaConf.to_container(configuration.handoff, resolve=True)))


if __name__ == "__main__":
    main()
