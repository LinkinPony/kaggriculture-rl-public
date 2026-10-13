"""Seed-cluster uncertainty for fixed-weight memory ablations."""

from typing import Any

import numpy as np

from kagg_revue.evaluation.comparison import paired_cash, paired_scores
from kagg_revue.evaluation.temperature.games import summary


def describe(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Add the terminal cash margin to direct WDL and cash summaries."""
    return {
        **summary(rows),
        "mean_cash_margin": float(np.mean([r["cash"] - r["opponent_cash"] for r in rows])),
    }


def compare(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare identical environment, seat, opponent and sampling-stream schedules."""
    panels = {mode: {"games": [r for r in rows if r["mode"] == mode]} for mode in ("on", "off")}
    margins = {
        mode: {"games": [{**r, "cash": r["cash"] - r["opponent_cash"]} for r in panel["games"]]}
        for mode, panel in panels.items()
    }
    return {
        "on": describe(panels["on"]["games"]),
        "off": describe(panels["off"]["games"]),
        "score_on_minus_off": paired_scores(panels["off"], panels["on"]),
        "cash_on_minus_off": paired_cash(panels["off"], panels["on"]),
        "margin_on_minus_off": paired_cash(margins["off"], margins["on"]),
    }


def report(rows: list[dict[str, Any]], opponents: tuple[str, ...]) -> dict[str, Any]:
    """Keep direct duels separate from the fixed native opponent panel."""
    scripts = [r for r in rows if r["mode"] != "duel"]
    duels = [r for r in rows if r["mode"] == "duel"]
    seeds = sorted({r["seed"] for r in duels})
    values = np.asarray(
        [
            [
                np.mean([(r["outcome"] + 1) / 2 for r in duels if r["seed"] == seed]),
                np.mean([r["cash"] - r["opponent_cash"] for r in duels if r["seed"] == seed]),
            ]
            for seed in seeds
        ]
    )
    indices = np.random.default_rng(0).integers(len(seeds), size=(4096, len(seeds)))
    intervals = np.quantile(values[indices].mean(1), [0.025, 0.975], axis=0)
    return {
        "scripts": compare(scripts),
        "opponents": {
            name: compare([r for r in scripts if r["opponent"] == name]) for name in opponents
        },
        "duels_on_vs_off": {
            **describe(duels),
            "independent_seeds": len(seeds),
            "score_seed_cluster_95_interval": intervals[:, 0].tolist(),
            "margin_seed_cluster_95_interval": intervals[:, 1].tolist(),
        },
        "scope": "Inference-time ablation of this single trained checkpoint. No retraining. "
        "Off clears history before every turn but preserves current-turn memory computations "
        "and all observation features. T=1 throughout. Intervals resample environment seeds, "
        "keeping seats and opponents together. Native panel results are not Kaggle-wide win rates.",
    }
