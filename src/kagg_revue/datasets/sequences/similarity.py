"""Compare collected versions by phase-conditioned action and workforce profiles."""

import json
import multiprocessing
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.sequences.collected import _snapshot
from kagg_revue.datasets.sequences.sources import read_replay
from kagg_revue.datasets.sequences.watching import catalog


class SimilaritySettings(FrozenSettings):
    """Pin a complete collector snapshot and the reference submission."""

    source: Path
    output: Path
    reference: int
    workers: int = Field(default=12, gt=0)


def _token(action: list[Any]) -> str:
    operation = str(action[0]) if action else "PASS"
    item = f"/{action[1]}" if len(action) > 1 and isinstance(action[1], str) else ""
    return operation + item


def profile(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Measure actions without opponent labels, reward selection or replay truncation."""
    replay = orjson.loads(read_replay(task))
    result = []
    for seat in task["seats"]:
        counts: dict[str, Counter[str]] = {key: Counter() for key in ("unit", "market")}
        workers = np.zeros(6)
        turns = np.zeros(6)
        market_quantities: Counter[str] = Counter()
        opening = []
        for turn, pair in enumerate(replay["steps"][1:]):
            action = pair[seat["seat"]].get("action") or {}
            phase = min(turn // 120, 5)
            units = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
            market = action.get("market", [])
            turns[phase] += 1
            workers[phase] += len(units)
            for unit in units:
                counts["unit"][f"{phase}/{_token(unit)}"] += 1
            for order in market or [["EMPTY"]]:
                token = _token(order)
                counts["market"][f"{phase}/{token}"] += 1
                if len(order) > 2 and isinstance(order[2], (int, float)):
                    market_quantities[token] += int(order[2])
            if turn < 8:
                opening.append(action)
        result.append(
            {
                "episode_id": task["episode_id"],
                "submission_id": seat["submission_id"],
                "seed": task["seed"],
                "seat": seat["seat"],
                "counts": {key: dict(value) for key, value in counts.items()},
                "workers": (workers / np.maximum(turns, 1)).tolist(),
                "quantities": dict(market_quantities),
                "opening": opening,
                "statuses": replay["statuses"],
            }
        )
    return result


def _distribution(rows: list[dict[str, Any]], domain: str) -> Counter[str]:
    total: Counter[str] = Counter()
    for row in rows:
        total.update(row["counts"][domain])
    return total


def distance(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> dict[str, float]:
    """Report average per-phase total variation and relative workforce differences."""
    result = {}
    for domain in ("unit", "market"):
        a, b = _distribution(left, domain), _distribution(right, domain)
        values = []
        for phase in range(6):
            keys = [key for key in a.keys() | b.keys() if key.startswith(f"{phase}/")]
            x, y = np.array([a[k] for k in keys]), np.array([b[k] for k in keys])
            values.append(float(np.abs(x / max(x.sum(), 1) - y / max(y.sum(), 1)).sum() / 2))
        result[f"{domain}_tv"] = float(np.mean(values))
    x = np.mean([r["workers"] for r in left], axis=0)
    y = np.mean([r["workers"] for r in right], axis=0)
    result["workforce_relative"] = float(np.mean(np.abs(x - y) / np.maximum(y, 1)))
    return result


def compare(config: SimilaritySettings) -> dict[str, Any]:
    """Archive per-game evidence and estimate the reference's own sampling variation."""
    snapshot = config.output / "collector-original.json"
    manifest = _snapshot(config.source, snapshot)
    tasks, _, _ = catalog((snapshot,), (manifest["team_name"],), 62001)
    destination = config.output / "profiles.json"
    if destination.exists():
        rows = json.loads(destination.read_text())
    else:
        with ProcessPoolExecutor(
            max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            rows = [row for group in pool.map(profile, tasks, chunksize=8) for row in group]
        write_json(destination, rows)
    groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["submission_id"]].append(row)
    reference = groups[config.reference]
    if len(reference) < 32:
        raise ValueError("reference needs at least 32 trajectories")
    rng = np.random.default_rng(56654377)
    noise = []
    for _ in range(200):
        order = rng.permutation(len(reference)).tolist()
        split = len(order) // 2
        noise.append(
            distance([reference[i] for i in order[:split]], [reference[i] for i in order[split:]])
        )
    versions = []
    for key, group in sorted(groups.items()):
        openings = Counter(json.dumps(r["opening"], sort_keys=True) for r in group)
        common, count = openings.most_common(1)[0]
        versions.append(
            {
                "submission_id": key,
                "trajectories": len(group),
                **distance(group, reference),
                "workers": np.mean([r["workers"] for r in group], axis=0).tolist(),
                "dominant_opening_fraction": count / len(group),
                "dominant_opening": json.loads(common),
            }
        )
    report = {
        "configuration": config.model_dump(mode="json"),
        "collector_sha256": digest(snapshot),
        "profiles_sha256": digest(destination),
        "reference_split_half_p95": {
            key: float(np.quantile([row[key] for row in noise], 0.95)) for key in noise[0]
        },
        "versions": versions,
        "limitation": "Descriptive similarity across different states; not policy equivalence.",
    }
    write_json(config.output / "report.json", report)
    return report


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="sequences_decem_20260929"
)
def main(configuration: DictConfig) -> None:
    """Compare version behavior from a reproducible Hydra configuration."""
    config = SimilaritySettings.model_validate(
        OmegaConf.to_container(configuration.similarity, resolve=True)
    )
    report = compare(config)
    print(
        json.dumps(
            {
                "versions": [
                    {k: v for k, v in row.items() if k not in {"dominant_opening", "workers"}}
                    for row in report["versions"]
                ],
                "reference_split_half_p95": report["reference_split_half_p95"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
