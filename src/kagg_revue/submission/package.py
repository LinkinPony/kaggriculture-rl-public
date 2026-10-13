"""Reproducible multi-ABI package construction for a frozen actor."""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from kagg_revue.artifacts.archive import _archive as _archive
from kagg_revue.artifacts.archive import _file_rows as _file_rows
from kagg_revue.artifacts.archive import _tar_filter as _tar_filter
from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.provenance import source_identity
from kagg_revue.native.compilation import _audit_elf as _audit_elf
from kagg_revue.native.compilation import _build_native as _build_native
from kagg_revue.native.compilation import _command as _command
from kagg_revue.native.compilation import _interpreter_value as _interpreter_value
from kagg_revue.native.compilation import _python_config_overlay as _python_config_overlay
from kagg_revue.native.compilation import _version_key as _version_key
from kagg_revue.submission.artifact import export_actor_snapshot
from kagg_revue.submission.config import SubmissionSettings

_SUBMISSION_LIMIT_BYTES = 100_000_000
_RUNTIME_SOURCES = (
    "kagg_revue/__init__.py",
    "kagg_revue/core/__init__.py",
    "kagg_revue/core/backend.py",
    "kagg_revue/native/__init__.py",
    "kagg_revue/native/engine.py",
    "kagg_revue/opponents/__init__.py",
    "kagg_revue/opponents/public.py",
    "kagg_revue/policy/__init__.py",
    "kagg_revue/policy/economics/__init__.py",
    "kagg_revue/policy/economics/compiler.py",
    "kagg_revue/policy/economics/layout.py",
    "kagg_revue/policy/economics/pricing.py",
    "kagg_revue/policy/economics/transition.py",
    "kagg_revue/policy/facts.py",
    "kagg_revue/policy/model.py",
    "kagg_revue/policy/quantity.py",
    "kagg_revue/policy/runtime.py",
    "kagg_revue/policy/skills.py",
    "kagg_revue/policy/state.py",
    "kagg_revue/policy/strategy.py",
    "kagg_revue/policy/transformer.py",
    "kagg_revue/policy/vocabulary.py",
    "kagg_revue/submission/__init__.py",
    "kagg_revue/submission/agent.py",
)
_ENTRYPOINT = """\
from pathlib import Path
import sys

if "__file__" in globals():
    _root = Path(__file__).resolve().parent
else:
    _root = Path(sys.path[-1]).resolve()
sys.path.insert(0, str(_root / "src"))

from kagg_revue.submission.agent import agent as _agent, runtime_info


def agent(observation, configuration):
    return _agent(observation, configuration)

__all__ = ["agent", "runtime_info"]
"""


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _copy_runtime_sources(repository_root: Path, package_root: Path) -> None:
    source_root = repository_root / "src"
    for relative in _RUNTIME_SOURCES:
        source = source_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"submission runtime source is absent: {source}")
        destination = package_root / "src" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _resolved_training(run_dir: Path) -> tuple[dict[str, Any], str]:
    path = run_dir / "resolved-settings.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("RL resolved settings must be a mapping")
    return cast(dict[str, Any], value), sha256_file(path)


def _reuse_actor_snapshot(
    source_dir: Path,
    destination: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    """Copy one authenticated actor so deployment-only fixes cannot change policy."""
    report_path = source_dir / "build-report.json"
    actor_path = source_dir / "actor.pt"
    if not report_path.is_file() or not actor_path.is_file():
        raise FileNotFoundError("source submission snapshot lacks its report or actor")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or not isinstance(report.get("snapshot"), dict):
        raise TypeError("source submission build report lacks its actor snapshot")
    snapshot = deepcopy(cast(dict[str, object], report["snapshot"]))
    if actor_path.stat().st_size != int(cast(int, snapshot.get("size_bytes", -1))) or sha256_file(
        actor_path
    ) != snapshot.get("sha256"):
        raise ValueError("source submission actor differs from its build report")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(actor_path, destination)
    snapshot["path"] = str(destination)
    return snapshot, {
        "path": str(source_dir),
        "build_report_sha256": sha256_file(report_path),
        "archive_sha256": sha256_file(source_dir / "submission.tar.gz"),
        "actor_sha256": snapshot["sha256"],
        "source": report.get("source"),
    }


def build_submission(
    settings: SubmissionSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Freeze the selected actor and atomically publish its Kaggle package."""
    repository_root = repository_root.resolve()
    training_run = (
        settings.training_run
        if settings.training_run.is_absolute()
        else repository_root / settings.training_run
    ).resolve()
    output_dir = (
        settings.output_dir
        if settings.output_dir.is_absolute()
        else repository_root / settings.output_dir
    ).resolve()
    if not training_run.is_relative_to((repository_root / "outputs").resolve()):
        raise ValueError("submission training run must be under repository outputs")
    if not output_dir.is_relative_to((repository_root / "outputs").resolve()):
        raise ValueError("submission artifacts must be written under repository outputs")
    source_snapshot = None
    if settings.source_snapshot is not None:
        source_snapshot = (
            settings.source_snapshot
            if settings.source_snapshot.is_absolute()
            else repository_root / settings.source_snapshot
        ).resolve()
        if not source_snapshot.is_relative_to((repository_root / "outputs").resolve()):
            raise ValueError("source submission snapshot must be under repository outputs")
    if output_dir.exists():
        raise FileExistsError(f"submission output already exists: {output_dir}")
    source = source_identity(repository_root)
    if source["worktree_dirty"]:
        raise ValueError("formal submission artifacts require a clean source revision")
    resolved, resolved_sha256 = _resolved_training(training_run)
    resolved_rl = resolved.get("rl")
    environment = resolved.get("resolved_environment")
    training_source = resolved.get("source")
    if not isinstance(resolved_rl, dict) or not isinstance(environment, dict):
        raise TypeError("RL resolved settings lack the deployment environment")
    if not isinstance(training_source, dict) or training_source.get("worktree_dirty") is not False:
        raise ValueError("RL training run was not launched from clean source")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{output_dir.name}-", dir=output_dir.parent
    ) as raw_staging:
        staging = Path(raw_staging)
        package_root = staging / "package"
        package_root.mkdir()
        _copy_runtime_sources(repository_root, package_root)
        (package_root / "main.py").write_text(_ENTRYPOINT, encoding="utf-8")

        actor_member = Path("artifacts") / "actor.pt"
        actor_path = package_root / actor_member
        repackaged_from: dict[str, object] | None = None
        if source_snapshot is None:
            snapshot = export_actor_snapshot(training_run, actor_path)
        else:
            snapshot, repackaged_from = _reuse_actor_snapshot(source_snapshot, actor_path)
        native_binaries = [
            _build_native(
                repository_root,
                package_root,
                interpreter,
                settings.native.compiler,
                settings.native.patchelf,
                settings.native.max_glibc,
                settings.native.jobs,
            )
            for interpreter in settings.native.interpreters
        ]
        native_abis = [str(record["python_abi"]) for record in native_binaries]
        if len(native_abis) != len(set(native_abis)):
            raise ValueError("native build interpreters produced duplicate Python ABIs")

        profile: dict[str, object] = {
            "schema_version": "turn-policy-submission-profile-v1",
            "actor_path": actor_member.as_posix(),
            "actor_sha256": snapshot["sha256"],
            "cpu_threads": settings.cpu_threads,
            "unit_limit": settings.unit_limit,
            "resolved_environment": environment,
            "native_binaries": native_binaries,
        }
        _write_json(package_root / "agent_profile.json", profile)
        files = _file_rows(package_root)
        manifest: dict[str, object] = {
            "schema_version": "turn-policy-kaggle-submission-v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "source_commit": source["commit"],
            "source_tree_sha256": source["source_tree_sha256"],
            "worktree_dirty": False,
            "probe_scaffold": False,
            "external_runtime_requirements": [],
            "base_runtime_imports": ["numpy", "pydantic", "torch"],
            "training_run": {
                "path": str(training_run),
                "resolved_settings_sha256": resolved_sha256,
                "launch_source": training_source,
            },
            "checkpoint": snapshot["checkpoint"],
            "initial_actor": snapshot["initial_actor"],
            "repackaged_from": repackaged_from,
            "actor_artifact": {
                "archive_path": actor_member.as_posix(),
                "sha256": snapshot["sha256"],
                "size_bytes": snapshot["size_bytes"],
                "actor_state_sha256": snapshot["actor_state_sha256"],
                "dtype": snapshot["dtype"],
            },
            "native_binaries": native_binaries,
            "agent_profile": profile,
            "files": files,
        }
        _write_json(package_root / "manifest.json", manifest)

        archive_path = staging / "submission.tar.gz"
        _archive(package_root, archive_path)
        if archive_path.stat().st_size >= _SUBMISSION_LIMIT_BYTES:
            raise ValueError("submission archive exceeds the competition byte limit")
        actor_output = staging / "actor.pt"
        shutil.copy2(actor_path, actor_output)
        snapshot["path"] = str(output_dir / "actor.pt")
        validation_source = repository_root / "src/kagg_revue/submission/kaggle_validate.py"
        shutil.copy2(validation_source, staging / "kaggle-validation.py")
        report: dict[str, object] = {
            "schema_version": "turn-policy-submission-build-v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "source": source,
            "training_source": training_source,
            "resolved_settings_sha256": resolved_sha256,
            "snapshot": snapshot,
            "repackaged_from": repackaged_from,
            "archive": {
                "path": str(output_dir / "submission.tar.gz"),
                "sha256": sha256_file(archive_path),
                "size_bytes": archive_path.stat().st_size,
                "submission_limit_bytes": _SUBMISSION_LIMIT_BYTES,
                "file_count": len(files) + 1,
            },
            "native_binaries": native_binaries,
        }
        _write_json(staging / "build-report.json", report)
        package_manifest = staging / "submission-manifest.json"
        shutil.copy2(package_root / "manifest.json", package_manifest)
        shutil.rmtree(package_root)
        staging.replace(output_dir)
    return cast(
        dict[str, object],
        json.loads((output_dir / "build-report.json").read_text(encoding="utf-8")),
    )


__all__ = ["build_submission"]
