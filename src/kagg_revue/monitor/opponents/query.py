"""Read-only summaries and cursor-paginated battle batches for one learner run."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from typing import Any

import numpy as np
from pydantic import Field

from kagg_revue.monitor.config import MonitorSettings
from kagg_revue.monitor.curves import CurveQuery, history_range
from kagg_revue.monitor.history import RunHistory
from kagg_revue.monitor.opponents.records import COUNTS, OpponentRecord, finite, identity
from kagg_revue.monitor.opponents.trends import curves


class OpponentQuery(CurveQuery):
    """Share inclusive training ranges and use an exclusive cursor for stable paging."""

    opponent: str | None = Field(default=None, min_length=1, max_length=512)
    before: int | None = Field(default=None, ge=1)
    limit: int = Field(default=50, ge=1, le=200)


def statistics(record: OpponentRecord, low: int = 0, high: int | None = None) -> dict[str, Any]:
    """Compute empirical rates and means from physical games, never batch averages."""
    counts = {name: sum(record.counts[name][low:high]) for name in COUNTS}
    games = counts["games"]
    result: dict[str, Any] = {
        **counts,
        "win_rate": counts["wins"] / games if games else None,
        "observed_score": (counts["wins"] + counts["ties"] / 2) / games if games else None,
    }
    weights = np.asarray(record.counts["games"][low:high], dtype=np.float64)
    for name in ("mean_terminal_cash", "mean_cash_difference"):
        values = np.asarray(record.values[name][low:high])
        result[name] = (
            float(np.average(values, weights=weights))
            if games and np.isfinite(values).all()
            else None
        )
    return result


def _batches(record: OpponentRecord, query: OpponentQuery, start: int, end: int) -> dict[str, Any]:
    low = bisect_left(record.steps, start)
    high = bisect_right(record.steps, min(end, query.before - 1) if query.before else end)
    indexes = list(range(high - 1, max(low - 1, high - query.limit - 1), -1))
    rows = []
    for index in indexes:
        panel = {name: record.counts[name][index] for name in COUNTS}
        rows.append(
            {
                "update": record.steps[index],
                **panel,
                "win_rate": panel["wins"] / panel["games"],
                "observed_score": (panel["wins"] + panel["ties"] / 2) / panel["games"],
                **{
                    (f"sampling_{name}" if name in {"score", "probability"} else name): finite(
                        record.values[name][index]
                    )
                    for name in record.values
                },
            }
        )
    return {
        "rows": rows,
        "total": max(0, bisect_right(record.steps, end) - low),
        "next_before": record.steps[indexes[-1]] if indexes and indexes[-1] > low else None,
    }


def payload(
    history: RunHistory, live: dict[str, Any], query: OpponentQuery, settings: MonitorSettings
) -> dict[str, Any]:
    """Join committed evidence with explicitly dated, live pool membership and scores."""
    start, end = history_range(history, query)
    pfsp = live.get("pfsp") or {}
    pool = pfsp.get("history")
    active: dict[str, dict[str, Any]] = {}
    unidentified_pool = 0
    if isinstance(pool, list):
        for entry in pool:
            if not isinstance(entry, dict):
                continue
            metadata = identity(entry)
            if metadata is None:
                unidentified_pool += 1
            else:
                active[metadata["key"]] = {**entry, **metadata}
    entries = []
    selected = None
    for key in sorted(history.opponents.records.keys() | active.keys()):
        current = active.get(key)
        record = history.opponents.records.get(key) or OpponentRecord(identity(current or {}) or {})
        low, high = bisect_left(record.steps, start), bisect_right(record.steps, end)
        row = {
            **record.metadata,
            **(identity(current) or {} if current else {}),
            "in_pool": (
                key in active
                if isinstance(pool, list)
                and (
                    current
                    or (
                        not unidentified_pool
                        and (finite(pfsp.get("update")) or 0)
                        >= (record.steps[-1] if record.steps else 0)
                    )
                )
                else None
            ),
            "score": finite(current.get("score")) if current else None,
            "probability": finite(current.get("probability")) if current else None,
            "last_update": record.steps[-1] if record.steps else None,
            "lifetime": statistics(record),
            "interval": statistics(record, low, high),
        }
        entries.append(row)
        if key == query.opponent:
            selected = {
                **row,
                "batches": _batches(record, query, start, end),
                "curves": curves(record, start, end, query.smoothing, settings),
            }
    return {
        "entries": entries,
        "selected": selected,
        "range": {"start": start, "end": end},
        "extent": {"start": history.first_step, "end": history.last_step},
        "saved_update": history.last_step,
        "live_update": live.get("update"),
        "pfsp_update": pfsp.get("update"),
        "last_modified": history.modified_ns / 1e9,
        "source": "metrics.jsonl",
        "unassigned_games": history.opponents.unassigned_games,
        "invalid_panels": history.opponents.invalid_panels,
        "unidentified_pool": unidentified_pool,
    }
