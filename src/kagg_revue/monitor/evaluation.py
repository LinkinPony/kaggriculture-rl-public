"""Cached history of independent matches, kept separate from rollout metrics."""

from __future__ import annotations

import json
import math
import re
import threading
from pathlib import Path
from typing import Any, cast
from zipfile import BadZipFile

import numpy as np
from numpy.typing import NDArray

from kagg_revue.monitor.league import pair_summaries


def summarize_matches(
    opponents: NDArray[Any], cash: NDArray[Any], outcomes: NDArray[Any]
) -> dict[str, Any]:
    """Aggregate candidate-relative outcomes without reversing the second seat."""
    count = len(outcomes)
    if (
        not count
        or opponents.shape != (count,)
        or outcomes.shape != (count,)
        or cash.shape != (count, 2)
        or not np.isfinite(cash).all()
        or not np.isin(outcomes, (-1, 0, 1)).all()
    ):
        raise ValueError("invalid independent match arrays")

    def summarize(mask: NDArray[np.bool_]) -> dict[str, int | float]:
        selected = outcomes[mask]
        return {
            "games": int(mask.sum()),
            "wins": int((selected > 0).sum()),
            "ties": int((selected == 0).sum()),
            "losses": int((selected < 0).sum()),
            "mean_terminal_cash": float(cash[mask, 0].mean()),
            "mean_cash_difference": float((cash[mask, 0] - cash[mask, 1]).mean()),
        }

    return {
        "overall": summarize(np.ones(count, dtype=np.bool_)),
        "opponents": {str(name): summarize(opponents == name) for name in np.unique(opponents)},
    }


def _summary(row: dict[str, Any]) -> dict[str, Any] | None:
    raw_counts = [row.get(name) for name in ("wins", "ties", "losses")]
    if not all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in raw_counts
    ):
        return None
    counts = cast(list[int], raw_counts)
    if not sum(counts):
        return None
    result: dict[str, int | float] = dict(zip(("wins", "ties", "losses"), counts, strict=True))
    result["games"] = sum(counts)
    for source, destination in (
        ("mean_cash", "mean_terminal_cash"),
        ("mean_terminal_cash", "mean_terminal_cash"),
        ("mean_cash_difference", "mean_cash_difference"),
    ):
        value = row.get(source)
        if isinstance(value, int | float) and math.isfinite(value):
            result[destination] = value
    return result


def _read_points(path: Path) -> list[dict[str, Any]]:
    league = re.fullmatch(r"update-(\d+)\.json", path.name)
    if path.parent.name == "evaluation" and league:
        report = json.loads(path.read_text())
        pairs = pair_summaries(report)
        return (
            [
                {
                    "step": int(league[1]),
                    "mode": f"league_{report.get('partition', 'selection')}",
                    "pairs": pairs,
                    "physical_games": report.get("physical_games"),
                }
            ]
            if pairs
            else []
        )
    learning = re.fullmatch(r"(selection|confirmation)-(\d+)\.json", path.name)
    if path.parent.name == "evaluation" and learning:
        report = json.loads(path.read_text())
        games = report["games"]
        learning_summary = summarize_matches(
            np.asarray([g["opponent"] for g in games]),
            np.asarray([[g["cash"], g["opponent_cash"]] for g in games]),
            np.asarray([g["outcome"] for g in games]),
        )
        return [
            {
                "step": int(learning[2]),
                "mode": f"{learning[1]}_sampled",
                "temperature": report["temperature"],
                "scope": report["scope"],
                **learning_summary,
            }
        ]
    if path.suffix == ".jsonl":
        points = []
        with path.open() as stream:
            for line in stream:
                if not line.endswith("\n"):
                    break
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict) or not isinstance(row.get("update"), int):
                    continue
                summary = _summary(row)
                if summary:
                    points.append(
                        {
                            "step": row["update"],
                            "mode": "greedy",
                            "overall": summary,
                            "opponents": {},
                        }
                    )
        return points
    match = re.fullmatch(r"update-(\d+)", path.stem if path.suffix == ".npz" else path.parent.name)
    if not match:
        return []
    step = int(match[1])
    if path.suffix == ".npz":
        with np.load(path, allow_pickle=False) as data:
            summary = summarize_matches(data["opponents"], data["cash"], data["outcomes"])
        return [{"step": step, "mode": "greedy", **summary}]
    report = json.loads(path.read_text())
    points = []
    for mode, panel in report.get("results", {}).items():
        games = panel.get("games")
        if not isinstance(games, list) or not games:
            continue
        summary = summarize_matches(
            np.asarray([game["opponent"] for game in games]),
            np.asarray([[game["cash"], game["opponent_cash"]] for game in games]),
            np.asarray([game["outcome"] for game in games]),
        )
        points.append(
            {"step": step, "mode": mode, "temperature": panel.get("temperature"), **summary}
        )
    return points


class EvaluationHistoryReader:
    """Read each changed evidence file once, retaining only compact summaries."""

    def __init__(self) -> None:
        """Create a thread-safe cache independent of operational configuration."""
        self._cache: dict[Path, tuple[tuple[int, int, int], list[dict[str, Any]]]] = {}
        self._lock = threading.Lock()

    def read(self, run_dir: Path) -> dict[str, Any]:
        """Return ordered checkpoints, preferring match details over total-only logs."""
        with self._lock:
            return self._read(run_dir)

    def _read(self, run_dir: Path) -> dict[str, Any]:
        selection = run_dir / "selection"
        paths = [
            run_dir / "selection-metrics.jsonl",
            *sorted((run_dir / "evaluation").glob("selection-*.json")),
            *sorted((run_dir / "evaluation").glob("confirmation-*.json")),
            *sorted((run_dir / "evaluation").glob("update-*.json")),
            *sorted(selection.glob("update-*.npz")),
            *sorted(selection.glob("update-*/comparison.json")),
        ]
        merged: dict[tuple[int, str], dict[str, Any]] = {}
        modified = 0.0
        unreadable = []
        for path in paths:
            if not path.is_file() or path.is_symlink():
                continue
            stat = path.stat()
            modified = max(modified, stat.st_mtime)
            token = (stat.st_ino, stat.st_mtime_ns, stat.st_size)
            cached = self._cache.get(path)
            if cached is not None and cached[0] == token:
                points = cached[1]
            else:
                try:
                    points = _read_points(path)
                except (OSError, ValueError, KeyError, TypeError, BadZipFile, EOFError):
                    # A running evaluator may still be writing this artifact.
                    unreadable.append(path.relative_to(run_dir).as_posix())
                    continue
                self._cache[path] = token, points
            for point in points:
                merged[point["step"], point["mode"]] = {
                    **point,
                    "source": path.relative_to(run_dir).as_posix(),
                }
        return {
            "points": [merged[key] for key in sorted(merged)],
            "modified_timestamp": modified,
            "unreadable_sources": unreadable,
        }
