"""Submission descriptions following the repository's established Kaggle format."""

from pathlib import Path
from typing import Any

from kagg_revue.deployment.publishing.config import Publishing


def describe(config: Publishing, job: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Include selected BC epoch or RL update, precision, temperature and provenance."""
    protocol = state["protocol"]
    member = job["member"]
    seed = str(protocol["seed"])
    label = config.labels.get(seed, Path(job["run"]).name)
    progress = state.get("pretraining", {})
    monitor = progress.get("early_stopping", {})
    is_bc = member.startswith("pretraining/")
    epoch = monitor.get("best_epoch") if monitor.get("best_member") == member else None
    position = (
        f"BC {'E' + str(epoch) + ' ' if epoch else ''}{Path(member).stem}"
        if is_bc
        else f"U{state['completed_update']}"
    )
    description = (
        f"{label} s{seed} {position}; FP32 T={config.temperature:g}; "
        f"ckpt {state['members'][member][:8]}"
    )
    population = protocol.get("population", {})
    return {
        "competition": "kaggriculture",
        "description": description,
        "captured_utc": job["captured_utc"],
        "run": job["run"],
        "run_id": state["run_id"],
        "training_status": job["training_status"],
        "checkpoint": member,
        "checkpoint_sha256": state["members"][member],
        "stage": "BC" if is_bc else "RL",
        "completed_update": state["completed_update"],
        "bc_selected_epoch": epoch,
        "bc_completed_epochs": len(progress.get("records", [])),
        "bc_selection": monitor,
        "initial_weights": protocol.get("initial_weights"),
        "initial_critic": protocol.get("initial_critic"),
        "precision": "fp32",
        "temperature": config.temperature,
        "memory_turns": protocol.get("memory_turns", 0),
        "reward": {
            "terminal_wdl": {"win": 1, "draw": 0, "loss": -1},
            "cash_weight": protocol.get("cash_weight", 0),
            "cash_margin": protocol.get("cash_margin"),
        },
        "population_fraction": population.get("fraction"),
        "pfsp": population.get("pfsp"),
        "qualification": (
            "Fresh CPU process smoke check; full official match not run by this scheduler."
        ),
        "archive_hash_location": (
            "External receipt.json (the final tar cannot contain its own hash)."
        ),
    }
