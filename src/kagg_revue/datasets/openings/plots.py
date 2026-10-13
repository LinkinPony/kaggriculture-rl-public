"""Standalone figures for the opening EDA, with authenticated input identities."""

from collections import Counter
from pathlib import Path

import hydra
import matplotlib
import numpy as np
import orjson
from omegaconf import DictConfig

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.openings.comparisons import cohorts, compare
from kagg_revue.datasets.openings.statistics import asset_key
from kagg_revue.native.features import Layout

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402


def label(key: str) -> str:
    """Use production counts instead of opaque hashes as legend labels."""
    assets = orjson.loads(key)
    return ", ".join(f"{n} {k.lower()}" for k, n in assets.items() if n)


def render(output: Path) -> None:
    """Plot source coverage; do not present observed replay WDL as policy strength."""
    rows = [
        orjson.loads(line) for line in (output / "trajectories.jsonl").read_bytes().splitlines()
    ]
    report = orjson.loads((output / "report.json").read_bytes())
    groups = cohorts(rows)
    keys = list(groups)
    colors = ["#52606d", "#2b8cbe", "#41ab5d", "#e08214"]
    figure, axes = plt.subplots(1, 3, figsize=(18, 5.8), layout="constrained")
    horizons = (1, 4, 12, 24, 48, 72, 144)
    for (name, group), color in zip(groups.items(), colors, strict=True):
        values = [
            max(Counter(r["prefixes"]["units"][str(h)] for r in group).values()) / len(group)
            for h in horizons
        ]
        axes[0].plot(range(len(horizons)), 100 * np.asarray(values), "o-", color=color, label=name)
    axes[0].set(
        xticks=range(len(horizons)),
        xticklabels=horizons,
        ylabel="Share (%)",
        xlabel="Opening turns",
        title="Most common exact unit sequence",
    )
    axes[0].legend(frameon=False)
    # Give each source cohort equal influence over legend selection.
    family_mass: Counter[str] = Counter()
    for group in groups.values():
        family_mass.update(
            {key: n / len(group) for key, n in Counter(asset_key(r) for r in group).items()}
        )
    families = [key for key, _ in family_mass.most_common(5)]
    bottom = np.zeros(len(keys))
    family_colors = ["#2369a0", "#72b7b2", "#e5a243", "#a775b5", "#dd6b65", "#c9cdd2"]
    for index, family in enumerate([*families, "Other"]):
        shares = np.asarray(
            [
                100
                * sum(
                    asset_key(r) == family if family != "Other" else asset_key(r) not in families
                    for r in groups[key]
                )
                / len(groups[key])
                for key in keys
            ]
        )
        axes[1].bar(
            keys,
            shares,
            bottom=bottom,
            color=family_colors[index],
            label=label(family) if family != "Other" else family,
        )
        bottom += shares
    axes[1].set(ylabel="Share (%)", title="Production composition after 24 turns")
    axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), frameon=False, fontsize=8)
    comparisons = compare(rows, 1)
    for index, operation in enumerate(("BUY_ANIMAL", "BUY_SEED", "HIRE")):
        values = [
            100
            * comparisons["cohorts"][key]["shortfalls24"]["by_operation"][operation]["trajectories"]
            / len(groups[key])
            for key in keys
        ]
        axes[2].bar(
            np.arange(len(keys)) + (index - 1) * 0.25,
            values,
            width=0.25,
            label=operation,
            color=family_colors[index],
        )
    axes[2].set(
        xticks=range(len(keys)),
        xticklabels=keys,
        ylabel="Affected trajectories (%)",
        title="Small purchase shortfalls in first 24 turns",
    )
    axes[2].legend(frameon=False)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.15)
        if ax != axes[0]:
            ax.tick_params(axis="x", rotation=20)
    figure.suptitle(
        "Actual BC training seats vs Sep 13-15 historical-teacher daily seats", fontsize=15
    )
    for extension in ("png", "svg"):
        figure.savefig(output / f"opening-coverage.{extension}", dpi=160)
    plt.close(figure)
    stored = orjson.loads((output / "validation-protocol.json").read_bytes())["layout"]
    layout = Layout(**stored["observation"])
    factors = layout.units * 8 + layout.markets * 2
    # float16 features, int16 labels/origins, bool quantity coverage; no optional weights.
    comparisons = compare(rows, 2 * layout.features + 2 * factors + 4 + 1)
    comparisons["provenance"] = {
        "inputs": {
            name: digest(output / name)
            for name in ("trajectories.jsonl", "report.json", "validation-protocol.json")
        },
        "sources": {
            name: digest(Path(__file__).with_name(name)) for name in ("plots.py", "comparisons.py")
        },
        "checked_observations": report["checked_observations"],
    }
    write_json(output / "comparisons.json", comparisons)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="opening_analysis",
)
def main(configuration: DictConfig) -> None:
    """Render the completed source audit using the same Hydra output setting."""
    render(Path(configuration.analysis.output))


if __name__ == "__main__":
    main()
