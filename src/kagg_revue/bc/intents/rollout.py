"""Native-batched causal teacher rollouts for canonical-intent BC."""

from __future__ import annotations

import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.intents.dataset import IntentTeacherShard, pack_intent_teacher_arrays
from kagg_revue.core.backend import load_backend
from kagg_revue.teacher.config import SubmissionArtifactSettings
from kagg_revue.teacher.intents import (
    ProgramIntentPlan,
    ProgramIntentPlanner,
    encode_native_intent_plans,
)
from kagg_revue.teacher.npz import write_compressed_npz
from kagg_revue.teacher.submission import load_submission_teacher


@dataclass(frozen=True, slots=True)
class IntentTeacherShardTask:
    """One independent complete-game output shard."""

    index: int
    seeds: tuple[int, ...]
    output_path: Path
    repository_root: Path
    artifact: SubmissionArtifactSettings
    environment: Mapping[str, object]
    route_codes: Mapping[str, int]
    unit_limit: int
    max_transaction_steps: int
    native_workers: int
    compression_level: int


@dataclass(frozen=True, slots=True)
class IntentTeacherShardResult:
    """One completed shard plus mergeable causal-teacher diagnostics."""

    shard: IntentTeacherShard
    route_counts: Mapping[str, int]
    event_day_counts: Mapping[str, int]
    operation_counts: Mapping[str, int]
    elapsed_seconds: float
    rollout_seconds: float
    export_seconds: float
    write_seconds: float


def _integer(values: Mapping[str, object], name: str) -> int:
    value = values.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"intent teacher environment {name} must be an integer")
    return value


def _advance(
    backend: Any,
    engines: list[Any],
    compiled: Mapping[str, Any],
    workers: int,
) -> None:
    tokens = np.asarray(compiled["tokens"], dtype=np.int64)
    quantities = np.asarray(compiled["quantities"], dtype=np.int64)
    counts = np.asarray(compiled["decision_counts"], dtype=np.int64)
    unit_counts = np.asarray(compiled["unit_counts"], dtype=np.int64)
    games = len(engines)
    backend.engine_step_numeric_batch(
        engines,
        tokens.reshape(games, 2, tokens.shape[1]),
        quantities.reshape(games, 2, quantities.shape[1]),
        counts.reshape(games, 2),
        unit_counts.reshape(games, 2),
        min(workers, games),
    )


def _route_metadata(
    planners: Sequence[ProgramIntentPlanner],
    route_codes: Mapping[str, int],
) -> tuple[NDArray[np.uint8], NDArray[np.int16], Counter[str], Counter[str]]:
    codes: list[int] = []
    days: list[int] = []
    route_counts: Counter[str] = Counter()
    event_counts: Counter[str] = Counter()
    for planner in planners:
        metadata = planner.metadata()
        route_id = str(metadata["route_id"])
        if route_id not in route_codes:
            raise ValueError(f"intent teacher selected unknown route {route_id!r}")
        raw_day = metadata["first_event_day"]
        if raw_day is not None and (not isinstance(raw_day, int) or isinstance(raw_day, bool)):
            raise TypeError("intent teacher event day must be an integer or null")
        day = -1 if raw_day is None else raw_day
        codes.append(route_codes[route_id])
        days.append(day)
        route_counts[route_id] += 1
        event_counts["none" if day < 0 else str(day)] += 1
    return (
        np.asarray(codes, dtype=np.uint8),
        np.asarray(days, dtype=np.int16),
        route_counts,
        event_counts,
    )


def generate_intent_teacher_shard(task: IntentTeacherShardTask) -> IntentTeacherShardResult:
    """Generate one exact causal-program shard through the native intent ABI."""
    started = time.perf_counter()
    backend = load_backend(task.repository_root)
    artifact = load_submission_teacher(
        task.artifact.archive_path,
        task.artifact.archive_sha256,
        task.artifact.source_commit,
        task.artifact.route_sha256,
    )
    engines = [backend.engine(seed, dict(task.environment)) for seed in task.seeds]
    if not engines:
        raise ValueError("intent teacher shard requires at least one seed")
    configuration = cast(dict[str, object], engines[0].configuration)
    if any(dict(engine.configuration) != configuration for engine in engines):
        raise RuntimeError("intent teacher engines resolved different configurations")
    perspective_engines = [engine for engine in engines for _ in (0, 1)]
    players = np.tile(np.asarray([0, 1], dtype=np.int64), len(engines))
    player_list = players.tolist()
    sessions = [backend.intent_ledger_session(configuration) for _ in players]
    planners = [ProgramIntentPlanner(configuration, artifact) for _ in players]
    native_batch = backend.intent_ledger_batch(
        sessions,
        perspective_engines,
        players,
        task.native_workers,
    )
    episodes = len(perspective_engines)
    turns = _integer(configuration, "episodeSteps") - 1
    board_size = _integer(configuration, "boardSize")
    maximum_market_orders = _integer(configuration, "maxMarketOrdersPerTurn")
    action_capacity = task.unit_limit + maximum_market_orders
    action_store = np.zeros((episodes, turns, action_capacity), dtype=np.int64)
    quantity_store = np.zeros_like(action_store)
    action_counts = np.zeros((episodes, turns), dtype=np.int64)
    board_store: NDArray[np.float16] | None = None
    unit_store: NDArray[np.float16] | None = None
    global_store: NDArray[np.float32] | None = None
    economic_store: NDArray[np.int32] | None = None
    maximum_decisions = 0
    clipped_market = 0
    omitted_sell = 0
    replaced_sell = 0
    operation_counts: Counter[str] = Counter()
    rollout_started = time.perf_counter()

    for turn in range(turns):
        observations = [
            cast(Mapping[str, object], engine.observation(player))
            for engine, player in zip(perspective_engines, player_list, strict=True)
        ]
        plans: list[ProgramIntentPlan] = [
            planner.plan(observation)
            for planner, observation in zip(planners, observations, strict=True)
        ]
        operation_counts.update(task_.operation.name for plan in plans for task_ in plan.tasks)
        encoded = encode_native_intent_plans(
            plans,
            cast(Mapping[str, object], backend.intent_ledger_spec()),
            board_size=board_size,
            unit_limit=task.unit_limit,
            maximum_market_orders=maximum_market_orders,
        )
        turn_inputs = backend.engine_policy_turn_inputs(
            perspective_engines,
            player_list,
            task.unit_limit,
            task.native_workers,
        )
        board = np.asarray(turn_inputs[0], dtype=np.float16)
        units = np.asarray(turn_inputs[1], dtype=np.float16)
        global_features = np.asarray(turn_inputs[2], dtype=np.float32)
        native_unit_counts = np.asarray(turn_inputs[3], dtype=np.int64)
        economic = np.asarray(turn_inputs[4], dtype=np.int32)
        if not np.array_equal(native_unit_counts, encoded.directive_counts):
            raise RuntimeError("intent teacher plan and native unit counts differ")
        if board_store is None:
            board_store = np.empty((episodes, turns, *board.shape[1:]), dtype=np.float16)
            unit_store = np.empty((episodes, turns, *units.shape[1:]), dtype=np.float16)
            global_store = np.empty((episodes, turns, global_features.shape[1]), dtype=np.float32)
            economic_store = np.empty((episodes, turns, economic.shape[1]), dtype=np.int32)
        if unit_store is None or global_store is None or economic_store is None:
            raise RuntimeError("intent teacher rollout storage was not initialized")
        board_store[:, turn] = board
        unit_store[:, turn] = units
        global_store[:, turn] = global_features
        economic_store[:, turn] = economic

        result = cast(
            Mapping[str, Any],
            native_batch.apply_teacher_plans(
                *encoded.arguments(),
                turn,
                task.max_transaction_steps,
            ),
        )
        turn_decisions = np.asarray(result["decision_counts"], dtype=np.int64)
        maximum_decisions = max(maximum_decisions, int(turn_decisions.max()))
        clipped_market += int(np.asarray(result["clipped_market_quantities"], dtype=np.int64).sum())
        omitted_sell += int(np.asarray(result["omitted_sell_orders"], dtype=np.int64).sum())
        replaced_sell += int(
            np.asarray(result["replaced_unavailable_sell_slots"], dtype=np.int64).sum()
        )
        compiled = cast(
            Mapping[str, Any],
            backend.intent_ledger_actions_batch(
                sessions,
                perspective_engines,
                players,
                task.native_workers,
            ),
        )
        tokens = np.asarray(compiled["tokens"], dtype=np.int64)
        quantities = np.asarray(compiled["quantities"], dtype=np.int64)
        counts = np.asarray(compiled["decision_counts"], dtype=np.int64)
        if tokens.shape[1] > action_capacity:
            raise RuntimeError("intent teacher compiled action exceeds actor history capacity")
        action_store[:, turn, : tokens.shape[1]] = tokens
        quantity_store[:, turn, : quantities.shape[1]] = quantities
        action_counts[:, turn] = counts
        _advance(backend, engines, compiled, task.native_workers)

    rollout_seconds = time.perf_counter() - rollout_started
    if not all(bool(engine.done) for engine in engines):
        raise RuntimeError("intent teacher shard did not reach terminal state")
    if any(value is None for value in (board_store, unit_store, global_store, economic_store)):
        raise RuntimeError("intent teacher shard contains no official turns")

    terminal_cash = np.asarray(
        [
            engine.money(player)
            for engine, player in zip(perspective_engines, player_list, strict=True)
        ],
        dtype=np.float64,
    )
    opponent_cash = np.asarray(
        [
            engine.money(1 - player)
            for engine, player in zip(perspective_engines, player_list, strict=True)
        ],
        dtype=np.float64,
    )
    outcomes = np.sign(terminal_cash - opponent_cash).astype(np.float32)
    route_codes, event_days, route_counts, event_counts = _route_metadata(
        planners, task.route_codes
    )
    export_started = time.perf_counter()
    decisions = [
        dict(payload)
        for payload in cast(Sequence[Mapping[str, Any]], native_batch.export_rollout_buckets())
    ]
    bucket_widths = np.asarray(
        [np.asarray(payload["candidate_fields"]).shape[1] for payload in decisions],
        dtype=np.int32,
    )
    decision_count = sum(int(np.asarray(payload["selected"]).shape[0]) for payload in decisions)
    export_seconds = time.perf_counter() - export_started
    base: dict[str, NDArray[np.generic]] = {
        "board": cast(NDArray[np.float16], board_store),
        "units": cast(NDArray[np.float16], unit_store),
        "global_features": cast(NDArray[np.float32], global_store),
        "economic_state": cast(NDArray[np.int32], economic_store),
        "actions": action_store,
        "quantities": quantity_store,
        "decision_counts": action_counts,
        "outcomes": outcomes,
        "seeds": np.repeat(np.asarray(task.seeds, dtype=np.int64), 2),
        "seats": players.astype(np.uint8),
        "terminal_cash": terminal_cash,
        "opponent_cash": opponent_cash,
        "route_codes": route_codes,
        "first_event_days": event_days,
        "bucket_widths": bucket_widths,
    }
    arrays = pack_intent_teacher_arrays(base=base, decisions=decisions)
    task.output_path.parent.mkdir(parents=True, exist_ok=True)
    write_started = time.perf_counter()
    write_compressed_npz(task.output_path, arrays, task.compression_level)
    write_seconds = time.perf_counter() - write_started
    better = int(np.count_nonzero(outcomes > 0))
    ties = int(np.count_nonzero(outcomes == 0))
    worse = int(np.count_nonzero(outcomes < 0))
    shard = IntentTeacherShard(
        index=task.index,
        path=task.output_path.name,
        seed_start=task.seeds[0],
        games=len(task.seeds),
        episodes=episodes,
        turns_per_episode=turns,
        decisions=decision_count,
        maximum_transaction_steps=maximum_decisions,
        bucket_widths=tuple(int(value) for value in bucket_widths),
        terminal_cash_sum=float(terminal_cash.sum()),
        opponent_cash_sum=float(opponent_cash.sum()),
        better=better,
        ties=ties,
        worse=worse,
        clipped_market_quantities=clipped_market,
        omitted_sell_orders=omitted_sell,
        replaced_unavailable_sell_slots=replaced_sell,
        size_bytes=task.output_path.stat().st_size,
        sha256=sha256_file(task.output_path),
    )
    return IntentTeacherShardResult(
        shard=shard,
        route_counts=dict(route_counts),
        event_day_counts=dict(event_counts),
        operation_counts=dict(operation_counts),
        elapsed_seconds=time.perf_counter() - started,
        rollout_seconds=rollout_seconds,
        export_seconds=export_seconds,
        write_seconds=write_seconds,
    )


__all__ = [
    "IntentTeacherShardResult",
    "IntentTeacherShardTask",
    "generate_intent_teacher_shard",
]
