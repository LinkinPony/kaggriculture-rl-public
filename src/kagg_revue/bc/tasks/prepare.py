"""Provenance-bound construction of K=2 unit-task BC shards."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import numpy as np
import orjson
import torch

from kagg_revue.bc.data_config import BcDataSettings
from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.prepare import ensure_raw_manifest, source_inventory
from kagg_revue.bc.replay import EpisodeLocator, ReplayRejected
from kagg_revue.bc.tasks.config import TaskBcSettings
from kagg_revue.bc.tasks.dataset import save_sequence_shard
from kagg_revue.bc.tasks.model import build_actor_architecture
from kagg_revue.bc.tasks.replay import load_replay_sequence
from kagg_revue.bc.tasks.translate import translate_sequence
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.tasks.native import NativeTaskContract


def _resolve(root: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def resolve_task_bc_settings(settings: TaskBcSettings, root: Path) -> TaskBcSettings:
    """Resolve every operational path against one repository checkout."""
    source = settings.source.model_copy(
        update={
            "index_archive": _resolve(root, settings.source.index_archive),
            "source_archives": tuple(
                _resolve(root, path) for path in settings.source.source_archives
            ),
        }
    )
    evaluation = settings.evaluation.model_copy(
        update={
            "public_agent_manifest": _resolve(
                root, settings.evaluation.public_agent_manifest
            )
        }
    )
    return settings.model_copy(
        update={
            "dataset_dir": _resolve(root, settings.dataset_dir),
            "output_dir": _resolve(root, settings.output_dir),
            "resume_policy_checkpoint": (
                _resolve(root, settings.resume_policy_checkpoint)
                if settings.resume_policy_checkpoint is not None
                else None
            ),
            "source": source,
            "evaluation": evaluation,
        }
    )


def _inventory_settings(settings: TaskBcSettings) -> BcDataSettings:
    return BcDataSettings(
        index_archive=settings.source.index_archive,
        source_archives=settings.source.source_archives,
        output_dir=settings.dataset_dir,
        report_dir=settings.output_dir,
        days=settings.source.days,
        episodes_per_shard=1,
        workers=settings.source.workers,
        maximum_rejection_fraction=settings.source.maximum_rejection_fraction,
        contract=settings.source.contract,
        opening_diversity=None,
    )


def _partition_value(seed: int, locator: EpisodeLocator) -> float:
    digest = hashlib.sha256(
        f"{seed}:partition:{locator.source_date}:{locator.entry}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _partition_population(
    locators: Sequence[EpisodeLocator],
    settings: TaskBcSettings,
) -> tuple[tuple[EpisodeLocator, ...], dict[str, str], dict[str, object]]:
    by_date: dict[str, list[EpisodeLocator]] = {}
    for locator in locators:
        by_date.setdefault(locator.source_date, []).append(locator)
    if len(by_date) != settings.source.days:
        raise ValueError("task BC inventory has an unexpected number of dates")
    partition_by_episode: dict[str, str] = {}
    daily_reports: list[dict[str, object]] = []
    for date in sorted(by_date):
        counts: Counter[str] = Counter()
        for locator in by_date[date]:
            episode_id = Path(locator.entry).stem
            value = _partition_value(settings.sampling.seed, locator)
            if value < settings.source.validation_fraction:
                partition = "validation"
            elif value < settings.source.validation_fraction + settings.source.test_fraction:
                partition = "test"
            else:
                partition = "train"
            partition_by_episode[episode_id] = partition
            counts[partition] += 1
        if any(counts[partition] == 0 for partition in ("train", "validation", "test")):
            raise ValueError(f"task BC hash partition is empty for {date}")
        daily_reports.append(
            {
                "date": date,
                "source_episodes": len(by_date[date]),
                "partitions": dict(sorted(counts.items())),
            }
        )
    selection: dict[str, object] = {
        "schema_version": "unit-task-bc-population-partition-v1",
        "semantics": (
            "every episode in every declared daily archive, partitioned by a "
            "stable episode hash; scores, agent names, and opening identity are ignored"
        ),
        "days": daily_reports,
        "source_episodes": len(locators),
        "included_episodes": len(partition_by_episode),
        "validation_fraction": settings.source.validation_fraction,
        "test_fraction": settings.source.test_fraction,
        "seed": settings.sampling.seed,
    }
    selection["selection_id"] = hashlib.sha256(
        orjson.dumps(selection, option=orjson.OPT_SORT_KEYS)
    ).hexdigest()
    return tuple(locators), partition_by_episode, selection


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def _merge_numeric_counter(
    target: Counter[str],
    value: object,
) -> None:
    if not isinstance(value, Mapping):
        return
    for key, count in value.items():
        if isinstance(count, int | float) and not isinstance(count, bool):
            target[str(key)] += int(count)


@dataclass(frozen=True)
class _EpisodeGroupTask:
    """One worker-local compiler and a disjoint subset of complete episodes."""

    index: int
    locators: tuple[EpisodeLocator, ...]
    partitions: dict[str, str]
    settings: TaskBcSettings
    repository_root: Path
    build_path: Path
    resolved_environment: dict[str, object]


@dataclass(frozen=True)
class _EpisodeGroupResult:
    """Accepted shards and explicit replay rejections from one worker."""

    records: tuple[dict[str, object], ...]
    rejected: tuple[dict[str, str], ...]


def _process_episode_group(task: _EpisodeGroupTask) -> _EpisodeGroupResult:
    """Compile a disjoint episode group without model-dependent contexts."""
    settings = task.settings
    torch.set_num_threads(settings.source.worker_cpu_threads)
    backend = load_backend(task.repository_root)
    contract = NativeTaskContract.from_spec(
        cast(
            Mapping[str, object],
            backend.unit_task_spec(
                task.resolved_environment,
                settings.abi.unit_limit,
                settings.abi.maximum_quantity,
            ),
        )
    )
    actor_architecture, _action_keys = build_actor_architecture(
        backend,
        task.resolved_environment,
        settings.abi.unit_limit,
        settings.actor,
    )
    task_architecture = contract.architecture(
        architecture_version=settings.model.architecture_version,
        context_width=actor_architecture.model_width,
        model_width=settings.model.model_width,
        feedforward_width=settings.model.feedforward_width,
        attention_heads=settings.model.attention_heads,
        prefix_layers=settings.model.prefix_layers,
        history_window=settings.model.history_window,
    )
    records: list[dict[str, object]] = []
    rejected: list[dict[str, str]] = []
    for completed, locator in enumerate(task.locators, start=1):
        episode_id = Path(locator.entry).stem
        try:
            replay = load_replay_sequence(
                locator,
                settings.source.contract,
                contract,
                actor_architecture,
            )
            replay_environment = cast(
                dict[str, object],
                backend.engine(
                    seed=0, configuration=dict(replay.configuration)
                ).configuration,
            )
            if replay_environment != task.resolved_environment:
                raise ReplayRejected(
                    "environment_mismatch",
                    "replay configuration resolves differently from the BC runtime",
                )
            zero_context = np.zeros(
                (replay.turns, actor_architecture.model_width),
                dtype=np.float16,
            )
            translated_seats = tuple(
                translate_sequence(
                    backend,
                    replay,
                    zero_context,
                    contract,
                    seat,
                    tasks_per_suffix=settings.sampling.tasks_per_suffix,
                    sample_capacity=settings.sampling.decisions_per_sequence,
                    sampling_seed=settings.sampling.seed,
                    factorized=(
                        settings.model.architecture_version == "factorized-v3"
                    ),
                    history_window=task_architecture.history_window,
                )
                for seat in range(settings.source.contract.agents)
            )
        except ReplayRejected as error:
            rejection = {
                "episode_id": episode_id,
                "source_date": locator.source_date,
                "reason": error.reason,
                "detail": error.detail,
            }
            rejected.append(rejection)
            print(
                json.dumps(
                    {
                        "worker_group": task.index,
                        "completed_in_group": completed,
                        "episodes_in_group": len(task.locators),
                        "rejected": rejection,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            continue
        for seat, translated in enumerate(translated_seats):
            partition = task.partitions[episode_id]
            shard_id = f"episode-{episode_id}-seat-{seat}"
            relative = Path("shards") / f"{shard_id}.npz"
            identity = save_sequence_shard(
                task.build_path / relative,
                translated,
                replay,
                seat,
            )
            records.append(
                {
                    "shard_id": shard_id,
                    "path": str(relative),
                    "episode_id": episode_id,
                    "source_date": locator.source_date,
                    "seat": seat,
                    "partition": partition,
                    **identity,
                    "statistics": dict(translated.statistics),
                }
            )
        print(
            json.dumps(
                {
                    "worker_group": task.index,
                    "completed_in_group": completed,
                    "episodes_in_group": len(task.locators),
                    "episode": replay.episode_id,
                },
                sort_keys=True,
            ),
            flush=True,
        )
    return _EpisodeGroupResult(tuple(records), tuple(rejected))


def prepare_task_bc_dataset(
    raw_settings: TaskBcSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Build exact compiler-validated shards from the latest daily episodes."""
    root = repository_root.resolve()
    settings = resolve_task_bc_settings(raw_settings, root)
    if settings.dataset_dir.exists():
        raise FileExistsError(f"task BC dataset already exists: {settings.dataset_dir}")
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.output_dir / "data-preparation-report.json"
    if report_path.exists():
        raise FileExistsError(f"task BC data report already exists: {report_path}")
    backend = load_backend(root)
    resolved_environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    contract = NativeTaskContract.from_spec(
        cast(
            Mapping[str, object],
            backend.unit_task_spec(
                resolved_environment,
                settings.abi.unit_limit,
                settings.abi.maximum_quantity,
            ),
        )
    )
    torch.set_num_threads(settings.source.worker_cpu_threads)
    actor_architecture_value, action_keys = build_actor_architecture(
        backend,
        resolved_environment,
        settings.abi.unit_limit,
        settings.actor,
    )
    task_architecture_value = contract.architecture(
        architecture_version=settings.model.architecture_version,
        context_width=actor_architecture_value.model_width,
        model_width=settings.model.model_width,
        feedforward_width=settings.model.feedforward_width,
        attention_heads=settings.model.attention_heads,
        prefix_layers=settings.model.prefix_layers,
        history_window=settings.model.history_window,
    )
    actor_architecture = actor_architecture_value.model_dump(mode="json")
    task_architecture = task_architecture_value.model_dump(mode="json")

    inventory_settings = _inventory_settings(settings)
    index_rows, archive_identities, locators = source_inventory(inventory_settings)
    raw_manifest_path, raw_manifest = ensure_raw_manifest(
        inventory_settings,
        index_rows,
        archive_identities,
    )
    selected, partition_by_episode, selection = _partition_population(
        locators, settings
    )
    (root / "tmp").mkdir(parents=True, exist_ok=True)
    build_path = Path(
        tempfile.mkdtemp(prefix="unit-task-bc-data-", dir=root / "tmp")
    )
    shards_dir = build_path / "shards"
    shards_dir.mkdir()
    _write_json(build_path / "selection.json", selection)
    shard_records: list[dict[str, object]] = []
    rejected: list[dict[str, str]] = []
    aggregate_kinds: Counter[str] = Counter()
    aggregate_operations: Counter[str] = Counter()
    aggregate_sampled_operations: Counter[str] = Counter()
    aggregate_factors: Counter[str] = Counter()
    aggregate_replay_repairs: Counter[str] = Counter()
    try:
        worker_count = min(settings.source.workers, len(selected))
        episode_groups = tuple(
            tuple(selected[index::worker_count]) for index in range(worker_count)
        )
        tasks = [
            _EpisodeGroupTask(
                index=index,
                locators=group,
                partitions=partition_by_episode,
                settings=settings,
                repository_root=root,
                build_path=build_path,
                resolved_environment=resolved_environment,
            )
            for index, group in enumerate(episode_groups)
        ]
        spawn = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=worker_count,
            mp_context=spawn,
        ) as executor:
            futures = [executor.submit(_process_episode_group, task) for task in tasks]
            for completed, future in enumerate(as_completed(futures), start=1):
                result = future.result()
                shard_records.extend(result.records)
                rejected.extend(result.rejected)
                print(
                    json.dumps(
                        {
                            "completed_worker_groups": completed,
                            "worker_groups": worker_count,
                            "completed_shards": len(shard_records),
                            "rejected_episodes": len(rejected),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
        rejection_fraction = len(rejected) / len(selected)
        if rejection_fraction > settings.source.maximum_rejection_fraction:
            raise RuntimeError(
                "task BC replay rejection fraction exceeds its declared maximum: "
                f"{len(rejected)}/{len(selected)}"
            )
        expected_shards = settings.source.contract.agents * (
            len(selected) - len(rejected)
        )
        if len(shard_records) != expected_shards:
            raise RuntimeError("task BC accepted episodes do not have every seat shard")
        shard_records.sort(
            key=lambda record: (
                str(record["source_date"]),
                int(str(record["episode_id"])),
                cast(int, record["seat"]),
            )
        )
        for record in shard_records:
            statistics = record["statistics"]
            if not isinstance(statistics, Mapping):
                raise TypeError("task BC shard statistics must be a mapping")
            _merge_numeric_counter(
                aggregate_kinds, statistics.get("decision_kinds")
            )
            _merge_numeric_counter(
                aggregate_operations, statistics.get("operation_counts")
            )
            _merge_numeric_counter(
                aggregate_sampled_operations,
                statistics.get("sampled_operation_counts"),
            )
            _merge_numeric_counter(
                aggregate_factors,
                statistics.get("sampled_active_factor_counts"),
            )
            _merge_numeric_counter(
                aggregate_replay_repairs,
                statistics.get("replay_repairs"),
            )
        partitions = {
            partition: tuple(
                str(record["shard_id"])
                for record in shard_records
                if record["partition"] == partition
            )
            for partition in ("train", "validation", "test")
        }
        stable_identity = {
            "raw_manifest_sha256": sha256_file(raw_manifest_path),
            "selection_id": selection["selection_id"],
            "model_initialization": "random_at_training",
            "actor_architecture": actor_architecture,
            "task_architecture": task_architecture,
            "native_task_abi": contract.version,
            "catalog_fingerprint": contract.catalog_fingerprint,
            "translation": {
                "suffix_tasks": settings.sampling.tasks_per_suffix,
                "reservoir_decisions_per_sequence": (
                    settings.sampling.decisions_per_sequence
                ),
                "reservoir_seed": settings.sampling.seed,
            },
            "shards": [
                {"shard_id": row["shard_id"], "sha256": row["sha256"]}
                for row in shard_records
            ],
        }
        dataset_id = hashlib.sha256(
            orjson.dumps(stable_identity, option=orjson.OPT_SORT_KEYS)
        ).hexdigest()
        manifest: dict[str, object] = {
            "schema_version": "unit-task-scratch-bc-dataset-v3",
            "dataset_id": dataset_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "source": {
                "raw_archive_manifest": {
                    "path": str(raw_manifest_path),
                    "sha256": sha256_file(raw_manifest_path),
                },
                "raw_archives": raw_manifest,
                "source_revision": source_identity(root),
                "rejected": rejected,
            },
            "source_actor_identity": None,
            "initialization_contract": {
                "kind": "random",
                "weight_artifact_imported": False,
                "optimizer_imported": False,
                "rng_imported": False,
            },
            "native_backend": backend.identity,
            "native_task_abi": contract.version,
            "catalog_fingerprint": contract.catalog_fingerprint,
            "actor_architecture": actor_architecture,
            "task_architecture": task_architecture,
            "action_keys": list(action_keys),
            "environment": resolved_environment,
            "translation": {
                "task_tape": "rolling suffix",
                "tasks_per_suffix": settings.sampling.tasks_per_suffix,
                "continue_when_legal": True,
                "active_end_is_supervised": True,
                "teacher_forcing": "compiler-in-the-loop exact conditional masks",
                "scheduled_sampling": False,
                "sampling": {
                    "kind": "uniform per-sequence reservoir",
                    "decisions_per_sequence": (
                        settings.sampling.decisions_per_sequence
                    ),
                    "seed": settings.sampling.seed,
                    "objective": "equal sequence mean of conditional joint NLL",
                },
                "complete_stream_gate": (
                    "every compiled unit action equals the semantically canonicalized "
                    "replay unit request"
                ),
                "canonical_replay_repairs": dict(
                    sorted(aggregate_replay_repairs.items())
                ),
                "aggregate_decision_kinds": dict(sorted(aggregate_kinds.items())),
                "aggregate_operation_counts": dict(
                    sorted(aggregate_operations.items())
                ),
                "aggregate_sampled_operation_counts": dict(
                    sorted(aggregate_sampled_operations.items())
                ),
                "aggregate_sampled_active_factor_counts": dict(
                    sorted(aggregate_factors.items())
                ),
            },
            "selection": selection,
            "partitions": partitions,
            "shards": shard_records,
        }
        _write_json(build_path / "manifest.json", manifest)
        manifest_identity = {
            "path": str(settings.dataset_dir / "manifest.json"),
            "sha256": sha256_file(build_path / "manifest.json"),
            "dataset_id": dataset_id,
            "shards": len(shard_records),
            "sampled_decisions": sum(
                cast(int, record["sampled_decisions"]) for record in shard_records
            ),
        }
        settings.dataset_dir.parent.mkdir(parents=True, exist_ok=True)
        build_path.replace(settings.dataset_dir)
    except BaseException:
        shutil.rmtree(build_path, ignore_errors=True)
        raise
    report: dict[str, object] = {
        "schema_version": "unit-task-bc-data-report-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "complete",
        "dataset": manifest_identity,
        "dates": [row["date"] for row in index_rows],
        "source_archives": archive_identities,
        "model_initialization": {
            "kind": "random_at_training",
            "precomputed_actor_context": False,
        },
        "preparation_execution": {
            "device": "cpu",
            "reason": "model-independent native replay translation",
        },
        "native_task_abi": contract.version,
        "catalog_fingerprint": contract.catalog_fingerprint,
        "translation": manifest["translation"],
        "selection": selection,
        "partitions": partitions,
    }
    _write_json(report_path, report)
    return report


__all__ = ["prepare_task_bc_dataset", "resolve_task_bc_settings"]
