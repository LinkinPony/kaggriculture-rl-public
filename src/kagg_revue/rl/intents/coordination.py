"""Distributed aggregation and restart state for intent-ledger PPO."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict, cast

import numpy as np

from kagg_revue.rl.distributed import DistributedContext, even_shard
from kagg_revue.rl.intents.rollout import IntentRolloutResult

_DISTRIBUTED_RNG_VERSION = "canonical-intent-distributed-rng-v1"


class IntentRolloutPayload(TypedDict):
    """Small rank-local rollout summary safe to gather through NCCL."""

    rank: int
    device: str
    diagnostics: dict[str, object]
    games: list[dict[str, int | float | str]]


def local_seeds(seeds: Sequence[int], context: DistributedContext) -> tuple[int, ...]:
    """Assign complete physical games to one rank without splitting seats."""
    indices = even_shard(len(seeds), context.rank, context.world_size)
    return tuple(int(seeds[index]) for index in indices)


def rollout_payload(
    rollout: IntentRolloutResult, context: DistributedContext
) -> IntentRolloutPayload:
    """Pack only diagnostics and direct outcomes for cross-rank aggregation."""
    return {
        "rank": context.rank,
        "device": str(context.device),
        "diagnostics": dict(rollout.diagnostics),
        "games": [
            {
                "episode_id": game.episode_id,
                "seed": game.seed,
                "seat": game.seat,
                "outcome": game.outcome,
                "terminal_cash": game.terminal_cash,
                "opponent_cash": game.opponent_cash,
            }
            for game in rollout.games
        ],
    }


def _number(values: Mapping[str, object], name: str) -> float:
    value = values.get(name)
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"intent rollout diagnostic {name} is not numeric")
    return float(value)


def aggregate_rollouts(
    payloads: Sequence[IntentRolloutPayload],
) -> tuple[dict[str, object], list[dict[str, int | float | str]]]:
    """Combine rank-local throughput and outcome rows at an update boundary."""
    if not payloads:
        raise ValueError("intent distributed rollout produced no rank payloads")
    diagnostics = [payload["diagnostics"] for payload in payloads]
    summed = (
        "physical_games",
        "episodes",
        "official_turns",
        "pseudo_steps",
        "policy_steps",
        "forced_steps",
        "graph_variants_created",
        "native_rollout_buckets",
        "actor_streams",
    )
    maximum = (
        "maximum_batched_actor_seconds",
        "encode_seconds",
        "policy_seconds",
        "environment_seconds",
        "native_observation_seconds",
        "decision_seconds",
        "recording_seconds",
        "native_selection_seconds",
        "action_compilation_seconds",
        "history_staging_seconds",
        "finalization_seconds",
        "turn_graph_capture_seconds",
        "graph_capture_seconds",
        "replica_sync_seconds",
    )
    result: dict[str, object] = {
        name: sum(int(_number(values, name)) for values in diagnostics) for name in summed
    }
    result.update({name: max(_number(values, name) for values in diagnostics) for name in maximum})
    elapsed = max(_number(values, "elapsed_seconds") for values in diagnostics)
    games = [game for payload in payloads for game in payload["games"]]
    games.sort(key=lambda game: (int(game["seed"]), int(game["seat"])))
    physical_games = int(cast(int, result["physical_games"]))
    episodes = int(cast(int, result["episodes"]))
    pseudo_steps = int(cast(int, result["pseudo_steps"]))
    result.update(
        {
            "elapsed_seconds": elapsed,
            "physical_games_per_second": physical_games / elapsed,
            "episodes_per_second": episodes / elapsed,
            "pseudo_steps_per_second": pseudo_steps / elapsed,
            "rollout_devices": [payload["device"] for payload in payloads],
            "device_elapsed_seconds": [
                _number(payload["diagnostics"], "elapsed_seconds") for payload in payloads
            ],
        }
    )
    if len(games) != episodes or physical_games * 2 != episodes:
        raise RuntimeError("intent distributed rollout lost a game perspective")
    return result, games


def outcome_metrics(
    games: Sequence[Mapping[str, int | float | str]],
) -> dict[str, int | float]:
    """Reduce direct self-play results across rank-local game shards."""
    outcomes = np.asarray([int(game["outcome"]) for game in games])
    cash = np.asarray([float(game["terminal_cash"]) for game in games])
    opponent = np.asarray([float(game["opponent_cash"]) for game in games])
    return {
        "wins": int(np.count_nonzero(outcomes > 0)),
        "ties": int(np.count_nonzero(outcomes == 0)),
        "losses": int(np.count_nonzero(outcomes < 0)),
        "mean_terminal_cash": float(cash.mean()),
        "mean_cash_difference": float((cash - opponent).mean()),
    }


def distributed_rng_state(
    states: Sequence[Mapping[str, object]], devices: Sequence[str]
) -> dict[str, object]:
    """Bind every rank-local RNG stream into one checkpoint payload."""
    if not states or len(states) != len(devices):
        raise ValueError("intent distributed RNG ranks and devices must align")
    return {
        "schema_version": _DISTRIBUTED_RNG_VERSION,
        "world_size": len(states),
        "devices": tuple(devices),
        "rank_states": tuple(dict(state) for state in states),
    }


def rank_rng_state(payload: object, context: DistributedContext) -> Mapping[str, object]:
    """Select this rank's RNG state, including legacy fleet checkpoints."""
    if not isinstance(payload, Mapping):
        raise ValueError("intent checkpoint RNG state is absent")
    if payload.get("schema_version") == _DISTRIBUTED_RNG_VERSION:
        states = payload.get("rank_states")
        if (
            payload.get("world_size") != context.world_size
            or not isinstance(states, tuple)
            or len(states) != context.world_size
            or not isinstance(states[context.rank], Mapping)
        ):
            raise ValueError("intent distributed RNG topology changed")
        return cast(Mapping[str, object], states[context.rank])
    if not context.enabled:
        return payload
    devices = payload.get("devices")
    action_states = payload.get("action_generators")
    device_states = payload.get("torch_devices")
    if (
        not isinstance(devices, tuple)
        or len(devices) != context.world_size
        or not isinstance(action_states, tuple)
        or len(action_states) != context.world_size
        or not isinstance(device_states, tuple)
        or len(device_states) != context.world_size
    ):
        raise ValueError("intent legacy RNG topology changed")
    return {
        **dict(payload),
        "devices": (devices[context.rank],),
        "action_generators": (action_states[context.rank],),
        "torch_devices": (device_states[context.rank],),
    }


__all__ = [
    "IntentRolloutPayload",
    "aggregate_rollouts",
    "distributed_rng_state",
    "local_seeds",
    "outcome_metrics",
    "rank_rng_state",
    "rollout_payload",
]
