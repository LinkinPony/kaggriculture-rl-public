"""Prepare reusable grounded demonstrations with whole-date source partitions."""

import json
import multiprocessing
import shutil
import tempfile
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.demonstrations.config import Preparation
from kagg_revue.datasets.demonstrations.partitions import tasks as partition_tasks
from kagg_revue.datasets.demonstrations.shards import encode_shard, index_quantities
from kagg_revue.learning.state import source_identity
from kagg_revue.policy.contracts import ContractLayout


def prepare(config: Preparation) -> Path:
    """Authenticate sources before creating fixed-size CPU encoding tasks."""
    manifest_path = config.output_dir / "manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        previous = {"quantity_encoding": "exact", **old["configuration"]}
        if previous != config.model_dump(mode="json"):
            raise ValueError("existing demonstrations have a different preparation protocol")
        return manifest_path
    if config.output_dir.exists():
        raise FileExistsError("demonstrations require a new output directory")
    started = time.perf_counter()
    identity = source_identity()
    for source in config.sources:
        if digest(source.archive) != source.sha256:
            raise ValueError("daily demonstration archive fingerprint changed")
    tasks, partition = partition_tasks(config)
    Path("tmp").mkdir(exist_ok=True)
    build = Path(tempfile.mkdtemp(prefix="grounded-demonstrations-", dir="tmp"))
    records: list[dict[str, Any]] = []
    try:
        with ProcessPoolExecutor(
            max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
        ) as workers:
            futures = [
                workers.submit(
                    encode_shard,
                    config.model_dump(mode="json"),
                    source.model_dump(mode="json"),
                    members,
                    str(build / f"shard-{index:05d}"),
                )
                for index, (source, members) in enumerate(tasks)
            ]
            for future in as_completed(futures):
                record = future.result()
                records.append(record)
                print(
                    json.dumps(
                        {
                            "phase": "demonstrations",
                            "completed_shards": len(records),
                            "total_shards": len(tasks),
                            "rows": record["rows"],
                            "date": record["source_date"],
                        }
                    ),
                    flush=True,
                )
        records.sort(key=lambda record: record["observations"])
        seeds: dict[int, str] = {}
        for record in records:
            for episode in record["episodes"]:
                if seeds.setdefault(episode["seed"], record["split"]) != record["split"]:
                    raise ValueError("a replay seed crosses demonstration date partitions")
        layout = ContractLayout.resolve(config.geometry())
        quantities = sorted(
            {
                *layout.observation.quantities,
                *(
                    quantity
                    for record in records
                    if record["split"] == "train" and config.quantity_encoding == "exact"
                    for quantity in record["literal_quantities"]
                ),
            }
        )
        if len(quantities) >= 32767:
            raise ValueError("exact training quantity vocabulary exceeds the compact action ABI")
        layout = replace(
            layout, observation=replace(layout.observation, quantities=tuple(quantities))
        )
        for record in records:
            index_quantities(build, record, layout, clip=config.quantity_encoding == "clip")
        coverage: dict[str, Any] = {}
        for split in sorted({record["split"] for record in records}):
            group = [record for record in records if record["split"] == split]
            episodes = [episode for record in group for episode in record["episodes"]]
            total = sum(episode["candidate_rows"] for episode in episodes)
            unsupported = sum(episode["unsupported_unit_rows"] for episode in episodes)
            quantities_missing = sum(record["quantity_uncovered_rows"] for record in group)
            coverage[split] = {
                "episodes": len(episodes),
                "candidate_rows": total,
                "unsupported_unit_rows": unsupported,
                "quantity_uncovered_rows": quantities_missing,
                "usable_rows": total - unsupported - quantities_missing,
                "display_name_counts": Counter(
                    name for episode in episodes for name in episode["agents"]
                ),
            }
            if config.quantity_encoding == "clip":
                coverage[split].update(
                    quantity_clipped_fields=sum(r["quantity_clipped_fields"] for r in group),
                    quantity_clipped_rows=sum(r["quantity_clipped_rows"] for r in group),
                )
            if (unsupported + quantities_missing) / total > config.maximum_excluded_row_fraction:
                raise ValueError(f"too many unrepresentable grounded demonstration rows: {split}")
        write_json(
            build / "manifest.json",
            {
                "schema": "grounded-daily-demonstrations-v1",
                "configuration": config.model_dump(mode="json"),
                "partition": partition,
                "layout": asdict(layout),
                "source": identity,
                "shards": records,
                "coverage": coverage,
                "elapsed_seconds": time.perf_counter() - started,
                "inputs": "Current own-private/public observation and causal public history.",
                "targets": (
                    "One turn: normalized applied unit actions and ordered market requests; "
                    f"quantity labels capped at {config.quantity_max} in every split."
                    if config.quantity_encoding == "clip"
                    else "One turn: normalized applied unit actions and exact market requests."
                ),
                "quantity_vocabulary": (
                    f"Fixed integers 1..{config.quantity_max}; "
                    "no data-dependent vocabulary fitting."
                    if config.quantity_encoding == "clip"
                    else "Training-source literals plus declared exploration "
                    "symbols; no held-out vocabulary fitting."
                ),
                "scope": "Multi-date raw episodes; display names do not identify independent "
                "policy versions. No model weights were read.",
            },
        )
        config.output_dir.parent.mkdir(parents=True, exist_ok=True)
        build.rename(config.output_dir)
    finally:
        if build.exists():
            shutil.rmtree(build)
    return manifest_path


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="demonstrations",
)
def main(configuration: DictConfig) -> None:
    """Resolve source dates and hashes before creating the persistent dataset."""
    config = Preparation.model_validate(OmegaConf.to_container(configuration.data, resolve=True))
    result = prepare(config)
    print(json.dumps({"manifest": str(result), "sha256": digest(result)}), flush=True)


if __name__ == "__main__":
    main()
