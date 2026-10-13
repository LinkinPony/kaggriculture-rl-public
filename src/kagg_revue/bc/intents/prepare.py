"""Prepare immutable causal Rank8 canonical-intent behavior shards."""

from __future__ import annotations

import hashlib
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import orjson

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.intents.config import IntentTeacherDataSettings
from kagg_revue.bc.intents.dataset import IntentTeacherManifest
from kagg_revue.bc.intents.rollout import (
    IntentTeacherShardResult,
    IntentTeacherShardTask,
    generate_intent_teacher_shard,
)
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.teacher.submission import load_submission_teacher


def _resolve(settings: IntentTeacherDataSettings, root: Path) -> IntentTeacherDataSettings:
    teacher = settings.teacher.model_copy(
        update={"archive_path": (root / settings.teacher.archive_path).resolve()}
    )
    return settings.model_copy(
        update={
            "teacher": teacher,
            "output_dir": (root / settings.output_dir).resolve(),
            "report_dir": (root / settings.report_dir).resolve(),
        }
    )


def _require_within(path: Path, parent: Path, name: str) -> None:
    if not path.is_relative_to(parent):
        raise ValueError(f"{name} escaped {parent}")


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(orjson.dumps(value, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))
    temporary.replace(path)


def _tasks(
    settings: IntentTeacherDataSettings,
    root: Path,
    output_dir: Path,
    route_codes: Mapping[str, int],
) -> list[IntentTeacherShardTask]:
    tasks: list[IntentTeacherShardTask] = []
    for index, offset in enumerate(range(0, settings.games, settings.games_per_shard)):
        count = min(settings.games_per_shard, settings.games - offset)
        seeds = tuple(range(settings.seed_start + offset, settings.seed_start + offset + count))
        tasks.append(
            IntentTeacherShardTask(
                index=index,
                seeds=seeds,
                output_path=output_dir / f"intent-{index:05d}.npz",
                repository_root=root,
                artifact=settings.teacher,
                environment=settings.environment,
                route_codes=route_codes,
                unit_limit=settings.unit_limit,
                max_transaction_steps=settings.max_transaction_steps,
                native_workers=settings.native_workers,
                compression_level=settings.compression_level,
            )
        )
    return tasks


def _run_tasks(
    tasks: Sequence[IntentTeacherShardTask], workers: int
) -> list[IntentTeacherShardResult]:
    if workers == 1:
        return [generate_intent_teacher_shard(task) for task in tasks]
    results: list[IntentTeacherShardResult] = []
    with ProcessPoolExecutor(max_workers=min(workers, len(tasks))) as executor:
        futures = {executor.submit(generate_intent_teacher_shard, task): task for task in tasks}
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results, key=lambda result: result.shard.index)


def _counter(results: Sequence[IntentTeacherShardResult], name: str) -> dict[str, int]:
    total: Counter[str] = Counter()
    for result in results:
        value = getattr(result, name)
        if not isinstance(value, Mapping):
            raise TypeError(f"intent teacher diagnostic {name} must be a mapping")
        total.update({str(key): int(count) for key, count in value.items()})
    return dict(sorted(total.items()))


def _manifest(
    *,
    settings: IntentTeacherDataSettings,
    repository_root: Path,
    source: Mapping[str, object],
    backend: Any,
    artifact: Any,
    route_codes: Mapping[str, int],
    results: Sequence[IntentTeacherShardResult],
) -> dict[str, object]:
    intent_spec = cast(Mapping[str, object], backend.intent_ledger_spec())
    actor_spec = cast(Mapping[str, object], backend.actor_encoder_spec())
    codec_spec = cast(Mapping[str, object], backend.action_codec_spec())
    intent_spec_sha256 = hashlib.sha256(
        orjson.dumps(intent_spec, option=orjson.OPT_SORT_KEYS)
    ).hexdigest()
    seed_digest = hashlib.sha256()
    for seed in range(settings.seed_start, settings.seed_start + settings.games):
        seed_digest.update(seed.to_bytes(8, "little", signed=False))
    teacher_identity = artifact.identity()
    teacher_identity["archive_path"] = str(
        settings.teacher.archive_path.relative_to(repository_root)
    )
    base: dict[str, object] = {
        "schema_version": "canonical-intent-teacher-dataset-v1",
        "source": dict(source),
        "native_backend": dict(backend.identity),
        "teacher": {
            **teacher_identity,
            "submission_id": settings.teacher.submission_id,
            "submission_record_commit": settings.submission_record_commit,
            "event_shop": artifact.route.event_shop,
            "default_route_id": artifact.route.default_route_id,
            "default_support": artifact.route.default_support,
            "branches": [
                {
                    "route_id": branch.route_id,
                    "first_event_day": branch.first_event_day,
                    "activation_step": branch.activation_step,
                    "support": branch.support,
                }
                for branch in artifact.route.branches
            ],
            "route_source": artifact.route.source,
            "causality": (
                "current observation history plus authenticated embedded route/program state"
            ),
        },
        "intent_abi_version": str(intent_spec["abi_version"]),
        "intent_spec_sha256": intent_spec_sha256,
        "actor_encoder_version": str(actor_spec["version"]),
        "action_codec_version": str(codec_spec["version"]),
        "unit_limit": settings.unit_limit,
        "max_transaction_steps": settings.max_transaction_steps,
        "environment": dict(settings.environment),
        "collection": {
            "policy_pairing": "causal authenticated teacher self-play; both seats retained",
            "seed_start": settings.seed_start,
            "games": settings.games,
            "seed_sequence_sha256": seed_digest.hexdigest(),
            "label_surface": "dynamic native canonical candidates and selected canonical ID",
            "official_history": "actions compiled by the same deterministic intent compiler",
            "hindsight_oracle_used": False,
        },
        "route_codes": dict(route_codes),
        "shards": [result.shard.model_dump(mode="json") for result in results],
    }
    base["dataset_id"] = hashlib.sha256(orjson.dumps(base, option=orjson.OPT_SORT_KEYS)).hexdigest()
    base["generated_at"] = datetime.now(UTC).isoformat()
    IntentTeacherManifest.model_validate(base)
    return base


def _report(
    settings: IntentTeacherDataSettings,
    manifest: Mapping[str, object],
    results: Sequence[IntentTeacherShardResult],
    wall_seconds: float,
) -> dict[str, object]:
    shards = [result.shard for result in results]
    episodes = sum(shard.episodes for shard in shards)
    decisions = sum(shard.decisions for shard in shards)
    terminal_cash = sum(shard.terminal_cash_sum for shard in shards)
    return {
        "schema_version": "canonical-intent-teacher-generation-report-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_id": manifest["dataset_id"],
        "games": settings.games,
        "episodes": episodes,
        "decisions": decisions,
        "terminal": {
            "better": sum(shard.better for shard in shards),
            "ties": sum(shard.ties for shard in shards),
            "worse": sum(shard.worse for shard in shards),
            "mean_cash": terminal_cash / episodes,
        },
        "compiler": {
            "maximum_transaction_steps": max(shard.maximum_transaction_steps for shard in shards),
            "configured_transaction_capacity": settings.max_transaction_steps,
            "clipped_market_quantities": sum(shard.clipped_market_quantities for shard in shards),
            "omitted_unavailable_sell_orders": sum(shard.omitted_sell_orders for shard in shards),
            "replaced_unavailable_sell_slots": sum(
                shard.replaced_unavailable_sell_slots for shard in shards
            ),
        },
        "coverage": {
            "routes": _counter(results, "route_counts"),
            "first_event_days": _counter(results, "event_day_counts"),
            "operations": _counter(results, "operation_counts"),
        },
        "throughput": {
            "wall_seconds": wall_seconds,
            "games_per_second": settings.games / wall_seconds,
            "decisions_per_second": decisions / wall_seconds,
            "compressed_bytes": sum(shard.size_bytes for shard in shards),
            "process_workers": min(settings.process_workers, len(results)),
            "native_workers_per_process": settings.native_workers,
            "shards": [
                {
                    "index": result.shard.index,
                    "elapsed_seconds": result.elapsed_seconds,
                    "rollout_seconds": result.rollout_seconds,
                    "export_seconds": result.export_seconds,
                    "write_seconds": result.write_seconds,
                }
                for result in results
            ],
        },
    }


def prepare_intent_teacher_dataset(
    settings: IntentTeacherDataSettings,
    repository_root: Path,
    *,
    smoke: bool = False,
) -> dict[str, object]:
    """Generate and atomically publish canonical-intent teacher shards."""
    root = repository_root.resolve()
    settings = _resolve(settings, root)
    if smoke:
        output_dir = settings.output_dir
        report_dir = settings.report_dir
        if "smoke" not in output_dir.name:
            output_dir = output_dir.with_name(f"{output_dir.name}-smoke")
        if "smoke" not in report_dir.name:
            report_dir = report_dir.with_name(f"{report_dir.name}-smoke")
        settings = settings.model_copy(
            update={
                "output_dir": output_dir,
                "report_dir": report_dir,
                "games": 1,
                "games_per_shard": 1,
                "process_workers": 1,
            }
        )
    data_root = (root / "data" / "external").resolve()
    output_root = (root / "outputs").resolve()
    _require_within(settings.teacher.archive_path, data_root, "submission teacher archive")
    _require_within(settings.output_dir, data_root, "intent teacher dataset")
    _require_within(settings.report_dir, output_root, "intent teacher report")
    if settings.output_dir.exists() or settings.report_dir.exists():
        raise FileExistsError("intent teacher output or report already exists")

    source = source_identity(root)
    if source["worktree_dirty"] and not smoke:
        raise RuntimeError("intent teacher production data requires a clean source revision")
    backend = load_backend(root)
    artifact = load_submission_teacher(
        settings.teacher.archive_path,
        settings.teacher.archive_sha256,
        settings.teacher.source_commit,
        settings.teacher.route_sha256,
    )
    probe = backend.engine(settings.seed_start, dict(settings.environment))
    settings = settings.model_copy(update={"environment": dict(probe.configuration)})
    route_ids = [artifact.route.default_route_id]
    route_ids.extend(branch.route_id for branch in artifact.route.branches)
    route_codes = {route_id: index for index, route_id in enumerate(route_ids)}
    if len(route_codes) > 256:
        raise ValueError("intent teacher route vocabulary exceeds uint8 storage")

    staging_data = settings.output_dir.with_name(settings.output_dir.name + ".incomplete")
    staging_report = settings.report_dir.with_name(settings.report_dir.name + ".incomplete")
    if staging_data.exists() or staging_report.exists():
        raise FileExistsError("incomplete intent teacher generation already exists")
    staging_data.mkdir(parents=True)
    staging_report.mkdir(parents=True)
    resolved = settings.model_dump(mode="json")
    resolved["teacher"]["archive_path"] = str(settings.teacher.archive_path.relative_to(root))
    resolved["output_dir"] = str(settings.output_dir.relative_to(root))
    resolved["report_dir"] = str(settings.report_dir.relative_to(root))
    _write_json(staging_report / "resolved-settings.json", {"intent_teacher_data": resolved})

    started = time.perf_counter()
    results = _run_tasks(
        _tasks(settings, root, staging_data, route_codes),
        settings.process_workers,
    )
    wall_seconds = time.perf_counter() - started
    manifest = _manifest(
        settings=settings,
        repository_root=root,
        source=source,
        backend=backend,
        artifact=artifact,
        route_codes=route_codes,
        results=results,
    )
    _write_json(staging_data / "manifest.json", manifest)
    report = _report(settings, manifest, results, wall_seconds)
    _write_json(staging_report / "generation-report.json", report)
    staging_data.replace(settings.output_dir)
    staging_report.replace(settings.report_dir)
    manifest_path = settings.output_dir / "manifest.json"
    return {
        "dataset_dir": str(settings.output_dir),
        "dataset_id": manifest["dataset_id"],
        "manifest_sha256": sha256_file(manifest_path),
        "games": settings.games,
        "episodes": 2 * settings.games,
        "decisions": report["decisions"],
        "mean_terminal_cash": cast(Mapping[str, object], report["terminal"])["mean_cash"],
        "wall_seconds": wall_seconds,
        "report_dir": str(settings.report_dir),
    }


__all__ = ["prepare_intent_teacher_dataset"]
