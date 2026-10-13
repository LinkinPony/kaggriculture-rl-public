"""Frozen native-policy demonstrations for conditional-program cloning."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from kagg_revue.bc.actions import EncodedTurnAction, ReplayActionEncoder
from kagg_revue.bc.tasks.replay import ReplaySequence
from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.native_batch import create_native_opponent_session
from kagg_revue.policy.model import ActorArchitecture


def _native_action(agent_id: str, session: Any, engine: Any, seat: int) -> dict[str, Any]:
    """Evaluate one source-authenticated native opponent on the live engine."""
    if agent_id == "kaito_v48":
        from kagg_revue.opponents.kaito.native import native_action

        return native_action(session, engine, seat)
    if agent_id == "kaito_v39":
        from kagg_revue.opponents.kaito.v39.native import native_action

        return native_action(session, engine, seat)
    if agent_id == "boatlee_v21":
        from kagg_revue.opponents.boatlee.native import native_action

        return native_action(session, engine, seat)
    if agent_id == "mugundh_v21":
        from kagg_revue.opponents.mugundh.native import native_action

        return native_action(session, engine, seat)
    raise ValueError(f"program demonstration lacks a native agent: {agent_id}")


def _positions(observation: Mapping[str, Any], seat: int) -> tuple[tuple[int, int], ...]:
    farms = cast(list[Mapping[str, Any]], observation["farms"])
    farm = farms[seat]
    raw = [farm["farmer"], *cast(list[object], farm["hands"])]
    result: list[tuple[int, int]] = []
    for value in raw:
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("native teacher produced a malformed unit position")
        result.append((int(value[0]), int(value[1])))
    return tuple(result)


def collect_demonstration(
    backend: BackendApi,
    *,
    seed: int,
    teacher_seat: int,
    teacher_id: str,
    opponent_id: str,
    environment: Mapping[str, object],
    architecture: ActorArchitecture,
    unit_limit: int,
) -> ReplaySequence:
    """Run one paired-seat game and retain exact teacher-facing causal inputs."""
    if teacher_seat not in {0, 1}:
        raise ValueError("program demonstration teacher seat must be zero or one")
    agent_ids = (
        (teacher_id, opponent_id) if teacher_seat == 0 else (opponent_id, teacher_id)
    )
    engine = backend.engine(seed=seed, configuration=dict(environment))
    configuration = cast(dict[str, Any], dict(engine.configuration))
    turns = int(configuration["episodeSteps"]) - 1
    maximum_orders = int(configuration["maxMarketOrdersPerTurn"])
    codec = ReplayActionEncoder(cast(Mapping[str, Any], backend.action_codec_spec()))
    if codec.unit_tokens != architecture.unit_action_tokens:
        raise ValueError("program teacher and actor action vocabularies differ")
    sessions = tuple(
        create_native_opponent_session(agent_id, maximum_orders) for agent_id in agent_ids
    )

    observations: list[list[dict[str, Any]]] = [[], []]
    positions: list[list[tuple[tuple[int, int], ...]]] = [[], []]
    encoded_actions: list[list[EncodedTurnAction]] = [[], []]
    repairs: list[Counter[str]] = [Counter(), Counter()]
    board_rows: list[list[NDArray[np.float16]]] = [[], []]
    unit_rows: list[list[NDArray[np.float16]]] = [[], []]
    global_rows: list[list[NDArray[np.float16]]] = [[], []]
    economic_rows: list[list[NDArray[np.int32]]] = [[], []]
    action_tokens = np.zeros(
        (2, turns, architecture.max_decisions), dtype=np.int64
    )
    action_quantities = np.zeros_like(action_tokens)
    decision_mask = np.zeros_like(action_tokens, dtype=np.bool_)

    for turn in range(turns):
        if bool(engine.done):
            raise RuntimeError("native teacher match ended before the official horizon")
        raw_observations = tuple(
            cast(Mapping[str, Any], engine.observation(seat)) for seat in (0, 1)
        )
        policy_batch = backend.engine_policy_session_batch(
            [engine, engine], [0, 1], unit_limit, 2
        )
        board_raw, units_raw, global_raw = policy_batch.encode_compact()
        economic_raw = np.asarray(policy_batch.gpu_state_compact(), dtype=np.int64)
        if np.any(economic_raw < np.iinfo(np.int32).min) or np.any(
            economic_raw > np.iinfo(np.int32).max
        ):
            raise ValueError("native teacher economic state exceeds int32 storage")

        actions = tuple(
            _native_action(agent_ids[seat], sessions[seat], engine, seat)
            for seat in (0, 1)
        )
        for seat in (0, 1):
            observation = dict(raw_observations[seat])
            current_positions = _positions(observation, seat)
            encoded = codec.encode(
                actions[seat], len(current_positions), maximum_orders
            )
            count = len(encoded.tokens)
            if count > architecture.max_decisions:
                raise ValueError("native teacher action exceeds actor decision capacity")
            action_tokens[seat, turn, :count] = encoded.tokens
            action_quantities[seat, turn, :count] = encoded.quantities
            decision_mask[seat, turn, :count] = True
            repairs[seat].update(encoded.repairs)
            observations[seat].append(observation)
            positions[seat].append(current_positions)
            encoded_actions[seat].append(encoded)
            board_rows[seat].append(
                np.asarray(board_raw[seat], dtype=np.float16)
            )
            unit_rows[seat].append(
                np.asarray(units_raw[seat], dtype=np.float16)
            )
            global_rows[seat].append(
                np.asarray(global_raw[seat], dtype=np.float16)
            )
            economic_rows[seat].append(economic_raw[seat].astype(np.int32))
        engine.step(actions[0], actions[1])

    if not bool(engine.done):
        raise RuntimeError("native teacher match did not reach the official horizon")
    rewards = (float(engine.money(0)), float(engine.money(1)))
    board = np.stack([np.stack(rows) for rows in board_rows]).astype(np.float16)
    units = np.stack([np.stack(rows) for rows in unit_rows]).astype(np.float16)
    global_features = np.stack([np.stack(rows) for rows in global_rows]).astype(
        np.float16
    )
    economic_state = np.stack([np.stack(rows) for rows in economic_rows]).astype(
        np.int32
    )
    if not all(
        np.isfinite(value).all() for value in (board, units, global_features)
    ):
        raise ValueError("native teacher actor input contains a non-finite value")
    return ReplaySequence(
        episode_id=f"{teacher_id}-vs-{opponent_id}-{seed}-seat-{teacher_seat}",
        configuration=configuration,
        observations=tuple(tuple(rows) for rows in observations),
        positions=tuple(tuple(rows) for rows in positions),
        unit_actions=(tuple(() for _ in range(turns)),) * 2,
        encoded_actions=tuple(tuple(rows) for rows in encoded_actions),
        board=board,
        units=units,
        global_features=global_features,
        economic_state=economic_state,
        action_tokens=action_tokens,
        action_quantities=action_quantities,
        decision_mask=decision_mask,
        rewards=rewards,
        agent_names=agent_ids,
        repairs=tuple(dict(values) for values in repairs),
        minimum_remaining_overage=(None, None),
    )


__all__ = ["collect_demonstration"]
