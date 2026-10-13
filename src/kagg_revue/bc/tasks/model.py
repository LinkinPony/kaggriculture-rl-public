"""Randomly initialized actor/task construction for scratch behavior cloning."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any, cast

import torch
from torch import Tensor

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.bc.config import ModelSettings
from kagg_revue.policy.economics import (
    CANDIDATE_FEATURES,
    PREFIX_FEATURES,
    QUANTITY_FEATURES,
    TURN_FEATURES,
)
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.policy.tasks.model import UnitTaskPolicy
from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.rl.tasks.config import TaskModelSettings
from kagg_revue.rl.tasks.model import TaskTapeActorCritic


def build_actor_architecture(
    backend: Any,
    environment: Mapping[str, object],
    unit_limit: int,
    settings: ModelSettings,
) -> tuple[ActorArchitecture, tuple[str, ...]]:
    """Bind random actor dimensions to the authenticated native ABI."""
    encoder = cast(Mapping[str, object], backend.actor_encoder_spec())
    codec = ReplayActionEncoder(
        cast(Mapping[str, Any], backend.action_codec_spec())
    )
    board_size = int(cast(int, environment["boardSize"]))
    keys = codec.keys
    architecture = ActorArchitecture(
        board_shape=(
            2,
            int(cast(int, encoder["board_channels"])),
            board_size,
            board_size,
        ),
        unit_shape=(
            2,
            unit_limit,
            int(cast(int, encoder["unit_feat"])),
        ),
        global_features=int(cast(int, encoder["global_feat"])),
        model_width=settings.model_width,
        entity_width=settings.entity_width,
        attention_heads=settings.attention_heads,
        feedforward_width=settings.feedforward_width,
        latent_tokens=settings.latent_tokens,
        register_tokens=settings.register_tokens,
        scene_layers=settings.scene_layers,
        temporal_layers=settings.temporal_layers,
        action_layers=settings.action_layers,
        max_history=settings.max_history,
        max_decisions=settings.max_decisions,
        unit_action_tokens=codec.unit_tokens,
        market_action_tokens=len(keys) - codec.unit_tokens,
        maximum_quantity=settings.maximum_quantity,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=settings.fact_dropout,
        skill_tokens=settings.skill_tokens,
        strategy_tokens=settings.strategy_tokens,
        strategy_version=settings.strategy_version,
        economic_feature_version=settings.economic_feature_version,
        economic_turn_features=(
            TURN_FEATURES if settings.economic_feature_version else 0
        ),
        economic_prefix_features=(
            PREFIX_FEATURES if settings.economic_feature_version else 0
        ),
        economic_candidate_features=(
            CANDIDATE_FEATURES if settings.economic_feature_version else 0
        ),
        economic_quantity_features=(
            QUANTITY_FEATURES if settings.economic_feature_version else 0
        ),
    )
    return architecture, keys


def initialize_scratch_model(
    actor_architecture: ActorArchitecture,
    contract: NativeTaskContract,
    settings: TaskModelSettings,
    device: torch.device,
) -> TaskTapeActorCritic:
    """Create every actor, task-policy, and outcome parameter from scratch."""
    task_architecture = contract.architecture(
        architecture_version=settings.architecture_version,
        context_width=actor_architecture.model_width,
        model_width=settings.model_width,
        feedforward_width=settings.feedforward_width,
        attention_heads=settings.attention_heads,
        prefix_layers=settings.prefix_layers,
        history_window=settings.history_window,
    )
    return TaskTapeActorCritic(
        TurnPolicyNet(actor_architecture),
        UnitTaskPolicy(task_architecture, contract.catalog),
    ).to(device)


def model_fingerprint(model: torch.nn.Module) -> str:
    """Hash an in-memory initialization without serializing an artifact."""
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        tensor = cast(Tensor, value).detach().cpu().contiguous()
        digest.update(name.encode())
        digest.update(str(tensor.dtype).encode())
        digest.update(str(tuple(tensor.shape)).encode())
        digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def scratch_initialization_identity(
    backend: Any,
    actor_architecture: ActorArchitecture,
    action_keys: tuple[str, ...],
    seed: int,
    model: torch.nn.Module,
) -> dict[str, object]:
    """Describe a random actor with the identities required at runtime."""
    encoder = cast(Mapping[str, object], backend.actor_encoder_spec())
    encoder_version = encoder.get("version")
    if not isinstance(encoder_version, str) or not encoder_version:
        raise ValueError("scratch actor encoder lacks a version")
    if len(action_keys) != actor_architecture.action_tokens:
        raise ValueError("scratch actor action vocabulary width differs")
    return {
        "kind": "random_from_seed",
        "seed": seed,
        "model_fingerprint": model_fingerprint(model),
        "actor_encoder_version": encoder_version,
        "derived_fact_version": actor_architecture.derived_fact_version,
        "action_keys": list(action_keys),
        "weight_artifact_imported": False,
        "optimizer_imported": False,
        "rng_imported": False,
    }


__all__ = [
    "build_actor_architecture",
    "initialize_scratch_model",
    "model_fingerprint",
    "scratch_initialization_identity",
]
