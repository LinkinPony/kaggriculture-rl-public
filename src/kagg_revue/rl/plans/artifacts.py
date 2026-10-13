"""Resolved ABI, source, opponent, and direct-outcome identities for plan PPO."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import numpy as np

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.plans.model import StructuredPlanArchitecture
from kagg_revue.policy.plans.observation import BOARD_SHAPE, UNIT_SHAPE
from kagg_revue.rl.plans.config import StructuredPlanRlSettings
from kagg_revue.rl.plans.rollout import PlanGameResult


def resolve_settings(
    settings: StructuredPlanRlSettings,
    repository_root: Path,
) -> StructuredPlanRlSettings:
    """Resolve artifact/output paths against the repository checkout."""

    def resolve(path: Path) -> Path:
        return path.resolve() if path.is_absolute() else (repository_root / path).resolve()

    return settings.model_copy(
        update={
            "resume_checkpoint": (
                resolve(settings.resume_checkpoint)
                if settings.resume_checkpoint is not None
                else None
            ),
            "initial_actor": (
                resolve(settings.initial_actor)
                if settings.initial_actor is not None
                else None
            ),
            "output_dir": resolve(settings.output_dir),
        }
    )


def validate_native_abi(
    backend: BackendApi,
    settings: StructuredPlanRlSettings,
) -> dict[str, Any]:
    """Require the loaded native plan ABI to equal the resolved profile."""
    spec = cast(dict[str, Any], backend.structured_plan_spec())
    actual = {
        "version": int(spec["version"]),
        "production_line_count": int(spec["production_line_count"]),
        "line_field_count": int(spec["line_field_count"]),
        "global_field_count": int(spec["global_field_count"]),
        "mode_token_count": int(spec["mode_token_count"]),
        "line_operation_token_count": int(spec["line_operation_token_count"]),
        "line_value_token_count": int(spec["line_value_token_count"]),
        "global_operation_token_count": int(spec["global_operation_token_count"]),
        "global_value_token_count": int(spec["global_value_token_count"]),
        "observation_feature_count": int(spec["observation_feature_count"]),
        "journal_feature_count": int(spec["journal_feature_count"]),
        "event_count": int(spec["event_count"]),
        "compiler_abi": str(spec["compiler_abi"]),
    }
    expected = {
        "version": settings.abi.version,
        "production_line_count": settings.abi.production_lines,
        "line_field_count": settings.abi.line_fields,
        "global_field_count": settings.abi.global_fields,
        "mode_token_count": settings.abi.mode_tokens,
        "line_operation_token_count": settings.abi.line_operation_tokens,
        "line_value_token_count": settings.abi.line_value_tokens,
        "global_operation_token_count": settings.abi.global_operation_tokens,
        "global_value_token_count": settings.abi.global_value_tokens,
        "observation_feature_count": settings.abi.observation_features,
        "journal_feature_count": settings.abi.journal_features,
        "event_count": settings.abi.event_features,
        "compiler_abi": settings.versions.executor,
    }
    if actual != expected:
        raise ValueError(f"resolved native structured-plan ABI differs: {actual} != {expected}")
    economic = EconomicStateLayout.from_spec(
        cast(
            Mapping[str, int],
            backend.gpu_policy_state_spec(BOARD_SHAPE[-1], UNIT_SHAPE[1]),
        ),
        board_size=BOARD_SHAPE[-1],
        unit_limit=UNIT_SHAPE[1],
    )
    spec = {
        **spec,
        "rich_policy_observation": {
            "board_shape": BOARD_SHAPE,
            "unit_shape": UNIT_SHAPE,
            "economic_state_version": 3,
            "economic_state_features": economic.width,
        },
    }
    return spec


def artifact_identities(
    backend: BackendApi,
    settings: StructuredPlanRlSettings,
) -> dict[str, str]:
    """Authenticate the same-lineage population contract and native binary."""
    identities = {
        "opponent_population": "direct-wdl-recency-fifo-history-v3",
    }
    if settings.initial_actor is not None:
        identities["initial_actor"] = sha256_file(settings.initial_actor)
    native = cast(Mapping[str, object], backend.identity["native_module"])
    identities["native_extension"] = str(native["sha256"])
    identities["structured_plan_contract"] = settings.versions.contract().fingerprint
    return identities


def architecture(settings: StructuredPlanRlSettings) -> StructuredPlanArchitecture:
    """Build the checkpoint-defining policy architecture from the ABI."""
    return StructuredPlanArchitecture(
        observation_features=settings.abi.observation_features,
        journal_features=settings.abi.journal_features,
        event_features=settings.abi.event_features,
        production_lines=settings.abi.production_lines,
        line_fields=settings.abi.line_fields,
        global_fields=settings.abi.global_fields,
        model_width=settings.model.model_width,
        entity_width=settings.model.entity_width,
        attention_heads=settings.model.attention_heads,
        feedforward_width=settings.model.feedforward_width,
        latent_tokens=settings.model.latent_tokens,
        register_tokens=settings.model.register_tokens,
        scene_layers=settings.model.scene_layers,
        temporal_layers=settings.model.temporal_layers,
        action_layers=settings.model.action_layers,
        max_history=settings.model.max_history,
        strategy_tokens=settings.model.strategy_tokens,
        fact_dropout=settings.model.fact_dropout,
    )


def outcome_metrics(games: Sequence[PlanGameResult]) -> dict[str, object]:
    """Report W/D/L and terminal cash without constructing a proxy score."""
    result: dict[str, object] = {}
    for opponent_id in sorted({game.opponent_id for game in games}):
        rows = [game for game in games if game.opponent_id == opponent_id]
        result[opponent_id] = {
            "games": len(rows),
            "wins": sum(game.outcome > 0 for game in rows),
            "ties": sum(game.outcome == 0 for game in rows),
            "losses": sum(game.outcome < 0 for game in rows),
            "win_rate": sum(game.outcome > 0 for game in rows) / len(rows),
            "mean_terminal_cash": float(np.mean([game.terminal_cash for game in rows])),
            "mean_cash_difference": float(
                np.mean([game.terminal_cash - game.opponent_cash for game in rows])
            ),
        }
    outcomes = [game.outcome for game in games]
    result["overall"] = {
        "games": len(games),
        "wins": sum(outcome > 0 for outcome in outcomes),
        "ties": sum(outcome == 0 for outcome in outcomes),
        "losses": sum(outcome < 0 for outcome in outcomes),
        "win_rate": sum(outcome > 0 for outcome in outcomes) / len(outcomes),
    }
    return result


def prepare_output(settings: StructuredPlanRlSettings, repository_root: Path) -> None:
    """Create a new immutable run directory under repository outputs/."""
    output_root = (repository_root / "outputs").resolve()
    if not settings.output_dir.is_relative_to(output_root):
        raise ValueError("structured-plan output must remain under repository outputs/")
    if settings.output_dir.exists():
        raise FileExistsError(f"structured-plan output already exists: {settings.output_dir}")
    settings.output_dir.mkdir(parents=True)


__all__ = [
    "architecture",
    "artifact_identities",
    "outcome_metrics",
    "prepare_output",
    "resolve_settings",
    "validate_native_abi",
]
