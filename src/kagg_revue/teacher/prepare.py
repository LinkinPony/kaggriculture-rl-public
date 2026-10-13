"""Parallel construction of provenance-bound teacher data."""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import orjson

from kagg_revue.bc.dataset import SourceManifest, sha256_file
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.native import _revue_native as native
from kagg_revue.teacher.config import TeacherDataSettings
from kagg_revue.teacher.rollout import (
    TeacherShardResult,
    TeacherShardTask,
    generate_teacher_shard,
    load_teacher_shard_checkpoint,
)
from kagg_revue.teacher.submission import (
    SubmissionTeacherArtifact,
    load_submission_teacher,
)


def _resolve(root: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def resolve_paths(settings: TeacherDataSettings, root: Path) -> TeacherDataSettings:
    """Resolve all operational paths relative to the repository checkout."""
    teacher = settings.teacher.model_copy(
        update={"archive_path": _resolve(root, settings.teacher.archive_path)}
    )
    return settings.model_copy(
        update={
            "teacher": teacher,
            "output_dir": _resolve(root, settings.output_dir),
            "report_dir": _resolve(root, settings.report_dir),
        }
    )


def _require_within(path: Path, parent: Path, name: str) -> None:
    if not path.is_relative_to(parent.resolve()):
        raise ValueError(f"{name} must be under {parent.resolve()}")


def _write_json(path: Path, value: Mapping[str, object], *, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite artifact metadata: {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _incomplete_path(path: Path) -> Path:
    return path.with_name(path.name + ".incomplete")


def _generation_spec(
    settings: TeacherDataSettings, source: Mapping[str, object]
) -> dict[str, object]:
    return {
        "settings": settings.model_dump(mode="json"),
        "source": dict(source),
    }


def _load_or_create_generation_state(
    path: Path,
    settings: TeacherDataSettings,
    source: Mapping[str, object],
) -> dict[str, object]:
    spec = _generation_spec(settings, source)
    generation_id = hashlib.sha256(orjson.dumps(spec, option=orjson.OPT_SORT_KEYS)).hexdigest()
    if path.exists():
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise TypeError("teacher generation state must be a mapping")
        if value.get("schema_version") != "submission-teacher-generation-state-v1":
            raise ValueError("teacher generation state schema differs")
        if value.get("generation_id") != generation_id or value.get("spec") != spec:
            raise ValueError("incomplete teacher dataset belongs to different settings or source")
        attempts = _integer(value.get("attempts"), "generation attempts") + 1
        value["attempts"] = attempts
        value["last_started_at"] = datetime.now(UTC).isoformat()
        _write_json(path, value, overwrite=True)
        return value
    value = {
        "schema_version": "submission-teacher-generation-state-v1",
        "generation_id": generation_id,
        "created_at": datetime.now(UTC).isoformat(),
        "last_started_at": datetime.now(UTC).isoformat(),
        "attempts": 1,
        "spec": spec,
    }
    _write_json(path, value)
    return value


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    return value


def _source_manifest(settings: TeacherDataSettings, root: Path) -> dict[str, object]:
    path = settings.teacher.archive_path.parent / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"submission teacher source manifest does not exist: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise TypeError("submission teacher source manifest must be a mapping")
    expected = {
        "submission_id": settings.teacher.submission_id,
        "archive_sha256": settings.teacher.archive_sha256,
        "source_commit": settings.teacher.source_commit,
        "route_sha256": settings.teacher.route_sha256,
    }
    for name, target in expected.items():
        if value.get(name) != target:
            raise ValueError(f"submission teacher source manifest differs at {name}")
    return {
        "path": str(path.relative_to(root)),
        "sha256": sha256_file(path),
        "schema_version": value.get("schema_version"),
    }


def _tasks(
    settings: TeacherDataSettings,
    output_dir: Path,
) -> list[TeacherShardTask]:
    seeds = range(settings.seed_start, settings.seed_start + settings.games)
    tasks: list[TeacherShardTask] = []
    for index, offset in enumerate(range(0, settings.games, settings.games_per_shard)):
        task_seeds = tuple(seeds[offset : offset + settings.games_per_shard])
        tasks.append(
            TeacherShardTask(
                index=index,
                seeds=task_seeds,
                output_path=output_dir / f"teacher-{index:05d}.npz",
                artifact=settings.teacher,
                environment=settings.environment,
                unit_limit=settings.unit_limit,
                policy_workers=settings.policy_workers,
                compression_level=settings.compression_level,
            )
        )
    return tasks


def _progress(result: TeacherShardResult, completed: int, total: int) -> None:
    print(
        json.dumps(
            {
                "completed_shards": completed,
                "total_shards": total,
                "shard_index": result.index,
                "games": result.games,
                "turns": result.shard["turns"],
                "elapsed_seconds": round(result.elapsed_seconds, 3),
            },
            sort_keys=True,
        ),
        flush=True,
    )


def _run_tasks(
    tasks: Sequence[TeacherShardTask],
    workers: int,
    *,
    completed_offset: int = 0,
    total_tasks: int | None = None,
) -> list[TeacherShardResult]:
    if not tasks:
        return []
    progress_total = len(tasks) if total_tasks is None else total_tasks
    effective_workers = min(workers, len(tasks))
    if effective_workers == 1:
        results = []
        for completed, task in enumerate(tasks, start=1):
            result = generate_teacher_shard(task)
            results.append(result)
            _progress(result, completed_offset + completed, progress_total)
        return results
    results = []
    with ProcessPoolExecutor(max_workers=effective_workers) as executor:
        futures = {executor.submit(generate_teacher_shard, task): task for task in tasks}
        for completed, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            results.append(result)
            _progress(result, completed_offset + completed, progress_total)
    return sorted(results, key=lambda result: result.index)


def _resume_results(
    tasks: Sequence[TeacherShardTask],
) -> tuple[list[TeacherShardResult], list[TeacherShardTask]]:
    completed: list[TeacherShardResult] = []
    pending: list[TeacherShardTask] = []
    for task in tasks:
        result = load_teacher_shard_checkpoint(task)
        if result is None:
            pending.append(task)
        else:
            completed.append(result)
    print(
        json.dumps(
            {
                "completed_shards_reused": len(completed),
                "pending_shards": len(pending),
                "total_shards": len(tasks),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return completed, pending


def _counter(results: Sequence[TeacherShardResult], field: str) -> Counter[Any]:
    values: Counter[Any] = Counter()
    for result in results:
        mapping = getattr(result, field)
        if not isinstance(mapping, Mapping):
            raise TypeError(f"teacher shard result {field} must be a mapping")
        values.update(mapping)
    return values


def _teacher_identity(
    artifact: SubmissionTeacherArtifact,
    submission_id: int,
    root: Path,
) -> dict[str, object]:
    identity = artifact.identity()
    identity["submission_id"] = submission_id
    identity["archive_path"] = str(artifact.archive_path.relative_to(root))
    identity["route_source"] = artifact.route.source
    identity["branches"] = [
        {
            "route_id": branch.route_id,
            "first_event_day": branch.first_event_day,
            "activation_step": branch.activation_step,
            "support": branch.support,
        }
        for branch in artifact.route.branches
    ]
    identity["default_route_id"] = artifact.route.default_route_id
    identity["default_support"] = artifact.route.default_support
    return identity


def _dataset_manifest(
    *,
    settings: TeacherDataSettings,
    results: Sequence[TeacherShardResult],
    artifact: SubmissionTeacherArtifact,
    source_manifest: Mapping[str, object],
    backend: BackendApi,
    root: Path,
    source: Mapping[str, object],
    generation_id: str,
) -> dict[str, object]:
    actor = cast(Mapping[str, Any], backend.actor_encoder_spec())
    codec = cast(Mapping[str, Any], backend.action_codec_spec())
    control = cast(Mapping[str, Any], native.official_action_control_spec())
    keys = tuple(str(key) for key in codec["keys"])
    unit_tokens = int(codec["unit_tokens"])
    seed_digest = hashlib.sha256()
    for seed in range(settings.seed_start, settings.seed_start + settings.games):
        seed_digest.update(seed.to_bytes(8, "little", signed=True))
    repairs = _counter(results, "repairs")
    base: dict[str, object] = {
        "schema_version": "turn-behavior-dataset-v2",
        "source_commit": source["commit"],
        "worktree_dirty": source["worktree_dirty"],
        "source_tree_sha256": source["source_tree_sha256"],
        "generation_id": generation_id,
        "native_backend": backend.identity,
        "actor_encoder_version": str(actor["version"]),
        "action_codec_version": str(codec["version"]),
        "control_spec": str(control["version"]),
        "board_shape": [
            2,
            int(actor["board_channels"]),
            _integer(settings.environment["boardSize"], "environment boardSize"),
            _integer(settings.environment["boardSize"], "environment boardSize"),
        ],
        "unit_shape": [2, settings.unit_limit, int(actor["unit_feat"])],
        "global_features": int(actor["global_feat"]),
        "unit_limit": settings.unit_limit,
        "unit_candidate_keys": list(keys[:unit_tokens]),
        "market_candidate_keys": list(keys[unit_tokens:]),
        "teacher": _teacher_identity(artifact, settings.teacher.submission_id, root),
        "teacher_source_manifest": dict(source_manifest),
        "rollout": {
            "policy_pairing": "authenticated teacher self-play; both seats retained",
            "opponent_policy": f"kaggle-submission-{settings.teacher.submission_id}",
            "seed_start": settings.seed_start,
            "games": settings.games,
            "seed_sequence_sha256": seed_digest.hexdigest(),
            "environment": settings.environment,
        },
        "cleaning": {
            "alignment": "native observation before step -> teacher request for same step",
            "label_surface": (
                "raw market requests; physically legal unit requests; otherwise UNIT:PASS"
            ),
            "transition_semantics": (
                "illegal submitted unit requests are silent no-ops, so PASS preserves state"
            ),
            "canonical_repairs": dict(sorted(repairs.items())),
        },
        "storage": {
            "format": "npz",
            "compression": "deflate",
            "compression_level": settings.compression_level,
        },
        "policy_labels": [f"kaggle-submission-{settings.teacher.submission_id}"],
        "shards": [dict(result.shard) for result in results],
    }
    base["dataset_id"] = hashlib.sha256(orjson.dumps(base, option=orjson.OPT_SORT_KEYS)).hexdigest()
    base["generated_at"] = datetime.now(UTC).isoformat()
    SourceManifest.model_validate(base)
    return base


def _keyed_counts(counts: Mapping[int, int], keys: Sequence[str]) -> dict[str, int]:
    return {keys[token]: count for token, count in sorted(counts.items()) if count > 0}


def _outcomes(results: Sequence[TeacherShardResult]) -> dict[str, object]:
    games = sum(result.games for result in results)
    cash_sums = [sum(result.terminal_cash_sums[seat] for result in results) for seat in range(2)]
    return {
        "seat_0_wins": sum(result.seat_wins[0] for result in results),
        "seat_1_wins": sum(result.seat_wins[1] for result in results),
        "ties": sum(result.ties for result in results),
        "mean_terminal_cash": [cash_sums[0] / games, cash_sums[1] / games],
        "mean_seat_0_margin": (cash_sums[0] - cash_sums[1]) / games,
    }


def _report(
    *,
    settings: TeacherDataSettings,
    results: Sequence[TeacherShardResult],
    manifest: Mapping[str, object],
    backend: BackendApi,
    root: Path,
    wall_seconds: float,
    measured_results: Sequence[TeacherShardResult],
    resumed_shards: int,
    generation_attempt: int,
    source: Mapping[str, object],
    generation_id: str,
) -> dict[str, object]:
    games = sum(result.games for result in results)
    shards = [result.shard for result in results]
    turns = sum(_integer(shard["turns"], "shard turns") for shard in shards)
    decisions = sum(_integer(shard["decisions"], "shard decisions") for shard in shards)
    compressed_bytes = sum(_integer(shard["size_bytes"], "shard size") for shard in shards)
    measured_games = sum(result.games for result in measured_results)
    measured_turns = sum(
        _integer(result.shard["turns"], "measured shard turns") for result in measured_results
    )
    measured_decisions = sum(
        _integer(result.shard["decisions"], "measured shard decisions")
        for result in measured_results
    )
    measured_bytes = sum(
        _integer(result.shard["size_bytes"], "measured shard size") for result in measured_results
    )
    codec = cast(Mapping[str, Any], backend.action_codec_spec())
    keys = tuple(str(key) for key in codec["keys"])
    return {
        "schema_version": "submission-teacher-generation-report-v2",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": dict(source),
        "generation_id": generation_id,
        "dataset": {
            "path": str(settings.output_dir.relative_to(root)),
            "dataset_id": manifest["dataset_id"],
            "games": games,
            "sequences": sum(_integer(shard["sequences"], "shard sequences") for shard in shards),
            "turns": turns,
            "decisions": decisions,
            "compressed_bytes": compressed_bytes,
        },
        "throughput": {
            "scope": (
                "shards generated in the final invocation; authenticated resumed shards "
                "are excluded from the rate"
            ),
            "measured_games": measured_games,
            "resumed_shards": resumed_shards,
            "generation_attempt": generation_attempt,
            "wall_seconds": wall_seconds,
            "games_per_second": measured_games / wall_seconds if wall_seconds else 0.0,
            "sequences_per_second": (2 * measured_games / wall_seconds if wall_seconds else 0.0),
            "turns_per_second": measured_turns / wall_seconds if wall_seconds else 0.0,
            "decisions_per_second": (measured_decisions / wall_seconds if wall_seconds else 0.0),
            "compressed_mib_per_second": (
                measured_bytes / (1024**2) / wall_seconds if wall_seconds else 0.0
            ),
            "configured_process_workers": settings.workers,
            "effective_process_workers": min(settings.workers, len(results)),
            "policy_workers_per_process": settings.policy_workers,
            "npz_compression_level": settings.compression_level,
            "host_logical_cpus": os.cpu_count(),
            "process_affinity_logical_cpus": len(os.sched_getaffinity(0)),
            "effective_process_workers_final_invocation": min(
                settings.workers, len(measured_results)
            ),
            "aggregate_worker_rollout_seconds": sum(result.rollout_seconds for result in results),
            "aggregate_worker_write_seconds": sum(result.write_seconds for result in results),
            "aggregate_worker_combine_seconds": sum(result.combine_seconds for result in results),
            "shards": [
                {
                    "index": result.index,
                    "games": result.games,
                    "rollout_seconds": result.rollout_seconds,
                    "combine_seconds": result.combine_seconds,
                    "write_seconds": result.write_seconds,
                    "elapsed_seconds": result.elapsed_seconds,
                    "size_bytes": result.shard["size_bytes"],
                }
                for result in results
            ],
        },
        "outcomes": _outcomes(results),
        "behavior": {
            "routes": dict(sorted(_counter(results, "route_counts").items())),
            "first_event_days": dict(sorted(_counter(results, "event_day_counts").items())),
            "raw_action_counts": _keyed_counts(
                cast(Mapping[int, int], _counter(results, "raw_action_counts")), keys
            ),
            "stored_action_counts": _keyed_counts(
                cast(Mapping[int, int], _counter(results, "action_counts")), keys
            ),
            "repairs": dict(sorted(_counter(results, "repairs").items())),
        },
    }


def _write_markdown(path: Path, report: Mapping[str, object]) -> None:
    dataset = cast(Mapping[str, object], report["dataset"])
    throughput = cast(Mapping[str, object], report["throughput"])
    outcomes = cast(Mapping[str, object], report["outcomes"])
    behavior = cast(Mapping[str, object], report["behavior"])
    lines = [
        "# Submission-teacher data generation",
        "",
        f"Dataset: `{dataset['path']}` (`{dataset['dataset_id']}`).",
        "",
        "## Throughput",
        "",
        (
            f"- Games measured in final invocation: {throughput['measured_games']} in "
            f"{cast(float, throughput['wall_seconds']):.3f} s"
        ),
        f"- Authenticated shards resumed: {throughput['resumed_shards']}",
        f"- Games/s: {cast(float, throughput['games_per_second']):.3f}",
        f"- Seat-turns/s: {cast(float, throughput['turns_per_second']):.1f}",
        f"- Decisions/s: {cast(float, throughput['decisions_per_second']):.1f}",
        (f"- Compressed MiB/s: {cast(float, throughput['compressed_mib_per_second']):.2f}"),
        "",
        "## Direct outcomes and coverage",
        "",
        (
            f"Seat 0 / seat 1 / ties: {outcomes['seat_0_wins']} / "
            f"{outcomes['seat_1_wins']} / {outcomes['ties']}."
        ),
        f"Routes: `{json.dumps(behavior['routes'], sort_keys=True)}`.",
        f"First event days: `{json.dumps(behavior['first_event_days'], sort_keys=True)}`.",
        f"Canonical repairs: `{json.dumps(behavior['repairs'], sort_keys=True)}`.",
        "",
        "The manifest authenticates the exact submission archive and records the resolved engine, "
        "label normalization, source tree, shards, and seed sequence.",
    ]
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temporary.replace(path)


def _published_result(settings: TeacherDataSettings) -> dict[str, object]:
    manifest_path = settings.output_dir / "manifest.json"
    report_path = settings.report_dir / "generation-report.json"
    resolved_path = settings.report_dir / "resolved-settings.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    resolved = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, Mapping) or not isinstance(report, Mapping):
        raise TypeError("published teacher metadata must be mappings")
    expected_settings = {"teacher_data": settings.model_dump(mode="json")}
    if resolved != expected_settings:
        raise ValueError("published teacher dataset uses different resolved settings")
    SourceManifest.model_validate(manifest)
    throughput = cast(Mapping[str, object], report["throughput"])
    return {
        "dataset_dir": str(settings.output_dir),
        "dataset_id": manifest["dataset_id"],
        "manifest_sha256": sha256_file(manifest_path),
        "games": settings.games,
        "sequences": settings.games * 2,
        "wall_seconds": throughput["wall_seconds"],
        "games_per_second": throughput["games_per_second"],
        "turns_per_second": throughput["turns_per_second"],
        "decisions_per_second": throughput["decisions_per_second"],
        "report_dir": str(settings.report_dir),
    }


def prepare_teacher_dataset(
    settings: TeacherDataSettings, repository_root: Path
) -> dict[str, object]:
    """Generate, resume, and atomically publish one authenticated teacher dataset."""
    root = repository_root.resolve()
    settings = resolve_paths(settings, root)
    data_root = (root / "data" / "external").resolve()
    output_root = (root / "outputs").resolve()
    _require_within(settings.teacher.archive_path, data_root, "submission archive")
    _require_within(settings.output_dir, data_root, "teacher dataset")
    _require_within(settings.report_dir, output_root, "generation report")

    backend = load_backend(root)
    artifact = load_submission_teacher(
        settings.teacher.archive_path,
        settings.teacher.archive_sha256,
        settings.teacher.source_commit,
        settings.teacher.route_sha256,
    )
    source_manifest = _source_manifest(settings, root)
    probe = backend.engine(seed=settings.seed_start, configuration=dict(settings.environment))
    resolved_environment = cast(dict[str, object], probe.configuration)
    settings = settings.model_copy(update={"environment": resolved_environment})

    settings.output_dir.parent.mkdir(parents=True, exist_ok=True)
    settings.report_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dataset = _incomplete_path(settings.output_dir)
    staging_report = _incomplete_path(settings.report_dir)
    _require_within(staging_dataset, data_root, "incomplete teacher dataset")
    _require_within(staging_report, output_root, "incomplete generation report")

    if settings.output_dir.exists():
        if not settings.report_dir.exists():
            required = (
                staging_report / "generation-report.json",
                staging_report / "resolved-settings.json",
                staging_report / "README.md",
            )
            if not staging_report.is_dir() or not all(path.is_file() for path in required):
                raise RuntimeError("teacher dataset was published without a complete report")
            staging_report.replace(settings.report_dir)
        return _published_result(settings)
    if settings.report_dir.exists():
        raise RuntimeError("teacher report exists without its published dataset")

    if staging_dataset.exists() and not staging_dataset.is_dir():
        raise NotADirectoryError(staging_dataset)
    staging_dataset.mkdir(exist_ok=True)
    state_path = staging_dataset / ".generation-state.json"
    if not state_path.exists() and any(staging_dataset.iterdir()):
        raise RuntimeError("incomplete teacher dataset lacks its generation state")
    source = source_identity(root)
    state = _load_or_create_generation_state(state_path, settings, source)
    generation_id = str(state["generation_id"])
    generation_attempt = _integer(state["attempts"], "generation attempts")

    if staging_report.exists() and not staging_report.is_dir():
        raise NotADirectoryError(staging_report)
    staging_report.mkdir(exist_ok=True)
    tasks = _tasks(settings, staging_dataset)
    resumed_results, pending_tasks = _resume_results(tasks)
    generation_started = time.perf_counter()
    generated_results = _run_tasks(
        pending_tasks,
        settings.workers,
        completed_offset=len(resumed_results),
        total_tasks=len(tasks),
    )
    wall_seconds = time.perf_counter() - generation_started
    results = sorted([*resumed_results, *generated_results], key=lambda result: result.index)
    if len(results) != len(tasks):
        raise RuntimeError("teacher generation did not produce every configured shard")

    spec = cast(Mapping[str, object], state["spec"])
    launch_source = cast(Mapping[str, object], spec["source"])
    manifest = _dataset_manifest(
        settings=settings,
        results=results,
        artifact=artifact,
        source_manifest=source_manifest,
        backend=backend,
        root=root,
        source=launch_source,
        generation_id=generation_id,
    )
    _write_json(staging_dataset / "manifest.json", manifest, overwrite=True)
    report = _report(
        settings=settings,
        results=results,
        manifest=manifest,
        backend=backend,
        root=root,
        wall_seconds=wall_seconds,
        measured_results=generated_results,
        resumed_shards=len(resumed_results),
        generation_attempt=generation_attempt,
        source=launch_source,
        generation_id=generation_id,
    )
    _write_json(staging_report / "generation-report.json", report, overwrite=True)
    _write_json(
        staging_report / "resolved-settings.json",
        {"teacher_data": settings.model_dump(mode="json")},
        overwrite=True,
    )
    _write_markdown(staging_report / "README.md", report)
    state["completed_at"] = datetime.now(UTC).isoformat()
    state["completed_shards"] = len(results)
    _write_json(state_path, state, overwrite=True)

    staging_dataset.replace(settings.output_dir)
    staging_report.replace(settings.report_dir)
    return _published_result(settings)


__all__ = ["prepare_teacher_dataset", "resolve_paths"]
