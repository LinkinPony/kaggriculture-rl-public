"""Qualified, explicitly requested opponent changes on an existing training lineage."""

import fcntl
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.collection.public import records
from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.matchmaking.archives import HistoricalArchive, import_archive
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining.weights import valid_root
from kagg_revue.learning.pretraining.weights import verify as verify_weights
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery
from kagg_revue.learning.storage.roles import required_members
from kagg_revue.opponents import artifacts as script_artifacts
from kagg_revue.opponents.settings import PublicPopulation


class BatchChange(FrozenSettings):
    """A requested rollout size and a fresh, disjoint training seed allocation."""

    games: int = Field(gt=0)
    train_seed: int = Field(ge=0)


class PopulationChange(Recovery):
    """Bind sampling and optional execution changes to authenticated integration evidence."""

    population: Population
    script_population: PublicPopulation
    batch: BatchChange | None = None
    execution: Execution | None = None
    historical_archive: HistoricalArchive | None = None
    qualification: Path
    qualification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def changed_protocol(
    state: dict[str, Any],
    population: Population,
    scripts: PublicPopulation,
    batch: BatchChange | None = None,
    execution: Execution | None = None,
) -> Experiment:
    """Preserve model/optimizer controls outside declared sampling and execution changes."""
    previous = Experiment.model_validate(state["protocol"], context={"archived_population": True})
    if (
        population.snapshot_interval != previous.population.snapshot_interval
        or population.capacity != previous.population.capacity
    ) and population.pfsp is None:
        raise ValueError("opponent integration must preserve the existing history archive")
    if batch is not None:
        if population != previous.population or scripts != previous.script_population:
            raise ValueError("batch resizing must preserve opponent composition")
        if batch.train_seed < previous.train_seed + previous.games * previous.updates:
            raise ValueError("resized batches require a fresh seed allocation after the old range")
    return Experiment.model_validate(
        {
            **state["protocol"],
            "population": population.model_dump(),
            "script_population": scripts.model_dump(),
            **(batch.model_dump() if batch is not None else {}),
            **({"execution": execution.model_dump()} if execution is not None else {}),
        }
    )


def change(config: PopulationChange) -> None:
    """Archive the transition without replacing any checkpoint or optimizer state."""
    directory = config.run
    with (directory / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status = json.loads((directory / "run-status.json").read_text())
        try:
            os.kill(status["pid"], 0)
        except ProcessLookupError:
            pass
        else:
            raise RuntimeError("stop the existing training process before changing opponents")
        state = json.loads((directory / "state.json").read_text())
        old = Experiment.model_validate(state["protocol"], context={"archived_population": True})
        if (
            old.output_dir != directory
            or not valid_root(state)
            or not 0 < state["completed_update"] < old.updates
        ):
            raise ValueError("opponent changes require an unfinished own-run PPO checkpoint")
        verify_weights(directory, state)
        resolved = changed_protocol(
            state, config.population, config.script_population, config.batch, config.execution
        )
        expected_protocol = artifacts.protocol(resolved)
        changes = {
            key
            for key in expected_protocol.keys() | state["protocol"].keys()
            if expected_protocol.get(key) != state["protocol"].get(key)
        }
        allowed = {"games", "train_seed"} if config.batch else {"population", "script_population"}
        if config.execution is not None:
            allowed.add("execution")
        if (
            not changes
            or not changes <= allowed
            or (config.batch and not {"games", "train_seed"} <= changes)
        ):
            raise ValueError("this transition must change only its declared sampling controls")
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="verify-population-", dir="tmp") as name:
            materialize(directory, state, Path(name))
        for member in required_members(old, state):
            artifacts.member_path(old, state, member)
        selected = records(config.script_population)
        identity = artifacts.source_identity()
        if identity["native_sha256"] != state["native"]:
            raise ValueError("public integration must preserve the authenticated rule engine")
        if digest(config.qualification) != config.qualification_sha256:
            raise ValueError("opponent qualification report hash differs")
        qualified = json.loads(config.qualification.read_text())
        expected = {
            "passed": True,
            "run_id": state["run_id"],
            "completed_update": state["completed_update"],
            "checkpoint_sha256": state["members"][state["latest"]],
            "source_state_sha256": digest(directory / "state.json"),
            "source_sha256": identity["source_sha256"],
            "native_sha256": state["native"],
            "script_runtime": script_artifacts.identity(config.script_population),
            "protocol": expected_protocol,
        }
        if config.historical_archive is not None:
            expected["historical_archive"] = config.historical_archive.model_dump(mode="json")
        if any(qualified.get(key) != value for key, value in expected.items()):
            raise ValueError("qualification does not bind this source, checkpoint and population")
        history_key = "batch_history" if config.batch else "population_history"
        revision = (
            directory
            / ("batch-revisions" if config.batch else "population-revisions")
            / f"{len(state.get(history_key, [])) + 1:04d}"
        )
        revision.mkdir(parents=True, exist_ok=False)
        write_json(revision / "previous-state.json", state)
        archive_source(revision, identity)
        scripts = script_artifacts.archive(revision, config.script_population)
        scripts["directory"] = str(revision.relative_to(directory) / scripts["directory"])
        write_json(revision / "qualification.json", qualified)
        selfplay_fraction = 1 - resolved.population.fraction - config.script_population.fraction
        transition = {
            "time": time.time(),
            "reason": (
                f"user requested {old.games} to {resolved.games} games per update"
                if config.batch
                else (
                    f"user requested {100 * selfplay_fraction:g}% "
                    f"self-play, {100 * resolved.population.fraction:g}% history, "
                    f"{100 * config.script_population.fraction:g}% public scripts"
                )
            ),
            "effective_from_update": state["completed_update"] + 1,
            "checkpoint_sha256": state["members"][state["latest"]],
            "previous_source": state["source"],
            "source": identity["source_sha256"],
            "previous_protocol": state["protocol"],
            "protocol": expected_protocol,
            "scripts": {name: record.model_dump(mode="json") for name, record in selected.items()},
            "revision": str(revision.relative_to(directory)),
            "qualification": str(config.qualification),
            "qualification_sha256": config.qualification_sha256,
            "optimizer_rng_and_history_preserved": True,
            "completed_physical_games": sum(row["physical_games"] for row in state["records"]),
            "remaining_physical_games": (resolved.updates - state["completed_update"])
            * resolved.games,
            "evaluation_scope": "training scripts are seen opponents",
        }
        if resolved.population.unified:
            transition["reason"] = (
                f"user requested {100 * (1 - resolved.population.fraction):g}% self-play "
                f"and {100 * resolved.population.fraction:g}% unified PFSP "
                "across history and scripts"
            )
        state[history_key] = [*state.get(history_key, []), transition]
        if resolved.execution != old.execution:
            assert resolved.execution is not None
            transition["reason"] += f"; execution devices {list(resolved.execution.devices)}"
            transition["execution"] = resolved.execution.model_dump(mode="json")
            transition["rng_transition"] = (
                "shared ranks restored; added ranks seeded from root seed, rank and update; "
                "original checkpoint RNG retained"
            )
            state["execution_history"] = [
                *state.get("execution_history", []),
                {**transition, "completed_update": state["completed_update"]},
            ]
        state["protocol"] = expected_protocol
        state["source"] = identity["source_sha256"]
        state["source_directory"] = str(revision.relative_to(directory))
        state["script_runtime"] = scripts
        if resolved.population.pfsp is not None:
            from kagg_revue.learning.matchmaking.imports import ensure_imported
            from kagg_revue.learning.matchmaking.imports import transition as migrate

            if config.historical_archive is not None:
                transition["historical_archive"] = import_archive(
                    resolved, state, config.historical_archive
                )
            ensure_imported(resolved, state)
            migrate(resolved, state, old)
        artifacts.write_ledger(directory, state)
        write_json(directory / "resolved-config.json", expected_protocol)
        print(json.dumps(transition), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_population_change",
)
def main(configuration: DictConfig) -> None:
    """Apply a qualified population change explicitly requested for one running lineage."""
    change(
        PopulationChange.model_validate(OmegaConf.to_container(configuration.change, resolve=True))
    )


if __name__ == "__main__":
    main()
