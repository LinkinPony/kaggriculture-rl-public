"""Read-only adaptation of policy-search artifacts, including older generations."""

import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from kagg_revue.production.expert.telemetry import (
    candidate_summary,
    generation_summary,
    panel_summary,
)


def enrich(directory: Path, row: dict[str, Any]) -> dict[str, Any]:
    """Recover old compact telemetry once during incremental ingestion, without rewriting it."""
    if "policy_search" in row:
        return row
    generation = row["generation"]
    try:
        complete = json.loads(
            (directory / "generations" / f"generation-{generation:06d}.json").read_text()
        )
        selected = json.loads(
            (directory / "selection" / f"generation-{generation:06d}.json").read_text()
        )
        ranks = complete["ranks"]
        for rank in ranks:
            report = json.loads(
                (
                    directory
                    / "generations"
                    / f"generation-{generation:06d}-rank-{rank['rank']}.json"
                ).read_text()
            )
            rank["search"] = {
                "seed_start": report["seed_start"],
                "controls": {
                    name: panel_summary(panel) for name, panel in report["controls"].items()
                },
                "candidates": [
                    candidate_summary(candidate, report["controls"])
                    for candidate in report["candidates"]
                ],
            }
        return {**row, "policy_search": generation_summary(ranks, selected)}
    except (OSError, ValueError, KeyError, TypeError):
        # Minimal generation/acceptance/timing telemetry remains usable if archives were removed.
        return row


def metrics(row: Mapping[str, Any]) -> dict[str, float]:
    """Name direct outcomes and measured costs without manufacturing PPO diagnostics."""
    result: dict[str, float] = {}

    def add(tag: str, value: object) -> None:
        if isinstance(value, int | float) and math.isfinite(value):
            result[f"search/{tag}"] = float(value)

    summary = row.get("policy_search", {})
    add("counts/accepted", row.get("accepted_policy_update"))
    for name, value in summary.get("counts", {}).items():
        add(f"counts/{name}", value)
    for name, value in row.get("timing", {}).items():
        add(f"timing/{name}", value)
    selection = summary.get("selection", {})
    for group in ("scripts", "neural", "paired_scripts", "paired_neural"):
        for name, value in selection.get(group, {}).items():
            add(f"selection/{group}/{name}", value)
    for opponent, panel in selection.get("scripts", {}).get("opponents", {}).items():
        games = sum(panel.get(name, 0) for name in ("wins", "ties", "losses"))
        if games:
            add(f"opponents/{opponent}/win_rate", panel["wins"] / games)
    ranks = summary.get("ranks", [])
    for name in (
        "elapsed_seconds",
        "inference_seconds",
        "native_seconds",
        "encoding_seconds",
        "collation_seconds",
        "proposal_seconds",
    ):
        values = [rank.get("timing", {}).get(name) for rank in ranks]
        valid = [value for value in values if isinstance(value, int | float)]
        if valid:
            add(f"ranks/{name}", max(valid))
    for name in ("peak_allocated_bytes", "peak_reserved_bytes", "cold_capture_seconds"):
        for rank in ranks:
            add(f"rank_{rank['rank']}/{name}", rank.get(name))
    return result


def context(row: Mapping[str, Any]) -> dict[str, Any]:
    """Bind the latest compact panels to their completed checkpoint and source identity."""
    return {
        **row.get("policy_search", {}),
        **{
            key: row[key]
            for key in ("generation", "checkpoint", "parent", "parent_sha256", "source_revision")
            if key in row
        },
    }


def live_progress(directory: Path) -> list[dict[str, Any]]:
    """Return coarse rank heartbeats; timestamps let the client expose stopped/stale phases."""
    rows = []
    for path in sorted((directory / "progress").glob("rank-*.json")):
        try:
            rows.append(json.loads(path.read_text()))
        except (OSError, ValueError):
            continue
    return rows
