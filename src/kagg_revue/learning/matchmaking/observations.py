"""Exact legacy observation contracts and authenticated native comparison evidence."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.policy.contracts import ContractLayout


def legacy_layout(layout: ContractLayout) -> ContractLayout:
    """Remove only the documented additive v4 fields from a grounded-v2 contract."""
    base = layout.observation
    if base.version != "grounded-production-context-v4":
        raise ValueError("legacy projection requires v4 observations")
    extra = (
        2 * layout.cells * base.agronomy_board_features
        + 9 * base.agronomy_product_features
        + base.agronomy_global_features
        + 2 * base.units * base.agronomy_unit_features
    )
    return replace(
        layout,
        observation=replace(
            base,
            version="grounded-production-context-v2",
            context_features=base.context_features - extra,
            agronomy_board_features=0,
            agronomy_product_features=0,
            agronomy_global_features=0,
            agronomy_unit_features=0,
        ),
    )


def verify_native_identity(state: dict[str, Any], source_native: str) -> None:
    """Require exact old/new native replay evidence before importing foreign binaries."""
    registered = state.get("opponent_native_qualification", {})
    path = Path(registered.get("path", ""))
    if not path.is_file() or digest(path) != registered.get("sha256"):
        raise ValueError("historical rule engine differs without authenticated replay evidence")
    report = json.loads(path.read_text())
    if report.get("schema") == "native-history-qualification-v2":
        matches = [
            entry
            for entry in report.get("comparisons", [])
            if entry.get("source_native_sha256") == source_native
            and entry.get("target_native_sha256") == state["native"]
        ]
        target_version = (
            "grounded-derived-context-v5b"
            if state.get("protocol", {}).get("derived", False)
            else "grounded-production-context-v4"
        )
        if report.get("passed") is not True or len(matches) != 1:
            raise ValueError("native qualification bundle has no unique authenticated source")
        evidence = matches[0]
        if (
            evidence.get("passed") is not True
            or evidence.get("legacy_version")
            not in {"grounded-production-context-v2", "grounded-production-context-v4"}
            or evidence.get("target_version") != target_version
            or evidence.get("checked_observations", 0) < 10000
            or evidence.get("matched_engine_trajectories") is not True
            or evidence.get("matched_features_actions_masks") is not True
        ):
            raise ValueError("native qualification bundle lacks exact legacy replay evidence")
        return
    if (
        report.get("passed") is not True
        or report.get("source_native_sha256") != source_native
        or report.get("target_native_sha256") != state["native"]
        or report.get("legacy_version") != "grounded-production-context-v2"
        or report.get("target_version") != "grounded-production-context-v4"
        or report.get("checked_observations", 0) < 10000
        or report.get("matched_engine_trajectories") is not True
    ):
        raise ValueError("native replay evidence does not bind these historical rule engines")
