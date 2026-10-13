"""Qualified terminal-reward changes that preserve the current training lineage."""

import fcntl
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Literal

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.optimization.settings import CashMargin
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining import weights
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery
from kagg_revue.learning.storage.roles import required_members
from kagg_revue.opponents.artifacts import identity as script_identity


class RewardChange(Recovery):
    """Authenticate one reward-only continuation of an existing training run."""

    wdl: bool = False
    cash_margin: CashMargin | None = None
    qualification: Path
    qualification_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_reward(self) -> "RewardChange":
        """Require exactly one explicit reward choice."""
        if self.wdl == (self.cash_margin is not None):
            raise ValueError("select either pure WDL or bounded terminal cash margin")
        return self


class WdlChange(RewardChange):
    """Preserve the existing explicit pure-WDL transition entry point."""

    wdl: Literal[True] = True


def wdl_protocol(state: dict[str, Any]) -> Experiment:
    """Remove cash shaping while retaining every other experimental control."""
    return Experiment.model_validate({**state["protocol"], "cash_weight": 0.0, "cash_margin": None})


def margin_protocol(state: dict[str, Any], margin: CashMargin) -> Experiment:
    """Add the requested bounded terminal cash difference to unit WDL."""
    return Experiment.model_validate(
        {**state["protocol"], "cash_weight": 0.0, "cash_margin": margin.model_dump()}
    )


def change(config: RewardChange) -> None:
    """Record an authenticated reward revision without replacing any training tensors."""
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
            raise RuntimeError("stop the recorded training process before changing rewards")
        state = json.loads((directory / "state.json").read_text())
        old = Experiment.model_validate(state["protocol"])
        if (
            old.output_dir != directory
            or not weights.valid_root(state)
            or not 0 < state["completed_update"] < old.updates
            or status["status"] != "stopped"
        ):
            raise ValueError("reward migration requires a stopped, unfinished PPO run")
        updated = (
            margin_protocol(state, config.cash_margin)
            if config.cash_margin is not None
            else wdl_protocol(state)
        )
        protocol = artifacts.protocol(updated)
        differences = {
            key
            for key in protocol.keys() | state["protocol"].keys()
            if protocol.get(key) != state["protocol"].get(key)
        }
        if not differences or not differences <= {"cash_weight", "cash_margin"}:
            raise ValueError("a reward transition may change only terminal reward controls")
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="verify-reward-", dir="tmp") as name:
            materialize(directory, state, Path(name))
        weights.verify(directory, state)
        for member in required_members(old, state):
            artifacts.member_path(old, state, member)
        identity = artifacts.source_identity()
        if identity["native_sha256"] != state["native"]:
            raise ValueError("reward migration must preserve the native rule engine")
        scripts = script_identity(updated.script_population) if updated.script_population else None
        if scripts and any(state["script_runtime"].get(k) != v for k, v in scripts.items()):
            raise ValueError("reward migration must preserve the native opponent runtime")
        if digest(config.qualification) != config.qualification_sha256:
            raise ValueError("reward qualification report hash differs")
        qualified = json.loads(config.qualification.read_text())
        expected = {
            "passed": True,
            "run_id": state["run_id"],
            "completed_update": state["completed_update"],
            "checkpoint_sha256": state["members"][state["latest"]],
            "source_state_sha256": digest(directory / "state.json"),
            "source_sha256": identity["source_sha256"],
            "native_sha256": state["native"],
            "script_runtime": scripts,
            "protocol": protocol,
            "wdl_returns_verified" if config.wdl else "cash_margin_returns_verified": True,
            "full_optimizer_rng_and_parent_chain": True,
            "archived_source_recovery": True,
            "source_run_unchanged": True,
        }
        if any(qualified.get(key) != value for key, value in expected.items()):
            raise ValueError(
                "qualification does not bind this checkpoint, source and reward protocol"
            )
        history = state.get("reward_history", [])
        revision = directory / "reward-revisions" / f"{len(history) + 1:04d}"
        revision.mkdir(parents=True, exist_ok=False)
        write_json(revision / "previous-state.json", state)
        archive_source(revision, identity)
        write_json(revision / "qualification.json", qualified)
        transition = {
            "time": time.time(),
            "reason": "user requested pure WDL for current and future policy optimization"
            if config.wdl
            else "user requested WDL plus bounded terminal cash difference",
            "effective_from_update": state["completed_update"] + 1,
            "checkpoint_sha256": state["members"][state["latest"]],
            "previous_source": state["source"],
            "source": identity["source_sha256"],
            "previous_protocol": state["protocol"],
            "protocol": protocol,
            "reward": {
                "win": 1.0,
                "draw": 0.0,
                "loss": -1.0,
                "cash_weight": 0.0,
                **(
                    {
                        "cash_margin": config.cash_margin.model_dump(mode="json"),
                        "formula": "sign(delta) + beta * delta / (abs(delta) + cash_scale)",
                        "delta": "own terminal cash minus opponent terminal cash",
                    }
                    if config.cash_margin is not None
                    else {}
                ),
            },
            "revision": str(revision.relative_to(directory)),
            "qualification_sha256": config.qualification_sha256,
            "optimizer_rng_history_and_critic_preserved": True,
        }
        state["reward_history"] = [*history, transition]
        state["protocol"] = protocol
        state["source"] = identity["source_sha256"]
        state["source_directory"] = str(revision.relative_to(directory))
        artifacts.write_ledger(directory, state)
        write_json(directory / "resolved-config.json", protocol)
        print(json.dumps(transition), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_wdl_change",
)
def main(configuration: DictConfig) -> None:
    """Apply one qualified terminal-reward revision before archived recovery."""
    change(RewardChange.model_validate(OmegaConf.to_container(configuration.change, resolve=True)))


if __name__ == "__main__":
    main()
