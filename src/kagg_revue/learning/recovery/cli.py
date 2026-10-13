"""Continue the original code and protocol in a disposable isolated source tree."""

import fcntl
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import FrameType

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import model_validator

from kagg_revue.artifacts.io import write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.pretraining.weights import valid_root
from kagg_revue.learning.recovery.archive import materialize

BOOTSTRAP = """
import json
import sys
from pathlib import Path
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.train import run
state = json.loads(Path(sys.argv[1]).read_text())
run(Experiment.model_validate(state['protocol']).model_copy(update={'resume': True}))
"""


class Recovery(FrozenSettings):
    """Name one existing own-run ledger; no model path or protocol override is accepted."""

    run: Path

    @model_validator(mode="after")
    def validate_run(self) -> "Recovery":
        """Restrict continuation to repository-owned fresh experiment directories."""
        if (
            self.run.is_absolute()
            or ".." in self.run.parts
            or self.run.parts[:2] != ("outputs", "learning")
        ):
            raise ValueError("recovery requires a registered outputs/learning run")
        return self


def recover(config: Recovery) -> None:
    """Hold a recovery lock, forward stop signals, and clean code only after child exit."""
    root = Path.cwd().resolve()
    directory = root / config.run
    with (directory / "recovery.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = json.loads((directory / "state.json").read_text())
        status = json.loads((directory / "run-status.json").read_text())
        if (
            not valid_root(state)
            or state["protocol"]["output_dir"] != str(config.run)
        ):
            raise ValueError("recovery requires an authenticated policy-root ledger")
        try:
            os.kill(status["pid"], 0)
        except ProcessLookupError:
            pass
        else:
            raise RuntimeError("the recorded training process is still live; do not restart it")
        if status["status"] == "complete":
            raise ValueError("the declared training budget and confirmation already completed")
        temporary = root / "tmp"
        temporary.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="learning-recovery-", dir=temporary) as name:
            isolated = Path(name)
            identity = materialize(directory, state, isolated)
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
            log_path = directory / f"recovery-{time.time_ns()}.log"
            with log_path.open("w") as log:
                child = subprocess.Popen(
                    [sys.executable, "-c", BOOTSTRAP, str(directory / "state.json")],
                    cwd=isolated,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )

                def forward(number: int, frame: FrameType | None) -> None:
                    if child.poll() is None:
                        child.send_signal(number)

                handlers = {
                    number: signal.signal(number, forward)
                    for number in (signal.SIGTERM, signal.SIGINT)
                }
                record = {
                    **identity,
                    "run_id": state["run_id"],
                    "pid": child.pid,
                    "parent_pid": os.getpid(),
                    "log": str(log_path.relative_to(root)),
                    "started_at": time.time(),
                    "status": "running",
                }
                write_json(directory / "recovery-status.json", record)
                print(json.dumps(record), flush=True)
                try:
                    code = child.wait()
                except BaseException:
                    if child.poll() is None:
                        child.terminate()
                        child.wait()
                    raise
                finally:
                    for number, handler in handlers.items():
                        signal.signal(number, handler)
                write_json(
                    directory / "recovery-status.json",
                    {
                        **record,
                        "status": "exited",
                        "exit_code": code,
                        "ended_at": time.time(),
                    },
                )
                if code:
                    raise RuntimeError(f"archived continuation failed; inspect {log_path}")


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_resume",
)
def main(configuration: DictConfig) -> None:
    """Reconstruct only the explicitly named experiment's original implementation."""
    recover(Recovery.model_validate(OmegaConf.to_container(configuration.recovery, resolve=True)))


if __name__ == "__main__":
    main()
