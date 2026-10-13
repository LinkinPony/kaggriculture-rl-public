"""Oracle language audit for the authenticated Rank8 submission archive."""

from __future__ import annotations

import json
import statistics
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.rl.intents.audit_config import IntentOracleAuditSettings
from kagg_revue.rl.intents.market import market_round_trip, same_engine_state
from kagg_revue.rl.intents.oracle import HindsightIntentController
from kagg_revue.rl.intents.trace import (
    TraceAudit,
    TraceTurn,
    adapt_source_units,
    compile_trace,
    trace_turn,
    unit_actions,
)
from kagg_revue.teacher.intents import ProgramIntentTeacher
from kagg_revue.teacher.submission import (
    SubmissionTeacher,
    SubmissionTeacherArtifact,
    load_submission_teacher,
)


@dataclass(frozen=True, slots=True)
class _DirectGame:
    row: Mapping[str, object]
    trace: TraceAudit


@dataclass(slots=True)
class _AuditTotals:
    unit_actions: Counter[str]
    market_actions: Counter[str]
    semantic_tasks: Counter[str]
    intent_pressure: Counter[str]
    pickup_items: Counter[str]
    pickup_quantities: Counter[str]
    pickup_consumers: Counter[str]
    pickup_actor_roles: Counter[str]
    bulk_pickup_actor_roles: Counter[str]
    oracle_actions: Counter[str]
    unavailable_intents: Counter[str]
    market_adjustments: Counter[str]
    causal_actions: Counter[str]
    causal_unavailable_intents: Counter[str]
    causal_market_adjustments: Counter[str]
    market_failures: Counter[str]
    compression_failures: list[Mapping[str, object]]
    market_failure_examples: list[Mapping[str, object]]
    oracle_mismatch_examples: list[Mapping[str, object]]
    causal_mismatch_examples: list[Mapping[str, object]]
    sequences: int = 0
    exact_sequences: int = 0
    waypoint_tasks: int = 0
    path_reversals: int = 0
    multi_moving_hand_turns: int = 0
    maximum_simultaneous_moves: int = 0
    market_turns: int = 0
    market_exact_turns: int = 0
    market_semantic_turns: int = 0
    market_orders: int = 0
    oracle_turns: int = 0
    oracle_exact_unit_turns: int = 0
    oracle_unit_requests: int = 0
    oracle_exact_unit_requests: int = 0
    oracle_canonical_decisions: int = 0
    oracle_maximum_decisions_per_turn: int = 0
    causal_turns: int = 0
    causal_exact_unit_turns: int = 0
    causal_unit_requests: int = 0
    causal_exact_unit_requests: int = 0
    causal_canonical_decisions: int = 0
    causal_maximum_decisions_per_turn: int = 0

    @classmethod
    def create(cls) -> _AuditTotals:
        return cls(
            unit_actions=Counter(),
            market_actions=Counter(),
            semantic_tasks=Counter(),
            intent_pressure=Counter(),
            pickup_items=Counter(),
            pickup_quantities=Counter(),
            pickup_consumers=Counter(),
            pickup_actor_roles=Counter(),
            bulk_pickup_actor_roles=Counter(),
            oracle_actions=Counter(),
            unavailable_intents=Counter(),
            market_adjustments=Counter(),
            causal_actions=Counter(),
            causal_unavailable_intents=Counter(),
            causal_market_adjustments=Counter(),
            market_failures=Counter(),
            compression_failures=[],
            market_failure_examples=[],
            oracle_mismatch_examples=[],
            causal_mismatch_examples=[],
        )


def _integer(configuration: Mapping[str, object], name: str) -> int:
    value = configuration[name]
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"oracle audit environment {name} must be an integer")
    return value


def _outcome(candidate_cash: float, opponent_cash: float) -> int:
    return int(candidate_cash > opponent_cash) - int(candidate_cash < opponent_cash)


def _run_direct_game(
    backend: BackendApi,
    artifact: SubmissionTeacherArtifact,
    configuration: Mapping[str, object],
    seed: int,
    seat: int,
    totals: _AuditTotals,
) -> _DirectGame:
    engine = backend.engine(seed=seed, configuration=dict(configuration))
    initial_cash = float(engine.money(seat))
    candidate = SubmissionTeacher(configuration, artifact)
    opponent = SubmissionTeacher(configuration, artifact)
    turns: list[TraceTurn] = []
    while not bool(engine.done):
        step = int(engine.step_index)
        observation = cast(Mapping[str, object], engine.observation(seat))
        candidate_action = candidate.act(observation)
        opponent_action = opponent.act(engine.observation(1 - seat))
        turns.append(trace_turn(observation, seat, candidate_action))
        market = cast(Sequence[Sequence[object]], candidate_action["market"])
        market_audit = market_round_trip(backend, configuration, engine, seat, market)
        totals.market_turns += 1
        totals.market_orders += len(market)
        totals.market_exact_turns += market_audit.exact_request
        totals.market_adjustments.update(market_audit.adjustments)
        canonical_engine = None
        if not market_audit.exact_request and market_audit.canonical_market is not None:
            canonical_engine = engine.clone()
            canonical_action = {
                **candidate_action,
                "market": [list(order) for order in market_audit.canonical_market],
            }
            canonical_actions = [opponent_action, opponent_action]
            canonical_actions[seat] = canonical_action
            canonical_engine.step(canonical_actions[0], canonical_actions[1])
        actions: list[Mapping[str, object]] = [opponent_action, opponent_action]
        actions[seat] = candidate_action
        engine.step(actions[0], actions[1])
        semantic = market_audit.exact_request or (
            canonical_engine is not None and same_engine_state(engine, canonical_engine)
        )
        totals.market_semantic_turns += semantic
        if not semantic:
            reason = market_audit.reason or (
                "unavailable_sell_skip_state_mismatch"
                if "replace_unavailable_sell_with_skip" in market_audit.adjustments
                else "canonical_state_mismatch"
            )
            totals.market_failures[reason] += 1
            if len(totals.market_failure_examples) < 20:
                totals.market_failure_examples.append(
                    {
                        "seed": seed,
                        "seat": seat,
                        "step": step,
                        "reason": reason,
                        "adjustments": list(market_audit.adjustments),
                    }
                )

    identity = {"seed": seed, "seat": seat}
    trace = compile_trace(
        turns,
        board_size=_integer(configuration, "boardSize"),
        turns_per_day=_integer(configuration, "turnsPerDay"),
        identity=identity,
    )
    totals.unit_actions.update(trace.unit_actions)
    totals.market_actions.update(trace.market_actions)
    totals.semantic_tasks.update(trace.semantic_tasks)
    totals.intent_pressure.update(trace.intent_pressure)
    totals.pickup_items.update(trace.pickup_items)
    totals.pickup_quantities.update(trace.pickup_quantities)
    totals.pickup_consumers.update(trace.pickup_consumers)
    totals.pickup_actor_roles.update(trace.pickup_actor_roles)
    totals.bulk_pickup_actor_roles.update(trace.bulk_pickup_actor_roles)
    totals.sequences += trace.sequences
    totals.exact_sequences += trace.exact_sequences
    totals.waypoint_tasks += trace.waypoint_tasks
    totals.path_reversals += trace.path_reversals
    totals.multi_moving_hand_turns += trace.multi_moving_hand_turns
    totals.maximum_simultaneous_moves = max(
        totals.maximum_simultaneous_moves, trace.maximum_simultaneous_moves
    )
    totals.compression_failures.extend(
        trace.failure_examples[: max(0, 20 - len(totals.compression_failures))]
    )
    candidate_cash = float(engine.money(seat))
    opponent_cash = float(engine.money(1 - seat))
    return _DirectGame(
        row={
            **identity,
            "transitions": int(engine.step_index),
            "done": bool(engine.done),
            "outcome": _outcome(candidate_cash, opponent_cash),
            "initial_cash": initial_cash,
            "terminal_cash": candidate_cash,
            "opponent_cash": opponent_cash,
            "candidate_route": candidate.metadata(),
            "opponent_route": opponent.metadata(),
        },
        trace=trace,
    )


def _run_oracle_game(
    backend: BackendApi,
    artifact: SubmissionTeacherArtifact,
    configuration: Mapping[str, object],
    seed: int,
    seat: int,
    source: _DirectGame,
    totals: _AuditTotals,
) -> Mapping[str, object]:
    engine = backend.engine(seed=seed, configuration=dict(configuration))
    initial_cash = float(engine.money(seat))
    controller = HindsightIntentController(backend, configuration)
    opponent = SubmissionTeacher(configuration, artifact)
    for directive in source.trace.directives:
        if bool(engine.done):
            break
        step = int(engine.step_index)
        result = controller.act(engine, seat, directive)
        totals.oracle_turns += 1
        totals.oracle_canonical_decisions += len(result.canonical_ids)
        totals.oracle_maximum_decisions_per_turn = max(
            totals.oracle_maximum_decisions_per_turn,
            len(result.canonical_ids),
        )
        totals.unavailable_intents.update(result.unavailable_intents)
        totals.market_adjustments.update(
            {f"oracle:{key}": value for key, value in result.market_adjustments.items()}
        )
        observation = cast(Mapping[str, object], engine.observation(seat))
        farm = cast(Sequence[Mapping[str, object]], observation["farms"])[seat]
        expected = adapt_source_units(directive.action, len(cast(Sequence[object], farm["hands"])))
        actual = unit_actions(result.action)
        totals.oracle_actions.update(str(action[0]) for action in actual)
        exact_turn = actual == expected
        totals.oracle_exact_unit_turns += exact_turn
        totals.oracle_unit_requests += max(len(actual), len(expected))
        totals.oracle_exact_unit_requests += sum(
            left == right for left, right in zip(actual, expected, strict=False)
        )
        if not exact_turn and len(totals.oracle_mismatch_examples) < 20:
            totals.oracle_mismatch_examples.append(
                {
                    "seed": seed,
                    "seat": seat,
                    "step": step,
                    "expected": [list(action) for action in expected],
                    "actual": [list(action) for action in actual],
                    "unavailable": dict(result.unavailable_intents),
                }
            )
        opponent_action = opponent.act(engine.observation(1 - seat))
        actions: list[Mapping[str, object]] = [opponent_action, opponent_action]
        actions[seat] = result.action
        engine.step(actions[0], actions[1])
    candidate_cash = float(engine.money(seat))
    opponent_cash = float(engine.money(1 - seat))
    return {
        "seed": seed,
        "seat": seat,
        "transitions": int(engine.step_index),
        "done": bool(engine.done),
        "outcome": _outcome(candidate_cash, opponent_cash),
        "initial_cash": initial_cash,
        "terminal_cash": candidate_cash,
        "opponent_cash": opponent_cash,
        "source_route": source.row["candidate_route"],
        "opponent_route": opponent.metadata(),
    }


def _run_causal_game(
    backend: BackendApi,
    artifact: SubmissionTeacherArtifact,
    configuration: Mapping[str, object],
    seed: int,
    seat: int,
    source: _DirectGame,
    totals: _AuditTotals,
) -> Mapping[str, object]:
    """Run the actor-safe route program through the canonical dispatcher."""
    engine = backend.engine(seed=seed, configuration=dict(configuration))
    initial_cash = float(engine.money(seat))
    teacher = ProgramIntentTeacher(backend, configuration, artifact)
    opponent = SubmissionTeacher(configuration, artifact)
    for source_directive in source.trace.directives:
        if bool(engine.done):
            break
        step = int(engine.step_index)
        turn = teacher.act(engine, seat)
        result = turn.result
        totals.causal_turns += 1
        totals.causal_canonical_decisions += len(result.canonical_ids)
        totals.causal_maximum_decisions_per_turn = max(
            totals.causal_maximum_decisions_per_turn,
            len(result.canonical_ids),
        )
        totals.causal_unavailable_intents.update(result.unavailable_intents)
        totals.causal_market_adjustments.update(result.market_adjustments)
        observation = cast(Mapping[str, object], engine.observation(seat))
        farm = cast(Sequence[Mapping[str, object]], observation["farms"])[seat]
        expected = adapt_source_units(
            source_directive.action,
            len(cast(Sequence[object], farm["hands"])),
        )
        actual = unit_actions(result.action)
        totals.causal_actions.update(str(action[0]) for action in actual)
        exact_turn = actual == expected
        totals.causal_exact_unit_turns += exact_turn
        totals.causal_unit_requests += max(len(actual), len(expected))
        totals.causal_exact_unit_requests += sum(
            left == right for left, right in zip(actual, expected, strict=False)
        )
        if not exact_turn and len(totals.causal_mismatch_examples) < 20:
            totals.causal_mismatch_examples.append(
                {
                    "seed": seed,
                    "seat": seat,
                    "step": step,
                    "expected": [list(action) for action in expected],
                    "actual": [list(action) for action in actual],
                    "tasks": [
                        {
                            "unit": unit,
                            "operation": task.operation.name,
                            "target": task.target,
                            "argument": task.argument,
                            "quantity": task.quantity,
                            "earliest_start": task.earliest_start,
                            "deadline": task.deadline,
                        }
                        for unit, task in enumerate(turn.tasks)
                    ],
                }
            )
        opponent_action = opponent.act(engine.observation(1 - seat))
        actions: list[Mapping[str, object]] = [opponent_action, opponent_action]
        actions[seat] = result.action
        engine.step(actions[0], actions[1])
    candidate_cash = float(engine.money(seat))
    opponent_cash = float(engine.money(1 - seat))
    return {
        "seed": seed,
        "seat": seat,
        "transitions": int(engine.step_index),
        "done": bool(engine.done),
        "outcome": _outcome(candidate_cash, opponent_cash),
        "initial_cash": initial_cash,
        "terminal_cash": candidate_cash,
        "opponent_cash": opponent_cash,
        "source_route": source.row["candidate_route"],
        "teacher_route": teacher.metadata(),
        "opponent_route": opponent.metadata(),
    }


def _summary(games: Sequence[Mapping[str, object]]) -> dict[str, float | int]:
    outcomes = [int(cast(int, game["outcome"])) for game in games]
    return {
        "games": len(games),
        "wins": sum(value > 0 for value in outcomes),
        "ties": sum(value == 0 for value in outcomes),
        "losses": sum(value < 0 for value in outcomes),
        "mean_terminal_cash": statistics.fmean(
            float(cast(float, game["terminal_cash"])) for game in games
        ),
        "mean_cash_difference": statistics.fmean(
            float(cast(float, game["terminal_cash"])) - float(cast(float, game["opponent_cash"]))
            for game in games
        ),
    }


def _cash_profile(games: Sequence[Mapping[str, object]]) -> dict[str, float | int | bool]:
    """Summarize productive value without treating cash as policy promotion."""
    terminal = [float(cast(float, game["terminal_cash"])) for game in games]
    initial = [float(cast(float, game["initial_cash"])) for game in games]
    gains = [end - start for end, start in zip(terminal, initial, strict=True)]
    return {
        "games": len(games),
        "minimum_terminal_cash": min(terminal),
        "median_terminal_cash": statistics.median(terminal),
        "mean_terminal_cash": statistics.fmean(terminal),
        "maximum_terminal_cash": max(terminal),
        "mean_initial_cash": statistics.fmean(initial),
        "minimum_gain_over_initial": min(gains),
        "mean_gain_over_initial": statistics.fmean(gains),
        "all_games_above_initial_cash": all(gain > 0.0 for gain in gains),
    }


def _paired_comparison(
    direct: Sequence[Mapping[str, object]], oracle: Sequence[Mapping[str, object]]
) -> dict[str, int]:
    direct_by_key = {
        (int(cast(int, row["seed"])), int(cast(int, row["seat"]))): int(cast(int, row["outcome"]))
        for row in direct
    }
    oracle_by_key = {
        (int(cast(int, row["seed"])), int(cast(int, row["seat"]))): int(cast(int, row["outcome"]))
        for row in oracle
    }
    if direct_by_key.keys() != oracle_by_key.keys():
        raise RuntimeError("oracle and direct Rank8 panels are not paired")
    deltas = [oracle_by_key[key] - direct_by_key[key] for key in direct_by_key]
    return {
        "games": len(deltas),
        "better": sum(value > 0 for value in deltas),
        "same": sum(value == 0 for value in deltas),
        "worse": sum(value < 0 for value in deltas),
    }


def _paired_cash_comparison(
    direct: Sequence[Mapping[str, object]],
    challenger: Sequence[Mapping[str, object]],
    *,
    label: str = "oracle",
) -> dict[str, float | int]:
    """Compare own terminal cash on identical source seed and seat keys."""
    direct_by_key = {
        (int(cast(int, row["seed"])), int(cast(int, row["seat"]))): float(
            cast(float, row["terminal_cash"])
        )
        for row in direct
    }
    challenger_by_key = {
        (int(cast(int, row["seed"])), int(cast(int, row["seat"]))): float(
            cast(float, row["terminal_cash"])
        )
        for row in challenger
    }
    if direct_by_key.keys() != challenger_by_key.keys():
        raise RuntimeError("oracle and direct Rank8 cash panels are not paired")
    direct_cash = list(direct_by_key.values())
    challenger_cash = [challenger_by_key[key] for key in direct_by_key]
    deltas = [right - left for left, right in zip(direct_cash, challenger_cash, strict=True)]
    return {
        "games": len(deltas),
        "direct_mean_terminal_cash": statistics.fmean(direct_cash),
        f"{label}_mean_terminal_cash": statistics.fmean(challenger_cash),
        f"mean_{label}_minus_direct": statistics.fmean(deltas),
        f"median_{label}_minus_direct": statistics.median(deltas),
        f"minimum_{label}_minus_direct": min(deltas),
        f"maximum_{label}_minus_direct": max(deltas),
        "aggregate_cash_retained_percent": 100.0 * sum(challenger_cash) / sum(direct_cash),
        f"{label}_cash_better_games": sum(value > 0.0 for value in deltas),
        f"{label}_cash_same_games": sum(value == 0.0 for value in deltas),
        f"{label}_cash_worse_games": sum(value < 0.0 for value in deltas),
    }


def _event_day(row: Mapping[str, object], route_field: str) -> int | None:
    route = cast(Mapping[str, object], row[route_field])
    value = route.get("first_event_day")
    return None if value is None else int(cast(int, value))


def _branch_summaries(
    direct: Sequence[Mapping[str, object]],
    oracle: Sequence[Mapping[str, object]],
    causal: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Report paired outcomes separately for each observed Rank8 branch."""
    days = sorted(
        {_event_day(row, "candidate_route") for row in direct},
        key=lambda value: -1 if value is None else value,
    )
    result: dict[str, object] = {}
    for day in days:
        direct_rows = [row for row in direct if _event_day(row, "candidate_route") == day]
        oracle_rows = [row for row in oracle if _event_day(row, "source_route") == day]
        causal_rows = [row for row in causal if _event_day(row, "source_route") == day]
        result["default" if day is None else f"day_{day}"] = {
            "direct": _summary(direct_rows),
            "oracle": _summary(oracle_rows),
            "causal_teacher": _summary(causal_rows),
            "oracle_vs_direct_paired": _paired_comparison(direct_rows, oracle_rows),
            "oracle_vs_direct_paired_cash": _paired_cash_comparison(direct_rows, oracle_rows),
            "causal_teacher_vs_direct_paired": _paired_comparison(direct_rows, causal_rows),
            "causal_teacher_vs_direct_paired_cash": _paired_cash_comparison(
                direct_rows, causal_rows, label="causal_teacher"
            ),
        }
    return result


def audit_oracle_language(
    settings: IntentOracleAuditSettings, repository_root: Path
) -> dict[str, object]:
    """Run exact Rank8 trace coverage and dispatcher closed-loop matches."""
    root = repository_root.resolve()
    output_dir = (root / settings.output_dir).resolve()
    if not output_dir.is_relative_to((root / "outputs").resolve()):
        raise ValueError("intent oracle audit escaped outputs/")
    if output_dir.exists():
        raise FileExistsError(f"intent oracle audit output exists: {output_dir}")
    source = source_identity(root)
    if settings.require_clean_source and bool(source["worktree_dirty"]):
        raise RuntimeError("formal intent oracle audit requires a clean worktree")

    archive_path = (root / settings.teacher.archive_path).resolve()
    artifact = load_submission_teacher(
        archive_path,
        settings.teacher.archive_sha256,
        settings.teacher.source_commit,
        settings.teacher.route_sha256,
    )
    backend = load_backend(root)
    configuration = settings.environment
    totals = _AuditTotals.create()
    direct_games: list[Mapping[str, object]] = []
    oracle_games: list[Mapping[str, object]] = []
    causal_games: list[Mapping[str, object]] = []
    started = time.perf_counter()
    for seed in settings.seeds:
        for seat in (0, 1):
            direct = _run_direct_game(backend, artifact, configuration, seed, seat, totals)
            direct_games.append(direct.row)
            oracle_games.append(
                _run_oracle_game(
                    backend,
                    artifact,
                    configuration,
                    seed,
                    seat,
                    direct,
                    totals,
                )
            )
            causal_games.append(
                _run_causal_game(
                    backend,
                    artifact,
                    configuration,
                    seed,
                    seat,
                    direct,
                    totals,
                )
            )
    elapsed = time.perf_counter() - started
    paired = _paired_comparison(direct_games, oracle_games)
    causal_paired = _paired_comparison(direct_games, causal_games)
    causal_cash = _paired_cash_comparison(direct_games, causal_games, label="causal_teacher")
    branch_summaries = _branch_summaries(direct_games, oracle_games, causal_games)
    observed_event_days = {
        day for row in direct_games if (day := _event_day(row, "candidate_route")) is not None
    }
    branch_coverage = set(settings.required_event_days).issubset(observed_event_days)
    complete = all(
        bool(game["done"])
        and int(cast(int, game["transitions"])) == _integer(configuration, "episodeSteps") - 1
        for game in [*direct_games, *oracle_games, *causal_games]
    )
    trace_exact = totals.exact_sequences == totals.sequences
    market_exact = totals.market_semantic_turns == totals.market_turns
    noninferior = paired["worse"] == 0
    fidelity_passed = complete and trace_exact and market_exact and branch_coverage and noninferior
    causal_cash_noninferior = causal_cash["causal_teacher_cash_worse_games"] == 0
    causal_fidelity = (
        complete
        and branch_coverage
        and causal_paired["worse"] == 0
        and causal_cash_noninferior
        and not totals.causal_unavailable_intents
    )
    cash_profile = _cash_profile(causal_games)
    productive = complete and bool(cash_profile["all_games_above_initial_cash"])
    promising = productive and causal_fidelity
    if promising and not bool(source["worktree_dirty"]):
        warm_start_status = "promising"
        training_decision = "proceed_to_causal_teacher_bc_pilot"
    elif promising:
        warm_start_status = "promising_dirty_diagnostic"
        training_decision = "reconfirm_clean_before_sealing_bc_data"
    else:
        warm_start_status = "not_productive"
        training_decision = "do_not_generate_bc_from_this_teacher"

    report: dict[str, object] = {
        "schema_version": "canonical-intent-oracle-language-audit-v6",
        "role": (
            "Rank8 language audit plus an actor-safe route-program teacher screen; "
            "only the causal teacher may produce training labels"
        ),
        "source": source,
        "artifacts": {
            "native_backend": backend.identity,
            "rank8_submission": {
                "submission_id": settings.teacher.submission_id,
                **artifact.identity(),
            },
            "opponent": {
                "kind": "same_authenticated_rank8_submission",
                "archive_sha256": artifact.archive_sha256,
                "route_sha256": artifact.route_sha256,
            },
            "intent_abi": cast(Mapping[str, object], backend.intent_ledger_spec())["abi_version"],
        },
        "panel": {
            "seeds": list(settings.seeds),
            "seed_count": len(settings.seeds),
            "paired_seats": True,
            "required_event_days": list(settings.required_event_days),
            "observed_event_days": sorted(observed_event_days),
            "required_branch_coverage": branch_coverage,
            "control": "direct Rank8 vs direct Rank8",
            "challengers": [
                "hindsight-translated Rank8 intent dispatcher vs direct Rank8",
                "causal Rank8 route-program intent teacher vs direct Rank8",
            ],
            "environment": dict(configuration),
        },
        "source_trace_language": {
            "lossless_semantic_compression": trace_exact,
            "day_unit_sequences": totals.sequences,
            "exact_sequences": totals.exact_sequences,
            "failure_examples": totals.compression_failures,
            "raw_operations": dict(sorted(totals.unit_actions.items())),
            "semantic_tasks": dict(sorted(totals.semantic_tasks.items())),
            "waypoint_tasks": totals.waypoint_tasks,
            "path_reversals": totals.path_reversals,
            "multi_moving_hand_turns": totals.multi_moving_hand_turns,
            "maximum_simultaneous_moves": totals.maximum_simultaneous_moves,
            "intent_pressure": dict(sorted(totals.intent_pressure.items())),
            "pickup_items": dict(sorted(totals.pickup_items.items())),
            "pickup_quantities": dict(sorted(totals.pickup_quantities.items())),
            "pickup_consumers": dict(sorted(totals.pickup_consumers.items())),
            "pickup_actor_roles": dict(sorted(totals.pickup_actor_roles.items())),
            "bulk_pickup_actor_roles": dict(sorted(totals.bulk_pickup_actor_roles.items())),
        },
        "market_language": {
            "canonical_state_transition_coverage": market_exact,
            "turns": totals.market_turns,
            "exact_request_turns": totals.market_exact_turns,
            "canonical_semantic_turns": totals.market_semantic_turns,
            "orders": totals.market_orders,
            "order_kinds": dict(sorted(totals.market_actions.items())),
            "adjustments": dict(sorted(totals.market_adjustments.items())),
            "failure_counts": dict(sorted(totals.market_failures.items())),
            "failure_examples": totals.market_failure_examples,
        },
        "oracle_dispatcher": {
            "uses_future_source_trace": True,
            "training_labels_permitted": False,
            "canonical_decisions": totals.oracle_canonical_decisions,
            "maximum_canonical_decisions_per_turn": (totals.oracle_maximum_decisions_per_turn),
            "turns": totals.oracle_turns,
            "exact_unit_turns": totals.oracle_exact_unit_turns,
            "unit_requests": totals.oracle_unit_requests,
            "exact_unit_requests": totals.oracle_exact_unit_requests,
            "compiled_unit_operations": dict(sorted(totals.oracle_actions.items())),
            "unavailable_intents": dict(sorted(totals.unavailable_intents.items())),
            "mismatch_examples": totals.oracle_mismatch_examples,
        },
        "causal_teacher": {
            "uses_future_environment_observations": False,
            "uses_authenticated_actor_program_suffix": True,
            "training_labels_permitted": True,
            "label_surface": "dynamic canonical candidate id",
            "canonical_decisions": totals.causal_canonical_decisions,
            "maximum_canonical_decisions_per_turn": (totals.causal_maximum_decisions_per_turn),
            "turns": totals.causal_turns,
            "exact_unit_turns": totals.causal_exact_unit_turns,
            "unit_requests": totals.causal_unit_requests,
            "exact_unit_requests": totals.causal_exact_unit_requests,
            "compiled_unit_operations": dict(sorted(totals.causal_actions.items())),
            "unavailable_intents": dict(sorted(totals.causal_unavailable_intents.items())),
            "market_adjustments": dict(sorted(totals.causal_market_adjustments.items())),
            "mismatch_examples": totals.causal_mismatch_examples,
            "direct_fidelity": {
                "passed": causal_fidelity,
                "paired_outcomes": causal_paired,
                "paired_cash": causal_cash,
            },
        },
        "closed_loop": {
            "complete_matches": complete,
            "decision_surface": "paired complete-match terminal W/D/L",
            "cash_role": "diagnostic only",
            "direct_control": {
                "summary": _summary(direct_games),
                "games": direct_games,
            },
            "oracle": {
                "summary": _summary(oracle_games),
                "games": oracle_games,
            },
            "causal_teacher": {
                "summary": _summary(causal_games),
                "games": causal_games,
            },
            "oracle_vs_direct_paired": paired,
            "oracle_vs_direct_paired_cash": _paired_cash_comparison(direct_games, oracle_games),
            "causal_teacher_vs_direct_paired": causal_paired,
            "causal_teacher_vs_direct_paired_cash": causal_cash,
            "by_source_event_branch": branch_summaries,
        },
        "rank8_fidelity_diagnostic": {
            "status": "passed" if fidelity_passed else "not_fidelity_preserving",
            "passed": fidelity_passed,
            "bc_warm_start_decision_authority": False,
            "criteria": {
                "complete_matches": complete,
                "lossless_source_trace": trace_exact,
                "canonical_market_state_equivalence": market_exact,
                "required_event_branch_coverage": branch_coverage,
                "zero_paired_outcome_regressions": noninferior,
                "clean_source": not bool(source["worktree_dirty"]),
            },
        },
        "bc_warm_start_screen": {
            "status": warm_start_status,
            "promising": promising,
            "cash_is_diagnostic_not_promotion_authority": True,
            "cash": cash_profile,
            "hindsight_labels_permitted": False,
            "causal_program_labels_permitted": causal_fidelity,
            "required_next_evidence": (
                "causal teacher and trained BC versus a frozen fresh-intent baseline "
                "on common seeds, followed by the weak strength ladder"
            ),
            "training_decision": training_decision,
        },
        "elapsed_seconds": elapsed,
    }
    output_dir.mkdir(parents=True)
    (output_dir / "resolved-settings.json").write_text(
        json.dumps(settings.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "audit-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report


__all__ = ["audit_oracle_language"]
