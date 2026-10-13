"""Inspect opening persistence, selected replay witnesses and shop associations."""

import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import orjson

from kagg_revue.artifacts.io import write_json
from kagg_revue.datasets.behavior.extraction import fingerprint
from kagg_revue.datasets.behavior.metrics import Hashes


def opening_changes(rows: list[dict[str, Any]], hashes: Hashes) -> list[dict[str, Any]]:
    """Distinguish opening variety from chronological persistence within each day."""
    groups: dict[tuple[str, str, int], list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        groups[(row["name"], row["date"], row["seat"])].append(index)
    result = []
    for (name, date, seat), indices in sorted(groups.items()):
        if len(indices) < 5:
            continue
        indices.sort(key=lambda i: rows[i]["create_time"])
        signatures = [fingerprint(hashes[i, :24, 1].tolist()) for i in indices]
        counts = Counter(signatures)
        labels = {signature: i for i, (signature, _) in enumerate(counts.most_common())}
        transitions = sum(a != b for a, b in zip(signatures[:-1], signatures[1:], strict=True))
        expected = len(indices) - sum(n * n for n in counts.values()) / len(indices)
        result.append(
            {
                "name": name,
                "date": date,
                "seat": seat,
                "n": len(indices),
                "distinct_openings": len(counts),
                "adjacent_switches": transitions,
                "random_permutation_expected_switches": expected,
                "sequence": [labels[s] for s in signatures],
                "times": [rows[i]["create_time"] for i in indices],
            }
        )
    return result


def _witnesses(output: Path, report: dict[str, Any]) -> list[dict[str, Any]]:
    sources = orjson.loads((output / "sources.json").read_bytes())
    archives = {row["date"]: row["path"] for row in sources["daily_archives"]}
    results = []
    for team in report["teams"]:
        if team["name"] not in {
            "SpaTaro",
            "ymg_aq",
            "我都先道歉",
            "沒有道歉 沒有道歉",
            "Matthew Huang",
        }:
            continue
        for witness in team["histories"]["witnesses"][:2]:
            pair = []
            with zipfile.ZipFile(archives[witness["date"]]) as archive:
                for episode in witness["episode_ids"]:
                    replay = orjson.loads(archive.read(f"{episode}.json"))
                    seat, step = witness["seat"], witness["decision_step"]
                    times = [
                        float(frame[seat]["observation"]["remainingOverageTime"])
                        for frame in replay["steps"]
                    ]
                    spent = [
                        (i, times[i] - times[i + 1])
                        for i in range(719)
                        if times[i] - times[i + 1] > 1e-5
                    ]
                    pair.append(
                        {
                            "episode_id": episode,
                            "action": replay["steps"][step + 1][seat]["action"],
                            "remaining_overage_before_decision": times[step],
                            "overage_spending": spent,
                            "observation_sha": fingerprint(
                                replay["steps"][step][seat]["observation"]
                            ),
                        }
                    )
            results.append({"name": team["name"], **witness, "replays": pair})
    return results


def _economy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["name"]].append(row)
    summaries, shops = [], []
    shop_names = sorted({shop for row in rows for shop in row["terminal"]["shops"]})
    for name, selected in groups.items():
        if len(selected) < 20:
            continue
        initial = Counter(fingerprint(row["first_action"]) for row in selected)
        terminal_kinds = sorted({kind for row in selected for kind in row["terminal"]["tiles"]})
        summaries.append(
            {
                "name": name,
                "n": len(selected),
                "first_action_distinct": len(initial),
                "first_action_max_fraction": max(initial.values()) / len(selected),
                "first_actions": [
                    {
                        "count": count,
                        "action": next(
                            row["first_action"]
                            for row in selected
                            if fingerprint(row["first_action"]) == key
                        ),
                    }
                    for key, count in initial.most_common(8)
                ],
                "terminal_tiles_median": {
                    kind: float(
                        np.median([row["terminal"]["tiles"].get(kind, 0) for row in selected])
                    )
                    for kind in terminal_kinds
                },
                "median_cash_by_day": np.median(
                    [row["money_by_game_day"] for row in selected], axis=0
                ).tolist(),
                "terminal_shed_median": float(
                    np.median([sum(row["terminal"]["shed"].values()) for row in selected])
                ),
            }
        )
        for shop in shop_names:
            present = [row for row in selected if shop in row["terminal"]["shops"]]
            absent = [row for row in selected if shop not in row["terminal"]["shops"]]
            if min(len(present), len(absent)) < 10:
                continue
            shops.append(
                {
                    "name": name,
                    "shop": shop,
                    "present_n": len(present),
                    "absent_n": len(absent),
                    "cash_median_present": float(np.median([row["cash"] for row in present])),
                    "cash_median_absent": float(np.median([row["cash"] for row in absent])),
                    "win_fraction_present": sum(row["result"] == 1 for row in present)
                    / len(present),
                    "win_fraction_absent": sum(row["result"] == 1 for row in absent) / len(absent),
                }
            )
    return {"teams": summaries, "shop_associations": shops}


def diagnose(output: Path) -> dict[str, Any]:
    """Write targeted raw-action evidence and exploratory economic summaries."""
    report = orjson.loads((output / "report.json").read_bytes())
    rows = orjson.loads((output / "trajectories.json").read_bytes())
    with np.load(output / "fingerprints.npz", allow_pickle=False) as data:
        hashes = data["hashes"]
    result = {
        "opening_chronology": opening_changes(rows, hashes),
        "witnesses": _witnesses(output, report),
        "economy": _economy(rows),
        "scope": "Chronology does not identify versions. Shop associations are descriptive and "
        "confounded by opponents, other shops, selected matches and policy versions.",
    }
    write_json(output / "diagnostics.json", result)
    return result
