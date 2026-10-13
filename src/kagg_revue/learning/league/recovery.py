"""Resume active specialists from their authenticated archived implementation."""

import fcntl
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import FrameType

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery

BOOTSTRAP = """
import json
import sys
from pathlib import Path
from kagg_revue.learning.league.config import League
from kagg_revue.learning.league.launch import run
state = json.loads(Path(sys.argv[1]).read_text())
run(League.model_validate(state['protocol']).model_copy(update={
    'resume': True, 'stop_after_update': json.loads(sys.argv[2])}))
"""


class LeagueRecovery(Recovery):
    """Optionally stop at a complete update without changing the experiment budget."""

    stop_after_update: int | None = Field(default=None, ge=0)


def recover(config: LeagueRecovery) -> None:
    """Reconstruct frozen source without replacing the current worktree."""
    root = Path.cwd().resolve()
    directory = root / config.run
    with (directory / "recovery.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = orjson.loads((directory / "league.json").read_bytes())
        status = orjson.loads((directory / "run-status.json").read_bytes())
        if state["schema"] != "three-specialist-league-v1" or state["protocol"]["experiment"][
            "output_dir"
        ] != str(config.run):
            raise ValueError("recovery requires the registered three-member league")
        try:
            os.kill(status["pid"], 0)
        except ProcessLookupError:
            pass
        else:
            raise RuntimeError("the recorded training process is still live")
        if status["status"] == "complete":
            raise ValueError("the declared league budget already completed")
        temporary = root / "tmp"
        temporary.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="league-recovery-", dir=temporary) as name:
            isolated = Path(name)
            first = next(iter(state["members"]))
            member = orjson.loads((directory / first / "state.json").read_bytes())
            if member["source"] != state["source"]:
                raise ValueError("member source does not match the joint league")
            identity = materialize(directory / first, member, isolated)
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
                    [
                        sys.executable,
                        "-c",
                        BOOTSTRAP,
                        str(directory / "league.json"),
                        orjson.dumps(config.stop_after_update).decode(),
                    ],
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
                print(orjson.dumps(record).decode(), flush=True)
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
                    {**record, "status": "exited", "exit_code": code, "ended_at": time.time()},
                )
                if code:
                    raise RuntimeError(f"archived league continuation failed: {log_path}")


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="learning_league_resume"
)
def main(configuration: DictConfig) -> None:
    """Resume one league, preserving all model, dataset and optimizer identities."""
    recover(
        LeagueRecovery.model_validate(OmegaConf.to_container(configuration.recovery, resolve=True))
    )


if __name__ == "__main__":
    main()
