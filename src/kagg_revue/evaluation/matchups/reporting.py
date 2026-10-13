"""Summarize complete replay ledgers without treating accounting as causal effects."""

from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import matplotlib
import numpy as np

from kagg_revue.artifacts.io import write_json

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def summarize(results: list[dict[str, Any]], submission: int, output: Path) -> None:
    """Save team/version breakdowns and an exportable four-panel figure."""
    groups: dict[str, list[Any]] = defaultdict(list)
    for result in results:
        own = next(p for p in result["players"] if p["submission_id"] == submission)
        opponent = result["players"][1 - own["seat"]]
        groups[opponent["name"]].append((result, own, opponent))
    summaries: dict[str, Any] = {}
    for name, rows in groups.items():
        keys = sorted({k for _, x, y in rows for z in (x, y) for k in z["ledger"]})
        ledger = {}
        for key in keys:
            sides = []
            for side in (1, 2):
                quantities = [r[side]["ledger"].get(key, {}).get("quantity", 0) for r in rows]
                cash = [r[side]["ledger"].get(key, {}).get("cash", 0) for r in rows]
                sides.append(
                    {
                        "quantity": mean(quantities),
                        "cash": mean(cash),
                        "unit_price": abs(sum(cash) / sum(quantities)) if sum(quantities) else None,
                    }
                )
            ledger[key] = {
                "own": sides[0],
                "opponent": sides[1],
                "cash_gap": sides[0]["cash"] - sides[1]["cash"],
            }
        versions = {}
        for version in sorted({y["submission_id"] for _, _, y in rows}):
            margins = [
                x["cash"][-1] - y["cash"][-1] for _, x, y in rows if y["submission_id"] == version
            ]
            versions[str(version)] = {
                "games": len(margins),
                "wins": sum(v > 0 for v in margins),
                "mean_cash_gap": mean(margins),
            }
        summaries[name] = {
            "games": len(rows),
            "wins": sum(x["cash"][-1] > y["cash"][-1] for _, x, y in rows),
            "draws": sum(x["cash"][-1] == y["cash"][-1] for _, x, y in rows),
            "own_cash": mean(x["cash"][-1] for _, x, _ in rows),
            "opponent_cash": mean(y["cash"][-1] for _, _, y in rows),
            "versions": versions,
            "ledger": ledger,
            "cash_gap_by_turn": {
                str(t): mean(x["cash"][t] - y["cash"][t] for _, x, y in rows)
                for t in (24, 72, 144, 240, 360, 480, 600, 696, 719)
            },
            "idle_fraction": [
                sum(r[s]["operations"].get("PASS", 0) for r in rows)
                / sum(sum(r[s]["operations"].values()) for r in rows)
                for s in (1, 2)
            ],
        }
    write_json(output / "aggregates.json", summaries)
    fig, axes = plt.subplots(2, len(groups), figsize=(13, 8), squeeze=False)
    products = ["STRAWBERRY", "MILK", "WOOL", "CARROT", "MELON", "EGG", "TOMATO"]
    for column, (name, rows) in enumerate(groups.items()):
        ax = axes[0, column]
        gaps = (
            np.array(
                [[a - b for a, b in zip(x["cash"], y["cash"], strict=True)] for _, x, y in rows]
            )
            / 1000
        )
        days = np.arange(gaps.shape[1]) / 24
        for gap in gaps:
            ax.plot(days, gap, color="#64748b", alpha=0.25, linewidth=0.7)
        ax.plot(days, gaps.mean(0), color="#2563eb", linewidth=2, label="Mean")
        ax.axhline(0, color="black", linewidth=0.7)
        ax.set(
            title=f"vs {name} ({len(rows)} games)",
            xlabel="Elapsed game days",
            ylabel="Our cash minus opponent cash (thousands)",
        )
        ax.grid(alpha=0.15)
        ax.legend()
        ax = axes[1, column]
        values = [
            summaries[name]["ledger"].get("SELL:" + product, {}).get("cash_gap", 0) / 1000
            for product in products
        ]
        ax.barh(products, values, color=["#dc2626" if v < 0 else "#16a34a" for v in values])
        ax.axvline(0, color="black", linewidth=0.7)
        ax.invert_yaxis()
        ax.set(
            xlabel="Mean sales revenue gap (thousands)", title="Actual settled revenue by product"
        )
        ax.grid(axis="x", alpha=0.15)
    fig.suptitle(
        f"Submission {submission}: observed matchups\n"
        "Revenue gaps are accounting differences, not isolated causal effects"
    )
    fig.tight_layout()
    fig.savefig(output / "matchups.png", dpi=180)
    fig.savefig(output / "matchups.svg")
    plt.close(fig)
