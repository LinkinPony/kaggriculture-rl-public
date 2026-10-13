"""Checkpointable validation patience and best-epoch selection for imitation."""

import math
from typing import Any

from kagg_revue.learning.pretraining.config import EarlyStopping


def observe(progress: dict[str, Any], config: EarlyStopping) -> bool:
    """Track the lowest NLL separately from the meaningful-improvement reference."""
    record = progress["records"][-1]
    value = float(record["selection_nll"])
    if not math.isfinite(value):
        raise ValueError("BC selection NLL must be finite")
    monitor = progress.setdefault("early_stopping", {})
    if not monitor or value < monitor["best_nll"]:
        monitor.update(
            best_nll=value,
            best_epoch=record["epoch"],
            best_member=f"pretraining/shard-{progress['cursor']:06d}.pt",
        )
    reference = monitor.get("reference_nll")
    improved = reference is None or (value < reference and reference - value >= config.min_delta)
    if improved:
        monitor.update(reference_nll=value, bad_epochs=0)
    else:
        monitor["bad_epochs"] += 1
    monitor.update(patience=config.patience, min_delta=config.min_delta)
    record.update(significant_improvement=improved, bad_epochs=monitor["bad_epochs"])
    return bool(monitor["bad_epochs"] >= config.patience)
