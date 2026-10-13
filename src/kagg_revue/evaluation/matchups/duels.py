"""Summarize audited direct games across explicitly identified policy versions."""

from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.openings.extraction import load
from kagg_revue.evaluation.matchups.extraction import extract
from kagg_revue.evaluation.matchups.figures import plot_duels


class Diagnosis(FrozenSettings):
    """Bind a frozen replay selection and groups without changing any policy."""

    manifest: Path
    output: Path
    groups: dict[str, list[int]]


def board_metrics(task: dict[str, Any], result: dict[str, Any]) -> list[dict[str, Any]]:
    """Measure land use and asset exposure from the authenticated replay states."""
    if digest(Path(task["path"])) != task["sha256"]:
        raise ValueError("replay fingerprint differs from the frozen selection")
    replay, raw_hash = load(task)
    if result["raw_sha256"] != raw_hash or result["episode_id"] != task["episode_id"]:
        raise ValueError("audited accounting belongs to a different replay")
    rows = []
    for seat in (0, 1):
        first_land: dict[str, int] = {}
        productive_turns: Counter[str] = Counter()
        asset_turns: Counter[str] = Counter()
        overage = []
        for turn, frame in enumerate(replay["steps"]):
            obs = frame[seat]["observation"]
            farm = obs["farms"][seat]
            overage.append(obs["remainingOverageTime"])
            for quadrant in farm["unlocked_quadrants"]:
                first_land.setdefault(quadrant, turn)
            if turn == len(replay["steps"]) - 1:
                continue
            midpoint = len(farm["tiles"]) // 2
            for y, tiles in enumerate(farm["tiles"]):
                for x, tile in enumerate(tiles):
                    if not isinstance(tile, dict):
                        continue
                    name = tile.get("crop") or tile.get("animal")
                    if name:
                        quadrant = ("N" if y < midpoint else "S") + ("W" if x < midpoint else "E")
                        productive_turns[quadrant] += 1
                        asset_turns[name] += 1
        rows.append(
            {
                "first_land_turn": first_land,
                "productive_tile_turns": dict(productive_turns),
                "asset_tile_days": {k: v / 24 for k, v in asset_turns.items()},
                "minimum_overage_seconds": min(overage),
            }
        )
    return rows


def _side(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate realized production and usage, leaving quantities in their units."""
    count = len(rows)
    operations = sum((Counter(row["operations"]) for row in rows), Counter())
    output: dict[str, Any] = {
        "mean_terminal_cash": mean(row["cash"][-1] for row in rows),
        "adjusted_unit_requests": sum(len(row["invalid_units"]) for row in rows),
        "illegal_unit_requests": sum(
            entry["status"] == "illegal" for row in rows for entry in row["invalid_units"]
        ),
        "pass_fraction": operations["PASS"] / sum(operations.values()),
        "minimum_overage_seconds": min(row["board"]["minimum_overage_seconds"] for row in rows),
        "se_unlocked_games": sum("SE" in row["board"]["first_land_turn"] for row in rows),
        "se_productive_games": sum(
            row["board"]["productive_tile_turns"].get("SE", 0) > 0 for row in rows
        ),
    }
    for field in ("harvested", "overflow"):
        total = sum((Counter(row[field]) for row in rows), Counter())
        output[f"mean_{field}"] = {key: value / count for key, value in total.items()}
    total = sum((Counter(row["board"]["asset_tile_days"]) for row in rows), Counter())
    output["mean_asset_tile_days"] = {key: value / count for key, value in total.items()}
    output["mean_se_unlock_turn"] = (
        mean(
            row["board"]["first_land_turn"]["SE"]
            for row in rows
            if "SE" in row["board"]["first_land_turn"]
        )
        if output["se_unlocked_games"]
        else None
    )
    return output


def _ledger(ours: list[dict[str, Any]], opponents: list[dict[str, Any]]) -> dict[str, Any]:
    """Split sales gaps arithmetically into quantity and realized-price components.

    For each game use the symmetric identity d(QP) = dQ * mean(P) + dP * mean(Q).
    A missing sale uses the other side's price, assigning its gap to quantity.
    These are accounting terms, not counterfactual effects of changing production.
    """
    keys = sorted({key for row in [*ours, *opponents] for key in row["ledger"]})
    output = {}
    for key in keys:
        quantities, cash = [], []
        for group in (ours, opponents):
            quantities.append([row["ledger"].get(key, {}).get("quantity", 0) for row in group])
            cash.append([row["ledger"].get(key, {}).get("cash", 0) for row in group])
        item: dict[str, Any] = {
            "mean_quantity": [mean(values) for values in quantities],
            "mean_cash": [mean(values) for values in cash],
            "cash_gap": mean(cash[0]) - mean(cash[1]),
            "lower_quantity_games": sum(a < b for a, b in zip(*quantities, strict=True)),
            "lower_revenue_games": sum(a < b for a, b in zip(*cash, strict=True)),
            "pooled_unit_price": [
                abs(sum(c) / sum(q)) if sum(q) else None
                for q, c in zip(quantities, cash, strict=True)
            ],
        }
        if key.startswith("SELL:"):
            volume, price = [], []
            for qa, qb, ra, rb in zip(*quantities, *cash, strict=True):
                pa = ra / qa if qa else (rb / qb if qb else 0)
                pb = rb / qb if qb else pa
                volume.append((qa - qb) * (pa + pb) / 2)
                price.append((pa - pb) * (qa + qb) / 2)
            item.update(quantity_component=mean(volume), price_component=mean(price))
            if abs(item["quantity_component"] + item["price_component"] - item["cash_gap"]) > 1e-6:
                raise ValueError("quantity/price identity does not reconcile")
        output[key] = item
    return output


def summarize(results: list[dict[str, Any]], submissions: list[int]) -> dict[str, Any]:
    """Keep within-game comparisons together, including both seats and all outcomes."""
    games, ours, opponents = [], [], []
    for result in results:
        own = [row for row in result["players"] if row["submission_id"] in submissions]
        if not own:
            continue
        if len(own) != 1:
            raise ValueError("direct opponent analysis requires exactly one selected seat")
        games.append(result)
        ours.append(own[0])
        opponents.append(result["players"][1 - own[0]["seat"]])
    if not games:
        return {"games": 0}
    margins = [a["cash"][-1] - b["cash"][-1] for a, b in zip(ours, opponents, strict=True)]
    ledger = _ledger(ours, opponents)
    if abs(sum(row["cash_gap"] for row in ledger.values()) - mean(margins)) > 1e-6:
        raise ValueError("aggregate cash identity does not reconcile")
    return {
        "games": len(games),
        "episode_ids": [game["episode_id"] for game in games],
        "opponent_submissions": dict(Counter(row["submission_id"] for row in opponents)),
        "wins": sum(value > 0 for value in margins),
        "draws": sum(value == 0 for value in margins),
        "losses": sum(value < 0 for value in margins),
        "mean_cash_gap": mean(margins),
        "median_cash_gap": median(margins),
        "mean_relative_cash_gap": mean(
            margin / row["cash"][-1] for margin, row in zip(margins, opponents, strict=True)
        ),
        "our_seat_counts": dict(Counter(row["seat"] for row in ours)),
        "ours": _side(ours),
        "opponent": _side(opponents),
        "ledger": ledger,
        "cash_gap_by_turn": [
            mean(a["cash"][t] - b["cash"][t] for a, b in zip(ours, opponents, strict=True))
            for t in range(720)
        ],
    }


def run(config: Diagnosis) -> None:
    """Reuse audited ledgers, authenticate raw inputs and publish grouped evidence."""
    manifest = orjson.loads(config.manifest.read_bytes())
    metadata = {row["id"]: row for row in manifest["episodes"]}
    replays = {row["episode_id"]: row for row in manifest["replays"]}
    if manifest["failures"] or set(metadata) != set(replays):
        raise ValueError("replay acquisition differs from the frozen episode selection")
    results = []
    for episode_id in sorted(metadata):
        task = {**metadata[episode_id], **replays[episode_id]}
        target = config.output / "episodes" / f"{episode_id}.json"
        result = orjson.loads(target.read_bytes()) if target.exists() else extract(task)
        for row, board in zip(result["players"], board_metrics(task, result), strict=True):
            row["board"] = board
        write_json(target, result)
        results.append(result)
    summary = {
        "configuration": config.model_dump(mode="json"),
        "manifest_sha256": digest(config.manifest),
        "code_sha256": digest(Path(__file__)),
        "checked_observations": sum(row["checked_observations"] for row in results),
        "cash_reconciled_games": sum(row["cash_ledger_reconciled"] for row in results),
        "groups": {name: summarize(results, ids) for name, ids in config.groups.items()},
        "scope": "All frozen direct games, with exact replay and cash-ledger audits. "
        "Accounting components are descriptive, not causal. Different versions played "
        "different seeds and opponent versions; group differences do not establish improvement.",
    }
    write_json(config.output / "diagnosis.json", summary)
    plot_duels(summary["groups"], config.output)
    print(orjson.dumps({k: v["games"] for k, v in summary["groups"].items()}).decode())


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="matchup_dsm_duels_20260925"
)
def main(configuration: DictConfig) -> None:
    """Read the immutable analysis protocol through Hydra."""
    run(Diagnosis.model_validate(OmegaConf.to_container(configuration.analysis, resolve=True)))


if __name__ == "__main__":
    main()
