"""Legacy future-action proposals and shared action-contract compatibility."""

import numpy as np
from numpy.typing import NDArray

from kagg_revue.policy.contracts import ContractLayout, NetworkShape

__all__ = ["ContractLayout", "NetworkShape", "RESERVES", "propose_contracts"]

RESERVES = np.array([0, 1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 80, 96, 100])


def propose_contracts(
    observations: NDArray[np.float16], raw_actions: NDArray[np.int16], layout: ContractLayout
) -> NDArray[np.int64]:
    """Extract spatial goals from a teacher's future behavior, for BC proposals only.

    This is intentionally non-causal: the actor receives only the boundary
    observation. Compiler replay must establish whether the proposed language
    preserves useful closed-loop behavior before training on these labels.
    """
    if layout.work:
        from kagg_revue.production.work import propose_programs

        return propose_programs(observations, raw_actions, layout).astype(np.int64)
    turns, games = observations.shape[:2]
    base = layout.observation
    board = observations[..., : base.board_features].reshape(turns, games, 2, 29, layout.cells)[
        :, :, 0
    ]
    unit_end = base.board_features + base.units * base.unit_features
    units = observations[..., base.board_features : unit_end].reshape(
        turns, games, base.units, base.unit_features
    )
    result = np.zeros((layout.decisions, games, layout.factors), dtype=np.int64)
    for decision, (start, span) in enumerate(zip(layout.starts, layout.spans, strict=True)):
        stop = start + span
        final = board[stop - 1]
        target = np.zeros((games, layout.cells), dtype=np.int64)
        for crop in range(5):
            target[final[:, 6 + crop] > 0] = crop + 1
        for animal in range(3):
            target[final[:, 18 + animal] > 0] = animal + 6
        # An unfinished structure is a complete animal establishment proposal.
        bare = (final[:, 17] == 0) & ((final[:, 4] + final[:, 5]) > 0)
        for later in range(stop, min(turns, stop + span)):
            for animal in range(3):
                found = bare & (board[later, :, 18 + animal] > 0)
                target[found] = animal + 6
                bare[found] = False
        cells = result[decision, :, : layout.cells * 4].reshape(games, layout.cells, 4)
        cells[..., 0] = target
        cells[..., 1] = 2
        cells[..., 2] = 2
        cells[..., 3] = 1
        # Fertilization belongs to the requested upkeep mode, not an implicit scorer.
        fertilize = raw_actions[start:stop, :, : base.units, 0] == 37
        offset, game, unit = np.nonzero(fertilize)
        position = units[start + offset, game, unit, 2:4]
        coordinates = np.rint(position * (layout.board_size - 1)).astype(int)
        cells[game, coordinates[:, 1] * layout.board_size + coordinates[:, 0], 1] = 3
        controls = result[decision, :, layout.cells * 4 : layout.cells * 4 + 5]
        controls[:, 0] = np.max(units[start:stop, ..., 0].sum(-1), axis=0).astype(int) - 1
        global_values = observations[stop - 1, :, unit_end:]
        controls[:, 1] = np.rint(global_values[:, 69:73].sum(-1)).astype(int) - 1
        controls[:, 1] = np.clip(controls[:, 1], 0, 3)
        controls[:, 3] = 8  # Bank at a material load; this is a proposal, not a rule.
        controls[:, 4] = 4
        products = result[decision, :, layout.cells * 4 + 5 :].reshape(games, 9, 2)
        animal_count = (target >= 6).sum(-1)
        products[:, 0, 0] = np.searchsorted(RESERVES, animal_count).clip(0, 15)
        # The final day has no automatic end-of-day transfer; request frequent banking.
        if stop == turns:
            controls[:, 3] = 1
            cells[..., 0] = 0
            cells[..., 2] = 1
    return result
