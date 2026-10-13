"""Preserve a BC engine while qualifying an exactly equivalent optimized encoder."""

import json
import shutil
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.native import _revue_core as native


def validate(state: dict[str, Any], report_path: Path) -> dict[str, Any]:
    """Bind complete v4 replay equality to the old and currently loaded libraries."""
    report: dict[str, Any] = json.loads(report_path.read_text())
    if (
        report.get("passed") is not True
        or report.get("source_native_sha256") != state["native"]
        or report.get("target_native_sha256") != digest(Path(native.__file__))
        or report.get("source_version") != "grounded-production-context-v4"
        or report.get("target_version") != "grounded-production-context-v4"
        or report.get("checked_observations", 0) < 10000
        or report.get("matched_engine_trajectories") is not True
        or report.get("matched_features_actions_masks") is not True
    ):
        raise ValueError("optimized encoder lacks exact complete-replay v4 qualification")
    return report


def install(directory: Path, state: dict[str, Any], report_path: Path) -> None:
    """Archive the new engine and evidence without overwriting the original BC binary."""
    report = validate(state, report_path)
    library = Path(native.__file__)
    revision = directory / "native-revisions" / report["target_native_sha256"]
    revision.mkdir(parents=True, exist_ok=False)
    target = revision / library.name
    shutil.copy2(library, target)
    if digest(target) != report["target_native_sha256"]:
        raise ValueError("native library changed during archival")
    write_json(revision / "qualification.json", report)
    event = {
        "previous_native": state["native"],
        "previous_artifact": state["native_artifact"],
        "native": report["target_native_sha256"],
        "native_artifact": str(target.relative_to(directory)),
        "qualification_sha256": digest(report_path),
        "completed_update": state["completed_update"],
    }
    state["native_revisions"] = [*state.get("native_revisions", []), event]
    state.update(native=event["native"], native_artifact=event["native_artifact"])
