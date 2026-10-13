"""Weighted opponent trends using the dashboard's existing range and point budgets."""

from array import array
from typing import Any

import numpy as np

from kagg_revue.monitor.config import MonitorSettings
from kagg_revue.monitor.curves import column_curves
from kagg_revue.monitor.history import ScalarHistory
from kagg_revue.monitor.opponents.records import OpponentRecord


def curves(
    record: OpponentRecord, start: int, end: int, smoothing: int, settings: MonitorSettings
) -> dict[str, Any]:
    """Smooth full evidence before downsampling; do not fill unsampled rounds."""
    steps = np.frombuffer(record.steps, dtype=np.int64)
    games = np.asarray(record.counts["games"], dtype=np.float64)
    wins = np.asarray(record.counts["wins"], dtype=np.float64)
    ties = np.asarray(record.counts["ties"], dtype=np.float64)
    fields = {
        "win_rate": wins / games,
        "observed_score": (wins + ties / 2) / games,
        "mean_cash_difference": np.asarray(record.values["mean_cash_difference"]),
    }
    limit = (
        settings.recent_points if end - start + 1 <= settings.recent_points else settings.max_points
    )
    raw, trends, summaries = {}, {}, {}
    for name, values in fields.items():
        valid = np.isfinite(values)
        column = ScalarHistory(
            steps=array("q", steps[valid]),
            values=array("d", values[valid]),
            weights=array("d", games[valid]),
            breaks=array("q", steps[~valid]),
        )
        points, trend, summary = column_curves(column, start, end, smoothing, limit)
        raw[name], trends[name], summaries[name] = points, trend, summary
    return {
        "series": raw,
        "trends": trends,
        "summaries": summaries,
        "range": {"start": start, "end": end},
        "smoothing": smoothing,
        "events": [],
        "resolution": "full" if limit == settings.recent_points else "buckets",
    }
