"""Compose distinct frozen-opponent batches into one learner-row partition."""

from typing import Any

import numpy as np
from numpy.typing import NDArray


class FrozenBatches:
    """Concatenate public scripts and historical neural games without mixing seats."""

    def __init__(self, groups: list[tuple[Any, int]]) -> None:
        """Keep group ordering identical across observations, actions and outcomes."""
        self.groups = groups

    @property
    def step_index(self) -> int:
        """Reject drift between frozen-opponent collection clocks."""
        clocks = {batch.step_index for batch, _ in self.groups}
        if len(clocks) != 1:
            raise ValueError("frozen populations have inconsistent turn clocks")
        return int(clocks.pop())

    @property
    def completed_games(self) -> int:
        """Sum completed physical games across opponent groups."""
        return sum(batch.completed_games for batch, _ in self.groups)

    @property
    def transitions(self) -> int:
        """Sum environment transitions across opponent groups."""
        return sum(batch.transitions for batch, _ in self.groups)

    def observe_into(self, output: NDArray[np.float16]) -> None:
        """Fill each group's learned-seat rows in the declared order."""
        offset = 0
        for batch, count in self.groups:
            batch.observe_into(output[offset : offset + count])
            offset += count
        if offset != len(output):
            raise ValueError("frozen population row count differs from the learner buffer")

    def advance_programs(self, plans: NDArray[np.int64], turns: int, capacity: int) -> None:
        """Route each learned program to exactly one physical game."""
        offset = 0
        for batch, count in self.groups:
            batch.advance_programs(plans[offset : offset + count], turns, capacity)
            offset += count
        if offset != len(plans):
            raise ValueError("frozen population action count differs from the learner buffer")

    def cash(self) -> NDArray[np.float64]:
        """Preserve learner-first seat routing in all frozen populations."""
        return np.concatenate([batch.cash() for batch, _ in self.groups])
