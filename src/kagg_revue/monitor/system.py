"""Host, accelerator, and repository training-process telemetry."""

from __future__ import annotations

import csv
import io
import json
import subprocess
import threading
import time
from contextlib import suppress
from pathlib import Path
from typing import Any, cast

import psutil  # type: ignore[import-untyped]

_GIB = 1024**3
_MIB = 1024**2
_IMPLICIT_RUN_FAMILIES = (
    ("kagg_revue.rl.tasks.cli", "unit-task-rl"),
    ("kagg-revue-task-rl", "unit-task-rl"),
    ("kagg_revue.rl.programs.cli", "conditional-program-rl"),
    ("kagg-revue-program-rl", "conditional-program-rl"),
    ("kagg_revue.rl.intents.cli", "intent-ledger-rl"),
    ("kagg-revue-intent-rl", "intent-ledger-rl"),
    ("kagg_revue.bc.programs.cli", "conditional-program-bc"),
    ("kagg-revue-program-bc", "conditional-program-bc"),
)


def _number(value: str) -> float | None:
    cleaned = value.strip()
    if not cleaned or cleaned.upper() in {"N/A", "[NOT SUPPORTED]"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _nvidia_rows(query: str) -> list[list[str]]:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                f"--query-{query}",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=2.0,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []
    return [row for row in csv.reader(io.StringIO(completed.stdout)) if row]


def _gpu_snapshot() -> tuple[list[dict[str, object]], dict[int, int]]:
    gpu_rows = _nvidia_rows(
        "gpu=index,name,uuid,utilization.gpu,memory.used,memory.total,"
        "temperature.gpu,power.draw,power.limit"
    )
    gpus: list[dict[str, object]] = []
    for row in gpu_rows:
        if len(row) != 9:
            continue
        used = _number(row[4])
        total = _number(row[5])
        gpus.append(
            {
                "index": int(row[0].strip()),
                "name": row[1].strip(),
                "uuid": row[2].strip(),
                "utilization_percent": _number(row[3]),
                "memory_used_bytes": None if used is None else int(used * _MIB),
                "memory_total_bytes": None if total is None else int(total * _MIB),
                "temperature_celsius": _number(row[6]),
                "power_watts": _number(row[7]),
                "power_limit_watts": _number(row[8]),
            }
        )

    process_memory: dict[int, int] = {}
    for row in _nvidia_rows("compute-apps=pid,used_gpu_memory"):
        if len(row) != 2:
            continue
        memory = _number(row[1])
        try:
            pid = int(row[0].strip())
        except ValueError:
            continue
        if memory is not None:
            process_memory[pid] = process_memory.get(pid, 0) + int(memory * _MIB)
    return gpus, process_memory


class SystemSampler:
    """Sample only telemetry needed to operate repository training runs."""

    def __init__(self, repository_root: Path, outputs_dir: Path) -> None:
        """Bind process matching to one repository output root."""
        self._repository_root = repository_root.resolve()
        self._outputs_dir = outputs_dir.resolve()
        self._lock = threading.RLock()
        self._cached_at = 0.0
        self._cached: dict[str, object] | None = None
        psutil.cpu_percent(interval=None)

    def snapshot(self) -> dict[str, object]:
        """Return a briefly cached system and relevant-process snapshot."""
        with self._lock:
            now = time.monotonic()
            if self._cached is not None and now - self._cached_at < 1.0:
                return self._cached
            gpus, gpu_process_memory = _gpu_snapshot()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self._outputs_dir))
            load = psutil.getloadavg()
            processes = self._training_processes(gpu_process_memory)
            snapshot: dict[str, object] = {
                "cpu": {
                    "utilization_percent": psutil.cpu_percent(interval=None),
                    "logical_cores": psutil.cpu_count(logical=True),
                    "load_1m": load[0],
                    "load_5m": load[1],
                    "load_15m": load[2],
                },
                "memory": {
                    "used_bytes": memory.used,
                    "available_bytes": memory.available,
                    "total_bytes": memory.total,
                    "utilization_percent": memory.percent,
                },
                "disk": {
                    "used_bytes": disk.used,
                    "free_bytes": disk.free,
                    "total_bytes": disk.total,
                    "utilization_percent": disk.percent,
                },
                "gpus": gpus,
                "training_processes": processes,
            }
            self._cached = snapshot
            self._cached_at = now
            return snapshot

    def _training_processes(self, gpu_memory: dict[int, int]) -> list[dict[str, object]]:
        matched: dict[int, tuple[psutil.Process, dict[str, Any], str, float]] = {}
        attributes = ["pid", "cmdline", "cpu_percent", "memory_info", "create_time", "status"]
        for process in psutil.process_iter(attributes):
            try:
                info = cast(dict[str, Any], process.info)
                cmdline_value = info.get("cmdline")
                if not isinstance(cmdline_value, list):
                    continue
                cmdline = [str(part) for part in cmdline_value]
                created_at = float(info.get("create_time") or time.time())
                run_id = self._run_id(cmdline, created_at, process.pid)
                if run_id is None:
                    continue
                matched[process.pid] = (process, info, run_id, created_at)
            except (psutil.Error, KeyError, TypeError, ValueError):
                continue

        processes: list[dict[str, object]] = []
        for process, info, run_id, created_at in matched.values():
            try:
                ancestor = process.parent()
                nested = False
                while ancestor is not None:
                    parent = matched.get(ancestor.pid)
                    if parent is not None and parent[2] == run_id:
                        nested = True
                        break
                    ancestor = ancestor.parent()
                if nested:
                    continue
                members = [process]
                with suppress(psutil.Error):
                    members.extend(process.children(recursive=True))
                rss = 0
                cpu_percent = 0.0
                member_pids: set[int] = set()
                for member in members:
                    try:
                        member_pids.add(member.pid)
                        rss += int(member.memory_info().rss)
                        cpu_percent += float(member.cpu_percent(interval=None))
                    except psutil.Error:
                        continue
                pid = int(info["pid"])
                processes.append(
                    {
                        "run_id": run_id,
                        "pid": pid,
                        "status": str(info.get("status", "unknown")),
                        "cpu_percent": cpu_percent,
                        "memory_bytes": rss,
                        "gpu_memory_bytes": sum(
                            gpu_memory.get(member_pid, 0) for member_pid in member_pids
                        ),
                        "process_count": len(member_pids),
                        "elapsed_seconds": max(0.0, time.time() - created_at),
                    }
                )
            except (psutil.Error, KeyError, TypeError, ValueError):
                continue
        return sorted(processes, key=lambda item: cast(str, item["run_id"]))

    def _run_id(
        self, cmdline: list[str], created_at: float | None = None, pid: int | None = None
    ) -> str | None:
        joined = " ".join(cmdline)
        if "kagg_revue" not in joined and "kagg-revue" not in joined:
            return None
        prefixes = (
            "rl.output_dir=",
            "experiment.output_dir=",
            "unit_task_rl.output_dir=",
            "conditional_program_rl.output_dir=",
            "intent_ledger_rl.output_dir=",
            "conditional_program_bc.output_dir=",
            "structured_plan_rl.output_dir=",
            "capability_rl.output_dir=",
            "route_ppo.output_dir=",
            "production.output_dir=",
            "output_dir=",
        )
        for argument in cmdline:
            for prefix in prefixes:
                if not argument.startswith(prefix):
                    continue
                raw = Path(argument.removeprefix(prefix))
                candidate = (
                    raw.resolve() if raw.is_absolute() else (self._repository_root / raw).resolve()
                )
                if not candidate.is_relative_to(self._outputs_dir):
                    continue
                relative = candidate.relative_to(self._outputs_dir)
                if len(relative.parts) == 2:
                    return relative.as_posix()
        if any(
            entry in joined
            for entry in (
                "kagg_revue.production.cli",
                "kagg_revue.production.migration.train",
                "kagg_revue.production.expert.evolution",
                "kagg_revue.production.expert.apprentice",
                "kagg_revue.production.branching.train",
                "kagg-revue-production",
            )
        ):
            family_dir = self._outputs_dir / "production-policy"
            if family_dir.is_dir():
                for run_dir in family_dir.iterdir():
                    status_path = run_dir / "run-status.json"
                    if not status_path.is_file() or status_path.stat().st_size > 4096:
                        continue
                    with suppress(OSError, ValueError, TypeError):
                        status = json.loads(status_path.read_text())
                        if status.get("pid") == pid and status.get("status") == "running":
                            return run_dir.relative_to(self._outputs_dir).as_posix()
        for signature, family in _IMPLICIT_RUN_FAMILIES:
            if signature not in joined:
                continue
            family_dir = self._outputs_dir / family
            if not family_dir.is_dir():
                return None
            candidates = [
                run_dir
                for run_dir in family_dir.iterdir()
                if run_dir.is_dir()
                and (run_dir / ".ddp-rendezvous").is_file()
                and (
                    created_at is None
                    or (run_dir / ".ddp-rendezvous").stat().st_mtime >= created_at - 30.0
                )
            ]
            if candidates:
                run_dir = max(
                    candidates,
                    key=lambda value: (value / ".ddp-rendezvous").stat().st_mtime,
                )
                return run_dir.relative_to(self._outputs_dir).as_posix()
        return None


__all__ = ["SystemSampler"]
