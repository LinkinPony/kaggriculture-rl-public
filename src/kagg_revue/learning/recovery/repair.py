"""Qualified source repairs that preserve the complete training protocol and state."""

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
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining import weights
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery
from kagg_revue.learning.storage.roles import required_members
from kagg_revue.opponents import artifacts as script_artifacts


class Repair(Recovery):
    """Bind a stopped run's implementation change to checkpoint-specific evidence."""

    qualification: Path
    qualification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def repair(config: Repair) -> None:
    """Archive the tested implementation without migrating any training state."""
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
        original = Experiment.model_validate(state["protocol"])
        unfinished_bc = (
            original.demonstrations is not None
            and state["completed_update"] == 0
            and "rl_initial" not in state
            and state.get("pretraining", {}).get("cursor", 0) > 0
        )
        if (
            original.output_dir != directory
            or not weights.valid_root(state)
            or not (unfinished_bc or 0 < state["completed_update"] < original.updates)
            or status["status"] not in {"failed", "stopped"}
        ):
            raise ValueError(
                "source repair requires a stopped, unfinished own-run BC or PPO ledger"
            )
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="verify-repair-", dir="tmp") as name:
            materialize(directory, state, Path(name))
        for name in required_members(original, state):
            artifacts.member_path(original, state, name)
        weights.verify(directory, state)
        identity = artifacts.source_identity()
        if identity["native_sha256"] != state["native"]:
            raise ValueError("source repair must preserve the native rule engine")
        if identity["source_sha256"] == state["source"]:
            raise ValueError("this implementation is already active")
        if digest(config.qualification) != config.qualification_sha256:
            raise ValueError("source repair qualification hash differs")
        qualified = json.loads(config.qualification.read_text())
        expected = {
            "passed": True,
            "run_id": state["run_id"],
            "completed_update": state["completed_update"],
            "checkpoint_sha256": state["members"][state["latest"]],
            "previous_source": state["source"],
            "source_sha256": identity["source_sha256"],
            "protocol": state["protocol"],
        }
        if unfinished_bc:
            expected["pretraining"] = state["pretraining"]
        scripts_changed = False
        if original.script_population is not None:
            scripts = script_artifacts.identity(original.script_population)
            previous_scripts = {
                key: state["script_runtime"][key] for key in ("backend", "files")
            }
            scripts_changed = scripts != previous_scripts
            if scripts_changed:
                if scripts["files"].keys() != previous_scripts["files"].keys() or any(
                    expected_hash != scripts["files"][name]
                    for name, expected_hash in previous_scripts["files"].items()
                    if not Path(name).name.startswith("_revue_native.")
                ):
                    raise ValueError("source repair must preserve the frozen script route assets")
                expected["previous_script_runtime"] = previous_scripts
                expected["script_runtime"] = scripts
        if any(qualified.get(key) != value for key, value in expected.items()):
            raise ValueError("qualification does not bind this checkpoint, source and protocol")
        revisions = state.get("repair_history", [])
        revision = directory / "source-revisions" / f"{len(revisions) + 1:04d}"
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
            "revision": str(revision.relative_to(directory)),
            "qualification_sha256": config.qualification_sha256,
            "protocol_unchanged": True,
        }
        if scripts_changed:
            assert original.script_population is not None
            archived = script_artifacts.archive(revision, original.script_population)
            if any(archived[key] != value for key, value in scripts.items()):
                raise ValueError("script runtime changed while archiving the source repair")
            archived["directory"] = str(revision.relative_to(directory) / archived["directory"])
            state["script_runtime"] = archived
            transition["previous_script_runtime"] = previous_scripts
            transition["script_runtime"] = scripts
        state["repair_history"] = [*revisions, transition]
        state["source"] = identity["source_sha256"]
        state["source_directory"] = str(revision.relative_to(directory))
        artifacts.write_ledger(directory, state)
        print(json.dumps(transition), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_resume",
)
def main(configuration: DictConfig) -> None:
    """Apply one qualified source repair before ordinary archived recovery."""
    repair(Repair.model_validate(OmegaConf.to_container(configuration.recovery, resolve=True)))


if __name__ == "__main__":
    main()
