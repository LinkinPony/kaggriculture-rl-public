"""Range queries and weighted trends computed before display downsampling."""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.monitor.config import MonitorSettings
from kagg_revue.monitor.history import HistoryReader, RunHistory, ScalarHistory


class CurveQuery(BaseModel):
    """Validated controls shared by all training charts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    window: int = Field(default=500, ge=0, le=1_000_000)
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)
    smoothing: int = Field(default=32, ge=1, le=2048)
    # Two models with five scripts already request 75 distinct chart series.
    tags: tuple[str, ...] = Field(default=(), max_length=128)

    @model_validator(mode="after")
    def ordered_bounds(self) -> CurveQuery:
        """Reject reversed custom ranges rather than silently changing the view."""
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("start must not exceed end")
        return self


def _points(
    steps: NDArray[np.int64],
    values: NDArray[np.float64],
    segments: NDArray[np.int64],
    weights: NDArray[np.float64],
    limit: int,
) -> list[dict[str, Any]]:
    """Keep exact endpoints and extrema; attach honest bucket coverage metadata."""
    count = len(steps)
    if not count:
        return []
    indexes = np.arange(count)
    buckets = np.array_split(indexes, max(1, limit // 4)) if count > limit else [indexes]
    output: list[dict[str, Any]] = []
    for bucket in buckets:
        if count <= limit:
            selected = bucket
        else:
            changes = np.flatnonzero(np.diff(segments[bucket]))
            selected = np.unique(
                np.concatenate(
                    (
                        [
                            bucket[0],
                            bucket[-1],
                            bucket[np.argmin(values[bucket])],
                            bucket[np.argmax(values[bucket])],
                        ],
                        bucket[changes],
                        bucket[changes + 1],
                    )
                )
            )
        for index in selected:
            point: dict[str, Any] = {
                "step": int(steps[index]),
                "value": float(values[index]),
                "segment": int(segments[index]),
            }
            if count > limit:
                point["bucket"] = {
                    "start": int(steps[bucket[0]]),
                    "end": int(steps[bucket[-1]]),
                    "count": len(bucket),
                    "samples": float(weights[bucket].sum()),
                    "mean": float(np.average(values[bucket], weights=weights[bucket])),
                    "min": float(values[bucket].min()),
                    "max": float(values[bucket].max()),
                }
            output.append(point)
    return output


def column_curves(
    column: ScalarHistory,
    start: int,
    end: int,
    smoothing: int,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Compute trailing step windows with warmup context and no cross-boundary mixing."""
    all_steps = np.frombuffer(column.steps, dtype=np.int64)
    low = int(np.searchsorted(all_steps, max(0, start - 2 * smoothing + 1)))
    high = int(np.searchsorted(all_steps, end, side="right"))
    steps = all_steps[low:high]
    if not len(steps):
        return [], [], {}
    values = np.frombuffer(column.values, dtype=np.float64)[low:high]
    weights = np.frombuffer(column.weights, dtype=np.float64)[low:high]
    breaks = np.frombuffer(column.breaks, dtype=np.int64)
    segments = np.searchsorted(breaks, steps, side="right").astype(np.int64)
    segment_start = np.maximum.accumulate(
        np.where(
            np.r_[True, np.diff(segments) != 0],
            np.arange(len(steps)),
            0,
        )
    )
    left = np.maximum(np.searchsorted(steps, steps - smoothing + 1), segment_start)
    totals = np.r_[0.0, np.cumsum(values * weights)]
    counts = np.r_[0.0, np.cumsum(weights)]
    trend_weights = counts[1:] - counts[left]
    trends = (totals[1:] - totals[left]) / trend_weights
    visible = steps >= start
    if not visible.any():
        return [], [], {}
    last = len(steps) - 1
    previous_end = int(np.searchsorted(steps, steps[last] - smoothing, side="right"))
    previous_start = max(
        int(segment_start[last]),
        int(
            np.searchsorted(
                steps,
                steps[last] - 2 * smoothing + 1,
            )
        ),
    )
    previous = (
        float(
            (totals[previous_end] - totals[previous_start])
            / (counts[previous_end] - counts[previous_start])
        )
        if previous_end > previous_start
        else None
    )
    summary = {
        "step": int(steps[last]),
        "value": float(values[last]),
        "mean": float(trends[last]),
        "previous_mean": previous,
        "delta": float(trends[last]) - previous if previous is not None else None,
        "window_start": int(steps[left[last]]),
        "count": int(last - left[last] + 1),
        "samples": float(trend_weights[last]),
        "min": float(values[visible].min()),
        "max": float(values[visible].max()),
        "visible_count": int(visible.sum()),
    }
    return (
        _points(steps[visible], values[visible], segments[visible], weights[visible], limit),
        _points(
            steps[visible], trends[visible], segments[visible], np.ones(int(visible.sum())), limit
        ),
        summary,
    )


def history_range(history: RunHistory, query: CurveQuery) -> tuple[int, int]:
    """Resolve shared inclusive update bounds for charts and opponent statistics."""
    end = query.end if query.end is not None else history.last_step or 0
    start = (
        query.start
        if query.start is not None
        else (
            max(history.first_step or 0, end - query.window + 1)
            if query.window
            else history.first_step or 0
        )
    )
    if start > end:
        if query.start is None:
            start = end
        else:
            end = start
    return start, end


def history_payload(
    history: RunHistory,
    query: CurveQuery,
    max_points: int,
    recent_points: int,
) -> dict[str, Any]:
    """Return one consistent range for every series and its change events."""
    start, end = history_range(history, query)
    limit = recent_points if end - start + 1 <= recent_points else max_points
    raw, trends, summaries = {}, {}, {}
    for tag, column in history.series.items():
        if query.tags and tag not in query.tags:
            continue
        points, trend, summary = column_curves(column, start, end, query.smoothing, limit)
        if points:
            raw[tag], trends[tag], summaries[tag] = points, trend, summary
    return {
        "series": raw,
        "trends": trends,
        "summaries": summaries,
        "events": history.events,
        "range": {"start": start, "end": end},
        "extent": {"start": history.first_step, "end": history.last_step},
        "smoothing": query.smoothing,
        "last_modified": history.modified_ns / 1e9,
        "source": "metrics.jsonl",
        "resolution": "full" if limit == recent_points else "buckets",
    }


class CurveReader:
    """Cache a few completed range responses while tailing selected histories."""

    def __init__(self, settings: MonitorSettings, history: HistoryReader | None = None) -> None:
        """Use Hydra-resolved cache and display budgets."""
        self._settings = settings
        self._history = (
            history if history is not None else HistoryReader(settings.history_cache_runs)
        )
        self._responses: OrderedDict[tuple[object, ...], dict[str, Any]] = OrderedDict()

    def read(self, path: Path, query: CurveQuery) -> dict[str, Any]:
        """Query under the reader lock so an append cannot invalidate numeric views."""
        with self._history.lock:
            history = self._history.read(path)
            key = (path, history.inode, history.offset, history.modified_ns, query)
            if key not in self._responses:
                self._responses[key] = history_payload(
                    history,
                    query,
                    self._settings.max_points,
                    self._settings.recent_points,
                )
            self._responses.move_to_end(key)
            while len(self._responses) > 4:
                self._responses.popitem(last=False)
            return self._responses[key]
