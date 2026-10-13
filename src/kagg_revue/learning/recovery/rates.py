"""Explicit actor learning-rate changes preserving the complete PPO continuation."""

import fcntl
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining import weights
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery
from kagg_revue.learning.storage.roles import required_members


class RateChange(Recovery):
    """Pin a stopped ledger and the user's requested constant actor learning rate."""

    state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    actor_learning_rate: float = Field(gt=0, allow_inf_nan=False)


def change(config: RateChange) -> dict[str, Any]:
    """Publish only the actor rate and source revision; leave saved tensors untouched."""
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
            raise RuntimeError("stop the existing training process before changing its rate")
        previous = (directory / "state.json").read_bytes()
        if hashlib.sha256(previous).hexdigest() != config.state_sha256:
            raise ValueError("learning-rate change requires the pinned stopped ledger")
        state = json.loads(previous)
        original = Experiment.model_validate(state["protocol"])
        if (
            status["status"] != "stopped"
            or original.output_dir != directory
            or not weights.valid_root(state)
            or not 0 < state["completed_update"] < original.updates
            or original.learning_rate_warmup_updates
        ):
            raise ValueError("rate changes require a stopped PPO run with constant learning rates")
        updated = original.model_copy(update={"actor_learning_rate": config.actor_learning_rate})
        protocol = artifacts.protocol(updated)
        changed = {
            key
            for key in protocol.keys() | state["protocol"].keys()
            if protocol.get(key) != state["protocol"].get(key)
        }
        if changed != {"actor_learning_rate"}:
            raise ValueError("this revision must change only the actor learning rate")
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="verify-rate-", dir="tmp") as name:
            materialize(directory, state, Path(name))
        weights.verify(directory, state)
        for member in required_members(original, state):
            artifacts.member_path(original, state, member)
        identity = artifacts.source_identity()
        if identity["native_sha256"] != state["native"]:
            raise ValueError("learning-rate changes must preserve the native rule engine")
        history = state.get("learning_rate_history", [])
        revision = directory / "learning-rate-revisions" / f"{len(history) + 1:04d}"
        revision.mkdir(parents=True, exist_ok=False)
        (revision / "previous-state.json").write_bytes(previous)
        archive_source(revision, identity)
        boundary = artifacts.member_path(original, state, state["latest"])
        os.link(boundary, revision / "checkpoint.pt")
        transition = {
            "time": time.time(),
            "reason": "user requested actor learning-rate change",
            "effective_from_update": state["completed_update"] + 1,
            "checkpoint": state["latest"],
            "checkpoint_sha256": state["members"][state["latest"]],
            "preserved_checkpoint": str((revision / "checkpoint.pt").relative_to(directory)),
            "previous_state_sha256": config.state_sha256,
            "previous_source": state["source"],
            "source": identity["source_sha256"],
            "previous_protocol": state["protocol"],
            "protocol": protocol,
            "revision": str(revision.relative_to(directory)),
            "checkpoint_bytes_unchanged": True,
            "optimizer_rng_and_history_preserved": True,
        }
        state.update(
            protocol=protocol,
            source=identity["source_sha256"],
            source_directory=str(revision.relative_to(directory)),
            learning_rate_history=[*history, transition],
        )
        write_json(revision / "transition.json", transition)
        artifacts.write_ledger(directory, state)
        write_json(directory / "resolved-config.json", protocol)
        return transition


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_rate_change",
)
def main(configuration: DictConfig) -> None:
    """Record one requested rate change before resuming through the source archive."""
    config = RateChange.model_validate(OmegaConf.to_container(configuration.change, resolve=True))
    transition = change(config)
    print(json.dumps(transition), flush=True)


if __name__ == "__main__":
    main()
