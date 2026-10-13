"""Expose fixed-opponent strata behind an aggregate learning curve."""

from pathlib import Path
from typing import Any

import numpy as np
from matplotlib import pyplot as plt

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.comparison import paired_cash, paired_scores


def render_opponents(
    arena: dict[str, Any],
    runs: dict[str, list[dict[str, Any]]],
    labels: tuple[str, ...],
    output_dir: Path,
) -> dict[str, str]:
    """Plot observed scores and record paired uncertainty for each frozen opponent.

    Opponent order and identities come from the measured arena, without choosing
    a subset after seeing the results. Intervals in the evidence retain both
    seats of each environment seed; they are pointwise within this fixed panel.
    """
    opponents = arena["opponent_sha256"]
    specifications = arena["configuration"]["opponents"]
    if not opponents or len(opponents) != len(specifications):
        raise ValueError("opponent identities must match the declared arena panel")
    figure, axes = plt.subplots(
        (len(opponents) + 1) // 2,
        2,
        figsize=(10, 3.4 * ((len(opponents) + 1) // 2)),
        squeeze=False,
        layout="constrained",
    )
    records = []
    for axis, sha, specification in zip(axes.flat, opponents, specifications, strict=False):
        for label, rows in zip(labels, runs.values(), strict=True):
            initial = previous = None
            scores = []
            for row in rows:
                games = [game for game in row["games"] if game["opponent"] == sha]
                if not games:
                    raise ValueError("each budget must contain every declared opponent")
                point = {"games": games}
                initial = point if initial is None else initial
                score = float(np.mean([(game["outcome"] + 1) / 2 for game in games]))
                scores.append(score * 100)
                record = {
                    "run": row["run"],
                    "update": row["update"],
                    "checkpoint_sha256": row["checkpoint_sha256"],
                    "opponent_sha256": sha,
                    "opponent": specification,
                    "games": len(games),
                    "independent_seeds": len({game["seed"] for game in games}),
                    "mean_score": score,
                    "mean_cash": float(np.mean([game["cash"] for game in games])),
                    "paired_initial_score": paired_scores(initial, point),
                    "paired_initial_cash": paired_cash(initial, point),
                }
                if previous is not None:
                    record["paired_previous_score"] = paired_scores(previous, point)
                    record["paired_previous_cash"] = paired_cash(previous, point)
                    record["previous_update"] = previous["update"]
                records.append(record)
                previous = {**point, "update": row["update"]}
            axis.plot(
                [row["update"] for row in rows], scores, marker="o", label=label, linewidth=1.8
            )
        opponent_run = Path(specification["run"]).name
        opponent_member = Path(specification["member"]).stem
        axis.set(
            title=f"{opponent_run}\n{opponent_member} / {sha[:12]}",
            xlabel="PPO update",
            ylabel="Observed score (%)",
            ylim=(-2, 102),
        )
        axis.axhline(50, linewidth=0.8, color="grey", linestyle="--")
        axis.grid(axis="y", alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
    for axis in list(axes.flat)[len(opponents) :]:
        axis.set_visible(False)
    axes.flat[0].legend(frameon=False)
    figure.suptitle("Learning against each fixed opponent", fontsize=13)
    figure.supxlabel(
        "All declared opponents shown separately. Observed WDL scores on paired seeds.\n"
        "Pointwise seed-cluster intervals for changes are in opponent-panels.json; "
        "no unseen-opponent guarantee.",
        fontsize=8,
    )
    paths = []
    for extension in ("png", "svg", "pdf"):
        path = output_dir / f"opponent-curves.{extension}"
        figure.savefig(path, dpi=180)
        paths.append(path)
    plt.close(figure)
    path = output_dir / "opponent-panels.json"
    write_json(
        path,
        {
            "opponent_sha256": opponents,
            "results": records,
            "scope": "All fixed opponent strata; paired intervals are pointwise, "
            "not simultaneous or unseen-opponent uncertainty.",
        },
    )
    paths.append(path)
    return {path.name: digest(path) for path in paths}
