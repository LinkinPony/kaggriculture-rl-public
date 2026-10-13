"""Official-rule paired evaluation of behavior-cloned actors."""

from __future__ import annotations

import json
import statistics
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

import numpy as np
import torch

from kagg_revue.bc.config import ExperimentSettings
from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.runtime import BaselineAgent, NumericAction, TurnPolicyAgent


class _Agent(Protocol):
    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return one official request."""


class MatchSettings(Protocol):
    """Configuration surface needed by official-rule match execution."""

    @property
    def environment(self) -> dict[str, object]:
        """Resolved official environment overrides."""

    @property
    def act_timeout_seconds(self) -> float:
        """Free time available for each action call."""

    @property
    def remaining_overage_seconds(self) -> float:
        """Cumulative action-time overage budget."""


AgentFactory = Callable[[Mapping[str, Any]], _Agent]


def _as_int(value: object) -> int:
    if not isinstance(value, int | float):
        raise TypeError("match value is not numeric")
    return int(value)


def _as_float(value: object) -> float:
    if not isinstance(value, int | float):
        raise TypeError("match value is not numeric")
    return float(value)


def _pass_action(observation: Mapping[str, Any]) -> dict[str, Any]:
    farm = observation["farms"][int(observation["player"])]
    return {
        "farmer": ["PASS"],
        "hands": [["PASS"] for _ in farm["hands"]],
        "market": [],
    }


def _step_actions(engine: Any, actions: Sequence[dict[str, Any] | NumericAction]) -> None:
    numeric_seats = [
        seat for seat, action in enumerate(actions) if isinstance(action, NumericAction)
    ]
    if len(numeric_seats) == 2:
        width = max(
            action.decision_count for action in actions if isinstance(action, NumericAction)
        )
        tokens = np.zeros((2, width), dtype=np.int64)
        quantities = np.zeros_like(tokens)
        decisions = np.zeros(2, dtype=np.int64)
        units = np.zeros(2, dtype=np.int64)
        for seat, raw in enumerate(actions):
            action = cast(NumericAction, raw)
            tokens[seat, : action.decision_count] = action.tokens
            quantities[seat, : action.decision_count] = action.quantities
            decisions[seat] = action.decision_count
            units[seat] = action.unit_count
        engine.step_numeric(tokens, quantities, decisions, units)
        return
    if len(numeric_seats) == 1:
        seat = numeric_seats[0]
        numeric = cast(NumericAction, actions[seat])
        engine.step_mixed_numeric(
            seat,
            numeric.tokens,
            numeric.quantities,
            numeric.decision_count,
            numeric.unit_count,
            actions[1 - seat],
        )
        return
    engine.step(actions[0], actions[1])


def run_game(
    backend: BackendApi,
    candidate_id: str,
    candidate_factory: AgentFactory,
    opponent_id: str,
    opponent_factory: AgentFactory,
    seed: int,
    candidate_seat: int,
    settings: MatchSettings,
) -> dict[str, object]:
    """Run one complete official-rule game with timeout accounting."""
    engine = backend.engine(seed=seed, configuration=dict(settings.environment))
    configuration = dict(engine.configuration)
    runtimes = [
        (
            candidate_factory(configuration)
            if seat == candidate_seat
            else opponent_factory(configuration)
        )
        for seat in (0, 1)
    ]
    errors: list[str | None] = [None, None]
    overage = [settings.remaining_overage_seconds, settings.remaining_overage_seconds]
    total_seconds = [0.0, 0.0]
    max_seconds = [0.0, 0.0]
    transitions = 0
    while not bool(engine.done):
        actions: list[dict[str, Any] | NumericAction] = []
        for seat in (0, 1):
            if errors[seat] is not None:
                actions.append(_pass_action(engine.observation(seat)))
                continue
            runtime = runtimes[seat]
            started = time.perf_counter()
            try:
                native = getattr(runtime, "act_native", None)
                action: dict[str, Any] | NumericAction = (
                    native(engine, seat)
                    if callable(native)
                    else runtime.act(engine.observation(seat))
                )
            except Exception as error:  # Notebook artifacts are an untyped boundary.
                errors[seat] = f"{type(error).__name__}: {error}"
                action = _pass_action(engine.observation(seat))
            elapsed = time.perf_counter() - started
            total_seconds[seat] += elapsed
            max_seconds[seat] = max(max_seconds[seat], elapsed)
            overage[seat] -= max(0.0, elapsed - settings.act_timeout_seconds)
            if overage[seat] < 0.0 and errors[seat] is None:
                errors[seat] = "ActionTimeout: remaining overage exhausted"
                action = _pass_action(engine.observation(seat))
            actions.append(action)
        _step_actions(engine, actions)
        transitions += 1
    candidate_money = float(engine.money(candidate_seat))
    opponent_money = float(engine.money(1 - candidate_seat))
    candidate_error = errors[candidate_seat]
    opponent_error = errors[1 - candidate_seat]
    if candidate_error is not None and opponent_error is None:
        outcome = -1
    elif opponent_error is not None and candidate_error is None:
        outcome = 1
    elif candidate_error is not None:
        outcome = 0
    else:
        outcome = int(candidate_money > opponent_money) - int(candidate_money < opponent_money)
    diagnostics_provider = getattr(runtimes[candidate_seat], "diagnostics", None)
    diagnostics = diagnostics_provider() if callable(diagnostics_provider) else None
    return {
        "candidate_id": candidate_id,
        "opponent_id": opponent_id,
        "seed": seed,
        "candidate_seat": candidate_seat,
        "candidate_money": candidate_money,
        "opponent_money": opponent_money,
        "margin": candidate_money - opponent_money,
        "outcome": outcome,
        "candidate_error": candidate_error,
        "opponent_error": opponent_error,
        "candidate_total_seconds": total_seconds[candidate_seat],
        "candidate_max_seconds": max_seconds[candidate_seat],
        "candidate_remaining_overage_seconds": overage[candidate_seat],
        "opponent_total_seconds": total_seconds[1 - candidate_seat],
        "opponent_max_seconds": max_seconds[1 - candidate_seat],
        "diagnostics": diagnostics,
        "done": bool(engine.done),
        "transitions": transitions,
    }


def summarize_games(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Summarize one identically configured complete-match panel."""
    if not rows:
        raise ValueError("cannot summarize an empty match panel")
    return {
        "games": len(rows),
        "wins": sum(_as_int(row["outcome"]) > 0 for row in rows),
        "ties": sum(_as_int(row["outcome"]) == 0 for row in rows),
        "losses": sum(_as_int(row["outcome"]) < 0 for row in rows),
        "mean_terminal_cash": statistics.fmean(_as_float(row["candidate_money"]) for row in rows),
        "mean_cash_difference": statistics.fmean(_as_float(row["margin"]) for row in rows),
        "errors": sum(row["candidate_error"] is not None for row in rows),
        "max_act_seconds": max(_as_float(row["candidate_max_seconds"]) for row in rows),
        "minimum_remaining_overage_seconds": min(
            _as_float(row["candidate_remaining_overage_seconds"]) for row in rows
        ),
    }


def run_paired_panel(
    backend: BackendApi,
    candidate_id: str,
    candidate_factory: AgentFactory,
    opponent_id: str,
    opponent_factory: AgentFactory,
    seeds: Sequence[int],
    settings: MatchSettings,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Run common seeds with the candidate in both seats."""
    rows = [
        run_game(
            backend,
            candidate_id,
            candidate_factory,
            opponent_id,
            opponent_factory,
            seed,
            seat,
            settings,
        )
        for seed in seeds
        for seat in (0, 1)
    ]
    return rows, summarize_games(rows)


def _public_factories(
    backend: BackendApi, settings: ExperimentSettings
) -> tuple[dict[str, AgentFactory], dict[str, dict[str, object]]]:
    manifest = backend.load_public_agent_manifest(settings.public_agent_manifest)
    records = manifest.by_id()
    factories: dict[str, AgentFactory] = {}
    identities: dict[str, dict[str, object]] = {}
    for opponent_id in settings.confirmation_opponents:
        if opponent_id not in records:
            raise KeyError(f"public opponent is absent from the manifest: {opponent_id}")
        record = records[opponent_id]

        def factory(configuration: Mapping[str, Any], record: Any = record) -> _Agent:
            return cast(
                _Agent,
                backend.public_agent_runtime(record, backend.repository_root, configuration),
            )

        factories[opponent_id] = factory
        identities[opponent_id] = {
            "notebook_ref": record.notebook_ref,
            "notebook_id": record.notebook_id,
            "artifact_sha256": record.sha256,
        }
    return factories, identities


def actor_path_from_report(training_report: Mapping[str, object]) -> Path:
    """Authenticate and return an actor artifact named by a training report."""
    artifact = training_report.get("actor_artifact")
    if not isinstance(artifact, Mapping):
        raise ValueError("training report lacks an actor artifact")
    path = Path(str(artifact["path"]))
    if not path.is_file():
        raise FileNotFoundError(f"actor artifact does not exist: {path}")
    if path.stat().st_size != _as_int(artifact["size_bytes"]):
        raise ValueError("actor artifact size differs from the training report")
    if sha256_file(path) != str(artifact["sha256"]):
        raise ValueError("actor artifact identity differs from the training report")
    return path


def evaluate_policy(
    settings: ExperimentSettings,
    backend: BackendApi,
    training_report: Mapping[str, object],
    output_dir: Path,
) -> dict[str, object]:
    """Run paired selection against the incumbent and frozen confirmation ladder."""
    if settings.evaluation_device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA evaluation was requested but no GPU is available")
    torch.set_num_threads(settings.cpu_threads)
    actor_path = actor_path_from_report(training_report)
    public_factories, opponent_identities = _public_factories(backend, settings)

    def candidate_factory(configuration: Mapping[str, Any]) -> _Agent:
        return TurnPolicyAgent(
            backend,
            configuration,
            actor_path,
            settings.evaluation_device,
            settings.unit_limit,
            cpu_threads=settings.cpu_threads,
        )

    def baseline_factory(configuration: Mapping[str, Any]) -> _Agent:
        return BaselineAgent(backend, configuration)

    all_rows: list[dict[str, object]] = []
    selection_rows, selection_summary = run_paired_panel(
        backend,
        "turn_policy",
        candidate_factory,
        "deterministic_incumbent",
        baseline_factory,
        settings.selection_seeds,
        settings,
    )
    all_rows.extend(selection_rows)
    confirmation: dict[str, object] = {}
    for opponent_id, opponent_factory in public_factories.items():
        candidate_rows, candidate_summary = run_paired_panel(
            backend,
            "turn_policy",
            candidate_factory,
            opponent_id,
            opponent_factory,
            settings.confirmation_seeds,
            settings,
        )
        incumbent_rows, incumbent_summary = run_paired_panel(
            backend,
            "deterministic_incumbent",
            baseline_factory,
            opponent_id,
            opponent_factory,
            settings.confirmation_seeds,
            settings,
        )
        all_rows.extend(candidate_rows)
        all_rows.extend(incumbent_rows)
        confirmation[opponent_id] = {
            "turn_policy": candidate_summary,
            "deterministic_incumbent": incumbent_summary,
        }
    games_path = output_dir / "match-games.json"
    games_path.write_text(json.dumps(all_rows, indent=2, sort_keys=True), encoding="utf-8")
    expected_transitions = _as_int(settings.environment["episodeSteps"]) - 1
    report: dict[str, object] = {
        "schema_version": "turn-policy-evaluation-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "decision_surface": [
            "win",
            "loss",
            "tie",
            "terminal cash",
            "cash difference",
        ],
        "selection_seeds": list(settings.selection_seeds),
        "confirmation_seeds": list(settings.confirmation_seeds),
        "paired_seats": True,
        "resolved_environment": settings.environment,
        "completion": {
            "all_done": all(bool(row["done"]) for row in all_rows),
            "all_transition_counts_match": all(
                _as_int(row["transitions"]) == expected_transitions for row in all_rows
            ),
            "expected_transitions_per_game": expected_transitions,
        },
        "execution": {
            "device": settings.evaluation_device,
            "reason": "deployment-parity inference and native official-rule matches",
            "act_timeout_seconds": settings.act_timeout_seconds,
            "remaining_overage_seconds": settings.remaining_overage_seconds,
            "timeout_enforced": True,
            "candidate_observation_path": "native numeric",
        },
        "backend": backend.identity,
        "opponents": opponent_identities,
        "actor_artifact": {
            "path": str(actor_path),
            "sha256": sha256_file(actor_path),
            "size_bytes": actor_path.stat().st_size,
        },
        "selection": {
            "opponent": "deterministic_incumbent",
            "turn_policy": selection_summary,
        },
        "confirmation": confirmation,
        "games_artifact": {
            "path": str(games_path),
            "sha256": sha256_file(games_path),
            "games": len(all_rows),
        },
    }
    (output_dir / "evaluation-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report


__all__ = [
    "AgentFactory",
    "MatchSettings",
    "actor_path_from_report",
    "evaluate_policy",
    "run_game",
    "run_paired_panel",
    "summarize_games",
]
