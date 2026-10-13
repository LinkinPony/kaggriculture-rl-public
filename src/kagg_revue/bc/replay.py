"""Bounded-memory conversion of Kaggle replays into compact shards."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import zipfile
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import orjson
from numpy.typing import NDArray

from kagg_revue.bc.actions import (
    ActionEncodingError,
    EncodedTurnAction,
    ReplayActionEncoder,
)
from kagg_revue.bc.data_config import ReplayContract
from kagg_revue.bc.dataset import sha256_file
from kagg_revue.native import _revue_native as native
from kagg_revue.policy.economics import EconomicStateLayout


class ReplayRejected(ValueError):
    """A stable data-quality rejection with a human-readable detail."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


ACTION_TARGET_CANONICALIZATION = "observable-sell-limit-v1"


@dataclass(frozen=True)
class EpisodeLocator:
    """One JSON member inside an authenticated daily source archive."""

    archive: Path
    entry: str
    source_date: str
    create_time: str
    average_score: float
    minimum_score: float


@dataclass(frozen=True)
class ShardTask:
    """A deterministic bounded group converted by one worker process."""

    index: int
    episodes: tuple[EpisodeLocator, ...]
    output_path: Path
    contract: ReplayContract
    maximum_turns: int | None = None


@dataclass(frozen=True)
class ShardResult:
    """Compact shard identity plus mergeable analysis statistics."""

    index: int
    shard: Mapping[str, object] | None
    sequences: tuple[Mapping[str, object], ...]
    rejected: tuple[Mapping[str, str], ...]
    action_counts: Mapping[int, int]
    repairs: Mapping[str, int]
    unit_histogram: Mapping[int, int]
    market_histogram: Mapping[int, int]
    decision_histogram: Mapping[int, int]
    quantity_histogram: Mapping[int, int]


@dataclass(frozen=True)
class _EpisodeArrays:
    arrays: Mapping[str, NDArray[np.generic]]
    sequences: tuple[Mapping[str, object], ...]
    action_counts: Mapping[int, int]
    repairs: Mapping[str, int]
    unit_histogram: Mapping[int, int]
    market_histogram: Mapping[int, int]
    decision_histogram: Mapping[int, int]
    quantity_histogram: Mapping[int, int]


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ReplayRejected("invalid_schema", f"{field} must be a mapping")
    return cast(Mapping[str, Any], value)


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ReplayRejected("invalid_schema", f"{field} must be a list")
    return value


def _integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ReplayRejected("invalid_schema", f"{field} must be an integer")
    return value


def _source_episode_id(replay: Mapping[str, Any], locator: EpisodeLocator) -> str:
    info = _mapping(replay.get("info"), "info")
    episode_id = _integer(info.get("EpisodeId"), "info.EpisodeId")
    if Path(locator.entry).stem != str(episode_id):
        raise ReplayRejected("identity_mismatch", "entry name and EpisodeId differ")
    return str(episode_id)


def _agent_names(replay: Mapping[str, Any], agents: int) -> tuple[str, ...]:
    info = _mapping(replay.get("info"), "info")
    raw_agents = info.get("Agents")
    names: list[str] = []
    if isinstance(raw_agents, list) and len(raw_agents) == agents:
        for index, raw_agent in enumerate(raw_agents):
            agent = _mapping(raw_agent, f"info.Agents[{index}]")
            value = agent.get("Name")
            names.append(value if isinstance(value, str) and value else "unknown")
    else:
        raw_names = info.get("TeamNames")
        if not isinstance(raw_names, list) or len(raw_names) != agents:
            raise ReplayRejected("invalid_schema", "replay lacks agent display names")
        names = [name if isinstance(name, str) and name else "unknown" for name in raw_names]
    return tuple(names)


def _validate_header(
    replay: Mapping[str, Any], locator: EpisodeLocator, contract: ReplayContract
) -> tuple[str, Mapping[str, Any], list[Any], tuple[float, ...], tuple[str, ...]]:
    if replay.get("name") != "kaggriculture":
        raise ReplayRejected("wrong_environment", "replay environment is not kaggriculture")
    if replay.get("schema_version") != contract.replay_schema_version:
        raise ReplayRejected("wrong_replay_schema", "replay schema version differs")
    if replay.get("module_version") != contract.module_version:
        raise ReplayRejected("wrong_module_version", "environment module version differs")
    configuration = _mapping(replay.get("configuration"), "configuration")
    expected_configuration = {
        "episodeSteps": contract.episode_steps,
        "boardSize": contract.board_size,
        "maxMarketOrdersPerTurn": contract.max_market_orders,
    }
    for key, expected in expected_configuration.items():
        if configuration.get(key) != expected:
            raise ReplayRejected("wrong_configuration", f"configuration.{key} differs")

    steps = _list(replay.get("steps"), "steps")
    if len(steps) != contract.episode_steps:
        raise ReplayRejected("incomplete_episode", "step count differs from episodeSteps")
    statuses = _list(replay.get("statuses"), "statuses")
    if statuses != ["DONE"] * contract.agents:
        raise ReplayRejected("incomplete_episode", "terminal statuses are not all DONE")
    raw_rewards = _list(replay.get("rewards"), "rewards")
    if len(raw_rewards) != contract.agents:
        raise ReplayRejected("invalid_schema", "reward count differs from agent count")
    rewards: list[float] = []
    for value in raw_rewards:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ReplayRejected("invalid_reward", "terminal reward is not numeric")
        reward = float(value)
        if not math.isfinite(reward):
            raise ReplayRejected("invalid_reward", "terminal reward is not finite")
        rewards.append(reward)
    return (
        _source_episode_id(replay, locator),
        configuration,
        steps,
        tuple(rewards),
        _agent_names(replay, contract.agents),
    )


def _quantity_bucket(quantity: int) -> int:
    return quantity.bit_length() - 1 if quantity > 0 else -1


def _canonicalize_observable_sell_quantities(
    action: EncodedTurnAction,
    observation: Mapping[str, Any],
    configuration: Mapping[str, Any],
    codec: ReplayActionEncoder,
) -> EncodedTurnAction:
    """Replace sell-request conventions with their observable effect.

    A positive SELL request above the post-unit shed stock is equivalent to
    selling that stock: official settlement partially fills it and cannot be
    affected by hidden opponent inventory. A SELL with no stock is an
    observable no-op and becomes an explicit skipped market slot. This keeps
    behavior targets causal while removing arbitrary values such as 999.
    """
    if not any(codec.keys[token].startswith("MARKET:SELL:") for token in action.tokens):
        return action
    builder = native.NativeOfficialActionBuilder(dict(observation), dict(configuration))
    skip_token = codec.keys.index("MARKET:SKIP_SLOT")
    tokens = list(action.tokens)
    quantities = list(action.quantities)
    repairs = Counter(action.repairs)
    for index, (token, raw_quantity) in enumerate(
        zip(action.tokens, action.quantities, strict=True)
    ):
        key = codec.keys[token]
        selected_token = token
        selected_quantity = raw_quantity
        if key.startswith("MARKET:SELL:"):
            item = key.rsplit(":", maxsplit=1)[1]
            local_state = _mapping(builder.local_state(), "official action local state")
            private = _mapping(local_state.get("private"), "official action private state")
            shed = _mapping(private.get("shed"), "official action shed")
            available = _integer(shed.get(item), f"official action shed.{item}")
            if available < 0:
                raise ReplayRejected(
                    "invalid_observation", "observable shed stock cannot be negative"
                )
            if available == 0:
                selected_token = skip_token
                selected_quantity = 0
                repairs["empty_sell_requests_to_skip"] += 1
            elif raw_quantity > available:
                selected_quantity = available
                repairs["sell_quantities_capped_to_observable_stock"] += 1
        tokens[index] = selected_token
        quantities[index] = selected_quantity
        builder.select(
            codec.keys[selected_token],
            selected_quantity if selected_quantity > 0 else None,
        )
    return EncodedTurnAction(
        tokens=tuple(tokens),
        quantities=tuple(quantities),
        unit_decisions=action.unit_decisions,
        market_orders=action.market_orders,
        repairs=dict(repairs),
    )


def _encode_episode(
    replay: Mapping[str, Any],
    locator: EpisodeLocator,
    contract: ReplayContract,
    maximum_turns: int | None,
) -> _EpisodeArrays:
    episode_id, configuration, steps, rewards, agent_names = _validate_header(
        replay, locator, contract
    )
    configuration_dict = dict(configuration)
    codec = ReplayActionEncoder(cast(Mapping[str, Any], native.action_codec_spec()))
    encoder = cast(Mapping[str, Any], native.actor_encoder_spec())
    available_turns = contract.episode_steps - 1
    turns = available_turns if maximum_turns is None else min(maximum_turns, available_turns)
    board_shape = (
        2,
        int(encoder["board_channels"]),
        contract.board_size,
        contract.board_size,
    )
    unit_shape = (2, contract.unit_limit, int(encoder["unit_feat"]))
    global_features = int(encoder["global_feat"])
    economic_layout = EconomicStateLayout.from_spec(
        cast(
            Mapping[str, int],
            native.gpu_policy_state_spec(contract.board_size, contract.unit_limit),
        ),
        board_size=contract.board_size,
        unit_limit=contract.unit_limit,
    )
    board = np.empty((contract.agents, turns, *board_shape), dtype=np.float16)
    units = np.empty((contract.agents, turns, *unit_shape), dtype=np.float16)
    globals_ = np.empty((contract.agents, turns, global_features), dtype=np.float16)
    economic_state = np.empty(
        (contract.agents, turns, economic_layout.width),
        dtype=np.int32,
    )
    per_seat_tokens: list[list[int]] = [[] for _ in range(contract.agents)]
    per_seat_quantities: list[list[int]] = [[] for _ in range(contract.agents)]
    per_seat_offsets: list[list[int]] = [[0] for _ in range(contract.agents)]
    per_seat_unit_counts: list[list[int]] = [[] for _ in range(contract.agents)]
    action_counts: Counter[int] = Counter()
    repairs: Counter[str] = Counter()
    unit_histogram: Counter[int] = Counter()
    market_histogram: Counter[int] = Counter()
    decision_histogram: Counter[int] = Counter()
    quantity_histogram: Counter[int] = Counter()
    minimum_overage = [math.inf] * contract.agents

    for turn in range(turns):
        source_step = _list(steps[turn], f"steps[{turn}]")
        target_step = _list(steps[turn + 1], f"steps[{turn + 1}]")
        if len(source_step) != contract.agents or len(target_step) != contract.agents:
            raise ReplayRejected("invalid_schema", "step agent count differs")
        for seat in range(contract.agents):
            source_state = _mapping(source_step[seat], f"steps[{turn}][{seat}]")
            if source_state.get("status") != "ACTIVE":
                raise ReplayRejected("inactive_source_turn", "source decision status is not ACTIVE")
            raw_observation = _mapping(
                source_state.get("observation"), f"steps[{turn}][{seat}].observation"
            )
            observation = dict(raw_observation)
            player = _integer(observation.get("player"), "observation.player")
            if player != seat:
                raise ReplayRejected("seat_mismatch", "observation player differs from seat")
            observed_step = observation.get("step")
            if observed_step is not None and observed_step != turn:
                raise ReplayRejected("turn_mismatch", "observation step differs from replay index")
            if observed_step is None:
                observation["step"] = turn
            farms = _list(observation.get("farms"), "observation.farms")
            if len(farms) != contract.agents:
                raise ReplayRejected("invalid_schema", "observation farm count differs")
            own_farm = _mapping(farms[player], "observation own farm")
            hands = _list(own_farm.get("hands"), "observation own hands")
            unit_count = 1 + len(hands)
            if unit_count > contract.unit_limit:
                raise ReplayRejected("unit_limit_exceeded", "visible units exceed actor capacity")

            try:
                encoded = native.encode_official_observation_numeric(
                    observation,
                    configuration_dict,
                    contract.unit_limit,
                )
            except (KeyError, TypeError, ValueError, RuntimeError) as error:
                raise ReplayRejected(
                    "observation_encoding_failed",
                    f"native observation encoder failed: {type(error).__name__}: {error}",
                ) from error
            board[seat, turn] = np.asarray(encoded[0], dtype=np.float16)
            units[seat, turn] = np.asarray(encoded[1], dtype=np.float16)
            globals_[seat, turn] = np.asarray(encoded[2], dtype=np.float16)
            try:
                policy_session = native.PolicySession(
                    observation,
                    configuration_dict,
                    contract.unit_limit,
                )
                raw_economic_state = np.asarray(policy_session.gpu_state(), dtype=np.int64)
            except (KeyError, TypeError, ValueError, RuntimeError) as error:
                raise ReplayRejected(
                    "economic_state_encoding_failed",
                    f"native economic state encoder failed: {type(error).__name__}: {error}",
                ) from error
            if raw_economic_state.shape != (economic_layout.width,):
                raise ReplayRejected(
                    "economic_state_encoding_failed",
                    "native economic state has the wrong width",
                )
            if np.any(raw_economic_state < np.iinfo(np.int32).min) or np.any(
                raw_economic_state > np.iinfo(np.int32).max
            ):
                raise ReplayRejected(
                    "economic_state_encoding_failed",
                    "native economic state exceeds compact int32 storage",
                )
            economic_state[seat, turn] = raw_economic_state.astype(np.int32)

            target_state = _mapping(target_step[seat], f"steps[{turn + 1}][{seat}]")
            try:
                action = codec.encode(
                    target_state.get("action"),
                    unit_count,
                    contract.max_market_orders,
                )
            except ActionEncodingError as error:
                raise ReplayRejected("invalid_action", str(error)) from error
            try:
                action = _canonicalize_observable_sell_quantities(
                    action,
                    observation,
                    configuration,
                    codec,
                )
            except (KeyError, TypeError, ValueError, RuntimeError) as error:
                raise ReplayRejected(
                    "action_canonicalization_failed",
                    f"observable action canonicalization failed: "
                    f"{type(error).__name__}: {error}",
                ) from error
            per_seat_tokens[seat].extend(action.tokens)
            per_seat_quantities[seat].extend(action.quantities)
            per_seat_offsets[seat].append(len(per_seat_tokens[seat]))
            per_seat_unit_counts[seat].append(action.unit_decisions)
            action_counts.update(action.tokens)
            repairs.update(action.repairs)
            unit_histogram[action.unit_decisions] += 1
            market_histogram[action.market_orders] += 1
            decision_histogram[len(action.tokens)] += 1
            quantity_histogram.update(_quantity_bucket(value) for value in action.quantities)
            overage = observation.get("remainingOverageTime")
            if isinstance(overage, (int, float)) and not isinstance(overage, bool):
                minimum_overage[seat] = min(minimum_overage[seat], float(overage))

    if (
        not np.isfinite(board).all()
        or not np.isfinite(units).all()
        or not np.isfinite(globals_).all()
    ):
        raise ReplayRejected("nonfinite_observation", "encoded observation contains NaN or Inf")

    sequence_offsets = np.arange(0, (contract.agents + 1) * turns, turns, dtype=np.int64)
    decision_offsets = [0]
    for offsets in per_seat_offsets:
        base = decision_offsets[-1]
        decision_offsets.extend(base + value for value in offsets[1:])
    tokens = [token for seat_tokens in per_seat_tokens for token in seat_tokens]
    quantities = [
        quantity for seat_quantities in per_seat_quantities for quantity in seat_quantities
    ]
    unit_counts = [count for seat_counts in per_seat_unit_counts for count in seat_counts]
    sequences: list[Mapping[str, object]] = []
    for seat in range(contract.agents):
        sequences.append(
            {
                "episode_id": episode_id,
                "source_date": locator.source_date,
                "source_create_time": locator.create_time,
                "source_average_score": locator.average_score,
                "source_minimum_score": locator.minimum_score,
                "seat": seat,
                "agent_name": agent_names[seat],
                "opponent_name": agent_names[1 - seat],
                "terminal_cash": rewards[seat],
                "opponent_cash": rewards[1 - seat],
                "margin": rewards[seat] - rewards[1 - seat],
                "turns": turns,
                "decisions": len(per_seat_tokens[seat]),
                "minimum_remaining_overage": (
                    minimum_overage[seat] if math.isfinite(minimum_overage[seat]) else None
                ),
            }
        )
    arrays: dict[str, NDArray[np.generic]] = {
        "episode_id": np.asarray([episode_id] * contract.agents, dtype=np.str_),
        "seat": np.arange(contract.agents, dtype=np.uint8),
        "source_date": np.asarray([locator.source_date] * contract.agents, dtype=np.str_),
        "source_create_time": np.asarray([locator.create_time] * contract.agents, dtype=np.str_),
        "source_average_score": np.full(contract.agents, locator.average_score, dtype=np.float32),
        "source_minimum_score": np.full(contract.agents, locator.minimum_score, dtype=np.float32),
        "agent_name": np.asarray(agent_names, dtype=np.str_),
        "terminal_cash": np.asarray(rewards, dtype=np.float64),
        "sequence_offsets": sequence_offsets,
        "board": board.reshape(contract.agents * turns, *board_shape),
        "units": units.reshape(contract.agents * turns, *unit_shape),
        "global_features": globals_.reshape(contract.agents * turns, global_features),
        "economic_state": economic_state.reshape(
            contract.agents * turns,
            economic_layout.width,
        ),
        "turn_decision_offsets": np.asarray(decision_offsets, dtype=np.int64),
        "unit_decisions": np.asarray(unit_counts, dtype=np.uint8),
        "action_token": np.asarray(tokens, dtype=np.uint8),
        "quantity_small": np.asarray(quantities, dtype=np.float32),
        "quantity_overflow_index": np.empty(0, dtype=np.int64),
        "quantity_overflow_decimal": np.empty(0, dtype=np.str_),
    }
    return _EpisodeArrays(
        arrays=arrays,
        sequences=tuple(sequences),
        action_counts=dict(action_counts),
        repairs=dict(repairs),
        unit_histogram=dict(unit_histogram),
        market_histogram=dict(market_histogram),
        decision_histogram=dict(decision_histogram),
        quantity_histogram=dict(quantity_histogram),
    )


def _combine(episodes: list[_EpisodeArrays]) -> dict[str, NDArray[np.generic]]:
    sequence_offsets = [0]
    decision_offsets = [0]
    for episode in episodes:
        arrays = episode.arrays
        sequence_base = sequence_offsets[-1]
        sequence_offsets.extend(
            sequence_base + int(value) for value in np.asarray(arrays["sequence_offsets"])[1:]
        )
        decision_base = decision_offsets[-1]
        decision_offsets.extend(
            decision_base + int(value) for value in np.asarray(arrays["turn_decision_offsets"])[1:]
        )
    concatenated = {
        name: np.concatenate([np.asarray(episode.arrays[name]) for episode in episodes])
        for name in (
            "episode_id",
            "seat",
            "source_date",
            "source_create_time",
            "source_average_score",
            "source_minimum_score",
            "agent_name",
            "terminal_cash",
            "board",
            "units",
            "global_features",
            "economic_state",
            "unit_decisions",
            "action_token",
            "quantity_small",
            "quantity_overflow_index",
            "quantity_overflow_decimal",
        )
    }
    concatenated["sequence_offsets"] = np.asarray(sequence_offsets, dtype=np.int64)
    concatenated["turn_decision_offsets"] = np.asarray(decision_offsets, dtype=np.int64)
    return concatenated


def _merge_counter(target: Counter[Any], values: Mapping[Any, int]) -> None:
    target.update(values)


def prepare_shard(task: ShardTask) -> ShardResult:
    """Convert one deterministic source group and atomically write its NPZ shard."""
    accepted: list[_EpisodeArrays] = []
    rejected: list[Mapping[str, str]] = []
    action_counts: Counter[int] = Counter()
    repairs: Counter[str] = Counter()
    unit_histogram: Counter[int] = Counter()
    market_histogram: Counter[int] = Counter()
    decision_histogram: Counter[int] = Counter()
    quantity_histogram: Counter[int] = Counter()

    by_archive: dict[Path, list[EpisodeLocator]] = {}
    for locator in task.episodes:
        by_archive.setdefault(locator.archive, []).append(locator)
    for archive_path, locators in by_archive.items():
        with zipfile.ZipFile(archive_path) as archive:
            for locator in locators:
                try:
                    with archive.open(locator.entry) as stream:
                        replay = orjson.loads(stream.read())
                    converted = _encode_episode(
                        _mapping(replay, "replay"),
                        locator,
                        task.contract,
                        task.maximum_turns,
                    )
                except ReplayRejected as error:
                    rejected.append(
                        {
                            "archive": archive_path.name,
                            "entry": locator.entry,
                            "reason": error.reason,
                            "detail": error.detail,
                        }
                    )
                    continue
                except orjson.JSONDecodeError as error:
                    rejected.append(
                        {
                            "archive": archive_path.name,
                            "entry": locator.entry,
                            "reason": "invalid_json",
                            "detail": str(error),
                        }
                    )
                    continue
                accepted.append(converted)
                _merge_counter(action_counts, converted.action_counts)
                _merge_counter(repairs, converted.repairs)
                _merge_counter(unit_histogram, converted.unit_histogram)
                _merge_counter(market_histogram, converted.market_histogram)
                _merge_counter(decision_histogram, converted.decision_histogram)
                _merge_counter(quantity_histogram, converted.quantity_histogram)

    shard: Mapping[str, object] | None = None
    if accepted:
        arrays = _combine(accepted)
        temporary = task.output_path.with_suffix(".npz.tmp")
        with temporary.open("wb") as stream:
            np.savez_compressed(stream, **cast(dict[str, Any], arrays))
        temporary.replace(task.output_path)
        shard = {
            "path": task.output_path.name,
            "sequences": int(np.asarray(arrays["episode_id"]).size),
            "turns": int(np.asarray(arrays["board"]).shape[0]),
            "decisions": int(np.asarray(arrays["action_token"]).size),
            "size_bytes": task.output_path.stat().st_size,
            "sha256": sha256_file(task.output_path),
        }
    return ShardResult(
        index=task.index,
        shard=shard,
        sequences=tuple(sequence for episode in accepted for sequence in episode.sequences),
        rejected=tuple(rejected),
        action_counts=dict(action_counts),
        repairs=dict(repairs),
        unit_histogram=dict(unit_histogram),
        market_histogram=dict(market_histogram),
        decision_histogram=dict(decision_histogram),
        quantity_histogram=dict(quantity_histogram),
    )


def archive_identity(path: Path) -> dict[str, object]:
    """Authenticate a daily ZIP and summarize members without extracting them."""
    with zipfile.ZipFile(path) as archive:
        members = [info for info in archive.infolist() if not info.is_dir()]
        json_members = [info for info in members if info.filename.endswith(".json")]
        manifest_members = [info for info in members if info.filename == "manifest.csv"]
        invalid = [
            info.filename
            for info in members
            if not info.filename.endswith(".json") and info.filename != "manifest.csv"
        ]
        if invalid or len(manifest_members) != 1:
            raise ValueError("daily archive must contain JSON episodes and one manifest.csv")
        with archive.open(manifest_members[0]) as stream:
            manifest_bytes = stream.read()
        return {
            "path": str(path),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "members": len(json_members),
            "uncompressed_bytes": sum(info.file_size for info in json_members),
            "compressed_member_bytes": sum(info.compress_size for info in json_members),
            "daily_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "daily_manifest_size_bytes": len(manifest_bytes),
        }


def daily_episode_metadata(path: Path) -> dict[str, dict[str, object]]:
    """Validate and return the rating metadata shipped beside daily episodes."""
    with zipfile.ZipFile(path) as archive:
        json_sizes = {
            Path(info.filename).stem: info.file_size
            for info in archive.infolist()
            if not info.is_dir() and info.filename.endswith(".json")
        }
        with archive.open("manifest.csv") as raw_stream:
            stream = io.TextIOWrapper(raw_stream, encoding="utf-8", newline="")
            rows = list(csv.DictReader(stream))
    metadata: dict[str, dict[str, object]] = {}
    for row in rows:
        try:
            episode_id = row["episode_id"]
            value: dict[str, object] = {
                "create_time": row["create_time"],
                "average_score": float(row["avg_score"]),
                "minimum_score": float(row["min_score"]),
                "sum_score": float(row["sum_score"]),
                "agent_count": int(row["agent_count"]),
                "size_bytes": int(row["size_bytes"]),
            }
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("daily episode manifest contains an invalid row") from error
        if episode_id in metadata:
            raise ValueError("daily episode manifest repeats an episode ID")
        metadata[episode_id] = value
    if set(metadata) != set(json_sizes):
        raise ValueError("daily episode manifest and JSON members differ")
    for episode_id, value in metadata.items():
        if value["size_bytes"] != json_sizes[episode_id]:
            raise ValueError("daily episode manifest size differs from ZIP member")
    return metadata


def source_fingerprint(identities: list[Mapping[str, object]]) -> str:
    """Return a stable identity for an ordered authenticated archive set."""
    digest = hashlib.sha256()
    for identity in identities:
        digest.update(str(identity["sha256"]).encode())
        digest.update(b"\0")
    return digest.hexdigest()


__all__ = [
    "ACTION_TARGET_CANONICALIZATION",
    "EpisodeLocator",
    "ShardResult",
    "ShardTask",
    "archive_identity",
    "daily_episode_metadata",
    "prepare_shard",
    "source_fingerprint",
]
