"""Record an explicitly requested BC budget extension without resetting training."""

import fcntl
import json
import os
import tempfile
import time
from pathlib import Path

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.verification import finite
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery


class Budget(Recovery):
    """Extend only the unfinished imitation phase of an explicitly named own run."""

    epochs: int = Field(gt=0)


def extend(config: Budget) -> None:
    """Preserve the checkpoint, optimizer, RNG, cursor, dataset and source archive."""
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
            raise RuntimeError("the recorded training process is still live")
        state = json.loads((directory / "state.json").read_text())
        previous = Experiment.model_validate(state["protocol"])
        source = previous.demonstrations
        if (
            source is None
            or config.epochs <= source.epochs
            or previous.output_dir != directory
            or state["schema"] != "random-root-league-v1"
            or state["initialization"] != "random"
            or state["input_weights"]
            or state["completed_update"]
            or "rl_initial" in state
            or status["status"] != "stopped"
            or not state.get("pretraining", {}).get("cursor")
        ):
            raise ValueError("BC extension requires a normally stopped unfinished BC run")
        with tempfile.TemporaryDirectory(prefix="verify-bc-budget-", dir="tmp") as name:
            materialize(directory, state, Path(name))
        path = artifacts.member_path(previous, state, state["latest"])
        payload = torch.load(path, map_location="cpu", weights_only=False)
        if (
            payload["pretraining"] != state["pretraining"]
            or payload["lineage"]["run_id"] != state["run_id"]
            or not finite(payload)
            or len(payload["rng"]["workers"]) != len(previous.execution.devices)  # type: ignore[union-attr]
        ):
            raise ValueError("BC checkpoint, cursor, optimizer or rank RNG validation failed")
        updated = Experiment.model_validate(
            {
                **state["protocol"],
                "demonstrations": {**source.model_dump(mode="json"), "epochs": config.epochs},
            }
        )
        revisions = state.get("bc_budget_history", [])
        revision = directory / "bc-budget-revisions" / f"{len(revisions) + 1:04d}"
        revision.mkdir(parents=True, exist_ok=False)
        write_json(revision / "previous-state.json", state)
        transition = {
            "time": time.time(),
            "previous_epochs": source.epochs,
            "epochs": config.epochs,
            "cursor": state["pretraining"]["cursor"],
            "checkpoint": state["latest"],
            "checkpoint_sha256": state["members"][state["latest"]],
            "source_unchanged": state["source"],
            "revision": str(revision.relative_to(directory)),
            "reason": "explicit_user_bc_epoch_extension",
        }
        write_json(revision / "transition.json", transition)
        state["protocol"] = artifacts.protocol(updated)
        state["bc_budget_history"] = [*revisions, transition]
        artifacts.write_ledger(directory, state)
        write_json(directory / "resolved-config.json", state["protocol"])
        print(json.dumps(transition), flush=True)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="learning_bc_budget")
def main(configuration: DictConfig) -> None:
    """Apply an authorized budget extension before ordinary archived recovery."""
    torch.set_num_threads(2)
    extend(Budget.model_validate(OmegaConf.to_container(configuration.budget, resolve=True)))


if __name__ == "__main__":
    main()
