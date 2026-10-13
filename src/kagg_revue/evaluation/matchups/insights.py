"""Summarize audited multi-team games without treating matchmaking as random."""

import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

import hydra
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.evaluation.matchups.duels import _ledger
from kagg_revue.evaluation.matchups.study import Study

TEAMS = ("DSM", "M & M & P & Q", "DECEM", "Boey", "Vadim Vasilenko", "Unknown Mother-Goose")
ITEMS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
ASSETS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "COW", "GOOSE", "SHEEP")


def load_rows(directory: Path) -> list[dict[str, Any]]:
    """Read completed lines so partial progress can also be explored safely."""
    rows = []
    for line in (directory / "features.jsonl").read_bytes().splitlines(keepends=True):
        if line.endswith(b"\n"):
            rows.append(orjson.loads(line))
    return rows


def outcome(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Report empirical WDL and interval estimates at the episode level."""
    if not rows:
        return {"games": 0}
    count = len(rows)
    wins = sum(row["result"] > 0 for row in rows)
    probability = wins / count
    denominator = 1 + 1.96**2 / count
    center = (probability + 1.96**2 / (2 * count)) / denominator
    radius = (
        1.96
        / denominator
        * math.sqrt(probability * (1 - probability) / count + 1.96**2 / (4 * count**2))
    )
    margins = np.array([row["margin"] for row in rows])
    rng = np.random.default_rng(20260927)
    resamples = rng.choice(margins, (2000, count)).mean(axis=1)
    return {
        "games": count,
        "wins": wins,
        "draws": sum(row["result"] == 0 for row in rows),
        "losses": sum(row["result"] < 0 for row in rows),
        "win_rate": probability,
        "win_rate_wilson95": [center - radius, center + radius],
        "mean_margin": mean(row["margin"] for row in rows),
        "median_margin": median(row["margin"] for row in rows),
        "mean_margin_bootstrap95": np.quantile(resamples, [0.025, 0.975]).tolist(),
        "mean_cash": mean(row["cash"] for row in rows),
        "median_cash": median(row["cash"] for row in rows),
    }


def profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe realized operations, investment, inventory and product cash flows."""
    if not rows:
        return {"games": 0}
    operations = sum((Counter(row["operations"]) for row in rows), Counter())
    products = {}
    for item in ITEMS:
        products[item] = {
            "quantity": mean(
                row["ledger"].get(f"SELL:{item}", {}).get("quantity", 0) for row in rows
            ),
            "gross_cash": mean(
                row["ledger"].get(f"SELL:{item}", {}).get("cash", 0) for row in rows
            ),
            "purchase_quantity": mean(
                row["ledger"].get(f"BUY_PRODUCT:{item}", {}).get("quantity", 0) for row in rows
            ),
            "net_cash": mean(
                sum(
                    row["ledger"].get(f"{op}:{item}", {}).get("cash", 0)
                    for op in ("SELL", "BUY_PRODUCT")
                )
                for row in rows
            ),
            "harvested": mean(row["harvested"].get(item, 0) for row in rows),
            "overflow": mean(row["overflow"].get(item, 0) for row in rows),
            "floor_quantity_lower_bound": mean(
                row["timing"].get(item, {}).get("floor_quantity", 0) for row in rows
            ),
            "end_stock": mean(row["end_stock"].get(item, 0) for row in rows),
        }
    costs = {}
    for operation in ("HIRE", "BUY_LAND", "BUY_SEED", "BUY_ANIMAL"):
        costs[operation] = mean(
            -sum(
                value["cash"]
                for key, value in row["ledger"].items()
                if key.split(":")[0] == operation
            )
            for row in rows
        )
    if (
        abs(
            sum(p["net_cash"] for p in products.values())
            - sum(costs.values())
            + 3000
            - mean(row["cash"] for row in rows)
        )
        > 1e-6
    ):
        raise ValueError("net product revenue does not reconcile with costs and final cash")
    return {
        **outcome(rows),
        "submissions": dict(Counter(str(row["submission"]) for row in rows)),
        "land_counts": dict(Counter(str(len(row["board"]["first_land_turn"])) for row in rows)),
        "se_turn_median": median(
            row["board"]["first_land_turn"]["SE"]
            for row in rows
            if "SE" in row["board"]["first_land_turn"]
        )
        if any("SE" in row["board"]["first_land_turn"] for row in rows)
        else None,
        "products": products,
        "costs": costs,
        "operations_per_game": {key: count / len(rows) for key, count in operations.items()},
        "pass_rate": operations["PASS"] / sum(operations.values()),
        "illegal_per_game": mean(row["invalid"].get("illegal", 0) for row in rows),
        "overflow_per_game": mean(sum(row["overflow"].values()) for row in rows),
        "asset_tile_days": {
            item: mean(row["board"]["asset_tile_days"].get(item, 0) for row in rows)
            for item in ASSETS
        },
        "animal_purchases_by_3day_window": {
            asset: {
                str(start): mean(
                    sum(
                        row["daily"][str(day)]["purchases"].get(f"BUY_ANIMAL:{asset}", [0])[0]
                        for day in range(start, start + 3)
                    )
                    for row in rows
                )
                for start in range(0, 30, 3)
            }
            for asset in ("COW", "GOOSE", "SHEEP")
        },
        "assets_by_day": {
            str(day): {
                item: mean(row["snapshots"][str(day)]["assets"].get(item, 0) for row in rows)
                for item in ASSETS
            }
            for day in (1, 3, 6, 9, 12, 15, 18, 21, 24, 27, 29)
        },
        "cash_by_day": {
            str(day): mean(row["cash_curve"][min(day * 24, 719)] for row in rows)
            for day in range(31)
        },
    }


def paired(
    rows: list[dict[str, Any]], index: dict[tuple[int, int], dict[str, Any]]
) -> dict[str, Any]:
    """Keep opponents' revenue and production on the same realized world."""
    others = [index[row["episode_id"], 1 - row["seat"]] for row in rows]
    ledger = _ledger(rows, others)
    if (
        rows
        and abs(
            sum(entry["cash_gap"] for entry in ledger.values())
            - mean(row["margin"] for row in rows)
        )
        > 1e-6
    ):
        raise ValueError("within-game accounting does not reconcile")
    return {
        "own": profile(rows),
        "opponent": profile(others),
        "ledger": ledger,
        "episode_ids": [row["episode_id"] for row in rows],
    }


def run(config: Study) -> None:
    """Publish complete paired comparisons and version-specific descriptive profiles."""
    all_rows = load_rows(config.output)
    rows = [row for row in all_rows if row["recent_game"] and row["name"] != row["opponent"]]
    index = {(row["episode_id"], row["seat"]): row for row in all_rows}
    focused = [row for row in rows if row["submission"] in config.focus_submissions]
    write_json(config.output / "latest-paired.json", paired(focused, index))
    boey = [row for row in rows if row["name"] == "Boey" and row["opponent"] == "DSM"]
    write_json(
        config.output / "boey-yarn-strata.json",
        {
            str(count): paired(
                [row for row in boey if min(row["shops"].count("YARN_STORE"), 2) == count],
                index,
            )
            for count in range(3)
        },
    )
    teams = {}
    versions: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for name in TEAMS:
        selected = [row for row in rows if row["name"] == name]
        teams[name] = {
            "all": profile(selected),
            "watched": profile([row for row in selected if row["opponent"] in TEAMS]),
        }
        for row in selected:
            versions[row["submission"]].append(row)
    pairs = {}
    for name in TEAMS:
        for opponent in TEAMS:
            if name == opponent:
                continue
            selected = [row for row in rows if row["name"] == name and row["opponent"] == opponent]
            if selected:
                pairs[f"{name} / {opponent}"] = paired(selected, index)
    write_json(
        config.output / "insights.json",
        {
            "teams": teams,
            "versions": {
                str(key): {
                    "name": group[0]["name"],
                    "all": profile(group),
                    "watched": profile([row for row in group if row["opponent"] in TEAMS]),
                }
                for key, group in versions.items()
            },
            "pairs": pairs,
            "scope": "Descriptive associations from observed matchups; version, seed and opponent "
            "mix differ. Confidence intervals assume independent games and do not correct "
            "matchmaking selection, submission clustering or exploratory multiple comparisons.",
        },
    )


@hydra.main(version_base=None, config_path="../../../../configs", config_name="replay_study")
def main(configuration: DictConfig) -> None:
    """Resolve the frozen study settings for offline statistical summaries."""
    run(Study.model_validate(OmegaConf.to_container(configuration.analysis, resolve=True)))


if __name__ == "__main__":
    main()
