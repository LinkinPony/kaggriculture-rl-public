"""Export standalone figures for teacher exposure and behavioral distribution changes."""

from pathlib import Path

import hydra
import matplotlib
import numpy as np
import orjson
from omegaconf import DictConfig

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402


def render(output: Path) -> None:
    """Keep sample exposure, observed production and sequence novelty distinct."""
    report = orjson.loads((output / "report.json").read_bytes())
    old, new = report["all"]["baseline"], report["all"]["current"]
    names = sorted(new["teachers"], key=lambda n: new["teachers"][n], reverse=True)
    names.append("Other old teachers")
    figure, axes = plt.subplots(1, 3, figsize=(19, 6), layout="constrained")
    colors = ("#64748b", "#0891b2")
    for index, (label, group) in enumerate((("Sep 14-16 (old)", old), ("Sep 16-20 (new)", new))):
        values = [group["teachers"].get(n, 0) for n in names[:-1]]
        values.append(group["trajectories"] - sum(values))
        axes[0].barh(
            np.arange(len(names)) + (index - 0.5) * 0.35,
            np.asarray(values) / group["trajectories"] * 100,
            height=0.35,
            color=colors[index],
            label=label,
        )
        products = ("WHEAT", "MELON", "STRAWBERRY", "COW", "SHEEP")
        axes[1].bar(
            np.arange(len(products)) + (index - 0.5) * 0.35,
            [group["snapshots"]["72"]["mean_assets"][p] for p in products],
            width=0.35,
            color=colors[index],
            label=label,
        )
    axes[0].set(
        yticks=range(len(names)),
        yticklabels=[n.replace(" 🍅", "") for n in names],
        xlabel="Share of teacher trajectories (%)",
        title="Teacher exposure: "
        f"{100 * report['all']['distances']['teachers']['total_variation']:.1f}% total variation",
    )
    axes[0].invert_yaxis()
    axes[1].legend(frameon=False, loc="upper right")
    axes[1].set(
        xticks=range(len(products)),
        xticklabels=[p.title() for p in products],
        ylabel="Mean deployed tiles / animals",
        title="Production after 72 turns",
    )
    axes[1].tick_params(axis="x", rotation=25)
    horizons = (1, 24, 72, 144)
    for channel, label, color in (
        ("units", "Unit requests", "#0891b2"),
        ("market", "Market requests", "#c2410c"),
    ):
        values = report["new_trajectories"]["unseen_prefix_fraction"]
        axes[2].plot(
            range(len(horizons)),
            [100 * values[f"{channel}:{t}"] for t in horizons],
            "o-",
            label=label,
            color=color,
        )
    axes[2].set(
        xticks=range(len(horizons)),
        xticklabels=horizons,
        ylim=(0, 100),
        xlabel="Opening length (turns)",
        ylabel="No exact match in old dataset (%)",
        title="Novel prefixes among "
        f"{report['new_trajectories']['current']['trajectories']:,} new trajectories",
    )
    axes[2].legend(frameon=False)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
    figure.savefig(output / "comparison.png", dpi=180)
    figure.savefig(output / "comparison.svg")
    plt.close(figure)


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="comparison_selected8_20260921",
)
def main(configuration: DictConfig) -> None:
    """Render only from the completed local comparison report."""
    render(Path(configuration.analysis.output))


if __name__ == "__main__":
    main()
