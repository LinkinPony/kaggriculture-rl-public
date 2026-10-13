"""Measure composition, requests, production states and exact prefix novelty."""

import math
from collections import Counter
from typing import Any

import numpy as np
import orjson

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "GOOSE", "COW", "SHEEP")


def distance(left: dict[str, float], right: dict[str, float]) -> dict[str, float]:
    """Return total variation and Jensen-Shannon divergence in bits."""
    keys = sorted(left.keys() | right.keys())
    p = np.asarray([left.get(k, 0) for k in keys], dtype=np.float64)
    q = np.asarray([right.get(k, 0) for k in keys], dtype=np.float64)
    if not p.sum() or not q.sum():
        raise ValueError("distribution comparison needs two nonempty populations")
    p, q = p / p.sum(), q / q.sum()
    m = (p + q) / 2
    divergence = 0.0
    for values in (p, q):
        positive = values > 0
        divergence += float((values[positive] * np.log2(values[positive] / m[positive])).sum()) / 2
    return {"total_variation": float(np.abs(p - q).sum() / 2), "js_divergence_bits": divergence}


def describe(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize selected seats without inferring strategy strength from cash."""
    if not rows:
        raise ValueError("cannot describe an empty cohort")
    teachers = Counter(row["name"] for row in rows)
    unit: Counter[str] = Counter()
    market: Counter[str] = Counter()
    for row in rows:
        unit.update(row["unit_operations"])
        market.update(row["market_operations"])
    cash = np.asarray([r["cash"] for r in rows], dtype=np.float64)
    snapshots = {}
    for turn in (24, 72, 144, 360, 718):
        states = [r["snapshots"][str(turn)] for r in rows]
        snapshots[str(turn)] = {
            "mean_assets": {
                p: float(np.mean([s["tiles"].get(p, 0) for s in states])) for p in PRODUCTS
            },
            "asset_presence": {
                p: float(np.mean([s["tiles"].get(p, 0) > 0 for s in states])) for p in PRODUCTS
            },
            "mean_hands": float(np.mean([s["hands"] for s in states])),
            "mean_land": float(np.mean([s["land"] for s in states])),
            "mean_cash": float(np.mean([s["cash"] for s in states])),
        }
    first_markets = Counter(
        orjson.dumps(r["first_action"].get("market", [])).decode() for r in rows
    )
    return {
        "trajectories": len(rows),
        "teachers": dict(teachers),
        "teacher_effective_count": math.exp(
            -sum((n / len(rows)) * math.log(n / len(rows)) for n in teachers.values())
        ),
        "dates": dict(Counter(r["date"] for r in rows)),
        "seats": dict(Counter(r["seat"] for r in rows)),
        "opponents": dict(Counter(r["opponent"] for r in rows)),
        "unit_requests": dict(unit),
        "market_requests": dict(market),
        "market_orders_per_trajectory": sum(market.values()) / len(rows),
        "all_units_pass_fraction": sum(r["all_units_pass_turns"] for r in rows) / (719 * len(rows)),
        "cash": {
            "mean": float(cash.mean()),
            "median": float(np.median(cash)),
            "p10": float(np.quantile(cash, 0.1)),
            "p90": float(np.quantile(cash, 0.9)),
        },
        "mean_match_rating": float(np.mean([r["average_match_rating"] for r in rows])),
        "win_fraction": sum(r["result"] > 0 for r in rows) / len(rows),
        "snapshots": snapshots,
        "first_markets": [
            {"orders": orjson.loads(key), "trajectories": n, "fraction": n / len(rows)}
            for key, n in first_markets.most_common(12)
        ],
        "unique_prefixes": {
            key: len({r["prefixes"][key] for r in rows}) for key in rows[0]["prefixes"]
        },
    }


def compare(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> dict[str, Any]:
    """Separate marginal changes from exact action-prefix overlap."""
    old, new = describe(left), describe(right)
    novelty = {}
    for key in left[0]["prefixes"]:
        known = {r["prefixes"][key] for r in left}
        novelty[key] = sum(r["prefixes"][key] not in known for r in right) / len(right)
    return {
        "baseline": old,
        "current": new,
        "distances": {
            key: distance(old[key], new[key])
            for key in ("teachers", "unit_requests", "market_requests", "opponents")
        },
        "first_market_distance": distance(
            dict(Counter(orjson.dumps(r["first_action"].get("market", [])).decode() for r in left)),
            dict(
                Counter(orjson.dumps(r["first_action"].get("market", [])).decode() for r in right)
            ),
        ),
        "unseen_prefix_fraction": novelty,
    }


def analyze(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare all data, training exposure and same-teacher disjoint date windows."""
    old = [r for r in rows if "baseline" in r["datasets"]]
    new = [r for r in rows if "current" in r["datasets"]]
    shared = sorted({r["name"] for r in old} & {r["name"] for r in new})
    overlapping_dates = {r["date"] for r in old} & {r["date"] for r in new}
    within = {}
    for name in shared:
        a = [r for r in old if r["name"] == name and r["date"] not in overlapping_dates]
        b = [r for r in new if r["name"] == name and r["date"] not in overlapping_dates]
        within[name] = compare(a, b)
    return {
        "all": compare(old, new),
        "train": compare(
            [r for r in old if r["split"] == "train"], [r for r in new if r["split"] == "train"]
        ),
        "new_trajectories": compare(old, [r for r in new if "baseline" not in r["datasets"]]),
        "same_teacher_disjoint_dates": within,
        "shared_teachers": shared,
        "notes": [
            "Dates and team display names are exact archive metadata, not submission identities.",
            "Requests are descriptive; market order counts and quantities are not realized trades.",
            "Production snapshots count deployed tiles, excluding stored or carried animals.",
            "Exact prefix novelty is sample-dependent and does not prove a new strategy.",
            "Cash, ratings and win rates involve different worlds and opponents; "
            "not causal strength.",
            "Same-teacher comparison uses disjoint dates, excluding the shared archive dates.",
        ],
    }
