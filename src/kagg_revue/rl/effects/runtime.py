"""Runtime contracts and reporting helpers for atomic-effect training."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

import torch
from torch.optim import Optimizer

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.effects.contract import NativeEffectContract
from kagg_revue.policy.effects.model import EffectActorCritic
from kagg_revue.rl.effects.config import EffectRlSettings


def integer_metric(values: Mapping[str, object], name: str) -> int:
    """Read a strict integer from a native or training metric mapping."""
    value = values.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"effect {name} must be an integer")
    return value


def numeric_metric(values: Mapping[str, object], name: str) -> float:
    """Read a finite-width numeric value from a training metric mapping."""
    value = values.get(name)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"effect {name} must be numeric")
    return float(value)


def native_contract(
    backend: BackendApi,
    environment: Mapping[str, object],
) -> NativeEffectContract:
    """Bind the resolved environment to the loaded native effect ABI."""
    raw = backend.effect_policy_spec()
    if not isinstance(raw, Mapping):
        raise TypeError("native effect spec must be a mapping")
    return NativeEffectContract.from_spec(
        raw,
        board_size=integer_metric(environment, "boardSize"),
    )


def validate_model_profile(
    model: EffectActorCritic,
    settings: EffectRlSettings,
    backend: BackendApi,
    contract: NativeEffectContract,
) -> None:
    """Reject a checkpoint whose model or encoder differs from the profile."""
    actor = model.actor.architecture
    effect = model.effects.architecture
    encoder = backend.actor_encoder_spec()
    codec = backend.action_codec_spec()
    if not isinstance(encoder, Mapping) or not isinstance(codec, Mapping):
        raise TypeError("native actor specs must be mappings")
    if (
        actor.board_shape[-2:]
        != (
            integer_metric(settings.environment, "boardSize"),
            integer_metric(settings.environment, "boardSize"),
        )
        or actor.unit_shape[1] != settings.unit_limit
        or actor.max_history < integer_metric(settings.environment, "episodeSteps") - 1
        or actor.max_decisions
        < settings.unit_limit + integer_metric(settings.environment, "maxMarketOrdersPerTurn")
        or actor.board_shape[1] != int(encoder["board_channels"])
        or actor.unit_shape[2] != int(encoder["unit_feat"])
        or actor.global_features != int(encoder["global_feat"])
        or actor.action_tokens != len(cast(Sequence[object], codec["keys"]))
        or effect.native_abi_version != contract.version
        or effect.native_spec_version != contract.spec_version
        or effect.board_size != contract.board_size
        or effect.unit_limit != settings.unit_limit
        or effect.maximum_market_orders
        != integer_metric(settings.environment, "maxMarketOrdersPerTurn")
        or effect.context_width != actor.model_width
        or effect.model_width != settings.model.model_width
        or effect.feedforward_width != settings.model.feedforward_width
        or effect.attention_heads != settings.model.attention_heads
        or effect.state_layers != settings.model.state_layers
        or effect.independent_critic != settings.model.independent_critic
        or effect.task_conditioning != settings.model.task_conditioning
        or (effect.task_conditioning and effect.prefix_encoding != settings.model.prefix_encoding)
        or effect.destination_tasks_enabled != settings.model.destination_tasks
    ):
        raise ValueError("effect checkpoint model differs from the resolved profile")


def output_directory(settings: EffectRlSettings, root: Path) -> Path:
    """Resolve an effect run beneath the repository output boundary."""
    output_dir = (root / settings.output_dir).resolve()
    if not output_dir.is_relative_to((root / "outputs").resolve()):
        raise ValueError("effect training output escaped repository outputs/")
    return output_dir


def prepare_output_directory(settings: EffectRlSettings, root: Path) -> Path:
    """Create one immutable run directory."""
    output_dir = output_directory(settings, root)
    if output_dir.exists():
        raise FileExistsError(f"effect training output already exists: {output_dir}")
    output_dir.mkdir(parents=True)
    return output_dir


def configure_optimizer_device(optimizer: Optimizer, device: torch.device) -> None:
    """Restore device-sensitive AdamW state after checkpoint loading."""
    for group in optimizer.param_groups:
        group["fused"] = device.type == "cuda"
    if device.type == "cuda":
        for state in optimizer.state.values():
            step = state.get("step")
            if isinstance(step, torch.Tensor) and step.device != device:
                state["step"] = step.to(device=device)


def stored_training_contract(metadata: Mapping[str, object]) -> dict[str, object]:
    """Remove scheduling-only fields before resume compatibility checks."""
    stored = metadata.get("resolved_config")
    if not isinstance(stored, Mapping):
        raise ValueError("effect checkpoint lacks its resolved config")
    payload = dict(stored)
    for name in (
        "initial_checkpoint",
        "resume_checkpoint",
        "output_dir",
        "updates",
        "checkpoint",
    ):
        payload.pop(name, None)
    return payload


def profile_row(
    update: int,
    rollout: Mapping[str, object],
    learning: Mapping[str, object],
    timing: Mapping[str, float],
    memory: Mapping[str, object] | None,
) -> dict[str, object]:
    """Keep the actionable production phases needed by readiness reports."""
    actor_requested = learning.get("actor_update_requested")
    actor_updated = learning.get("actor_update")
    if not isinstance(actor_requested, bool) or not isinstance(actor_updated, bool):
        raise TypeError("effect actor update profile fields must be boolean")
    return {
        "update": update,
        "actor_update_requested": actor_requested,
        "actor_update": actor_updated,
        "rollout_seconds": numeric_metric(rollout, "elapsed_seconds"),
        "inference_seconds": numeric_metric(rollout, "inference_seconds"),
        "native_observation_seconds": numeric_metric(rollout, "native_observation_seconds"),
        "native_transition_seconds": numeric_metric(rollout, "native_transition_seconds"),
        "collation_seconds": numeric_metric(learning, "input_materialization_seconds"),
        "collation_wait_seconds": numeric_metric(learning, "input_wait_seconds"),
        "learner_seconds": timing["optimization_seconds"],
        "checkpoint_seconds": timing["checkpoint_seconds"],
        "update_seconds": timing["update_seconds"],
        "physical_games_per_second": timing["physical_games_per_second"],
        "graph_capture_seconds": numeric_metric(rollout, "graph_capture_seconds"),
        "cuda_memory": memory,
    }


def steady_profile(
    profiles: Sequence[Mapping[str, object]],
) -> dict[str, object] | None:
    """Average supplied updates while retaining peak observed memory."""
    if not profiles:
        return None
    rows = profiles
    numeric_names = tuple(
        name
        for name, value in rows[0].items()
        if name != "update" and isinstance(value, int | float) and not isinstance(value, bool)
    )
    memory: dict[str, dict[str, int]] = {}
    for row in rows:
        raw_memory = row.get("cuda_memory")
        if not isinstance(raw_memory, Mapping):
            continue
        for device, raw_values in raw_memory.items():
            if not isinstance(raw_values, Mapping):
                continue
            target = memory.setdefault(
                str(device),
                {"peak_allocated_bytes": 0, "peak_reserved_bytes": 0},
            )
            for name in target:
                value = raw_values.get(name)
                if isinstance(value, int) and not isinstance(value, bool):
                    target[name] = max(target[name], value)
    return {
        "updates": len(rows),
        **{
            name: sum(numeric_metric(row, name) for row in rows) / len(rows)
            for name in numeric_names
        },
        "cuda_memory_peak": memory or None,
    }


__all__ = [
    "configure_optimizer_device",
    "integer_metric",
    "native_contract",
    "numeric_metric",
    "output_directory",
    "prepare_output_directory",
    "profile_row",
    "steady_profile",
    "stored_training_contract",
    "validate_model_profile",
]
