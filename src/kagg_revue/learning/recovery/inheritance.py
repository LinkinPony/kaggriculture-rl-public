"""Add discounted predecessor PFSP evidence to a stopped run at its committed boundary."""

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
from kagg_revue.learning.matchmaking.archives import HistoricalArchive
from kagg_revue.learning.matchmaking.config import Inheritance
from kagg_revue.learning.matchmaking.inheritance import inherit
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining import weights
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery
from kagg_revue.learning.storage.roles import required_members


class InheritanceChange(Recovery):
    """Pin a stopped ledger, predecessor ledgers from nearest, and the discount."""

    state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    donors: tuple[HistoricalArchive, ...] = Field(min_length=1)
    inheritance: Inheritance


def change(config: InheritanceChange) -> dict[str, Any]:
    """Publish inherited statistics and a source revision; saved tensors stay untouched."""
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
            raise RuntimeError("stop the existing training process before changing PFSP")
        previous = (directory / "state.json").read_bytes()
        if hashlib.sha256(previous).hexdigest() != config.state_sha256:
            raise ValueError("PFSP inheritance requires the pinned stopped ledger")
        state = json.loads(previous)
        original = Experiment.model_validate(
            state["protocol"], context={"archived_population": True}
        )
        options = original.population.pfsp
        if (
            status["status"] != "stopped"
            or original.output_dir != directory
            or not weights.valid_root(state)
            or not 0 < state["completed_update"] < original.updates
            or options is None
            or options.inheritance is not None
            or not original.population.unified
        ):
            raise ValueError("inheritance requires a stopped unified-PFSP run without it")
        updated = original.model_copy(
            update={
                "population": original.population.model_copy(
                    update={"pfsp": options.model_copy(update={"inheritance": config.inheritance})}
                )
            }
        )
        protocol = artifacts.protocol(updated)
        changed = {
            key
            for key in protocol.keys() | state["protocol"].keys()
            if protocol.get(key) != state["protocol"].get(key)
        }
        pfsp = protocol["population"]["pfsp"]
        if (
            changed != {"population"}
            or {
                **protocol["population"],
                "pfsp": {k: v for k, v in pfsp.items() if k != "inheritance"},
            }
            != state["protocol"]["population"]
        ):
            raise ValueError("this revision must change only PFSP inheritance")
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="verify-inheritance-", dir="tmp") as name:
            materialize(directory, state, Path(name))
        weights.verify(directory, state)
        for member in required_members(original, state):
            artifacts.member_path(original, state, member)
        identity = artifacts.source_identity()
        if identity["native_sha256"] != state["native"]:
            raise ValueError("PFSP inheritance must preserve the native rule engine")
        history = state.get("pfsp_inheritance_history", [])
        revision = directory / "pfsp-inheritance-revisions" / f"{len(history) + 1:04d}"
        revision.mkdir(parents=True, exist_ok=False)
        (revision / "previous-state.json").write_bytes(previous)
        archive_source(revision, identity)
        boundary = artifacts.member_path(original, state, state["latest"])
        os.link(boundary, revision / "checkpoint.pt")
        report = inherit(updated, state, config.donors)
        event = state["pfsp_inheritance_history"][-1]
        event.update(
            time=time.time(),
            reason="user requested discounted predecessor PFSP evidence",
            effective_from_update=state["completed_update"] + 1,
            checkpoint=state["latest"],
            checkpoint_sha256=state["members"][state["latest"]],
            preserved_checkpoint=str((revision / "checkpoint.pt").relative_to(directory)),
            previous_state_sha256=config.state_sha256,
            previous_source=state["source"],
            source=identity["source_sha256"],
            previous_protocol=state["protocol"],
            protocol=protocol,
            revision=str(revision.relative_to(directory)),
            summary=report,
            checkpoint_bytes_unchanged=True,
            optimizer_rng_and_history_preserved=True,
        )
        state.update(
            protocol=protocol,
            source=identity["source_sha256"],
            source_directory=str(revision.relative_to(directory)),
        )
        write_json(revision / "transition.json", {k: v for k, v in event.items() if k != "records"})
        artifacts.write_ledger(directory, state)
        write_json(directory / "resolved-config.json", protocol)
        return report


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_pfsp_inheritance_change",
)
def main(configuration: DictConfig) -> None:
    """Record one requested inheritance before resuming through the source archive."""
    config = InheritanceChange.model_validate(
        OmegaConf.to_container(configuration.change, resolve=True)
    )
    print(json.dumps(change(config)), flush=True)


if __name__ == "__main__":
    main()
