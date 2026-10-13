"""Explicit single-rank checkpoint branching into pure self-play DDP."""

from __future__ import annotations

import json
import random
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.runtime import load_actor
from kagg_revue.policy.state import causal_actor_state, migrate_optimizer_state
from kagg_revue.rl.checkpoint import (
    _CHECKPOINT_VERSION,
    _TRAINING_STATE_VERSION,
    _load_outcome_state,
    _training_contract,
)
from kagg_revue.rl.config import RlSettings
from kagg_revue.rl.outcome import OutcomeActorCritic

_SOURCE_CHECKPOINT_VERSION = "terminal-wdl-actor-critic-v4"

_ALLOWED_CONTRACT_CHANGES = frozenset(
    {
        "devices",
        "distributed_world_size",
        "episodes_per_minibatch",
        "pfsp",
        "rollout_actor_streams",
        "rollout_batch_games",
        "rollout_cpu_workers",
        "rollout_gpu_memory_fraction",
        "rollout_host_memory_limit_gib",
        "skill_effect_weight",
        "skill_recognition_weight",
    }
)


def _numpy_state(seed: int) -> dict[str, object]:
    randomizer = np.random.RandomState(seed % (2**32 - 1))
    name, keys, position, has_gauss, cached_gaussian = cast(
        tuple[str, NDArray[np.uint32], int, int, float],
        randomizer.get_state(),
    )
    return {
        "name": name,
        "keys": torch.from_numpy(keys.copy()),
        "position": position,
        "has_gauss": has_gauss,
        "cached_gaussian": cached_gaussian,
    }


def _seeded_training_state(seed: int, device: torch.device) -> dict[str, object]:
    """Create one independent continuation stream without mutating process RNGs."""
    if device.type != "cuda" or device.index is None:
        raise ValueError("distributed checkpoint migration requires indexed CUDA devices")
    python_randomizer = random.Random(seed)
    optimization_randomizer = random.Random(seed)
    cpu_generator = torch.Generator(device="cpu").manual_seed(seed)
    device_generator = torch.Generator(device=device).manual_seed(seed)
    return {
        "state_version": _TRAINING_STATE_VERSION,
        "python_random_state": python_randomizer.getstate(),
        "numpy_random_state": _numpy_state(seed),
        "torch_cpu_random_state": cpu_generator.get_state(),
        "torch_device_random_state": device_generator.get_state(),
        "optimization_random_state": optimization_randomizer.getstate(),
        "pfsp_state": None,
    }


def _contract_changes(
    source: Mapping[str, object], destination: Mapping[str, object]
) -> dict[str, dict[str, object]]:
    keys = set(source) | set(destination)
    return {
        key: {"source": source.get(key), "destination": destination.get(key)}
        for key in sorted(keys)
        if source.get(key) != destination.get(key)
    }


def migrate_single_rank_checkpoint(
    source: Path,
    destination: Path,
    settings: RlSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Branch one complete v4 endpoint into the current authenticated DDP endpoint."""
    source = source.resolve()
    destination = destination.resolve()
    output_root = (repository_root / "outputs").resolve()
    if not destination.is_relative_to(output_root):
        raise ValueError("migrated RL checkpoint must remain under repository outputs")
    if not source.is_file():
        raise FileNotFoundError(f"source RL checkpoint does not exist: {source}")
    if destination.parent.exists():
        raise FileExistsError(f"checkpoint migration output already exists: {destination.parent}")
    if settings.pfsp.enabled or settings.opponents != ("self_play",):
        raise ValueError("distributed checkpoint branch must use pure self-play")
    if len(settings.training_devices) != 2:
        raise ValueError("single-rank checkpoint migration currently requires two CUDA ranks")

    raw = torch.load(source, map_location="cpu", weights_only=True)
    if not isinstance(raw, dict):
        raise ValueError("source RL checkpoint is not a mapping")
    checkpoint = cast(dict[str, object], raw)
    if checkpoint.get("checkpoint_version") != _SOURCE_CHECKPOINT_VERSION:
        raise ValueError("source RL checkpoint is not a complete single-rank v4 endpoint")
    update = checkpoint.get("update")
    if not isinstance(update, int) or isinstance(update, bool) or update < 1:
        raise ValueError("source RL checkpoint update is invalid")
    source_contract = checkpoint.get("training_contract")
    if not isinstance(source_contract, Mapping):
        raise ValueError("source RL checkpoint training contract is invalid")
    source_pfsp = source_contract.get("pfsp")
    if not isinstance(source_pfsp, Mapping) or source_pfsp.get("enabled") is not True:
        raise ValueError("source RL checkpoint does not contain the expected PFSP branch")

    initial_actor_sha256 = sha256_file(settings.initial_actor)
    if checkpoint.get("initial_actor_sha256") != initial_actor_sha256:
        raise ValueError("source checkpoint and configured initial actor differ")
    expected_objective = {
        "discount": settings.discount,
        "gae_lambda": settings.gae_lambda,
    }
    source_objective = checkpoint.get("objective")
    if not isinstance(source_objective, Mapping):
        raise ValueError("source checkpoint objective is invalid")
    normalized_objective = dict(source_objective)
    normalized_objective.pop("skill_recognition_weight", None)
    normalized_objective.pop("skill_effect_weight", None)
    if normalized_objective != expected_objective:
        raise ValueError("source checkpoint and configured objective differ")

    actor_state = checkpoint.get("actor_state")
    outcome_state = checkpoint.get("outcome_state")
    optimizer_state = checkpoint.get("optimizer_state")
    if not isinstance(actor_state, Mapping) or not isinstance(outcome_state, Mapping):
        raise ValueError("source checkpoint lacks actor or critic state")
    if not isinstance(optimizer_state, Mapping):
        raise ValueError("source checkpoint optimizer state is invalid")
    actor, _, _, _ = load_actor(settings.initial_actor, torch.device("cpu"))
    causal_state, removed = causal_actor_state(actor_state)
    actor.load_state_dict(causal_state, strict=True)
    model = OutcomeActorCritic(actor)
    initialized_outcome = _load_outcome_state(
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
        allowed_missing_parameter_names=((), initialized_outcome),
    )
    if set(removed_slots) != set(removed):
        raise ValueError("source optimizer and actor auxiliary tensors differ")

    destination_contract = _training_contract(settings)
    changes = _contract_changes(source_contract, destination_contract)
    unsupported = set(changes) - _ALLOWED_CONTRACT_CHANGES
    if unsupported:
        raise ValueError(
            "checkpoint migration changes unsupported training semantics: "
            + ", ".join(sorted(unsupported))
        )
    source_state = checkpoint.get("training_state")
    if not isinstance(source_state, Mapping) or source_state.get("state_version") != (
        _TRAINING_STATE_VERSION
    ):
        raise ValueError("source checkpoint training state is invalid")
    primary_state = dict(source_state)
    primary_state["pfsp_state"] = None
    devices = tuple(torch.device(value) for value in settings.training_devices)
    secondary_seed = (settings.seed + 10_000_019 + update * 1_000_003) % (2**63 - 1)
    training_states = [
        primary_state,
        _seeded_training_state(secondary_seed, devices[1]),
    ]
    source_sha256 = sha256_file(source)
    migrated = dict(checkpoint)
    migrated.update(
        {
            "checkpoint_version": _CHECKPOINT_VERSION,
            "architecture": actor.architecture_json(),
            "objective": expected_objective,
            "actor_state": causal_state,
            "outcome_state": {
                key: value.detach().cpu() for key, value in model.outcome.state_dict().items()
            },
            "optimizer_state": migrated_optimizer,
            "training_contract": destination_contract,
            "training_state": training_states[0],
            "distributed_training_states": training_states,
            "distributed_world_size": len(training_states),
            "migration": {
                "kind": "single_rank_pfsp_to_pure_selfplay_ddp",
                "generated_at": datetime.now(UTC).isoformat(),
                "source_path": str(source),
                "source_sha256": source_sha256,
                "source_checkpoint_version": _SOURCE_CHECKPOINT_VERSION,
                "source_update": update,
                "legacy_auxiliary_tensors_removed": len(removed),
                "critic_parameters_initialized": len(initialized_outcome),
                "contract_changes": changes,
                "rank_rng": [
                    {"rank": 0, "kind": "restored_source_state_without_pfsp"},
                    {
                        "rank": 1,
                        "kind": "deterministic_continuation_seed",
                        "seed": secondary_seed,
                    },
                ],
            },
        }
    )

    destination.parent.mkdir(parents=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    torch.save(migrated, temporary)
    temporary.replace(destination)
    report: dict[str, object] = {
        "schema_version": "rl-checkpoint-migration-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_revision": source_identity(repository_root),
        "source": {
            "path": str(source),
            "sha256": source_sha256,
            "checkpoint_version": _SOURCE_CHECKPOINT_VERSION,
            "update": update,
        },
        "destination": {
            "path": str(destination),
            "sha256": sha256_file(destination),
            "size_bytes": destination.stat().st_size,
            "checkpoint_version": _CHECKPOINT_VERSION,
            "distributed_world_size": len(training_states),
        },
        "contract_changes": changes,
        "rank_rng": cast(dict[str, object], migrated["migration"])["rank_rng"],
    }
    report_path = destination.parent / "migration-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


__all__ = ["migrate_single_rank_checkpoint"]
