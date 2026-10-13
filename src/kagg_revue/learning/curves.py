"""Export paired online-budget curves from the common-opponent arena evidence."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import hydra
import matplotlib
import numpy as np
from omegaconf import DictConfig, OmegaConf
from pydantic import model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.comparison import paired_cash, paired_scores

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

from kagg_revue.learning.panels import render_opponents  # noqa: E402


class Curves(FrozenSettings):
    """One measured arena panel, exported without mixing opponents or seed roles."""

    source: Path
    output_dir: Path
    title: str = "Online learning against fixed internal neural opponents"
    labels: tuple[str, ...]

    @model_validator(mode="after")
    def validate_paths(self) -> "Curves":
        """Read measured results and write reproducible figures only under outputs."""
        for path in (self.source, self.output_dir):
            if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("outputs",):
                raise ValueError("learning curves use repository output artifacts")
        return self


def render(config: Curves) -> None:
    """Show paired score and cash differences with seed-cluster uncertainty."""
    arena = json.loads(config.source.read_text())
    runs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in arena["results"]:
        runs[record["run"]].append(record)
    if not runs or len(config.labels) != len(runs):
        raise ValueError("each measured run requires one distinct figure label")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    panels = (
        ("paired_initial_score", "mean_score_change", "Score change (percentage points)", 100),
        ("paired_initial_cash", "mean_cash_change", "Terminal cash change", 1),
    )
    increments = []
    for label, rows in zip(config.labels, runs.values(), strict=True):
        rows.sort(key=lambda row: row["update"])
        updates = [row["update"] for row in rows]
        if len(set(updates)) != len(updates) or updates[0] != 0:
            raise ValueError("figure requires unique measured budgets including the RL control")
        for previous, current in zip(rows, rows[1:], strict=False):
            increments.append(
                {
                    "run": current["run"],
                    "from_update": previous["update"],
                    "to_update": current["update"],
                    "from_sha256": previous["checkpoint_sha256"],
                    "to_sha256": current["checkpoint_sha256"],
                    "score": paired_scores(previous, current),
                    "cash": paired_cash(previous, current),
                }
            )
        for axis, (metric, key, title, scale) in zip(axes, panels, strict=True):
            values = np.asarray([row[metric][key] for row in rows]) * scale
            limits = (
                np.asarray([row[metric]["seed_cluster_bootstrap_95_interval"] for row in rows])
                * scale
            )
            (line,) = axis.plot(updates, values, marker="o", label=label, linewidth=1.8)
            axis.fill_between(
                updates, limits[:, 0], limits[:, 1], color=line.get_color(), alpha=0.15
            )
            axis.set(xlabel="PPO update", ylabel=title)
            axis.axhline(0, linewidth=0.8, color="grey", linestyle="--")
            axis.grid(axis="y", alpha=0.2)
            axis.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False)
    figure.suptitle(config.title, fontsize=12)
    figure.supxlabel(
        "Changes relative to each run's fixed RL initial control. "
        "Shading: 95% seed-cluster bootstrap intervals.\n"
        "Internal opponents; this figure does not establish external competitive strength.",
        fontsize=8,
    )
    for extension in ("png", "svg", "pdf"):
        figure.savefig(config.output_dir / f"curves.{extension}", dpi=180)
    plt.close(figure)
    opponent_artifacts = render_opponents(arena, runs, config.labels, config.output_dir)
    write_json(
        config.output_dir / "incremental.json",
        {
            "source_sha256": digest(config.source),
            "results": increments,
            "scope": "Adjacent declared budgets on the same panel; intervals are pointwise, "
            "not simultaneous guarantees across the whole curve.",
        },
    )
    write_json(
        config.output_dir / "manifest.json",
        {
            "configuration": config.model_dump(mode="json"),
            "source_sha256": digest(config.source),
            "opponent_sha256": arena["opponent_sha256"],
            "seed_role": arena["configuration"]["role"],
            "opponent_artifacts": opponent_artifacts,
            "figures": {
                extension: digest(config.output_dir / f"curves.{extension}")
                for extension in ("png", "svg", "pdf")
            },
        },
    )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="learning_curves",
)
def main(configuration: DictConfig) -> None:
    """Resolve the measured panel and figure labels before exporting artifacts."""
    render(Curves.model_validate(OmegaConf.to_container(configuration.curves, resolve=True)))


if __name__ == "__main__":
    main()
