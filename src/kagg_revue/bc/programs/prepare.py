"""Parallel construction of compiler-canonical conditional-program shards."""

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
from typing import Any, cast

import orjson
import torch

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.bc.data_config import BcDataSettings
from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.prepare import ensure_raw_manifest, source_inventory
from kagg_revue.bc.programs.config import ProgramBcSettings
from kagg_revue.bc.programs.dataset import save_program_replay_shard
from kagg_revue.bc.programs.translate import translate_program_replay
from kagg_revue.bc.replay import EpisodeLocator, ReplayRejected
from kagg_revue.bc.tasks.replay import load_replay_sequence
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.runtime import load_actor
from kagg_revue.policy.tasks.native import NativeTaskContract


def _resolve(root: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def resolve_program_bc_settings(settings: ProgramBcSettings, root: Path) -> ProgramBcSettings:
    """Resolve all operational paths against one checkout."""
    source = None
    if settings.source is not None:
        source = settings.source.model_copy(
            update={
                "index_archive": _resolve(root, settings.source.index_archive),
                "source_archives": tuple(
                    _resolve(root, path) for path in settings.source.source_archives
                ),
            }
        )
    demonstration = None
    if settings.demonstration_source is not None:
        demonstration = settings.demonstration_source.model_copy(
            update={
                "public_agent_manifest": _resolve(
                    root, settings.demonstration_source.public_agent_manifest
                )
            }
        )
    correction = None
    if settings.correction_source is not None:
        correction = settings.correction_source.model_copy(
            update={
                "student_checkpoint": _resolve(
                    root, settings.correction_source.student_checkpoint
                ),
                "public_agent_manifest": _resolve(
                    root, settings.correction_source.public_agent_manifest
                ),
            }
        )
    aggregate = None
    if settings.aggregate_source is not None:
        aggregate = settings.aggregate_source.model_copy(
            update={
                "components": {
                    name: _resolve(root, path)
                    for name, path in settings.aggregate_source.components.items()
                }
            }
        )
    return settings.model_copy(
        update={
            "dataset_dir": _resolve(root, settings.dataset_dir),
            "output_dir": _resolve(root, settings.output_dir),
            "initial_actor": _resolve(root, settings.initial_actor),
            "initial_checkpoint": (
                _resolve(root, settings.initial_checkpoint)
                if settings.initial_checkpoint is not None
                else None
            ),
            "source": source,
            "demonstration_source": demonstration,
            "correction_source": correction,
            "aggregate_source": aggregate,
        }
    )


def _inventory_settings(settings: ProgramBcSettings) -> BcDataSettings:
    if settings.source is None:
        raise ValueError("daily replay preparation requires a replay source")
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
        f"{seed}:program-bc-partition:{locator.source_date}:{locator.entry}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _partition_population(
    locators: Sequence[EpisodeLocator], settings: ProgramBcSettings
) -> tuple[tuple[EpisodeLocator, ...], dict[str, str], dict[str, object]]:
    if settings.source is None:
        raise ValueError("daily replay preparation requires a replay source")
    by_date: dict[str, list[EpisodeLocator]] = {}
    for locator in locators:
        by_date.setdefault(locator.source_date, []).append(locator)
    if len(by_date) != settings.source.days:
        raise ValueError("program BC inventory has an unexpected number of dates")
    partition_by_episode: dict[str, str] = {}
    days: list[dict[str, object]] = []
    for date in sorted(by_date):
        counts: Counter[str] = Counter()
        for locator in by_date[date]:
            episode_id = Path(locator.entry).stem
            value = _partition_value(settings.optimization.seed, locator)
            if value < settings.source.validation_fraction:
                partition = "validation"
            elif value < (settings.source.validation_fraction + settings.source.test_fraction):
                partition = "test"
            else:
                partition = "train"
            partition_by_episode[episode_id] = partition
            counts[partition] += 1
        if any(counts[name] == 0 for name in ("train", "validation", "test")):
            raise ValueError(f"program BC hash partition is empty for {date}")
        days.append(
            {
                "date": date,
                "source_episodes": len(by_date[date]),
                "partitions": dict(sorted(counts.items())),
            }
        )
    selection: dict[str, object] = {
        "schema_version": "conditional-program-bc-population-partition-v1",
        "semantics": (
            "every episode in the latest declared daily archives; stable episode-level "
            "partitions retain both seats and ignore replay score"
        ),
        "days": days,
        "source_episodes": len(locators),
        "included_episodes": len(partition_by_episode),
        "validation_fraction": settings.source.validation_fraction,
        "test_fraction": settings.source.test_fraction,
        "seed": settings.optimization.seed,
    }
    selection["selection_id"] = hashlib.sha256(
        orjson.dumps(selection, option=orjson.OPT_SORT_KEYS)
    ).hexdigest()
    return tuple(locators), partition_by_episode, selection


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, default=str), encoding="utf-8")
    temporary.replace(path)


@dataclass(frozen=True)
class _EpisodeGroupTask:
    """One process-local native compiler and disjoint episode group."""

    index: int
    locators: tuple[EpisodeLocator, ...]
    partitions: dict[str, str]
    settings: ProgramBcSettings
    repository_root: Path
    build_path: Path
    resolved_environment: dict[str, object]
    actor_architecture: dict[str, object]


@dataclass(frozen=True)
class _EpisodeGroupResult:
    records: tuple[dict[str, object], ...]
    rejected: tuple[dict[str, str], ...]


def _process_episode_group(task: _EpisodeGroupTask) -> _EpisodeGroupResult:
    settings = task.settings
    source = settings.source
    if source is None:
        raise ValueError("daily replay worker requires a replay source")
    torch.set_num_threads(source.worker_cpu_threads)
    backend = load_backend(task.repository_root)
    actor_architecture = ActorArchitecture.model_validate(task.actor_architecture)
    task_contract = NativeTaskContract.from_spec(
        cast(
            Mapping[str, object],
            backend.unit_task_spec(
                task.resolved_environment,
                settings.abi.unit_limit,
                actor_architecture.maximum_quantity,
            ),
        )
    )
    program_contract = NativeProgramContract.from_spec(
        cast(
            Mapping[str, object],
            backend.conditional_program_spec(task.resolved_environment, settings.abi.unit_limit),
        )
    )
    codec = ReplayActionEncoder(cast(Mapping[str, Any], backend.action_codec_spec()))
    records: list[dict[str, object]] = []
    rejected: list[dict[str, str]] = []
    for completed, locator in enumerate(task.locators, start=1):
        episode_id = Path(locator.entry).stem
        try:
            replay = load_replay_sequence(
                locator,
                source.contract,
                task_contract,
                actor_architecture,
            )
            for seat in range(source.contract.agents):
                translated = translate_program_replay(
                    replay,
                    seat,
                    codec,
                    program_contract,
                    backend,
                    semantic=settings.translation == "semantic",
                )
                shard_id = f"episode-{replay.episode_id}-seat-{seat}"
                relative = Path("shards") / f"{shard_id}.npz"
                identity = save_program_replay_shard(task.build_path / relative, translated)
                opponent = 1 - seat
                records.append(
                    {
                        "shard_id": shard_id,
                        "path": relative.as_posix(),
                        **identity,
                        "episode_id": replay.episode_id,
                        "source_date": locator.source_date,
                        "seat": seat,
                        "partition": task.partitions[replay.episode_id],
                        "terminal_cash": float(replay.rewards[seat]),
                        "opponent_cash": float(replay.rewards[opponent]),
                        "statistics": dict(translated.statistics),
                    }
                )
        except ReplayRejected as error:
            rejected.append(
                {
                    "episode_id": episode_id,
                    "source_date": locator.source_date,
                    "reason": error.reason,
                    "detail": error.detail,
                }
            )
        except (KeyError, TypeError, ValueError, RuntimeError) as error:
            rejected.append(
                {
                    "episode_id": episode_id,
                    "source_date": locator.source_date,
                    "reason": "program_translation_failed",
                    "detail": f"{type(error).__name__}: {error}",
                }
            )
        print(
            json.dumps(
                {
                    "worker_group": task.index,
                    "completed_in_group": completed,
                    "episodes_in_group": len(task.locators),
                    "episode": episode_id,
                },
                sort_keys=True,
            ),
            flush=True,
        )
    return _EpisodeGroupResult(tuple(records), tuple(rejected))


def prepare_program_bc_dataset(
    raw_settings: ProgramBcSettings, repository_root: Path
) -> dict[str, object]:
    """Build exact compiler-canonical program shards from daily episodes."""
    root = repository_root.resolve()
    settings = resolve_program_bc_settings(raw_settings, root)
    if settings.source is None:
        raise ValueError("daily replay preparation requires a replay source")
    source = source_identity(root)
    if bool(source["worktree_dirty"]):
        raise RuntimeError("program BC data preparation requires a clean source tree")
    if settings.dataset_dir.exists():
        raise FileExistsError(f"program BC dataset already exists: {settings.dataset_dir}")
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.output_dir / "data-preparation-report.json"
    if report_path.exists():
        raise FileExistsError(f"program BC data report already exists: {report_path}")
    backend = load_backend(root)
    resolved_environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    actor, action_keys, encoder_version, fact_version = load_actor(
        settings.initial_actor, torch.device("cpu")
    )
    actor_architecture = actor.architecture
    if actor_architecture.unit_shape[1] != settings.abi.unit_limit:
        raise ValueError("program BC actor and native unit limits differ")
    contract = NativeProgramContract.from_spec(
        cast(
            Mapping[str, object],
            backend.conditional_program_spec(resolved_environment, settings.abi.unit_limit),
        )
    )
    program_architecture = contract.architecture(
        context_width=actor_architecture.model_width,
        model_width=settings.model.model_width,
        feedforward_width=settings.model.feedforward_width,
    )
    inventory_settings = _inventory_settings(settings)
    index_rows, archive_identities, locators = source_inventory(inventory_settings)
    raw_manifest_path, raw_manifest = ensure_raw_manifest(
        inventory_settings, index_rows, archive_identities
    )
    selected, partition_by_episode, selection = _partition_population(locators, settings)
    (root / "tmp").mkdir(parents=True, exist_ok=True)
    build_path = Path(tempfile.mkdtemp(prefix="conditional-program-bc-data-", dir=root / "tmp"))
    (build_path / "shards").mkdir()
    _write_json(build_path / "selection.json", selection)
    records: list[dict[str, object]] = []
    rejected: list[dict[str, str]] = []
    try:
        workers = min(settings.source.workers, len(selected))
        groups = tuple(tuple(selected[index::workers]) for index in range(workers))
        tasks = [
            _EpisodeGroupTask(
                index=index,
                locators=group,
                partitions=partition_by_episode,
                settings=settings,
                repository_root=root,
                build_path=build_path,
                resolved_environment=resolved_environment,
                actor_architecture=actor_architecture.model_dump(mode="json"),
            )
            for index, group in enumerate(groups)
        ]
        spawn = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=workers, mp_context=spawn) as executor:
            futures = [executor.submit(_process_episode_group, task) for task in tasks]
            for completed, future in enumerate(as_completed(futures), start=1):
                result = future.result()
                records.extend(result.records)
                rejected.extend(result.rejected)
                print(
                    json.dumps(
                        {
                            "completed_worker_groups": completed,
                            "worker_groups": workers,
                            "completed_shards": len(records),
                            "rejected_episodes": len(rejected),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
        rejection_fraction = len(rejected) / len(selected)
        if rejection_fraction > settings.source.maximum_rejection_fraction:
            raise RuntimeError(
                "program BC replay rejection fraction exceeds its maximum: "
                f"{len(rejected)}/{len(selected)}"
            )
        expected = settings.source.contract.agents * (len(selected) - len(rejected))
        if len(records) != expected:
            raise RuntimeError("program BC accepted episodes do not retain every seat")
        records.sort(
            key=lambda row: (
                str(row["source_date"]),
                int(str(row["episode_id"])),
                int(cast(int, row["seat"])),
            )
        )
        partitions = {
            partition: tuple(
                str(row["shard_id"]) for row in records if row["partition"] == partition
            )
            for partition in ("train", "validation", "test")
        }
        repairs: Counter[str] = Counter()
        for row in records:
            statistics = row.get("statistics")
            if isinstance(statistics, Mapping):
                repairs.update(
                    {
                        str(name): int(count)
                        for name, count in statistics.items()
                        if isinstance(count, int) and not isinstance(count, bool)
                    }
                )
        actor_identity = {
            "path": str(settings.initial_actor),
            "sha256": sha256_file(settings.initial_actor),
            "size_bytes": settings.initial_actor.stat().st_size,
            "actor_encoder_version": encoder_version,
            "derived_fact_version": fact_version,
            "action_keys": list(action_keys),
        }
        stable = {
            "raw_manifest_sha256": sha256_file(raw_manifest_path),
            "selection_id": selection["selection_id"],
            "source_actor_sha256": actor_identity["sha256"],
            "actor_architecture": actor_architecture.model_dump(mode="json"),
            "program_architecture": program_architecture.model_dump(mode="json"),
            "native_program_abi": contract.version,
            "translation": settings.translation,
            "shards": [{"shard_id": row["shard_id"], "sha256": row["sha256"]} for row in records],
        }
        dataset_id = hashlib.sha256(orjson.dumps(stable, option=orjson.OPT_SORT_KEYS)).hexdigest()
        manifest: dict[str, object] = {
            "schema_version": "conditional-program-bc-dataset-v1",
            "dataset_id": dataset_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "source": {
                "raw_archive_manifest": {
                    "path": str(raw_manifest_path),
                    "sha256": sha256_file(raw_manifest_path),
                },
                "raw_archives": raw_manifest,
                "source_revision": source,
                "rejected": rejected,
            },
            "source_actor_identity": actor_identity,
            "native_backend": backend.identity,
            "native_program_abi": contract.version,
            "actor_architecture": actor_architecture.model_dump(mode="json"),
            "program_architecture": program_architecture.model_dump(mode="json"),
            "action_keys": list(action_keys),
            "environment": resolved_environment,
            "translation": {
                "teacher": (
                    "replay-suffix semantic proposals with native exact-equivalence fallback"
                    if settings.translation == "semantic"
                    else "compiler-in-the-loop legal raw programs"
                ),
                "mode": settings.translation,
                "unit_actions": (
                    "KEEP or ASSIGN when native-equivalent; otherwise STEP, RAW_LOCAL, "
                    "or CANCEL_PASS"
                    if settings.translation == "semantic"
                    else "STEP, RAW_LOCAL, or CANCEL_PASS"
                ),
                "market_actions": "ordered effective actions with empty slots compacted",
                "quantities": "ONE or bounded EXACT effective quantities",
                "history": "compiler-canonical numeric actions",
                "scheduled_sampling": False,
                "canonical_repairs": dict(sorted(repairs.items())),
            },
            "selection": selection,
            "partitions": partitions,
            "shards": records,
        }
        _write_json(build_path / "manifest.json", manifest)
        settings.dataset_dir.parent.mkdir(parents=True, exist_ok=True)
        build_path.replace(settings.dataset_dir)
        report: dict[str, object] = {
            "schema_version": "conditional-program-bc-data-report-v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "dataset": {
                "path": str(settings.dataset_dir),
                "manifest_sha256": sha256_file(settings.dataset_dir / "manifest.json"),
                "dataset_id": dataset_id,
                "shards": len(records),
            },
            "source": manifest["source"],
            "selection": selection,
            "translation": manifest["translation"],
            "partitions": {name: len(values) for name, values in partitions.items()},
        }
        _write_json(report_path, report)
        return report
    finally:
        if build_path.exists():
            shutil.rmtree(build_path)


__all__ = ["prepare_program_bc_dataset", "resolve_program_bc_settings"]
