"""Stable extraction of an inference-only actor from live RL training."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.policy.state import load_causal_actor_state
from kagg_revue.rl.pfsp import actor_fingerprint

_SUPPORTED_CHECKPOINTS = frozenset(
    {
        "terminal-wdl-actor-critic-v2",
        "terminal-wdl-actor-critic-v3",
        "terminal-wdl-actor-critic-v4",
        "terminal-wdl-actor-critic-v5",
        "terminal-wdl-actor-critic-v6",
        "terminal-wdl-actor-critic-v7",
        "terminal-wdl-actor-critic-v8",
        "terminal-wdl-actor-critic-v9",
        "terminal-wdl-actor-critic-v10",
    }
)


@dataclass(frozen=True)
class FrozenCheckpoint:
    """One immutable checkpoint selected from an atomically published index."""

    path: Path
    update: int
    size_bytes: int
    sha256: str
    index_sha256: str


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    return cast(Mapping[str, object], value)


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _checkpoint_from_index(run_dir: Path, raw_index: bytes) -> FrozenCheckpoint:
    index = _mapping(json.loads(raw_index), "checkpoint index")
    if index.get("schema_version") != "rl-checkpoint-index-v1":
        raise ValueError("unsupported RL checkpoint index")
    latest = _mapping(index.get("latest"), "latest checkpoint")
    update = _integer(latest.get("update"), "checkpoint update")
    size = _integer(latest.get("size_bytes"), "checkpoint size")
    digest = str(latest.get("sha256", ""))
    if len(digest) != 64:
        raise ValueError("checkpoint index has an invalid SHA-256")
    raw_path = Path(str(latest.get("path", "")))
    path = (raw_path if raw_path.is_absolute() else run_dir / raw_path).resolve()
    checkpoint_root = (run_dir / "checkpoints").resolve()
    if not path.is_relative_to(checkpoint_root):
        raise ValueError("indexed checkpoint resolves outside the training run")
    if not path.is_file():
        raise FileNotFoundError(f"indexed checkpoint does not exist: {path}")
    if path.stat().st_size != size:
        raise ValueError("indexed checkpoint size differs from the published record")
    actual = sha256_file(path)
    if actual != digest:
        raise ValueError("indexed checkpoint SHA-256 differs from the published record")
    return FrozenCheckpoint(
        path=path,
        update=update,
        size_bytes=size,
        sha256=digest,
        index_sha256=hashlib.sha256(raw_index).hexdigest(),
    )


def select_frozen_checkpoint(run_dir: Path, attempts: int = 3) -> FrozenCheckpoint:
    """Select the newest complete checkpoint without racing a live index update."""
    run_dir = run_dir.resolve()
    index_path = run_dir / "checkpoints" / "checkpoint-index.json"
    if not index_path.is_file():
        raise FileNotFoundError(f"RL checkpoint index does not exist: {index_path}")
    for _ in range(attempts):
        before = index_path.read_bytes()
        checkpoint = _checkpoint_from_index(run_dir, before)
        after = index_path.read_bytes()
        if before == after:
            return checkpoint
    raise RuntimeError("RL checkpoint index changed during every stable-read attempt")


def _initial_actor_metadata(run_dir: Path) -> tuple[Path, Mapping[str, object]]:
    settings_path = run_dir / "resolved-settings.json"
    if not settings_path.is_file():
        raise FileNotFoundError(f"RL resolved settings do not exist: {settings_path}")
    resolved = _mapping(json.loads(settings_path.read_bytes()), "resolved settings")
    rl = _mapping(resolved.get("rl"), "resolved RL settings")
    initial_path = Path(str(rl.get("initial_actor", ""))).resolve()
    if not initial_path.is_file():
        raise FileNotFoundError(f"initial actor does not exist: {initial_path}")
    raw = torch.load(initial_path, map_location="cpu", weights_only=True)
    return initial_path, _mapping(raw, "initial actor artifact")


def export_actor_snapshot(
    run_dir: Path,
    destination: Path,
) -> dict[str, object]:
    """Export and authenticate the newest complete actor state as FP32 weights."""
    run_dir = run_dir.resolve()
    checkpoint = select_frozen_checkpoint(run_dir)
    raw = torch.load(checkpoint.path, map_location="cpu", weights_only=True)
    payload = _mapping(raw, "RL checkpoint")
    if payload.get("checkpoint_version") not in _SUPPORTED_CHECKPOINTS:
        raise ValueError("unsupported RL checkpoint version")
    if _integer(payload.get("update"), "checkpoint payload update") != checkpoint.update:
        raise ValueError("RL checkpoint payload update differs from its index")
    architecture_payload = _mapping(payload.get("architecture"), "actor architecture")
    architecture = ActorArchitecture.model_validate(dict(architecture_payload))
    actor_state = payload.get("actor_state")
    if not isinstance(actor_state, dict):
        raise ValueError("RL checkpoint lacks actor state")
    model = TurnPolicyNet(architecture)
    load_causal_actor_state(model, actor_state)

    initial_path, initial = _initial_actor_metadata(run_dir)
    expected_initial_sha256 = str(payload.get("initial_actor_sha256", ""))
    actual_initial_sha256 = sha256_file(initial_path)
    if actual_initial_sha256 != expected_initial_sha256:
        raise ValueError("RL checkpoint and initial actor identities differ")
    initial_architecture = ActorArchitecture.model_validate(
        dict(_mapping(initial.get("architecture"), "initial actor architecture"))
    )
    if initial_architecture != architecture:
        raise ValueError("RL checkpoint architecture differs from its initial actor")
    keys_value = initial.get("action_keys")
    if not isinstance(keys_value, Sequence) or isinstance(keys_value, str | bytes):
        raise TypeError("initial actor action keys must be a sequence")
    action_keys = [str(value) for value in keys_value]
    if len(action_keys) != architecture.action_tokens:
        raise ValueError("initial actor vocabulary differs from the RL architecture")
    economic_feature_version = initial.get("economic_feature_version")
    if economic_feature_version is not None and not isinstance(
        economic_feature_version, str
    ):
        raise TypeError("initial actor economic-feature version is invalid")
    if economic_feature_version != architecture.economic_feature_version:
        raise ValueError(
            "initial actor economic-feature identity differs from its architecture"
        )

    state = {key: value.detach().cpu() for key, value in model.state_dict().items()}
    artifact = {
        "artifact_version": (
            "turn-policy-actor-v6"
            if economic_feature_version is not None
            else "turn-policy-actor-v4"
        ),
        "architecture": model.architecture_json(),
        "actor_encoder_version": str(initial.get("actor_encoder_version", "")),
        "derived_fact_version": initial.get("derived_fact_version"),
        "economic_feature_version": economic_feature_version,
        "action_codec_version": initial.get("action_codec_version"),
        "action_keys": action_keys,
        "model_state": state,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(f"{destination.suffix}.tmp")
    torch.save(artifact, temporary)
    temporary.replace(destination)
    return {
        "artifact_version": artifact["artifact_version"],
        "path": str(destination),
        "sha256": sha256_file(destination),
        "size_bytes": destination.stat().st_size,
        "dtype": "float32",
        "actor_state_sha256": actor_fingerprint(model),
        "checkpoint": {
            "path": str(checkpoint.path),
            "update": checkpoint.update,
            "sha256": checkpoint.sha256,
            "size_bytes": checkpoint.size_bytes,
            "index_sha256": checkpoint.index_sha256,
        },
        "initial_actor": {
            "path": str(initial_path),
            "sha256": actual_initial_sha256,
        },
    }


__all__ = ["FrozenCheckpoint", "export_actor_snapshot", "select_frozen_checkpoint"]
