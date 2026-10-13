"""Identity-bound checkpoints for conditional-program PPO."""

from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch.optim import Optimizer

from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet, parameter_count
from kagg_revue.policy.programs.model import ConditionalProgramPolicy
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.schema import ProgramArchitecture
from kagg_revue.rl.programs.config import ProgramCheckpointSettings
from kagg_revue.rl.programs.model import ProgramActorCritic

PROGRAM_CHECKPOINT_VERSION = "conditional-program-actor-critic-v1"
PROGRAM_RNG_VERSION = "conditional-program-rng-v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def save_program_checkpoint(
    path: Path,
    model: ProgramActorCritic,
    optimizer: Optimizer,
    *,
    update: int,
    contract: NativeProgramContract,
    source_actor_identity: Mapping[str, object],
    resolved_config: Mapping[str, object],
    opponent_identities: Mapping[str, object],
    source_identity: Mapping[str, object],
    rng_state: Mapping[str, object],
) -> dict[str, object]:
    """Atomically persist the model, optimizer, compiler ABI, and provenance."""
    if path.suffix != ".pt" or update < 0:
        raise ValueError("conditional-program checkpoint path or update is invalid")
    architecture = model.programs.architecture
    if architecture.native_abi_version != contract.version:
        raise ValueError("conditional-program checkpoint model and compiler differ")
    payload: dict[str, object] = {
        "artifact_version": PROGRAM_CHECKPOINT_VERSION,
        "update": update,
        "actor_architecture": model.actor.architecture_json(),
        "program_architecture": architecture.model_dump(mode="json"),
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "native_program_abi": contract.version,
        "source_actor_identity": dict(source_actor_identity),
        "resolved_config": dict(resolved_config),
        "opponent_identities": dict(opponent_identities),
        "source_identity": dict(source_identity),
        "rng_state": dict(rng_state),
        "parameter_count": parameter_count(model),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, temporary)
    temporary.replace(path)
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
        "update": update,
    }


def load_program_checkpoint(
    path: Path,
    contract: NativeProgramContract,
    device: torch.device,
) -> tuple[ProgramActorCritic, dict[str, object]]:
    """Load a complete checkpoint only after matching the native ABI."""
    raw = torch.load(path, map_location="cpu", weights_only=False)
    if (
        not isinstance(raw, Mapping)
        or raw.get("artifact_version") != PROGRAM_CHECKPOINT_VERSION
        or raw.get("native_program_abi") != contract.version
    ):
        raise ValueError("conditional-program checkpoint identity is unsupported")
    actor_architecture = ActorArchitecture.model_validate(raw.get("actor_architecture"))
    program_architecture = ProgramArchitecture.model_validate(
        raw.get("program_architecture")
    )
    measured = contract.architecture(
        context_width=program_architecture.context_width,
        model_width=program_architecture.model_width,
        feedforward_width=program_architecture.feedforward_width,
    )
    if measured != program_architecture:
        raise ValueError("conditional-program checkpoint has a stale compiler shape")
    model = ProgramActorCritic(
        TurnPolicyNet(actor_architecture),
        ConditionalProgramPolicy(program_architecture, contract),
    )
    state = raw.get("model_state")
    if not isinstance(state, Mapping):
        raise ValueError("conditional-program checkpoint lacks model state")
    model.load_state_dict(cast(dict[str, Any], state), strict=True)
    model.to(device)
    metadata = {
        key: value
        for key, value in raw.items()
        if key not in {"model_state", "optimizer_state"}
    }
    metadata["optimizer_state"] = raw.get("optimizer_state")
    metadata["checkpoint_identity"] = {
        "path": str(path),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }
    return model, cast(dict[str, object], metadata)


def capture_program_rng_state(
    randomizer: random.Random,
    device: torch.device,
) -> dict[str, object]:
    """Capture every stochastic stream at a complete update boundary."""
    return {
        "version": PROGRAM_RNG_VERSION,
        "python_training": randomizer.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state(),
        "torch_device": (
            torch.cuda.get_rng_state(device) if device.type == "cuda" else None
        ),
        "device": str(device),
    }


def restore_program_rng_state(
    value: object,
    randomizer: random.Random,
    device: torch.device,
) -> None:
    """Validate and restore the checkpointed stochastic topology."""
    expected = {
        "version",
        "python_training",
        "numpy",
        "torch_cpu",
        "torch_device",
        "device",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ValueError("conditional-program checkpoint RNG state is incomplete")
    python_state = value.get("python_training")
    numpy_state = value.get("numpy")
    cpu_state = value.get("torch_cpu")
    device_state = value.get("torch_device")
    try:
        stored_device_type = torch.device(str(value.get("device"))).type
    except RuntimeError as error:
        raise ValueError("conditional-program checkpoint RNG device is invalid") from error
    if (
        value.get("version") != PROGRAM_RNG_VERSION
        or stored_device_type != device.type
        or not isinstance(python_state, tuple)
        or not isinstance(numpy_state, tuple)
        or not isinstance(cpu_state, torch.Tensor)
        or (device.type == "cuda" and not isinstance(device_state, torch.Tensor))
        or (device.type != "cuda" and device_state is not None)
    ):
        raise ValueError("conditional-program checkpoint RNG state differs from trainer")
    randomizer.setstate(python_state)
    np.random.set_state(cast(Any, numpy_state))
    torch.set_rng_state(cpu_state.detach().cpu())
    if device.type == "cuda":
        torch.cuda.set_rng_state(
            cast(torch.Tensor, device_state).detach().cpu(), device
        )


class ProgramCheckpointStore:
    """Publish bounded rolling and permanent conditional-program endpoints."""

    def __init__(self, output_dir: Path, settings: ProgramCheckpointSettings) -> None:
        """Create checkpoint namespaces under one immutable run directory."""
        self._settings = settings
        self._root = output_dir / "checkpoints"
        self._rolling = self._root / "rolling"
        self._permanent = self._root / "permanent"
        self._rolling.mkdir(parents=True, exist_ok=True)
        self._permanent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _name(update: int) -> str:
        return f"checkpoint-{update:08d}.pt"

    @staticmethod
    def _alias(source: Path, destination: Path) -> None:
        temporary = destination.with_name(f"{destination.name}.tmp")
        temporary.unlink(missing_ok=True)
        try:
            os.link(source, temporary)
        except OSError:
            shutil.copy2(source, temporary)
        temporary.replace(destination)

    def publish(
        self,
        update: int,
        model: ProgramActorCritic,
        optimizer: Optimizer,
        *,
        final: bool,
        contract: NativeProgramContract,
        source_actor_identity: Mapping[str, object],
        resolved_config: Mapping[str, object],
        opponent_identities: Mapping[str, object],
        source_identity: Mapping[str, object],
        rng_state: Mapping[str, object],
    ) -> dict[str, object] | None:
        """Save a due checkpoint, bounded rolling set, and latest alias."""
        rolling = update % self._settings.rolling_interval == 0
        permanent = update % self._settings.permanent_interval == 0
        if final and not rolling and not permanent:
            rolling = True
        if not rolling and not permanent:
            return None
        rolling_path = self._rolling / self._name(update) if rolling else None
        permanent_path = self._permanent / self._name(update) if permanent else None
        primary = permanent_path or rolling_path
        if primary is None:
            raise RuntimeError("conditional-program checkpoint has no destination")
        record = save_program_checkpoint(
            primary,
            model,
            optimizer,
            update=update,
            contract=contract,
            source_actor_identity=source_actor_identity,
            resolved_config=resolved_config,
            opponent_identities=opponent_identities,
            source_identity=source_identity,
            rng_state=rng_state,
        )
        if rolling_path is not None and rolling_path != primary:
            self._alias(primary, rolling_path)
        obsolete = sorted(self._rolling.glob("checkpoint-*.pt"))[
            : -self._settings.rolling_keep
        ]
        for path in obsolete:
            path.unlink()
        latest = self._root / "latest.pt"
        self._alias(primary, latest)
        record.update(rolling=rolling, permanent=permanent, latest_path=str(latest))
        index = {
            "schema_version": "conditional-program-checkpoint-index-v1",
            "latest": record,
            "rolling": [str(path) for path in sorted(self._rolling.glob("*.pt"))],
            "permanent": [str(path) for path in sorted(self._permanent.glob("*.pt"))],
            "policy": self._settings.model_dump(mode="json"),
        }
        index_path = self._root / "checkpoint-index.json"
        temporary = index_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(index, indent=2, sort_keys=True), encoding="utf-8"
        )
        temporary.replace(index_path)
        return record


__all__ = [
    "PROGRAM_CHECKPOINT_VERSION",
    "ProgramCheckpointStore",
    "capture_program_rng_state",
    "load_program_checkpoint",
    "restore_program_rng_state",
    "save_program_checkpoint",
]
