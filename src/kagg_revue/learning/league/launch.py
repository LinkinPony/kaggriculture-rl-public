"""Supervise dual-GPU specialists with one joint writer and graceful boundaries."""

import fcntl
import os
import signal
import time
import traceback
from datetime import timedelta
from pathlib import Path
from typing import Any

import orjson
import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.distributed import bind_cpus
from kagg_revue.learning.league import storage
from kagg_revue.learning.league.config import League
from kagg_revue.learning.train import StopRequest


def _worker(rank: int, resolved: dict[str, Any], rendezvous: str, event: Any) -> None:
    config = League.model_validate(resolved)
    execution = config.experiment.execution
    devices = execution.devices if execution else (config.experiment.device,)
    device = torch.device(devices[rank])
    cpus = bind_cpus(rank, len(devices))
    torch.cuda.set_device(device)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    # Preserve the qualified attention backend. Decoder normalization has its
    # own atomic boundary; attention flags alone did not repair its NaNs.
    torch.backends.cuda.enable_cudnn_sdp(config.cudnn_attention)
    torch.set_num_threads(
        execution.cpu_threads_per_rank if execution else config.experiment.cpu_threads
    )
    torch.use_deterministic_algorithms(config.experiment.deterministic)
    dist.init_process_group(
        "nccl",
        init_method=rendezvous,
        rank=rank,
        world_size=len(devices),
        device_id=device,
        timeout=timedelta(minutes=30),
    )

    class WorkerStop(StopRequest):
        @property
        def requested(self) -> bool:
            return bool(event.is_set())

        @requested.setter
        def requested(self, value: bool) -> None:
            if value:
                event.set()

    stop = WorkerStop()
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, stop.handle)
    root = config.experiment.output_dir
    write_json(
        root / f"worker-{rank}.json",
        {"rank": rank, "pid": os.getpid(), "device": str(device), "cpu_affinity": cpus},
    )
    try:
        from kagg_revue.learning.league.training import train

        train(config, orjson.loads((root / "league.json").read_bytes()), stop)
    except BaseException:
        traceback.print_exc()
        os._exit(1)
    else:
        dist.destroy_process_group()


def run(config: League) -> None:
    """Hold the only league writer lock and propagate stops to both GPU workers."""
    root = config.experiment.output_dir
    root.mkdir(parents=True, exist_ok=True)
    with (root / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = storage.restore(config) if config.resume else storage.create(config)
        stop = StopRequest()
        handlers = {
            number: signal.signal(number, stop.handle) for number in (signal.SIGINT, signal.SIGTERM)
        }
        temporary = Path("tmp/league-distributed")
        temporary.mkdir(parents=True, exist_ok=True)
        rendezvous = (temporary / f"nccl-{os.getpid()}-{time.time_ns()}").resolve()
        os.environ.setdefault("TORCHINDUCTOR_COMPILE_THREADS", "8")
        context = mp.get_context("spawn")
        event = context.Event()
        devices = (
            config.experiment.execution.devices
            if config.experiment.execution
            else (config.experiment.device,)
        )
        write_json(
            root / "run-status.json",
            {
                "status": "running",
                "phase": state["phase"],
                "pid": os.getpid(),
                "devices": devices,
                "run_id": state["run_id"],
                "completed_update": state["completed_update"],
                "started_at": time.time(),
            },
        )
        status = "failed"
        try:
            processes = mp.spawn(  # type: ignore[attr-defined, no-untyped-call]
                _worker,
                args=(config.model_dump(mode="json"), rendezvous.as_uri(), event),
                nprocs=len(devices),
                join=False,
            )
            while not processes.join(timeout=1):
                if stop.requested:
                    event.set()
            status = "stopped" if event.is_set() else "complete"
        finally:
            state = orjson.loads((root / "league.json").read_bytes())
            write_json(
                root / "run-status.json",
                {
                    "status": status,
                    "phase": state["phase"],
                    "pid": os.getpid(),
                    "completed_update": state["completed_update"],
                    "run_id": state["run_id"],
                    "ended_at": time.time(),
                },
            )
            rendezvous.unlink(missing_ok=True)
            for number, handler in handlers.items():
                signal.signal(number, handler)
