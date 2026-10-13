"""Reproducible opening EDA with per-episode caches and authenticated raw sources."""

import json
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.openings.catalog import Analysis, tasks
from kagg_revue.datasets.openings.extraction import extract
from kagg_revue.datasets.openings.statistics import analyze
from kagg_revue.native import _revue_core as native


def run(config: Analysis) -> None:
    """Preserve source membership and permit exact cache reuse after interruption."""
    if not config.output.resolve().is_relative_to((Path.cwd() / "outputs").resolve()):
        raise ValueError("EDA results belong under outputs")
    config.output.mkdir(parents=True, exist_ok=True)
    selected, provenance = tasks(config)
    write_json(config.output / "tasks.json", selected)
    write_json(config.output / "sources.json", provenance)
    source = {str(path): digest(path) for path in Path(__file__).parent.glob("*.py")}
    identity = {
        "configuration": config.model_dump(mode="json"),
        "sources": provenance,
        "extractor_sha256": source[str(Path(__file__).with_name("extraction.py"))],
        "native_sha256": digest(Path(native.__file__)),
    }
    protocol = config.output / "protocol.json"
    if protocol.exists() and orjson.loads(protocol.read_bytes()) != identity:
        raise ValueError("existing EDA protocol or extraction source differs")
    write_json(protocol, identity)
    cache = config.output / "episodes"
    cache.mkdir(exist_ok=True)
    pending = [task for task in selected if not (cache / f"{task['episode_id']}.json").exists()]
    started = time.perf_counter()
    print(
        json.dumps({"phase": "extract", "pending": len(pending), "total": len(selected)}),
        flush=True,
    )
    with ProcessPoolExecutor(
        max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        futures = {pool.submit(extract, task): task for task in pending}
        for index, future in enumerate(as_completed(futures), 1):
            task = futures[future]
            result = future.result()
            result["source_task"] = task
            path = cache / f"{task['episode_id']}.json"
            path.write_bytes(orjson.dumps(result))
            if index % 100 == 0 or index == len(pending):
                progress = {
                    "completed": len(selected) - len(pending) + index,
                    "total": len(selected),
                    "elapsed_seconds": time.perf_counter() - started,
                }
                write_json(config.output / "progress.json", progress)
                print(json.dumps(progress), flush=True)
    rows, rejected, fingerprints = [], [], {}
    checked = 0
    with (config.output / "trajectories.jsonl").open("wb") as stream:
        for task in selected:
            path = cache / f"{task['episode_id']}.json"
            result = orjson.loads(path.read_bytes())
            if result["source_task"] != task:
                raise ValueError("cached extraction uses another episode task")
            fingerprints[str(path)] = digest(path)
            if "rejected" in result:
                rejected.append(result)
                continue
            checked += result["checked_observations"]
            for row in result["rows"]:
                rows.append(row)
                stream.write(orjson.dumps(row) + b"\n")
    report = {
        "configuration": config.model_dump(mode="json"),
        "checked_observations": checked,
        "rejected": rejected,
        **analyze(rows),
    }
    write_json(config.output / "report.json", report)
    write_json(
        config.output / "extraction.json",
        {
            "files": fingerprints,
            "trajectories_sha256": digest(config.output / "trajectories.jsonl"),
            "source": source,
        },
    )
    print(
        json.dumps(
            {
                "complete": True,
                "trajectories": len(rows),
                "rejected_episodes": len(rejected),
                "checked_observations": checked,
            }
        ),
        flush=True,
    )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="opening_analysis",
)
def main(configuration: DictConfig) -> None:
    """Analyze existing source episodes without changing training or deployment."""
    run(Analysis.model_validate(OmegaConf.to_container(configuration.analysis, resolve=True)))


if __name__ == "__main__":
    main()
