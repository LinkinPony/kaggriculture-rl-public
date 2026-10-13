"""Supervised multiprocessing with graceful, synchronized update-boundary stops."""

import faulthandler
import json
import os
import signal
import time
import traceback
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import torch
import torch.distributed as dist
import torch.multiprocessing as mp

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import bind_cpus

if TYPE_CHECKING:
    from kagg_revue.learning.train import StopRequest


def _rank(
    rank: int, resolved: dict[str, Any], rendezvous: str, event: Any, pretraining: bool
) -> None:
    from kagg_revue.learning.train import StopRequest, _train

    config = Experiment.model_validate(resolved)
    assert config.execution is not None
    execution = config.execution
    device = torch.device(execution.devices[rank])
    cpus = bind_cpus(rank, len(execution.devices))
    if execution.workers_per_rank > len(cpus):
        raise ValueError("native workers per rank exceed the permitted CPU partition")
    torch.set_num_threads(execution.cpu_threads_per_rank)
    torch.cuda.set_device(device)
    torch.use_deterministic_algorithms(config.deterministic)
    dist.init_process_group(
        "nccl",
        init_method=rendezvous,
        rank=rank,
        world_size=len(execution.devices),
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
    faulthandler.register(signal.SIGUSR1, all_threads=True)
    for number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(number, stop.handle)
    try:
        state = json.loads((config.output_dir / "state.json").read_text())
        write_json(
            config.output_dir / f"worker-{rank}.json",
            {
                "pid": os.getpid(),
                "rank": rank,
                "device": str(device),
                "cpu_affinity": cpus,
                "native_workers": execution.workers_per_rank,
                "cpu_threads": execution.cpu_threads_per_rank,
                "started_at": time.time(),
            },
        )
        if pretraining:
            from kagg_revue.learning.pretraining.train import initialize

            initialize(config, runtime_settings(config), state, lambda: stop.requested)
        else:
            _train(config, runtime_settings(config), state, stop)
    except BaseException:
        # NCCL shutdown can wait forever when another rank is in a collective.
        # Exit immediately so the parent supervisor can terminate the other ranks.
        traceback.print_exc()
        os._exit(1)
    else:
        dist.destroy_process_group()


def parallel(config: Experiment, stop: "StopRequest", *, pretraining: bool = False) -> None:
    """Forward parent stops through an event and wait for every final checkpoint write."""
    assert config.execution is not None
    temporary = Path("tmp/learning-distributed")
    temporary.mkdir(parents=True, exist_ok=True)
    rendezvous = (temporary / f"nccl-{os.getpid()}-{time.time_ns()}").resolve()
    context = mp.get_context("spawn")
    os.environ.setdefault("TORCHINDUCTOR_COMPILE_THREADS", "8")
    # Native observation and opponent teams pause while CUDA runs each turn.
    # Busy waiting here otherwise competes with the next CPU phase.
    os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")
    event = context.Event()
    try:
        workers = mp.spawn(  # type: ignore[attr-defined, no-untyped-call]
            _rank,
            args=(config.model_dump(mode="json"), rendezvous.as_uri(), event, pretraining),
            nprocs=len(config.execution.devices),
            join=False,
        )
        while not workers.join(timeout=1):
            if stop.requested:
                event.set()
        stop.requested = stop.requested or event.is_set()
    finally:
        rendezvous.unlink(missing_ok=True)
