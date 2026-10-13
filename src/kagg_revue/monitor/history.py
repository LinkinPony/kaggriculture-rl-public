"""Compact, lossless scalar histories for the currently inspected runs."""

from __future__ import annotations

import json
import math
import threading
from array import array
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from kagg_revue.monitor.metrics import _step_and_metrics
from kagg_revue.monitor.opponents.records import OpponentIndex


@dataclass
class ScalarHistory:
    """Packed numeric columns, without a Python object per observation."""

    steps: array[int] = field(default_factory=lambda: array("q"))
    values: array[float] = field(default_factory=lambda: array("d"))
    weights: array[float] = field(default_factory=lambda: array("d"))
    breaks: array[int] = field(default_factory=lambda: array("q"))
    interrupted: bool = False


def sample_weight(tag: str, metrics: dict[str, float]) -> float:
    """Weight rates and cash by actual games; other scalars by observations."""
    prefix, _, field_name = tag.rpartition("/")
    if tag.startswith("rl/league/members/") and field_name in {"win_rate", "tie_rate", "loss_rate"}:
        return metrics.get(f"{prefix}/mutual_games", 1.0)
    if field_name in {
        "win_rate",
        "tie_rate",
        "loss_rate",
        "mean_terminal_cash",
        "mean_cash_difference",
        "mean_cash_left",
        "mean_cash_right",
        "mean_absolute_cash_difference",
    }:
        return metrics.get(f"{prefix}/games", metrics.get(f"{prefix}/physical_games", 1.0))
    return 1.0


def event_affects_metric(kind: str, tag: str) -> bool:
    """Reset performance on device changes, and all windows on population changes."""
    return kind == "population" or any(
        part in tag for part in ("/system/", "_seconds", "_per_second", "_bytes")
    )


def unsampled_prefixes(row: dict[str, Any]) -> tuple[str, ...]:
    """Identify opponents explicitly assigned no games, without filling their values."""
    panels: dict[str, Any] = {}
    prefixes = []
    pfsp = row.get("pfsp")
    if isinstance(pfsp, dict) and pfsp.get("enabled"):
        scripts = pfsp.get("scripts")
        if isinstance(scripts, dict):
            panels.update(scripts)
        selected = pfsp.get("selected")
        if pfsp.get("unified") and isinstance(selected, dict) and selected.get("kind") == "script":
            panels["historical_self_play"] = {"games": 0}
    populations = row.get("populations")
    if isinstance(populations, dict):
        panels.update(populations)
    for name, panel in panels.items():
        if isinstance(panel, dict) and panel.get("games") == 0:
            label = "history" if name == "historical_self_play" else name
            prefixes.append(f"rl/rollout/opponents/{label}/")
            if label == "history":
                prefixes.append("rl/run/history_score")
    return tuple(prefixes)


def row_signatures(row: dict[str, Any]) -> dict[str, str]:
    """Extract comparable population and execution descriptions from actual rows."""
    signatures = {}
    populations = row.get("populations")
    if isinstance(row.get("pairs"), dict):
        populations = row["pairs"]
    if isinstance(populations, dict):
        signatures["population"] = " · ".join(
            f"{name}: {panel['games']} 场"
            for name, panel in sorted(populations.items())
            if isinstance(panel, dict)
            and isinstance(panel.get("games"), int | float)
            and panel["games"] > 0
        )
        if row.get("pfsp", {}).get("enabled"):
            scripts = sorted(set(populations) - {"self_play", "historical_self_play"})
            pool = row["pfsp"].get("scripts")
            signatures["population"] = " · ".join(
                [
                    f"{name}: {populations.get(name, {}).get('games', 0)} 场"
                    for name in ("self_play", "historical_self_play")
                ]
                + [
                    f"PFSP scripts ({', '.join(scripts)}): "
                    f"{sum(populations[name]['games'] for name in scripts)} 场"
                ]
            )
            if row["pfsp"].get("unified"):
                signatures["population"] = (
                    f"Self-play: {100 * row['pfsp']['selfplay_fraction']:g}% · "
                    f"Unified PFSP: {100 * row['pfsp']['pool_fraction']:g}%"
                )
            elif row["pfsp"].get("separate_scripts"):
                signatures["population"] = (
                    f"Self-play: {100 * row['pfsp']['selfplay_fraction']:g}% · "
                    f"Adaptive scripts: {100 * row['pfsp']['script_fraction']:g}% · "
                    f"History PFSP: {100 * row['pfsp']['history_fraction']:g}%"
                )
            if isinstance(pool, dict):
                signatures["population"] += f" · Scripts: {', '.join(sorted(pool))}"
    workers = row.get("workers")
    if isinstance(workers, list):
        devices = sorted(
            {
                str(w["device"])
                for w in workers
                if isinstance(w, dict) and isinstance(w.get("device"), str)
            }
        )
        if devices:
            signatures["execution"] = ", ".join(devices)
    return signatures


@dataclass
class RunHistory:
    """One incrementally read file and its reproducible change boundaries."""

    inode: int
    offset: int = 0
    modified_ns: int = 0
    last_step: int | None = None
    first_step: int | None = None
    series: dict[str, ScalarHistory] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    signatures: dict[str, str] = field(default_factory=dict)
    opponents: OpponentIndex = field(default_factory=OpponentIndex)

    def append(self, row: dict[str, Any]) -> None:
        """Normalize one completed record; never interpolate missing measurements."""
        step, metrics = _step_and_metrics(row)
        if step is None or (self.last_step is not None and step <= self.last_step):
            return
        self.opponents.append(row, step)
        signatures = row_signatures(row)
        for kind, description in signatures.items():
            previous = self.signatures.get(kind)
            if previous is not None and previous != description:
                self.events.append(
                    {
                        "step": step,
                        "kind": kind,
                        "title": "对手组成变化" if kind == "population" else "执行设备变化",
                        "before": previous,
                        "after": description,
                        "source": "metrics.jsonl",
                    }
                )
        self.signatures.update(signatures)
        changes = [event["kind"] for event in self.events[-2:] if event["step"] == step]
        unsampled = unsampled_prefixes(row)
        samples = {}
        for tag, value in metrics.items():
            weight = sample_weight(tag, metrics)
            if math.isfinite(value) and math.isfinite(weight) and weight > 0:
                samples[tag] = (value, weight)
        # Remember interruptions even when a sparse metric is absent on the
        # boundary row. Scheduled zero-game rounds preserve its existing segment.
        for tag, column in self.series.items():
            column.interrupted |= any(event_affects_metric(kind, tag) for kind in changes) or (
                tag not in samples and not tag.startswith(unsampled)
            )
        for tag, (value, weight) in samples.items():
            column = self.series.setdefault(tag, ScalarHistory())
            if column.steps and column.interrupted:
                column.breaks.append(step)
            column.steps.append(step)
            column.values.append(value)
            column.weights.append(weight)
            column.interrupted = False
        self.last_step = step
        if self.first_step is None:
            self.first_step = step


class HistoryReader:
    """Keep exact columns for a small LRU of inspected runs, never all run summaries."""

    def __init__(self, cache_runs: int = 2) -> None:
        """Set the number of active detail histories retained in memory."""
        self._cache_runs = cache_runs
        self._runs: OrderedDict[Path, RunHistory] = OrderedDict()
        self.lock = threading.RLock()

    def read(self, path: Path) -> RunHistory:
        """Tail complete JSONL lines, rebuilding after replacement or truncation."""
        with self.lock:
            if not path.is_file():
                self._runs.pop(path, None)
                return RunHistory(inode=0)
            stat = path.stat()
            history = self._runs.get(path)
            if (
                history is None
                or history.inode != stat.st_ino
                or stat.st_size < history.offset
                or (stat.st_size == history.offset and stat.st_mtime_ns != history.modified_ns)
            ):
                history = RunHistory(inode=stat.st_ino)
                self._runs[path] = history
            self._runs.move_to_end(path)
            while len(self._runs) > self._cache_runs:
                self._runs.popitem(last=False)
            with path.open("rb") as stream:
                stream.seek(history.offset)
                while line := stream.readline():
                    if not line.endswith(b"\n"):
                        break
                    history.offset = stream.tell()
                    try:
                        row = json.loads(line)
                    except (ValueError, UnicodeDecodeError):
                        continue
                    if isinstance(row, dict):
                        history.append(row)
            history.modified_ns = stat.st_mtime_ns
            return history
