"""Render static evidence panels for the September replay study."""

from pathlib import Path
from typing import Any

import hydra
import matplotlib
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.evaluation.matchups.insights import TEAMS
from kagg_revue.evaluation.matchups.study import Study

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

LABELS = ("DSM", "MMPQ", "DECEM", "Boey", "Vadim", "Ours")


def plot(output: Path) -> None:
    """Keep matchup denominators visible and distinguish net cash from turnover."""
    summary = orjson.loads((output / "insights.json").read_bytes())
    latest = orjson.loads((output / "latest-paired.json").read_bytes())
    yarn = orjson.loads((output / "boey-yarn-strata.json").read_bytes())
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    figure, axes = plt.subplots(2, 2, figsize=(14, 10), layout="constrained")
    ax = axes[0, 0]
    matrix = np.full((6, 6), np.nan)
    for i, team in enumerate(TEAMS):
        for j, opponent in enumerate(TEAMS):
            if i == j:
                continue
            row = summary["pairs"][f"{team} / {opponent}"]["own"]
            matrix[i, j] = row["win_rate"]
            ax.text(
                j,
                i,
                f"{row['wins']}/{row['games']}\n{row['win_rate']:.0%}",
                ha="center",
                va="center",
                color="white" if abs(row["win_rate"] - 0.5) > 0.3 else "black",
            )
    ax.imshow(matrix, vmin=0, vmax=1, cmap="RdBu")
    ax.set(xticks=range(6), xticklabels=LABELS, yticks=range(6), yticklabels=LABELS)
    ax.set_title("Observed head-to-head wins / games\nRow player wins; mixed submission versions")

    ax = axes[0, 1]
    versions = summary["versions"]
    ids = [
        "56518845",
        "56527482",
        "56541087",
        "56553722",
        "56557996",
        "56571979",
        "56575949",
        "56582621",
        "56582776",
    ]
    fractions = [
        versions[sid]["all"]["land_counts"].get("4", 0) / versions[sid]["all"]["games"]
        for sid in ids
    ]
    ax.bar(range(len(ids)), fractions, color="#526e9a")
    ax.set(
        ylim=(0, 1.22),
        ylabel="Fraction buying fourth quadrant",
        xticks=range(len(ids)),
        xticklabels=[sid[-5:] for sid in ids],
    )
    ax.tick_params(axis="x", rotation=45)
    ax.set_title(
        "DSM switched between distinct production plans\n"
        "Submission ID suffix; all collected recent games"
    )
    for i, sid in enumerate(ids):
        row = versions[sid]["all"]
        ax.text(i, fractions[i] + 0.04, f"n={row['games']}", ha="center", fontsize=8)

    ax = axes[1, 0]
    components: dict[str, float] = {
        item.title(): latest["own"]["products"][item]["net_cash"]
        - latest["opponent"]["products"][item]["net_cash"]
        for item in (
            "TOMATO",
            "WHEAT",
            "EGG",
            "FERTILIZER",
            "STRAWBERRY",
            "MILK",
            "WOOL",
            "CARROT",
            "MELON",
        )
    }
    components["Cost savings"] = sum(latest["opponent"]["costs"].values()) - sum(
        latest["own"]["costs"].values()
    )
    components["Final margin"] = latest["own"]["mean_margin"]
    ax.barh(
        list(components),
        list(components.values()),
        color=["#22866f" if v >= 0 else "#be5a53" for v in components.values()],
    )
    ax.invert_yaxis()
    ax.axvline(0, color="black", linewidth=0.7)
    ax.set_title(
        "Our latest three-land submissions: paired cash gaps\n"
        "55 games, 10 wins; purchases deducted from product cash"
    )
    ax.set_xlabel("Mean coins, ours minus opponent")
    ax.set_xlim(-4200, 6500)
    for i, value in enumerate(components.values()):
        ax.text(
            value + (100 if value >= 0 else -100),
            i,
            f"{value:+,.0f}",
            va="center",
            ha="left" if value >= 0 else "right",
            fontsize=9,
        )

    ax = axes[1, 1]
    groups: list[dict[str, Any]] = [yarn[str(i)]["own"] for i in range(3)]
    probability = np.array([row["win_rate"] for row in groups])
    intervals = np.array([row["win_rate_wilson95"] for row in groups])
    ax.bar(range(3), probability, color="#4c8b88")
    ax.errorbar(
        range(3),
        probability,
        yerr=np.stack((probability - intervals[:, 0], intervals[:, 1] - probability)),
        color="black",
        fmt="none",
        capsize=5,
    )
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=1)
    ax.set(
        xticks=range(3),
        xticklabels=["0 yarn shops", "1 yarn shop", "2+ yarn shops"],
        ylim=(0, 1.15),
        ylabel="Boey win rate vs DSM",
    )
    ax.set_title(
        "Boey's strength depends on the realized shop mix\nExploratory strata, 95% Wilson intervals"
    )
    for i, row in enumerate(groups):
        ax.text(
            i,
            1.04,
            f"{row['wins']}/{row['games']}\n{row['mean_margin']:+,.0f} coins",
            ha="center",
            va="center",
        )
    figure.suptitle("Kaggriculture replay study | collected September 25–27, 2026", fontsize=16)
    figure.savefig(output / "overview.png", dpi=160)
    figure.savefig(output / "overview.svg")
    plt.close(figure)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="replay_study")
def main(configuration: DictConfig) -> None:
    """Render audited summaries from the declared output directory."""
    settings = Study.model_validate(OmegaConf.to_container(configuration.analysis, resolve=True))
    plot(settings.output)


if __name__ == "__main__":
    main()
