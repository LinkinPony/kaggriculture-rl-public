"""Macro-behaviour fingerprint of each version of a watched team from its public replays."""

import gzip
import json
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from statistics import mean
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings

ASSETS = ("GOOSE", "COW", "SHEEP", "WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
DAYS = 30


class Options(FrozenSettings):
    """Fingerprint the listed versions of one watched team on every downloaded game."""

    output: Path
    manifest: Path
    submissions: tuple[int, ...] = Field(min_length=1)
    workers: int = Field(default=16, ge=1, le=48)


def game(task: tuple[str, int]) -> dict[str, Any]:
    """Count one seat's hires, land purchases, asset purchases and market orders."""
    path, seat = task
    opener: Any = gzip.open if path.endswith(".gz") else open
    with opener(path, "rb") as handle:
        steps = json.load(handle)["steps"]
    purchases: Counter[str] = Counter()
    first: dict[str, int] = {}
    land: list[int] = []
    hires = orders = 0
    for turn in range(1, len(steps)):
        day = (turn - 1) // 24
        market = (steps[turn][seat]["action"] or {}).get("market") or []
        orders += len(market)
        for order in filter(None, market):
            if order[0] == "HIRE":
                hires += 1
            elif order[0] == "BUY_LAND":
                land.append(day)
            elif order[0] in ("BUY_ANIMAL", "BUY_SEED") and len(order) >= 3:
                purchases[order[1]] += int(order[2])
                first.setdefault(order[1], day)
    rewards = [steps[-1][side]["reward"] for side in (0, 1)]
    return {
        "cash": rewards[seat],
        "opponent_cash": rewards[1 - seat],
        "hires": hires,
        "orders_per_turn": orders / (len(steps) - 1),
        "land_days": land,
        "purchases": dict(purchases),
        "first_purchase_day": first,
    }


def summarize(games: list[dict[str, Any]]) -> dict[str, Any]:
    """Average one version's games into its plan fingerprint."""
    bought = [asset for asset in ASSETS if any(asset in row["purchases"] for row in games)]
    return {
        "games": len(games),
        "wins": sum(row["cash"] > row["opponent_cash"] for row in games),
        "losses": sum(row["cash"] < row["opponent_cash"] for row in games),
        "mean_cash": mean(row["cash"] for row in games),
        "mean_opponent_cash": mean(row["opponent_cash"] for row in games),
        "hires_per_day": mean(row["hires"] for row in games) / DAYS,
        "orders_per_turn": mean(row["orders_per_turn"] for row in games),
        "land_plots": dict(Counter(str(len(row["land_days"])) for row in games)),
        "land_days": [
            [list(days), count]
            for days, count in Counter(tuple(row["land_days"]) for row in games).most_common(3)
        ],
        "purchases": {a: mean(row["purchases"].get(a, 0) for row in games) for a in bought},
        "first_purchase_day": {
            a: mean(row["first_purchase_day"][a] for row in games if a in row["purchases"])
            for a in bought
        },
    }


def fingerprint(options: Options) -> dict[str, Any]:
    """Fingerprint every requested version on all of its downloaded public games."""
    manifest = json.loads(options.manifest.read_text())
    replays = {row["episode_id"]: row["path"] for row in manifest["replays"]}
    wanted = set(options.submissions)
    tasks, owners = [], []
    for episode in manifest["episodes"]:
        if episode["id"] not in replays:
            continue
        for agent in episode["agents"]:
            if agent.get("teamId") == manifest["team_id"] and agent["submissionId"] in wanted:
                tasks.append((replays[episode["id"]], int(agent.get("index", 0))))
                owners.append(agent["submissionId"])
    with ProcessPoolExecutor(options.workers) as pool:
        games = list(pool.map(game, tasks, chunksize=4))
    versions: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for owner, row in zip(owners, games, strict=True):
        versions[owner].append(row)
    fingerprints = {
        str(key): summarize(versions[key]) for key in options.submissions if versions[key]
    }
    return {
        "manifest": str(options.manifest),
        "manifest_sha256": digest(options.manifest),
        "team": manifest["team_name"],
        "versions": fingerprints,
    }


@hydra.main(version_base=None, config_path="../../../../configs", config_name="replay_fingerprint")
def main(config: DictConfig) -> None:
    """Write the requested versions' fingerprints and print one line per version."""
    options = Options.model_validate(OmegaConf.to_container(config.analysis, resolve=True))
    result = fingerprint(options)
    write_json(options.output / "fingerprints.json", result)
    for key, row in result["versions"].items():
        brief = {name: row[name] for name in ("games", "wins", "losses")}
        brief |= {name: round(row[name], 2) for name in ("hires_per_day", "orders_per_turn")}
        print(json.dumps({"submission": int(key), **brief, "land_days": row["land_days"][0]}))


if __name__ == "__main__":
    main()
