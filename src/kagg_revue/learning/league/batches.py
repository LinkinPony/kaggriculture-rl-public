"""Shared neural inference over native self-play and native script game batches."""

from typing import Any

import numpy as np

from kagg_revue.learning.league.config import League
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.native.batches import create_selfplay_batch
from kagg_revue.opponents.batches import create_batch


class LeagueBatch:
    """Keep scripts entirely inside C++ while exposing the common physical-seat layout."""

    def __init__(self, config: League, settings: RuntimeSettings, seeds: list[int], owners: Any):
        """Allocate separate native sessions once per complete game."""
        self.groups: list[tuple[Any, Any, Any]] = []
        learned = len(config.members)
        neural = np.flatnonzero((owners < learned).all(axis=1))
        if len(neural):
            self.groups.append(
                (create_selfplay_batch(settings, [seeds[i] for i in neural]), neural, None)
            )
        scripted = np.flatnonzero((owners >= learned).any(axis=1))
        if len(scripted):
            seats = (owners[scripted, 0] >= learned).astype(np.int64)
            jobs = [
                (seeds[i], int(seat), config.participants[owners[i, 1 - seat]])
                for i, seat in zip(scripted, seats, strict=True)
            ]
            self.groups.append((create_batch(settings, jobs), scripted, seats))
        self.size = len(seeds)

    def observe_selfplay_into(self, host: Any) -> None:
        """Write contiguous schedule regions directly into pinned host storage."""
        for batch, indices, _ in self.groups:
            if indices[-1] - indices[0] + 1 != len(indices):
                raise ValueError("native league groups must occupy contiguous schedule regions")
            batch.observe_selfplay_into(host[2 * indices[0] : 2 * (indices[-1] + 1)])

    def advance_programs(self, selected: Any, span: int, capacity: int) -> None:
        """Advance learned seats and native script opponents with the GIL released."""
        plans = selected.reshape(self.size, 2, -1)
        for batch, indices, seats in self.groups:
            if seats is None:
                batch.advance_programs(
                    plans[indices].reshape(2 * len(indices), -1), span, capacity, True
                )
            else:
                batch.advance_programs(plans[indices, seats], span, capacity)

    @property
    def completed_games(self) -> int:
        """Count each physical game once across both native backends."""
        return sum(int(batch.completed_games) for batch, _, _ in self.groups)

    @property
    def transitions(self) -> int:
        """Count actual environment turns, including all script-controlled turns."""
        return sum(int(batch.transitions) for batch, _, _ in self.groups)

    def cash(self) -> Any:
        """Return terminal cash in the original schedule and physical-seat order."""
        result = np.empty((self.size, 2), np.float64)
        for batch, indices, seats in self.groups:
            cash = batch.cash()
            # Native script batches return [learner, opponent]; the league
            # carries physical [seat 0, seat 1] everywhere, including rewards.
            if seats is not None:
                cash = np.where(seats[:, None] == 0, cash, cash[:, ::-1])
            result[indices] = cash
        return result
