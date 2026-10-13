"""Atomic, bounded checkpoints for terminal-outcome training."""

from __future__ import annotations

import io
import json
import math
import os
import random
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.state import load_causal_actor_state, migrate_optimizer_state
from kagg_revue.rl.config import (
    CheckpointSettings,
    ResumeTransitionSettings,
    RlSettings,
)
from kagg_revue.rl.outcome import OutcomeActorCritic
from kagg_revue.rl.pfsp import HistoricalPfsp, actor_fingerprint

_CHECKPOINT_VERSION = "terminal-wdl-actor-critic-v10"
_COMPLETE_CHECKPOINT_VERSIONS = frozenset(
    {
        "terminal-wdl-actor-critic-v4",
        "terminal-wdl-actor-critic-v5",
        "terminal-wdl-actor-critic-v6",
        "terminal-wdl-actor-critic-v7",
        "terminal-wdl-actor-critic-v8",
        "terminal-wdl-actor-critic-v9",
        _CHECKPOINT_VERSION,
    }
)
_TRAINING_STATE_VERSION = "rl-training-state-v1"
_LEGACY_WDL_REWARD: dict[str, object] = {
    "mode": "wdl",
    "margin_beta": 0.0,
    "margin_cash_scale": 1.0,
}
_RUNTIME_EXECUTION_FIELDS = frozenset(
    {
        "rollout_actor_streams",
        "rollout_batch_games",
        "rollout_cpu_workers",
        "rollout_gpu_memory_fraction",
        "rollout_host_memory_limit_gib",
        "devices",
    }
)


def _training_contract(settings: RlSettings) -> dict[str, object]:
    """Return settings that must remain fixed across a resumed branch."""
    payload = settings.model_dump(mode="json")
    for name in (
        "initial_actor",
        "resume_checkpoint",
        "resume_transition",
        "output_dir",
        "updates",
        "checkpoint",
        "evaluation_opponents",
        "selection_seeds",
        "confirmation_seeds",
        "evaluation_device",
        "act_timeout_seconds",
        "remaining_overage_seconds",
        "observability",
    ):
        payload.pop(name)
    payload["distributed_world_size"] = len(settings.training_devices)
    return cast(dict[str, object], payload)


def _semantic_training_contract(payload: Mapping[str, object]) -> dict[str, object]:
    """Remove execution-only tuning from one persisted training contract."""
    normalized = dict(payload)
    normalized.setdefault("actor_initialization", "artifact")
    normalized.pop("skill_recognition_weight", None)
    normalized.pop("skill_effect_weight", None)
    normalized.setdefault("devices", [])
    normalized.setdefault("distributed_world_size", 1)
    normalized.setdefault("opponent_sampling", None)
    normalized.setdefault("frozen_actor_opponents", {})
    normalized.setdefault("terminal_reward", dict(_LEGACY_WDL_REWARD))
    parameter_noise = normalized.get("parameter_noise")
    if not isinstance(parameter_noise, Mapping) or parameter_noise.get("enabled") is not True:
        normalized.pop("parameter_noise", None)
    opening = normalized.get("opening_exploration")
    if not isinstance(opening, Mapping) or opening.get("enabled") is not True:
        normalized.pop("opening_exploration", None)
    return {
        name: value for name, value in normalized.items() if name not in _RUNTIME_EXECUTION_FIELDS
    }


def _critic_actor_gradient_transition(
    stored: Mapping[str, object],
    current: Mapping[str, object],
) -> bool:
    """Allow only the explicit one-way transition into joint critic gradients."""
    stored_semantic = _semantic_training_contract(stored)
    current_semantic = _semantic_training_contract(current)
    stored_gradient = stored_semantic.pop("critic_actor_gradient", False)
    current_gradient = current_semantic.pop("critic_actor_gradient", False)
    return (
        stored_gradient is False
        and current_gradient is True
        and stored_semantic == current_semantic
    )


def _actor_optimization_transition(
    stored: Mapping[str, object],
    current: Mapping[str, object],
    authorization: ResumeTransitionSettings | None,
) -> dict[str, object] | None:
    """Authenticate one critic-detach and actor learning-rate branch."""
    if authorization is None:
        return None
    stored_semantic = _semantic_training_contract(stored)
    current_semantic = _semantic_training_contract(current)
    stored_gradient = stored_semantic.pop("critic_actor_gradient", False)
    current_gradient = current_semantic.pop("critic_actor_gradient", False)
    stored_learning_rate = stored_semantic.pop("actor_learning_rate", None)
    current_learning_rate = current_semantic.pop("actor_learning_rate", None)
    if (
        not isinstance(stored_gradient, bool)
        or not isinstance(current_gradient, bool)
        or not isinstance(stored_learning_rate, int | float)
        or isinstance(stored_learning_rate, bool)
        or not isinstance(current_learning_rate, int | float)
        or isinstance(current_learning_rate, bool)
    ):
        return None
    if authorization.detach_critic_from_actor:
        if stored_gradient is not True or current_gradient is not False:
            return None
    elif stored_gradient is not current_gradient:
        return None
    multiplier = authorization.actor_learning_rate_multiplier
    expected_learning_rate = float(stored_learning_rate) * multiplier
    if (
        not math.isfinite(expected_learning_rate)
        or not math.isclose(
            float(current_learning_rate),
            expected_learning_rate,
            rel_tol=1e-12,
            abs_tol=0.0,
        )
        or stored_semantic != current_semantic
    ):
        return None
    return {
        "critic_actor_gradient": {
            "checkpoint": stored_gradient,
            "resolved": current_gradient,
            "detach_authorized": authorization.detach_critic_from_actor,
        },
        "actor_learning_rate": {
            "checkpoint": float(stored_learning_rate),
            "resolved": float(current_learning_rate),
            "multiplier": multiplier,
        },
    }


def _training_population_transition(
    stored: Mapping[str, object],
    current: Mapping[str, object],
) -> bool:
    """Allow a pure-self-play endpoint to start one explicit weighted branch."""
    stored_semantic = _semantic_training_contract(stored)
    current_semantic = _semantic_training_contract(current)
    stored_opponents = stored_semantic.pop("opponents", None)
    current_opponents = current_semantic.pop("opponents", None)
    stored_sampling = stored_semantic.pop("opponent_sampling", None)
    current_sampling = current_semantic.pop("opponent_sampling", None)
    stored_frozen = stored_semantic.pop("frozen_actor_opponents", {})
    current_frozen = current_semantic.pop("frozen_actor_opponents", {})
    stored_semantic.pop("public_agent_manifest", None)
    current_semantic.pop("public_agent_manifest", None)
    if stored_opponents != ["self_play"] or stored_sampling is not None or stored_frozen != {}:
        return False
    if not isinstance(current_opponents, list) or not isinstance(current_sampling, Mapping):
        return False
    weights = current_sampling.get("weights")
    return (
        current_sampling.get("mode") == "weighted_per_seed"
        and isinstance(weights, Mapping)
        and list(weights) == current_opponents
        and "self_play" in weights
        and len(current_opponents) > 1
        and isinstance(current_frozen, Mapping)
        and set(current_frozen) <= set(current_opponents) - {"self_play"}
        and stored_semantic == current_semantic
    )


def _terminal_reward_transition(
    stored: Mapping[str, object],
    current: Mapping[str, object],
    authorization: ResumeTransitionSettings | None,
) -> dict[str, object] | None:
    """Authorize one pure W/D/L to bounded margin-augmented branch."""
    if authorization is None or not authorization.enable_margin_augmented_wdl:
        return None
    stored_semantic = _semantic_training_contract(stored)
    current_semantic = _semantic_training_contract(current)
    stored_reward = stored_semantic.pop("terminal_reward", None)
    current_reward = current_semantic.pop("terminal_reward", None)
    if stored_reward != _LEGACY_WDL_REWARD or not isinstance(current_reward, Mapping):
        return None
    beta = current_reward.get("margin_beta")
    cash_scale = current_reward.get("margin_cash_scale")
    if (
        current_reward.get("mode") != "margin_augmented_wdl"
        or not isinstance(beta, int | float)
        or isinstance(beta, bool)
        or not math.isfinite(float(beta))
        or float(beta) <= 0.0
        or not isinstance(cash_scale, int | float)
        or isinstance(cash_scale, bool)
        or not math.isfinite(float(cash_scale))
        or float(cash_scale) <= 0.0
        or stored_semantic != current_semantic
    ):
        return None
    return {
        "checkpoint": dict(_LEGACY_WDL_REWARD),
        "resolved": dict(current_reward),
        "explicitly_authorized": True,
    }


def _opening_exploration_transition(
    stored: Mapping[str, object],
    current: Mapping[str, object],
    authorization: ResumeTransitionSettings | None,
) -> bool:
    """Allow an explicit switch into or between opening-exploration semantics."""
    if authorization is None or not (
        authorization.enable_opening_exploration or authorization.replace_opening_exploration
    ):
        return False
    stored_semantic = _semantic_training_contract(stored)
    current_semantic = _semantic_training_contract(current)
    stored_opening = stored_semantic.pop("opening_exploration", None)
    current_opening = current_semantic.pop("opening_exploration", None)
    stored_enabled = isinstance(stored_opening, Mapping) and stored_opening.get("enabled") is True
    current_enabled = (
        isinstance(current_opening, Mapping) and current_opening.get("enabled") is True
    )
    if stored_semantic != current_semantic or not current_enabled:
        return False
    if authorization.enable_opening_exploration:
        return not stored_enabled
    return (
        authorization.replace_opening_exploration
        and stored_enabled
        and stored_opening != current_opening
    )


def _runtime_execution_overrides(
    stored: Mapping[str, object],
    current: Mapping[str, object],
) -> dict[str, dict[str, object]]:
    """Describe resume-time throughput tuning without weakening provenance."""
    return {
        name: {"checkpoint": stored.get(name), "resolved": current.get(name)}
        for name in sorted(_RUNTIME_EXECUTION_FIELDS)
        if stored.get(name) != current.get(name)
    }


def _apply_actor_learning_rate_transition(
    optimizer: torch.optim.Optimizer,
    learning_rate: float,
) -> None:
    """Reapply the authorized actor rate after loading optimizer state."""
    if len(optimizer.param_groups) != 2:
        raise ValueError("RL actor-critic optimizer must contain two parameter groups")
    optimizer.param_groups[0]["lr"] = learning_rate


def _numpy_random_state() -> dict[str, object]:
    state = cast(
        tuple[str, NDArray[np.uint32], int, int, float],
        np.random.get_state(),
    )
    name, keys, position, has_gauss, cached_gaussian = state
    return {
        "name": name,
        "keys": torch.from_numpy(keys.copy()),
        "position": position,
        "has_gauss": has_gauss,
        "cached_gaussian": cached_gaussian,
    }


def _restore_numpy_random_state(payload: object) -> None:
    if not isinstance(payload, Mapping):
        raise ValueError("RL checkpoint NumPy random state is invalid")
    name = payload.get("name")
    keys = payload.get("keys")
    position = payload.get("position")
    has_gauss = payload.get("has_gauss")
    cached_gaussian = payload.get("cached_gaussian")
    if (
        not isinstance(name, str)
        or not isinstance(keys, Tensor)
        or not isinstance(position, int)
        or isinstance(position, bool)
        or not isinstance(has_gauss, int)
        or isinstance(has_gauss, bool)
        or not isinstance(cached_gaussian, int | float)
        or isinstance(cached_gaussian, bool)
    ):
        raise ValueError("RL checkpoint NumPy random state is incomplete")
    np.random.set_state(
        (
            name,
            keys.detach().cpu().numpy().astype(np.uint32, copy=True),
            position,
            has_gauss,
            float(cached_gaussian),
        )
    )


def capture_training_state(
    randomizer: random.Random,
    pfsp: HistoricalPfsp | None,
    device: torch.device,
    opening_exploration_state: dict[str, object] | None = None,
) -> dict[str, object]:
    """Capture every stochastic and bounded-population state used between updates."""
    return {
        "state_version": _TRAINING_STATE_VERSION,
        "python_random_state": random.getstate(),
        "numpy_random_state": _numpy_random_state(),
        "torch_cpu_random_state": torch.get_rng_state(),
        "torch_device_random_state": (
            torch.cuda.get_rng_state(device) if device.type == "cuda" else None
        ),
        "optimization_random_state": randomizer.getstate(),
        "pfsp_state": pfsp.state_dict() if pfsp is not None else None,
        "opening_exploration_state": opening_exploration_state,
    }


def serialize_training_state(payload: dict[str, object]) -> bytes:
    """Encode RNG state before object collectives touch tensor storages."""
    stream = io.BytesIO()
    torch.save(payload, stream)
    return stream.getvalue()


def deserialize_training_state(payload: bytes) -> dict[str, object]:
    """Decode one trusted rank-local RNG payload on CPU."""
    value = torch.load(io.BytesIO(payload), map_location="cpu", weights_only=True)
    if not isinstance(value, dict):
        raise ValueError("distributed RL training state is not a mapping")
    return cast(dict[str, object], value)


def restore_training_state(
    payload: object,
    randomizer: random.Random,
    pfsp: HistoricalPfsp | None,
    device: torch.device,
) -> dict[str, object] | None:
    """Restore stochastic streams and the bounded opponent population."""
    if not isinstance(payload, Mapping) or payload.get("state_version") != (
        _TRAINING_STATE_VERSION
    ):
        raise ValueError("RL checkpoint training state is unsupported")
    python_state = payload.get("python_random_state")
    optimization_state = payload.get("optimization_random_state")
    torch_cpu_state = payload.get("torch_cpu_random_state")
    torch_device_state = payload.get("torch_device_random_state")
    if not isinstance(python_state, tuple) or not isinstance(optimization_state, tuple):
        raise ValueError("RL checkpoint Python random state is invalid")
    if not isinstance(torch_cpu_state, Tensor):
        raise ValueError("RL checkpoint torch random state is invalid")
    if device.type == "cuda" and not isinstance(torch_device_state, Tensor):
        raise ValueError("RL checkpoint CUDA random state is absent")
    if device.type != "cuda" and torch_device_state is not None:
        raise ValueError("RL checkpoint device random state differs from the profile")

    pfsp_state = payload.get("pfsp_state")
    if pfsp is None:
        if pfsp_state is not None:
            raise ValueError("RL checkpoint contains PFSP state for a disabled population")
    else:
        if not isinstance(pfsp_state, Mapping):
            raise ValueError("RL checkpoint lacks its PFSP population")
        pfsp.load_state_dict(cast(Mapping[str, object], pfsp_state))

    try:
        random.setstate(python_state)
        randomizer.setstate(optimization_state)
    except (TypeError, ValueError) as error:
        raise ValueError("RL checkpoint Python random state is malformed") from error
    _restore_numpy_random_state(payload.get("numpy_random_state"))
    torch.set_rng_state(torch_cpu_state.detach().cpu())
    if isinstance(torch_device_state, Tensor):
        torch.cuda.set_rng_state(torch_device_state.detach().cpu(), device)
    legacy_noise_state = payload.get("parameter_noise_state")
    if legacy_noise_state is not None:
        raise ValueError("failed whole-episode parameter-noise checkpoints cannot resume")
    opening_state = payload.get("opening_exploration_state")
    if opening_state is not None and not isinstance(opening_state, dict):
        raise ValueError("RL checkpoint opening-exploration state is invalid")
    return cast(dict[str, object] | None, opening_state)


def build_checkpoint_payload(
    model: OutcomeActorCritic,
    optimizer: torch.optim.Optimizer,
    update: int,
    settings: RlSettings,
    initial_actor_sha256: str,
    randomizer: random.Random,
    pfsp: HistoricalPfsp | None,
    device: torch.device,
    distributed_training_states: list[dict[str, object]] | None = None,
    opening_exploration_state: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build one self-contained actor/critic/optimizer training endpoint."""
    training_states = (
        distributed_training_states
        if distributed_training_states is not None
        else [capture_training_state(randomizer, pfsp, device, opening_exploration_state)]
    )
    if len(training_states) != len(settings.training_devices):
        raise ValueError("checkpoint training states differ from the distributed world")
    return {
        "checkpoint_version": _CHECKPOINT_VERSION,
        "update": update,
        "architecture": model.actor.architecture_json(),
        "objective": {
            "discount": settings.discount,
            "gae_lambda": settings.gae_lambda,
        },
        "training_contract": _training_contract(settings),
        "initial_actor_sha256": initial_actor_sha256,
        "actor_state": {
            key: value.detach().cpu() for key, value in model.actor.state_dict().items()
        },
        "outcome_state": {
            key: value.detach().cpu() for key, value in model.outcome.state_dict().items()
        },
        "optimizer_state": optimizer.state_dict(),
        "training_state": training_states[0],
        "distributed_training_states": training_states,
        "distributed_world_size": len(training_states),
    }


def _load_outcome_state(
    model: OutcomeActorCritic,
    state: Mapping[str, object],
    *,
    checkpoint_version: object,
) -> tuple[str, ...]:
    """Load a critic, explicitly initializing context paths absent before v7."""
    valid = all(
        isinstance(name, str) and isinstance(value, Tensor) for name, value in state.items()
    )
    if not valid:
        raise ValueError("RL resume checkpoint critic state is invalid")
    tensors = cast(dict[str, Tensor], dict(state))
    if checkpoint_version in {"terminal-wdl-actor-critic-v9", _CHECKPOINT_VERSION}:
        model.outcome.load_state_dict(tensors, strict=True)
        return ()

    target_state = model.outcome.state_dict()
    initialized = tuple(name for name in target_state if name not in tensors)
    incompatible = model.outcome.load_state_dict(tensors, strict=False)
    if incompatible.unexpected_keys or set(incompatible.missing_keys) != set(initialized):
        raise ValueError("legacy RL critic state differs from the expected history-only head")
    parameter_names = {name for name, _ in model.outcome.named_parameters()}
    if not set(initialized) <= parameter_names:
        raise ValueError("legacy RL critic migration unexpectedly initialized buffers")
    return tuple(name for name, _ in model.outcome.named_parameters() if name in initialized)


def restore_checkpoint(
    path: Path,
    model: OutcomeActorCritic,
    optimizer: torch.optim.Optimizer,
    settings: RlSettings,
    initial_actor_sha256: str,
    randomizer: random.Random,
    pfsp: HistoricalPfsp | None,
    device: torch.device,
    *,
    distributed_rank: int = 0,
    distributed_world_size: int = 1,
) -> dict[str, object]:
    """Restore and authenticate a complete endpoint into a new output branch."""
    if not path.is_file():
        raise FileNotFoundError(f"RL resume checkpoint does not exist: {path}")
    raw = torch.load(path, map_location=device, weights_only=True)
    if not isinstance(raw, dict):
        raise ValueError("RL resume checkpoint is not a mapping")
    checkpoint = cast(dict[str, object], raw)
    checkpoint_version = checkpoint.get("checkpoint_version")
    if checkpoint_version not in {
        "terminal-wdl-actor-critic-v2",
        "terminal-wdl-actor-critic-v3",
        *_COMPLETE_CHECKPOINT_VERSIONS,
    }:
        raise ValueError("RL resume checkpoint version is unsupported")
    update = checkpoint.get("update")
    if not isinstance(update, int) or isinstance(update, bool) or update < 0:
        raise ValueError("RL resume checkpoint has an invalid update")
    if update >= settings.updates:
        raise ValueError(
            "RL target updates must exceed the resume checkpoint update: "
            f"{settings.updates} <= {update}"
        )
    checkpoint_architecture = ActorArchitecture.model_validate(checkpoint.get("architecture"))
    if checkpoint_architecture != model.actor.architecture:
        raise ValueError("RL resume checkpoint architecture differs from the initial actor")
    if checkpoint.get("initial_actor_sha256") != initial_actor_sha256:
        raise ValueError("RL resume checkpoint names a different initial actor")
    objective = checkpoint.get("objective")
    if checkpoint_version == "terminal-wdl-actor-critic-v2" and model.actor.skills is not None:
        raise ValueError("latent actor cannot resume a pre-latent RL checkpoint")
    if not isinstance(objective, Mapping):
        raise ValueError("RL resume checkpoint objective is invalid")
    normalized_objective = dict(objective)
    normalized_objective.pop("skill_recognition_weight", None)
    normalized_objective.pop("skill_effect_weight", None)
    expected_objective = {
        "discount": settings.discount,
        "gae_lambda": settings.gae_lambda,
    }
    if normalized_objective != expected_objective:
        raise ValueError("RL resume checkpoint objective differs from the resolved profile")
    runtime_overrides: dict[str, dict[str, object]] = {}
    actor_optimization_transition: dict[str, object] | None = None
    critic_actor_gradient_transition = False
    training_population_transition = False
    opening_exploration_transition = False
    terminal_reward_transition: dict[str, object] | None = None
    if checkpoint_version in _COMPLETE_CHECKPOINT_VERSIONS:
        stored_contract = checkpoint.get("training_contract")
        if not isinstance(stored_contract, Mapping):
            raise ValueError("RL resume checkpoint training profile is invalid")
        current_contract = _training_contract(settings)
        actor_optimization_transition = _actor_optimization_transition(
            stored_contract,
            current_contract,
            settings.resume_transition,
        )
        opening_exploration_transition = _opening_exploration_transition(
            stored_contract,
            current_contract,
            settings.resume_transition,
        )
        terminal_reward_transition = _terminal_reward_transition(
            stored_contract,
            current_contract,
            settings.resume_transition,
        )
        if settings.resume_transition is not None:
            authorized = (
                actor_optimization_transition is not None
                or opening_exploration_transition
                or terminal_reward_transition is not None
            )
            requested_opening = (
                settings.resume_transition.enable_opening_exploration
                or settings.resume_transition.replace_opening_exploration
            )
            matched_opening = not requested_opening or opening_exploration_transition
            requested_actor = (
                settings.resume_transition.detach_critic_from_actor
                or settings.resume_transition.actor_learning_rate_multiplier != 1.0
            )
            matched_actor = not requested_actor or actor_optimization_transition is not None
            requested_reward = settings.resume_transition.enable_margin_augmented_wdl
            matched_reward = not requested_reward or terminal_reward_transition is not None
            if not authorized or not matched_opening or not matched_actor or not matched_reward:
                raise ValueError(
                    "RL resume transition does not match the checkpoint and resolved profile"
                )
        if _semantic_training_contract(stored_contract) != _semantic_training_contract(
            current_contract
        ):
            critic_actor_gradient_transition = _critic_actor_gradient_transition(
                stored_contract,
                current_contract,
            )
            training_population_transition = _training_population_transition(
                stored_contract,
                current_contract,
            )
            if (
                actor_optimization_transition is None
                and not critic_actor_gradient_transition
                and not training_population_transition
                and not opening_exploration_transition
                and terminal_reward_transition is None
            ):
                raise ValueError("RL resume checkpoint training profile differs")
        runtime_overrides = _runtime_execution_overrides(
            stored_contract,
            current_contract,
        )
    elif settings.resume_transition is not None:
        raise ValueError("RL resume transition requires a complete checkpoint")

    actor_state = checkpoint.get("actor_state")
    outcome_state = checkpoint.get("outcome_state")
    optimizer_state = checkpoint.get("optimizer_state")
    fresh_optimizer = checkpoint.get("fresh_optimizer") is True
    if not isinstance(actor_state, dict) or not isinstance(outcome_state, dict):
        raise ValueError("RL resume checkpoint lacks actor or critic state")
    if not fresh_optimizer and not isinstance(optimizer_state, dict):
        raise ValueError("RL resume checkpoint lacks optimizer state")
    removed = load_causal_actor_state(model.actor, actor_state)
    initialized_outcome = _load_outcome_state(
        model,
        outcome_state,
        checkpoint_version=checkpoint_version,
    )
    if fresh_optimizer:
        if checkpoint_version != _CHECKPOINT_VERSION or update != 0:
            raise ValueError("fresh optimizer is only valid for a migrated v9 seed")
    elif removed or initialized_outcome:
        migrated_optimizer, removed_slots = migrate_optimizer_state(
            cast(dict[str, object], optimizer_state),
            (tuple(actor_state), tuple(outcome_state)),
            optimizer,
            (
                tuple(name for name, _ in model.actor.named_parameters()),
                tuple(name for name, _ in model.outcome.named_parameters()),
            ),
            allowed_missing_parameter_names=((), initialized_outcome),
        )
        optimizer.load_state_dict(migrated_optimizer)
        if set(removed_slots) != set(removed):
            raise ValueError("RL optimizer and actor auxiliary tensors differ")
    else:
        optimizer.load_state_dict(cast(dict[str, Any], optimizer_state))
    if actor_optimization_transition is not None:
        _apply_actor_learning_rate_transition(
            optimizer,
            settings.actor_learning_rate,
        )

    complete_state = checkpoint_version in _COMPLETE_CHECKPOINT_VERSIONS
    if complete_state:
        if checkpoint_version in {
            "terminal-wdl-actor-critic-v5",
            "terminal-wdl-actor-critic-v6",
            "terminal-wdl-actor-critic-v7",
            "terminal-wdl-actor-critic-v8",
            "terminal-wdl-actor-critic-v9",
            _CHECKPOINT_VERSION,
        }:
            checkpoint_world_size = checkpoint.get("distributed_world_size")
            training_states = checkpoint.get("distributed_training_states")
            if distributed_rank < 0 or distributed_rank >= distributed_world_size:
                raise ValueError("RL checkpoint distributed rank is outside the world")
            if checkpoint_world_size != distributed_world_size:
                raise ValueError("RL checkpoint distributed world size differs")
            if not isinstance(training_states, list) or len(training_states) != (
                distributed_world_size
            ):
                raise ValueError("RL checkpoint distributed training states are invalid")
            training_state = training_states[distributed_rank]
        else:
            if distributed_world_size != 1 or distributed_rank != 0:
                raise ValueError("legacy RL checkpoint cannot change distributed world size")
            training_state = checkpoint.get("training_state")
        opening_exploration_state = restore_training_state(
            training_state,
            randomizer,
            pfsp,
            device,
        )
    else:
        opening_exploration_state = None
    identity = {
        "kind": "actor_critic_checkpoint",
        "path": str(path),
        "sha256": sha256_file(path),
        "update": update,
        "actor_state_sha256": actor_fingerprint(model.actor),
    }
    return {
        "checkpoint": identity,
        "start_update": update + 1,
        "actor_critic_optimizer_restored": not fresh_optimizer,
        "legacy_auxiliary_tensors_removed": len(removed),
        "critic_parameters_initialized": len(initialized_outcome),
        "historical_population_restored": complete_state and pfsp is not None,
        "rng_state_restored": complete_state,
        "runtime_execution_overrides": runtime_overrides,
        "actor_optimization_transition": actor_optimization_transition,
        "critic_actor_gradient_transition": critic_actor_gradient_transition,
        "training_population_transition": training_population_transition,
        "opening_exploration_transition": opening_exploration_transition,
        "terminal_reward_transition": terminal_reward_transition,
        "opening_exploration_state": opening_exploration_state,
        "branch_semantics": (
            "new challenger seed with inherited weights and a fresh optimizer"
            if fresh_optimizer
            else (
                "complete update-boundary continuation with critic-to-actor gradients "
                "detached and actor learning rate changed"
            )
            if actor_optimization_transition is not None
            and settings.resume_transition is not None
            and settings.resume_transition.detach_critic_from_actor
            else "complete update-boundary continuation with actor learning rate changed"
            if actor_optimization_transition is not None
            else "complete update-boundary continuation with weighted training population enabled"
            if training_population_transition
            else "complete update-boundary continuation with opening exploration semantics changed"
            if opening_exploration_transition
            else "complete update-boundary continuation with bounded margin reward enabled"
            if terminal_reward_transition is not None
            else "complete update-boundary continuation with critic-to-actor gradients enabled"
            if critic_actor_gradient_transition
            else "complete update-boundary continuation with actor-safe critic expansion"
            if complete_state and initialized_outcome
            else (
                (
                    "complete update-boundary continuation with recorded runtime execution "
                    "overrides"
                    if runtime_overrides
                    else "complete update-boundary continuation"
                )
                if complete_state
                else "legacy model and optimizer continuation with newly seeded stochastic state"
            )
        ),
    }


class CheckpointStore:
    """Publish bounded rolling checkpoints and non-expiring milestones."""

    def __init__(self, output_dir: Path, settings: CheckpointSettings) -> None:
        """Create endpoint namespaces inside one immutable training run."""
        self._settings = settings
        self._root = output_dir / "checkpoints"
        self._rolling_dir = self._root / "rolling"
        self._permanent_dir = self._root / "permanent"
        self._rolling_dir.mkdir(parents=True)
        self._permanent_dir.mkdir(parents=True)
        self._rolling: dict[int, dict[str, object]] = {}
        self._permanent: dict[int, dict[str, object]] = {}

    @staticmethod
    def _name(update: int) -> str:
        return f"checkpoint-{update:08d}.pt"

    @staticmethod
    def _save(path: Path, payload: Mapping[str, object]) -> None:
        temporary = path.with_suffix(".pt.tmp")
        torch.save(dict(payload), temporary)
        temporary.replace(path)

    @staticmethod
    def _alias(source: Path, destination: Path) -> None:
        temporary = destination.with_name(f"{destination.name}.tmp")
        temporary.unlink(missing_ok=True)
        try:
            os.link(source, temporary)
        except OSError:
            shutil.copy2(source, temporary)
        temporary.replace(destination)

    @staticmethod
    def _record(path: Path, update: int, digest: str, size: int) -> dict[str, object]:
        return {
            "path": str(path),
            "sha256": digest,
            "size_bytes": size,
            "update": update,
        }

    def due(self, update: int, *, final: bool) -> bool:
        """Return whether this update must publish a recovery endpoint."""
        return (
            final
            or update % self._settings.rolling_interval == 0
            or update % self._settings.permanent_interval == 0
        )

    def _write_index(self, latest: Mapping[str, object]) -> None:
        payload = {
            "schema_version": "rl-checkpoint-index-v1",
            "latest": dict(latest),
            "rolling": [self._rolling[update] for update in sorted(self._rolling)],
            "permanent": [self._permanent[update] for update in sorted(self._permanent)],
            "policy": self._settings.model_dump(mode="json"),
        }
        path = self._root / "checkpoint-index.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(path)

    def publish(
        self,
        update: int,
        payload: Mapping[str, object],
        *,
        final: bool,
    ) -> dict[str, object] | None:
        """Save a due endpoint once, alias it as latest, and prune rolling excess."""
        rolling = update % self._settings.rolling_interval == 0
        permanent = update % self._settings.permanent_interval == 0
        if final and not rolling and not permanent:
            rolling = True
        if not rolling and not permanent:
            return None

        rolling_path = self._rolling_dir / self._name(update) if rolling else None
        permanent_path = self._permanent_dir / self._name(update) if permanent else None
        primary = permanent_path if permanent_path is not None else rolling_path
        if primary is None:
            raise RuntimeError("checkpoint publication lacks a destination")
        self._save(primary, payload)
        digest = sha256_file(primary)
        size = primary.stat().st_size
        if rolling_path is not None:
            if rolling_path != primary:
                self._alias(primary, rolling_path)
            self._rolling[update] = self._record(rolling_path, update, digest, size)
        if permanent_path is not None:
            self._permanent[update] = self._record(permanent_path, update, digest, size)

        while len(self._rolling) > self._settings.rolling_keep:
            oldest = min(self._rolling)
            old_path = Path(str(self._rolling.pop(oldest)["path"]))
            old_path.unlink(missing_ok=True)

        latest_path = self._root / "latest.pt"
        self._alias(primary, latest_path)
        record = {
            **self._record(primary, update, digest, size),
            "rolling": rolling,
            "permanent": permanent,
            "rolling_path": str(rolling_path) if rolling_path is not None else None,
            "permanent_path": str(permanent_path) if permanent_path is not None else None,
            "latest_path": str(latest_path),
        }
        self._write_index(record)
        return record


__all__ = [
    "CheckpointStore",
    "build_checkpoint_payload",
    "capture_training_state",
    "deserialize_training_state",
    "restore_checkpoint",
    "restore_training_state",
    "serialize_training_state",
]
