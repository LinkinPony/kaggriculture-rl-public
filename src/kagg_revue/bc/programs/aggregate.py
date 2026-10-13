"""Immutable aggregation of teacher and student-state program datasets."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import orjson

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.programs.config import ProgramBcSettings
from kagg_revue.bc.programs.dataset import ProgramBcDataset, ProgramBcManifest
from kagg_revue.bc.programs.prepare import resolve_program_bc_settings
from kagg_revue.core.provenance import source_identity


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def _require_compatible(
    reference: ProgramBcManifest,
    candidate: ProgramBcManifest,
    name: str,
) -> None:
    """Reject unions that would silently change the model or compiler contract."""
    fields = (
        "native_program_abi",
        "actor_architecture",
        "program_architecture",
        "action_keys",
        "environment",
    )
    for field in fields:
        if getattr(reference, field) != getattr(candidate, field):
            raise ValueError(f"program aggregate component {name} has incompatible {field}")
    identity_fields = (
        "sha256",
        "actor_encoder_version",
        "derived_fact_version",
        "action_keys",
    )
    for field in identity_fields:
        if reference.source_actor_identity.get(field) != candidate.source_actor_identity.get(
            field
        ):
            raise ValueError(
                f"program aggregate component {name} has incompatible source actor {field}"
            )


def _link_or_copy(source: Path, destination: Path) -> None:
    """Reuse immutable shard bytes without requiring hard-link support."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def prepare_program_aggregate(
    raw_settings: ProgramBcSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Union authenticated shards while preserving component validation groups."""
    root = repository_root.resolve()
    settings = resolve_program_bc_settings(raw_settings, root)
    aggregate = settings.aggregate_source
    if aggregate is None:
        raise ValueError("program aggregate preparation requires an aggregate source")
    source = source_identity(root)
    if bool(source["worktree_dirty"]):
        raise RuntimeError("program aggregate preparation requires a clean source tree")
    if settings.dataset_dir.exists():
        raise FileExistsError(f"program aggregate dataset exists: {settings.dataset_dir}")
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    report_path = settings.output_dir / "data-preparation-report.json"
    if report_path.exists():
        raise FileExistsError(f"program aggregate report exists: {report_path}")

    components = {
        name: ProgramBcDataset(path)
        for name, path in sorted(aggregate.components.items())
    }
    reference = next(iter(components.values())).manifest
    for name, dataset in components.items():
        _require_compatible(reference, dataset.manifest, name)

    component_identities = {
        name: {
            "path": str(aggregate.components[name]),
            "sha256": dataset.manifest_sha256,
            "dataset_id": dataset.manifest.dataset_id,
        }
        for name, dataset in components.items()
    }
    stable = {
        "components": component_identities,
        "sampling": "each authenticated episode shard exactly once per epoch",
    }
    dataset_id = hashlib.sha256(
        orjson.dumps(stable, option=orjson.OPT_SORT_KEYS)
    ).hexdigest()

    (root / "tmp").mkdir(parents=True, exist_ok=True)
    build_path = Path(tempfile.mkdtemp(prefix="program-aggregate-", dir=root / "tmp"))
    records: list[dict[str, object]] = []
    try:
        for name, dataset in components.items():
            for shard in dataset.manifest.shards:
                shard_source = (dataset.root / shard.path).resolve()
                if not shard_source.is_relative_to(dataset.root) or not shard_source.is_file():
                    raise FileNotFoundError(
                        f"program aggregate component shard is absent: {shard_source}"
                    )
                if (
                    shard_source.stat().st_size != shard.size_bytes
                    or sha256_file(shard_source) != shard.sha256
                ):
                    raise ValueError(
                        f"program aggregate component shard identity changed: {shard_source}"
                    )
                relative = Path("shards") / name / Path(shard.path).name
                _link_or_copy(shard_source, build_path / relative)
                record = cast(dict[str, object], shard.model_dump(mode="json"))
                record.update(
                    {
                        "shard_id": f"{name}:{shard.shard_id}",
                        "path": str(relative),
                        "source_group": name,
                    }
                )
                records.append(record)
        records.sort(key=lambda row: str(row["shard_id"]))
        partitions = {
            partition: tuple(
                str(record["shard_id"])
                for record in records
                if record["partition"] == partition
            )
            for partition in ("train", "validation", "test")
        }
        selection = {
            "schema_version": "conditional-program-aggregate-v1",
            "sampling": "each authenticated episode shard exactly once per epoch",
            "components": {
                name: {
                    "train": len(dataset.manifest.partitions["train"]),
                    "validation": len(dataset.manifest.partitions["validation"]),
                    "test": len(dataset.manifest.partitions["test"]),
                }
                for name, dataset in components.items()
            },
        }
        manifest: dict[str, object] = {
            "schema_version": "conditional-program-bc-dataset-v1",
            "dataset_id": dataset_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "source": {
                "kind": "authenticated_dataset_aggregate",
                "source_revision": source,
                "components": component_identities,
            },
            "source_actor_identity": reference.source_actor_identity,
            "native_backend": reference.native_backend,
            "native_program_abi": reference.native_program_abi,
            "actor_architecture": reference.actor_architecture.model_dump(mode="json"),
            "program_architecture": reference.program_architecture.model_dump(mode="json"),
            "action_keys": list(reference.action_keys),
            "environment": reference.environment,
            "translation": {
                "kind": "immutable_union",
                "components": {
                    name: dataset.manifest.translation
                    for name, dataset in components.items()
                },
            },
            "selection": selection,
            "partitions": partitions,
            "shards": records,
        }
        _write_json(build_path / "manifest.json", manifest)
        settings.dataset_dir.parent.mkdir(parents=True, exist_ok=True)
        build_path.replace(settings.dataset_dir)
    except BaseException:
        shutil.rmtree(build_path, ignore_errors=True)
        raise

    result: dict[str, object] = {
        "schema_version": "conditional-program-aggregate-report-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "complete",
        "source": source,
        "dataset": {
            "path": str(settings.dataset_dir / "manifest.json"),
            "sha256": sha256_file(settings.dataset_dir / "manifest.json"),
            "dataset_id": dataset_id,
            "shards": len(records),
        },
        "components": component_identities,
        "selection": selection,
    }
    _write_json(report_path, result)
    return result


__all__ = ["prepare_program_aggregate"]
