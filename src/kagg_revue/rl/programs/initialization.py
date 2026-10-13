"""Verified actor reuse for conditional-program PPO."""

from __future__ import annotations

import hashlib
from pathlib import Path

import torch

from kagg_revue.policy.model import TurnPolicyNet
from kagg_revue.policy.programs.model import ConditionalProgramPolicy
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.runtime import load_actor
from kagg_revue.rl.programs.config import ProgramModelSettings
from kagg_revue.rl.programs.model import ProgramActorCritic


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def initialize_program_model(
    actor_path: Path,
    contract: NativeProgramContract,
    settings: ProgramModelSettings,
    device: torch.device,
    *,
    random_actor: bool = False,
) -> tuple[ProgramActorCritic, dict[str, object]]:
    """Create a program model from an actor ABI, optionally without its weights."""
    actor, action_keys, encoder_version, fact_version = load_actor(actor_path, device)
    architecture = actor.architecture
    if architecture.unit_shape[1] != contract.unit_limit:
        raise ValueError("initial actor and program compiler use different unit limits")
    if architecture.board_shape[-1] != contract.board_size:
        raise ValueError("initial actor and program compiler use different board sizes")
    if architecture.max_decisions < contract.maximum_decisions:
        raise ValueError("initial actor history cannot retain a complete program action")
    if architecture.turn_fact_features:
        raise ValueError("conditional-program v1 does not persist derived turn facts")
    if architecture.skill_tokens:
        raise ValueError("conditional-program v1 requires a deterministic causal context")
    if random_actor:
        actor = TurnPolicyNet(architecture).to(device)
    program_architecture = contract.architecture(
        context_width=architecture.model_width,
        model_width=settings.model_width,
        feedforward_width=settings.feedforward_width,
    )
    model = ProgramActorCritic(
        actor,
        ConditionalProgramPolicy(program_architecture, contract).to(device),
    ).to(device)
    return model, {
        "path": str(actor_path),
        "sha256": _sha256(actor_path),
        "size_bytes": actor_path.stat().st_size,
        "actor_encoder_version": encoder_version,
        "derived_fact_version": fact_version,
        "action_keys": action_keys,
        "initialization": "random" if random_actor else "pretrained",
    }


__all__ = ["initialize_program_model"]
