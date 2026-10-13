"""Teacher programs aligned to states and histories visited by a student."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.bc.programs.teacher_batch import compile_teacher_program_turn_batch
from kagg_revue.bc.programs.translate import ProgramReplaySeat
from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.kaito.native import create_native_session as kaito_session
from kagg_revue.opponents.native_batch import (
    create_native_opponent_session,
    step_native_opponent_batch,
)
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.runtime import compact_mask_width
from kagg_revue.rl.programs.data import ProgramEpisode


def to_numpy(
    value: NDArray[np.generic] | Tensor,
    dtype: np.dtype[Any],
) -> NDArray[np.generic]:
    """Copy or view one rollout field as a requested NumPy dtype."""
    raw = value.detach().cpu().numpy() if isinstance(value, Tensor) else value
    return np.asarray(raw, dtype=dtype)


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"{name} is not numeric")
    return int(value)


def translate_student_episodes(
    backend: BackendApi,
    episodes: Sequence[ProgramEpisode],
    environment: Mapping[str, object],
    architecture: ActorArchitecture,
    codec: ReplayActionEncoder,
    contract: NativeProgramContract,
    workers: int,
) -> tuple[ProgramReplaySeat, ...]:
    """Replay frozen students while batch-compiling each teacher turn."""
    if not episodes:
        raise ValueError("program correction requires student episodes")
    turns = episodes[0].turn_count
    if any(episode.turn_count != turns for episode in episodes):
        raise ValueError("program correction episodes have different horizons")
    engines = [
        backend.engine(seed=episode.seed, configuration=dict(environment))
        for episode in episodes
    ]
    seats = np.asarray([episode.seat for episode in episodes], dtype=np.int64)
    opponent_ids = tuple(episode.opponent_id for episode in episodes)
    maximum_orders = _integer(
        environment["maxMarketOrdersPerTurn"], "maxMarketOrdersPerTurn"
    )
    teacher_sessions = [kaito_session(maximum_orders) for _ in episodes]
    opponent_sessions = [
        create_native_opponent_session(opponent, maximum_orders)
        for opponent in opponent_ids
    ]
    program_sessions = [
        backend.conditional_program_session(dict(environment), contract.unit_limit)
        for _ in episodes
    ]
    batch = len(episodes)
    width = architecture.max_decisions
    capacity = contract.maximum_decisions
    teacher_tokens = np.zeros((batch, width), dtype=np.int64)
    teacher_quantities = np.zeros_like(teacher_tokens)
    teacher_counts = np.zeros(batch, dtype=np.int64)
    teacher_units = np.zeros(batch, dtype=np.int64)
    repairs = [Counter[str]() for _ in episodes]
    program_scalars = np.zeros((batch, turns, capacity, 7), dtype=np.int16)
    program_roots = np.zeros(
        (batch, turns, capacity, contract.root_feature_count), dtype=np.float32
    )
    program_options = np.zeros(
        (batch, turns, capacity, contract.option_feature_count), dtype=np.int32
    )
    program_reservations = np.zeros(
        (batch, turns, capacity, contract.tile_count), dtype=np.int16
    )
    program_actions = np.zeros((batch, turns, capacity, 9), dtype=np.int64)
    program_masks = np.zeros(
        (batch, turns, capacity, compact_mask_width(contract)), dtype=np.bool_
    )
    program_quantity_max = np.zeros((batch, turns, capacity), dtype=np.int64)
    program_counts = np.zeros((batch, turns), dtype=np.int16)
    student_tokens = np.stack(
        [to_numpy(episode.actions, np.dtype(np.int64)) for episode in episodes]
    )
    student_quantities = np.stack(
        [to_numpy(episode.quantities, np.dtype(np.int64)) for episode in episodes]
    )
    student_counts = np.stack(
        [
            to_numpy(episode.action_decision_counts, np.dtype(np.int64))
            for episode in episodes
        ]
    )
    done = np.zeros(batch, dtype=np.bool_)
    for turn in range(turns):
        teacher_tokens.fill(0)
        teacher_quantities.fill(0)
        teacher_counts.fill(0)
        teacher_units.fill(0)
        backend.kaito_v48_action_numeric_batch(
            engines,
            seats,
            teacher_sessions,
            teacher_tokens,
            teacher_quantities,
            teacher_counts,
            teacher_units,
            workers,
        )
        trace = compile_teacher_program_turn_batch(
            backend,
            program_sessions,
            engines,
            seats,
            teacher_tokens,
            teacher_quantities,
            teacher_counts,
            teacher_units,
            codec,
            contract,
            workers,
            repairs,
        )
        program_scalars[:, turn] = trace.scalars
        program_roots[:, turn] = trace.root_features
        program_options[:, turn] = trace.option_features
        program_reservations[:, turn] = trace.target_reservations
        program_actions[:, turn] = trace.actions
        program_masks[:, turn] = trace.conditional_masks
        program_quantity_max[:, turn] = trace.quantity_max
        program_counts[:, turn] = trace.decision_counts
        done = step_native_opponent_batch(
            backend,
            engines,
            seats,
            opponent_ids,
            opponent_sessions,
            student_tokens[:, turn],
            student_quantities[:, turn],
            student_counts[:, turn],
            teacher_units,
            workers,
        )
    if not bool(done.all()):
        raise RuntimeError("program correction replay missed the official horizon")
    for engine, episode in zip(engines, episodes, strict=True):
        if (
            float(engine.money(episode.seat)) != episode.terminal_cash
            or float(engine.money(1 - episode.seat)) != episode.opponent_cash
        ):
            raise RuntimeError("program correction could not reproduce student rollout")
    return tuple(
        ProgramReplaySeat(
            board=cast(
                NDArray[np.float16],
                to_numpy(episode.board, np.dtype(np.float16)),
            ),
            units=cast(
                NDArray[np.float16],
                to_numpy(episode.units, np.dtype(np.float16)),
            ),
            global_features=cast(
                NDArray[np.float16],
                to_numpy(episode.global_features, np.dtype(np.float16)),
            ),
            economic_state=cast(
                NDArray[np.int32],
                to_numpy(episode.economic_state, np.dtype(np.int32)),
            ),
            actions=student_tokens[row],
            quantities=student_quantities[row],
            action_decision_counts=student_counts[row].astype(np.int16),
            program_scalars=program_scalars[row],
            program_root_features=program_roots[row],
            program_option_features=program_options[row],
            program_target_reservations=program_reservations[row],
            program_actions=program_actions[row],
            program_conditional_masks=program_masks[row],
            program_quantity_max=program_quantity_max[row],
            program_decision_counts=program_counts[row],
            outcome=episode.outcome,
            statistics=dict(sorted(repairs[row].items())),
        )
        for row, episode in enumerate(episodes)
    )


__all__ = ["to_numpy", "translate_student_episodes"]
