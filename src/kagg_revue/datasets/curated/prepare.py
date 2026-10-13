"""Prepare authenticated mixed-source BC data without strategy stratification."""

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
import numpy as np
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.curated.catalog import Preparation, catalog
from kagg_revue.datasets.curated.encoding import encode_shard
from kagg_revue.datasets.demonstrations.shards import index_quantities
from kagg_revue.learning.state import source_identity
from kagg_revue.policy.contracts import ContractLayout


def prepare(config: Preparation) -> Path:
    """Fit train-only quantity vocabulary and save all provenance with the arrays."""
    if config.output_dir.parts[:2] != ("outputs", "datasets") or config.output_dir.exists():
        raise ValueError("curated demonstrations require a fresh outputs/datasets directory")
    started = time.perf_counter()
    selected, screening = catalog(config)
    paths = {Path(task["path"]) for task in selected}
    paths.update((config.tasks, config.trajectories, config.public_manifest))
    provenance = {str(path): digest(path) for path in sorted(paths)}
    public = json.loads(config.public_manifest.read_text())
    for replay in public["replays"]:
        if replay["path"] in provenance and provenance[replay["path"]] != replay["sha256"]:
            raise ValueError("downloaded public replay fingerprint changed")
    groups: list[list[dict[str, Any]]] = []
    for split in ("train", "selection", "confirmation"):
        group = [task for task in selected if task["split"] == split]
        np.random.default_rng(config.partition_seed).shuffle(group)
        groups.extend(
            group[start : start + config.episodes_per_shard]
            for start in range(0, len(group), config.episodes_per_shard)
        )
    Path("tmp").mkdir(exist_ok=True)
    build = Path(tempfile.mkdtemp(prefix="curated-demonstrations-", dir="tmp"))
    records: list[dict[str, Any]] = []
    try:
        with ProcessPoolExecutor(
            max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
        ) as workers:
            futures = [
                workers.submit(
                    encode_shard,
                    config.model_dump(mode="json"),
                    group,
                    str(build / f"shard-{i:05d}"),
                )
                for i, group in enumerate(groups)
            ]
            for future in as_completed(futures):
                records.append(future.result())
                print(
                    json.dumps(
                        {"phase": "encode", "completed": len(records), "total": len(groups)}
                    ),
                    flush=True,
                )
        records.sort(key=lambda record: record["observations"])
        layout = ContractLayout.resolve(config.geometry())
        quantities = sorted(
            {
                *layout.observation.quantities,
                *(q for r in records if r["split"] == "train" for q in r["literal_quantities"]),
            }
        )
        if len(quantities) >= 32767:
            raise ValueError("quantity vocabulary exceeds compact action storage")
        layout = replace(
            layout, observation=replace(layout.observation, quantities=tuple(quantities))
        )
        for record in records:
            index_quantities(build, record, layout)
            record["hashes"]["sampling_weights"] = digest(build / record["sampling_weights"])
        coverage = {}
        for split in ("train", "selection", "confirmation"):
            group = [r for r in records if r["split"] == split]
            episodes = [e for r in group for e in r["episodes"]]
            candidates = sum(e["candidate_rows"] for e in episodes)
            unsupported = sum(e["unsupported_unit_rows"] for e in episodes)
            missing = sum(r["quantity_uncovered_rows"] for r in group)
            if not candidates or (unsupported + missing) / candidates > 0.05:
                raise ValueError("insufficient representable demonstration coverage")
            coverage[split] = {
                "episodes": len(episodes),
                "candidate_rows": candidates,
                "unsupported_unit_rows": unsupported,
                "quantity_uncovered_rows": missing,
                "usable_rows": candidates - unsupported - missing,
                "selected_trajectories": sum(len(e["selected_seats"]) for e in episodes),
                "source_counts": dict(Counter(e["source"] for e in episodes)),
            }
        write_json(
            build / "manifest.json",
            {
                "schema": "grounded-daily-demonstrations-v1",
                "configuration": config.model_dump(mode="json"),
                "layout": asdict(layout),
                "source": source_identity(),
                "provenance": provenance,
                "screening": screening,
                "sampling_weights_required": True,
                "shards": records,
                "coverage": coverage,
                "elapsed_seconds": time.perf_counter() - started,
                "inputs": "Current visible observation and causal public history; no future state.",
                "targets": "Selected teacher's observed applied unit actions and market requests.",
                "quantity_vocabulary": "Training literals plus fixed exploration symbols only.",
                "scope": "No outcome weighting, opening quotas, auxiliary targets "
                "or strategy strata.",
            },
        )
        config.output_dir.parent.mkdir(parents=True, exist_ok=True)
        build.rename(config.output_dir)
    finally:
        if build.exists():
            shutil.rmtree(build)
    return config.output_dir / "manifest.json"


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="demonstrations_budget",
)
def main(configuration: DictConfig) -> None:
    """Resolve the one approved preparation recipe."""
    config = Preparation.model_validate(OmegaConf.to_container(configuration.data, resolve=True))
    manifest = prepare(config)
    print(json.dumps({"manifest": str(manifest), "sha256": digest(manifest)}), flush=True)


if __name__ == "__main__":
    main()
