"""Complete atomic checkpoints for capability-search PPO."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.policy.capability import CapabilitySelector
from kagg_revue.rl.capabilities.config import (
    CapabilityCheckpointSettings,
    CapabilityRlSettings,
)

CAPABILITY_CHECKPOINT_VERSION = "capability-search-ppo-v1"
_RNG_STATE_VERSION = "capability-rng-v1"
_RNG_KEYS = frozenset(
    {
        "state_version",
        "python_global",
        "python_training",
        "numpy_global",
        "numpy_generator_type",
        "numpy_training",
        "torch_cpu",
        "torch_cuda",
        "torch_generators",
    }
)
_CHECKPOINT_KEYS = frozenset(
    {
        "checkpoint_version",
        "completed_update",
        "target_update",
        "architecture",
        "training_contract",
        "version_contract",
        "source_revision",
        "artifact_identities",
        "model_state",
        "target_state",
        "optimizer_state",
        "rng_state",
    }
)


@dataclass(frozen=True)
class CapabilityResumeState:
    """Authenticated position restored from one complete update boundary."""

    checkpoint: dict[str, object]
    start_update: int
    target_update: int
    source_revision: str


def _numpy_random_state() -> dict[str, object]:
    name, keys, position, has_gauss, cached_gaussian = cast(
        tuple[str, NDArray[np.uint32], int, int, float],
        np.random.get_state(),
    )
    return {
        "name": name,
        "keys": torch.from_numpy(keys.astype(np.uint32, copy=True)),
        "position": position,
        "has_gauss": has_gauss,
        "cached_gaussian": float(cached_gaussian),
    }


def _validated_numpy_random_state(
    value: object,
) -> tuple[str, NDArray[np.uint32], int, int, float]:
    if not isinstance(value, Mapping):
        raise ValueError("capability checkpoint NumPy global RNG state is invalid")
    name = value.get("name")
    keys = value.get("keys")
    position = value.get("position")
    has_gauss = value.get("has_gauss")
    cached_gaussian = value.get("cached_gaussian")
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
        raise ValueError("capability checkpoint NumPy global RNG state is incomplete")
    return (
        name,
        keys.detach().cpu().numpy().astype(np.uint32, copy=True),
        position,
        has_gauss,
        float(cached_gaussian),
    )


def _canonical_devices(devices: tuple[torch.device | str, ...]) -> tuple[torch.device, ...]:
    parsed = tuple(torch.device(device) for device in devices)
    if len(set(map(str, parsed))) != len(parsed):
        raise ValueError("capability RNG devices must be unique")
    if any(device.type != "cuda" or device.index is None for device in parsed):
        raise ValueError("capability RNG device state requires indexed CUDA devices")
    return parsed


def capture_capability_rng_state(
    randomizer: random.Random,
    numpy_generator: np.random.Generator,
    torch_generators: Mapping[str, torch.Generator],
    *,
    devices: tuple[torch.device | str, ...] = (),
) -> dict[str, object]:
    """Capture every global and named stochastic stream used by training."""
    if not torch_generators:
        raise ValueError("capability training requires named torch RNG streams")
    if any(not name or name != name.strip() for name in torch_generators):
        raise ValueError("capability torch RNG stream names must be canonical")
    parsed_devices = _canonical_devices(devices)
    cuda_states = {
        str(device): torch.cuda.get_rng_state(device).detach().cpu() for device in parsed_devices
    }
    return {
        "state_version": _RNG_STATE_VERSION,
        "python_global": random.getstate(),
        "python_training": randomizer.getstate(),
        "numpy_global": _numpy_random_state(),
        "numpy_generator_type": type(numpy_generator.bit_generator).__name__,
        "numpy_training": copy.deepcopy(numpy_generator.bit_generator.state),
        "torch_cpu": torch.get_rng_state().detach().cpu(),
        "torch_cuda": cuda_states,
        "torch_generators": {
            name: generator.get_state().detach().cpu()
            for name, generator in sorted(torch_generators.items())
        },
    }


def restore_capability_rng_state(
    value: object,
    randomizer: random.Random,
    numpy_generator: np.random.Generator,
    torch_generators: Mapping[str, torch.Generator],
    *,
    devices: tuple[torch.device | str, ...] = (),
) -> None:
    """Validate and restore the exact stochastic topology from a checkpoint."""
    if (
        not isinstance(value, Mapping)
        or set(value) != _RNG_KEYS
        or value.get("state_version") != _RNG_STATE_VERSION
    ):
        raise ValueError("capability checkpoint RNG state version is unsupported")
    python_global = value.get("python_global")
    python_training = value.get("python_training")
    torch_cpu = value.get("torch_cpu")
    cuda_states = value.get("torch_cuda")
    named_states = value.get("torch_generators")
    numpy_type = value.get("numpy_generator_type")
    numpy_training = value.get("numpy_training")
    if not isinstance(python_global, tuple) or not isinstance(python_training, tuple):
        raise ValueError("capability checkpoint Python RNG state is invalid")
    if not isinstance(torch_cpu, Tensor):
        raise ValueError("capability checkpoint torch CPU RNG state is invalid")
    if not isinstance(cuda_states, Mapping) or not isinstance(named_states, Mapping):
        raise ValueError("capability checkpoint torch RNG topology is invalid")
    if numpy_type != type(numpy_generator.bit_generator).__name__ or not isinstance(
        numpy_training,
        Mapping,
    ):
        raise ValueError("capability checkpoint NumPy generator differs from runtime")

    parsed_devices = _canonical_devices(devices)
    expected_devices = tuple(map(str, parsed_devices))
    if tuple(cuda_states) != expected_devices:
        raise ValueError("capability checkpoint CUDA RNG devices differ from runtime")
    if tuple(named_states) != tuple(sorted(torch_generators)):
        raise ValueError("capability checkpoint named torch RNG streams differ from runtime")
    if any(not isinstance(cuda_states[name], Tensor) for name in expected_devices):
        raise ValueError("capability checkpoint CUDA RNG state is incomplete")
    if any(not isinstance(named_states[name], Tensor) for name in sorted(torch_generators)):
        raise ValueError("capability checkpoint named torch RNG state is incomplete")

    numpy_global = _validated_numpy_random_state(value.get("numpy_global"))
    try:
        random_probe = random.Random()
        random_probe.setstate(python_global)
        training_probe = random.Random()
        training_probe.setstate(python_training)
        numpy_probe = copy.deepcopy(numpy_generator.bit_generator)
        numpy_probe.state = dict(numpy_training)
        numpy_global_probe = np.random.RandomState()
        numpy_global_probe.set_state(numpy_global)
        torch_probe = torch.Generator(device="cpu")
        torch_probe.set_state(torch_cpu.detach().cpu())
        for device in parsed_devices:
            cuda_probe = torch.Generator(device=device)
            cuda_probe.set_state(cast(Tensor, cuda_states[str(device)]).detach().cpu())
        for name, generator in torch_generators.items():
            state = cast(Tensor, named_states[name]).detach().cpu()
            generator_probe = torch.Generator(device=generator.device)
            generator_probe.set_state(state)
    except (RuntimeError, TypeError, ValueError) as error:
        raise ValueError("capability checkpoint RNG state is malformed") from error

    random.setstate(python_global)
    randomizer.setstate(python_training)
    np.random.set_state(numpy_global)
    numpy_generator.bit_generator.state = dict(numpy_training)
    torch.set_rng_state(torch_cpu.detach().cpu())
    for device in parsed_devices:
        torch.cuda.set_rng_state(cast(Tensor, cuda_states[str(device)]).detach().cpu(), device)
    for name, generator in torch_generators.items():
        generator.set_state(cast(Tensor, named_states[name]).detach().cpu())


def _cpu_tree(value: object) -> object:
    if isinstance(value, Tensor):
        return value.detach().cpu()
    if isinstance(value, Mapping):
        return {key: _cpu_tree(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_cpu_tree(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_cpu_tree(item) for item in value)
    return value


def _module_state(module: CapabilitySelector) -> dict[str, Tensor]:
    return {name: tensor.detach().cpu() for name, tensor in module.state_dict().items()}


def _validated_module_state(
    value: object,
    expected: Mapping[str, Tensor],
    name: str,
) -> dict[str, Tensor]:
    if not isinstance(value, Mapping) or any(
        not isinstance(key, str) or not isinstance(tensor, Tensor) for key, tensor in value.items()
    ):
        raise ValueError(f"capability checkpoint {name} state is invalid")
    state = cast(dict[str, Tensor], dict(value))
    if set(state) != set(expected):
        raise ValueError(f"capability checkpoint {name} parameter names differ")
    for key, expected_tensor in expected.items():
        actual = state[key]
        if actual.shape != expected_tensor.shape or actual.dtype != expected_tensor.dtype:
            raise ValueError(f"capability checkpoint {name} tensor differs: {key}")
    return state


def _validate_source_revision(value: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("capability checkpoint source revision must be a full git SHA")


def _artifact_identities(value: Mapping[str, str]) -> dict[str, str]:
    result = dict(value)
    if not result:
        raise ValueError("capability checkpoint artifact identities cannot be empty")
    for name, identity in result.items():
        if not name or name != name.strip() or not identity or identity != identity.strip():
            raise ValueError("capability checkpoint artifact identities must be canonical")
    return dict(sorted(result.items()))


def build_capability_checkpoint(
    model: CapabilitySelector,
    target: CapabilitySelector,
    optimizer: torch.optim.Optimizer,
    *,
    completed_update: int,
    target_update: int,
    settings: CapabilityRlSettings,
    source_revision: str,
    artifact_identities: Mapping[str, str],
    rng_state: Mapping[str, object],
) -> dict[str, object]:
    """Build a complete, CPU-portable update-boundary endpoint."""
    if completed_update < 0 or completed_update > settings.updates:
        raise ValueError("capability completed update lies outside the run")
    if target_update < 0 or target_update > completed_update:
        raise ValueError("capability target snapshot update is invalid")
    if model.architecture != target.architecture:
        raise ValueError("capability online and target selector architectures differ")
    _validate_source_revision(source_revision)
    artifacts = _artifact_identities(artifact_identities)
    if set(rng_state) != _RNG_KEYS or rng_state.get("state_version") != _RNG_STATE_VERSION:
        raise ValueError("capability checkpoint requires a complete RNG state")
    cuda_states = rng_state.get("torch_cuda")
    named_generators = rng_state.get("torch_generators")
    if not isinstance(cuda_states, Mapping) or tuple(cuda_states) != settings.devices:
        raise ValueError("capability checkpoint RNG devices differ from training devices")
    if not isinstance(named_generators, Mapping) or not named_generators:
        raise ValueError("capability checkpoint lacks named torch RNG streams")
    optimizer_state = optimizer.state_dict()
    if set(optimizer_state) != {"state", "param_groups"}:
        raise ValueError("capability optimizer state is incomplete")
    if not optimizer_state["param_groups"] or (
        completed_update > 0 and not optimizer_state["state"]
    ):
        raise ValueError("capability optimizer has no resumable parameter state")
    return {
        "checkpoint_version": CAPABILITY_CHECKPOINT_VERSION,
        "completed_update": completed_update,
        "target_update": target_update,
        "architecture": model.architecture_json(),
        "training_contract": settings.checkpoint_contract(),
        "version_contract": settings.versions.contract().payload(),
        "source_revision": source_revision,
        "artifact_identities": artifacts,
        "model_state": _module_state(model),
        "target_state": _module_state(target),
        "optimizer_state": _cpu_tree(optimizer_state),
        "rng_state": _cpu_tree(rng_state),
    }


def restore_capability_checkpoint(
    path: Path,
    model: CapabilitySelector,
    target: CapabilitySelector,
    optimizer: torch.optim.Optimizer,
    settings: CapabilityRlSettings,
    *,
    source_revision: str,
    artifact_identities: Mapping[str, str],
    randomizer: random.Random,
    numpy_generator: np.random.Generator,
    torch_generators: Mapping[str, torch.Generator],
    devices: tuple[torch.device | str, ...] | None = None,
) -> CapabilityResumeState:
    """Authenticate and restore model, target, optimizer and all RNG streams."""
    if not path.is_file():
        raise FileNotFoundError(f"capability resume checkpoint does not exist: {path}")
    raw = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(raw, Mapping) or set(raw) != _CHECKPOINT_KEYS:
        raise ValueError("capability checkpoint is not a complete v1 mapping")
    checkpoint = cast(dict[str, object], dict(raw))
    if checkpoint.get("checkpoint_version") != CAPABILITY_CHECKPOINT_VERSION:
        raise ValueError("capability checkpoint version is unsupported")
    completed_update = checkpoint.get("completed_update")
    target_update = checkpoint.get("target_update")
    if (
        not isinstance(completed_update, int)
        or isinstance(completed_update, bool)
        or completed_update < 0
        or completed_update >= settings.updates
    ):
        raise ValueError("capability checkpoint update cannot resume this run")
    if (
        not isinstance(target_update, int)
        or isinstance(target_update, bool)
        or not 0 <= target_update <= completed_update
    ):
        raise ValueError("capability checkpoint target update is invalid")
    _validate_source_revision(source_revision)
    if checkpoint.get("source_revision") != source_revision:
        raise ValueError("capability checkpoint source revision differs")
    if checkpoint.get("artifact_identities") != _artifact_identities(artifact_identities):
        raise ValueError("capability checkpoint artifact identities differ")
    if checkpoint.get("architecture") != model.architecture_json():
        raise ValueError("capability checkpoint model architecture differs")
    if target.architecture != model.architecture:
        raise ValueError("capability target selector architecture differs")
    if checkpoint.get("training_contract") != settings.checkpoint_contract():
        raise ValueError("capability checkpoint training contract differs")
    if checkpoint.get("version_contract") != settings.versions.contract().payload():
        raise ValueError("capability checkpoint proposal/search/executor versions differ")

    model_state = _validated_module_state(
        checkpoint.get("model_state"),
        model.state_dict(),
        "online model",
    )
    target_state = _validated_module_state(
        checkpoint.get("target_state"),
        target.state_dict(),
        "target model",
    )
    optimizer_state = checkpoint.get("optimizer_state")
    if not isinstance(optimizer_state, Mapping) or set(optimizer_state) != {
        "state",
        "param_groups",
    }:
        raise ValueError("capability checkpoint optimizer state is incomplete")

    restore_capability_rng_state(
        checkpoint.get("rng_state"),
        randomizer,
        numpy_generator,
        torch_generators,
        devices=settings.devices if devices is None else devices,
    )
    model.load_state_dict(model_state, strict=True)
    target.load_state_dict(target_state, strict=True)
    optimizer.load_state_dict(cast(dict[str, Any], dict(optimizer_state)))
    digest = sha256_file(path)
    return CapabilityResumeState(
        checkpoint={
            "kind": "capability_search_ppo_checkpoint",
            "path": str(path),
            "sha256": digest,
            "completed_update": completed_update,
            "target_update": target_update,
        },
        start_update=completed_update + 1,
        target_update=target_update,
        source_revision=source_revision,
    )


class CapabilityCheckpointStore:
    """Publish rolling and permanent capability endpoints atomically."""

    def __init__(self, output_dir: Path, settings: CapabilityCheckpointSettings) -> None:
        """Create checkpoint namespaces inside one resolved output directory."""
        self._settings = settings
        self._root = output_dir / "checkpoints"
        self._rolling = self._root / "rolling"
        self._permanent = self._root / "permanent"
        self._rolling.mkdir(parents=True, exist_ok=True)
        self._permanent.mkdir(parents=True, exist_ok=True)

    def due(self, update: int, *, final: bool) -> bool:
        """Return whether an update must publish a recovery endpoint."""
        return (
            final
            or update % self._settings.rolling_interval == 0
            or update % self._settings.permanent_interval == 0
        )

    @staticmethod
    def _checkpoint_name(update: int) -> str:
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

    def publish(
        self,
        update: int,
        payload: Mapping[str, object],
        *,
        final: bool,
    ) -> dict[str, object] | None:
        """Atomically publish a due endpoint and enforce rolling retention."""
        rolling = update % self._settings.rolling_interval == 0
        permanent = update % self._settings.permanent_interval == 0
        if final and not rolling and not permanent:
            rolling = True
        if not rolling and not permanent:
            return None
        rolling_path = self._rolling / self._checkpoint_name(update) if rolling else None
        permanent_path = self._permanent / self._checkpoint_name(update) if permanent else None
        primary = permanent_path if permanent_path is not None else rolling_path
        if primary is None:
            raise RuntimeError("capability checkpoint publication has no destination")
        self._save(primary, payload)
        if rolling_path is not None and rolling_path != primary:
            self._alias(primary, rolling_path)

        rolling_paths = sorted(self._rolling.glob("checkpoint-*.pt"))
        for obsolete in rolling_paths[: -self._settings.rolling_keep]:
            obsolete.unlink()
        latest = self._root / "latest.pt"
        self._alias(primary, latest)
        digest = sha256_file(primary)
        record: dict[str, object] = {
            "path": str(primary),
            "sha256": digest,
            "size_bytes": primary.stat().st_size,
            "update": update,
            "rolling": rolling,
            "permanent": permanent,
            "latest_path": str(latest),
        }
        index_path = self._root / "checkpoint-index.json"
        temporary_index = index_path.with_suffix(".json.tmp")
        index = {
            "schema_version": "capability-checkpoint-index-v1",
            "latest": record,
            "rolling": [str(path) for path in sorted(self._rolling.glob("*.pt"))],
            "permanent": [str(path) for path in sorted(self._permanent.glob("*.pt"))],
            "policy": self._settings.model_dump(mode="json"),
        }
        temporary_index.write_text(
            json.dumps(index, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary_index.replace(index_path)
        return record


def checkpoint_payload_fingerprint(payload: Mapping[str, object]) -> str:
    """Return a diagnostic hash of checkpoint metadata, excluding tensor bytes."""
    metadata = {
        key: value
        for key, value in payload.items()
        if key not in {"model_state", "target_state", "optimizer_state", "rng_state"}
    }
    encoded = json.dumps(metadata, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "CAPABILITY_CHECKPOINT_VERSION",
    "CapabilityCheckpointStore",
    "CapabilityResumeState",
    "build_capability_checkpoint",
    "capture_capability_rng_state",
    "checkpoint_payload_fingerprint",
    "restore_capability_checkpoint",
    "restore_capability_rng_state",
]
