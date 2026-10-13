"""Supervise a running BC's validation-best handoff under a frozen implementation."""

import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.matchmaking.defaults import training_defaults
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.workflows.config import Workflow
from kagg_revue.learning.workflows.process import Supervisor
from kagg_revue.native import _revue_core as native
from kagg_revue.opponents.artifacts import materialize as materialize_scripts


def attach(config: Workflow) -> None:
    """Bind the plan to the live BC protocol, then freeze code for selection and PPO.

    The implementation is archived when the plan is made, so later working-tree
    edits cannot reach the handoff, the opponent bootstrap or the PPO stage.
    """
    if not config.attached_bc:
        raise ValueError("attach requires a plan for an already running BC stage")
    config = config.model_copy(
        update={"bc": training_defaults(config.bc), "rl": training_defaults(config.rl)}
    )
    root = Path.cwd().resolve()
    directory = root / config.output_dir
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "workflow.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (directory / "plan.json").exists() or config.rl.output_dir.exists():
            raise FileExistsError("workflow requires unused plan and RL destinations")
        running = json.loads((config.bc.output_dir / "state.json").read_text())
        if running["protocol"] != artifacts.protocol(config.bc):
            raise ValueError("attached BC protocol differs from the planned BC stage")
        donor = config.historical_archive.run
        if digest(donor / "state.json") != config.historical_archive.state_sha256:
            raise ValueError("opponent archive changed before workflow preparation")
        archived = json.loads((donor / "state.json").read_text())
        implementation = directory / "implementation"
        implementation.mkdir()
        identity = artifacts.source_identity()
        archive_source(implementation, identity)
        binary = Path(native.__file__)
        shutil.copy2(binary, implementation / binary.name)
        frozen = {
            "source": identity["source_sha256"],
            "native": identity["native_sha256"],
            "source_directory": "implementation",
            "native_artifact": f"implementation/{binary.name}",
        }
        plan = directory / "plan.json"
        write_json(plan, config.model_dump(mode="json"))
        temporary = root / "tmp"
        temporary.mkdir(exist_ok=True)
        supervisor = Supervisor()
        try:
            with tempfile.TemporaryDirectory(prefix="learning-workflow-", dir=temporary) as name:
                isolated = Path(name)
                materialized = materialize(directory, frozen, isolated)
                materialize_scripts(donor, archived["script_runtime"], isolated)
                for linked in ("outputs", "data"):
                    (isolated / linked).symlink_to(root / linked, target_is_directory=True)
                (isolated / "tmp").mkdir()
                environment = {
                    **os.environ,
                    "PYTHONPATH": str(isolated / "src"),
                    "TMPDIR": str(isolated / "tmp"),
                    "TORCHINDUCTOR_CACHE_DIR": str(temporary / "torchinductor"),
                    "TRITON_CACHE_DIR": str(temporary / "triton"),
                }
                write_json(
                    directory / "implementation.json",
                    {
                        **materialized,
                        "plan_sha256": digest(plan),
                        "parent_pid": os.getpid(),
                        "isolated": str(isolated),
                        "attached_bc": str(config.bc.output_dir),
                        "attached_bc_run_id": running["run_id"],
                        "script_runtime": archived["script_runtime"],
                    },
                )
                with (directory / "runner.log").open("a") as log:
                    code = supervisor.run(
                        [sys.executable, "-m", "kagg_revue.learning.workflows.runner", str(plan)],
                        cwd=isolated,
                        env=environment,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                    )
                if code:
                    raise RuntimeError("workflow failed; inspect runner.log and status.json")
        finally:
            supervisor.close()


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="workflow_strength_canonical_bc_to_rl_20260928",
)
def main(configuration: DictConfig) -> None:
    """Resolve the complete plan against the running BC before supervising the handoff."""
    attach(Workflow.model_validate(OmegaConf.to_container(configuration.workflow, resolve=True)))


if __name__ == "__main__":
    main()
