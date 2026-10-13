"""Validated behavior-cloning checkpoint persistence and continuation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import torch

from kagg_revue.bc.dataset import SequenceDataset, sha256_file
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.policy.state import load_causal_actor_state, migrate_optimizer_state


@dataclass(frozen=True)
class ResumeState:
    """Validated state inherited by a new immutable training run."""

    epoch: int
    objective: float
    report: dict[str, object]


def save_training_checkpoint(
    path: Path,
    model: TurnPolicyNet,
    dataset: SequenceDataset,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    validation: dict[str, float],
) -> None:
    """Atomically save model, optimizer, and selection evidence."""
    payload = {
        "checkpoint_version": "turn-policy-training-v5",
        "architecture": model.architecture_json(),
        "dataset": {
            "dataset_id": dataset.manifest.dataset_id,
            "manifest_sha256": dataset.manifest_sha256,
        },
        "epoch": epoch,
        "validation": validation,
        "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
        "optimizer_state": optimizer.state_dict(),
    }
    temporary = path.with_suffix(".pt.tmp")
    torch.save(payload, temporary)
    temporary.replace(path)


def restore_training_checkpoint(
    source_path: Path,
    destination_path: Path,
    model: TurnPolicyNet,
    dataset: SequenceDataset,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> ResumeState:
    """Restore a compatible best checkpoint and seed a new output run."""
    if not source_path.is_file():
        raise FileNotFoundError(f"resume checkpoint does not exist: {source_path}")
    if source_path.resolve() == destination_path.resolve():
        raise ValueError("resume checkpoint must belong to a different output directory")
    payload = torch.load(source_path, map_location=device, weights_only=True)
    if not isinstance(payload, dict):
        raise ValueError("resume checkpoint is not a mapping")
    version = payload.get("checkpoint_version")
    if version not in {
        "turn-policy-training-v3",
        "turn-policy-training-v4",
        "turn-policy-training-v5",
    }:
        raise ValueError(f"unsupported resume checkpoint version: {version}")

    checkpoint_architecture = ActorArchitecture.model_validate(payload.get("architecture"))
    if checkpoint_architecture != model.architecture:
        raise ValueError("resume checkpoint actor architecture differs")
    checkpoint_dataset = payload.get("dataset")
    if not isinstance(checkpoint_dataset, dict):
        raise ValueError("resume checkpoint lacks dataset identity")
    if (
        checkpoint_dataset.get("dataset_id") != dataset.manifest.dataset_id
        or checkpoint_dataset.get("manifest_sha256") != dataset.manifest_sha256
    ):
        raise ValueError("resume checkpoint dataset identity differs")

    epoch = payload.get("epoch")
    if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 1:
        raise ValueError("resume checkpoint epoch is invalid")
    validation_payload = payload.get("validation")
    if not isinstance(validation_payload, dict):
        raise ValueError("resume checkpoint lacks validation metrics")
    validation: dict[str, float] = {}
    for name, value in validation_payload.items():
        if not isinstance(name, str) or isinstance(value, bool) or not isinstance(
            value, (int, float)
        ):
            raise ValueError("resume checkpoint validation metrics are invalid")
        validation[name] = float(value)
    objective = (
        validation.get("objective_nll")
        if version == "turn-policy-training-v5"
        else validation.get("causal_objective_nll", validation.get("objective_nll"))
    )
    if objective is None or not math.isfinite(objective):
        raise ValueError("resume checkpoint lacks a finite selection objective")

    model_state = payload.get("model_state")
    if not isinstance(model_state, dict):
        raise ValueError("resume checkpoint lacks model state")
    removed = load_causal_actor_state(model, model_state)
    optimizer_state = payload.get("optimizer_state")
    optimizer_restored = optimizer_state is not None
    if optimizer_restored:
        if not isinstance(optimizer_state, dict):
            raise ValueError("resume checkpoint optimizer state is invalid")
        if removed:
            migrated_optimizer, removed_slots = migrate_optimizer_state(
                optimizer_state,
                (tuple(model_state),),
                optimizer,
                (tuple(name for name, _ in model.named_parameters()),),
            )
            optimizer.load_state_dict(migrated_optimizer)
            if set(removed_slots) != set(removed):
                raise ValueError("BC optimizer and actor auxiliary tensors differ")
        else:
            optimizer.load_state_dict(cast(dict[str, Any], optimizer_state))

    migrated_validation = dict(validation)
    migrated_validation["objective_nll"] = objective
    migrated_validation["total_loss"] = objective
    for name in (
        "auxiliary_loss",
        "causal_action_nll",
        "causal_quantity_nll",
        "causal_objective_nll",
        "skill_balance_kl",
        "skill_effect_mse",
        "skill_kl",
    ):
        migrated_validation.pop(name, None)
    save_training_checkpoint(
        destination_path,
        model,
        dataset,
        optimizer,
        epoch,
        migrated_validation,
    )
    return ResumeState(
        epoch=epoch,
        objective=objective,
        report={
            "path": str(source_path),
            "sha256": sha256_file(source_path),
            "checkpoint_version": version,
            "epoch": epoch,
            "optimizer_state_restored": optimizer_restored,
            "legacy_auxiliary_tensors_removed": len(removed),
            "random_state_restored": False,
        },
    )


__all__ = ["ResumeState", "restore_training_checkpoint", "save_training_checkpoint"]
