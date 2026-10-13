"""Stream daily replays through the shared native encoder into work-plan shards."""

import hashlib
import json
import multiprocessing
import shutil
import tempfile
import time
import zipfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np
import orjson

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.bc.data_config import ReplayContract
from kagg_revue.bc.replay import (
    EpisodeLocator,
    ReplayRejected,
    _validate_header,
    daily_episode_metadata,
)
from kagg_revue.native import _revue_native as native
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import Settings
from kagg_revue.production.work import propose_programs


def quantity_fields(layout: ContractLayout) -> np.ndarray[Any, np.dtype[np.int64]]:
    """Identify only the quantity columns in the shared work-plan ABI."""
    return np.concatenate(
        (
            np.arange(2, layout.work_factors, 4),
            np.arange(layout.work_factors + 1, layout.factors, 2),
        )
    )


def _group(
    resolved: dict[str, Any], locators: list[EpisodeLocator], partition: str, prefix: str
) -> dict[str, Any]:
    settings = Settings.model_validate(resolved)
    layout = ContractLayout.resolve(settings)
    contract = ReplayContract(
        replay_schema_version=1,
        module_version=settings.bc.replay_module_version,
        agents=2,
        episode_steps=int(settings.environment["episodeSteps"]),
        board_size=layout.board_size,
        max_market_orders=layout.observation.markets,
        unit_limit=layout.observation.units,
    )
    observations = np.empty(
        (layout.decisions, 2 * len(locators), layout.observation.features), np.float16
    )
    actions = np.empty((layout.decisions, 2 * len(locators), layout.factors), np.int64)
    qfields = quantity_fields(layout)
    episodes: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    with zipfile.ZipFile(locators[0].archive) as archive:
        for locator in locators:
            try:
                with archive.open(locator.entry) as stream:
                    replay = orjson.loads(stream.read())
                episode_id, environment, steps, rewards, names = _validate_header(
                    replay, locator, contract
                )
                encoded = np.empty((2, settings.turns, layout.observation.features), np.float16)
                raw = np.empty((2, settings.turns, layout.observation.slots, 2), np.int64)
                for seat in (0, 1):
                    session = native.ContractSession(dict(environment), settings.unit_limit)
                    session.encode_replay_into(steps, seat, encoded[seat], raw[seat])
                quantities = np.unique(np.maximum(raw[..., 1], 1))
                if len(quantities) >= np.iinfo(np.int16).max:
                    raise ValueError("episode quantity vocabulary exceeds compact label bounds")
                raw[..., 1] = np.searchsorted(quantities, np.maximum(raw[..., 1], 1))
                local = replace(
                    layout, observation=replace(layout.observation, quantities=tuple(quantities))
                )
                labels = propose_programs(
                    encoded.transpose(1, 0, 2), raw.transpose(1, 0, 2, 3).astype(np.int16), local
                ).astype(np.int64)
                labels[..., qfields] = quantities[labels[..., qfields]]
                start = 2 * len(episodes)
                observations[:, start : start + 2] = encoded[:, list(layout.starts)].transpose(
                    1, 0, 2
                )
                actions[:, start : start + 2] = labels
                episodes.append(
                    {
                        "episode_id": episode_id,
                        "seed": replay["info"]["seed"],
                        "date": locator.source_date,
                        "agents": names,
                        "rewards": rewards,
                        "average_rating": locator.average_score,
                    }
                )
                del replay, steps, encoded, raw, labels
            except (ReplayRejected, ValueError, RuntimeError, KeyError) as error:
                rejected.append({"episode": locator.entry, "reason": str(error)})
    games = 2 * len(episodes)
    if not games:
        return {"rejected": rejected, "episodes": []}
    destination = Path(prefix)
    obs_path = destination.with_name(destination.name + "-observations.npy")
    raw_path = destination.with_name(destination.name + "-raw.npy")
    np.save(obs_path, observations[:, :games])
    np.save(raw_path, actions[:, :games])
    return {
        "observations": obs_path.name,
        "raw_actions": raw_path.name,
        "games": games,
        "rows": games * layout.decisions,
        "partition": partition,
        "quantities": np.unique(actions[:, :games, qfields]).tolist(),
        "episodes": episodes,
        "rejected": rejected,
    }


def prepare(settings: Settings) -> Path:
    """Build complete-episode splits and lossless, globally indexed quantity labels."""
    output = settings.bc.directory
    manifest_path = output / "manifest.json"
    source_path = settings.bc.source / "manifest.json"
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text())
        expected = json.loads(json.dumps(asdict(ContractLayout.resolve(settings))))
        if existing["layout"] != expected or existing["source_sha256"] != digest(source_path):
            raise ValueError("daily dataset differs from the resolved model layout or raw source")
        return manifest_path
    if settings.model.time_prior or not ContractLayout.resolve(settings).work:
        raise ValueError("daily work BC requires a state-conditioned work actor without time prior")
    source = json.loads(source_path.read_text())
    started = time.perf_counter()
    build = Path(tempfile.mkdtemp(prefix="daily-work-", dir="tmp"))
    tasks = []
    for record in source["daily_archives"]:
        archive = settings.bc.source / Path(record["path"]).name
        if digest(archive) != record["sha256"]:
            raise ValueError("daily archive fingerprint differs from downloaded manifest")
        metadata = daily_episode_metadata(archive)
        groups: dict[str, list[EpisodeLocator]] = {
            name: [] for name in ("train", "validation", "test")
        }
        for episode_id, values in sorted(metadata.items()):
            fraction = (
                int.from_bytes(
                    hashlib.sha256(f"{settings.seed}:{episode_id}".encode()).digest()[:8], "big"
                )
                / 2**64
            )
            partition = (
                "test"
                if fraction < settings.bc.test_fraction
                else "validation"
                if fraction < settings.bc.test_fraction + settings.bc.validation_fraction
                else "train"
            )
            groups[partition].append(
                EpisodeLocator(
                    archive,
                    f"{episode_id}.json",
                    record["date"],
                    str(values["create_time"]),
                    float(str(values["average_score"])),
                    float(str(values["minimum_score"])),
                )
            )
        for partition, locators in groups.items():
            for start in range(0, len(locators), settings.bc.shard_games // 2):
                tasks.append((locators[start : start + settings.bc.shard_games // 2], partition))
    records = []
    try:
        with ProcessPoolExecutor(
            max_workers=settings.workers, mp_context=multiprocessing.get_context("spawn")
        ) as executor:
            futures = [
                executor.submit(
                    _group,
                    settings.model_dump(mode="json"),
                    locators,
                    partition,
                    str(build / f"shard-{index:04d}"),
                )
                for index, (locators, partition) in enumerate(tasks)
            ]
            for future in as_completed(futures):
                records.append(future.result())
                print(
                    json.dumps({"phase": "replays", "shards": len(records), "total": len(tasks)}),
                    flush=True,
                )
        rejected = [entry for record in records for entry in record.pop("rejected")]
        accepted = sum(len(record["episodes"]) for record in records)
        if len(rejected) / (accepted + len(rejected)) > settings.bc.maximum_rejection_fraction:
            raise ValueError(f"too many rejected daily episodes: {len(rejected)}")
        records = sorted((r for r in records if r["episodes"]), key=lambda r: r["observations"])
        seeds: dict[int, str] = {}
        for record in records:
            for episode in record["episodes"]:
                seed = int(episode["seed"])
                previous = seeds.setdefault(seed, record["partition"])
                if previous != record["partition"]:
                    raise ValueError("a replay seed crosses BC partitions; regroup before training")
        quantities = sorted(
            {1, *settings.quantities, *(q for r in records for q in r["quantities"])}
        )
        if len(quantities) >= np.iinfo(np.int16).max:
            raise ValueError("global quantity vocabulary exceeds compact label bounds")
        layout = replace(
            ContractLayout.resolve(settings),
            observation=replace(
                ContractLayout.resolve(settings).observation, quantities=tuple(quantities)
            ),
        )
        qfields = quantity_fields(layout)
        for record in records:
            raw_path = build / record.pop("raw_actions")
            values = np.load(raw_path, mmap_mode="r")
            labels = values.astype(np.int16)
            labels[..., qfields] = np.searchsorted(quantities, values[..., qfields])
            path = raw_path.with_name(raw_path.name.replace("-raw.npy", "-contracts.npy"))
            np.save(path, labels)
            record.update(
                actions=path.name,
                observations_sha256=digest(build / record["observations"]),
                actions_sha256=digest(path),
            )
            record.pop("quantities")
            raw_path.unlink()
        splits: Counter[str] = Counter()
        for record in records:
            splits[record["partition"]] += len(record["episodes"])
        if any(not splits[name] for name in ("train", "validation", "test")):
            raise ValueError("daily BC requires all three complete-episode partitions")
        write_json(
            build / "manifest.json",
            {
                "schema": "daily-work-program-demonstrations-v1",
                "layout": asdict(layout),
                "source": str(source_path),
                "source_sha256": digest(source_path),
                "provenance": provenance(settings),
                "shards": records,
                "rejected": rejected,
                "episode_partitions": dict(splits),
                "elapsed_seconds": time.perf_counter() - started,
                "label_kind": "future work proposals; inputs contain only boundary observations",
                "quantity_semantics": (
                    "Exact observed request vocabulary; unit actions normalized by the shared "
                    "official compiler. No quantity rounding."
                ),
            },
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        build.rename(output)
    except BaseException:
        shutil.rmtree(build)
        raise
    return manifest_path
