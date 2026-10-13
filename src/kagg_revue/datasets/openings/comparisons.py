"""Compact diagnostics for opening-only finetuning and source balancing."""

from collections import Counter
from typing import Any

import orjson

from kagg_revue.datasets.openings.statistics import asset_key


def cohorts(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Keep actual BC membership separate from historical-name daily candidates."""
    groups = {
        "BC train": [r for r in rows if r["baseline_selected"] and r["split"] == "train"],
    }
    for date in sorted({r["date"] for r in rows if r["daily"]}):
        groups[date] = [
            r for r in rows if r["daily"] and r["historical_teacher"] and r["date"] == date
        ]
    return groups


def describe(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Count exposure and follow-up purchases without using cash to rank teachers."""
    markets = Counter(orjson.dumps(r["first_action"]["market"]).decode() for r in rows)
    events = [(r, e) for r in rows for e in r["shortfalls"] if e["turn"] < 24]
    statuses = Counter(e["status"] for _, e in events)
    patterns = {
        "frozen_u5952": [
            ["BUY_PRODUCT", "WHEAT", 13],
            ["BUY_PRODUCT", "WHEAT", 5],
            ["SELL", "WHEAT", 13],
        ],
        "buy_five_only": [["BUY_PRODUCT", "WHEAT", 5]],
    }
    return {
        "trajectories": len(rows),
        "exact_first_market_patterns": {
            name: sum(r["first_action"]["market"] == pattern for r in rows)
            for name, pattern in patterns.items()
        },
        "teacher_exposure": Counter(r["name"] for r in rows).most_common(),
        "first_markets": [
            {"orders": orjson.loads(key), "trajectories": count}
            for key, count in markets.most_common(12)
        ],
        "production24": [
            {"assets": orjson.loads(key), "trajectories": count}
            for key, count in Counter(asset_key(r) for r in rows).most_common(12)
        ],
        "shortfalls24": {
            "statuses": dict(statuses),
            "by_operation": {
                op: {
                    "events": sum(e["requested"][0] == op for _, e in events),
                    "trajectories": len(
                        {(r["episode_id"], r["seat"]) for r, e in events if e["requested"][0] == op}
                    ),
                    "catchup_events_12": sum(
                        e["requested"][0] == op and e["catchup_turns"] is not None
                        for _, e in events
                    ),
                }
                for op in ("BUY_ANIMAL", "BUY_SEED", "HIRE")
            },
        },
    }


def compare(rows: list[dict[str, Any]], bytes_per_row: int) -> dict[str, Any]:
    """Estimate compact storage before eligibility checks, excluding NPY headers."""
    groups = cohorts(rows)
    daily = [r for r in rows if r["daily"] and r["historical_teacher"]]
    selected = [
        r for r in rows if r["baseline_selected"] or (r["daily"] and r["historical_teacher"])
    ]
    training = [r for r in selected if r["split"] == "train"]
    result = {
        "cohorts": {key: describe(group) for key, group in groups.items()},
        "daily_teachers": describe(daily),
        "daily_teachers_train": describe([r for r in daily if r["split"] == "train"]),
        "ymg_aq": {
            name: describe([r for r in group if r["name"] == "ymg_aq"])
            for name, group in groups.items()
        },
        "union_candidates": {
            "trajectories": len(selected),
            "train_trajectories": len(training),
            "partitions": dict(Counter(r["split"] for r in selected)),
            "bytes_per_row": bytes_per_row,
            "train_prefixes": {
                str(h): {
                    "candidate_rows": h * len(training),
                    "dense_gib_upper_bound": h * len(training) * bytes_per_row / 2**30,
                    "fraction_of_full_rows": h / 719,
                }
                for h in (24, 48, 72)
            },
        },
    }
    return result
