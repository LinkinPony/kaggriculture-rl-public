"""Validate additive diagnostics and plot the main strategic evidence."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.evaluation.diagnosis.imitation import Options


def paired(directory: Path) -> dict[str, Any]:
    """Bootstrap environment seeds, retaining both teacher seats of the same game."""
    models = {
        model: {
            (row["episode_id"], row["teacher"]["seat"]): row
            for row in (
                json.loads(line) for line in (directory / f"{model}.jsonl").read_text().splitlines()
            )
        }
        for model in ("bc", "ppo")
    }
    if models["bc"].keys() != models["ppo"].keys():
        raise ValueError("the actors were not scored on the same validation trajectories")
    output = {}
    for metric in (
        "unit_target",
        "market_operation",
        "market_quantity",
        "market/BUY_ANIMAL:GOOSE",
        "market/BUY_ANIMAL:COW",
        "market/BUY_ANIMAL:SHEEP",
        "market/BUY_LAND",
    ):
        clusters: dict[int, np.ndarray[Any, Any]] = defaultdict(lambda: np.zeros(5))
        for key, old in models["bc"].items():
            new = models["ppo"][key]
            a, b = np.asarray(old["totals"][metric]), np.asarray(new["totals"][metric])
            if a[0] != b[0] or not np.isfinite([a, b]).all():
                raise ValueError("conditional metric populations or finite checks disagree")
            clusters[old["seed"]] += np.array([a[0], *(b[1:] - a[1:])])
        values = np.stack(list(clusters.values()))
        rng = np.random.default_rng(92852)
        draws = values[rng.integers(len(values), size=(4096, len(values)))].sum(1)
        valid = draws[:, 0] > 0
        ratios = draws[valid, 1:] / draws[valid, :1]
        estimate = values[:, 1:].sum(0) / values[:, 0].sum()
        output[metric] = {
            "count": int(values[:, 0].sum()),
            "environment_seeds": len(values),
            "ppo_minus_bc": {
                name: {
                    "estimate": float(estimate[index]),
                    "ci95": np.quantile(ratios[:, index], [0.025, 0.975]).tolist(),
                }
                for index, name in enumerate(("nll", "accuracy", "teacher_probability", "entropy"))
            },
        }
    return output


def figure(output: Path) -> None:
    """Export a standalone figure from the final immutable reports."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    imitation = json.loads((output / "imitation/report.json").read_text())
    census = json.loads((output / "imitation/census.json").read_text())["splits"]["train"]
    replays = json.loads((output / "replays/report.json").read_text())["all"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), constrained_layout=True)
    boey = census["teachers"]["Boey"]
    shares = [
        boey["trajectories"] / census["trajectories"],
        boey["market_operation_domain_share"],
        boey["market_quantity_domain_share"],
    ]
    axes[0].bar(
        ["Trajectories", "Market op.\nloss weight", "Market qty.\nloss weight"],
        np.array(shares) * 100,
        color=["#587f9d", "#d28b48", "#bd6449"],
    )
    axes[0].set(title="Boey exposure in BC", ylabel="Share (%)", ylim=(0, 65))
    for index, value in enumerate(shares):
        axes[0].text(index, value * 100 + 1, f"{value:.1%}", ha="center")
    names = ["GOOSE", "COW", "SHEEP"]
    for index, model in enumerate(("bc", "ppo")):
        values = [
            imitation["models"][model]["all"][f"market/BUY_ANIMAL:{name}"]["teacher_probability"]
            for name in names
        ]
        axes[1].bar(
            np.arange(3) + (index - 0.5) * 0.34,
            np.array(values) * 100,
            width=0.34,
            label=model.upper(),
            color=["#587f9d", "#d28b48"][index],
        )
    axes[1].set(
        xticks=np.arange(3),
        xticklabels=names,
        ylim=(0, 100),
        title="Probability of teacher animal purchase",
        ylabel="Mean probability (%)",
    )
    axes[1].legend(frameon=False)
    names = ["WHEAT", "EGG", "MILK", "TOMATO"]
    values = [replays["products"][name]["net_cash_gap"] for name in names]
    axes[2].bar(names, values, color=["#bd6449" if value < 0 else "#608f6f" for value in values])
    axes[2].axhline(0, color="#777777", linewidth=0.8)
    axes[2].set(title="38 official games: selected cash gaps", ylabel="Ours minus opponent")
    for axis in axes:
        axis.spines[["right", "top"]].set_visible(False)
    fig.suptitle("2026-09-28 diagnosis | BC/PPO: s97001 U472 | Official games: s95001", fontsize=13)
    fig.savefig(output / "overview.png", dpi=180)
    fig.savefig(output / "overview.svg")
    plt.close(fig)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="diagnosis_imitation")
def main(config: DictConfig) -> None:
    """Require exact validation label counts before publishing comparisons."""
    options = Options.model_validate(OmegaConf.to_container(config.analysis, resolve=True))
    census = json.loads((options.output / "census.json").read_text())["splits"]["val"]["teachers"]
    report = json.loads((options.output / "report.json").read_text())
    for result in report["models"].values():
        for name, teacher in census.items():
            measured = result["by_teacher"][name]
            if sum(teacher["counts"].values()) != measured["market_operation"]["count"]:
                raise ValueError("label census disagrees with the actor's actual field mask")
            for operation, count in teacher["counts"].items():
                if count != measured.get(f"market/{operation}", {}).get("count", 0):
                    raise ValueError("operation census disagrees with conditional inference")
    write_json(options.output / "paired.json", paired(options.output))
    figure(options.output.parent)


if __name__ == "__main__":
    main()
