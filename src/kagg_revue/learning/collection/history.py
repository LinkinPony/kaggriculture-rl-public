"""Bulk seat routing around the unchanged persistent native self-play engine."""

from typing import Any

import numpy as np
from numpy.typing import NDArray


class HistoricalBatch:
    """Expose one learned seat and one frozen neural seat per complete native game."""

    def __init__(
        self,
        batch: Any,
        seats: NDArray[np.int64],
        opponent_observations: NDArray[np.float16],
        opponent_actions: NDArray[np.int64],
        quantity_maps: tuple[NDArray[np.int64], NDArray[np.int64]] | None = None,
        work_factors: int = 0,
        support_features: int = 0,
    ) -> None:
        """Allocate reusable routing buffers once; both role indices have proven bounds."""
        if seats.ndim != 1 or not np.isin(seats, [0, 1]).all():
            raise ValueError("historical games require binary learned seats")
        if len(seats) != len(opponent_observations) or len(seats) != len(opponent_actions):
            raise ValueError("historical actor buffers must match physical games")
        self.batch = batch
        self.seats = seats.copy()
        self.rows = np.arange(len(seats))
        self.learned = 2 * self.rows + seats
        self.frozen = 2 * self.rows + 1 - seats
        self.observations = np.empty((2 * len(seats), opponent_observations.shape[1]), np.float16)
        self.learner_observations: NDArray[np.float16] | None = None
        self.frozen_observations: NDArray[np.float16] | None = None
        self.support_features = support_features
        self.actions = np.empty((2 * len(seats), opponent_actions.shape[1]), np.int64)
        self.opponent_observations = opponent_observations
        self.opponent_actions = opponent_actions
        self.quantity_maps = quantity_maps
        self.quantity_columns = np.concatenate(
            (np.arange(2, work_factors, 4), np.arange(work_factors + 1, self.actions.shape[1], 2))
        )

    @property
    def step_index(self) -> int:
        """Expose the common official clock of the routed native states."""
        return int(self.batch.step_index)

    @property
    def completed_games(self) -> int:
        """Return actual completed physical games from the native owner."""
        return int(self.batch.completed_games)

    @property
    def transitions(self) -> int:
        """Return native official transitions, counting each game once."""
        return int(self.batch.transitions)

    def observe_into(self, output: NDArray[np.float16]) -> None:
        """Route native observations into the two fixed pinned actor input buffers."""
        learned = self.observations
        if output.shape[1] != self.observations.shape[1]:
            if self.support_features <= 0 or output.shape[1] < self.observations.shape[1]:
                raise ValueError("legacy history projection requires additive observations")
            if self.learner_observations is None:
                self.learner_observations = np.empty(
                    (len(self.observations), output.shape[1]), np.float16
                )
                self.frozen_observations = np.empty((len(self.seats), output.shape[1]), np.float16)
            learned = self.learner_observations
        self.batch.observe_selfplay_into(learned)
        np.take(learned, self.learned, axis=0, out=output, mode="clip")
        if learned is self.observations:
            np.take(learned, self.frozen, axis=0, out=self.opponent_observations, mode="clip")
        else:
            assert self.frozen_observations is not None
            np.take(learned, self.frozen, axis=0, out=self.frozen_observations, mode="clip")
            # V4 and v5b append their supplements before the unchanged final
            # unit-support block. Every older version is these exact two spans.
            prefix = self.opponent_observations.shape[1] - self.support_features
            self.opponent_observations[:, :prefix] = self.frozen_observations[:, :prefix]
            self.opponent_observations[:, prefix:] = self.frozen_observations[
                :, -self.support_features :
            ]

    def advance_programs(self, plans: NDArray[np.int64], turns: int, capacity: int) -> None:
        """Scatter both neural plans in bulk, then release the GIL in native execution."""
        self.actions[self.learned] = plans
        self.actions[self.frozen] = self.opponent_actions
        if self.quantity_maps is not None:
            for rows, mapping in zip((self.learned, self.frozen), self.quantity_maps, strict=True):
                index = np.ix_(rows, self.quantity_columns)
                self.actions[index] = mapping[self.actions[index]]
        self.batch.advance_programs(self.actions, turns, capacity, True)

    def cash(self) -> NDArray[np.float64]:
        """Return learned-seat-first cash, excluding frozen seats from training rows."""
        cash: NDArray[np.float64] = self.batch.cash()
        return np.stack((cash[self.rows, self.seats], cash[self.rows, 1 - self.seats]), axis=1)
