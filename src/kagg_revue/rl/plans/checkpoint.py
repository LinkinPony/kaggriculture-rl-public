"""Atomic update-boundary checkpoints for structured-plan PPO."""

from __future__ import annotations

import json
import os
import random
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import torch
from torch import Tensor

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.policy.plans.model import StructuredPlanPolicy
from kagg_revue.rl.plans.config import PlanCheckpointSettings, StructuredPlanRlSettings
from kagg_revue.rl.plans.health import PlanCollapseGuard
from kagg_revue.rl.plans.population import PlanSelfPlayPopulation

PLAN_CHECKPOINT_VERSION = "structured-portfolio-history-ppo-v10"
PLAN_RNG_VERSION = "structured-portfolio-rng-v3"
_PLAN_RANK_RNG_VERSION = "structured-portfolio-rank-rng-v1"


@dataclass(frozen=True)
class PlanResumeState:
    """Authenticated update position restored from a complete endpoint."""

    checkpoint: dict[str, object]
    start_update: int


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


def capture_plan_rng_state(
    randomizer: random.Random,
    action_generator: torch.Generator,
    device: torch.device,
) -> dict[str, object]:
    """Capture every stochastic stream used after model initialization."""
    if device.type != "cuda" or device.index is None:
        raise ValueError("structured-plan RNG capture requires indexed CUDA")
    return {
        "version": _PLAN_RANK_RNG_VERSION,
        "python_training": randomizer.getstate(),
        "torch_cpu": torch.get_rng_state().detach().cpu(),
        "torch_cuda": torch.cuda.get_rng_state(device).detach().cpu(),
        "action_generator": action_generator.get_state().detach().cpu(),
        "device": str(device),
    }


def combine_plan_rng_states(
    states: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Bind one authenticated stochastic state to every distributed rank."""
    if not states:
        raise ValueError("structured-plan checkpoint needs at least one RNG rank")
    expected = {
        "version",
        "python_training",
        "torch_cpu",
        "torch_cuda",
        "action_generator",
        "device",
    }
    devices: set[str] = set()
    ranks: list[dict[str, object]] = []
    for state in states:
        if set(state) != expected or state.get("version") != _PLAN_RANK_RNG_VERSION:
            raise ValueError("structured-plan rank RNG state is incomplete")
        device = state.get("device")
        if not isinstance(device, str) or not device or device in devices:
            raise ValueError("structured-plan rank RNG devices are invalid")
        devices.add(device)
        ranks.append(dict(state))
    return {
        "version": PLAN_RNG_VERSION,
        "world_size": len(ranks),
        "ranks": tuple(ranks),
    }


def restore_plan_rng_state(
    value: object,
    randomizer: random.Random,
    action_generator: torch.Generator,
    device: torch.device,
    *,
    rank: int,
    devices: Sequence[str],
) -> None:
    """Validate and restore the exact structured-plan stochastic topology."""
    expected = {"version", "world_size", "ranks"}
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ValueError("structured-plan checkpoint RNG state is incomplete")
    raw_ranks = value.get("ranks")
    if (
        value.get("version") != PLAN_RNG_VERSION
        or value.get("world_size") != len(devices)
        or not isinstance(raw_ranks, (list, tuple))
        or len(raw_ranks) != len(devices)
        or rank < 0
        or rank >= len(devices)
        or devices[rank] != str(device)
    ):
        raise ValueError("structured-plan checkpoint RNG topology differs")
    rank_expected = {
        "version",
        "python_training",
        "torch_cpu",
        "torch_cuda",
        "action_generator",
        "device",
    }
    validated_ranks: list[Mapping[str, object]] = []
    for index, raw_rank in enumerate(raw_ranks):
        if (
            not isinstance(raw_rank, Mapping)
            or set(raw_rank) != rank_expected
            or raw_rank.get("version") != _PLAN_RANK_RNG_VERSION
            or raw_rank.get("device") != devices[index]
            or not isinstance(raw_rank.get("python_training"), tuple)
            or any(
                not isinstance(raw_rank.get(name), Tensor)
                for name in ("torch_cpu", "torch_cuda", "action_generator")
            )
        ):
            raise ValueError("structured-plan checkpoint rank RNG state is malformed")
        validated_ranks.append(raw_rank)
    local = validated_ranks[rank]
    python_state = local.get("python_training")
    cpu_state = local.get("torch_cpu")
    cuda_state = local.get("torch_cuda")
    action_state = local.get("action_generator")
    if not isinstance(python_state, tuple) or any(
        not isinstance(item, Tensor) for item in (cpu_state, cuda_state, action_state)
    ):
        raise ValueError("structured-plan checkpoint RNG state is malformed")
    cpu_tensor = cast(Tensor, cpu_state).detach().cpu()
    cuda_tensor = cast(Tensor, cuda_state).detach().cpu()
    action_tensor = cast(Tensor, action_state).detach().cpu()
    try:
        probe = random.Random()
        probe.setstate(python_state)
        torch_probe = torch.Generator(device="cpu")
        torch_probe.set_state(cpu_tensor)
        cuda_probe = torch.Generator(device=device)
        cuda_probe.set_state(cuda_tensor)
        action_probe = torch.Generator(device=device)
        action_probe.set_state(action_tensor)
    except (RuntimeError, TypeError, ValueError) as error:
        raise ValueError("structured-plan checkpoint RNG state cannot be restored") from error
    randomizer.setstate(python_state)
    torch.set_rng_state(cpu_tensor)
    torch.cuda.set_rng_state(cuda_tensor, device)
    action_generator.set_state(action_tensor)


def _model_state(model: StructuredPlanPolicy) -> dict[str, Tensor]:
    return {name: value.detach().cpu() for name, value in model.state_dict().items()}


def _validate_revision(value: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("structured-plan source revision must be a full git SHA")


def _identities(value: Mapping[str, str]) -> dict[str, str]:
    result = dict(sorted(value.items()))
    if not result or any(
        not name or name != name.strip() or not identity or identity != identity.strip()
        for name, identity in result.items()
    ):
        raise ValueError("structured-plan artifact identities must be canonical")
    return result


def build_plan_checkpoint(
    model: StructuredPlanPolicy,
    optimizer: torch.optim.Optimizer,
    *,
    completed_update: int,
    settings: StructuredPlanRlSettings,
    source_revision: str,
    artifact_identities: Mapping[str, str],
    rng_state: Mapping[str, object],
    population_state: Mapping[str, object],
    health_state: Mapping[str, object],
) -> dict[str, object]:
    """Build a CPU-portable checkpoint at one complete update boundary."""
    if completed_update < 0 or completed_update > settings.updates:
        raise ValueError("structured-plan completed update lies outside the run")
    _validate_revision(source_revision)
    if rng_state.get("version") != PLAN_RNG_VERSION:
        raise ValueError("structured-plan checkpoint requires complete RNG state")
    optimizer_state = optimizer.state_dict()
    if set(optimizer_state) != {"state", "param_groups"} or not optimizer_state["param_groups"]:
        raise ValueError("structured-plan optimizer state is incomplete")
    if completed_update > 0 and not optimizer_state["state"]:
        raise ValueError("structured-plan optimizer has no resumable state")
    return {
        "checkpoint_version": PLAN_CHECKPOINT_VERSION,
        "completed_update": completed_update,
        "architecture": model.architecture.payload(),
        "training_contract": settings.checkpoint_contract(),
        "version_contract": settings.versions.contract().payload(),
        "source_revision": source_revision,
        "artifact_identities": _identities(artifact_identities),
        "model_state": _model_state(model),
        "optimizer_state": _cpu_tree(optimizer_state),
        "rng_state": _cpu_tree(rng_state),
        "self_play_population": _cpu_tree(population_state),
        "health": _cpu_tree(health_state),
    }


def _validated_model_state(value: object, model: StructuredPlanPolicy) -> dict[str, Tensor]:
    expected = model.state_dict()
    if not isinstance(value, Mapping) or any(
        not isinstance(name, str) or not isinstance(tensor, Tensor)
        for name, tensor in value.items()
    ):
        raise ValueError("structured-plan checkpoint model state is invalid")
    state = cast(dict[str, Tensor], dict(value))
    if set(state) != set(expected):
        raise ValueError("structured-plan checkpoint parameter names differ")
    for name, tensor in expected.items():
        if state[name].shape != tensor.shape or state[name].dtype != tensor.dtype:
            raise ValueError(f"structured-plan checkpoint tensor differs: {name}")
    return state


def restore_plan_checkpoint(
    path: Path,
    model: StructuredPlanPolicy,
    optimizer: torch.optim.Optimizer,
    population: PlanSelfPlayPopulation,
    health: PlanCollapseGuard,
    settings: StructuredPlanRlSettings,
    *,
    source_revision: str,
    artifact_identities: Mapping[str, str],
    randomizer: random.Random,
    action_generator: torch.Generator,
    device: torch.device,
    distributed_rank: int,
) -> PlanResumeState:
    """Authenticate and restore model, optimizer, update, and RNG streams."""
    if not path.is_file():
        raise FileNotFoundError(f"structured-plan checkpoint does not exist: {path}")
    raw = torch.load(path, map_location="cpu", weights_only=True)
    expected_keys = {
        "checkpoint_version",
        "completed_update",
        "architecture",
        "training_contract",
        "version_contract",
        "source_revision",
        "artifact_identities",
        "model_state",
        "optimizer_state",
        "rng_state",
        "self_play_population",
        "health",
    }
    if not isinstance(raw, Mapping) or set(raw) != expected_keys:
        raise ValueError("structured-plan checkpoint is not a complete endpoint")
    checkpoint = cast(dict[str, object], dict(raw))
    completed = checkpoint.get("completed_update")
    if (
        checkpoint.get("checkpoint_version") != PLAN_CHECKPOINT_VERSION
        or not isinstance(completed, int)
        or isinstance(completed, bool)
        or completed < 0
        or completed >= settings.updates
    ):
        raise ValueError("structured-plan checkpoint cannot resume this run")
    _validate_revision(source_revision)
    if checkpoint.get("source_revision") != source_revision:
        raise ValueError("structured-plan checkpoint source revision differs")
    if checkpoint.get("artifact_identities") != _identities(artifact_identities):
        raise ValueError("structured-plan checkpoint artifact identities differ")
    if checkpoint.get("architecture") != model.architecture.payload():
        raise ValueError("structured-plan checkpoint architecture differs")
    if checkpoint.get("training_contract") != settings.checkpoint_contract():
        raise ValueError("structured-plan checkpoint training contract differs")
    if checkpoint.get("version_contract") != settings.versions.contract().payload():
        raise ValueError("structured-plan checkpoint version contract differs")
    population.load_state_dict(
        checkpoint.get("self_play_population"),
        completed_update=completed,
    )
    health.load_state_dict(checkpoint.get("health"), completed_update=completed)
    model.load_state_dict(_validated_model_state(checkpoint.get("model_state"), model))
    optimizer_state = checkpoint.get("optimizer_state")
    if not isinstance(optimizer_state, Mapping):
        raise ValueError("structured-plan checkpoint optimizer state is invalid")
    optimizer.load_state_dict(dict(optimizer_state))
    restore_plan_rng_state(
        checkpoint.get("rng_state"),
        randomizer,
        action_generator,
        device,
        rank=distributed_rank,
        devices=settings.devices,
    )
    return PlanResumeState(checkpoint=checkpoint, start_update=completed + 1)


class PlanCheckpointStore:
    """Publish bounded rolling and permanent endpoints atomically."""

    def __init__(self, output_dir: Path, settings: PlanCheckpointSettings) -> None:
        """Create checkpoint namespaces inside one immutable run directory."""
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
        payload: Mapping[str, object],
        *,
        final: bool,
    ) -> dict[str, object] | None:
        """Atomically save a due endpoint and enforce rolling retention."""
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
            raise RuntimeError("structured-plan checkpoint has no destination")
        temporary = primary.with_suffix(".pt.tmp")
        torch.save(dict(payload), temporary)
        temporary.replace(primary)
        if rolling_path is not None and rolling_path != primary:
            self._alias(primary, rolling_path)
        for obsolete in sorted(self._rolling.glob("checkpoint-*.pt"))[
            : -self._settings.rolling_keep
        ]:
            obsolete.unlink()
        latest = self._root / "latest.pt"
        self._alias(primary, latest)
        record: dict[str, object] = {
            "path": str(primary),
            "sha256": sha256_file(primary),
            "size_bytes": primary.stat().st_size,
            "update": update,
            "rolling": rolling,
            "permanent": permanent,
            "latest_path": str(latest),
        }
        index = {
            "schema_version": "structured-plan-checkpoint-index-v1",
            "latest": record,
            "rolling": [str(path) for path in sorted(self._rolling.glob("*.pt"))],
            "permanent": [str(path) for path in sorted(self._permanent.glob("*.pt"))],
            "policy": self._settings.model_dump(mode="json"),
        }
        index_path = self._root / "checkpoint-index.json"
        temporary_index = index_path.with_suffix(".json.tmp")
        temporary_index.write_text(
            json.dumps(index, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary_index.replace(index_path)
        return record


__all__ = [
    "PLAN_CHECKPOINT_VERSION",
    "PlanCheckpointStore",
    "PlanResumeState",
    "build_plan_checkpoint",
    "capture_plan_rng_state",
    "combine_plan_rng_states",
    "restore_plan_checkpoint",
    "restore_plan_rng_state",
]
