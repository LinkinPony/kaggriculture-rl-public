"""Artifact-bound quality analysis for compact behavior datasets."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import numpy as np

from kagg_revue.bc.dataset import sha256_file


def _summary(values: Sequence[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "min": None, "median": None, "p90": None, "max": None}
    array = np.asarray(values, dtype=np.float64)
    return {
        "count": len(values),
        "min": float(array.min()),
        "mean": float(array.mean()),
        "median": float(np.quantile(array, 0.5)),
        "p90": float(np.quantile(array, 0.9)),
        "max": float(array.max()),
    }


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    return value


def _float(value: object, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    return float(value)


def build_analysis(
    *,
    dataset_dir: Path,
    dataset_id: str,
    source: Mapping[str, object],
    source_archives: Sequence[Mapping[str, object]],
    index_rows: Sequence[Mapping[str, object]],
    sequences: Sequence[Mapping[str, object]],
    rejected: Sequence[Mapping[str, str]],
    action_keys: Sequence[str],
    action_counts: Mapping[int, int],
    repairs: Mapping[str, int],
    unit_histogram: Mapping[int, int],
    market_histogram: Mapping[int, int],
    decision_histogram: Mapping[int, int],
    quantity_histogram: Mapping[int, int],
) -> dict[str, object]:
    """Build direct, descriptive diagnostics without assigning promotion authority."""
    episode_ids = {str(row["episode_id"]) for row in sequences}
    turns = sum(_integer(row["turns"], "turns") for row in sequences)
    decisions = sum(_integer(row["decisions"], "decisions") for row in sequences)
    source_uncompressed = sum(
        _integer(row["uncompressed_bytes"], "uncompressed_bytes") for row in source_archives
    )
    source_compressed = sum(_integer(row["size_bytes"], "size_bytes") for row in source_archives)
    compact_bytes = (
        sum(path.stat().st_size for path in dataset_dir.glob("turn-*.npz"))
        + (dataset_dir / "manifest.json").stat().st_size
    )
    agent_counts = Counter(str(row["agent_name"]) for row in sequences)
    date_sequences = Counter(str(row["source_date"]) for row in sequences)
    date_episodes: dict[str, set[str]] = {}
    for row in sequences:
        date_episodes.setdefault(str(row["source_date"]), set()).add(str(row["episode_id"]))
    cash = [_float(row["terminal_cash"], "terminal_cash") for row in sequences]
    margins = [_float(row["margin"], "margin") for row in sequences]
    source_scores = [
        _float(row["source_average_score"], "source_average_score")
        for row in sequences
        if _integer(row["seat"], "seat") == 0
    ]
    overage = [
        _float(value, "minimum_remaining_overage")
        for row in sequences
        if (value := row.get("minimum_remaining_overage")) is not None
    ]
    total_action_count = sum(action_counts.values())
    action_rows = [
        {
            "token": token,
            "key": action_keys[token],
            "count": action_counts.get(token, 0),
            "fraction": action_counts.get(token, 0) / max(1, total_action_count),
        }
        for token in range(len(action_keys))
    ]
    action_rows.sort(key=lambda row: _integer(row["count"], "action count"), reverse=True)
    rejection_counts = Counter(row["reason"] for row in rejected)
    quantity_rows = []
    for bucket, count in sorted(quantity_histogram.items()):
        quantity_rows.append(
            {
                "bucket": bucket,
                "range": ("no-quantity" if bucket < 0 else f"{2**bucket}..{2 ** (bucket + 1) - 1}"),
                "count": count,
            }
        )
    return {
        "schema_version": "bc-data-analysis-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "purpose": "behavior warm-start data diagnostics; no promotion authority",
        "dataset": {
            "path": str(dataset_dir),
            "dataset_id": dataset_id,
            "manifest_sha256": sha256_file(dataset_dir / "manifest.json"),
            "compact_bytes": compact_bytes,
        },
        "source": dict(source),
        "raw": {
            "archives": list(source_archives),
            "index_rows": list(index_rows),
            "compressed_bytes": source_compressed,
            "uncompressed_json_bytes": source_uncompressed,
        },
        "cleaning": {
            "accepted_episodes": len(episode_ids),
            "rejected_episodes": len(rejected),
            "rejection_counts": dict(sorted(rejection_counts.items())),
            "rejection_examples": list(rejected[:100]),
            "canonical_repairs": dict(sorted(repairs.items())),
            "sequences": len(sequences),
            "turns": turns,
            "decisions": decisions,
        },
        "storage": {
            "compact_to_uncompressed_json_ratio": compact_bytes / max(1, source_uncompressed),
            "compact_to_source_zip_ratio": compact_bytes / max(1, source_compressed),
        },
        "coverage": {
            "unique_agent_display_names": len(agent_counts),
            "daily_selection_average_score": _summary(source_scores),
            "top_agent_display_names": [
                {"name": name, "sequences": count} for name, count in agent_counts.most_common(30)
            ],
            "by_date": {
                date: {
                    "episodes": len(date_episodes[date]),
                    "sequences": date_sequences[date],
                }
                for date in sorted(date_sequences)
            },
        },
        "outcomes": {
            "terminal_cash": _summary(cash),
            "terminal_cash_difference": _summary(margins),
            "wins": sum(value > 0 for value in margins),
            "ties": sum(value == 0 for value in margins),
            "losses": sum(value < 0 for value in margins),
        },
        "time_budget": {
            "minimum_remaining_overage_seconds": _summary(overage),
            "sequences_below_zero": sum(value < 0 for value in overage),
        },
        "actions": {
            "total": total_action_count,
            "by_token": action_rows,
            "unit_decisions_per_turn": {
                str(key): value for key, value in sorted(unit_histogram.items())
            },
            "market_orders_per_turn": {
                str(key): value for key, value in sorted(market_histogram.items())
            },
            "total_decisions_per_turn": {
                str(key): value for key, value in sorted(decision_histogram.items())
            },
            "quantity_log2_histogram": quantity_rows,
        },
        "interpretation": {
            "selection": (
                "Kaggle daily archives are already selected by average agent rating; both "
                "seats are retained, and no terminal-outcome filtering is applied."
            ),
            "agent_identity": (
                "Agent names are public display labels, not immutable notebook artifact IDs."
            ),
            "decision_boundary": (
                "BC accuracy and replay resemblance are diagnostics only; a checkpoint must "
                "earn production status in complete official-rule paired matches."
            ),
        },
    }


def write_analysis(report: Mapping[str, object], output_dir: Path) -> None:
    """Persist machine-readable evidence and a compact human entry point."""
    output_dir.mkdir(parents=True)
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    cleaning = report["cleaning"]
    storage = report["storage"]
    outcomes = report["outcomes"]
    coverage = report["coverage"]
    if not all(isinstance(value, Mapping) for value in (cleaning, storage, outcomes, coverage)):
        raise TypeError("analysis report sections must be mappings")
    cleaning = cast(Mapping[str, object], cleaning)
    storage = cast(Mapping[str, object], storage)
    outcomes = cast(Mapping[str, object], outcomes)
    coverage = cast(Mapping[str, object], coverage)
    top_agents = coverage["top_agent_display_names"]
    if not isinstance(top_agents, list):
        raise TypeError("top agent rows must be a list")
    dataset = report["dataset"]
    if not isinstance(dataset, Mapping):
        raise TypeError("analysis dataset section must be a mapping")
    agent_lines = "\n".join(
        f"- {row['name']}: {row['sequences']} sequences"
        for row in top_agents[:15]
        if isinstance(row, Mapping)
    )
    compact_ratio = _float(
        storage["compact_to_uncompressed_json_ratio"],
        "compact_to_uncompressed_json_ratio",
    )
    markdown = f"""# Kaggriculture BC data evidence snapshot

Generated: `{report["generated_at"]}`

Dataset: `{dataset["dataset_id"]}`

Manifest SHA-256: `{dataset["manifest_sha256"]}`

## Result

- Accepted episodes: {cleaning["accepted_episodes"]}; rejected: {cleaning["rejected_episodes"]}.
- Seat sequences: {cleaning["sequences"]}; turns: {cleaning["turns"]};
  decisions: {cleaning["decisions"]}.
- Compact/uncompressed JSON ratio: {compact_ratio:.4%}.
- Outcome snapshot: {outcomes["wins"]} wins, {outcomes["ties"]} ties,
  {outcomes["losses"]} losses across paired seats.

## Most represented public agent display names

{agent_lines}

## Interpretation

The daily source is preselected by Kaggle using average agent rating. Both seats are retained
without filtering on terminal cash. Display names are not immutable notebook identities. BC
metrics have no promotion authority; closed-loop official-rule paired matches remain required.
"""
    (output_dir / "report.md").write_text(markdown, encoding="utf-8")


__all__ = ["build_analysis", "write_analysis"]
