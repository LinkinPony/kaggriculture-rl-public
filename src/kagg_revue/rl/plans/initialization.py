"""Authenticated, representation-only BC initialization for plan PPO."""

from __future__ import annotations

from pathlib import Path

import torch
from torch import nn

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.policy.model import TurnPolicyNet
from kagg_revue.policy.plans.model import StructuredPlanPolicy
from kagg_revue.policy.runtime import load_actor

_NONTRANSFERRED_ARCHITECTURE_FIELDS = frozenset(
    {"action_layers", "max_decisions", "max_history"}
)


def _shared_architecture(model: StructuredPlanPolicy) -> dict[str, object]:
    payload = model.backbone.scene.architecture.model_dump(mode="python")
    return {
        name: value
        for name, value in payload.items()
        if name not in _NONTRANSFERRED_ARCHITECTURE_FIELDS
    }


def _source_architecture(model: TurnPolicyNet) -> dict[str, object]:
    payload = model.architecture.model_dump(mode="python")
    return {
        name: value
        for name, value in payload.items()
        if name not in _NONTRANSFERRED_ARCHITECTURE_FIELDS
    }


def transfer_plan_backbone(
    model: StructuredPlanPolicy,
    source: TurnPolicyNet,
) -> dict[str, int]:
    """Copy only semantically compatible scene, temporal, and strategy modules."""
    if _source_architecture(source) != _shared_architecture(model):
        raise ValueError("BC actor shared architecture differs from structured plan")
    if source.strategy is None or model.backbone.strategy is None:
        raise ValueError("BC actor and structured plan both require strategy state")
    groups: tuple[tuple[str, nn.Module, nn.Module], ...] = (
        ("scene", model.backbone.scene, source.scene),
        ("temporal", model.backbone.temporal, source.temporal),
        ("strategy", model.backbone.strategy, source.strategy),
    )
    report: dict[str, int] = {}
    for name, destination, origin in groups:
        destination.load_state_dict(origin.state_dict(), strict=True)
        report[name] = sum(parameter.numel() for parameter in destination.parameters())
    report["total"] = sum(report.values())
    return report


def initialize_plan_backbone(
    model: StructuredPlanPolicy,
    artifact: Path,
) -> dict[str, object]:
    """Authenticate an old BC actor and transfer no action-decision modules."""
    if not artifact.is_file():
        raise FileNotFoundError(f"structured-plan BC actor does not exist: {artifact}")
    cpu_rng = torch.get_rng_state()
    try:
        source, action_keys, encoder_version, fact_version = load_actor(
            artifact,
            torch.device("cpu"),
        )
    finally:
        torch.set_rng_state(cpu_rng)
    transferred = transfer_plan_backbone(model, source)
    return {
        "mode": "bc_backbone",
        "artifact": str(artifact),
        "sha256": sha256_file(artifact),
        "actor_encoder_version": encoder_version,
        "derived_fact_version": fact_version,
        "source_action_tokens": len(action_keys),
        "transferred_groups": transferred,
        "excluded_groups": [
            "primitive_action_decoder",
            "portfolio_encoder",
            "portfolio_factor_decoder",
            "portfolio_action_heads",
            "outcome_critic",
        ],
    }


__all__ = ["initialize_plan_backbone", "transfer_plan_backbone"]
