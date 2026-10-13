"""Authenticate two BC manifests and compare their preserved official replays."""

import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.comparison.extraction import extract
from kagg_revue.datasets.comparison.statistics import analyze


class Comparison(FrozenSettings):
    """Pin the previous training dataset, new dataset and analysis outputs."""

    baseline_run: Path
    baseline: Path
    baseline_sha256: str
    current: Path
    current_sha256: str
    output: Path
    workers: int = Field(default=24, gt=0, le=48)


def catalog(config: Comparison) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Deduplicate replay reads and preserve seat-level dataset/split membership."""
    run = orjson.loads(config.baseline_run.read_bytes())
    if (
        run["demonstrations"]["manifest"] != str(config.baseline)
        or run["demonstrations"]["sha256"] != config.baseline_sha256
    ):
        raise ValueError("baseline differs from the actual training configuration")
    manifests = {}
    tasks: dict[int, dict[str, Any]] = {}
    sources: dict[str, str] = {}
    world_splits: dict[int, str] = {}
    for label, path, expected in (
        ("baseline", config.baseline, config.baseline_sha256),
        ("current", config.current, config.current_sha256),
    ):
        if digest(path) != expected:
            raise ValueError("comparison manifest identity differs")
        manifest = orjson.loads(path.read_bytes())
        manifests[label] = manifest
        sources.update({r["path"]: r["sha256"] for r in manifest["sources"]["daily_archives"]})
        for record in manifest["shards"]:
            row = record["task"]
            if world_splits.setdefault(row["seed"], row["split"]) != row["split"]:
                raise ValueError("the two datasets leak a world between partitions")
            task = tasks.setdefault(row["episode_id"], {**row, "memberships": {}})
            if task["seed"] != row["seed"] or task["split"] != row["split"]:
                raise ValueError("shared episode changed world or partition")
            for seat in row["seats"]:
                entry = task["memberships"].setdefault(
                    str(seat["seat"]), {"name": seat["name"], "datasets": []}
                )
                if entry["name"] != seat["name"]:
                    raise ValueError("shared teacher identity changed")
                entry["datasets"].append(label)
    for archive_path, expected in sources.items():
        if digest(Path(archive_path)) != expected:
            raise ValueError(f"raw archive identity differs: {archive_path}")
    return sorted(tasks.values(), key=lambda r: r["episode_id"]), manifests


def run(config: Comparison) -> None:
    """Extract once, cache compact rows by source/code hashes and summarize."""
    if config.output.parts[:2] != ("outputs", "analysis"):
        raise ValueError("comparison results belong under outputs/analysis")
    config.output.mkdir(parents=True, exist_ok=True)
    write_json(config.output / "resolved-config.json", config.model_dump(mode="json"))
    tasks, manifests = catalog(config)
    write_json(config.output / "catalog.json", tasks)
    key = {
        "catalog_sha256": digest(config.output / "catalog.json"),
        "extractor_sha256": digest(Path(__file__).with_name("extraction.py")),
        "daily_extractor_sha256": digest(Path(__file__).parents[1] / "behavior/extraction.py"),
    }
    cached_path, rows_path = config.output / "extraction.json", config.output / "trajectories.json"
    if cached_path.exists():
        cached = orjson.loads(cached_path.read_bytes())
        if cached["key"] != key or digest(rows_path) != cached["sha256"]:
            raise ValueError("cached extraction differs; use a fresh analysis directory")
        rows = orjson.loads(rows_path.read_bytes())
    else:
        rows = []
        with ProcessPoolExecutor(
            max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            for index, result in enumerate(pool.map(extract, tasks, chunksize=1), 1):
                rows.extend(result)
                if index % 100 == 0 or index == len(tasks):
                    print(f"Extracted {index}/{len(tasks)} episodes", flush=True)
        rows_path.write_bytes(orjson.dumps(rows))
        write_json(
            cached_path, {"key": key, "sha256": digest(rows_path), "trajectories": len(rows)}
        )
    report = analyze(rows)
    report["manifests"] = {
        label: {
            "coverage": m["coverage"],
            "excluded": len(m["exclusions"]),
            "masked_rows": sum(r["rows"] - r["usable_rows"] for r in m["shards"]),
            "clipped_rows": sum(r["quantity_clipped_rows"] for r in m["shards"]),
        }
        for label, m in manifests.items()
    }
    report["identical_layout"] = manifests["baseline"]["layout"] == manifests["current"]["layout"]
    report["overlap"] = {
        "episodes": sum(
            {d for s in t["memberships"].values() for d in s["datasets"]} == {"baseline", "current"}
            for t in tasks
        ),
        "trajectories": sum(len(r["datasets"]) == 2 for r in rows),
        "cross_split_leakage": 0,
    }
    write_json(config.output / "report.json", report)
    print(f"Comparison complete: {config.output / 'report.json'}", flush=True)


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="comparison_selected8_20260921",
)
def main(configuration: DictConfig) -> None:
    """Resolve the pinned comparison without touching any running training process."""
    run(Comparison.model_validate(OmegaConf.to_container(configuration.analysis, resolve=True)))


if __name__ == "__main__":
    main()
