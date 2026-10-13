"""Audit a frozen multi-team replay cohort and retain compact strategic features."""

import gzip
import multiprocessing
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.behavior.extraction import fingerprint, normalized_action
from kagg_revue.evaluation.matchups.duels import board_metrics
from kagg_revue.evaluation.matchups.extraction import extract


class Study(FrozenSettings):
    """Declare a read-only replay analysis independently of training."""

    manifest: Path
    output: Path
    workers: int = Field(default=12, ge=1, le=24)
    excluded_episodes: dict[int, str] = Field(default_factory=dict)
    focus_submissions: tuple[int, ...] = ()


def features(result: dict[str, Any], task: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep game-level samples and daily decisions with exact settled quantities."""
    rows = []
    for seat, player in enumerate(result["players"]):
        opponent = result["players"][1 - seat]
        daily: dict[int, dict[str, Any]] = {
            day: {"sales": {}, "purchases": {}, "hires": 0, "hire_cost": 0} for day in range(30)
        }
        timing: dict[str, Any] = {}
        purchases = []
        for order in player["orders"]:
            request, quantity = order["requested"], order["committed"]
            if not request or not quantity:
                continue
            turn = order["turn"]
            cash = order["money_after"] - order["money_before"]
            operation = request[0]
            if operation == "HIRE":
                daily[turn // 24]["hires"] += quantity
                daily[turn // 24]["hire_cost"] -= cash
            elif operation == "SELL":
                item = request[1]
                record = daily[turn // 24]["sales"].setdefault(item, [0, 0])
                record[0] += quantity
                record[1] += cash
                timing.setdefault(
                    item,
                    {"first": turn, "last": turn, "hours": [0] * 24, "floor_quantity": 0},
                )
                timing[item]["last"] = turn
                timing[item]["hours"][turn % 24] += quantity
                # This identifies entirely floor-priced orders, a conservative count.
                timing[item]["floor_quantity"] += quantity if cash == quantity else 0
            elif operation in {"BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT", "BUY_LAND"}:
                key = ":".join(request[:2])
                record = daily[turn // 24]["purchases"].setdefault(key, [0, 0])
                record[0] += quantity
                record[1] -= cash
                purchases.append([turn, key, quantity, -cash])
        snapshots = {day: player["snapshots"][str(day * 24)] for day in range(30)}
        stock = player["snapshots"]["719"]["inventory"]
        invalid = Counter(entry["status"] for entry in player["invalid_units"])
        missed: Counter[str] = Counter()
        lost: Counter[str] = Counter()
        for event in player["events"]:
            missed.update(event.get("unwatered_or_unfed", {}))
            if "asset_lost_at_refresh" in event:
                lost[event["asset_lost_at_refresh"]] += 1
        margin = player["cash"][-1] - opponent["cash"][-1]
        actions = [normalized_action(action) for action in player["opening_actions"]]
        rows.append(
            {
                "episode_id": result["episode_id"],
                "date": result["date"],
                "seed": result["seed"],
                "seat": seat,
                "name": player["name"],
                "submission": player["submission_id"],
                "opponent": opponent["name"],
                "opponent_submission": opponent["submission_id"],
                "recent_game": task["recent_game"],
                "recent_download": task["recent_download"],
                "cash": player["cash"][-1],
                "margin": margin,
                "result": int(margin > 0) - int(margin < 0),
                "cash_curve": player["cash"],
                "shops": result["shops"],
                "daily": daily,
                "snapshots": snapshots,
                "ledger": player["ledger"],
                "harvested": player["harvested"],
                "overflow": player["overflow"],
                "end_stock": stock,
                "timing": timing,
                "purchases": purchases,
                "board": player["board"],
                "operations": player["operations"],
                "invalid": dict(invalid),
                "missed": dict(missed),
                "lost": dict(lost),
                "shortfalls": player["shortfalls"],
                "opening": {
                    str(horizon): str(fingerprint(actions[:horizon])) for horizon in (1, 4, 12, 24)
                },
            }
        )
    return rows


def audit(job: tuple[dict[str, Any], str]) -> list[dict[str, Any]]:
    """Reuse completed audited artifacts, validating their source identity."""
    task, output = job
    target = Path(output) / "episodes" / f"{task['episode_id']}.json.gz"
    if target.exists():
        result = orjson.loads(gzip.decompress(target.read_bytes()))
        if result["source_sha256"] != task["sha256"]:
            raise ValueError("cached analysis does not match the frozen source")
    else:
        result = extract(task)
        for player, board in zip(result["players"], board_metrics(task, result), strict=True):
            player["board"] = board
        result["source_sha256"] = task["sha256"]
        target.write_bytes(gzip.compress(orjson.dumps(result), compresslevel=1, mtime=0))
    return features(result, task)


def run(config: Study) -> None:
    """Reconcile every game, preserving failures instead of silently excluding them."""
    manifest = orjson.loads(config.manifest.read_bytes())
    (config.output / "episodes").mkdir(parents=True, exist_ok=True)
    write_json(config.output / "resolved-study.json", config.model_dump(mode="json"))
    started = time.monotonic()
    failures, rows = [], []
    # Prioritize direct games for useful intermediate results, without filtering.
    names = {"DSM", "M & M & P & Q", "DECEM", "Boey", "Vadim Vasilenko"}
    names.add("Unknown Mother-Goose")
    tasks = sorted(
        [task for task in manifest["tasks"] if task["episode_id"] not in config.excluded_episodes],
        key=lambda task: -sum(agent["teamName"] in names for agent in task["agents"]),
    )
    with (
        ProcessPoolExecutor(
            max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool,
        (config.output / "features.jsonl").open("wb") as stream,
    ):
        futures = {pool.submit(audit, (task, str(config.output))): task for task in tasks}
        for done, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
                rows.extend(result)
                for row in result:
                    stream.write(orjson.dumps(row, option=orjson.OPT_NON_STR_KEYS) + b"\n")
                stream.flush()
            except Exception as error:
                failures.append({"episode_id": futures[future]["episode_id"], "error": repr(error)})
            if done % 100 == 0 or done == len(tasks):
                progress = {
                    "completed": done,
                    "total": len(tasks),
                    "failures": failures,
                    "seconds": time.monotonic() - started,
                }
                write_json(config.output / "progress.json", progress)
                print(orjson.dumps({**progress, "failures": len(failures)}).decode(), flush=True)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["name"]].append(row)
    write_json(
        config.output / "audit.json",
        {
            "manifest_sha256": digest(config.manifest),
            "code_sha256": digest(Path(__file__)),
            "extraction_sha256": digest(Path(__file__).with_name("extraction.py")),
            "games": len(rows) // 2,
            "checked_observations": len(rows) * 720,
            "failures": failures,
            "excluded_episodes": {
                str(key): reason for key, reason in config.excluded_episodes.items()
            },
            "teams": {name: len(group) for name, group in grouped.items()},
        },
    )
    if failures:
        raise RuntimeError("some episodes failed reconciliation; see audit.json")


@hydra.main(version_base=None, config_path="../../../../configs", config_name="replay_study")
def main(configuration: DictConfig) -> None:
    """Load the analysis configuration without touching a training process."""
    run(Study.model_validate(OmegaConf.to_container(configuration.analysis, resolve=True)))


if __name__ == "__main__":
    main()
