"""Restart explicitly requested PPO controls from a preserved own-lineage BC boundary."""

import copy
import fcntl
import json
import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.verification import finite
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery


def restart(source: Recovery, config: Experiment) -> None:
    """Create a separate PPO branch while leaving every parent artifact untouched."""
    directory = source.run
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
            raise RuntimeError("stop the source training process before restarting PPO")
        parent = json.loads((directory / "state.json").read_text())
        original = Experiment.model_validate(parent["protocol"])
        if (
            status["status"] != "stopped"
            or original.output_dir != directory
            or parent["schema"] != "random-root-league-v1"
            or parent["initialization"] != "random"
            or parent["input_weights"]
            or not parent["completed_update"]
            or parent.get("rl_initial") != parent.get("bc_final")
            or not parent.get("bc_final")
            or config.pretraining_only
            or config.resume
            or config.population.pfsp is not None
            or config.script_population is not None
        ):
            raise ValueError("restart requires stopped own-lineage BC/PPO with a neural pool")
        target_protocol = artifacts.protocol(config)
        changes = {
            key
            for key in target_protocol.keys() | parent["protocol"].keys()
            if target_protocol.get(key) != parent["protocol"].get(key)
        }
        if not changes <= {"output_dir", "gamma", "gae_lambda", "batch_rows"}:
            raise ValueError(f"restart changes unrelated controls: {changes}")
        destination = config.output_dir
        if destination.exists():
            raise FileExistsError(destination)
        runtime_settings(config)
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="verify-ppo-restart-", dir="tmp") as name:
            materialize(directory, parent, Path(name))
        selected = parent["bc_final"]
        boundary = directory / parent["bc_completion"]["revision"] / "bc-final.pt"
        if digest(boundary) != parent["members"][selected]:
            raise ValueError("preserved full BC boundary differs from the original identity")
        payload = torch.load(boundary, map_location="cpu", weights_only=False)
        if (
            payload.get("lineage", {}).get("run_id") != parent["run_id"]
            or payload.get("pretraining") != parent["pretraining"]
            or not finite(payload)
            or {int(row["step"]) for row in payload["optimizer"]["state"].values()}
            != {parent["pretraining"]["optimizer_steps"]}
            or len(payload["rng"].get("workers", [payload["rng"]]))
            != len(config.execution.devices if config.execution else [0])
        ):
            raise ValueError("BC boundary weights, optimizer, RNG or lineage failed verification")
        identity = artifacts.source_identity()
        if identity["native_sha256"] != parent["native"]:
            raise ValueError("restart must preserve the authenticated native rule engine")
        names = {
            "initial.pt",
            selected,
            *(f"anchors/seed-{seed}.pt" for seed in config.evaluation.anchor_seeds),
        }
        sources = {
            name: boundary if name == selected else artifacts.member_path(original, parent, name)
            for name in names
        }
        artifacts.member_path(original, parent, parent["latest"])
        destination.mkdir(parents=True)
        for name, path in sources.items():
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            if digest(target) != parent["members"][name]:
                raise ValueError("restart copy changed an authenticated checkpoint")
        native = Path(parent["native_artifact"])
        (destination / native).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(directory / native, destination / native)
        revision = Path(parent["bc_completion"]["revision"])
        shutil.copytree(directory / revision, destination / revision)
        archive_source(destination, identity)
        event = {
            "branch_id": uuid.uuid4().hex,
            "time": time.time(),
            "reason": "explicit_user_restore_large_model_gamma_lambda_and_dual_gpu_step_count",
            "directory": str(directory),
            "source_state_sha256": digest(directory / "state.json"),
            "completed_update": parent["completed_update"],
            "stopped_checkpoint": parent["latest"],
            "stopped_checkpoint_sha256": parent["members"][parent["latest"]],
            "bc_checkpoint": selected,
            "bc_checkpoint_sha256": parent["members"][selected],
            "changed_protocol_fields": sorted(changes),
            "run_id_scope": "shared random-root and BC lineage; distinct PPO branch directory",
            "optimizer": "fresh PPO actor and critic Adam; original BC optimizer preserved",
            "rng": "original configured PPO initialization seeds; not parent PPO continuation",
        }
        state = {
            key: copy.deepcopy(parent[key])
            for key in (
                "schema", "run_id", "initialization", "input_weights", "native",
                "native_artifact", "pretraining", "rl_initial", "bc_final", "bc_completion",
            )
        }
        state.update(
            created_at=time.time(),
            protocol=target_protocol,
            source=identity["source_sha256"],
            source_directory=".",
            members={name: parent["members"][name] for name in names},
            pool=[selected],
            completed_update=0,
            latest=selected,
            records=[],
            restart_parent=event,
        )
        provenance = destination / "restart"
        provenance.mkdir()
        write_json(provenance / "parent-state.json", parent)
        write_json(provenance / "transition.json", event)
        artifacts.write_ledger(destination, state)
        write_json(destination / "resolved-config.json", target_protocol)
        write_json(
            destination / "run-status.json",
            {"status": "stopped", "pid": status["pid"], "completed_update": 0, "prepared": True},
        )
        print(json.dumps(event), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_compact_ppo_restart_20260921",
)
def main(configuration: DictConfig) -> None:
    """Resolve the requested restart protocol and parent through Hydra."""
    torch.set_num_threads(2)
    restart(
        Recovery.model_validate(OmegaConf.to_container(configuration.restart, resolve=True)),
        Experiment.model_validate(OmegaConf.to_container(configuration.experiment, resolve=True)),
    )


if __name__ == "__main__":
    main()
