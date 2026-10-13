"""Authenticated recurrent-encoder reuse for atomic-effect PPO."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import torch
from torch import nn

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.effects.contract import NativeEffectContract
from kagg_revue.policy.effects.model import EffectActorCritic, EffectPolicy
from kagg_revue.policy.effects.schema import EffectArchitecture
from kagg_revue.policy.model import TurnPolicyNet
from kagg_revue.policy.runtime import load_actor
from kagg_revue.rl.effects.config import EffectModelSettings


def _integer(values: Mapping[str, object], name: str) -> int:
    value = values.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"effect environment {name} must be an integer")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def configure_effect_trainable(
    model: EffectActorCritic,
    *,
    train_turn_encoder: bool,
) -> tuple[nn.Parameter, ...]:
    """Enable exactly the modules that causally feed the effect objective."""
    model.requires_grad_(False)
    model.effects.requires_grad_(True)
    if model.critic is not None:
        model.critic.requires_grad_(True)
        model.effects.value_head.requires_grad_(False)
    if train_turn_encoder:
        modules = (
            model.actor.scene,
            model.actor.temporal,
            model.actor.strategy,
        )
        for module in modules:
            if module is not None:
                module.requires_grad_(True)
    parameters = tuple(parameter for parameter in model.parameters() if parameter.requires_grad)
    if not parameters:
        raise RuntimeError("effect profile froze every trainable parameter")
    return parameters


def effect_optimizer_parameters(
    model: EffectActorCritic,
) -> tuple[tuple[nn.Parameter, ...], tuple[nn.Parameter, ...]]:
    """Separate policy/shared parameters from the terminal W/D/L head."""
    critic = tuple(
        parameter
        for parameter in (
            model.effects.value_head if model.critic is None else model.critic
        ).parameters()
        if parameter.requires_grad
    )
    critic_ids = {id(parameter) for parameter in critic}
    actor = tuple(
        parameter
        for parameter in model.parameters()
        if parameter.requires_grad and id(parameter) not in critic_ids
    )
    if not actor or not critic:
        raise RuntimeError("effect optimizer requires actor and critic parameter groups")
    return actor, critic


def initialize_effect_model(
    actor_path: Path,
    backend: BackendApi,
    environment: Mapping[str, object],
    unit_limit: int,
    settings: EffectModelSettings,
    device: torch.device,
    *,
    random_actor: bool = False,
) -> tuple[EffectActorCritic, NativeEffectContract, dict[str, object]]:
    """Build an effect model from a checked actor ABI and optional fresh weights."""
    actor, action_keys, encoder_version, fact_version = load_actor(actor_path, device)
    architecture = actor.architecture
    board_size = _integer(environment, "boardSize")
    episode_steps = _integer(environment, "episodeSteps")
    market_orders = _integer(environment, "maxMarketOrdersPerTurn")
    encoder = backend.actor_encoder_spec()
    codec = backend.action_codec_spec()
    if not isinstance(encoder, Mapping) or not isinstance(codec, Mapping):
        raise TypeError("native actor specs must be mappings")
    native_keys = tuple(str(value) for value in cast(Sequence[object], codec["keys"]))
    if (
        architecture.board_shape[-2:] != (board_size, board_size)
        or architecture.unit_shape[1] != unit_limit
        or architecture.board_shape[1] != int(encoder["board_channels"])
        or architecture.unit_shape[2] != int(encoder["unit_feat"])
        or architecture.global_features != int(encoder["global_feat"])
    ):
        raise ValueError("initial actor and effect rollout tensor ABIs differ")
    if encoder_version != str(encoder["version"]):
        raise ValueError("initial actor uses a different native encoder version")
    if action_keys != native_keys:
        raise ValueError("initial actor and native action vocabularies differ")
    if fact_version is not None or architecture.turn_fact_features:
        raise ValueError("atomic-effect policy does not persist derived actor facts")
    if architecture.skill_tokens:
        raise ValueError("atomic-effect policy requires deterministic turn context")
    if architecture.max_history < episode_steps - 1:
        raise ValueError("initial actor history is shorter than the episode")
    if architecture.max_decisions < unit_limit + market_orders:
        raise ValueError("initial actor cannot retain compiled effect actions")
    if random_actor:
        actor = TurnPolicyNet(architecture).to(device)
    raw_contract = backend.effect_policy_spec()
    if not isinstance(raw_contract, Mapping):
        raise TypeError("native effect spec must be a mapping")
    contract = NativeEffectContract.from_spec(raw_contract, board_size=board_size)
    effect_architecture = EffectArchitecture.from_contract(
        contract,
        item_count=int(encoder["num_items"]),
        unit_limit=unit_limit,
        maximum_market_orders=market_orders,
        context_width=architecture.model_width,
        model_width=settings.model_width,
        feedforward_width=settings.feedforward_width,
        attention_heads=settings.attention_heads,
        state_layers=settings.state_layers,
    )
    effect_architecture = effect_architecture.model_copy(
        update={
            "critic_representation": "entity_recurrent_v2",
            "prefix_encoding": settings.prefix_encoding,
            "independent_critic": settings.independent_critic,
            "task_conditioning": settings.task_conditioning,
            "destination_tasks": settings.destination_tasks,
        }
    )
    model = EffectActorCritic(actor, EffectPolicy(effect_architecture)).to(device)
    configure_effect_trainable(
        model,
        train_turn_encoder=settings.train_turn_encoder,
    )
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


def initialize_challenger(
    model: EffectActorCritic, settings: EffectModelSettings
) -> EffectActorCritic:
    """Transplant a neural checkpoint into an explicitly requested new architecture."""
    previous = model.effects.architecture
    changes = {
        "critic_representation": "entity_recurrent_v2",
        "prefix_encoding": settings.prefix_encoding,
        "independent_critic": settings.independent_critic,
        "task_conditioning": settings.task_conditioning,
        "destination_tasks": settings.destination_tasks,
    }
    if all(getattr(previous, name) == value for name, value in changes.items()):
        return model
    if any(getattr(previous, name) and not value for name, value in changes.items()):
        raise ValueError("challenger initialization cannot silently remove trained modules")
    effects = EffectPolicy(previous.model_copy(update=changes)).to(next(model.parameters()).device)
    missing, unexpected = effects.load_state_dict(model.effects.state_dict(), strict=False)
    if unexpected or any(not name.startswith("prefix_query.") for name in missing):
        raise ValueError("challenger initialization changed existing actor weights")
    result = EffectActorCritic(model.actor, effects).to(next(model.parameters()).device)
    if model.critic is not None and result.critic is not None:
        result.critic.load_state_dict(model.critic.state_dict())
    return result


__all__ = [
    "configure_effect_trainable",
    "effect_optimizer_parameters",
    "initialize_effect_model",
]
