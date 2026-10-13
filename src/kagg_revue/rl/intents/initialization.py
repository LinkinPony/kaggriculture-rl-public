"""Authenticated turn-encoder reuse for intent-ledger PPO."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path

import torch

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.intents.contract import NativeIntentContract
from kagg_revue.policy.intents.model import (
    IntentActorCritic,
    IntentPolicy,
)
from kagg_revue.policy.intents.schema import IntentArchitecture
from kagg_revue.policy.model import TurnPolicyNet
from kagg_revue.policy.runtime import load_actor
from kagg_revue.rl.intents.config import IntentModelSettings


def _integer(values: Mapping[str, object], name: str) -> int:
    value = values.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"intent environment {name} must be an integer")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def initialize_intent_model(
    actor_path: Path,
    backend: BackendApi,
    environment: Mapping[str, object],
    unit_limit: int,
    settings: IntentModelSettings,
    device: torch.device,
    *,
    random_actor: bool = False,
) -> tuple[IntentActorCritic, NativeIntentContract, dict[str, object]]:
    """Create an intent model from a checked actor ABI and optional random weights."""
    actor, action_keys, encoder_version, fact_version = load_actor(actor_path, device)
    architecture = actor.architecture
    board_size = _integer(environment, "boardSize")
    episode_steps = _integer(environment, "episodeSteps")
    market_orders = _integer(environment, "maxMarketOrdersPerTurn")
    encoder = backend.actor_encoder_spec()
    codec = backend.action_codec_spec()
    if not isinstance(encoder, Mapping) or not isinstance(codec, Mapping):
        raise TypeError("native actor specs must be mappings")
    if (
        architecture.board_shape[-2:] != (board_size, board_size)
        or architecture.unit_shape[1] != unit_limit
        or architecture.board_shape[1] != int(encoder["board_channels"])
        or architecture.unit_shape[2] != int(encoder["unit_feat"])
        or architecture.global_features != int(encoder["global_feat"])
    ):
        raise ValueError("initial actor and intent rollout tensor ABIs differ")
    if encoder_version != str(encoder["version"]):
        raise ValueError("initial actor uses a different native encoder version")
    if action_keys != tuple(str(value) for value in codec["keys"]):
        raise ValueError("initial actor and native action vocabularies differ")
    if fact_version is not None or architecture.turn_fact_features:
        raise ValueError("canonical intent policy does not persist derived actor facts")
    if architecture.skill_tokens:
        raise ValueError("canonical intent policy requires deterministic turn context")
    if architecture.max_history < episode_steps - 1:
        raise ValueError("initial actor history is shorter than the episode")
    if architecture.max_decisions < unit_limit + market_orders:
        raise ValueError("initial actor cannot retain compiled intent actions")
    if random_actor:
        actor = TurnPolicyNet(architecture).to(device)
    raw_contract = backend.intent_ledger_spec()
    if not isinstance(raw_contract, Mapping):
        raise TypeError("native intent spec must be a mapping")
    contract = NativeIntentContract.from_spec(raw_contract, board_size=board_size)
    intent_architecture = IntentArchitecture.from_contract(
        contract,
        item_count=int(encoder["num_items"]),
        unit_limit=unit_limit,
        maximum_market_orders=market_orders,
        context_width=architecture.model_width,
        model_width=settings.model_width,
        feedforward_width=settings.feedforward_width,
    )
    model = IntentActorCritic(actor, IntentPolicy(intent_architecture)).to(device)
    model.actor.requires_grad_(False)
    if settings.train_turn_encoder:
        model.actor.scene.requires_grad_(True)
        model.actor.temporal.requires_grad_(True)
    return (
        model,
        contract,
        {
            "path": str(actor_path),
            "sha256": _sha256(actor_path),
            "size_bytes": actor_path.stat().st_size,
            "actor_encoder_version": encoder_version,
            "action_keys": action_keys,
            "initialization": "random" if random_actor else "pretrained",
        },
    )


__all__ = ["initialize_intent_model"]
