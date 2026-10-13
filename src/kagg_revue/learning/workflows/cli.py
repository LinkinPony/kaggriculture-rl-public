"""Archive both training stages before running them in an isolated implementation."""

import fcntl
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.matchmaking.defaults import training_defaults
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.workflows.config import Workflow
from kagg_revue.learning.workflows.process import Supervisor
from kagg_revue.opponents.artifacts import materialize as materialize_scripts


def launch(config: Workflow) -> None:
    """Pin code, protocols and native scripts while keeping every run artifact durable."""
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
        donor = config.historical_archive.run
        if digest(donor / "state.json") != config.historical_archive.state_sha256:
            raise ValueError("opponent archive changed before workflow preparation")
        archived = json.loads((donor / "state.json").read_text())
        supervisor = Supervisor()
        try:
            config.bc.output_dir.mkdir(parents=True, exist_ok=True)
            with (config.bc.output_dir / "run.lock").open("a") as bc_lock:
                fcntl.flock(bc_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                state = artifacts.create(config.bc, runtime_settings(config.bc))
            plan = directory / "plan.json"
            write_json(plan, config.model_dump(mode="json"))
            temporary = root / "tmp"
            temporary.mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="learning-workflow-", dir=temporary) as name:
                isolated = Path(name)
                identity = materialize(config.bc.output_dir, state, isolated)
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
                write_json(directory / "implementation.json", {
                    **identity,
                    "plan_sha256": digest(plan),
                    "parent_pid": os.getpid(),
                    "isolated": str(isolated),
                    "script_runtime": archived["script_runtime"],
                })
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
    config_name="workflow_watch6_u2137_bc_to_rl_20260927",
)
def main(configuration: DictConfig) -> None:
    """Resolve the complete training plan before archiving and launching either stage."""
    launch(Workflow.model_validate(OmegaConf.to_container(configuration.workflow, resolve=True)))


if __name__ == "__main__":
    main()
