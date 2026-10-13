"""Direct outcome reporting for atomic-effect opponent populations."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np

from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.registry import trusted_runtime_identity
from kagg_revue.rl.effects.rollout import EffectGameResult


def effect_opponent_identities(
    backend: BackendApi,
    repository_root: Path,
    weights: Mapping[str, float],
    public_agent_manifest: Path | None,
) -> dict[str, object]:
    """Authenticate every frozen native opponent used by a training lineage."""
    external = tuple(name for name in weights if name != "self_play")
    records: Mapping[str, Any] = {}
    if external:
        if public_agent_manifest is None:
            raise ValueError("effect native opponents require a public agent manifest")
        manifest_path = repository_root / public_agent_manifest
        records = backend.load_public_agent_manifest(manifest_path).by_id()
    identities: dict[str, object] = {}
    for opponent_id in weights:
        if opponent_id == "self_play":
            identities[opponent_id] = {
                "kind": "self_play",
                "identity": "current_live_atomic_effect_policy",
                "training_perspectives_per_seed": 2,
            }
            continue
        record = records.get(opponent_id)
        native_identity = None if record is None else trusted_runtime_identity(record)
        if (
            record is None
            or native_identity is None
            or opponent_id not in backend.native_opponent_batch_steps
        ):
            raise KeyError(f"effect PPO requires an authenticated native opponent: {opponent_id}")
        identities[opponent_id] = {
            "kind": "public_notebook_native",
            "notebook_ref": record.notebook_ref,
            "notebook_id": record.notebook_id,
            "artifact_sha256": record.sha256,
            "native_runtime": native_identity,
        }
    return identities


def effect_outcome_metrics(
    games: Sequence[EffectGameResult],
) -> dict[str, dict[str, int | float]]:
    """Summarize W/L/T and terminal cash without a proxy score."""
    if not games:
        raise ValueError("effect outcome panel cannot be empty")
    grouped: dict[str, list[EffectGameResult]] = {}
    for game in games:
        grouped.setdefault(game.opponent_id, []).append(game)
    result: dict[str, dict[str, int | float]] = {}
    for opponent_id in sorted(grouped, key=lambda value: (value != "self_play", value)):
        group = grouped[opponent_id]
        outcomes = np.asarray([game.outcome for game in group], dtype=np.int64)
        cash = np.asarray([game.terminal_cash for game in group], dtype=np.float64)
        opponent_cash = np.asarray([game.opponent_cash for game in group], dtype=np.float64)
        count = len(group)
        result[opponent_id] = {
            "games": count,
            "seeds": len({game.seed for game in group}),
            "training_trajectories": count,
            "training_fraction": count / len(games),
            "wins": int(np.count_nonzero(outcomes > 0)),
            "ties": int(np.count_nonzero(outcomes == 0)),
            "losses": int(np.count_nonzero(outcomes < 0)),
            "win_rate": float(np.count_nonzero(outcomes > 0) / count),
            "tie_rate": float(np.count_nonzero(outcomes == 0) / count),
            "loss_rate": float(np.count_nonzero(outcomes < 0) / count),
            "mean_terminal_cash": float(cash.mean()),
            "mean_opponent_cash": float(opponent_cash.mean()),
            "mean_cash_difference": float((cash - opponent_cash).mean()),
        }
    return result


__all__ = ["effect_opponent_identities", "effect_outcome_metrics"]
