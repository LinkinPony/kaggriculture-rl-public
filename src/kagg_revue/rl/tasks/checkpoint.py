"""Identity-bound checkpoints for the unit-task-tape challenger."""

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
from kagg_revue.policy.tasks.model import UnitTaskPolicy
from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.policy.tasks.schema import TaskTapeArchitecture
from kagg_revue.rl.tasks.config import TaskCheckpointSettings
from kagg_revue.rl.tasks.model import TaskTapeActorCritic

TASK_CHECKPOINT_VERSION = "unit-task-tape-actor-critic-v1"
TASK_RNG_VERSION = "unit-task-tape-rng-v2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def save_task_checkpoint(
    path: Path,
    model: TaskTapeActorCritic,
    optimizer: Optimizer,
    *,
    update: int,
    contract: NativeTaskContract,
    source_actor_identity: Mapping[str, object],
    resolved_config: Mapping[str, object],
    opponent_identities: Mapping[str, object],
    source_identity: Mapping[str, object],
    rng_state: Mapping[str, object],
) -> dict[str, object]:
    """Atomically persist model, optimizer, exact ABI, and experiment identities."""
    if path.suffix != ".pt" or update < 0:
        raise ValueError("unit-task checkpoint needs a .pt path and non-negative update")
    architecture = model.tasks.architecture
    if (
        architecture.native_abi_version != contract.version
        or architecture.catalog_fingerprint != contract.catalog_fingerprint
    ):
        raise ValueError("unit-task model and native compiler identities differ")
    payload: dict[str, object] = {
        "artifact_version": TASK_CHECKPOINT_VERSION,
        "update": update,
        "actor_architecture": model.actor.architecture_json(),
        "task_architecture": architecture.model_dump(mode="json"),
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "native_task_abi": contract.version,
        "catalog_fingerprint": contract.catalog_fingerprint,
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


def load_task_checkpoint(
    path: Path,
    contract: NativeTaskContract,
    device: torch.device,
    *,
    include_optimizer: bool = True,
) -> tuple[TaskTapeActorCritic, dict[str, object]]:
    """Load a checkpoint only after matching its native catalog identity."""
    raw = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(raw, Mapping) or raw.get("artifact_version") != TASK_CHECKPOINT_VERSION:
        raise ValueError("unit-task checkpoint artifact version is unsupported")
    if (
        raw.get("native_task_abi") != contract.version
        or raw.get("catalog_fingerprint") != contract.catalog_fingerprint
    ):
        raise ValueError("unit-task checkpoint and native compiler identities differ")
    actor_architecture = ActorArchitecture.model_validate(raw.get("actor_architecture"))
    task_architecture = TaskTapeArchitecture.model_validate(raw.get("task_architecture"))
    if (
        task_architecture.native_abi_version != contract.version
        or task_architecture.catalog_fingerprint != contract.catalog_fingerprint
    ):
        raise ValueError("unit-task checkpoint architecture has a stale catalog")
    model = TaskTapeActorCritic(
        TurnPolicyNet(actor_architecture),
        UnitTaskPolicy(task_architecture, contract.catalog),
    )
    state = raw.get("model_state")
    if not isinstance(state, Mapping):
        raise ValueError("unit-task checkpoint lacks a model state")
    model.load_state_dict(cast(dict[str, Any], state), strict=True)
    model.to(device)
    metadata = {
        key: value
        for key, value in raw.items()
        if key not in {"model_state", "optimizer_state"}
    }
    if include_optimizer:
        metadata["optimizer_state"] = raw.get("optimizer_state")
    metadata["checkpoint_identity"] = {
        "path": str(path),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }
    return model, cast(dict[str, object], metadata)


def capture_task_rng_state(
    randomizer: random.Random,
    device: torch.device,
) -> dict[str, object]:
    """Capture every stochastic stream used after a complete PPO update."""
    return {
        "version": TASK_RNG_VERSION,
        "python_training": randomizer.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state(),
        "torch_device": (
            torch.cuda.get_rng_state(device) if device.type == "cuda" else None
        ),
        "device": str(device),
    }


def restore_task_rng_state(
    value: object,
    randomizer: random.Random,
    device: torch.device,
) -> None:
    """Validate and restore the unit-task trainer's stochastic topology."""
    expected = {
        "version",
        "python_training",
        "numpy",
        "torch_cpu",
        "torch_device",
        "device",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ValueError("unit-task checkpoint RNG state is incomplete")
    python_state = value.get("python_training")
    numpy_state = value.get("numpy")
    cpu_state = value.get("torch_cpu")
    device_state = value.get("torch_device")
    if (
        value.get("version") != TASK_RNG_VERSION
        or value.get("device") != str(device)
        or not isinstance(python_state, tuple)
        or not isinstance(numpy_state, tuple)
        or not isinstance(cpu_state, torch.Tensor)
        or (device.type == "cuda" and not isinstance(device_state, torch.Tensor))
        or (device.type != "cuda" and device_state is not None)
    ):
        raise ValueError("unit-task checkpoint RNG state differs from this trainer")
    probe = random.Random()
    try:
        probe.setstate(python_state)
        numpy_probe = np.random.RandomState()
        numpy_probe.set_state(cast(Any, numpy_state))
        torch_probe = torch.Generator(device="cpu")
        torch_probe.set_state(cpu_state.detach().cpu())
        if device.type == "cuda":
            device_probe = torch.Generator(device=device)
            device_probe.set_state(cast(torch.Tensor, device_state).detach().cpu())
    except (RuntimeError, TypeError, ValueError) as error:
        raise ValueError("unit-task checkpoint RNG state cannot be restored") from error
    randomizer.setstate(python_state)
    np.random.set_state(cast(Any, numpy_state))
    torch.set_rng_state(cpu_state.detach().cpu())
    if device.type == "cuda":
        torch.cuda.set_rng_state(
            cast(torch.Tensor, device_state).detach().cpu(),
            device,
        )


class TaskCheckpointStore:
    """Publish bounded rolling and permanent unit-task endpoints."""

    def __init__(self, output_dir: Path, settings: TaskCheckpointSettings) -> None:
        """Create checkpoint namespaces inside one immutable run directory."""
        self._settings = settings
        self._root = output_dir / "checkpoints"
        self._rolling = self._root / "rolling"
        self._permanent = self._root / "permanent"
        self._rolling.mkdir(parents=True, exist_ok=True)
        self._permanent.mkdir(parents=True, exist_ok=True)

    def due(self, update: int, *, final: bool) -> bool:
        """Return whether this complete update requires a checkpoint."""
        return (
            final
            or update % self._settings.rolling_interval == 0
            or update % self._settings.permanent_interval == 0
        )

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
        model: TaskTapeActorCritic,
        optimizer: Optimizer,
        *,
        final: bool,
        contract: NativeTaskContract,
        source_actor_identity: Mapping[str, object],
        resolved_config: Mapping[str, object],
        opponent_identities: Mapping[str, object],
        source_identity: Mapping[str, object],
        rng_state: Mapping[str, object],
    ) -> dict[str, object] | None:
        """Atomically save a due endpoint and update bounded aliases."""
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
            raise RuntimeError("unit-task checkpoint has no destination")
        record = save_task_checkpoint(
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
        record.update(
            rolling=rolling,
            permanent=permanent,
            latest_path=str(latest),
        )
        index = {
            "schema_version": "unit-task-checkpoint-index-v1",
            "latest": record,
            "rolling": [str(path) for path in sorted(self._rolling.glob("*.pt"))],
            "permanent": [str(path) for path in sorted(self._permanent.glob("*.pt"))],
            "policy": self._settings.model_dump(mode="json"),
        }
        index_path = self._root / "checkpoint-index.json"
        temporary = index_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(index, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(index_path)
        return record


__all__ = [
    "TASK_CHECKPOINT_VERSION",
    "TASK_RNG_VERSION",
    "TaskCheckpointStore",
    "capture_task_rng_state",
    "load_task_checkpoint",
    "restore_task_rng_state",
    "save_task_checkpoint",
]
