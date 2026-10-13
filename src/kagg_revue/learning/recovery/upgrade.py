"""Explicit, qualified hardware upgrades retaining every original root and source archive."""

import fcntl
import json
import os
import tempfile
import time
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery
from kagg_revue.learning.storage.roles import required_members


class Upgrade(Recovery):
    """Bind one stopped run to an exact tested implementation and execution profile."""

    execution: Execution
    qualification: Path
    qualification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def upgrade(config: Upgrade) -> None:
    """Authenticate the old implementation, then atomically record a qualified transition."""
    directory = config.run
    with (directory / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status = json.loads((directory / "run-status.json").read_text())
        try:
            os.kill(status["pid"], 0)
        except ProcessLookupError:
            pass
        else:
            raise RuntimeError("the original training process is still live")
        state = json.loads((directory / "state.json").read_text())
        old = Experiment.model_validate(state["protocol"])
        if (
            old.output_dir != directory
            or state["schema"] != "random-root-league-v1"
            or state["input_weights"]
            or state["initialization"] != "random"
            or state["completed_update"] >= old.updates
            or not state["completed_update"]
        ):
            raise ValueError("hardware upgrades require a stopped, unfinished own-run PPO ledger")
        if config.execution == old.execution:
            raise ValueError("this execution profile is already active")
        temporary = Path("tmp")
        temporary.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="verify-upgrade-", dir=temporary) as name:
            materialize(directory, state, Path(name))
        for name in required_members(old, state):
            artifacts.member_path(old, state, name)
        identity = artifacts.source_identity()
        if identity["native_sha256"] != state["native"]:
            raise ValueError("a hardware-only upgrade must preserve the native rule engine binary")
        if digest(config.qualification) != config.qualification_sha256:
            raise ValueError("qualification report hash differs from the requested transition")
        qualified = json.loads(config.qualification.read_text())
        expected = {
            "passed": True,
            "run_id": state["run_id"],
            "completed_update": state["completed_update"],
            "checkpoint_sha256": state["members"][state["latest"]],
            "source_sha256": identity["source_sha256"],
            "execution": config.execution.model_dump(mode="json"),
        }
        if any(qualified.get(key) != value for key, value in expected.items()):
            raise ValueError("qualification does not bind this checkpoint, source and execution")
        resolved = Experiment.model_validate(
            {
                **state["protocol"],
                "execution": config.execution.model_dump(),
            }
        )
        changes = {
            key
            for key in set(artifacts.protocol(resolved)) | set(state["protocol"])
            if artifacts.protocol(resolved).get(key) != state["protocol"].get(key)
        }
        if changes != {"execution"}:
            raise ValueError("hardware upgrade must preserve every statistical protocol field")
        revisions = state.get("execution_history", [])
        revision = directory / "runtime-revisions" / f"{len(revisions) + 1:04d}"
        revision.mkdir(parents=True, exist_ok=False)
        write_json(revision / "previous-state.json", state)
        archive_source(revision, identity)
        write_json(revision / "qualification.json", qualified)
        transition = {
            "time": time.time(),
            "completed_update": state["completed_update"],
            "checkpoint_sha256": state["members"][state["latest"]],
            "previous_source": state["source"],
            "source": identity["source_sha256"],
            "previous_protocol": state["protocol"],
            "execution": config.execution.model_dump(mode="json"),
            "qualification": str(config.qualification),
            "qualification_sha256": config.qualification_sha256,
            "revision": str(revision.relative_to(directory)),
            "rng_transition": "shared ranks restored; added ranks seeded from root seed, rank "
            "and update; removed streams retained in the original checkpoint",
            "bitwise_equivalent_to_single_gpu": False,
        }
        state["execution_history"] = [*revisions, transition]
        state["protocol"] = artifacts.protocol(resolved)
        state["source"] = identity["source_sha256"]
        state["source_directory"] = str(revision.relative_to(directory))
        write_json(directory / "state.json", state)
        write_json(directory / "resolved-config.json", state["protocol"])
        print(json.dumps(transition), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_upgrade",
)
def main(configuration: DictConfig) -> None:
    """Apply an explicitly requested, qualified hardware change to one existing run."""
    upgrade(Upgrade.model_validate(OmegaConf.to_container(configuration.upgrade, resolve=True)))


if __name__ == "__main__":
    main()
