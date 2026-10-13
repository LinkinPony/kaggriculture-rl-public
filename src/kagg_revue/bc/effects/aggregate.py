"""Immutable aggregation of Rank8 demonstrations and effect corrections."""

from __future__ import annotations

import hashlib
import os
import shutil
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import orjson

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.effects.config import (
    EffectAggregateComponentSettings,
    EffectAggregateDataSettings,
)
from kagg_revue.bc.effects.dataset import (
    EffectTeacherManifest,
    EffectTeacherShard,
    load_effect_teacher_manifest,
)
from kagg_revue.core.provenance import source_identity


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(
        orjson.dumps(value, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)
    )
    temporary.replace(path)


def _link_or_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def _require_compatible(
    reference: EffectTeacherManifest,
    candidate: EffectTeacherManifest,
    name: str,
) -> None:
    fields = (
        "effect_abi_version",
        "effect_spec_sha256",
        "actor_encoder_version",
        "action_codec_version",
        "unit_limit",
        "maximum_quantity",
        "environment",
        "route_codes",
    )
    for field in fields:
        if getattr(reference, field) != getattr(candidate, field):
            raise ValueError(f"effect aggregate component {name} has incompatible {field}")
    for field in ("archive_sha256", "source_commit", "route_sha256"):
        if reference.teacher.get(field) != candidate.teacher.get(field):
            raise ValueError(
                f"effect aggregate component {name} has incompatible teacher {field}"
            )


def _component_partitions(
    manifest: EffectTeacherManifest,
    settings: EffectAggregateComponentSettings,
) -> dict[str, tuple[EffectTeacherShard, ...]]:
    if manifest.partitions is not None:
        by_id = {
            shard.shard_id: shard
            for shard in manifest.shards
            if shard.shard_id is not None
        }
        return {
            name: tuple(by_id[shard_id] for shard_id in manifest.partitions[name])
            for name in ("train", "validation", "test")
        }
    training = len(manifest.shards) - settings.validation_games - settings.test_games
    if training < 1:
        raise ValueError("effect aggregate component split has no training games")
    validation_end = training + settings.validation_games
    return {
        "train": manifest.shards[:training],
        "validation": manifest.shards[training:validation_end],
        "test": manifest.shards[validation_end:],
    }


def prepare_effect_aggregate(
    raw_settings: EffectAggregateDataSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Link authenticated shards and preserve held-out groups per component."""
    root = repository_root.resolve()
    output_dir = (root / raw_settings.output_dir).resolve()
    report_dir = (root / raw_settings.report_dir).resolve()
    if not output_dir.is_relative_to((root / "data" / "external").resolve()):
        raise ValueError("effect aggregate dataset escaped data/external/")
    if not report_dir.is_relative_to((root / "outputs").resolve()):
        raise ValueError("effect aggregate report escaped outputs/")
    if output_dir.exists() or report_dir.exists():
        raise FileExistsError("effect aggregate output or report already exists")
    source = source_identity(root)
    if bool(source["worktree_dirty"]):
        raise RuntimeError("effect aggregate preparation requires a clean source tree")

    paths = {
        name: (root / component.manifest).resolve()
        for name, component in sorted(raw_settings.components.items())
    }
    if any(
        not path.is_relative_to((root / "data" / "external").resolve())
        or not path.is_file()
        for path in paths.values()
    ):
        raise FileNotFoundError("effect aggregate component manifest is absent")
    components = {
        name: load_effect_teacher_manifest(path.parent)
        for name, path in paths.items()
    }
    reference = next(iter(components.values()))
    for name, manifest in components.items():
        _require_compatible(reference, manifest, name)
    component_identities = {
        name: {
            "path": str(paths[name].relative_to(root)),
            "sha256": sha256_file(paths[name]),
            "dataset_id": manifest.dataset_id,
        }
        for name, manifest in components.items()
    }

    staging_data = output_dir.with_name(output_dir.name + ".incomplete")
    staging_report = report_dir.with_name(report_dir.name + ".incomplete")
    if staging_data.exists() or staging_report.exists():
        raise FileExistsError("incomplete effect aggregate already exists")
    staging_data.mkdir(parents=True)
    staging_report.mkdir(parents=True)
    records: list[EffectTeacherShard] = []
    partition_ids: dict[str, list[str]] = {
        "train": [],
        "validation": [],
        "test": [],
    }
    component_counts: dict[str, dict[str, int]] = {}
    try:
        for name, manifest in components.items():
            partitions = _component_partitions(
                manifest,
                raw_settings.components[name],
            )
            assignment = {
                id(shard): partition
                for partition, shards in partitions.items()
                for shard in shards
            }
            component_counts[name] = {
                partition: len(shards) for partition, shards in partitions.items()
            }
            for shard in manifest.shards:
                source_path = (paths[name].parent / shard.path).resolve()
                if (
                    not source_path.is_relative_to(paths[name].parent)
                    or not source_path.is_file()
                    or source_path.stat().st_size != shard.size_bytes
                    or sha256_file(source_path) != shard.sha256
                ):
                    raise ValueError(
                        f"effect aggregate component shard changed: {source_path}"
                    )
                partition = assignment.get(id(shard))
                if partition is None:
                    raise ValueError("effect aggregate split omitted a component shard")
                shard_id = f"{name}:{shard.shard_id or shard.index}"
                relative = Path("shards") / name / Path(shard.path).name
                _link_or_copy(source_path, staging_data / relative)
                record = EffectTeacherShard.model_validate(
                    {
                        **shard.model_dump(
                            mode="json",
                            exclude={"shard_id", "partition", "source_group"},
                        ),
                        "index": len(records),
                        "shard_id": shard_id,
                        "path": str(relative),
                        "partition": partition,
                        "source_group": name,
                    }
                )
                records.append(record)
                partition_ids[partition].append(shard_id)
        stable = {
            "components": component_identities,
            "partitions": partition_ids,
            "shards": [
                {"shard_id": shard.shard_id, "sha256": shard.sha256}
                for shard in records
            ],
            "sampling": "each authenticated paired-seat shard exactly once per epoch",
        }
        dataset_id = hashlib.sha256(
            orjson.dumps(stable, option=orjson.OPT_SORT_KEYS)
        ).hexdigest()
        aggregate_manifest: dict[str, object] = {
            "schema_version": "atomic-effect-teacher-dataset-v2",
            "dataset_id": dataset_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "source": {
                **dict(source),
                "kind": "authenticated_effect_dataset_aggregate",
                "components": component_identities,
            },
            "native_backend": reference.native_backend,
            "teacher": {
                "kind": "rank8_demonstration_and_student_state_aggregate",
                "archive_sha256": reference.teacher["archive_sha256"],
                "source_commit": reference.teacher["source_commit"],
                "route_sha256": reference.teacher["route_sha256"],
                "components": {
                    name: component.teacher for name, component in components.items()
                },
            },
            "effect_abi_version": reference.effect_abi_version,
            "effect_spec_sha256": reference.effect_spec_sha256,
            "actor_encoder_version": reference.actor_encoder_version,
            "action_codec_version": reference.action_codec_version,
            "unit_limit": reference.unit_limit,
            "maximum_quantity": reference.maximum_quantity,
            "environment": reference.environment,
            "collection": {
                "kind": "immutable_union",
                "sampling": "every shard once per epoch",
                "component_partitions": component_counts,
                "paired_seed_groups": sum(shard.games for shard in records),
                "physical_games": sum(
                    shard.physical_games or shard.games for shard in records
                ),
            },
            "route_codes": reference.route_codes,
            "partitions": partition_ids,
            "shards": [shard.model_dump(mode="json") for shard in records],
        }
        EffectTeacherManifest.model_validate(aggregate_manifest)
        _write_json(staging_data / "manifest.json", aggregate_manifest)
        totals = Counter(shard.partition for shard in records)
        report: dict[str, object] = {
            "schema_version": "atomic-effect-aggregate-report-v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "complete",
            "source": dict(source),
            "dataset": {
                "path": str(raw_settings.output_dir / "manifest.json"),
                "dataset_id": dataset_id,
                "manifest_sha256": sha256_file(staging_data / "manifest.json"),
                "paired_seed_groups": sum(shard.games for shard in records),
                "physical_games": sum(
                    shard.physical_games or shard.games for shard in records
                ),
                "factors": sum(shard.factors for shard in records),
                "compressed_bytes": sum(shard.size_bytes for shard in records),
            },
            "components": component_identities,
            "partitions": {
                name: totals[name] for name in ("train", "validation", "test")
            },
        }
        _write_json(staging_report / "aggregate-report.json", report)
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        report_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_data.replace(output_dir)
        staging_report.replace(report_dir)
        return cast(dict[str, object], report["dataset"])
    except BaseException:
        shutil.rmtree(staging_data, ignore_errors=True)
        shutil.rmtree(staging_report, ignore_errors=True)
        raise


__all__ = ["prepare_effect_aggregate"]
