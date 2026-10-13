"""Build ordinary BC arrays from selected daily and public demonstration seats."""

import json
import multiprocessing
import shutil
import tempfile
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.curated.encoding import encode_selected_shard
from kagg_revue.datasets.demonstrations.shards import index_quantities
from kagg_revue.datasets.ranked.catalog import catalog
from kagg_revue.datasets.ranked.config import Preparation
from kagg_revue.learning.state import source_identity
from kagg_revue.policy.contracts import ContractLayout


def prepare(config: Preparation) -> Path:
    """Preserve the current BC ABI, clipping, equal row weights and seed roles."""
    if config.output_dir.parts[:2] != ("outputs", "datasets") or config.output_dir.exists():
        raise ValueError("ranked demonstrations require a fresh outputs/datasets directory")
    started = time.perf_counter()
    selected, screening = catalog(config)
    paths = {Path(task["path"]) for task in selected}
    paths.update((config.daily_manifest, config.public_manifest, *config.leaderboard_snapshots))
    if config.frame_audit is not None:
        paths.add(config.frame_audit)
    provenance = {str(path): digest(path) for path in sorted(paths)}
    groups: list[list[dict[str, Any]]] = []
    for split in ("train", "selection", "confirmation"):
        group = [task for task in selected if task["split"] == split]
        np.random.default_rng(config.partition_seed).shuffle(group)
        groups.extend(
            group[start : start + config.episodes_per_shard]
            for start in range(0, len(group), config.episodes_per_shard)
        )
    Path("tmp").mkdir(exist_ok=True)
    build = Path(tempfile.mkdtemp(prefix="ranked-demonstrations-", dir="tmp"))
    records: list[dict[str, Any]] = []
    try:
        with ProcessPoolExecutor(
            max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            futures = [
                pool.submit(
                    encode_selected_shard, config.geometry(), tasks, str(build / f"shard-{i:05d}")
                )
                for i, tasks in enumerate(groups)
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
        for record in records:
            index_quantities(build, record, layout, clip=True)
            # The shared selected-seat encoder also serves exposure-weighted BC.
            # This recipe traverses every retained row once, so omit its unit weights.
            (build / record.pop("sampling_weights")).unlink()
        coverage = {}
        for split in ("train", "selection", "confirmation"):
            group = [record for record in records if record["split"] == split]
            episodes = [episode for record in group for episode in record["episodes"]]
            candidates = sum(episode["candidate_rows"] for episode in episodes)
            unsupported = sum(episode["unsupported_unit_rows"] for episode in episodes)
            if not candidates or unsupported / candidates > config.maximum_excluded_row_fraction:
                raise ValueError(f"insufficient representable demonstration coverage: {split}")
            coverage[split] = {
                "episodes": len(episodes),
                "selected_trajectories": sum(len(e["selected_seats"]) for e in episodes),
                "candidate_rows": candidates,
                "unsupported_unit_rows": unsupported,
                "quantity_uncovered_rows": sum(r["quantity_uncovered_rows"] for r in group),
                "quantity_clipped_rows": sum(r["quantity_clipped_rows"] for r in group),
                "quantity_clipped_fields": sum(r["quantity_clipped_fields"] for r in group),
                "usable_rows": sum(r["rows"] - r["quantity_uncovered_rows"] for r in group),
                "source_counts": dict(Counter(e["source"] for e in episodes)),
                "display_name_counts": dict(
                    Counter(seat["name"] for e in episodes for seat in e["selected_seats"])
                ),
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
                "shards": records,
                "coverage": coverage,
                "elapsed_seconds": time.perf_counter() - started,
                "partition": {
                    "method": "SHA256(partition_seed:episode_seed)",
                    "fractions": [0.9, 0.05, 0.05],
                },
                "inputs": "Current visible observation and causal public history only.",
                "targets": "Selected teacher's applied unit actions and ordered market requests.",
                "quantity_vocabulary": f"Fixed integers 1..{config.quantity_max}; cap every split.",
                "scope": "Snapshot-proven historical top-ten daily seats plus all retrievable "
                "public episodes of current top-ten submissions scoring strictly above 2900. "
                "See screening.ranking_evidence for the incomplete historical-rank evidence.",
            },
        )
        config.output_dir.parent.mkdir(parents=True, exist_ok=True)
        build.rename(config.output_dir)
    finally:
        if build.exists():
            shutil.rmtree(build)
    return config.output_dir / "manifest.json"


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="demonstrations_ranked"
)
def main(configuration: DictConfig) -> None:
    """Resolve ranked-source preparation without starting or modifying training."""
    config = Preparation.model_validate(OmegaConf.to_container(configuration.data, resolve=True))
    path = prepare(config)
    print(json.dumps({"manifest": str(path), "sha256": digest(path)}), flush=True)


if __name__ == "__main__":
    main()
