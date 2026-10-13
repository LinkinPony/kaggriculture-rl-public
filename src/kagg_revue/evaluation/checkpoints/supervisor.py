"""Watch training health and stop only evaluator process groups on resource pressure."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import write_json
from kagg_revue.configuration import FrozenSettings


class Supervision(FrozenSettings):
    """Explicit evaluator limits and immutable training-process identity."""

    manifest: Path
    schedule: Path
    output: Path
    devices: tuple[str, ...] = ("cuda:1",)
    batch_games: int = Field(default=32, gt=0, multiple_of=2)
    memory_fraction: float = Field(default=0.06, gt=0, le=0.08)
    minimum_free_mib: int = Field(default=12288, ge=8192)
    maximum_seconds: int = Field(default=28800, gt=0, le=28800)
    stale_training_seconds: int = Field(default=900, gt=0)


def health(run: Path, pid: int) -> dict[str, Any]:
    """Read live memory and training heartbeat without importing or modifying Torch."""
    os.kill(pid, 0)
    progress = json.loads((run / "learning-progress.json").read_text())
    state = json.loads((run / "run-status.json").read_text())
    if state["status"] != "running" or state["pid"] != pid:
        raise RuntimeError("training process identity or status changed")
    raw = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=index,memory.free,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        text=True,
        timeout=10,
    )
    gpu = [list(map(int, line.split(","))) for line in raw.strip().splitlines()]
    return {
        "time": time.time(),
        "training_pid": pid,
        "training_update": progress["update"],
        "training_heartbeat_age": time.time() - progress["updated_at"],
        "gpus": gpu,
    }


def run(options: Supervision) -> None:
    """Launch isolated workers and record health until completion or a bounded stop."""
    manifest = json.loads(options.manifest.read_text())
    training_run = Path(manifest["run"])
    training_pid = json.loads((training_run / "run-status.json").read_text())["pid"]
    options.output.mkdir(parents=True, exist_ok=True)
    write_json(options.output / "supervision.json", options.model_dump(mode="json"))
    initial = health(training_run, training_pid)
    if min(row[1] for row in initial["gpus"]) < 24576:
        raise RuntimeError("insufficient free memory for a bounded evaluator")
    processes: list[subprocess.Popen[bytes]] = []
    streams = []
    started = time.monotonic()
    reason = "complete"
    try:
        for shard, device in enumerate(options.devices):
            command = [
                sys.executable,
                "-m",
                "kagg_revue.evaluation.checkpoints.worker",
                f"comparison.manifest={options.manifest}",
                f"comparison.schedule={options.schedule}",
                f"comparison.output={options.output}",
                f"comparison.device={device}",
                f"comparison.batch_games={options.batch_games}",
                f"comparison.memory_fraction={options.memory_fraction}",
                f"comparison.shard={shard}",
                f"comparison.shards={len(options.devices)}",
            ]
            stream = (options.output / f"worker-{shard}.log").open("ab")
            streams.append(stream)
            processes.append(
                subprocess.Popen(
                    command, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True
                )
            )
        write_json(options.output / "processes.json", {"pids": [p.pid for p in processes]})
        with (options.output / "health.jsonl").open("a") as health_stream:
            while any(p.poll() is None for p in processes):
                current = health(training_run, training_pid)
                health_stream.write(json.dumps(current) + "\n")
                health_stream.flush()
                if min(row[1] for row in current["gpus"]) < options.minimum_free_mib:
                    raise RuntimeError("GPU reserve crossed; stopping evaluators only")
                if current["training_heartbeat_age"] > options.stale_training_seconds:
                    raise RuntimeError("training heartbeat stale; stopping evaluators only")
                if any(p.poll() not in (None, 0) for p in processes):
                    raise RuntimeError("evaluation worker failed; stopping the remaining shard")
                if time.monotonic() - started > options.maximum_seconds:
                    raise RuntimeError("evaluation reached its wall-clock limit")
                time.sleep(5)
        if any(p.returncode != 0 for p in processes):
            raise RuntimeError("an evaluation worker failed")
    except BaseException as error:
        reason = f"{type(error).__name__}: {error}"
        raise
    finally:
        for process in processes:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
        for process in processes:
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=15)
        for stream in streams:
            stream.close()
        write_json(
            options.output / "supervisor-result.json",
            {
                "reason": reason,
                "elapsed_seconds": time.monotonic() - started,
                "exit_codes": [p.returncode for p in processes],
                "training_pid": training_pid,
            },
        )


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="evaluation_checkpoints_guard"
)
def main(configuration: DictConfig) -> None:
    """Resolve resource limits using Hydra and leave training entirely untouched."""
    options = Supervision.model_validate(
        OmegaConf.to_container(configuration.supervision, resolve=True)
    )
    run(options)


if __name__ == "__main__":
    main()
