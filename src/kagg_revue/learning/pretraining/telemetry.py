"""Persist BC diagnostics separately from later PPO history and recovery state."""

import json
import time
from pathlib import Path
from typing import Any

from kagg_revue.learning.pretraining.config import GroupedLoss
from kagg_revue.learning.pretraining.statistics import DOMAINS


def mean_nll(loss_sum: float, rows: int, totals: list[float], config: GroupedLoss | None) -> float:
    """Normalize partition totals once, avoiding averages of unequal batch means."""
    if rows <= 0:
        raise ValueError("BC metrics require supervised rows")
    if config is None:
        return loss_sum / rows
    weights = [getattr(config.weights, name) for name in DOMAINS]
    if config.normalization == "field_mean":
        mass = sum(weight * totals[3 * index + 2] for index, weight in enumerate(weights))
        loss = sum(weight * totals[3 * index] for index, weight in enumerate(weights))
        return float(loss / mass) if mass > 0 else 0.0
    return float(
        sum(
            (weight / sum(weights)) * (totals[3 * index] / max(totals[3 * index + 2], 1))
            for index, weight in enumerate(weights)
        )
    )


def summed_fields(records: list[dict[str, Any]]) -> list[float]:
    """Combine additive field statistics across independently evaluated batches."""
    totals = [0.0] * (3 * len(DOMAINS))
    for record in records:
        if "field_totals" in record:
            totals = [
                left + right for left, right in zip(totals, record["field_totals"], strict=True)
            ]
    return totals


def partition_nll(records: list[dict[str, Any]], config: GroupedLoss | None) -> float:
    """Use all held-out fields for selection and confirmation, independent of packing."""
    return mean_nll(
        sum(record["loss_sum"] for record in records),
        sum(record["rows"] for record in records),
        summed_fields(records),
        config,
    )


def domain_metrics(totals: list[float]) -> dict[str, float]:
    """Normalize each action domain by its own count of supervised choices."""
    result = {}
    for index, name in enumerate(DOMAINS):
        loss, correct, count = totals[3 * index : 3 * index + 3]
        if count:
            result[f"{name}_nll"] = loss / count
            result[f"{name}_accuracy"] = correct / count
            result[f"{name}_fields"] = count
    return result


def accumulate(progress: dict[str, Any], result: dict[str, Any]) -> None:
    """Save additive epoch totals so checkpoint recovery retains metric weighting."""
    if "field_totals" in result:
        previous = progress.setdefault("epoch_field_totals", [0.0] * (3 * len(DOMAINS)))
        progress["epoch_field_totals"] = [
            left + right for left, right in zip(previous, result["field_totals"], strict=True)
        ]
    progress["epoch_seconds"] = progress.get("epoch_seconds", 0.0) + result.get(
        "performance", {}
    ).get("seconds", 0.0)


def epoch_metrics(
    progress: dict[str, Any], heldout: list[dict[str, Any]], validation_seconds: float
) -> dict[str, Any]:
    """Attach full-partition train/selection detail to an authenticated epoch record."""
    totals = summed_fields(heldout)
    return {
        "training": domain_metrics(progress.get("epoch_field_totals", [0.0] * len(totals))),
        "validation": domain_metrics(totals),
        "training_seconds": progress.get("epoch_seconds", 0.0),
        "validation_seconds": validation_seconds,
    }


def append(directory: Path, name: str, record: dict[str, Any]) -> None:
    """Append one completed measurement; training owns this file on rank zero only."""
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / name).open("a") as stream:
        stream.write(json.dumps({"wall_time": time.time(), **record}) + "\n")


def publish_epoch(directory: Path, record: dict[str, Any], elapsed: float) -> None:
    """Expose epoch curves without placing BC points on the PPO update axis."""
    seconds = record["training_seconds"]
    validation = record["validation_seconds"]
    append(
        directory,
        "metrics.jsonl",
        {
            "epoch": record["epoch"],
            **({"loss": record["loss"]} if "loss" in record else {}),
            "training": {
                **record["training"],
                "action_nll": record["train_nll"],
                "rows": record["train_rows"],
                "optimizer_steps": record["optimizer_steps"],
                "turns_per_second": record["train_rows"] / seconds if seconds else 0.0,
            },
            "validation": {
                **record["validation"],
                "action_nll": record["selection_nll"],
                "rows": record["selection_rows"],
                "turns_per_second": record["selection_rows"] / validation if validation else 0.0,
            },
            "system": {
                "elapsed_seconds": elapsed,
                "training_seconds": seconds,
                "validation_seconds": validation,
            },
        },
    )
