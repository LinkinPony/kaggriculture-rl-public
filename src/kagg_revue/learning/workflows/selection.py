"""Authenticate the completed BC selection before granting a PPO handoff."""

import json
import math
from typing import Any

import torch

from kagg_revue.artifacts.io import digest
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.verification import finite
from kagg_revue.learning.pretraining.config import InitialWeights
from kagg_revue.learning.storage.artifacts import resolve
from kagg_revue.learning.workflows.config import Workflow


def select(config: Workflow) -> tuple[Experiment, dict[str, Any]]:
    """Use the minimum measured validation NLL only after normal BC completion."""
    directory = config.bc.output_dir
    status = json.loads((directory / "run-status.json").read_text())
    state = json.loads((directory / "state.json").read_text())
    progress = state.get("pretraining", {})
    monitor = progress.get("early_stopping", {})
    records = progress.get("records", [])
    if (
        status["status"] != "complete"
        or progress.get("completion_reason") not in {"patience", "epoch_limit"}
        or not records
        or not all(math.isfinite(row["selection_nll"]) for row in records)
        or not state.get("rl_initial")
    ):
        raise ValueError("BC must complete normally with a finite validation selection")
    best = min(records, key=lambda row: row["selection_nll"])
    member = state["rl_initial"]
    if (
        best["epoch"] != monitor["best_epoch"]
        or best["selection_nll"] != monitor["best_nll"]
        or member != monitor["best_member"]
    ):
        raise ValueError("BC handoff differs from the measured validation-best checkpoint")
    payload = torch.load(resolve(directory, state, member), map_location="cpu", weights_only=False)
    assert config.bc.demonstrations is not None
    if (
        payload["lineage"]["run_id"] != state["run_id"]
        or payload["lineage"].get("dataset_sha256") != config.bc.demonstrations.sha256
        or not finite(payload)
    ):
        raise ValueError("BC selected checkpoint has invalid lineage or nonfinite tensors")
    initial = InitialWeights(run=directory, checkpoint=member, sha256=state["members"][member])
    rl = Experiment.model_validate(
        {**config.rl.model_dump(mode="json"), "initial_weights": initial.model_dump(mode="json")}
    )
    return rl, {
        "bc_run": str(directory),
        "bc_run_id": state["run_id"],
        "bc_state_sha256": digest(directory / "state.json"),
        "completion_reason": progress["completion_reason"],
        "completed_epochs": len(records),
        "best_epoch": best["epoch"],
        "best_validation_nll": best["selection_nll"],
        "final_validation_nll": records[-1]["selection_nll"],
        "initial_weights": initial.model_dump(mode="json"),
        **(
            {"initial_critic": rl.initial_critic.model_dump(mode="json")}
            if rl.initial_critic is not None
            else {}
        ),
        "criterion": "minimum full validation grouped NLL among completed BC epochs",
    }
