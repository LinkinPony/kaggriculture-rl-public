"""Authenticate the latest daily archives and retain every teacher context frame."""

import hashlib
import json
import multiprocessing
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.bc.data_config import ReplayContract
from kagg_revue.bc.replay import EpisodeLocator, ReplayRejected, _validate_header
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.behavior.acquisition import acquire
from kagg_revue.datasets.demonstrations.canonical import aggregate, canonicalize
from kagg_revue.datasets.demonstrations.encoding import encode, quantity_columns
from kagg_revue.datasets.sequences.catalog import catalog
from kagg_revue.datasets.sequences.sources import read_replay
from kagg_revue.learning.config import default_environment
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.settings import GeometrySettings, ModelSettings


class Preparation(FrozenSettings):
    """Bind source dates, ranking evidence and complete-sequence output."""

    output: Path
    raw: Path
    reuse: tuple[Path, ...]
    screening: Path | None = None
    teachers: tuple[str, ...] = ()
    expected_dates: tuple[str, ...] = ()
    days: int = Field(default=3, gt=0)
    workers: int = Field(default=12, gt=0)
    partition_seed: int = 62001
    train_val: bool = Field(
        default=False, description="Move legacy confirmation to train and rename selection to val."
    )
    agronomy: bool = False
    derived: bool = False
    canonical_market: bool = Field(
        default=False,
        description="Label teacher markets by realized requests; observations are unchanged.",
    )
    watch_manifests: tuple[Path, ...] = ()
    environment: dict[str, int | float] = Field(default_factory=default_environment)

    @model_validator(mode="after")
    def validate_selection(self) -> "Preparation":
        """Require one unambiguous teacher selection and a complete pinned window."""
        if bool(self.teachers) == (self.screening is not None):
            raise ValueError("specify either teacher names or ranking screening")
        if self.watch_manifests and (not self.teachers or self.expected_dates):
            raise ValueError("collector snapshots require teachers and their original date scopes")
        if len(set(self.teachers)) != len(self.teachers) or any(not n for n in self.teachers):
            raise ValueError("teacher names must be distinct and nonempty")
        if self.expected_dates and (
            len(self.expected_dates) != self.days
            or tuple(sorted(set(self.expected_dates))) != self.expected_dates
        ):
            raise ValueError("expected dates must be distinct, ordered and match days")
        return self

    def geometry(self) -> GeometrySettings:
        """Retain grounded-v2 features and the exact 1..100 quantity interface."""
        return GeometrySettings(
            environment=self.environment,
            unit_limit=32,
            width=384,
            decision_interval=1,
            quantity_max=100,
            quantity_extra=(),
            model=ModelSettings(
                architecture="grounded-v2",
                time_prior=False,
                prior_scale=0,
                agronomy=self.agronomy,
                derived=self.derived,
            ),
        )


def encode_episode(arguments: tuple[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
    """Keep unrepresentable frames in memory but exclude their supervised loss."""
    configuration, task = arguments
    config = Preparation.model_validate(configuration)
    directory = config.output
    record_path = directory / f"episode-{task['episode_id']}.json"
    if record_path.exists():
        record: dict[str, Any] = json.loads(record_path.read_text())
        if record.get("task") != task:
            raise ValueError("resumed data task differs")
        if all(digest(directory / record[key]) == value for key, value in record["hashes"].items()):
            return record
        raise ValueError("resumed sequence array differs")
    raw = read_replay(task)
    replay = orjson.loads(raw)
    if any(s.get("status") != "ACTIVE" for pair in replay["steps"][:-1] for s in pair):
        return {"excluded": True, "task": task, "reason": "non-ACTIVE decision frame"}
    layout = ContractLayout.resolve(config.geometry())
    contract = ReplayContract(
        replay_schema_version=1,
        module_version="1.32.7",
        agents=2,
        episode_steps=int(config.environment["episodeSteps"]),
        board_size=layout.board_size,
        max_market_orders=layout.observation.markets,
        unit_limit=32,
    )
    locator = EpisodeLocator(
        Path(task["path"]),
        task["member"],
        task["date"],
        task["create_time"],
        task["average_score"],
        task["minimum_score"],
    )
    try:
        _, environment, _, _, names = _validate_header(replay, locator, contract)
    except ReplayRejected as error:
        return {"excluded": True, "task": task, "reason": str(error)}
    if replay["info"]["seed"] != task["seed"] or any(
        names[seat["seat"]] != seat["name"] for seat in task["seats"]
    ):
        raise ValueError("replay identity differs from the selected teacher catalog")
    if (
        native.Engine(0, dict(environment)).configuration
        != native.Engine(0, config.environment).configuration
    ):
        raise ValueError("source episode uses a different game configuration")
    seats = [s["seat"] for s in task["seats"]]
    audit = None
    if config.canonical_market:
        replay, audit = canonicalize(replay, seats)
    observations, labels, eligible, counts = encode(replay, layout)
    observations, labels, eligible = observations[:, seats], labels[:, seats], eligible[:, seats]
    columns = quantity_columns(layout)
    clipped = labels[..., columns] > 100
    labels[..., columns] = np.clip(labels[..., columns], 1, 100) - 1
    arrays = {
        "observations": observations,
        "actions": labels.astype(np.int16),
        "eligible": eligible,
    }
    record = {
        "task": task,
        "source_date": task["date"],
        "split": task["split"],
        "rows": int(eligible.size),
        "usable_rows": int(eligible.sum()),
        "quantity_clipped_rows": int(clipped.any(-1).sum()),
        **({"canonical_market": audit} if audit is not None else {}),
        "hashes": {},
        "episodes": [
            {
                "episode_id": task["episode_id"],
                "seed": task["seed"],
                "selected_seats": task["seats"],
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                **counts,
            }
        ],
    }
    for name, array in arrays.items():
        path = directory / f"episode-{task['episode_id']}-{name}.npy"
        with path.with_suffix(".partial").open("wb") as stream:
            np.save(stream, array)
        path.with_suffix(".partial").replace(path)
        record[name] = path.name
        record["hashes"][name] = digest(path)
    write_json(record_path, record)
    return record


def prepare(config: Preparation) -> None:
    """Preserve source provenance and deterministic world-separated partitions."""
    config.output.mkdir(parents=True, exist_ok=True)
    resolved = config.model_dump(mode="json")
    if not config.derived:
        resolved.pop("derived")
    if not config.canonical_market:
        resolved.pop("canonical_market")
    if not config.train_val:
        resolved.pop("train_val")
    previous = config.output / "preparation.json"
    if previous.exists() and json.loads(previous.read_text()) != resolved:
        raise ValueError("cannot change a sequence preparation in place")
    write_json(previous, resolved)
    if config.watch_manifests:
        from kagg_revue.datasets.sequences.watching import catalog as watch_catalog

        tasks, manifest, evidence = watch_catalog(
            config.watch_manifests, config.teachers, config.partition_seed
        )
    else:
        manifest, entries = acquire(config.raw, list(config.reuse), config.days)
        dates = tuple(row["date"] for row in manifest["daily_archives"])
        if config.expected_dates and dates != config.expected_dates:
            raise ValueError(f"daily index dates differ from the requested window: {dates}")
        tasks, evidence = catalog(entries, config.teachers, config.screening, config.partition_seed)
    source_path = config.output / "sources.json"
    if (
        config.watch_manifests
        and source_path.exists()
        and json.loads(source_path.read_text()) != manifest
    ):
        raise ValueError("cannot change frozen sequence sources in place")
    write_json(source_path, manifest)
    if config.train_val:
        for task in tasks:
            task["split"] = "val" if task["split"] == "selection" else "train"
    write_json(config.output / "catalog.json", tasks)
    records: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    with ProcessPoolExecutor(
        max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        for result in pool.map(encode_episode, ((resolved, task) for task in tasks), chunksize=1):
            (exclusions if result.get("excluded") else records).append(result)
            count = len(records) + len(exclusions)
            if count % 32 == 0:
                print(json.dumps({"encoded": count, "total": len(tasks)}), flush=True)
    records.sort(key=lambda r: r["task"]["episode_id"])
    coverage = {}
    for split in ("train", "val") if config.train_val else ("train", "selection", "confirmation"):
        group = [r for r in records if r["split"] == split]
        coverage[split] = {
            "episodes": len(group),
            "usable_rows": sum(r["usable_rows"] for r in group),
            "context_rows": sum(r["rows"] for r in group),
            "trajectories": sum(len(r["task"]["seats"]) for r in group),
            "dates": dict(Counter(r["source_date"] for r in group)),
        }
    write_json(
        config.output / "manifest.json",
        {
            "schema": "grounded-daily-demonstrations-v1",
            "sequence_format": "complete-turn-seat-v1",
            "configuration": {
                **resolved,
                "partition": "episode-seed",
                **(
                    {
                        "split_mapping": {
                            "train": "train",
                            "selection": "val",
                            "confirmation": "train",
                        }
                    }
                    if config.train_val
                    else {}
                ),
            },
            "layout": asdict(ContractLayout.resolve(config.geometry())),
            "shards": records,
            "coverage": coverage,
            "exclusions": exclusions,
            "sources": manifest,
            **({"canonical_market": aggregate(records)} if config.canonical_market else {}),
            **evidence,
            "scope": (
                "Frozen collector snapshots with original submission scopes; "
                if config.watch_manifests
                else f"Latest {config.days} daily dates; "
            )
            + ("explicit named teachers; " if config.teachers else "historical top-ten teachers; ")
            + "all outcomes and ratings; "
            + ("canonical realized market requests; " if config.canonical_market else "")
            + "complete observations, unsupported decisions masked only from loss.",
        },
    )
    print(json.dumps({"coverage": coverage, "excluded": len(exclusions)}), flush=True)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="sequences_20260916")
def main(configuration: DictConfig) -> None:
    """Prepare authenticated recurrent demonstrations."""
    prepare(Preparation.model_validate(OmegaConf.to_container(configuration.data, resolve=True)))


if __name__ == "__main__":
    main()
