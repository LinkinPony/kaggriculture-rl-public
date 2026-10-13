"""Native-batched causal Rank8 rollouts for atomic-effect BC."""

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
from kagg_revue.bc.effects.dataset import (
    EffectTeacherShard,
    pack_effect_teacher_arrays,
)
from kagg_revue.core.backend import load_backend
from kagg_revue.teacher.config import SubmissionArtifactSettings
from kagg_revue.teacher.effects import Rank8EffectTeacher
from kagg_revue.teacher.npz import write_compressed_npz
from kagg_revue.teacher.submission import load_submission_teacher


@dataclass(frozen=True, slots=True)
class EffectTeacherShardTask:
    """One independent complete-game output shard."""

    index: int
    seeds: tuple[int, ...]
    output_path: Path
    repository_root: Path
    artifact: SubmissionArtifactSettings
    environment: Mapping[str, object]
    route_codes: Mapping[str, int]
    unit_limit: int
    maximum_quantity: int
    native_workers: int
    compression_level: int


@dataclass(frozen=True, slots=True)
class EffectTeacherShardResult:
    """One completed shard plus mergeable translation diagnostics."""

    shard: EffectTeacherShard
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
        raise TypeError(f"effect teacher environment {name} must be an integer")
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
    controllers: Sequence[Rank8EffectTeacher],
    route_codes: Mapping[str, int],
) -> tuple[NDArray[np.uint8], NDArray[np.int16], Counter[str], Counter[str]]:
    codes: list[int] = []
    days: list[int] = []
    route_counts: Counter[str] = Counter()
    event_counts: Counter[str] = Counter()
    for controller in controllers:
        metadata = controller.metadata()
        route_id = str(metadata["route_id"])
        if route_id not in route_codes:
            raise ValueError(f"effect teacher selected unknown route {route_id!r}")
        raw_day = metadata["first_event_day"]
        if raw_day is not None and (
            not isinstance(raw_day, int) or isinstance(raw_day, bool)
        ):
            raise TypeError("effect teacher event day must be an integer or null")
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


def generate_effect_teacher_shard(
    task: EffectTeacherShardTask,
) -> EffectTeacherShardResult:
    """Generate one causal Rank8 shard through the exact native effect ABI."""
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
        raise ValueError("effect teacher shard requires at least one seed")
    configuration = cast(dict[str, object], engines[0].configuration)
    if any(dict(engine.configuration) != configuration for engine in engines):
        raise RuntimeError("effect teacher engines resolved different configurations")
    perspective_engines = [engine for engine in engines for _ in (0, 1)]
    players = np.tile(np.asarray([0, 1], dtype=np.int64), len(engines))
    player_list = players.tolist()
    sessions = [
        backend.effect_policy_session(
            configuration,
            task.unit_limit,
            task.maximum_quantity,
        )
        for _ in players
    ]
    effect_spec = cast(Mapping[str, object], backend.effect_policy_spec())
    actor_spec = cast(Mapping[str, object], backend.actor_encoder_spec())
    item_names = cast(Sequence[object], actor_spec["item_names"])
    controllers = [
        Rank8EffectTeacher(configuration, artifact, effect_spec, item_names)
        for _ in players
    ]
    native_batch = backend.effect_policy_batch(
        sessions,
        perspective_engines,
        players,
        task.native_workers,
    )
    episodes = len(perspective_engines)
    turns = _integer(configuration, "episodeSteps") - 1
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
    policy_factors = 0
    rollout_started = time.perf_counter()
    all_rows = np.arange(episodes, dtype=np.int64)

    for turn in range(turns):
        observations = [
            cast(Mapping[str, object], engine.observation(player))
            for engine, player in zip(
                perspective_engines,
                player_list,
                strict=True,
            )
        ]
        for controller, observation in zip(controllers, observations, strict=True):
            controller.prepare(observation)
        turn_inputs = backend.engine_policy_turn_inputs(
            perspective_engines,
            player_list,
            task.unit_limit,
            task.native_workers,
        )
        board = np.asarray(turn_inputs[0], dtype=np.float16)
        units = np.asarray(turn_inputs[1], dtype=np.float16)
        global_features = np.asarray(turn_inputs[2], dtype=np.float32)
        economic = np.asarray(turn_inputs[4], dtype=np.int32)
        if board_store is None:
            board_store = np.empty((episodes, turns, *board.shape[1:]), dtype=np.float16)
            unit_store = np.empty((episodes, turns, *units.shape[1:]), dtype=np.float16)
            global_store = np.empty(
                (episodes, turns, global_features.shape[1]),
                dtype=np.float32,
            )
            economic_store = np.empty(
                (episodes, turns, economic.shape[1]),
                dtype=np.int32,
            )
        if unit_store is None or global_store is None or economic_store is None:
            raise RuntimeError("effect teacher rollout storage was not initialized")
        board_store[:, turn] = board
        unit_store[:, turn] = units
        global_store[:, turn] = global_features
        economic_store[:, turn] = economic

        native_batch.reset_transaction()
        per_episode = np.zeros(episodes, dtype=np.int64)
        active = all_rows
        while active.size:
            payload = cast(Mapping[str, Any], native_batch.observe(active))
            fields = np.asarray(payload["candidate_fields"], dtype=np.int64)
            masks = np.asarray(payload["candidate_mask"], dtype=np.bool_)
            policy_factors += int(np.count_nonzero(masks.sum(axis=1) > 1))
            selected = np.asarray(
                [
                    controllers[int(row)].select_work(fields[index], masks[index])
                    for index, row in enumerate(active)
                ],
                dtype=np.int64,
            )
            phases = np.asarray(
                native_batch.advance(
                    selected,
                    np.zeros(active.size, dtype=np.float32),
                    np.zeros(active.size, dtype=np.float32),
                    turn,
                ),
                dtype=np.int64,
            )
            per_episode[active] += 1
            active = active[phases == 0]
            if int(per_episode.max()) > task.unit_limit + 1:
                raise RuntimeError("effect teacher work transaction did not terminate")

        active = all_rows
        while active.size:
            payload = cast(Mapping[str, Any], native_batch.observe(active))
            fields = np.asarray(payload["candidate_fields"], dtype=np.int64)
            masks = np.asarray(payload["candidate_mask"], dtype=np.bool_)
            policy_factors += int(np.count_nonzero(masks.sum(axis=1) > 1))
            selected = np.asarray(
                [
                    controllers[int(row)].select_market(fields[index], masks[index])
                    for index, row in enumerate(active)
                ],
                dtype=np.int64,
            )
            phases = np.asarray(
                native_batch.advance(
                    selected,
                    np.zeros(active.size, dtype=np.float32),
                    np.zeros(active.size, dtype=np.float32),
                    turn,
                ),
                dtype=np.int64,
            )
            per_episode[active] += 1
            active = active[phases != 2]
            if int(per_episode.max()) > task.unit_limit + maximum_market_orders + 2:
                raise RuntimeError("effect teacher market transaction did not terminate")
        maximum_decisions = max(maximum_decisions, int(per_episode.max()))

        compiled = cast(Mapping[str, Any], native_batch.actions())
        tokens = np.asarray(compiled["tokens"], dtype=np.int64)
        quantities = np.asarray(compiled["quantities"], dtype=np.int64)
        counts = np.asarray(compiled["decision_counts"], dtype=np.int64)
        if tokens.shape[1] > action_capacity:
            raise RuntimeError("effect teacher action exceeds actor history capacity")
        action_store[:, turn, : tokens.shape[1]] = tokens
        quantity_store[:, turn, : quantities.shape[1]] = quantities
        action_counts[:, turn] = counts
        _advance(backend, engines, compiled, task.native_workers)

    rollout_seconds = time.perf_counter() - rollout_started
    if not all(bool(engine.done) for engine in engines):
        raise RuntimeError("effect teacher shard did not reach terminal state")
    if any(
        value is None
        for value in (board_store, unit_store, global_store, economic_store)
    ):
        raise RuntimeError("effect teacher shard contains no official turns")
    terminal_cash = np.asarray(
        [
            engine.money(player)
            for engine, player in zip(
                perspective_engines,
                player_list,
                strict=True,
            )
        ],
        dtype=np.float64,
    )
    opponent_cash = np.asarray(
        [
            engine.money(1 - player)
            for engine, player in zip(
                perspective_engines,
                player_list,
                strict=True,
            )
        ],
        dtype=np.float64,
    )
    outcomes = np.sign(terminal_cash - opponent_cash).astype(np.float32)
    route_codes, event_days, route_counts, event_counts = _route_metadata(
        controllers,
        task.route_codes,
    )
    operation_counts: Counter[str] = Counter()
    for controller in controllers:
        operation_counts.update(controller.diagnostics())

    export_started = time.perf_counter()
    decisions = [
        dict(payload)
        for payload in cast(
            Sequence[Mapping[str, Any]],
            native_batch.export_rollout_buckets(),
        )
    ]
    bucket_widths = np.asarray(
        [np.asarray(payload["candidate_fields"]).shape[1] for payload in decisions],
        dtype=np.int32,
    )
    factor_count = sum(int(np.asarray(payload["selected"]).shape[0]) for payload in decisions)
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
    arrays = pack_effect_teacher_arrays(base=base, decisions=decisions)
    task.output_path.parent.mkdir(parents=True, exist_ok=True)
    write_started = time.perf_counter()
    write_compressed_npz(task.output_path, arrays, task.compression_level)
    write_seconds = time.perf_counter() - write_started
    shard = EffectTeacherShard(
        index=task.index,
        path=task.output_path.name,
        seed_start=task.seeds[0],
        games=len(task.seeds),
        physical_games=len(task.seeds),
        episodes=episodes,
        turns_per_episode=turns,
        factors=factor_count,
        policy_factors=policy_factors,
        maximum_transaction_steps=maximum_decisions,
        bucket_widths=tuple(int(value) for value in bucket_widths),
        terminal_cash_sum=float(terminal_cash.sum()),
        opponent_cash_sum=float(opponent_cash.sum()),
        better=int(np.count_nonzero(outcomes > 0)),
        ties=int(np.count_nonzero(outcomes == 0)),
        worse=int(np.count_nonzero(outcomes < 0)),
        size_bytes=task.output_path.stat().st_size,
        sha256=sha256_file(task.output_path),
    )
    return EffectTeacherShardResult(
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
    "EffectTeacherShardResult",
    "EffectTeacherShardTask",
    "generate_effect_teacher_shard",
]
