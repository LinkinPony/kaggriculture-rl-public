"""Atomic resumable checkpoints for intent-ledger PPO."""

from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import Tensor
from torch.optim import Optimizer

from kagg_revue.policy.intents.contract import NativeIntentContract
from kagg_revue.policy.intents.model import (
    IntentActorCritic,
    IntentPolicy,
)
from kagg_revue.policy.intents.schema import IntentArchitecture
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet, parameter_count
from kagg_revue.rl.intents.config import IntentCheckpointSettings

CHECKPOINT_VERSION = "canonical-intent-ledger-actor-critic-v2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def capture_rng(
    randomizer: random.Random,
    action_generators: torch.Generator | Sequence[torch.Generator],
    devices: torch.device | Sequence[torch.device],
) -> dict[str, object]:
    """Capture all stochastic streams at an update boundary."""
    generators = (
        (action_generators,)
        if isinstance(action_generators, torch.Generator)
        else tuple(action_generators)
    )
    device_list = (devices,) if isinstance(devices, torch.device) else tuple(devices)
    if not generators or len(generators) != len(device_list):
        raise ValueError("intent RNG streams must align with rollout devices")
    return {
        "python": randomizer.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state(),
        "torch_devices": tuple(
            torch.cuda.get_rng_state(device) if device.type == "cuda" else None
            for device in device_list
        ),
        "action_generators": tuple(generator.get_state() for generator in generators),
        "devices": tuple(str(device) for device in device_list),
        "device_type": device_list[0].type,
    }


def restore_rng(
    payload: object,
    randomizer: random.Random,
    action_generators: torch.Generator | Sequence[torch.Generator],
    devices: torch.device | Sequence[torch.device],
) -> None:
    """Restore a complete stochastic boundary after validation."""
    generators = (
        (action_generators,)
        if isinstance(action_generators, torch.Generator)
        else tuple(action_generators)
    )
    device_list = (devices,) if isinstance(devices, torch.device) else tuple(devices)
    if (
        not generators
        or len(generators) != len(device_list)
        or not isinstance(payload, Mapping)
        or payload.get("device_type") != device_list[0].type
        or payload.get("devices") != tuple(str(device) for device in device_list)
    ):
        raise ValueError("intent checkpoint RNG state uses a different device type")
    python_state = payload.get("python")
    numpy_state = payload.get("numpy")
    cpu_state = payload.get("torch_cpu")
    action_states = payload.get("action_generators")
    device_states = payload.get("torch_devices")
    if (
        not isinstance(python_state, tuple)
        or not isinstance(numpy_state, tuple)
        or not isinstance(cpu_state, Tensor)
        or not isinstance(action_states, tuple)
        or len(action_states) != len(generators)
        or not all(isinstance(state, Tensor) for state in action_states)
        or not isinstance(device_states, tuple)
        or len(device_states) != len(device_list)
        or any(
            device.type == "cuda" and not isinstance(state, Tensor)
            for device, state in zip(device_list, device_states, strict=True)
        )
    ):
        raise ValueError("intent checkpoint RNG state is incomplete")
    randomizer.setstate(python_state)
    np.random.set_state(cast(Any, numpy_state))
    torch.set_rng_state(cpu_state.cpu())
    for generator, state in zip(generators, action_states, strict=True):
        generator.set_state(cast(Tensor, state).cpu())
    for device, state in zip(device_list, device_states, strict=True):
        if device.type == "cuda":
            torch.cuda.set_rng_state(cast(Tensor, state).cpu(), device)


def save_checkpoint(
    path: Path,
    model: IntentActorCritic,
    optimizer: Optimizer,
    *,
    update: int,
    contract: NativeIntentContract,
    resolved_config: Mapping[str, object],
    source_actor: Mapping[str, object],
    source_revision: Mapping[str, object],
    rng_state: Mapping[str, object],
) -> dict[str, object]:
    """Atomically save model, optimizer, ABI, config, source, and RNG."""
    payload: dict[str, object] = {
        "artifact_version": CHECKPOINT_VERSION,
        "update": update,
        "native_intent_abi": contract.version,
        "actor_architecture": model.actor.architecture_json(),
        "intent_architecture": model.intents.architecture.model_dump(mode="json"),
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "resolved_config": dict(resolved_config),
        "source_actor": dict(source_actor),
        "source_revision": dict(source_revision),
        "rng_state": dict(rng_state),
        "parameter_count": parameter_count(model),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".pt.tmp")
    torch.save(payload, temporary)
    temporary.replace(path)
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
        "update": update,
    }


def load_checkpoint(
    path: Path,
    contract: NativeIntentContract,
    device: torch.device,
) -> tuple[IntentActorCritic, dict[str, object]]:
    """Load a checkpoint only when its measured native ABI still matches."""
    raw = torch.load(path, map_location="cpu", weights_only=False)
    if (
        not isinstance(raw, Mapping)
        or raw.get("artifact_version") != CHECKPOINT_VERSION
        or raw.get("native_intent_abi") != contract.version
    ):
        raise ValueError("intent checkpoint identity is unsupported")
    actor_architecture = ActorArchitecture.model_validate(raw["actor_architecture"])
    intent_architecture = IntentArchitecture.model_validate(raw["intent_architecture"])
    if (
        intent_architecture.native_abi_version != contract.version
        or intent_architecture.native_spec_version != contract.spec_version
        or intent_architecture.board_size != contract.board_size
        or intent_architecture.candidate_field_count != len(contract.candidate_fields)
        or intent_architecture.candidate_feature_count != len(contract.candidate_features)
    ):
        raise ValueError("intent checkpoint model shape is stale")
    model = IntentActorCritic(TurnPolicyNet(actor_architecture), IntentPolicy(intent_architecture))
    state = raw.get("model_state")
    if not isinstance(state, Mapping):
        raise ValueError("intent checkpoint lacks model state")
    model.load_state_dict(cast(dict[str, Any], state), strict=True)
    model.to(device)
    metadata = {
        str(key): value
        for key, value in raw.items()
        if key not in {"model_state", "optimizer_state"}
    }
    metadata["optimizer_state"] = raw.get("optimizer_state")
    metadata["checkpoint_identity"] = {
        "path": str(path),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }
    return model, metadata


class IntentCheckpointStore:
    """Publish bounded rolling checkpoints and a latest alias."""

    def __init__(self, output_dir: Path, settings: IntentCheckpointSettings) -> None:
        """Create the rolling namespace under one immutable run directory."""
        self._root = output_dir / "checkpoints"
        self._rolling = self._root / "rolling"
        self._settings = settings
        self._rolling.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _alias(source: Path, destination: Path) -> None:
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.unlink(missing_ok=True)
        try:
            os.link(source, temporary)
        except OSError:
            shutil.copy2(source, temporary)
        temporary.replace(destination)

    def publish(
        self,
        update: int,
        model: IntentActorCritic,
        optimizer: Optimizer,
        *,
        final: bool,
        contract: NativeIntentContract,
        resolved_config: Mapping[str, object],
        source_actor: Mapping[str, object],
        source_revision: Mapping[str, object],
        rng_state: Mapping[str, object],
    ) -> dict[str, object] | None:
        """Save a due update and remove only obsolete rolling siblings."""
        if update % self._settings.interval and not final:
            return None
        path = self._rolling / f"checkpoint-{update:08d}.pt"
        record = save_checkpoint(
            path,
            model,
            optimizer,
            update=update,
            contract=contract,
            resolved_config=resolved_config,
            source_actor=source_actor,
            source_revision=source_revision,
            rng_state=rng_state,
        )
        obsolete = sorted(self._rolling.glob("checkpoint-*.pt"))[: -self._settings.keep]
        for old_path in obsolete:
            old_path.unlink()
        latest = self._root / "latest.pt"
        self._alias(path, latest)
        index = {
            "schema_version": "canonical-intent-checkpoint-index-v1",
            "latest": record,
            "rolling": [str(item) for item in sorted(self._rolling.glob("*.pt"))],
        }
        temporary = self._root / "checkpoint-index.json.tmp"
        temporary.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self._root / "checkpoint-index.json")
        return record


__all__ = [
    "CHECKPOINT_VERSION",
    "IntentCheckpointStore",
    "capture_rng",
    "load_checkpoint",
    "restore_rng",
    "save_checkpoint",
]
