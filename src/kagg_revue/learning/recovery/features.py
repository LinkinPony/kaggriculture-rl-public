"""Continue an authenticated v4 PPO run with complete additive v5b features."""

import copy
import fcntl
import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.artifacts.serialization import save
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.features import evidence
from kagg_revue.learning.features.checkpoint import expand
from kagg_revue.learning.matchmaking.archives import NativeQualification
from kagg_revue.learning.matchmaking.imports import layout_from_payload, validate_layout
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining import weights
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery
from kagg_revue.learning.storage.roles import required_members
from kagg_revue.native import _revue_core as native
from kagg_revue.opponents import artifacts as script_artifacts
from kagg_revue.policy.contracts import ContractLayout


class FeatureChange(Recovery):
    """Pin the stopped training ledger and independently qualified v5b compatibility."""

    state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    native_qualification: NativeQualification
    model_qualification: NativeQualification
    script_qualification: NativeQualification


def change(config: FeatureChange) -> dict[str, Any]:
    """Preserve the original run and every old identity, migrating only the live checkpoint."""
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
            raise RuntimeError("stop the source training process before migrating features")
        previous = (directory / "state.json").read_bytes()
        if hashlib.sha256(previous).hexdigest() != config.state_sha256:
            raise ValueError("feature migration requires the pinned stopped ledger")
        state = json.loads(previous)
        original = Experiment.model_validate(state["protocol"])
        if (
            status["status"] != "stopped"
            or original.output_dir != directory
            or not weights.valid_root(state)
            or not 0 < state["completed_update"] < original.updates
            or original.derived
            or not original.agronomy
            or not original.memory_turns
            or original.script_population is None
        ):
            raise ValueError("feature continuation requires a stopped, complete v4 PPO state")
        updated = Experiment.model_validate({**state["protocol"], "derived": True})
        if artifacts.protocol(updated) != {**state["protocol"], "derived": True}:
            raise ValueError("feature continuation must preserve all other training controls")
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="verify-features-", dir="tmp") as name:
            materialize(directory, state, Path(name))
        weights.verify(directory, state)
        settings = runtime_settings(updated)
        layout = ContractLayout.resolve(settings)
        for member in required_members(original, state):
            path = artifacts.member_path(original, state, member)
            if member in state["pool"]:
                payload = torch.load(path, map_location="cpu", weights_only=False, mmap=True)
                validate_layout(layout, layout_from_payload(payload))
        identity = artifacts.source_identity()
        evidence.verify(
            state,
            updated,
            identity["native_sha256"],
            config.native_qualification,
            config.model_qualification,
            config.script_qualification,
        )
        source = artifacts.member_path(original, state, state["latest"])
        payload = torch.load(source, map_location="cpu", weights_only=False, mmap=True)
        if (
            payload["update"] != state["completed_update"]
            or payload["lineage"]["run_id"] != state["run_id"]
            or payload["pfsp"] != state["pfsp"]
        ):
            raise ValueError("source checkpoint does not preserve the committed PPO boundary")
        expanded, report = expand(payload, settings, state["members"][state["latest"]])
        history = state.get("feature_history", [])
        revision = directory / "feature-revisions" / f"{len(history) + 1:04d}"
        revision.mkdir(parents=True, exist_ok=False)
        (revision / "previous-state.json").write_bytes(previous)
        os.link(source, revision / "previous-checkpoint.pt")
        archive_source(revision, identity)
        binary = revision / "native" / Path(native.__file__).name
        binary.parent.mkdir()
        shutil.copy2(native.__file__, binary)
        if digest(binary) != identity["native_sha256"]:
            raise ValueError("native binary changed while archiving the feature revision")
        scripts = script_artifacts.archive(revision, original.script_population)
        scripts["directory"] = str(revision.relative_to(directory) / scripts["directory"])
        for name, pointer in (
            ("native", config.native_qualification),
            ("model", config.model_qualification),
            ("script", config.script_qualification),
        ):
            evidence.read(pointer)
            shutil.copy2(pointer.path, revision / f"{name}-qualification.json")
        checkpoint = revision / "migrated.pt"
        checksum = save(expanded, checkpoint)
        transition = {
            "time": time.time(),
            "reason": "user requested direct v4 to full v5b PPO continuation",
            "effective_from_update": state["completed_update"] + 1,
            "completed_update": state["completed_update"],
            "previous_checkpoint": state["latest"],
            "previous_checkpoint_sha256": state["members"][state["latest"]],
            "preserved_previous_checkpoint": str(
                (revision / "previous-checkpoint.pt").relative_to(directory)
            ),
            "checkpoint": str(checkpoint.relative_to(directory)),
            "checkpoint_sha256": checksum,
            "previous_state_sha256": config.state_sha256,
            "previous_source": state["source"],
            "source": identity["source_sha256"],
            "previous_native": state["native"],
            "native": identity["native_sha256"],
            "previous_protocol": state["protocol"],
            "protocol": artifacts.protocol(updated),
            "revision": str(revision.relative_to(directory)),
            "migration": report,
        }
        migrated = copy.deepcopy(state)
        migrated["members"][transition["checkpoint"]] = checksum
        migrated.update(
            protocol=transition["protocol"],
            source=identity["source_sha256"],
            source_directory=transition["revision"],
            native=identity["native_sha256"],
            native_artifact=str(binary.relative_to(directory)),
            script_runtime=scripts,
            latest=transition["checkpoint"],
            feature_history=[*history, transition],
            opponent_native_qualification={
                "path": str(revision / "native-qualification.json"),
                "sha256": config.native_qualification.sha256,
            },
        )
        if digest(directory / "state.json") != config.state_sha256:
            raise ValueError("source ledger changed during feature migration")
        write_json(revision / "transition.json", transition)
        artifacts.write_ledger(directory, migrated)
        write_json(directory / "resolved-config.json", migrated["protocol"])
        return transition


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_feature_change",
)
def main(configuration: DictConfig) -> None:
    """Apply the qualified migration before the usual archived recovery command."""
    config = FeatureChange.model_validate(
        OmegaConf.to_container(configuration.change, resolve=True)
    )
    print(json.dumps(change(config)), flush=True)


if __name__ == "__main__":
    main()
