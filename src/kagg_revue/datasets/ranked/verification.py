"""Authenticate ranked BC arrays and qualify complete decoded source trajectories."""

import gzip
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.demonstrations.encoding import quantity_columns
from kagg_revue.datasets.demonstrations.loading import Dataset
from kagg_revue.datasets.demonstrations.verify import verify
from kagg_revue.datasets.ranked.config import Preparation
from kagg_revue.policy.contracts import ContractLayout


def verify_dataset(config: Preparation) -> dict[str, Any]:
    """Check all hashes, rows, chosen seats, quantity bounds and partition leakage."""
    path = config.output_dir / "manifest.json"
    layout = ContractLayout.resolve(config.geometry())
    dataset = Dataset(path, digest(path), layout, config.environment, ((4260000000, 4283000000),))
    for name, expected in dataset.manifest["provenance"].items():
        if digest(Path(name)) != expected:
            raise ValueError(f"source provenance changed: {name}")
    public = json.loads(config.public_manifest.read_text())
    raw = config.public_manifest.parent
    metadata_paths = {raw / "leaderboard.json"}
    for submission in public["submissions"]:
        metadata_paths.add(raw / "teams" / f"{submission['teamId']}.json")
        metadata_paths.add(raw / "submissions" / f"{submission['id']}.json")
        if (
            submission["rank"] > public["configuration"]["maximum_rank"]
            or float(submission["publicScore"]) <= public["configuration"]["minimum_score"]
        ):
            raise ValueError("public submission does not satisfy the frozen rank and score cutoffs")
    for metadata_path in metadata_paths:
        source = json.loads(metadata_path.with_suffix(".source.json").read_text())
        if digest(metadata_path) != source["sha256"]:
            raise ValueError("a frozen Kaggle metadata response changed after its retrieval")
    counts: Counter[str] = Counter()
    seats: Counter[str] = Counter()
    qfields = quantity_columns(layout)
    for record in dataset.shards:
        arrays = {
            key: np.load(dataset.path(record[key]), mmap_mode="r")
            for key in ("observations", "actions", "origins", "quantity_coverage")
        }
        observations, actions, origins, covered = (
            arrays[key] for key in ("observations", "actions", "origins", "quantity_coverage")
        )
        rows = record["rows"]
        if (
            observations.shape != (rows, layout.observation.features)
            or actions.shape != (rows, layout.factors)
            or origins.shape != (rows, 2)
            or covered.shape != (rows,)
            or not np.isfinite(observations).all()
            or not covered.all()
            or (actions[:, qfields] < 0).any()
            or (actions[:, qfields] >= config.quantity_max).any()
            or "sampling_weights" in record
        ):
            raise ValueError("ranked arrays violate shape, numeric, quantity or sampling contracts")
        stop = 0
        for episode in record["episodes"]:
            begin, end = episode["row_start"], episode["row_stop"]
            selected = origins[begin:end]
            selected_seats = [seat["seat"] for seat in episode["selected_seats"]]
            if (
                begin != stop
                or not np.isin(selected[:, 1], selected_seats).all()
                or (selected[:, 0] < 0).any()
                or (selected[:, 0] >= layout.observation.turns).any()
                or len(np.unique(selected, axis=0)) != len(selected)
                or len(selected) != episode["candidate_rows"] - episode["unsupported_unit_rows"]
            ):
                raise ValueError("episode rows contain an excluded seat or duplicate decision")
            stop = end
            seats.update(seat["name"] for seat in episode["selected_seats"])
        if stop != rows:
            raise ValueError("episode row offsets do not cover the shard")
        counts[record["split"]] += rows
    expected = {split: row["usable_rows"] for split, row in dataset.manifest["coverage"].items()}
    if dict(counts) != expected:
        raise ValueError("dataset row totals differ from coverage")
    result = {
        "manifest": str(path),
        "sha256": digest(path),
        "coverage": dataset.manifest["coverage"],
        "shards": len(dataset.shards),
        "teachers": dict(seats),
        "fixed_quantities": list(layout.observation.quantities),
        "all_source_and_array_hashes_verified": True,
        "authenticated_api_metadata_responses": len(metadata_paths),
        "all_observations_finite": True,
        "only_selected_seats": True,
        "duplicate_episode_or_decision_rows": 0,
        "seed_partition_overlap": 0,
        "reserved_online_seeds": [[4260000000, 4283000000]],
        "equal_row_weights_without_replacement": True,
        "history_complete": dataset.manifest["screening"]["ranking_evidence"]["history_complete"],
    }
    write_json(config.report_dir / "dataset-verification.json", result)
    return result


def verify_sources(config: Preparation) -> list[dict[str, Any]]:
    """Cover both daily dates, all partitions and every supplemented submission."""
    tasks = json.loads((config.report_dir / "catalog.json").read_text())
    sampled: dict[int, Any] = {}
    roles: set[tuple[str, Any]] = set()
    for task in sorted(tasks, key=lambda task: task["episode_id"]):
        keys = {("split", task["split"])}
        if task["source"] == "daily":
            keys.add(("daily_date", task["date"]))
        keys.update(
            ("submission", seat["submission_id"])
            for seat in task["seats"]
            if seat["submission_id"] is not None
        )
        if keys - roles:
            roles.update(keys)
            sampled[task["episode_id"]] = task
    layout = ContractLayout.resolve(config.geometry())
    reports = []
    for task in sampled.values():
        path = Path(task["path"])
        if task.get("member"):
            with zipfile.ZipFile(path) as archive:
                raw = archive.read(task["member"])
        else:
            raw = gzip.decompress(path.read_bytes())
        report = verify(orjson.loads(raw), layout, clip_quantities=True)
        reports.append({"episode_id": task["episode_id"], "source": task["source"], **report})
        write_json(
            config.report_dir / "replay-verification.json",
            {"complete": False, "planned": len(sampled), "reports": reports},
        )
        print(
            json.dumps({"phase": "verify_replay", "done": len(reports), "total": len(sampled)}),
            flush=True,
        )
    write_json(
        config.report_dir / "replay-verification.json",
        {
            "complete": True,
            "roles": sorted(roles),
            "reports": reports,
            "verified_observations": sum(report["verified_observations"] for report in reports),
            "scope": "Deterministic complete-trajectory sample; not full-corpus state equivalence.",
        },
    )
    return reports


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="demonstrations_ranked"
)
def main(configuration: DictConfig) -> None:
    """Check the prepared artifacts and shared causal replay contract on CPU."""
    config = Preparation.model_validate(OmegaConf.to_container(configuration.data, resolve=True))
    verify_dataset(config)
    verify_sources(config)


if __name__ == "__main__":
    main()
