"""Measure replay repetition, public-route overlap and descriptive outcomes."""

import math
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import orjson
from numpy.typing import NDArray

from kagg_revue.artifacts.io import digest
from kagg_revue.datasets.behavior.extraction import action_fingerprints, fingerprint

Hashes = NDArray[np.uint64]
STAGES = ((0, 24), (24, 72), (72, 144), (144, 216), (216, 360), (360, 504), (504, 648), (648, 719))


def _route_overlap(hashes: Hashes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    reference_names, reference_hashes, provenance = [], [], []
    root = Path(__file__).parents[2] / "opponents" / "portfolios"
    for path in sorted(root.glob("*.json.zlib")):
        payload = orjson.loads(zlib.decompress(path.read_bytes()))
        provenance.append(
            {"path": str(path), "sha256": digest(path), "agent_id": payload["agent_id"]}
        )
        for index, route in enumerate(payload["routes"]):
            reference_names.append(f"{payload['agent_id']}:{index}")
            reference_hashes.append([action_fingerprints(action)[1] for action in route[:719]])
    reference = np.asarray(reference_hashes, dtype=np.uint64)
    results = []
    for trajectory in hashes:
        matches = reference == trajectory[:, 1]
        scores = matches.mean(axis=1)
        best = int(scores.argmax())
        stage_best = [int(matches[:, start:end].mean(axis=1).argmax()) for start, end in STAGES]
        results.append(
            {
                "best_reference": reference_names[best],
                "best_single_route_fraction": float(scores[best]),
                "any_reference_turn_fraction": float(matches.any(axis=0).mean()),
                "best_route_per_stage": [reference_names[i] for i in stage_best],
                "stage_route_fraction": [
                    float(matches[i, start:end].mean())
                    for i, (start, end) in zip(stage_best, STAGES, strict=True)
                ],
            }
        )
    return results, provenance


def _pair_profile(hashes: Hashes, groups: list[list[int]], channel: int) -> tuple[list[float], int]:
    counts = np.zeros(hashes.shape[1], dtype=np.float64)
    pairs = 0
    for indices in groups:
        n = len(indices)
        if n < 2:
            continue
        pairs += n * (n - 1)
        selected = hashes[indices, :, channel]
        for step in range(selected.shape[1]):
            _, frequencies = np.unique(selected[:, step], return_counts=True)
            counts[step] += (frequencies * (frequencies - 1)).sum()
    return (counts / pairs if pairs else counts).tolist(), pairs // 2


def _history_conflicts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[Any, ...], list[tuple[dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for row in rows:
        for frame in row["early"]:
            key = (
                row["date"],
                row["seat"],
                row["configuration_hash"],
                frame["step"],
                frame["history"],
            )
            groups[key].append((row, frame))
    replicated = conflicts = unit_conflicts = 0
    witnesses = []
    for key, entries in groups.items():
        if len(entries) < 2:
            continue
        replicated += 1
        actions = {frame["action"] for _, frame in entries}
        unit_conflicts += len({frame["units"] for _, frame in entries}) > 1
        if len(actions) > 1:
            conflicts += 1
            first = entries[0]
            other = next(entry for entry in entries if entry[1]["action"] != first[1]["action"])
            witnesses.append(
                {
                    "date": key[0],
                    "seat": key[1],
                    "decision_step": key[3],
                    "episode_ids": [first[0]["episode_id"], other[0]["episode_id"]],
                    "create_times": [first[0]["create_time"], other[0]["create_time"]],
                    "distinct_actions": len(actions),
                    "observations": len(entries),
                }
            )
    return {
        "replicated_history_groups": replicated,
        "conflicting_history_groups": conflicts,
        "conflicting_unit_history_groups": unit_conflicts,
        "witnesses": sorted(witnesses, key=lambda x: (x["decision_step"], x["date"]))[:12],
    }


def _summary(
    indices: list[int], rows: list[dict[str, Any]], hashes: Hashes, overlaps: list[dict[str, Any]]
) -> dict[str, Any]:
    selected = [rows[i] for i in indices]
    groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    for index in indices:
        row = rows[index]
        groups[(row["date"], row["seat"], row["configuration_hash"])].append(index)
    profiles = {}
    pair_count = 0
    for channel, name in ((0, "raw"), (1, "units"), (2, "structure"), (3, "market")):
        profile, pair_count = _pair_profile(hashes, list(groups.values()), channel)
        profiles[name] = profile
    cash = np.asarray([row["cash"] for row in selected])
    external = [row for row in selected if row["name"] != row["opponent"]]
    results = Counter(row["result"] for row in external)
    route_scores = [overlaps[i]["any_reference_turn_fraction"] for i in indices]
    single_scores = [overlaps[i]["best_single_route_fraction"] for i in indices]
    prefix_counts = {}
    for length in (1, 24, 72, 144, 360, 719):
        counter = Counter(fingerprint(hashes[i, :length, 1].tolist()) for i in indices)
        prefix_counts[str(length)] = {
            "distinct": len(counter),
            "largest_fraction": max(counter.values()) / len(indices),
            "entropy_bits": -sum(
                (n / len(indices)) * math.log2(n / len(indices)) for n in counter.values()
            ),
        }
    daily_first = []
    for key, group in groups.items():
        signatures = Counter(int(hashes[i, 0, 0]) for i in group)
        daily_first.append(
            {"date": key[0], "seat": key[1], "n": len(group), "distinct": len(signatures)}
        )
    return {
        "trajectories": len(indices),
        "distinct_episodes": len({row["episode_id"] for row in selected}),
        "opponents": len({row["opponent"] for row in external}),
        "external_games": len(external),
        "wins": results[1],
        "draws": results[0],
        "losses": results[-1],
        "win_fraction": results[1] / len(external) if external else None,
        "score_fraction": (results[1] + results[0] / 2) / len(external) if external else None,
        "cash_median": float(np.median(cash)),
        "cash_q10": float(np.quantile(cash, 0.1)),
        "cash_q90": float(np.quantile(cash, 0.9)),
        "mean_match_rating": float(np.mean([row["average_match_rating"] for row in selected])),
        "median_margin": float(np.median([row["cash_margin"] for row in external]))
        if external
        else None,
        "within_date_seat_pairs": pair_count,
        "pair_agreement": {
            name: float(np.mean(values)) if pair_count else None
            for name, values in profiles.items()
        },
        "stage_unit_agreement": [
            float(np.mean(profiles["units"][a:b])) if pair_count else None for a, b in STAGES
        ],
        "unit_agreement_by_step": profiles["units"] if pair_count else [],
        "prefix_unit_routes": prefix_counts,
        "first_action_groups": daily_first,
        "reference_union_median": float(np.median(route_scores)),
        "reference_union_ge95_fraction": sum(x >= 0.95 for x in route_scores) / len(indices),
        "reference_single_median": float(np.median(single_scores)),
        "best_references": dict(Counter(overlaps[i]["best_reference"] for i in indices)),
        "overage_spent_median": float(np.median([row["overage_spent"] for row in selected])),
        "overage_spent_max": max(row["overage_spent"] for row in selected),
        "all_pass_fraction": sum(row["all_units_pass_turns"] for row in selected)
        / (719 * len(indices)),
        "histories": _history_conflicts(selected),
    }


def _classify(summary: dict[str, Any], minimum: int) -> str:
    if summary["trajectories"] < minimum or summary["within_date_seat_pairs"] < 5:
        return "insufficient"
    agreement = summary["pair_agreement"]["units"]
    if agreement >= 0.97:
        return "near_fixed_route"
    if summary["reference_union_median"] >= 0.95:
        return "public_route_family"
    if agreement >= 0.80:
        return "stable_backbone"
    if summary["prefix_unit_routes"]["24"]["largest_fraction"] >= 0.8:
        return "fixed_opening_variable_later"
    return "high_variation_unresolved"


def analyze(rows: list[dict[str, Any]], hashes: Hashes, minimum: int) -> dict[str, Any]:
    """Compute diagnostics without treating display names as submission identities."""
    overlaps, references = _route_overlap(hashes)
    groups: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        row["reference_overlap"] = overlaps[index]
        if row["complete"]:
            groups[row["name"]].append(index)
    teams = []
    for name, indices in groups.items():
        summary = _summary(indices, rows, hashes, overlaps)
        dates = sorted({rows[i]["date"] for i in indices})
        daily = {
            date: _summary([i for i in indices if rows[i]["date"] == date], rows, hashes, overlaps)
            for date in dates
        }
        teams.append(
            {"name": name, "category": _classify(summary, minimum), **summary, "daily": daily}
        )
        print(f"Summarized {name}: {len(indices)} trajectories", flush=True)
    teams.sort(key=lambda team: team["trajectories"], reverse=True)
    date_summary = []
    for date in sorted({row["date"] for row in rows}):
        selected = [row for row in rows if row["date"] == date]
        date_summary.append(
            {
                "date": date,
                "episodes": len({row["episode_id"] for row in selected}),
                "teams": len({row["name"] for row in selected}),
                "cash_median": float(np.median([row["cash"] for row in selected])),
                "match_rating_median": float(
                    np.median([row["average_match_rating"] for row in selected])
                ),
                "seat0_wins": sum(row["result"] == 1 for row in selected if row["seat"] == 0),
                "seat1_wins": sum(row["result"] == 1 for row in selected if row["seat"] == 1),
                "ties": sum(row["result"] == 0 for row in selected if row["seat"] == 0),
            }
        )
    return {
        "schema": "daily-behavior-report-v1",
        "episodes": len(rows) // 2,
        "trajectories": len(rows),
        "action_turns": int(hashes.shape[0] * hashes.shape[1]),
        "complete_trajectories": sum(row["complete"] for row in rows),
        "module_versions": dict(Counter(row["module_version"] for row in rows)),
        "configuration_hashes": dict(Counter(str(row["configuration_hash"]) for row in rows)),
        "distinct_seeds": len({row["seed"] for row in rows}),
        "dates": date_summary,
        "minimum_games": minimum,
        "stages": STAGES,
        "reference_sources": references,
        "teams": teams,
        "category_counts": dict(Counter(team["category"] for team in teams)),
        "notes": [
            "Daily archives select high average-rating matches; not a random leaderboard sample.",
            "Names identify display-name groups, not submission IDs or immutable agent versions.",
            "All behavioral classification is descriptive; no RL training method is established.",
            "Pair agreement compares different trajectories by turn, within UTC date and seat.",
            "Reference overlap checks unit requests, not market quantities or execution success.",
            "Union overlap mixes routes by turn; it is an upper bound, not a verified router.",
            "History conflicts exclude remainingOverageTime; versions, randomness, timing and "
            "hidden state remain confounded.",
            "Action t+1 belongs to observation t; frame zero is initialization, not a decision.",
            "Overage measures only time exceeding per-turn allowance, not total inference runtime.",
            "Requested market quantities are not realized production or sales.",
        ],
    }
