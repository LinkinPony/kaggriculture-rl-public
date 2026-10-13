"""Descriptive opening coverage; outcome associations are not causal rankings."""

import math
from collections import Counter, defaultdict
from typing import Any

import orjson

from kagg_revue.datasets.coverage.analysis import concentration
from kagg_revue.datasets.openings.extraction import HORIZONS


def asset_key(row: dict[str, Any], turn: int = 24) -> str:
    """Group production composition, including undeployed animals and hired labor."""
    value = {**row["production"][str(turn)]}
    if turn == 24:
        value["HIRES"] = row["hires24"]
    return orjson.dumps(value, option=orjson.OPT_SORT_KEYS).decode()


def shortfalls(rows: list[dict[str, Any]], turns: int) -> dict[str, Any]:
    """Count trajectories as well as repeated events, with fixed follow-up windows."""
    events = [(row, event) for row in rows for event in row["shortfalls"] if event["turn"] < turns]
    return {
        "trajectories": len({(r["episode_id"], r["seat"]) for r, _ in events}),
        "events": len(events),
        "by_operation": dict(Counter(e["requested"][0] for _, e in events)),
        "catchup_events_12": sum(e["catchup_turns"] is not None for _, e in events),
        "complete_followup_events": sum(e["followup_complete"] for _, e in events),
        "zero_fill_events": sum(e["committed"] == 0 for _, e in events),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep repeated requests, actual procurement and resulting assets distinct."""
    return {
        "trajectories": len(rows),
        "episodes": len({r["episode_id"] for r in rows}),
        "seeds": len({r["seed"] for r in rows}),
        "names": len({r["name"] for r in rows}),
        "partitions": dict(Counter(r["split"] for r in rows)),
        "maximum_candidate_rows": {str(h): len(rows) * h for h in HORIZONS},
        "prefixes": {
            channel: {
                str(h): concentration([r["prefixes"][channel][str(h)] for r in rows])
                for h in HORIZONS
            }
            for channel in ("full", "units", "market", "settled_market")
        },
        "production": {
            str(h): concentration([asset_key(r, h) for r in rows]) for h in (24, 48, 72, 144)
        },
        "wheat_roundtrip_trajectories": sum(r["wheat_roundtrip_requested"] for r in rows),
        "wheat_roundtrip_quantities": dict(
            Counter(str(r["wheat_buy"]) for r in rows if r["wheat_roundtrip_requested"])
        ),
        "shortfalls": {str(h): shortfalls(rows, h) for h in (4, 24, 72)},
    }


def families(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Describe frequent portfolios without interpreting observed WDL as value."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[asset_key(row)].append(row)
    result = []
    for key, group in sorted(groups.items(), key=lambda item: -len(item[1])):
        external = [r for r in group if r["name"] != r["opponent"]]
        result.append(
            {
                "assets": orjson.loads(key),
                "trajectories": len(group),
                "names": Counter(r["name"] for r in group).most_common(8),
                "market_first": concentration([r["prefixes"]["market"]["1"] for r in group]),
                "units24": concentration([r["prefixes"]["units"]["24"] for r in group]),
                "nonmirror_wdl": dict(Counter(str(r["result"]) for r in external)),
                "examples": [
                    {
                        "episode_id": r["episode_id"],
                        "seat": r["seat"],
                        "first_market": r["first_action"]["market"],
                    }
                    for r in group[:3]
                ],
                "shortfalls24": shortfalls(group, 24),
            }
        )
    return result


def novelty(rows: list[dict[str, Any]], baseline: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare coverage only with the actual BC training split's exemplars."""
    result = {}
    for key, get in (
        ("first_market", lambda r: r["prefixes"]["market"]["1"]),
        ("units24", lambda r: r["prefixes"]["units"]["24"]),
        ("production24", asset_key),
    ):
        known = {get(r) for r in baseline}
        fresh = [r for r in rows if get(r) not in known]
        result[key] = {
            "new_trajectories": len(fresh),
            "new_values": len({get(r) for r in fresh}),
            "fraction": len(fresh) / max(1, len(rows)),
        }
    return result


def histories(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Expose multimodal labels at identical visible histories, without future inputs."""
    groups: dict[tuple[int, int, str], list[str]] = defaultdict(list)
    for row in rows:
        for frame in row["histories"]:
            groups[row["seat"], frame["turn"], frame["history"]].append(frame["action"])
    by_turn = {}
    for turn in (0, 1, 2, 4, 12, 23):
        repeated = [v for k, v in groups.items() if k[1] == turn and len(v) >= 2]
        mass = sum(map(len, repeated))
        entropy = 0.0
        for values in repeated:
            counts = Counter(values)
            entropy += sum(-n * math.log(n / len(values)) for n in counts.values())
        by_turn[str(turn)] = {
            "repeated_groups": len(repeated),
            "trajectories": mass,
            "conflicting_groups": sum(len(set(v)) > 1 for v in repeated),
            "conditional_entropy_nats": entropy / max(1, mass),
        }
    return by_turn


def analyze(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize source changes separately from the teacher selection policy."""
    baseline = [r for r in rows if r["baseline_selected"]]
    training = [r for r in baseline if r["split"] == "train"]
    daily = [r for r in rows if r["daily"]]
    teachers = [r for r in daily if r["historical_teacher"]]
    groups = {
        "baseline_bc": baseline,
        "baseline_bc_train": training,
        "daily_all": daily,
        "daily_teachers": teachers,
    }
    dates = sorted({r["date"] for r in daily})
    for date in dates:
        groups[f"daily_all/{date}"] = [r for r in daily if r["date"] == date]
        groups[f"daily_teachers/{date}"] = [r for r in teachers if r["date"] == date]
    names = []
    for name in sorted({r["name"] for r in daily}):
        selected = [r for r in daily if r["name"] == name]
        if len(selected) < 8:
            continue
        names.append(
            {
                "name": name,
                "trajectories": len(selected),
                "first_market": concentration([r["prefixes"]["market"]["1"] for r in selected]),
                "production24": concentration([asset_key(r) for r in selected]),
                "units24": concentration([r["prefixes"]["units"]["24"] for r in selected]),
                "shortfalls24": shortfalls(selected, 24),
            }
        )
    witnesses = [
        {
            "episode_id": r["episode_id"],
            "seat": r["seat"],
            "date": r["date"],
            "name": r["name"],
            "split": r["split"],
            "historical_teacher": r["historical_teacher"],
            "first_market": r["first_action"]["market"],
            "assets24": r["production"]["24"],
            "event": e,
        }
        for r in daily
        for e in r["shortfalls"]
        if e["turn"] < 24
    ]
    return {
        "groups": {name: summarize(group) for name, group in groups.items()},
        "daily_teacher_novelty_vs_bc_train": {
            date: novelty([r for r in teachers if r["date"] == date], training) for date in dates
        },
        "families": {"baseline_bc_train": families(training), "daily_teachers": families(teachers)},
        "histories": {
            "baseline_bc_train": histories(training),
            "daily_teachers": histories(teachers),
        },
        "names": names,
        "shortfall_witnesses": witnesses,
        "notes": [
            "Daily high-average-rating episodes are selected, not a random leaderboard sample.",
            "Teacher aliases have historical ranking evidence; daily versions remain unknown.",
            "Raw row counts precede grounded support filtering and quantity clipping.",
            "Procurement deficits and catch-up do not prove mistakes or causal recovery.",
            "Portfolio families ignore geometry and cash; request coverage is a separate metric.",
            "Observed WDL is confounded by matchmaking; never a reward or teacher weight.",
        ],
    }
