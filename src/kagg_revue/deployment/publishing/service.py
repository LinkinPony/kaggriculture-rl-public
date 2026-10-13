"""Run one export or upload at a time while continuing to capture scheduled inputs."""

import fcntl
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.deployment.publishing.config import Publishing
from kagg_revue.deployment.publishing.drive import upload
from kagg_revue.deployment.publishing.queue import enqueue, pending

LOGGER = logging.getLogger(__name__)


def process(config: Publishing, job: Path) -> None:
    """Build once, upload immutable files, then publish a verified delivery receipt."""
    try:
        if not (job / "ready.json").is_file():
            with (job / "worker.log").open("a") as stream:
                worker = subprocess.Popen(
                    [
                        "nice",
                        "-n",
                        "10",
                        sys.executable,
                        "-m",
                        "kagg_revue.deployment.publishing.worker",
                        str(job),
                    ],
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                    env={
                        **os.environ,
                        "CUDA_VISIBLE_DEVICES": "",
                        "OMP_NUM_THREADS": "1",
                        "MKL_NUM_THREADS": "1",
                        "OPENBLAS_NUM_THREADS": "1",
                    },
                )
                write_json(job / "worker.json", {"pid": worker.pid, "started_at": time.time()})
                try:
                    code = worker.wait(timeout=config.worker_timeout_seconds)
                except subprocess.TimeoutExpired:
                    os.killpg(worker.pid, signal.SIGKILL)
                    worker.wait()
                    raise
                if code:
                    raise RuntimeError(f"export exited {code}; inspect {job / 'worker.log'}")
        archive = json.loads((job / "ready.json").read_text())
        path = Path(archive["path"])
        if digest(path) != archive["sha256"]:
            raise ValueError("ready archive has changed")
        delivery = job / "delivery.json"
        remote_files = json.loads(delivery.read_text()) if delivery.exists() else {}

        def deliver(key: str, source: Path, name: str) -> dict[str, Any]:
            checksum = digest(source)
            if key in remote_files:
                if remote_files[key]["local_sha256"] != checksum:
                    raise ValueError("a previously delivered local artifact changed")
            else:
                remote_files[key] = {
                    **upload(config, source, f"{job.name}/{name}"),
                    "local_sha256": checksum,
                }
                write_json(delivery, remote_files)
            result: dict[str, Any] = remote_files[key]
            return result

        deliver("archive", path, "submission.tar.gz")
        for name in ("submission-info.txt", "submission-info.json"):
            deliver(name, job / name, name)
        receipt_path = job / "receipt.json"
        if not receipt_path.exists():
            metadata = json.loads((job / "submission-info.json").read_text())
            write_json(
                receipt_path,
                {
                    "description": metadata["description"] + f"; pkg {archive['sha256'][:8]}",
                    "archive": archive,
                    "remote_files": remote_files,
                    "smoke": json.loads((job / "smoke.json").read_text()),
                },
            )
        deliver("receipt", receipt_path, "receipt.json")
        write_json(job / "uploaded.json", {"time": time.time(), "remote_files": remote_files})
        (job / "failure.json").unlink(missing_ok=True)
        LOGGER.info("Uploaded and verified %s", job.name)
    except Exception as error:
        write_json(
            job / "failure.json",
            {
                "time": time.time(),
                "retry_at": time.time() + config.retry_seconds,
                "error": str(error),
            },
        )
        LOGGER.exception("Job failed; saved for retry: %s", job.name)


def run(config: Publishing) -> None:
    """Keep a durable, single-instance timer until explicitly stopped."""
    config.output_dir.mkdir(parents=True, exist_ok=True)
    with (config.output_dir / "publisher.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stop = threading.Event()
        for number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(number, lambda *_: stop.set())
        registry_path = config.output_dir / "registry.json"
        registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}
        write_json(config.output_dir / "configuration.json", config.model_dump(mode="json"))
        running: Future[None] | None = None
        with ThreadPoolExecutor(max_workers=1) as executor:
            while not stop.is_set():
                now = time.time()
                enqueue(config, registry, now)
                if running is not None and running.done():
                    running.result()
                    running = None
                jobs = pending(config, now)
                if running is None and jobs:
                    running = executor.submit(process, config, jobs[0])
                write_json(
                    config.output_dir / "status.json",
                    {
                        "pid": os.getpid(),
                        "status": "running",
                        "updated_at": now,
                        "pending_jobs": len(jobs),
                        "worker_active": running is not None,
                        "next_capture_at": (int(now // config.interval_seconds) + 1)
                        * config.interval_seconds,
                        "runs": registry.get("runs", {}),
                    },
                )
                if config.once:
                    if running is not None:
                        running.result()
                    for job in jobs[1:]:
                        process(config, job)
                    break
                stop.wait(config.poll_seconds)
        write_json(
            config.output_dir / "status.json",
            {
                "pid": os.getpid(),
                "status": "stopped",
                "updated_at": time.time(),
            },
        )
