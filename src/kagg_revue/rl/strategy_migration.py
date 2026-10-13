"""Migrate the incumbent into the compact recurrent-strategy challenger."""

from __future__ import annotations

import json
import random
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf
from torch import Tensor

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.economics import ECONOMIC_FEATURE_VERSION
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.rl.checkpoint import (
    _CHECKPOINT_VERSION,
    _training_contract,
    capture_training_state,
)
from kagg_revue.rl.config import (
    RlSettings,
    StrategyMigrationAppSettings,
    StrategyMigrationSettings,
)
from kagg_revue.rl.distillation import semantic_distill
from kagg_revue.rl.outcome import OutcomeActorCritic
from kagg_revue.rl.train import resolve_rl_paths

_SOURCE_CHECKPOINT_VERSION = "terminal-wdl-actor-critic-v8"
_MIGRATION_VERSION = "strategy-workspace-migration-v1"


def repository_root() -> Path:
    """Return the checkout containing the Hydra profiles."""
    return Path(__file__).resolve().parents[3]


def target_architecture(
    source: ActorArchitecture,
    migration: StrategyMigrationSettings,
    settings: RlSettings,
) -> ActorArchitecture:
    """Resolve the new ABI from actor capacity and the official market slots."""
    market_orders = settings.environment.get("maxMarketOrdersPerTurn")
    if not isinstance(market_orders, int) or isinstance(market_orders, bool):
        raise ValueError("resolved maxMarketOrdersPerTurn must be an integer")
    if source.action_tokens != 91 or source.unit_action_tokens != 68:
        raise ValueError("strategy migration requires the 91-token source actor")
    if source.unit_shape[1:] != (16, 48) or source.max_decisions != 16 + market_orders:
        raise ValueError("strategy migration source has an unexpected unit/decision ABI")
    payload = source.model_dump(mode="python")
    payload.update(
        {
            "unit_shape": (2, migration.unit_limit, 60),
            "max_decisions": migration.unit_limit + market_orders,
            "unit_action_tokens": 44,
            "market_action_tokens": 23,
            "skill_tokens": 0,
            "strategy_tokens": migration.strategy_tokens,
            "strategy_version": "attention-v1",
            "economic_feature_version": ECONOMIC_FEATURE_VERSION,
        }
    )
    return ActorArchitecture.model_validate(payload)


def _tensor_mapping(value: object, name: str) -> dict[str, Tensor]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} is not a tensor mapping")
    result: dict[str, Tensor] = {}
    for key, tensor in value.items():
        if not isinstance(key, str) or not isinstance(tensor, Tensor):
            raise ValueError(f"{name} contains an invalid tensor")
        result[key] = tensor.detach().cpu()
    return result


def _action_row_map(source_keys: Sequence[str], target_keys: Sequence[str]) -> tuple[int, ...]:
    source_by_key = {key: index for index, key in enumerate(source_keys)}
    if len(source_by_key) != len(source_keys):
        raise ValueError("source action keys are not unique")
    try:
        return tuple(source_by_key[key] for key in target_keys)
    except KeyError as error:
        missing = error.args[0]
        raise ValueError(
            f"target semantic action is absent from source: {missing}"
        ) from error


def migrate_actor_weights(
    source_state: Mapping[str, Tensor],
    target: TurnPolicyNet,
    row_map: tuple[int, ...],
) -> dict[str, object]:
    """Copy every semantically retained element and classify all other elements."""
    target_state = {name: value.detach().clone() for name, value in target.state_dict().items()}
    used_source: dict[str, int] = {}
    copied_by_kind: dict[str, int] = {
        "unchanged_tensors": 0,
        "action_rows": 0,
        "unit_input_columns": 0,
        "unit_slot_rows": 0,
        "decision_position_rows": 0,
    }
    copied_by_tensor: dict[str, int] = {}

    def record(name: str, elements: int, kind: str) -> None:
        copied_by_tensor[name] = elements
        used_source[name] = elements
        copied_by_kind[kind] += elements

    special = {
        "scene.action_embedding.weight",
        "action.action_embedding.weight",
        "action.action_head.weight",
        "scene.unit_encoder.network.0.weight",
        "scene.unit_slot_embedding.weight",
        "action.position_embedding.weight",
    }
    for name, destination in target_state.items():
        source = source_state.get(name)
        if name in special or source is None or name.startswith("skills."):
            continue
        if source.shape != destination.shape:
            raise ValueError(f"retained actor tensor changed unexpectedly: {name}")
        destination.copy_(source.to(destination.dtype))
        record(name, destination.numel(), "unchanged_tensors")

    for name in (
        "scene.action_embedding.weight",
        "action.action_head.weight",
    ):
        source = source_state[name]
        destination = target_state[name]
        destination.copy_(source[list(row_map)].to(destination.dtype))
        record(name, destination.numel(), "action_rows")

    source_embedding = source_state["action.action_embedding.weight"]
    destination_embedding = target_state["action.action_embedding.weight"]
    destination_embedding[:-1].copy_(
        source_embedding[list(row_map)].to(destination_embedding.dtype)
    )
    destination_embedding[-1].copy_(source_embedding[-1].to(destination_embedding.dtype))
    record(
        "action.action_embedding.weight",
        destination_embedding.numel(),
        "action_rows",
    )

    unit_name = "scene.unit_encoder.network.0.weight"
    source_unit = source_state[unit_name]
    destination_unit = target_state[unit_name]
    destination_unit.zero_()
    destination_unit[:, : source_unit.shape[1]].copy_(source_unit.to(destination_unit.dtype))
    unit_elements = source_unit.numel()
    record(unit_name, unit_elements, "unit_input_columns")

    for name, kind in (
        ("scene.unit_slot_embedding.weight", "unit_slot_rows"),
        ("action.position_embedding.weight", "decision_position_rows"),
    ):
        source = source_state[name]
        destination = target_state[name]
        destination[: source.shape[0]].copy_(source.to(destination.dtype))
        record(name, source.numel(), kind)

    target.load_state_dict(target_state, strict=True)
    source_elements = sum(tensor.numel() for tensor in source_state.values())
    target_elements = sum(tensor.numel() for tensor in target_state.values())
    copied_elements = sum(copied_by_tensor.values())
    initialized_by_tensor = {
        name: tensor.numel() - copied_by_tensor.get(name, 0)
        for name, tensor in target_state.items()
        if tensor.numel() != copied_by_tensor.get(name, 0)
    }
    deleted_by_tensor = {
        name: tensor.numel() - used_source.get(name, 0)
        for name, tensor in source_state.items()
        if tensor.numel() != used_source.get(name, 0)
    }
    return {
        "source_elements": source_elements,
        "student_elements": target_elements,
        "copied_elements": copied_elements,
        "initialized_elements": target_elements - copied_elements,
        "deleted_source_elements": source_elements - sum(used_source.values()),
        "copied_by_kind": copied_by_kind,
        "copied_by_tensor": copied_by_tensor,
        "initialized_by_tensor": initialized_by_tensor,
        "deleted_by_tensor": deleted_by_tensor,
        "new_unit_columns_zero_initialized": int(
            destination_unit[:, source_unit.shape[1] :].numel()
        ),
    }


def migrate_critic_weights(
    source_state: Mapping[str, Tensor], model: OutcomeActorCritic
) -> dict[str, object]:
    """Copy the old critic and retain zero-output initialization for strategy."""
    target_state = {
        name: value.detach().clone()
        for name, value in model.outcome.state_dict().items()
    }
    copied: dict[str, int] = {}
    for name, source in source_state.items():
        destination = target_state.get(name)
        if destination is None or destination.shape != source.shape:
            raise ValueError(f"source critic tensor cannot be retained: {name}")
        destination.copy_(source.to(destination.dtype))
        copied[name] = source.numel()
    model.outcome.load_state_dict(target_state, strict=True)
    initialized = {
        name: tensor.numel()
        for name, tensor in target_state.items()
        if name not in copied
    }
    return {
        "source_elements": sum(tensor.numel() for tensor in source_state.values()),
        "student_elements": sum(tensor.numel() for tensor in target_state.values()),
        "copied_elements": sum(copied.values()),
        "initialized_elements": sum(initialized.values()),
        "initialized_by_tensor": initialized,
    }


def _save_atomic(payload: Mapping[str, object], destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    torch.save(dict(payload), temporary)
    temporary.replace(destination)


def _training_states(settings: RlSettings, seed: int) -> list[dict[str, object]]:
    states = []
    for rank, raw_device in enumerate(settings.training_devices):
        rank_seed = (seed + rank * 10_000_019) % (2**63 - 1)
        random.seed(rank_seed)
        np.random.seed(rank_seed % (2**32 - 1))
        torch.manual_seed(rank_seed)
        device = torch.device(raw_device)
        if device.type == "cuda":
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA migration profile requires an available GPU")
            torch.cuda.manual_seed(rank_seed)
        states.append(
            capture_training_state(random.Random(rank_seed), None, device)
        )
    return states


def migrate_strategy_checkpoint(
    migration: StrategyMigrationSettings,
    settings: RlSettings,
    root: Path,
) -> dict[str, object]:
    """Create an update-zero actor/critic seed with a fresh optimizer."""
    settings = resolve_rl_paths(settings, root)
    source_checkpoint = (root / migration.source_checkpoint).resolve()
    source_initial_actor = (root / migration.source_initial_actor).resolve()
    destination_dir = (root / migration.destination_dir).resolve()
    output_root = (root / "outputs").resolve()
    if not destination_dir.is_relative_to(output_root):
        raise ValueError("strategy migration output must remain under outputs")
    if destination_dir.exists():
        raise FileExistsError(f"strategy migration output already exists: {destination_dir}")
    if not source_checkpoint.is_file() or not source_initial_actor.is_file():
        raise FileNotFoundError("strategy migration source artifact is absent")

    checkpoint_raw = torch.load(source_checkpoint, map_location="cpu", weights_only=True)
    actor_raw = torch.load(source_initial_actor, map_location="cpu", weights_only=True)
    if not isinstance(checkpoint_raw, Mapping) or not isinstance(actor_raw, Mapping):
        raise ValueError("strategy migration source is not an artifact mapping")
    checkpoint = dict(checkpoint_raw)
    if checkpoint.get("checkpoint_version") != _SOURCE_CHECKPOINT_VERSION:
        raise ValueError("strategy migration requires a complete v8 checkpoint")
    source_architecture = ActorArchitecture.model_validate(checkpoint.get("architecture"))
    initial_architecture = ActorArchitecture.model_validate(actor_raw.get("architecture"))
    if source_architecture != initial_architecture:
        raise ValueError("source checkpoint and initial actor architectures differ")
    source_initial_sha256 = sha256_file(source_initial_actor)
    if checkpoint.get("initial_actor_sha256") != source_initial_sha256:
        raise ValueError("source checkpoint names a different initial actor")
    source_keys_value = actor_raw.get("action_keys")
    if not isinstance(source_keys_value, Sequence) or isinstance(
        source_keys_value, str | bytes
    ):
        raise ValueError("source action keys are invalid")
    source_keys = tuple(str(key) for key in source_keys_value)

    from kagg_revue.native import _revue_native as native

    codec = cast(Mapping[str, object], native.action_codec_spec())
    encoder = cast(Mapping[str, object], native.actor_encoder_spec())
    target_keys_value = codec.get("keys")
    if not isinstance(target_keys_value, Sequence) or isinstance(
        target_keys_value, str | bytes
    ):
        raise ValueError("native target action keys are invalid")
    target_keys = tuple(str(key) for key in target_keys_value)
    architecture = target_architecture(source_architecture, migration, settings)
    if len(target_keys) != architecture.action_tokens:
        raise ValueError("native target vocabulary differs from the migration architecture")
    native_unit_features = encoder["unit_feat"]
    if not isinstance(native_unit_features, int) or isinstance(
        native_unit_features, bool
    ):
        raise ValueError("native target unit width is invalid")
    if native_unit_features != architecture.unit_shape[2]:
        raise ValueError("native target observation differs from the migration architecture")
    row_map = _action_row_map(source_keys, target_keys)

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(migration.seed)
        actor = TurnPolicyNet(architecture)
    source_actor_state = _tensor_mapping(
        checkpoint.get("actor_state"), "source actor state"
    )
    actor_report = migrate_actor_weights(
        source_actor_state,
        actor,
        row_map,
    )
    teacher = TurnPolicyNet(source_architecture)
    teacher.load_state_dict(source_actor_state, strict=True)
    distillation_report = semantic_distill(
        teacher,
        actor,
        source_keys,
        target_keys,
        settings.environment,
        games=migration.distillation_games,
        turns_per_game=migration.distillation_turns,
        learning_rate=migration.distillation_learning_rate,
        seed=migration.seed + 20_000,
        device=torch.device(settings.device),
    )
    del teacher
    if torch.device(settings.device).type == "cuda":
        torch.cuda.empty_cache()
    model = OutcomeActorCritic(actor)
    critic_report = migrate_critic_weights(
        _tensor_mapping(checkpoint.get("outcome_state"), "source critic state"),
        model,
    )

    destination_dir.mkdir(parents=True)
    actor_path = destination_dir / "initial-actor.pt"
    checkpoint_path = destination_dir / "checkpoint.pt"
    actor_payload = {
        "artifact_version": "turn-policy-actor-v6",
        "architecture": actor.architecture_json(),
        "actor_encoder_version": str(encoder["version"]),
        "derived_fact_version": actor_raw.get("derived_fact_version"),
        "economic_feature_version": architecture.economic_feature_version,
        "action_codec_version": str(codec["version"]),
        "action_keys": list(target_keys),
        "model_state": {
            name: (value.detach().cpu().half() if value.is_floating_point() else value.cpu())
            for name, value in actor.state_dict().items()
        },
    }
    _save_atomic(actor_payload, actor_path)
    actor_sha256 = sha256_file(actor_path)
    training_states = _training_states(settings, migration.seed + 1)
    checkpoint_payload = {
        "checkpoint_version": _CHECKPOINT_VERSION,
        "update": 0,
        "architecture": actor.architecture_json(),
        "objective": {
            "discount": settings.discount,
            "gae_lambda": settings.gae_lambda,
        },
        "training_contract": _training_contract(settings),
        "initial_actor_sha256": actor_sha256,
        "actor_state": {
            name: value.detach().cpu() for name, value in actor.state_dict().items()
        },
        "outcome_state": {
            name: value.detach().cpu() for name, value in model.outcome.state_dict().items()
        },
        "optimizer_state": None,
        "fresh_optimizer": True,
        "training_state": training_states[0],
        "distributed_training_states": training_states,
        "distributed_world_size": len(training_states),
        "migration": {
            "kind": _MIGRATION_VERSION,
            "source_update": checkpoint.get("update"),
            "source_checkpoint_sha256": sha256_file(source_checkpoint),
        },
    }
    _save_atomic(checkpoint_payload, checkpoint_path)
    report: dict[str, object] = {
        "schema_version": _MIGRATION_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "source_revision": source_identity(root),
        "source": {
            "checkpoint": str(source_checkpoint),
            "checkpoint_sha256": sha256_file(source_checkpoint),
            "checkpoint_version": checkpoint.get("checkpoint_version"),
            "update": checkpoint.get("update"),
            "initial_actor": str(source_initial_actor),
            "initial_actor_sha256": source_initial_sha256,
        },
        "destination": {
            "initial_actor": str(actor_path),
            "initial_actor_sha256": actor_sha256,
            "checkpoint": str(checkpoint_path),
            "checkpoint_sha256": sha256_file(checkpoint_path),
            "checkpoint_version": _CHECKPOINT_VERSION,
            "architecture": actor.architecture_json(),
        },
        "actor_elements": actor_report,
        "critic_elements": critic_report,
        "optimizer": "fresh AdamW state; no source moments retained",
        "distillation": distillation_report,
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


def _settings(overrides: list[str]) -> StrategyMigrationAppSettings:
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(config_name="migration_config", overrides=overrides)
    value = OmegaConf.to_container(composed, resolve=True)
    return StrategyMigrationAppSettings.model_validate(cast(dict[str, Any], value))


def main() -> None:
    """Run the Hydra-configured migration."""
    import sys

    settings = _settings(sys.argv[1:])
    report = migrate_strategy_checkpoint(
        settings.migration,
        settings.rl,
        repository_root(),
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


__all__ = [
    "migrate_actor_weights",
    "migrate_critic_weights",
    "migrate_strategy_checkpoint",
    "target_architecture",
]
