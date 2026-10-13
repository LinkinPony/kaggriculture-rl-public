"""Summarize passive public-game accounting and export mean cash trajectories."""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import hydra
import matplotlib
import numpy as np
from omegaconf import DictConfig, OmegaConf
from pydantic import model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.comparison import paired_cash

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402


class AccountingReport(FrozenSettings):
    """Read one completed measured panel and preserve its seed and opponent roles."""

    source: Path
    output_dir: Path

    @model_validator(mode="after")
    def validate_paths(self) -> "AccountingReport":
        """Keep generated analysis in the repository output tree."""
        for path in (self.source, self.output_dir):
            if (
                path.is_absolute()
                or ".." in path.parts
                or path.parts[:2] != ("outputs", "analysis")
            ):
                raise ValueError("accounting reports belong under outputs/analysis")
        return self


def _mean_players(players: list[dict[str, Any]]) -> dict[str, Any]:
    scalar_keys = (
        "initial_cash",
        "terminal_cash",
        "sales_revenue",
        "market_expenditure",
        "nonmarket_cash_delta",
        "unit_turns",
        "plant_tile_turns",
        "animal_tile_turns",
        "uncollected_yield_turns",
    )
    result: dict[str, Any] = {
        key: float(np.mean([player[key] for player in players])) for key in scalar_keys
    }
    for key in (
        "revenue_by_item",
        "expenditure_by_order",
        "committed_quantities",
        "market_status",
        "submitted_unit_actions",
    ):
        counts: Counter[str] = Counter()
        for player in players:
            counts.update(player[key])
        result[key] = {name: value / len(players) for name, value in sorted(counts.items())}
    steps = [point["step"] for point in players[0]["timeline"]]
    if any([point["step"] for point in player["timeline"]] != steps for player in players):
        raise ValueError("accounting snapshots have inconsistent step boundaries")
    result["mean_cash_trajectory"] = [
        {"step": step, "cash": float(np.mean([p["timeline"][i]["cash"] for p in players]))}
        for i, step in enumerate(steps)
    ]
    return result


def render(config: AccountingReport) -> None:
    """Show observed financial differences without attributing them to a causal fix."""
    source = json.loads(config.source.read_text())
    records = []
    by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in source["results"]:
        if not record["games"] or any(
            not g["accounting"]["cash_reconciled"] for g in record["games"]
        ):
            raise ValueError("accounting requires nonempty reconciled game records")
        summary = {key: record[key] for key in ("run", "run_id", "update", "checkpoint_sha256")}
        summary["games"] = len(record["games"])
        summary["independent_seeds"] = len({g["seed"] for g in record["games"]})
        for role, offset in (("candidate", 0), ("opponent", 1)):
            players = [g["accounting"]["players"][g["seat"] ^ offset] for g in record["games"]]
            summary[role] = _mean_players(players)
        opponent = {"games": [{**g, "cash": g["opponent_cash"]} for g in record["games"]]}
        summary["paired_cash_relative_to_opponent"] = paired_cash(opponent, record)
        summary["cash_gap_components"] = {
            key: summary["candidate"][key] - summary["opponent"][key]
            for key in (
                "initial_cash",
                "sales_revenue",
                "market_expenditure",
                "nonmarket_cash_delta",
            )
        }
        records.append(summary)
        by_run[summary["run"]].append(summary)
    if not records:
        raise ValueError("accounting report has no measured budgets")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(
        1, len(by_run), figsize=(6 * len(by_run), 4.5), squeeze=False, layout="constrained"
    )
    for axis, (run, rows) in zip(axes[0], by_run.items(), strict=True):
        colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        for index, row in enumerate(sorted(rows, key=lambda row: row["update"])):
            color = colors[index % len(colors)]
            for role, style in (("candidate", "-"), ("opponent", "--")):
                trajectory = row[role]["mean_cash_trajectory"]
                axis.plot(
                    [p["step"] for p in trajectory],
                    [p["cash"] for p in trajectory],
                    color=color,
                    linestyle=style,
                    label=f"RL {row['update']}: {role}",
                )
        axis.set(title=Path(run).name, xlabel="Official step", ylabel="Mean cash")
        axis.legend(frameon=False, fontsize=8)
        axis.grid(axis="y", alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("Complete public-opponent games: cash trajectories")
    figure.supxlabel(
        f"Same measured {source['configuration']['role']} games; means without interval bands. "
        "Public-opponent cash can change with candidate actions.",
        fontsize=8,
    )
    for extension in ("png", "svg", "pdf"):
        figure.savefig(config.output_dir / f"cash-trajectories.{extension}", dpi=180)
    plt.close(figure)
    write_json(
        config.output_dir / "summary.json",
        {
            "configuration": config.model_dump(mode="json"),
            "source_sha256": digest(config.source),
            "seed_role": source["configuration"]["role"],
            "results": records,
            "figures": {
                extension: digest(config.output_dir / f"cash-trajectories.{extension}")
                for extension in ("png", "svg", "pdf")
            },
            "scope": "Observed mean per-seat accounting on the source panel. Cash differences "
            "equal initial cash plus sales minus expenditure plus nonmarket changes. Production "
            "counts and submitted actions do not establish a causal intervention "
            "or new strength evidence.",
        },
    )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="learning_accounting",
)
def main(configuration: DictConfig) -> None:
    """Resolve passive analysis inputs and export their measured financial summaries."""
    render(
        AccountingReport.model_validate(
            OmegaConf.to_container(configuration.accounting, resolve=True)
        )
    )


if __name__ == "__main__":
    main()
