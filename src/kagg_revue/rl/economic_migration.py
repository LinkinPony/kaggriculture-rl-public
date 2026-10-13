"""Function-preserving actor/critic expansion for economic consequence features."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.economics import (
    CANDIDATE_FEATURES,
    ECONOMIC_FEATURE_VERSION,
    PREFIX_FEATURES,
    QUANTITY_FEATURES,
    TURN_FEATURES,
)
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.policy.runtime import load_actor
from kagg_revue.policy.state import causal_actor_state, migrate_optimizer_state
from kagg_revue.rl.checkpoint import (
    _CHECKPOINT_VERSION,
    _load_outcome_state,
    _semantic_training_contract,
    _training_contract,
)
from kagg_revue.rl.config import RlSettings
from kagg_revue.rl.outcome import OutcomeActorCritic

_SOURCE_CHECKPOINT_VERSION = "terminal-wdl-actor-critic-v7"
_MIGRATION_VERSION = "economic-feature-migration-v1"


def economic_architecture(source: ActorArchitecture) -> ActorArchitecture:
    """Return the source shape with the supported economic feature ABI enabled."""
    if source.economic_feature_version is not None:
        raise ValueError("source actor already has economic consequence features")
    return source.model_copy(
        update={
            "economic_feature_version": ECONOMIC_FEATURE_VERSION,
            "economic_turn_features": TURN_FEATURES,
            "economic_prefix_features": PREFIX_FEATURES,
            "economic_candidate_features": CANDIDATE_FEATURES,
            "economic_quantity_features": QUANTITY_FEATURES,
        }
    )


def _load_actor_expansion(
    model: TurnPolicyNet,
    source: Mapping[str, object],
    *,
    allow_legacy_auxiliaries: bool = False,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Load every retained actor tensor and authenticate only new missing parameters."""
    state, removed = causal_actor_state(source)
    if removed and not allow_legacy_auxiliaries:
        raise ValueError("economic migration source unexpectedly has legacy auxiliaries")
    incompatible = model.load_state_dict(state, strict=False)
    if incompatible.unexpected_keys:
        raise ValueError("economic migration source has unexpected actor tensors")
    missing = tuple(incompatible.missing_keys)
    allowed_prefixes = ("scene.economic_encoder.", "action.economic_")
    if not missing or any(not name.startswith(allowed_prefixes) for name in missing):
        raise ValueError("economic migration actor expansion is not the expected additive change")
    parameter_names = {name for name, _ in model.named_parameters()}
    if not set(missing) <= parameter_names:
        raise ValueError("economic migration unexpectedly initialized actor buffers")
    return (
        tuple(name for name, _ in model.named_parameters() if name in missing),
        removed,
    )


def _actor_payload(
    source_payload: Mapping[str, object],
    model: TurnPolicyNet,
) -> dict[str, object]:
    state = {
        name: (value.detach().cpu().half() if value.is_floating_point() else value.detach().cpu())
        for name, value in model.state_dict().items()
    }
    payload = dict(source_payload)
    payload.update(
        {
            "artifact_version": "turn-policy-actor-v5",
            "architecture": model.architecture_json(),
            "economic_feature_version": ECONOMIC_FEATURE_VERSION,
            "model_state": state,
        }
    )
    return payload


def _save_atomic(payload: Mapping[str, object], destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    torch.save(dict(payload), temporary)
    temporary.replace(destination)


def migrate_economic_checkpoint(
    source_checkpoint: Path,
    source_initial_actor: Path,
    destination_actor: Path,
    destination_checkpoint: Path,
    settings: RlSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Expand a complete v7 endpoint without changing its actor or critic outputs."""
    source_checkpoint = source_checkpoint.resolve()
    source_initial_actor = source_initial_actor.resolve()
    destination_actor = destination_actor.resolve()
    destination_checkpoint = destination_checkpoint.resolve()
    output_root = (repository_root / "outputs").resolve()
    for destination in (destination_actor, destination_checkpoint):
        if not destination.is_relative_to(output_root):
            raise ValueError("economic migration outputs must remain under repository outputs")
    if destination_actor.parent != destination_checkpoint.parent:
        raise ValueError("economic actor and checkpoint must share one migration directory")
    if destination_actor.parent.exists():
        raise FileExistsError(
            f"economic migration output already exists: {destination_actor.parent}"
        )
    if not source_checkpoint.is_file() or not source_initial_actor.is_file():
        raise FileNotFoundError("economic migration source artifact is absent")

    raw_actor = torch.load(source_initial_actor, map_location="cpu", weights_only=True)
    if not isinstance(raw_actor, Mapping):
        raise ValueError("source initial actor is not an artifact mapping")
    old_actor, _, _, _ = load_actor(source_initial_actor, torch.device("cpu"))
    architecture = economic_architecture(old_actor.architecture)
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(settings.seed + 41_009)
        migrated_initial_actor = TurnPolicyNet(architecture)
    initial_missing, initial_removed = _load_actor_expansion(
        migrated_initial_actor,
        cast(Mapping[str, object], raw_actor["model_state"]),
        allow_legacy_auxiliaries=True,
    )

    raw_checkpoint = torch.load(source_checkpoint, map_location="cpu", weights_only=True)
    if not isinstance(raw_checkpoint, dict):
        raise ValueError("source RL checkpoint is not a mapping")
    checkpoint = cast(dict[str, object], raw_checkpoint)
    if checkpoint.get("checkpoint_version") != _SOURCE_CHECKPOINT_VERSION:
        raise ValueError("economic migration requires a complete v7 checkpoint")
    if ActorArchitecture.model_validate(checkpoint.get("architecture")) != old_actor.architecture:
        raise ValueError("source checkpoint and source initial actor architectures differ")
    source_actor_sha256 = sha256_file(source_initial_actor)
    if checkpoint.get("initial_actor_sha256") != source_actor_sha256:
        raise ValueError("source checkpoint names a different initial actor")
    actor_state = checkpoint.get("actor_state")
    outcome_state = checkpoint.get("outcome_state")
    optimizer_state = checkpoint.get("optimizer_state")
    source_contract = checkpoint.get("training_contract")
    if not isinstance(actor_state, Mapping) or not isinstance(outcome_state, Mapping):
        raise ValueError("source checkpoint lacks actor or critic state")
    if not isinstance(optimizer_state, Mapping) or not isinstance(source_contract, Mapping):
        raise ValueError("source checkpoint lacks optimizer or training contract")

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(settings.seed + 41_009)
        actor = TurnPolicyNet(architecture)
    actor_missing, actor_removed = _load_actor_expansion(actor, actor_state)
    if actor_removed:
        raise RuntimeError("economic checkpoint migration retained legacy auxiliaries")
    model = OutcomeActorCritic(actor)
    outcome_missing = _load_outcome_state(
        model,
        outcome_state,
        checkpoint_version=_SOURCE_CHECKPOINT_VERSION,
    )
    optimizer = torch.optim.AdamW(
        [
            {"params": model.actor.parameters(), "lr": settings.actor_learning_rate},
            {"params": model.outcome.parameters(), "lr": settings.critic_learning_rate},
        ],
        weight_decay=settings.weight_decay,
    )
    migrated_optimizer, removed_slots = migrate_optimizer_state(
        optimizer_state,
        (tuple(actor_state), tuple(outcome_state)),
        optimizer,
        (
            tuple(name for name, _ in model.actor.named_parameters()),
            tuple(name for name, _ in model.outcome.named_parameters()),
        ),
        allowed_missing_parameter_names=(actor_missing, outcome_missing),
    )
    if removed_slots:
        raise ValueError("economic migration unexpectedly removed optimizer slots")

    destination_contract = _training_contract(settings)
    if _semantic_training_contract(source_contract) != _semantic_training_contract(
        destination_contract
    ):
        raise ValueError("economic migration settings change training semantics")

    destination_actor.parent.mkdir(parents=True)
    _save_atomic(_actor_payload(raw_actor, migrated_initial_actor), destination_actor)
    destination_actor_sha256 = sha256_file(destination_actor)
    migrated_checkpoint = dict(checkpoint)
    migrated_checkpoint.update(
        {
            "checkpoint_version": _CHECKPOINT_VERSION,
            "architecture": actor.architecture_json(),
            "initial_actor_sha256": destination_actor_sha256,
            "actor_state": {
                name: value.detach().cpu() for name, value in model.actor.state_dict().items()
            },
            "outcome_state": {
                name: value.detach().cpu() for name, value in model.outcome.state_dict().items()
            },
            "optimizer_state": migrated_optimizer,
            "training_contract": destination_contract,
            "migration": {
                "kind": _MIGRATION_VERSION,
                "generated_at": datetime.now(UTC).isoformat(),
                "source_checkpoint": str(source_checkpoint),
                "source_checkpoint_sha256": sha256_file(source_checkpoint),
                "source_initial_actor": str(source_initial_actor),
                "source_initial_actor_sha256": source_actor_sha256,
                "actor_parameters_initialized": len(actor_missing),
                "critic_parameters_initialized": len(outcome_missing),
                "initial_actor_auxiliary_tensors_removed": len(initial_removed),
                "function_preserving_initialization": True,
            },
        }
    )
    _save_atomic(migrated_checkpoint, destination_checkpoint)
    report: dict[str, object] = {
        "schema_version": _MIGRATION_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "source_revision": source_identity(repository_root),
        "source": {
            "checkpoint": str(source_checkpoint),
            "checkpoint_sha256": sha256_file(source_checkpoint),
            "initial_actor": str(source_initial_actor),
            "initial_actor_sha256": source_actor_sha256,
            "update": checkpoint.get("update"),
        },
        "destination": {
            "checkpoint": str(destination_checkpoint),
            "checkpoint_sha256": sha256_file(destination_checkpoint),
            "initial_actor": str(destination_actor),
            "initial_actor_sha256": destination_actor_sha256,
            "checkpoint_version": _CHECKPOINT_VERSION,
        },
        "initialized": {
            "initial_actor_parameters": len(initial_missing),
            "initial_actor_auxiliary_tensors_removed": len(initial_removed),
            "actor_parameters": len(actor_missing),
            "critic_parameters": len(outcome_missing),
        },
    }
    report_path = destination_actor.parent / "migration-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def _settings(
    path: Path,
    destination_actor: Path,
    destination_checkpoint: Path,
    output: Path,
) -> RlSettings:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping) or not isinstance(payload.get("rl"), Mapping):
        raise ValueError("resolved settings file lacks an RL profile")
    values = dict(cast(Mapping[str, Any], payload["rl"]))
    values.update(
        {
            "initial_actor": str(destination_actor),
            "resume_checkpoint": str(destination_checkpoint),
            "output_dir": str(output),
        }
    )
    return RlSettings.model_validate(values)


def main() -> None:
    """Migrate one stopped checkpoint using its resolved training profile."""
    parser = argparse.ArgumentParser(prog="kagg-revue-economic-migration")
    parser.add_argument("--source-checkpoint", type=Path, required=True)
    parser.add_argument("--source-initial-actor", type=Path, required=True)
    parser.add_argument("--resolved-settings", type=Path, required=True)
    parser.add_argument("--destination-dir", type=Path, required=True)
    parser.add_argument("--training-output", type=Path, required=True)
    arguments = parser.parse_args()
    destination_actor = arguments.destination_dir / "initial-actor.pt"
    destination_checkpoint = arguments.destination_dir / "checkpoint.pt"
    settings = _settings(
        arguments.resolved_settings,
        destination_actor,
        destination_checkpoint,
        arguments.training_output,
    )
    root = Path(__file__).resolve().parents[3]
    report = migrate_economic_checkpoint(
        arguments.source_checkpoint,
        arguments.source_initial_actor,
        destination_actor,
        destination_checkpoint,
        settings,
        root,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()


__all__ = ["economic_architecture", "migrate_economic_checkpoint"]
