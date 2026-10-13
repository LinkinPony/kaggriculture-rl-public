"""Export standalone date and rating comparison figures."""

from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def plot(report: dict[str, Any], output: Path) -> None:
    """Show source mix, SE coverage, observed rating bins and missingness."""
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    figure, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)
    dates = report["by_date"]
    labels = [r["date"][5:] if r["date"] != "unknown" else "Unknown" for r in dates]
    positions = np.arange(len(dates))
    for axis, prefix, title in (
        (axes[0, 0], "", "All merged replays by UTC date"),
        (axes[0, 1], "se_", "SE crop / animal use by UTC date"),
    ):
        daily = np.array([r[prefix + "daily_episodes"] for r in dates])
        total = np.array([r[prefix + "episodes"] for r in dates])
        axis.bar(positions, daily, color="#277DA1", label="Daily archives")
        axis.bar(positions, total - daily, bottom=daily, color="#F8961E", label="Local supplement")
        axis.set_xticks(positions, labels, rotation=65, ha="right", fontsize=8)
        axis.set(title=title, ylabel="Unique episodes")
        axis.legend(frameon=False)
    axis = axes[1, 0]
    labels = [r["range"] for r in report["all"]["histogram"]]
    positions = np.arange(len(labels))
    for offset, key, color, label in (
        (-0.2, "all", "#277DA1", "All with rating"),
        (0.2, "se", "#D1495B", "SE users with rating"),
    ):
        values = [
            100 * r["episodes"] / max(1, report[key]["known_ratings"])
            for r in report[key]["histogram"]
        ]
        axis.bar(positions + offset, values, width=0.4, color=color, label=label)
    axis.set_xticks(positions, labels, rotation=25, ha="right")
    axis.set(title="Recorded two-player average rating", ylabel="% of episodes with known rating")
    axis.legend(frameon=False)
    axis = axes[1, 1]
    for y, key in enumerate(("all", "se")):
        r = report[key]
        known = r["rating_coverage_percent"]
        axis.barh(y, known, color="#277DA1", label="Known" if y == 0 else None)
        axis.barh(y, 100 - known, left=known, color="#D8DEE9", label="Missing" if y == 0 else None)
        axis.text(
            2,
            y,
            f"{r['known_ratings']:,} / {r['episodes']:,} ({known:.1f}%)",
            va="center",
            color="white",
        )
    axis.set_yticks([0, 1], ["All", "SE users"])
    axis.set(title="Rating availability", xlabel="% of episodes", xlim=(0, 100))
    axis.legend(frameon=False, loc="lower right")
    figure.suptitle(
        "Kaggriculture replay collection: dates and ratings\n"
        "SE = observed crop or stocked animal; unknown ratings are not imputed",
        fontsize=15,
    )
    figure.savefig(output / "distributions.png", dpi=170)
    figure.savefig(output / "distributions.pdf")
    plt.close(figure)
