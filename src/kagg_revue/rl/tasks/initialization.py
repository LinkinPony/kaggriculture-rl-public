"""Verified actor reuse for a single unit-task-tape challenger."""

from __future__ import annotations

import hashlib
from pathlib import Path

import torch

from kagg_revue.policy.runtime import load_actor
from kagg_revue.policy.tasks.model import UnitTaskPolicy
from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.rl.tasks.config import TaskModelSettings
from kagg_revue.rl.tasks.model import TaskTapeActorCritic


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def initialize_task_model(
    actor_path: Path,
    contract: NativeTaskContract,
    settings: TaskModelSettings,
    device: torch.device,
) -> tuple[TaskTapeActorCritic, dict[str, object]]:
    """Reuse the observation/market actor and create a neutral task pointer."""
    actor, action_keys, encoder_version, fact_version = load_actor(actor_path, device)
    architecture = actor.architecture
    if architecture.unit_shape[1] != contract.unit_limit:
        raise ValueError("initial actor and native task compiler use different unit limits")
    if architecture.maximum_quantity != contract.maximum_quantity:
        raise ValueError("initial actor and task compiler use different quantity limits")
    if architecture.board_shape[-1] != contract.board_size:
        raise ValueError("initial actor and task compiler use different board sizes")
    if architecture.skill_tokens:
        raise ValueError(
            "unit-task v1 requires a deterministic shared context, not latent skill samples"
        )
    task_architecture = contract.architecture(
        architecture_version=settings.architecture_version,
        context_width=architecture.model_width,
        model_width=settings.model_width,
        feedforward_width=settings.feedforward_width,
        attention_heads=settings.attention_heads,
        prefix_layers=settings.prefix_layers,
        history_window=settings.history_window,
    )
    model = TaskTapeActorCritic(
        actor,
        UnitTaskPolicy(task_architecture, contract.catalog).to(device),
    ).to(device)
    return model, {
        "path": str(actor_path),
        "sha256": _sha256(actor_path),
        "size_bytes": actor_path.stat().st_size,
        "actor_encoder_version": encoder_version,
        "derived_fact_version": fact_version,
        "action_keys": action_keys,
    }


__all__ = ["initialize_task_model"]
