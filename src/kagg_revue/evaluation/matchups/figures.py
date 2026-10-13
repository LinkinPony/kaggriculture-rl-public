"""Export descriptive figures from authenticated direct-game accounting."""

from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def plot_duels(groups: dict[str, Any], output: Path) -> None:
    """Show cash development and additive income/spending gaps for the latest pair."""
    names = ("s82001_u276_t1", "s82001_u800_t1")
    if "latest_two" not in groups or any(not groups.get(name, {}).get("games") for name in names):
        return
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    days = np.arange(720) / 24
    for name, color, label in zip(names, ("#2563eb", "#ea580c"), ("U276", "U800"), strict=True):
        group = groups[name]
        axes[0].plot(
            days,
            np.asarray(group["cash_gap_by_turn"]) / 1000,
            color=color,
            label=f"{label} ({group['games']} games)",
        )
    axes[0].axhline(0, color="#64748b", linewidth=0.8)
    axes[0].set(
        xlabel="Elapsed game days",
        ylabel="Our cash minus DSM (thousands)",
        title="Cash gap develops after midseason",
    )
    axes[0].legend()
    ledger = groups["latest_two"]["ledger"]
    products = [
        "MILK",
        "EGG",
        "TOMATO",
        "FERTILIZER",
        "WHEAT",
        "WOOL",
        "STRAWBERRY",
        "CARROT",
        "MELON",
    ]
    values = [ledger[f"SELL:{product}"]["cash_gap"] / 1000 for product in products]
    products.append("Spending difference")
    values.append(sum(v["cash_gap"] for k, v in ledger.items() if not k.startswith("SELL:")) / 1000)
    axes[1].barh(
        products, values, color=["#dc2626" if value < 0 else "#16a34a" for value in values]
    )
    axes[1].invert_yaxis()
    axes[1].axvline(0, color="#64748b", linewidth=0.8)
    axes[1].set(
        xlabel="Mean contribution to our terminal cash gap (thousands)",
        title=f"Latest {groups['latest_two']['games']} games: exact cash accounting",
    )
    for axis in axes:
        axis.grid(alpha=0.15)
        axis.set_axisbelow(True)
    fig.suptitle("Direct games against DSM | Observed accounting, not causal effects")
    fig.tight_layout()
    fig.savefig(output / "overview.png", dpi=180)
    fig.savefig(output / "overview.svg")
    plt.close(fig)
