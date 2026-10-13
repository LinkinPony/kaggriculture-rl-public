"""Build compact program-BC data from one coherent frozen teacher."""

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
from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.programs.config import ProgramBcSettings
from kagg_revue.bc.programs.dataset import save_program_replay_shard
from kagg_revue.bc.programs.demonstration import collect_demonstration
from kagg_revue.bc.programs.prepare import resolve_program_bc_settings
from kagg_revue.bc.programs.translate import translate_program_replay
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.opponents.registry import trusted_runtime_identity
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.runtime import load_actor


@dataclass(frozen=True)
class _GenerationTask:
    """One process-local group of paired-seat demonstration seeds."""

    seeds: tuple[int, ...]
    repository_root: Path
    build_path: Path
    environment: dict[str, object]
    actor_architecture: dict[str, object]
    unit_limit: int
    teacher: str
    opponent: str
    partitions: dict[int, str]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    temporary.replace(path)


def _partition_value(seed: int, partition_seed: int) -> float:
    digest = hashlib.sha256(
        f"{partition_seed}:program-demonstration:{seed}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _partitions(
    seeds: Sequence[int],
    *,
    partition_seed: int,
    validation_fraction: float,
    test_fraction: float,
    semantics: str = (
        "paired seats from one frozen authenticated teacher against one frozen "
        "authenticated opponent; no replay-score or cash filtering"
    ),
) -> tuple[dict[int, str], dict[str, object]]:
    partitions: dict[int, str] = {}
    counts: Counter[str] = Counter()
    for seed in seeds:
        value = _partition_value(seed, partition_seed)
        if value < validation_fraction:
            partition = "validation"
        elif value < validation_fraction + test_fraction:
            partition = "test"
        else:
            partition = "train"
        partitions[seed] = partition
        counts[partition] += 1
    if any(counts[name] == 0 for name in ("train", "validation", "test")):
        raise ValueError("program demonstration hash partition is empty")
    selection: dict[str, object] = {
        "schema_version": "conditional-program-demonstration-partition-v1",
        "semantics": semantics,
        "seeds": len(seeds),
        "seed_start": min(seeds),
        "seed_stop": max(seeds) + 1,
        "validation_fraction": validation_fraction,
        "test_fraction": test_fraction,
        "partition_seed": partition_seed,
        "partitions": dict(sorted(counts.items())),
    }
    selection["selection_id"] = hashlib.sha256(
        orjson.dumps(selection, option=orjson.OPT_SORT_KEYS)
    ).hexdigest()
    return partitions, selection


def _generate_group(task: _GenerationTask) -> list[dict[str, object]]:
    torch.set_num_threads(1)
    backend = load_backend(task.repository_root)
    architecture = ActorArchitecture.model_validate(task.actor_architecture)
    engine = backend.engine(seed=0, configuration=task.environment)
    environment = cast(dict[str, object], dict(engine.configuration))
    contract = NativeProgramContract.from_spec(
        cast(
            Mapping[str, object],
            backend.conditional_program_spec(environment, task.unit_limit),
        )
    )
    codec = ReplayActionEncoder(cast(Mapping[str, Any], backend.action_codec_spec()))
    records: list[dict[str, object]] = []
    for seed in task.seeds:
        for teacher_seat in (0, 1):
            replay = collect_demonstration(
                backend,
                seed=seed,
                teacher_seat=teacher_seat,
                teacher_id=task.teacher,
                opponent_id=task.opponent,
                environment=environment,
                architecture=architecture,
                unit_limit=task.unit_limit,
            )
            translated = translate_program_replay(
                replay, teacher_seat, codec, contract, backend
            )
            shard_id = f"demonstration-{seed}-teacher-seat-{teacher_seat}"
            relative = Path("shards") / f"{shard_id}.npz"
            identity = save_program_replay_shard(task.build_path / relative, translated)
            opponent_seat = 1 - teacher_seat
            records.append(
                {
                    "shard_id": shard_id,
                    "path": str(relative),
                    **identity,
                    "episode_id": replay.episode_id,
                    "source_date": "frozen-native-demonstration",
                    "seat": teacher_seat,
                    "partition": task.partitions[seed],
                    "terminal_cash": replay.rewards[teacher_seat],
                    "opponent_cash": replay.rewards[opponent_seat],
                    "outcome": int(
                        replay.rewards[teacher_seat] > replay.rewards[opponent_seat]
                    )
                    - int(replay.rewards[teacher_seat] < replay.rewards[opponent_seat]),
                    "statistics": dict(translated.statistics),
                }
            )
    return records


def _agent_identities(
    backend: Any, manifest_path: Path, agent_ids: Sequence[str]
) -> dict[str, object]:
    manifest = backend.load_public_agent_manifest(manifest_path)
    records = manifest.by_id()
    identities: dict[str, object] = {}
    for agent_id in agent_ids:
        record = records.get(agent_id)
        runtime = None if record is None else trusted_runtime_identity(record)
        if record is None or runtime is None or agent_id not in backend.native_opponent_batch_steps:
            raise ValueError(
                f"program demonstration requires an authenticated native agent: {agent_id}"
            )
        identities[agent_id] = {
            "notebook_ref": record.notebook_ref,
            "notebook_id": record.notebook_id,
            "source_artifact_sha256": record.sha256,
            "native_runtime": runtime,
        }
    return identities


def prepare_program_demonstrations(
    raw_settings: ProgramBcSettings, repository_root: Path
) -> dict[str, object]:
    """Generate paired official-horizon demonstrations without route mixing."""
    root = repository_root.resolve()
    settings = resolve_program_bc_settings(raw_settings, root)
    demonstration = settings.demonstration_source
    if demonstration is None:
        raise ValueError("native demonstration preparation requires a demonstration source")
    source = source_identity(root)
    if bool(source["worktree_dirty"]):
        raise RuntimeError("program demonstration preparation requires a clean source tree")
    if settings.dataset_dir.exists():
        raise FileExistsError(f"program BC dataset already exists: {settings.dataset_dir}")
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.output_dir / "data-preparation-report.json"
    if report_path.exists():
        raise FileExistsError(f"program BC data report already exists: {report_path}")

    backend = load_backend(root)
    environment = cast(
        dict[str, object],
        dict(backend.engine(seed=0, configuration=settings.environment).configuration),
    )
    identities = _agent_identities(
        backend,
        demonstration.public_agent_manifest,
        (demonstration.teacher, demonstration.opponent),
    )
    actor, action_keys, encoder_version, fact_version = load_actor(
        settings.initial_actor, torch.device("cpu")
    )
    architecture = actor.architecture
    if architecture.unit_shape[1] != settings.abi.unit_limit:
        raise ValueError("program demonstration actor and native unit limits differ")
    contract = NativeProgramContract.from_spec(
        cast(
            Mapping[str, object],
            backend.conditional_program_spec(environment, settings.abi.unit_limit),
        )
    )
    program_architecture = contract.architecture(
        context_width=architecture.model_width,
        model_width=settings.model.model_width,
        feedforward_width=settings.model.feedforward_width,
    )
    seeds = tuple(
        range(demonstration.seed_start, demonstration.seed_start + demonstration.seeds)
    )
    partitions_by_seed, selection = _partitions(
        seeds,
        partition_seed=settings.optimization.seed,
        validation_fraction=demonstration.validation_fraction,
        test_fraction=demonstration.test_fraction,
    )

    (root / "tmp").mkdir(parents=True, exist_ok=True)
    build_path = Path(
        tempfile.mkdtemp(prefix="program-demonstrations-", dir=root / "tmp")
    )
    (build_path / "shards").mkdir()
    records: list[dict[str, object]] = []
    try:
        workers = min(demonstration.workers, len(seeds))
        groups = tuple(tuple(seeds[index::workers]) for index in range(workers))
        tasks = tuple(
            _GenerationTask(
                seeds=group,
                repository_root=root,
                build_path=build_path,
                environment=environment,
                actor_architecture=architecture.model_dump(mode="json"),
                unit_limit=settings.abi.unit_limit,
                teacher=demonstration.teacher,
                opponent=demonstration.opponent,
                partitions=partitions_by_seed,
            )
            for group in groups
        )
        spawn = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(max_workers=workers, mp_context=spawn) as executor:
            futures = [executor.submit(_generate_group, task) for task in tasks]
            for completed, future in enumerate(as_completed(futures), start=1):
                records.extend(future.result())
                print(
                    json.dumps(
                        {
                            "completed_worker_groups": completed,
                            "worker_groups": workers,
                            "completed_shards": len(records),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
        records.sort(key=lambda row: str(row["shard_id"]))
        partitions = {
            partition: tuple(
                str(row["shard_id"])
                for row in records
                if row["partition"] == partition
            )
            for partition in ("train", "validation", "test")
        }
        repairs: Counter[str] = Counter()
        outcomes: Counter[int] = Counter()
        for row in records:
            repairs.update(cast(Mapping[str, int], row["statistics"]))
            outcomes[int(cast(int, row["outcome"]))] += 1
        actor_identity = {
            "path": str(settings.initial_actor),
            "sha256": sha256_file(settings.initial_actor),
            "size_bytes": settings.initial_actor.stat().st_size,
            "actor_encoder_version": encoder_version,
            "derived_fact_version": fact_version,
            "action_keys": list(action_keys),
        }
        stable = {
            "selection_id": selection["selection_id"],
            "teacher": identities[demonstration.teacher],
            "opponent": identities[demonstration.opponent],
            "source_actor_sha256": actor_identity["sha256"],
            "actor_architecture": architecture.model_dump(mode="json"),
            "program_architecture": program_architecture.model_dump(mode="json"),
            "native_program_abi": contract.version,
            "shards": [
                {"shard_id": row["shard_id"], "sha256": row["sha256"]}
                for row in records
            ],
        }
        dataset_id = hashlib.sha256(
            orjson.dumps(stable, option=orjson.OPT_SORT_KEYS)
        ).hexdigest()
        manifest: dict[str, object] = {
            "schema_version": "conditional-program-bc-dataset-v1",
            "dataset_id": dataset_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "source": {
                "kind": "frozen_native_demonstration",
                "source_revision": source,
                "teacher": {
                    "agent_id": demonstration.teacher,
                    **cast(dict[str, object], identities[demonstration.teacher]),
                },
                "opponent": {
                    "agent_id": demonstration.opponent,
                    **cast(dict[str, object], identities[demonstration.opponent]),
                },
                "public_agent_manifest": {
                    "path": str(demonstration.public_agent_manifest),
                    "sha256": sha256_file(demonstration.public_agent_manifest),
                },
            },
            "source_actor_identity": actor_identity,
            "native_backend": backend.identity,
            "native_program_abi": contract.version,
            "actor_architecture": architecture.model_dump(mode="json"),
            "program_architecture": program_architecture.model_dump(mode="json"),
            "action_keys": list(action_keys),
            "environment": environment,
            "translation": {
                "teacher": "one frozen native lineage in both seats",
                "opponent": "one frozen native lineage",
                "history": "compiler-canonical teacher actions",
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
            "teacher_outcomes": {
                "wins": outcomes[1],
                "ties": outcomes[0],
                "losses": outcomes[-1],
            },
        }
        _write_json(report_path, report)
        return report
    finally:
        if build_path.exists():
            shutil.rmtree(build_path)


__all__ = ["prepare_program_demonstrations"]
