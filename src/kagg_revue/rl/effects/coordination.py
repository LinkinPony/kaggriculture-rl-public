"""Distributed rollout and restart coordination for atomic-effect PPO."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict, cast

import numpy as np

from kagg_revue.rl.distributed import DistributedContext
from kagg_revue.rl.effects.population import effect_outcome_metrics
from kagg_revue.rl.effects.rollout import EffectGameResult, EffectRolloutResult
from kagg_revue.rl.rollout.batch import Job
from kagg_revue.rl.rollout.population import weighted_rollout_jobs

_DISTRIBUTED_RNG_VERSION = "atomic-effect-distributed-rng-v1"


class EffectRolloutPayload(TypedDict):
    """Small rank-local payload gathered without moving rollout tensors."""

    rank: int
    device: str
    diagnostics: dict[str, object]
    games: list[dict[str, int | float | str]]


def local_population_jobs(
    seeds: Sequence[int],
    weights: Mapping[str, float],
    context: DistributedContext,
    *,
    sampling_seed: int,
) -> tuple[Job, ...]:
    """Allocate the exact global mix and keep complete games on one rank."""
    return weighted_rollout_jobs(
        seeds,
        weights,
        rank=context.rank,
        world_size=context.world_size,
        sampling_seed=sampling_seed,
    )


def rollout_payload(
    rollout: EffectRolloutResult,
    context: DistributedContext,
) -> EffectRolloutPayload:
    """Pack only direct outcomes and coarse timings for rank aggregation."""
    return {
        "rank": context.rank,
        "device": str(context.device),
        "diagnostics": dict(rollout.diagnostics),
        "games": [
            {
                "episode_id": game.episode_id,
                "opponent_id": game.opponent_id,
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
        raise TypeError(f"effect rollout diagnostic {name} is not numeric")
    return float(value)


def aggregate_rollouts(
    payloads: Sequence[EffectRolloutPayload],
) -> tuple[dict[str, object], list[dict[str, int | float | str]]]:
    """Combine rank-local critical paths while leaving training tapes local."""
    if not payloads:
        raise ValueError("effect distributed rollout produced no rank payloads")
    diagnostics = [payload["diagnostics"] for payload in payloads]
    summed = (
        "physical_games",
        "episodes",
        "official_turns",
        "policy_factors",
        "factors",
        "native_rollout_buckets",
        "graph_variants_created",
        "actor_streams",
    )
    maximum = (
        "maximum_batched_actor_seconds",
        "encode_seconds",
        "native_observation_seconds",
        "inference_seconds",
        "native_transition_seconds",
        "action_compilation_seconds",
        "environment_seconds",
        "finalization_seconds",
        "turn_graph_capture_seconds",
        "graph_capture_seconds",
    )
    result: dict[str, object] = {
        name: sum(int(_number(values, name)) for values in diagnostics) for name in summed
    }
    result.update({name: max(_number(values, name) for values in diagnostics) for name in maximum})
    elapsed = max(_number(values, "elapsed_seconds") for values in diagnostics)
    games = [game for payload in payloads for game in payload["games"]]
    games.sort(
        key=lambda game: (
            int(game["seed"]),
            str(game["opponent_id"]),
            int(game["seat"]),
        )
    )
    episodes = int(cast(int, result["episodes"]))
    physical_games = int(cast(int, result["physical_games"]))
    if len(games) != episodes:
        raise RuntimeError("effect distributed rollout lost a trained perspective")
    result.update(
        {
            "elapsed_seconds": elapsed,
            "physical_games_per_second": physical_games / elapsed,
            "episodes_per_second": episodes / elapsed,
            "rollout_devices": [payload["device"] for payload in payloads],
            "device_elapsed_seconds": [
                _number(payload["diagnostics"], "elapsed_seconds") for payload in payloads
            ],
            "workers": [
                {
                    "rank": payload["rank"],
                    "device": payload["device"],
                    "diagnostics": payload["diagnostics"],
                }
                for payload in payloads
            ],
        }
    )
    return result, games


def outcome_metrics(
    games: Sequence[Mapping[str, int | float | str]],
) -> dict[str, object]:
    """Report only direct W/L/T and terminal-cash surfaces by opponent."""
    if not games:
        raise ValueError("effect outcome panel cannot be empty")
    outcomes = np.asarray([int(game["outcome"]) for game in games], dtype=np.int64)
    cash = np.asarray([float(game["terminal_cash"]) for game in games], dtype=np.float64)
    opponent_cash = np.asarray(
        [float(game["opponent_cash"]) for game in games],
        dtype=np.float64,
    )
    typed_games = tuple(
        EffectGameResult(
            episode_id=str(game["episode_id"]),
            opponent_id=str(game["opponent_id"]),
            seed=int(game["seed"]),
            seat=int(game["seat"]),
            outcome=int(game["outcome"]),
            terminal_cash=float(game["terminal_cash"]),
            opponent_cash=float(game["opponent_cash"]),
        )
        for game in games
    )
    return {
        "wins": int(np.count_nonzero(outcomes > 0)),
        "ties": int(np.count_nonzero(outcomes == 0)),
        "losses": int(np.count_nonzero(outcomes < 0)),
        "mean_terminal_cash": float(cash.mean()),
        "mean_cash_difference": float((cash - opponent_cash).mean()),
        "opponents": effect_outcome_metrics(typed_games),
    }


def distributed_rng_state(
    states: Sequence[Mapping[str, object]],
    devices: Sequence[str],
) -> dict[str, object]:
    """Bind every rank-local stochastic stream into one checkpoint."""
    if not states or len(states) != len(devices):
        raise ValueError("effect distributed RNG ranks and devices must align")
    return {
        "schema_version": _DISTRIBUTED_RNG_VERSION,
        "world_size": len(states),
        "devices": tuple(devices),
        "rank_states": tuple(dict(state) for state in states),
    }


def rank_rng_state(payload: object, context: DistributedContext) -> Mapping[str, object]:
    """Select this rank's exact stochastic state from a checkpoint."""
    if not isinstance(payload, Mapping):
        raise ValueError("effect checkpoint RNG state is absent")
    if not context.enabled:
        return payload
    states = payload.get("rank_states")
    if (
        payload.get("schema_version") != _DISTRIBUTED_RNG_VERSION
        or payload.get("world_size") != context.world_size
        or not isinstance(states, tuple)
        or len(states) != context.world_size
        or not isinstance(states[context.rank], Mapping)
    ):
        raise ValueError("effect distributed RNG topology changed")
    return cast(Mapping[str, object], states[context.rank])


__all__ = [
    "EffectRolloutPayload",
    "aggregate_rollouts",
    "distributed_rng_state",
    "local_population_jobs",
    "outcome_metrics",
    "rank_rng_state",
    "rollout_payload",
]
