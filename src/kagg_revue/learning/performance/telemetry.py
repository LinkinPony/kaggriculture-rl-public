"""Phase-tagged device telemetry for isolated GPU throughput experiments."""

import json
import statistics
import subprocess
import threading
import time
from collections import defaultdict
from pathlib import Path
from types import TracebackType
from typing import Any

from kagg_revue.artifacts.io import write_json


class GpuTelemetry:
    """Sample device activity and power; device busy time is not SM occupancy."""

    def __init__(self, output: Path, physical_gpu: int) -> None:
        """Bind output to one physical device, independently of CUDA remapping."""
        self.output = output
        self.physical_gpu = physical_gpu
        self.phase = (-1, "startup", time.time())
        self.rows: list[dict[str, Any]] = []
        self.process: subprocess.Popen[str] | None = None
        self.thread: threading.Thread | None = None

    def mark(self, repeat: int, phase: str) -> None:
        """Record wall-clock phase boundaries alongside the benchmark output."""
        self.phase = (repeat, phase, time.time())
        print(json.dumps({"repeat": repeat, "phase": phase, "time": self.phase[2]}), flush=True)

    def __enter__(self) -> "GpuTelemetry":
        """Start a bounded-rate monitor without synchronizing the CUDA stream."""
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.process = subprocess.Popen(
            [
                "nvidia-smi",
                "-i",
                str(self.physical_gpu),
                "--query-gpu=utilization.gpu,utilization.memory,power.draw,power.limit,"
                "clocks.sm,memory.used",
                "--format=csv,noheader,nounits",
                "-lms",
                "500",
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()
        return self

    def _read(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        fields = (
            "device_busy_percent",
            "memory_busy_percent",
            "power_watts",
            "power_limit_watts",
            "sm_clock_mhz",
            "memory_mib",
        )
        with self.output.with_suffix(".telemetry.jsonl").open("w") as stream:
            for line in self.process.stdout:
                try:
                    values = [float(value.strip()) for value in line.split(",")]
                except ValueError:
                    continue
                if len(values) != len(fields):
                    continue
                repeat, phase, started = self.phase
                now = time.time()
                row = {
                    "time": now,
                    "repeat": repeat,
                    "phase": phase,
                    "phase_seconds": now - started,
                    **dict(zip(fields, values, strict=True)),
                }
                self.rows.append(row)
                stream.write(json.dumps(row) + "\n")
                stream.flush()

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop the owned monitor and preserve summaries even after a failed experiment."""
        assert self.process is not None and self.thread is not None
        self.process.terminate()
        self.process.wait(timeout=5)
        self.thread.join(timeout=5)
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in self.rows:
            if row["phase_seconds"] >= 1:
                grouped[f"repeat{row['repeat']}/{row['phase']}"].append(row)
        summary = {}
        for name, rows in grouped.items():
            summary[name] = {
                "samples": len(rows),
                **{
                    field: {
                        "mean": statistics.mean(row[field] for row in rows),
                        "min": min(row[field] for row in rows),
                        "max": max(row[field] for row in rows),
                    }
                    for field in (
                        "device_busy_percent",
                        "memory_busy_percent",
                        "power_watts",
                        "power_limit_watts",
                        "sm_clock_mhz",
                        "memory_mib",
                    )
                },
            }
        write_json(
            self.output.with_suffix(".telemetry.json"),
            {
                "physical_gpu": self.physical_gpu,
                "scope": "NVML device/memory busy time and board power, not achieved SM occupancy "
                "or a fraction of peak memory bandwidth. First second of each phase excluded.",
                "phases": summary,
            },
        )
