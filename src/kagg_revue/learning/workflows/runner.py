"""Execute a frozen BC-to-PPO plan with a validated, cancellation-aware handoff."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.bootstrap import prepare
from kagg_revue.learning.workflows.config import Workflow
from kagg_revue.learning.workflows.process import Supervisor
from kagg_revue.learning.workflows.selection import select

ATTACH_POLL_SECONDS = 30.0


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def attend(experiment: Experiment, supervisor: Supervisor, poll: float) -> str:
    """Wait for a separately launched stage; a vanished running process has failed."""
    path = experiment.output_dir / "run-status.json"
    while not supervisor.cancelled:
        record = json.loads(path.read_text())
        if not _alive(record["pid"]):
            return "failed" if record["status"] == "running" else str(record["status"])
        time.sleep(poll)
    return "cancelled"


def execute(config: Workflow) -> None:
    """Start PPO only after successful BC and authenticated best-weight selection."""
    supervisor = Supervisor()
    record: dict[str, Any] = {"pid": os.getpid(), "started_at": time.time()}

    def status(stage: str, result: str, **extra: Any) -> None:
        record.update(stage=stage, status=result, updated_at=time.time(), **extra)
        write_json(config.output_dir / "status.json", record)

    def train(stage: str, experiment: Experiment) -> bool:
        path = config.output_dir / f"{stage}-config.json"
        write_json(path, experiment.model_dump(mode="json"))
        status(stage, "running", run=str(experiment.output_dir))
        with (experiment.output_dir / "train.log").open("a") as log:
            code = supervisor.run(
                [
                    sys.executable, "-m", "kagg_revue.learning.workflows.runner",
                    "--train", str(path),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        if code is None:
            status(stage, "cancelled")
            return False
        if code:
            raise RuntimeError(f"{stage} exited with code {code}; inspect its train.log")
        outcome = json.loads((experiment.output_dir / "run-status.json").read_text())
        if outcome["status"] != "complete":
            status(stage, "stopped", training_status=outcome["status"])
            return False
        return True

    try:
        if config.attached_bc:
            status("bc", "attached", run=str(config.bc.output_dir))
            outcome = attend(config.bc, supervisor, ATTACH_POLL_SECONDS)
            if outcome != "complete":
                result = "cancelled" if outcome == "cancelled" else "stopped"
                status("bc", result, training_status=outcome)
                return
        elif not train("bc", config.bc):
            return
        status("selection", "running")
        rl, selection = select(config)
        write_json(config.output_dir / "selection.json", selection)
        if supervisor.cancelled:
            status("selection", "cancelled")
            return
        status("rl-bootstrap", "running")
        evidence = prepare(rl, config.historical_archive)
        write_json(config.output_dir / "opponent-bootstrap.json", evidence)
        if supervisor.cancelled:
            status("rl-bootstrap", "cancelled")
            return
        if train("rl", rl):
            status("rl", "complete")
    except BaseException as error:
        status(record.get("stage", "preparing"), "failed", error=str(error))
        raise
    finally:
        supervisor.close()


def main() -> None:
    """Read a previously resolved plan, or launch one prepared stage with resume."""
    if len(sys.argv) == 3 and sys.argv[1] == "--train":
        from kagg_revue.learning.train import run

        config = Experiment.model_validate_json(Path(sys.argv[2]).read_text())
        run(config.model_copy(update={"resume": True}))
    elif len(sys.argv) == 2:
        execute(Workflow.model_validate_json(Path(sys.argv[1]).read_text()))
    else:
        raise ValueError("expected a workflow plan or --train stage-config.json")


if __name__ == "__main__":
    main()
