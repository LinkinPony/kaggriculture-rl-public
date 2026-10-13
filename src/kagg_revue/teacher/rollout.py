"""Bounded-memory native rollouts for an authenticated teacher."""

from __future__ import annotations

import hashlib
import math
import os
import time
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import orjson
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.bc.dataset import sha256_file
from kagg_revue.native import _revue_native as native
from kagg_revue.teacher.config import SubmissionArtifactSettings
from kagg_revue.teacher.npz import write_compressed_npz
from kagg_revue.teacher.submission import (
    SubmissionTeacher,
    load_submission_teacher,
)


@dataclass(frozen=True)
class TeacherShardTask:
    """One deterministic, process-local group of native teacher games."""

    index: int
    seeds: tuple[int, ...]
    output_path: Path
    artifact: SubmissionArtifactSettings
    environment: Mapping[str, object]
    unit_limit: int
    policy_workers: int
    compression_level: int


@dataclass(frozen=True)
class TeacherShardResult:
    """One shard identity and mergeable rollout diagnostics."""

    index: int
    shard: Mapping[str, object]
    games: int
    terminal_cash_sums: tuple[float, float]
    seat_wins: tuple[int, int]
    ties: int
    raw_action_counts: Mapping[int, int]
    action_counts: Mapping[int, int]
    repairs: Mapping[str, int]
    route_counts: Mapping[str, int]
    event_day_counts: Mapping[str, int]
    rollout_seconds: float
    combine_seconds: float
    write_seconds: float
    elapsed_seconds: float


class TeacherShardFile(BaseModel):
    """Authenticated compact shard stored beside a recovery checkpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str
    sequences: int = Field(gt=0)
    turns: int = Field(gt=0)
    decisions: int = Field(gt=0)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class TeacherShardCheckpoint(BaseModel):
    """Durable result needed to skip an authenticated completed shard."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["submission-teacher-shard-checkpoint-v1"]
    task_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    index: int = Field(ge=0)
    seed_start: int = Field(ge=0)
    seed_count: int = Field(gt=0)
    shard: TeacherShardFile
    games: int = Field(gt=0)
    terminal_cash_sums: tuple[float, float]
    seat_wins: tuple[int, int]
    ties: int = Field(ge=0)
    raw_action_counts: dict[int, int]
    action_counts: dict[int, int]
    repairs: dict[str, int]
    route_counts: dict[str, int]
    event_day_counts: dict[str, int]
    rollout_seconds: float = Field(ge=0.0)
    combine_seconds: float = Field(ge=0.0)
    write_seconds: float = Field(ge=0.0)
    elapsed_seconds: float = Field(ge=0.0)

    @model_validator(mode="after")
    def validate_counts(self) -> TeacherShardCheckpoint:
        """Keep game, outcome, and task counts internally consistent."""
        if self.games != self.seed_count:
            raise ValueError("teacher shard game count differs from its seed count")
        if sum(self.seat_wins) + self.ties != self.games:
            raise ValueError("teacher shard outcomes do not cover every game")
        return self

    def result(self) -> TeacherShardResult:
        """Restore the in-memory result used by manifest aggregation."""
        return TeacherShardResult(
            index=self.index,
            shard=self.shard.model_dump(),
            games=self.games,
            terminal_cash_sums=self.terminal_cash_sums,
            seat_wins=self.seat_wins,
            ties=self.ties,
            raw_action_counts=self.raw_action_counts,
            action_counts=self.action_counts,
            repairs=self.repairs,
            route_counts=self.route_counts,
            event_day_counts=self.event_day_counts,
            rollout_seconds=self.rollout_seconds,
            combine_seconds=self.combine_seconds,
            write_seconds=self.write_seconds,
            elapsed_seconds=self.elapsed_seconds,
        )


@dataclass(frozen=True)
class _GameArrays:
    arrays: Mapping[str, NDArray[np.generic]]
    terminal_cash: tuple[float, float]
    winner: int | None
    raw_action_counts: Mapping[int, int]
    action_counts: Mapping[int, int]
    repairs: Mapping[str, int]
    route_counts: Mapping[str, int]
    event_day_counts: Mapping[str, int]


@dataclass
class _WorkerRuntime:
    engine: Any
    teachers: tuple[SubmissionTeacher, SubmissionTeacher]
    codec: ReplayActionEncoder
    keys: tuple[str, ...]
    configuration: dict[str, Any]
    turns: int
    board_shape: tuple[int, int, int, int]
    unit_shape: tuple[int, int, int]
    global_features: int
    max_market_orders: int


_RUNTIME_CACHE: dict[tuple[object, ...], _WorkerRuntime] = {}


def _worker_runtime(task: TeacherShardTask) -> _WorkerRuntime:
    environment_identity = orjson.dumps(task.environment, option=orjson.OPT_SORT_KEYS)
    key = (
        str(task.artifact.archive_path),
        task.artifact.archive_sha256,
        task.artifact.source_commit,
        task.artifact.route_sha256,
        environment_identity,
        task.unit_limit,
    )
    cached = _RUNTIME_CACHE.get(key)
    if cached is not None:
        return cached
    artifact = load_submission_teacher(
        task.artifact.archive_path,
        task.artifact.archive_sha256,
        task.artifact.source_commit,
        task.artifact.route_sha256,
    )
    engine = native.Engine(seed=task.seeds[0], configuration=dict(task.environment))
    configuration = engine.configuration
    encoder_spec = cast(Mapping[str, Any], native.actor_encoder_spec())
    codec_spec = cast(Mapping[str, Any], native.action_codec_spec())
    keys = tuple(str(value) for value in codec_spec["keys"])
    if len(keys) > np.iinfo(np.uint8).max:
        raise ValueError("native action vocabulary exceeds compact uint8 storage")
    board_size = int(configuration["boardSize"])
    runtime = _WorkerRuntime(
        engine=engine,
        teachers=(
            SubmissionTeacher(configuration, artifact),
            SubmissionTeacher(configuration, artifact),
        ),
        codec=ReplayActionEncoder(codec_spec),
        keys=keys,
        configuration=configuration,
        turns=int(configuration["episodeSteps"]) - 1,
        board_shape=(
            2,
            int(encoder_spec["board_channels"]),
            board_size,
            board_size,
        ),
        unit_shape=(2, task.unit_limit, int(encoder_spec["unit_feat"])),
        global_features=int(encoder_spec["global_feat"]),
        max_market_orders=int(configuration["maxMarketOrdersPerTurn"]),
    )
    _RUNTIME_CACHE[key] = runtime
    return runtime


def _live_unit_count(observation: Mapping[str, Any], seat: int) -> int:
    farms = observation.get("farms")
    if not isinstance(farms, list) or len(farms) != 2:
        raise TypeError("teacher observation must contain two farms")
    farm = farms[seat]
    if not isinstance(farm, Mapping):
        raise TypeError("teacher active farm must be a mapping")
    hands = farm.get("hands")
    if not isinstance(hands, list):
        raise TypeError("teacher active farm hands must be a list")
    return 1 + len(hands)


def _canonical_actions(
    batch: Any,
    encoded_actions: list[Any],
    keys: tuple[str, ...],
) -> tuple[list[list[int]], list[list[int]], Counter[int], Counter[str]]:
    """Project physically illegal unit requests to deployment-representable PASS."""
    pass_token = keys.index("UNIT:PASS")
    selected_tokens: list[list[int]] = [[], []]
    selected_quantities: list[list[int]] = [[], []]
    cursors = [0, 0]
    raw_counts: Counter[int] = Counter()
    repairs: Counter[str] = Counter()
    for action in encoded_actions:
        raw_counts.update(action.tokens)
        repairs.update(action.repairs)

    while any(cursors[seat] < encoded_actions[seat].unit_decisions for seat in range(2)):
        phases, legal_masks = batch.decision_inputs()
        phases_array = np.asarray(phases, dtype=np.int64)
        legal_array = np.asarray(legal_masks, dtype=np.uint8)
        tokens = np.full(2, pass_token, dtype=np.int64)
        quantities = np.zeros(2, dtype=np.int64)
        active = np.zeros(2, dtype=np.uint8)
        for seat in range(2):
            action = encoded_actions[seat]
            cursor = cursors[seat]
            if cursor >= action.unit_decisions:
                if int(phases_array[seat]) != 1:
                    raise RuntimeError("teacher unit prefix ended before the policy session")
                continue
            phase = int(phases_array[seat])
            if phase != 0:
                raise RuntimeError("teacher unit prefix and policy-session phases differ")
            token = int(action.tokens[cursor])
            quantity = int(action.quantities[cursor])
            if not legal_array[seat, token]:
                repairs["physically_illegal_unit_requests_to_pass"] += 1
                repairs[f"illegal:{keys[token]}->UNIT:PASS"] += 1
                token = pass_token
                quantity = 0
            tokens[seat] = token
            quantities[seat] = quantity
            active[seat] = 1
            selected_tokens[seat].append(token)
            selected_quantities[seat].append(quantity)
            cursors[seat] += 1
        batch.select(tokens, quantities, active)

    final_phases = np.asarray(batch.phases(), dtype=np.int64)
    if not np.array_equal(final_phases, np.full(2, 1, dtype=np.int64)):
        raise RuntimeError("canonical teacher unit prefix did not complete both seats")
    for seat, action in enumerate(encoded_actions):
        selected_tokens[seat].extend(action.tokens[action.unit_decisions :])
        selected_quantities[seat].extend(action.quantities[action.unit_decisions :])
    return selected_tokens, selected_quantities, raw_counts, repairs


def _episode_arrays(
    *,
    seed: int,
    submission_id: int,
    runtime: _WorkerRuntime,
    unit_limit: int,
    policy_workers: int,
) -> _GameArrays:
    engine = runtime.engine
    engine.reset(seed)
    for teacher in runtime.teachers:
        teacher.reset()
    turns = runtime.turns
    max_market_orders = runtime.max_market_orders
    keys = runtime.keys
    codec = runtime.codec
    board_shape = runtime.board_shape
    unit_shape = runtime.unit_shape
    global_features = runtime.global_features
    board = np.empty((2, turns, *board_shape), dtype=np.float16)
    units = np.empty((2, turns, *unit_shape), dtype=np.float16)
    globals_ = np.empty((2, turns, global_features), dtype=np.float16)
    teachers = runtime.teachers
    per_seat_tokens: list[list[int]] = [[], []]
    per_seat_quantities: list[list[int]] = [[], []]
    per_seat_offsets: list[list[int]] = [[0], [0]]
    per_seat_unit_counts: list[list[int]] = [[], []]
    raw_action_counts: Counter[int] = Counter()
    action_counts: Counter[int] = Counter()
    repairs: Counter[str] = Counter()

    for turn in range(turns):
        observations = [engine.observation(seat) for seat in range(2)]
        live_unit_counts = [_live_unit_count(observations[seat], seat) for seat in range(2)]
        if any(count > unit_limit for count in live_unit_counts):
            raise ValueError("teacher game exceeds the configured actor unit capacity")
        plans = [teachers[seat].plan(observations[seat]) for seat in range(2)]
        repairs["teacher_weed_repairs_started"] += sum(
            int(plan["weed_repairs_started"]) for plan in plans
        )
        batch = native.engine_policy_session_batch(
            [engine, engine], [0, 1], unit_limit, policy_workers
        )
        encoded_board, encoded_units, encoded_global = batch.encode()
        board[:, turn] = np.asarray(encoded_board, dtype=np.float16)
        units[:, turn] = np.asarray(encoded_units, dtype=np.float16)
        globals_[:, turn] = np.asarray(encoded_global, dtype=np.float16)
        session_unit_counts = np.asarray(batch.unit_counts(), dtype=np.int64)
        if not np.array_equal(session_unit_counts, np.asarray(live_unit_counts, dtype=np.int64)):
            raise RuntimeError("native policy session and live unit counts differ")
        encoded_actions = [
            codec.encode(
                cast(Mapping[str, Any], plans[seat]["action"]),
                live_unit_counts[seat],
                max_market_orders,
            )
            for seat in range(2)
        ]
        selected_tokens, selected_quantities, turn_raw_counts, turn_repairs = _canonical_actions(
            batch, encoded_actions, keys
        )
        raw_action_counts.update(turn_raw_counts)
        repairs.update(turn_repairs)
        width = max(len(tokens) for tokens in selected_tokens)
        token_buffer = np.zeros((2, width), dtype=np.int64)
        quantity_buffer = np.zeros((2, width), dtype=np.int64)
        decision_counts = np.empty(2, dtype=np.int64)
        for seat in range(2):
            decision_count = len(selected_tokens[seat])
            token_buffer[seat, :decision_count] = selected_tokens[seat]
            quantity_buffer[seat, :decision_count] = selected_quantities[seat]
            decision_counts[seat] = decision_count
            per_seat_tokens[seat].extend(selected_tokens[seat])
            per_seat_quantities[seat].extend(selected_quantities[seat])
            per_seat_offsets[seat].append(len(per_seat_tokens[seat]))
            per_seat_unit_counts[seat].append(live_unit_counts[seat])
            action_counts.update(selected_tokens[seat])
        engine.step_numeric(
            token_buffer,
            quantity_buffer,
            decision_counts,
            np.asarray(live_unit_counts, dtype=np.int64),
        )

    if not engine.done or engine.step_index != turns:
        raise RuntimeError("teacher rollout did not reach the configured terminal step")
    if not np.isfinite(board).all() or not np.isfinite(units).all():
        raise RuntimeError("teacher rollout produced a non-finite observation tensor")
    if not np.isfinite(globals_).all():
        raise RuntimeError("teacher rollout produced a non-finite global tensor")

    episode_id = f"submission-{submission_id}-seed-{seed}"
    terminal_cash = (float(engine.money(0)), float(engine.money(1)))
    route_metadata = [teachers[seat].metadata() for seat in range(2)]
    route_ids = [str(metadata["route_id"]) for metadata in route_metadata]
    event_days = [
        "none" if metadata["first_event_day"] is None else str(metadata["first_event_day"])
        for metadata in route_metadata
    ]
    route_counts: Counter[str] = Counter(route_ids)
    event_day_counts: Counter[str] = Counter(event_days)
    sequence_offsets = np.arange(0, 3 * turns, turns, dtype=np.int64)
    decision_offsets = [0]
    for offsets in per_seat_offsets:
        base = decision_offsets[-1]
        decision_offsets.extend(base + value for value in offsets[1:])
    tokens = [token for seat_tokens in per_seat_tokens for token in seat_tokens]
    quantities = [
        quantity for seat_quantities in per_seat_quantities for quantity in seat_quantities
    ]
    quantity_small = np.asarray(quantities, dtype=np.float32)
    overflow_indices = [
        index
        for index, (stored, exact) in enumerate(zip(quantity_small, quantities, strict=True))
        if not math.isfinite(float(stored)) or int(stored) != exact
    ]
    quantity_small[overflow_indices] = 0
    if terminal_cash[0] > terminal_cash[1]:
        winner: int | None = 0
    elif terminal_cash[1] > terminal_cash[0]:
        winner = 1
    else:
        winner = None
    arrays: dict[str, NDArray[np.generic]] = {
        "episode_id": np.asarray([episode_id, episode_id], dtype=np.str_),
        "seat": np.asarray([0, 1], dtype=np.uint8),
        "seed": np.asarray([seed, seed], dtype=np.int64),
        "teacher_route_id": np.asarray(route_ids, dtype=np.str_),
        "terminal_cash": np.asarray(terminal_cash, dtype=np.float64),
        "sequence_offsets": sequence_offsets,
        "board": board.reshape(2 * turns, *board_shape),
        "units": units.reshape(2 * turns, *unit_shape),
        "global_features": globals_.reshape(2 * turns, global_features),
        "turn_decision_offsets": np.asarray(decision_offsets, dtype=np.int64),
        "unit_decisions": np.asarray(
            [count for seat_counts in per_seat_unit_counts for count in seat_counts],
            dtype=np.uint8,
        ),
        "action_token": np.asarray(tokens, dtype=np.uint8),
        "quantity_small": quantity_small,
        "quantity_overflow_index": np.asarray(overflow_indices, dtype=np.int64),
        "quantity_overflow_decimal": np.asarray(
            [str(quantities[index]) for index in overflow_indices], dtype=np.str_
        ),
    }
    return _GameArrays(
        arrays=arrays,
        terminal_cash=terminal_cash,
        winner=winner,
        raw_action_counts=dict(raw_action_counts),
        action_counts=dict(action_counts),
        repairs=dict(repairs),
        route_counts=dict(route_counts),
        event_day_counts=dict(event_day_counts),
    )


def _combine(games: list[_GameArrays]) -> dict[str, NDArray[np.generic]]:
    sequence_offsets = [0]
    decision_offsets = [0]
    overflow_indices: list[int] = []
    overflow_decimals: list[str] = []
    action_base = 0
    for game in games:
        arrays = game.arrays
        sequence_base = sequence_offsets[-1]
        sequence_offsets.extend(
            sequence_base + int(value) for value in np.asarray(arrays["sequence_offsets"])[1:]
        )
        decision_base = decision_offsets[-1]
        decision_offsets.extend(
            decision_base + int(value) for value in np.asarray(arrays["turn_decision_offsets"])[1:]
        )
        overflow_indices.extend(
            action_base + int(value) for value in np.asarray(arrays["quantity_overflow_index"])
        )
        overflow_decimals.extend(
            str(value) for value in np.asarray(arrays["quantity_overflow_decimal"])
        )
        action_base += int(np.asarray(arrays["action_token"]).size)
    concatenated = {
        name: np.concatenate([np.asarray(game.arrays[name]) for game in games])
        for name in (
            "episode_id",
            "seat",
            "seed",
            "teacher_route_id",
            "terminal_cash",
            "board",
            "units",
            "global_features",
            "unit_decisions",
            "action_token",
            "quantity_small",
        )
    }
    concatenated["sequence_offsets"] = np.asarray(sequence_offsets, dtype=np.int64)
    concatenated["turn_decision_offsets"] = np.asarray(decision_offsets, dtype=np.int64)
    concatenated["quantity_overflow_index"] = np.asarray(overflow_indices, dtype=np.int64)
    concatenated["quantity_overflow_decimal"] = np.asarray(overflow_decimals, dtype=np.str_)
    return concatenated


def _merge_counter(games: list[_GameArrays], field: str) -> dict[Any, int]:
    values: Counter[Any] = Counter()
    for game in games:
        value = getattr(game, field)
        if not isinstance(value, Mapping):
            raise TypeError(f"game diagnostic {field} must be a mapping")
        values.update(value)
    return dict(values)


def _task_fingerprint(task: TeacherShardTask) -> str:
    payload = {
        "index": task.index,
        "seeds": task.seeds,
        "artifact": task.artifact.model_dump(mode="json"),
        "environment": dict(task.environment),
        "unit_limit": task.unit_limit,
        "policy_workers": task.policy_workers,
        "compression_level": task.compression_level,
    }
    return hashlib.sha256(orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)).hexdigest()


def teacher_shard_checkpoint_path(output_path: Path) -> Path:
    """Return the durable checkpoint path paired with an NPZ shard."""
    return output_path.with_suffix(".result.json")


def _write_checkpoint(task: TeacherShardTask, result: TeacherShardResult) -> TeacherShardCheckpoint:
    checkpoint = TeacherShardCheckpoint(
        schema_version="submission-teacher-shard-checkpoint-v1",
        task_fingerprint=_task_fingerprint(task),
        index=task.index,
        seed_start=task.seeds[0],
        seed_count=len(task.seeds),
        shard=TeacherShardFile.model_validate(result.shard),
        games=result.games,
        terminal_cash_sums=result.terminal_cash_sums,
        seat_wins=result.seat_wins,
        ties=result.ties,
        raw_action_counts=dict(result.raw_action_counts),
        action_counts=dict(result.action_counts),
        repairs=dict(result.repairs),
        route_counts=dict(result.route_counts),
        event_day_counts=dict(result.event_day_counts),
        rollout_seconds=result.rollout_seconds,
        combine_seconds=result.combine_seconds,
        write_seconds=result.write_seconds,
        elapsed_seconds=result.elapsed_seconds,
    )
    path = teacher_shard_checkpoint_path(task.output_path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    payload = orjson.dumps(checkpoint.model_dump(mode="json"), option=orjson.OPT_SORT_KEYS)
    with temporary.open("wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    return checkpoint


def load_teacher_shard_checkpoint(
    task: TeacherShardTask,
) -> TeacherShardResult | None:
    """Load a matching completed shard, or request regeneration if data is absent."""
    path = teacher_shard_checkpoint_path(task.output_path)
    if not path.is_file():
        return None
    checkpoint = TeacherShardCheckpoint.model_validate_json(path.read_bytes())
    if checkpoint.index != task.index:
        raise ValueError(f"teacher shard checkpoint index differs: {path}")
    if checkpoint.task_fingerprint != _task_fingerprint(task):
        raise ValueError(f"teacher shard checkpoint task differs: {path}")
    if checkpoint.seed_start != task.seeds[0] or checkpoint.seed_count != len(task.seeds):
        raise ValueError(f"teacher shard checkpoint seed range differs: {path}")
    shard_path = task.output_path
    shard = checkpoint.shard
    if shard.path != shard_path.name:
        raise ValueError(f"teacher shard checkpoint filename differs: {path}")
    if not shard_path.is_file() or shard_path.stat().st_size != shard.size_bytes:
        return None
    if sha256_file(shard_path) != shard.sha256:
        return None
    return checkpoint.result()


def generate_teacher_shard(task: TeacherShardTask) -> TeacherShardResult:
    """Generate one compact shard directly from native closed-loop games."""
    started = time.perf_counter()
    runtime = _worker_runtime(task)
    games = [
        _episode_arrays(
            seed=seed,
            submission_id=task.artifact.submission_id,
            runtime=runtime,
            unit_limit=task.unit_limit,
            policy_workers=task.policy_workers,
        )
        for seed in task.seeds
    ]
    rollout_seconds = time.perf_counter() - started
    combine_started = time.perf_counter()
    arrays = _combine(games)
    combine_seconds = time.perf_counter() - combine_started
    write_started = time.perf_counter()
    write_compressed_npz(task.output_path, arrays, task.compression_level)
    write_seconds = time.perf_counter() - write_started
    elapsed_seconds = time.perf_counter() - started
    shard: Mapping[str, object] = {
        "path": task.output_path.name,
        "sequences": int(np.asarray(arrays["episode_id"]).size),
        "turns": int(np.asarray(arrays["board"]).shape[0]),
        "decisions": int(np.asarray(arrays["action_token"]).size),
        "size_bytes": task.output_path.stat().st_size,
        "sha256": sha256_file(task.output_path),
    }
    result = TeacherShardResult(
        index=task.index,
        shard=shard,
        games=len(games),
        terminal_cash_sums=(
            sum(game.terminal_cash[0] for game in games),
            sum(game.terminal_cash[1] for game in games),
        ),
        seat_wins=(
            sum(game.winner == 0 for game in games),
            sum(game.winner == 1 for game in games),
        ),
        ties=sum(game.winner is None for game in games),
        raw_action_counts=cast(Mapping[int, int], _merge_counter(games, "raw_action_counts")),
        action_counts=cast(Mapping[int, int], _merge_counter(games, "action_counts")),
        repairs=cast(Mapping[str, int], _merge_counter(games, "repairs")),
        route_counts=cast(Mapping[str, int], _merge_counter(games, "route_counts")),
        event_day_counts=cast(Mapping[str, int], _merge_counter(games, "event_day_counts")),
        rollout_seconds=rollout_seconds,
        combine_seconds=combine_seconds,
        write_seconds=write_seconds,
        elapsed_seconds=elapsed_seconds,
    )
    _write_checkpoint(task, result)
    return result


__all__ = [
    "TeacherShardCheckpoint",
    "TeacherShardResult",
    "TeacherShardTask",
    "generate_teacher_shard",
    "load_teacher_shard_checkpoint",
    "teacher_shard_checkpoint_path",
]
