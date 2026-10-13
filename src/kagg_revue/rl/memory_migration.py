"""Migrate serial strategy attention into fused persistent GRU memory."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import torch
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf
from torch import Tensor

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.policy.state import migrate_optimizer_state
from kagg_revue.rl.checkpoint import _CHECKPOINT_VERSION, _training_contract
from kagg_revue.rl.config import (
    MemoryMigrationAppSettings,
    MemoryMigrationSettings,
    RlSettings,
)
from kagg_revue.rl.outcome import OutcomeActorCritic
from kagg_revue.rl.train import resolve_rl_paths

_MIGRATION_VERSION = "persistent-strategy-memory-migration-v1"


def repository_root() -> Path:
    """Return the checkout containing the Hydra profiles."""
    return Path(__file__).resolve().parents[3]


def target_architecture(source: ActorArchitecture) -> ActorArchitecture:
    """Replace only the authenticated serial workspace implementation."""
    if source.strategy_tokens < 2 or source.strategy_version != "attention-v1":
        raise ValueError("memory migration requires a serial strategy workspace")
    payload = source.model_dump(mode="python")
    payload["strategy_version"] = "gru-v1"
    return ActorArchitecture.model_validate(payload)


def _tensor_mapping(value: object, name: str) -> dict[str, Tensor]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} is not a tensor mapping")
    tensors: dict[str, Tensor] = {}
    for key, tensor in value.items():
        if not isinstance(key, str) or not isinstance(tensor, Tensor):
            raise ValueError(f"{name} contains an invalid tensor")
        tensors[key] = tensor.detach().cpu()
    return tensors


def migrate_actor_weights(
    source_state: Mapping[str, Tensor],
    target: TurnPolicyNet,
) -> dict[str, object]:
    """Reuse every unchanged tensor and retain initialization only for the GRU."""
    target_state = {
        name: value.detach().clone() for name, value in target.state_dict().items()
    }
    copied: dict[str, int] = {}
    initialized: dict[str, int] = {}
    for name, destination in target_state.items():
        source = source_state.get(name)
        if source is None:
            if not name.startswith("strategy.recurrent."):
                raise ValueError(f"memory migration unexpectedly initialized actor tensor: {name}")
            initialized[name] = destination.numel()
            continue
        if source.shape != destination.shape:
            raise ValueError(f"memory migration changed retained actor tensor: {name}")
        destination.copy_(source.to(destination.dtype))
        copied[name] = destination.numel()
    unexpected = sorted(set(source_state) - set(target_state))
    if unexpected:
        raise ValueError(f"memory migration unexpectedly deleted actor tensor: {unexpected[0]}")
    target.load_state_dict(target_state, strict=True)
    return {
        "source_elements": sum(value.numel() for value in source_state.values()),
        "target_elements": sum(value.numel() for value in target_state.values()),
        "copied_elements": sum(copied.values()),
        "initialized_elements": sum(initialized.values()),
        "initialized_by_tensor": initialized,
    }


def _save_atomic(payload: Mapping[str, object], destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    torch.save(dict(payload), temporary)
    temporary.replace(destination)


def _validate_source(
    checkpoint: Mapping[str, object],
    initial_actor: Mapping[str, object],
    initial_actor_path: Path,
) -> ActorArchitecture:
    if checkpoint.get("checkpoint_version") != _CHECKPOINT_VERSION:
        raise ValueError("memory migration requires a complete current-version checkpoint")
    architecture = ActorArchitecture.model_validate(checkpoint.get("architecture"))
    initial_architecture = ActorArchitecture.model_validate(
        initial_actor.get("architecture")
    )
    if architecture != initial_architecture:
        raise ValueError("source checkpoint and initial actor architectures differ")
    if checkpoint.get("initial_actor_sha256") != sha256_file(initial_actor_path):
        raise ValueError("source checkpoint names a different initial actor")
    return architecture


def _artifact_payload(
    source: Mapping[str, object],
    actor: TurnPolicyNet,
) -> dict[str, object]:
    keys = source.get("action_keys")
    if not isinstance(keys, Sequence) or isinstance(keys, str | bytes):
        raise ValueError("source initial actor action keys are invalid")
    if len(keys) != actor.architecture.action_tokens:
        raise ValueError("source vocabulary differs from the migrated architecture")
    return {
        "artifact_version": source.get("artifact_version"),
        "architecture": actor.architecture_json(),
        "actor_encoder_version": source.get("actor_encoder_version"),
        "derived_fact_version": source.get("derived_fact_version"),
        "economic_feature_version": source.get("economic_feature_version"),
        "action_codec_version": source.get("action_codec_version"),
        "action_keys": list(keys),
        "model_state": {
            name: (
                value.detach().cpu().half()
                if value.is_floating_point()
                else value.detach().cpu()
            )
            for name, value in actor.state_dict().items()
        },
    }


def migrate_memory_checkpoint(
    migration: MemoryMigrationSettings,
    settings: RlSettings,
    root: Path,
) -> dict[str, object]:
    """Create an update-preserving GRU branch with retained optimizer moments."""
    settings = resolve_rl_paths(settings, root)
    source_checkpoint = (root / migration.source_checkpoint).resolve()
    source_initial_actor = (root / migration.source_initial_actor).resolve()
    destination_dir = (root / migration.destination_dir).resolve()
    output_root = (root / "outputs").resolve()
    if not destination_dir.is_relative_to(output_root):
        raise ValueError("memory migration output must remain under outputs")
    if destination_dir.exists():
        raise FileExistsError(f"memory migration output already exists: {destination_dir}")
    if not source_checkpoint.is_file() or not source_initial_actor.is_file():
        raise FileNotFoundError("memory migration source artifact is absent")

    checkpoint_raw = torch.load(source_checkpoint, map_location="cpu", weights_only=True)
    actor_raw = torch.load(source_initial_actor, map_location="cpu", weights_only=True)
    if not isinstance(checkpoint_raw, Mapping) or not isinstance(actor_raw, Mapping):
        raise ValueError("memory migration source is not an artifact mapping")
    checkpoint = dict(checkpoint_raw)
    initial_actor = dict(actor_raw)
    source_architecture = _validate_source(
        checkpoint, initial_actor, source_initial_actor
    )
    architecture = target_architecture(source_architecture)

    source_contract = checkpoint.get("training_contract")
    if not isinstance(source_contract, Mapping) or dict(source_contract) != (
        _training_contract(settings)
    ):
        raise ValueError("target training contract differs from the source checkpoint")
    expected_objective = {
        "discount": settings.discount,
        "gae_lambda": settings.gae_lambda,
    }
    if checkpoint.get("objective") != expected_objective:
        raise ValueError("target objective differs from the source checkpoint")
    world_size = len(settings.training_devices)
    if checkpoint.get("distributed_world_size") != world_size:
        raise ValueError("target distributed world differs from the source checkpoint")

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(migration.seed)
        actor = TurnPolicyNet(architecture)
    source_actor_state = _tensor_mapping(
        checkpoint.get("actor_state"), "source actor state"
    )
    actor_report = migrate_actor_weights(source_actor_state, actor)
    model = OutcomeActorCritic(actor)
    outcome_state = _tensor_mapping(
        checkpoint.get("outcome_state"), "source critic state"
    )
    model.outcome.load_state_dict(outcome_state, strict=True)

    optimizer_state = checkpoint.get("optimizer_state")
    if not isinstance(optimizer_state, Mapping):
        raise ValueError("source checkpoint optimizer state is invalid")
    optimizer = torch.optim.AdamW(
        [
            {"params": model.actor.parameters(), "lr": settings.actor_learning_rate},
            {"params": model.outcome.parameters(), "lr": settings.critic_learning_rate},
        ],
        weight_decay=settings.weight_decay,
    )
    target_actor_names = tuple(name for name, _ in model.actor.named_parameters())
    target_outcome_names = tuple(name for name, _ in model.outcome.named_parameters())
    new_actor_names = tuple(
        name for name in target_actor_names if name not in source_actor_state
    )
    migrated_optimizer, removed_slots = migrate_optimizer_state(
        optimizer_state,
        (tuple(source_actor_state), tuple(outcome_state)),
        optimizer,
        (target_actor_names, target_outcome_names),
        allowed_missing_parameter_names=(new_actor_names, ()),
    )
    if removed_slots:
        raise ValueError("memory migration unexpectedly removed optimizer slots")

    destination_dir.mkdir(parents=True)
    actor_path = destination_dir / "initial-actor.pt"
    checkpoint_path = destination_dir / "checkpoint.pt"
    _save_atomic(_artifact_payload(initial_actor, actor), actor_path)
    actor_sha256 = sha256_file(actor_path)
    target_checkpoint = dict(checkpoint)
    target_checkpoint.update(
        {
            "architecture": actor.architecture_json(),
            "initial_actor_sha256": actor_sha256,
            "actor_state": {
                name: value.detach().cpu() for name, value in actor.state_dict().items()
            },
            "outcome_state": {
                name: value.detach().cpu()
                for name, value in model.outcome.state_dict().items()
            },
            "optimizer_state": migrated_optimizer,
            "migration": {
                "kind": _MIGRATION_VERSION,
                "source_checkpoint_sha256": sha256_file(source_checkpoint),
                "source_initial_actor_sha256": sha256_file(source_initial_actor),
                "recurrent_parameter_seed": migration.seed,
                "distillation": False,
            },
        }
    )
    _save_atomic(target_checkpoint, checkpoint_path)

    report: dict[str, object] = {
        "schema_version": _MIGRATION_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "source_revision": source_identity(root),
        "source": {
            "checkpoint": str(source_checkpoint),
            "checkpoint_sha256": sha256_file(source_checkpoint),
            "update": checkpoint.get("update"),
            "initial_actor": str(source_initial_actor),
            "initial_actor_sha256": sha256_file(source_initial_actor),
            "architecture": source_architecture.model_dump(mode="json"),
        },
        "destination": {
            "initial_actor": str(actor_path),
            "initial_actor_sha256": actor_sha256,
            "checkpoint": str(checkpoint_path),
            "checkpoint_sha256": sha256_file(checkpoint_path),
            "architecture": actor.architecture_json(),
        },
        "actor_elements": actor_report,
        "critic_elements_reused": sum(value.numel() for value in outcome_state.values()),
        "optimizer": {
            "retained_parameter_names": len(source_actor_state) + len(outcome_state),
            "new_parameter_names": list(new_actor_names),
            "removed_parameter_names": [],
        },
        "distillation": False,
    }
    (destination_dir / "migration-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    resolved = {
        "migration": migration.model_dump(mode="json"),
        "rl": settings.model_dump(mode="json"),
    }
    (destination_dir / "resolved-migration.json").write_text(
        json.dumps(resolved, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report


def _settings(overrides: list[str]) -> MemoryMigrationAppSettings:
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="memory_migration_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return MemoryMigrationAppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Run the Hydra-configured persistent-memory migration."""
    import sys

    settings = _settings(sys.argv[1:])
    report = migrate_memory_checkpoint(
        settings.migration,
        settings.rl,
        repository_root(),
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


__all__ = [
    "migrate_actor_weights",
    "migrate_memory_checkpoint",
    "target_architecture",
]
