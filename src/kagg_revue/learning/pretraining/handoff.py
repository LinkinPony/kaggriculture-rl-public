"""Qualified latest-BC handoff to mixed opponents, preserving the original lineage."""

import fcntl
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.imports import import_opponents, transition
from kagg_revue.learning.matchmaking.verification import finite
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining import native as native_transition
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.opponents.artifacts import archive as archive_scripts
from kagg_revue.opponents.artifacts import identity as script_identity

ALLOWED = {
    "pretraining_only",
    "population",
    "script_population",
    "batch_rows",
    "sequence_games_per_rank",
    "execution",
    "actor_learning_rate",
    "critic_learning_rate",
    "learning_rate_warmup_updates",
    "gamma",
    "gae_lambda",
}


def stopped(config: Experiment) -> dict[str, Any]:
    """Authenticate the latest own-run BC and only the requested phase/sampling changes."""
    directory = config.output_dir
    status = json.loads((directory / "run-status.json").read_text())
    try:
        os.kill(status["pid"], 0)
    except ProcessLookupError:
        pass
    else:
        raise ValueError("BC process must stop before handoff")
    state: dict[str, Any] = json.loads((directory / "state.json").read_text())
    original = Experiment.model_validate(state["protocol"])
    if (
        status["status"] != "stopped"
        or state["completed_update"]
        or "rl_initial" in state
        or not state.get("pretraining", {}).get("cursor")
        or state["initialization"] != "random"
        or state["input_weights"]
        or original.output_dir != directory
        or config.pretraining_only
        or config.cash_weight
        or config.cash_margin is not None
    ):
        raise ValueError("handoff requires stopped own-run BC and terminal-WDL RL")
    target = artifacts.protocol(config)
    changes = {
        key
        for key in target.keys() | state["protocol"].keys()
        if target.get(key) != state["protocol"].get(key)
    }
    if not changes <= ALLOWED:
        raise ValueError(f"handoff changes unrelated controls: {changes - ALLOWED}")
    with tempfile.TemporaryDirectory(prefix="verify-mixed-bc-", dir="tmp") as name:
        materialize(directory, state, Path(name))
    payload = torch.load(
        artifacts.member_path(original, state, state["latest"]),
        map_location="cpu",
        weights_only=False,
    )
    progress = state["pretraining"]
    if (
        payload.get("pretraining") != progress
        or not finite(payload)
        or payload["lineage"]["run_id"] != state["run_id"]
        or {int(r["step"]) for r in payload["optimizer"]["state"].values()}
        != {progress["optimizer_steps"]}
        or len(payload["rng"]["workers"])
        != len(config.execution.devices if config.execution else [0])
    ):
        raise ValueError("latest BC weights, Adam, RNG or progress failed authentication")
    return state


def activate(config: Experiment, state: dict[str, Any], native_report: Path) -> None:
    """Register frozen foreign opponents and initialize fresh PFSP evidence for this actor."""
    previous = Experiment.model_validate(state["protocol"])
    selected = state["latest"]
    state.update(rl_initial=selected, bc_final=selected, pool=[selected])
    state["opponent_native_qualification"] = {
        "path": str(native_report),
        "sha256": digest(native_report),
    }
    import_opponents(config, state)
    transition(config, state, previous)
    state["protocol"] = artifacts.protocol(config)


def commit(config: Experiment, options: DictConfig) -> None:
    """Publish a tested protocol and source revision without rewriting any saved BC state."""
    directory = config.output_dir
    with (directory / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = stopped(config)
        identity = artifacts.source_identity()
        native_transition.validate(state, Path(options.encoder_qualification))
        assert config.script_population is not None
        report_path = Path(options.qualification)
        report = json.loads(report_path.read_text())
        expected = {
            "passed": True,
            "run_id": state["run_id"],
            "source_state_sha256": digest(directory / "state.json"),
            "checkpoint_sha256": state["members"][state["latest"]],
            "source_sha256": identity["source_sha256"],
            "native_sha256": identity["native_sha256"],
            "encoder_qualification_sha256": digest(Path(options.encoder_qualification)),
            "protocol": artifacts.protocol(config),
            "native_qualification_sha256": digest(Path(options.native_qualification)),
            "script_runtime": script_identity(config.script_population),
        }
        if any(report.get(key) != value for key, value in expected.items()):
            raise ValueError("qualification does not bind the latest BC, source and RL protocol")
        revision = directory / "bc-completion" / "0001"
        revision.mkdir(parents=True, exist_ok=False)
        write_json(revision / "previous-state.json", state)
        archive_source(revision, identity)
        write_json(revision / "qualification.json", report)
        assert config.script_population is not None
        scripts = archive_scripts(revision, config.script_population)
        scripts["directory"] = str(revision.relative_to(directory) / scripts["directory"])
        native_transition.install(directory, state, Path(options.encoder_qualification))
        activate(config, state, Path(options.native_qualification))
        event = {
            "time": time.time(),
            "reason": "explicit_user_latest_bc_to_script_pfsp_rl",
            "checkpoint": state["rl_initial"],
            "checkpoint_sha256": state["members"][state["rl_initial"]],
            "pretraining": state["pretraining"],
            "previous_source": state["source"],
            "source": identity["source_sha256"],
            "qualification_sha256": digest(report_path),
            "revision": str(revision.relative_to(directory)),
        }
        state.update(
            source=identity["source_sha256"],
            source_directory=str(revision.relative_to(directory)),
            script_runtime=scripts,
            bc_completion=event,
        )
        write_json(revision / "transition.json", event)
        artifacts.write_ledger(directory, state)
        write_json(directory / "resolved-config.json", state["protocol"])
        print(json.dumps({"phase": "handoff", "checkpoint": state["latest"]}), flush=True)


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="learning_agronomy_rl_20260917",
)
def main(configuration: DictConfig) -> None:
    """Commit only an authenticated latest-weight mixed-opponent handoff."""
    torch.set_num_threads(2)
    config = Experiment.model_validate(
        OmegaConf.to_container(configuration.experiment, resolve=True)
    )
    commit(config, configuration.handoff)


if __name__ == "__main__":
    main()
