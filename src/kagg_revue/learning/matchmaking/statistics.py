"""Decayed learner-relative W/D/L with a finite prior and bounded evidence mass."""

from typing import Any

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field

from kagg_revue.learning.matchmaking.config import Pfsp


class Inherited(BaseModel):
    """The last real observation behind evidence seeded from another learner."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    run: str
    update: int = Field(ge=0)
    games: float = Field(ge=0)
    score: float = Field(ge=0)


class Record(BaseModel):
    """Lifetime diagnostics and recent sufficient statistics for one immutable opponent.

    Lifetime counts contain only this learner's games; inherited evidence adds
    discounted effective mass without counting as games this learner played.
    """

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    wins: int = Field(default=0, ge=0)
    ties: int = Field(default=0, ge=0)
    losses: int = Field(default=0, ge=0)
    effective_games: float = Field(default=0, ge=0)
    effective_score: float = Field(default=0, ge=0)
    last_update: int = Field(default=0, ge=0)
    inherited: Inherited | None = None

    def evidence(self, update: int, config: Pfsp) -> tuple[float, float]:
        """Forget stale evidence toward the prior as the learner changes."""
        if update < self.last_update or self.effective_score > self.effective_games:
            raise ValueError("PFSP evidence has an invalid update or score")
        decay = 2 ** (-(update - self.last_update) / config.half_life_updates)
        return self.effective_games * decay, self.effective_score * decay

    def probability(self, update: int, config: Pfsp) -> float:
        """Estimate learner score, counting a draw as half a win."""
        games, score = self.evidence(update, config)
        return (score + config.prior_games / 2) / (games + config.prior_games)

    def mastered(self, config: Pfsp) -> bool:
        """Use the last observed evidence, so elapsed time alone cannot undo mastery.

        The bounded sample count and score at the last encounter determine
        mastery. A review updates both normally, allowing regressions to return
        an opponent to regular PFSP. Until this learner meets an opponent, the
        inherited last observation decides, so a learner change alone cannot
        undo mastery either.
        """
        options = config.mastery
        if options is None:
            return False
        games, score = self.effective_games, self.effective_score
        if self.inherited is not None and not self.wins + self.ties + self.losses:
            games, score = self.inherited.games, self.inherited.score
        return games >= options.min_games and score / games >= options.score_threshold

    def observe(self, panel: dict[str, Any], update: int, config: Pfsp) -> None:
        """Add one globally reduced physical-game panel exactly once."""
        wins, ties, losses = (int(panel[key]) for key in ("wins", "ties", "losses"))
        if min(wins, ties, losses) < 0 or wins + ties + losses != panel["games"]:
            raise ValueError("PFSP outcomes do not account for every physical game")
        games, score = self.evidence(update, config)
        games += wins + ties + losses
        score += wins + ties / 2
        scale = min(1.0, config.max_effective_games / max(games, 1))
        self.effective_games, self.effective_score = games * scale, score * scale
        self.wins += wins
        self.ties += ties
        self.losses += losses
        self.last_update = update


def probabilities(
    records: list[Record], update: int, config: Pfsp, *, latest: bool
) -> NDArray[np.float64]:
    """Combine normalized loss power, a uniform floor, and optionally the newest member."""
    if not records:
        raise ValueError("PFSP requires at least one eligible opponent")
    if config.mastery is not None:
        mastered = np.asarray([record.mastered(config) for record in records])
        if latest:
            mastered[-1] = False  # Keep the newest own policy in regular PFSP.
        if mastered.all():
            return np.full(len(records), 1.0 / len(records), dtype=np.float64)
        if mastered.any():
            active = [record for record, done in zip(records, mastered, strict=True) if not done]
            weights = probabilities(
                active, update, config.model_copy(update={"mastery": None}), latest=latest
            )
            reviewed = np.full(
                len(records), config.mastery.review_fraction / mastered.sum(), dtype=np.float64
            )
            reviewed[~mastered] = (1 - config.mastery.review_fraction) * weights
            return reviewed
    scores = np.asarray([record.probability(update, config) for record in records])
    weights = np.power(1 - scores, config.power)
    weights = weights / weights.sum() if weights.sum() > 0 else np.ones(len(records)) / len(records)
    recent = config.latest_fraction if latest else 0
    result: NDArray[np.float64] = np.asarray(
        (1 - config.uniform_fraction - recent) * weights, dtype=np.float64
    )
    result += config.uniform_fraction / len(records)
    if latest:
        result[-1] += recent
    result /= float(result.sum())
    return result
