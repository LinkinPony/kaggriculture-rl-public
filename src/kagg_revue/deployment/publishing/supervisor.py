"""Restart the detached publisher on failure in containers without systemd."""

import fcntl
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.deployment.publishing.config import Publishing

LOGGER = logging.getLogger(__name__)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="deployment_publish",
)
def main(configuration: DictConfig) -> None:
    """Run the same resolved configuration after each abnormal child exit."""
    config = Publishing.model_validate(
        OmegaConf.to_container(configuration.publishing, resolve=True)
    )
    root = config.output_dir
    root.mkdir(parents=True, exist_ok=True)
    with (root / "supervisor.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stop = threading.Event()
        for number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(number, lambda *_: stop.set())
        frozen = root / "supervisor-config.yaml"
        OmegaConf.save(configuration, frozen, resolve=True)
        while not stop.is_set():
            with (root / "publisher.log").open("a") as stream:
                child = subprocess.Popen(
                    [
                        sys.executable,
                        "-u",
                        "-m",
                        "kagg_revue.deployment.publishing.cli",
                        "--config-path",
                        str(root.resolve()),
                        "--config-name",
                        frozen.stem,
                    ],
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    env={
                        **os.environ,
                        "CUDA_VISIBLE_DEVICES": "",
                        "OMP_NUM_THREADS": "1",
                        "MKL_NUM_THREADS": "1",
                        "OPENBLAS_NUM_THREADS": "1",
                    },
                )
                write_json(
                    root / "supervisor.json",
                    {
                        "pid": os.getpid(),
                        "child_pid": child.pid,
                        "status": "running",
                        "started_at": time.time(),
                    },
                )
                while child.poll() is None:
                    if stop.wait(1):
                        child.terminate()
                        child.wait()  # Finish the current upload before releasing the lock.
                        break
            if child.returncode == 0:
                break
            LOGGER.error("Publisher exited %s; restarting in 15 seconds", child.returncode)
            stop.wait(15)
        write_json(
            root / "supervisor.json",
            {
                "pid": os.getpid(),
                "status": "stopped",
                "ended_at": time.time(),
            },
        )


if __name__ == "__main__":
    main()
