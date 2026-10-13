"""Authenticated loading of actor-critic checkpoints as frozen opponents."""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.state import load_causal_actor_state
from kagg_revue.rl.outcome import OutcomeActorCritic
from kagg_revue.rl.pfsp import actor_fingerprint

_SUPPORTED_CHECKPOINT_VERSIONS = frozenset(
    {
        "terminal-wdl-actor-critic-v9",
        "terminal-wdl-actor-critic-v10",
    }
)


@dataclass(frozen=True)
class FrozenActorOpponent:
    """One graph-safe frozen model and its authenticated artifact identity."""

    model: OutcomeActorCritic
    identity: dict[str, object]


def load_frozen_actor_opponent(
    template: OutcomeActorCritic,
    checkpoint: Path,
    expected_sha256: str,
) -> FrozenActorOpponent:
    """Load only an exact compatible actor without consuming training RNG."""
    if not checkpoint.is_file():
        raise FileNotFoundError(f"frozen actor checkpoint does not exist: {checkpoint}")
    actual_sha256 = sha256_file(checkpoint)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "frozen actor checkpoint SHA-256 differs: "
            f"expected {expected_sha256}, found {actual_sha256}"
        )
    raw = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if not isinstance(raw, Mapping):
        raise ValueError("frozen actor checkpoint is not a mapping")
    checkpoint_version = raw.get("checkpoint_version")
    if checkpoint_version not in _SUPPORTED_CHECKPOINT_VERSIONS:
        raise ValueError("frozen actor checkpoint version is unsupported")
    update = raw.get("update")
    if not isinstance(update, int) or isinstance(update, bool) or update < 0:
        raise ValueError("frozen actor checkpoint update is invalid")
    architecture = ActorArchitecture.model_validate(raw.get("architecture"))
    if architecture != template.actor.architecture:
        raise ValueError("frozen actor checkpoint architecture differs from the learner")
    actor_state = raw.get("actor_state")
    if not isinstance(actor_state, Mapping):
        raise ValueError("frozen actor checkpoint lacks actor state")

    # deepcopy preserves the restored learner RNG while giving CUDA Graphs stable,
    # disjoint parameter storage for the immutable opponent.
    model = copy.deepcopy(template)
    removed = load_causal_actor_state(model.actor, cast(Mapping[str, object], actor_state))
    model.eval()
    model.requires_grad_(False)
    return FrozenActorOpponent(
        model=model,
        identity={
            "kind": "frozen_actor_checkpoint",
            "path": str(checkpoint),
            "sha256": actual_sha256,
            "checkpoint_version": checkpoint_version,
            "update": update,
            "actor_state_sha256": actor_fingerprint(model.actor),
            "legacy_auxiliary_tensors_removed": len(removed),
        },
    )


__all__ = ["FrozenActorOpponent", "load_frozen_actor_opponent"]
