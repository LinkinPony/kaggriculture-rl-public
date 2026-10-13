"""Qualified switches to current-policy mirror games and larger learner batches."""

import fcntl
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Literal

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


class SelfPlayChange(Recovery):
    """Bind the requested game count, minibatch and execution to a tested continuation."""

    selfplay: Literal[True] = True
    games: int = Field(default=128, gt=0)
    train_seed: int = Field(ge=0)
    batch_rows: int = Field(gt=0)
    sequence_games_per_rank: int | None = Field(default=None, gt=0)
    actor_learning_rate: float | None = Field(default=None, gt=0)
    target_kl: float | None = Field(default=None, gt=0)
    kl_control: Literal["rollback", "early_stop"] | None = None
    execution: Execution
    qualification: Path
    qualification_sha256: str = Field(default="0" * 64, pattern=r"^[a-f0-9]{64}$")


def resolved(state: dict[str, Any], change: SelfPlayChange) -> Experiment:
    """Change only explicitly requested sampling and batch controls on the same model."""
    old = Experiment.model_validate(state["protocol"])
    same_allocation = change.games == old.games and change.train_seed == old.train_seed
    if not same_allocation and change.train_seed < old.train_seed + old.games * old.updates:
        raise ValueError("resized rollouts require a fresh seed range after the old allocation")
    if old.execution is None or change.execution.devices != old.execution.devices:
        raise ValueError("self-play tuning must preserve the registered worker RNG streams")
    return Experiment.model_validate(
        {
            **state["protocol"],
            "games": change.games,
            "train_seed": change.train_seed,
            "batch_rows": change.batch_rows,
            "sequence_games_per_rank": change.sequence_games_per_rank
            if change.sequence_games_per_rank is not None
            else old.sequence_games_per_rank,
            "actor_learning_rate": change.actor_learning_rate
            if change.actor_learning_rate is not None
            else old.actor_learning_rate,
            "target_kl": change.target_kl if change.target_kl is not None else old.target_kl,
            "kl_control": change.kl_control or old.kl_control,
            "execution": change.execution.model_dump(),
            "population": {**old.population.model_dump(), "fraction": 0.0, "pfsp": None},
            "script_population": None,
        }
    )


def sampling_fields(config: Experiment) -> dict[str, Any]:
    """Describe the same allowed changes to an isolated qualification copy."""
    return {
        "games": config.games,
        "train_seed": config.train_seed,
        "batch_rows": config.batch_rows,
        "population": config.population.model_dump(),
        "script_population": None,
        **(
            {
                "sequence_games_per_rank": config.sequence_games_per_rank,
                "actor_learning_rate": config.actor_learning_rate,
                "target_kl": config.target_kl,
                "kl_control": config.kl_control,
            }
            if config.memory_turns
            else {}
        ),
    }


def change(config: SelfPlayChange) -> None:
    """Archive an authenticated protocol revision while retaining every training tensor."""
    directory = config.run
    with (directory / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status = json.loads((directory / "run-status.json").read_text())
        try:
            os.kill(status["pid"], 0)
        except ProcessLookupError:
            pass
        else:
            raise RuntimeError("stop the existing training process before changing sampling")
        state = json.loads((directory / "state.json").read_text())
        old = Experiment.model_validate(state["protocol"])
        if (
            old.output_dir != directory
            or state["schema"] != "random-root-league-v1"
            or state["input_weights"]
            or state["initialization"] != "random"
            or not 0 < state["completed_update"] < old.updates
        ):
            raise ValueError("self-play changes require an unfinished own-run PPO checkpoint")
        updated = resolved(state, config)
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="verify-selfplay-", dir="tmp") as name:
            materialize(directory, state, Path(name))
        for member in required_members(old, state):
            artifacts.member_path(old, state, member)
        identity = artifacts.source_identity()
        if identity["native_sha256"] != state["native"]:
            raise ValueError("sampling changes must preserve the authenticated native rule engine")
        if digest(config.qualification) != config.qualification_sha256:
            raise ValueError("self-play qualification report hash differs")
        qualified = json.loads(config.qualification.read_text())
        expected = {
            "passed": True,
            "run_id": state["run_id"],
            "completed_update": state["completed_update"],
            "checkpoint_sha256": state["members"][state["latest"]],
            "source_state_sha256": digest(directory / "state.json"),
            "source_sha256": identity["source_sha256"],
            "native_sha256": state["native"],
            "script_runtime": None,
            "protocol": artifacts.protocol(updated),
        }
        if any(qualified.get(key) != value for key, value in expected.items()):
            raise ValueError("qualification does not bind this checkpoint, source and protocol")
        if not qualified.get("full_optimizer_rng_and_parent_chain"):
            _verify_benchmark(qualified, state, updated)
        revisions = state.get("sampling_history", [])
        revision = directory / "sampling-revisions" / f"{len(revisions) + 1:04d}"
        revision.mkdir(parents=True, exist_ok=False)
        write_json(revision / "previous-state.json", state)
        archive_source(revision, identity)
        write_json(revision / "qualification.json", qualified)
        transition = {
            "time": time.time(),
            "reason": "user requested pure self-play with qualified sampling and batch controls",
            "effective_from_update": state["completed_update"] + 1,
            "checkpoint_sha256": state["members"][state["latest"]],
            "previous_source": state["source"],
            "source": identity["source_sha256"],
            "previous_protocol": state["protocol"],
            "protocol": artifacts.protocol(updated),
            "revision": str(revision.relative_to(directory)),
            "qualification_sha256": config.qualification_sha256,
            "optimizer_rng_and_history_preserved": True,
            "completed_physical_games": sum(row["physical_games"] for row in state["records"]),
            "remaining_physical_games": (updated.updates - state["completed_update"])
            * updated.games,
        }
        state["sampling_history"] = [*revisions, transition]
        state["protocol"] = artifacts.protocol(updated)
        state["source"] = identity["source_sha256"]
        state["source_directory"] = str(revision.relative_to(directory))
        state.pop("script_runtime", None)
        artifacts.write_ledger(directory, state)
        write_json(directory / "resolved-config.json", state["protocol"])
        print(json.dumps(transition), flush=True)


def _verify_benchmark(qualified: dict[str, Any], state: dict[str, Any], config: Experiment) -> None:
    """Accept an explicitly selected measured profile without claiming a separate resume test."""
    evidence = qualified.get("selected_benchmark", {})
    if (
        evidence.get("launch_authorization")
        != "user requested direct launch of this measured profile"
    ):
        raise ValueError("direct launch requires an explicitly selected measured profile")
    path = Path(evidence["path"])
    if digest(path) != evidence["sha256"]:
        raise ValueError("selected benchmark hash differs")
    measured = json.loads(path.read_text())
    assert config.execution is not None
    expected = {
        "run_id": state["run_id"],
        "update": state["completed_update"],
        "checkpoint_sha256": state["members"][state["latest"]],
        "execution": config.execution.model_dump(mode="json"),
        "batch_rows": config.batch_rows,
        "physical_games": config.games,
    }
    if any(measured.get(key) != value for key, value in expected.items()):
        raise ValueError("selected benchmark does not match the requested continuation")
    rows = measured["measurements"]
    if len(rows) < 3 or any(
        row["maximum_rank_parameter_difference"] != 0
        or row["optimization"]["actor_steps"] <= 0
        or row["optimization"]["critic_steps"] <= 0
        for row in rows
    ):
        raise ValueError("selected benchmark lacks repeated synchronized optimizer updates")


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_selfplay_change",
)
def main(configuration: DictConfig) -> None:
    """Apply the requested and qualified pure self-play continuation."""
    change(
        SelfPlayChange.model_validate(OmegaConf.to_container(configuration.change, resolve=True))
    )


if __name__ == "__main__":
    main()
