"""Prepare immutable Rank8 atomic-effect behavior shards."""

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
from kagg_revue.bc.effects.config import EffectTeacherDataSettings
from kagg_revue.bc.effects.dataset import EffectTeacherManifest
from kagg_revue.bc.effects.rollout import (
    EffectTeacherShardResult,
    EffectTeacherShardTask,
    generate_effect_teacher_shard,
)
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.teacher.submission import load_submission_teacher


def _resolve(
    settings: EffectTeacherDataSettings,
    root: Path,
) -> EffectTeacherDataSettings:
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
    temporary.write_bytes(
        orjson.dumps(value, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)
    )
    temporary.replace(path)


def _tasks(
    settings: EffectTeacherDataSettings,
    root: Path,
    output_dir: Path,
    route_codes: Mapping[str, int],
) -> list[EffectTeacherShardTask]:
    tasks: list[EffectTeacherShardTask] = []
    for index, offset in enumerate(
        range(0, settings.games, settings.games_per_shard)
    ):
        count = min(settings.games_per_shard, settings.games - offset)
        seeds = tuple(
            range(
                settings.seed_start + offset,
                settings.seed_start + offset + count,
            )
        )
        tasks.append(
            EffectTeacherShardTask(
                index=index,
                seeds=seeds,
                output_path=output_dir / f"effect-{index:05d}.npz",
                repository_root=root,
                artifact=settings.teacher,
                environment=settings.environment,
                route_codes=route_codes,
                unit_limit=settings.unit_limit,
                maximum_quantity=settings.maximum_quantity,
                native_workers=settings.native_workers,
                compression_level=settings.compression_level,
            )
        )
    return tasks


def _run_tasks(
    tasks: Sequence[EffectTeacherShardTask],
    workers: int,
) -> list[EffectTeacherShardResult]:
    if workers == 1:
        return [generate_effect_teacher_shard(task) for task in tasks]
    results: list[EffectTeacherShardResult] = []
    with ProcessPoolExecutor(max_workers=min(workers, len(tasks))) as executor:
        futures = {
            executor.submit(generate_effect_teacher_shard, task): task
            for task in tasks
        }
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results, key=lambda result: result.shard.index)


def _counter(
    results: Sequence[EffectTeacherShardResult],
    name: str,
) -> dict[str, int]:
    total: Counter[str] = Counter()
    for result in results:
        value = getattr(result, name)
        if not isinstance(value, Mapping):
            raise TypeError(f"effect teacher diagnostic {name} must be a mapping")
        total.update({str(key): int(count) for key, count in value.items()})
    return dict(sorted(total.items()))


def _manifest(
    *,
    settings: EffectTeacherDataSettings,
    repository_root: Path,
    source: Mapping[str, object],
    backend: Any,
    artifact: Any,
    route_codes: Mapping[str, int],
    results: Sequence[EffectTeacherShardResult],
) -> dict[str, object]:
    effect_spec = cast(Mapping[str, object], backend.effect_policy_spec())
    actor_spec = cast(Mapping[str, object], backend.actor_encoder_spec())
    codec_spec = cast(Mapping[str, object], backend.action_codec_spec())
    effect_spec_sha256 = hashlib.sha256(
        orjson.dumps(effect_spec, option=orjson.OPT_SORT_KEYS)
    ).hexdigest()
    seed_digest = hashlib.sha256()
    for seed in range(settings.seed_start, settings.seed_start + settings.games):
        seed_digest.update(seed.to_bytes(8, "little", signed=False))
    teacher_identity = artifact.identity()
    teacher_identity["archive_path"] = str(
        settings.teacher.archive_path.relative_to(repository_root)
    )
    base: dict[str, object] = {
        "schema_version": "atomic-effect-teacher-dataset-v1",
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
                "current actor observation plus authenticated embedded route state"
            ),
        },
        "effect_abi_version": str(effect_spec["abi_version"]),
        "effect_spec_sha256": effect_spec_sha256,
        "actor_encoder_version": str(actor_spec["version"]),
        "action_codec_version": str(codec_spec["version"]),
        "unit_limit": settings.unit_limit,
        "maximum_quantity": settings.maximum_quantity,
        "environment": dict(settings.environment),
        "collection": {
            "policy_pairing": "causal authenticated teacher self-play; both seats retained",
            "seed_start": settings.seed_start,
            "games": settings.games,
            "seed_sequence_sha256": seed_digest.hexdigest(),
            "label_surface": "dynamic native atomic-effect candidates",
            "official_history": "actions compiled by the same deterministic effect compiler",
            "hindsight_oracle_used": False,
            "translation": (
                "exact bound unit effects, exact store transfers, and explicit rejected "
                "market slots"
            ),
        },
        "route_codes": dict(route_codes),
        "shards": [result.shard.model_dump(mode="json") for result in results],
    }
    base["dataset_id"] = hashlib.sha256(
        orjson.dumps(base, option=orjson.OPT_SORT_KEYS)
    ).hexdigest()
    base["generated_at"] = datetime.now(UTC).isoformat()
    EffectTeacherManifest.model_validate(base)
    return base


def _report(
    settings: EffectTeacherDataSettings,
    manifest: Mapping[str, object],
    results: Sequence[EffectTeacherShardResult],
    wall_seconds: float,
) -> dict[str, object]:
    shards = [result.shard for result in results]
    episodes = sum(shard.episodes for shard in shards)
    factors = sum(shard.factors for shard in shards)
    terminal_cash = sum(shard.terminal_cash_sum for shard in shards)
    return {
        "schema_version": "atomic-effect-teacher-generation-report-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset_id": manifest["dataset_id"],
        "games": settings.games,
        "episodes": episodes,
        "factors": factors,
        "policy_factors": sum(shard.policy_factors for shard in shards),
        "terminal": {
            "better": sum(shard.better for shard in shards),
            "ties": sum(shard.ties for shard in shards),
            "worse": sum(shard.worse for shard in shards),
            "mean_cash": terminal_cash / episodes,
        },
        "compiler": {
            "maximum_transaction_steps": max(
                shard.maximum_transaction_steps for shard in shards
            ),
            "maximum_candidate_width": max(
                width for shard in shards for width in shard.bucket_widths
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
            "factors_per_second": factors / wall_seconds,
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


def prepare_effect_teacher_dataset(
    settings: EffectTeacherDataSettings,
    repository_root: Path,
    *,
    smoke: bool = False,
) -> dict[str, object]:
    """Generate and atomically publish atomic-effect teacher shards."""
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
    _require_within(
        settings.teacher.archive_path,
        data_root,
        "submission teacher archive",
    )
    _require_within(settings.output_dir, data_root, "effect teacher dataset")
    _require_within(settings.report_dir, output_root, "effect teacher report")
    if settings.output_dir.exists() or settings.report_dir.exists():
        raise FileExistsError("effect teacher output or report already exists")

    source = source_identity(root)
    if source["worktree_dirty"] and not smoke:
        raise RuntimeError("effect teacher production data requires a clean source revision")
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
        raise ValueError("effect teacher route vocabulary exceeds uint8 storage")

    staging_data = settings.output_dir.with_name(settings.output_dir.name + ".incomplete")
    staging_report = settings.report_dir.with_name(settings.report_dir.name + ".incomplete")
    if staging_data.exists() or staging_report.exists():
        raise FileExistsError("incomplete effect teacher generation already exists")
    staging_data.mkdir(parents=True)
    staging_report.mkdir(parents=True)
    resolved = settings.model_dump(mode="json")
    resolved["teacher"]["archive_path"] = str(
        settings.teacher.archive_path.relative_to(root)
    )
    resolved["output_dir"] = str(settings.output_dir.relative_to(root))
    resolved["report_dir"] = str(settings.report_dir.relative_to(root))
    _write_json(staging_report / "resolved-settings.json", {"effect_teacher_data": resolved})

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
        "factors": report["factors"],
        "mean_terminal_cash": cast(Mapping[str, object], report["terminal"])[
            "mean_cash"
        ],
        "wall_seconds": wall_seconds,
        "report_dir": str(settings.report_dir),
    }


__all__ = ["prepare_effect_teacher_dataset"]
