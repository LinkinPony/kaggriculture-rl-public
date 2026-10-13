"""Non-causal work-order proposals retaining demonstrated task dependencies."""

import numpy as np
from numpy.typing import NDArray

from kagg_revue.policy.contracts import ContractLayout


def propose_work(
    observations: NDArray[np.float16], actions: NDArray[np.int16], layout: ContractLayout
) -> NDArray[np.int16]:
    """Compress movement into destinations and retain each worker's ordered jobs."""
    base = layout.observation
    turns, games = observations.shape[:2]
    units = observations[
        ..., base.board_features : base.board_features + base.units * base.unit_features
    ]
    units = units.reshape(turns, games, base.units, base.unit_features)
    coordinates = np.rint(units[..., 2:4] * (layout.board_size - 1)).astype(np.int16)
    result = np.zeros((layout.decisions, games, base.units, max(layout.spans) + 1, 4), np.int16)
    for decision, (start, span) in enumerate(zip(layout.starts, layout.spans, strict=True)):
        raw = actions[start : start + span, :, : base.units]
        active = raw[..., 0] >= 5
        slot = np.cumsum(active, axis=0) - 1
        time, game, unit = np.nonzero(active)
        destination = coordinates[start + time, game, unit]
        selected = result[decision]
        selected[game, unit, slot[time, game, unit], 0] = (
            1 + destination[:, 0] + layout.board_size * destination[:, 1]
        )
        selected[game, unit, slot[time, game, unit], 1:3] = raw[time, game, unit]
        selected[game, unit, slot[time, game, unit], 3] = time
        # Preserve unfinished travel across interval boundaries without copying moves.
        final = coordinates[start + span - 1].copy()
        final_op = raw[-1, ..., 0]
        final[..., 0] += (final_op == 3).astype(np.int16) - (final_op == 4)
        final[..., 1] += (final_op == 2).astype(np.int16) - (final_op == 1)
        game, unit = np.nonzero(units[start + span - 1, ..., 0] > 0)
        selected[game, unit, active.sum(0)[game, unit], 0] = (
            1 + final[game, unit, 0] + layout.board_size * final[game, unit, 1]
        )
    return result


def propose_programs(
    observations: NDArray[np.float16], actions: NDArray[np.int16], layout: ContractLayout
) -> NDArray[np.int16]:
    """Pack executable jobs and explicit market requests into the actor's flat ABI."""
    work = propose_work(observations, actions, layout)
    games = observations.shape[1]
    result = np.zeros((layout.decisions, games, layout.factors), dtype=np.int16)
    result[..., : layout.work_factors] = work.reshape(layout.decisions, games, -1)
    markets = result[..., layout.work_factors :].reshape(
        layout.decisions, games, layout.capacity, layout.observation.markets, 2
    )
    for decision, (start, span) in enumerate(zip(layout.starts, layout.spans, strict=True)):
        markets[decision, :, :span] = actions[
            start : start + span, :, layout.observation.units :
        ].transpose(1, 0, 2, 3)
    return result
