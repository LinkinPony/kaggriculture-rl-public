"""Direct-match collapse quarantine for structured-plan PPO."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

PLAN_HEALTH_STATE_VERSION = "structured-plan-collapse-health-v1"


@dataclass(frozen=True)
class PlanHealthObservation:
    """One update's behavior and direct matchup against the selected history."""

    update: int
    opponent_update: int
    stop_fraction: float
    plan_change_fraction: float
    wins: int
    ties: int
    losses: int

    def __post_init__(self) -> None:
        """Validate direct outcomes and bounded empirical fractions."""
        integer_fields = (
            self.update,
            self.opponent_update,
            self.wins,
            self.ties,
            self.losses,
        )
        if any(
            not isinstance(value, int) or isinstance(value, bool)
            for value in integer_fields
        ):
            raise ValueError("structured-plan health counts are invalid")
        if (
            self.update < 1
            or self.opponent_update < 0
            or self.opponent_update >= self.update
            or min(self.wins, self.ties, self.losses) < 0
            or self.games < 1
        ):
            raise ValueError("structured-plan health matchup is invalid")
        if not 0.0 <= self.stop_fraction <= 1.0 or not (
            0.0 <= self.plan_change_fraction <= 1.0
        ):
            raise ValueError("structured-plan health behavior fractions are invalid")

    @property
    def games(self) -> int:
        """Return the complete-match panel size."""
        return self.wins + self.ties + self.losses

    @property
    def loss_rate(self) -> float:
        """Return direct loss frequency without constructing a proxy score."""
        return self.losses / self.games

    def payload(self) -> dict[str, int | float]:
        """Return the checkpoint-safe observation payload."""
        return {
            "update": self.update,
            "opponent_update": self.opponent_update,
            "stop_fraction": self.stop_fraction,
            "plan_change_fraction": self.plan_change_fraction,
            "wins": self.wins,
            "ties": self.ties,
            "losses": self.losses,
        }

    def summary(self) -> dict[str, int | float]:
        """Return the direct diagnostic surface."""
        return {**self.payload(), "games": self.games, "loss_rate": self.loss_rate}


class PlanCollapseGuard:
    """Quarantine repeated action stasis that directly loses to update zero."""

    def __init__(
        self,
        *,
        warmup_updates: int,
        anchor_panels: int,
        stop_fraction_floor: float,
        plan_change_fraction_ceiling: float,
        anchor_loss_rate_floor: float,
    ) -> None:
        """Bind a conservative conjunction over recent anchor match panels."""
        if warmup_updates < 0:
            raise ValueError("structured-plan health warmup cannot be negative")
        if anchor_panels < 2:
            raise ValueError("structured-plan health needs repeated anchor panels")
        if any(
            not 0.0 <= value <= 1.0
            for value in (
                stop_fraction_floor,
                plan_change_fraction_ceiling,
                anchor_loss_rate_floor,
            )
        ):
            raise ValueError("structured-plan health thresholds must be probabilities")
        self._warmup_updates = warmup_updates
        self._anchor_panels = anchor_panels
        self._stop_fraction_floor = stop_fraction_floor
        self._plan_change_fraction_ceiling = plan_change_fraction_ceiling
        self._anchor_loss_rate_floor = anchor_loss_rate_floor
        self._recent_anchor: deque[PlanHealthObservation] = deque(
            maxlen=anchor_panels
        )
        self._quarantined = False

    @property
    def quarantined(self) -> bool:
        """Return whether this lineage must stop before producing more updates."""
        return self._quarantined

    def _collapsed(self, observation: PlanHealthObservation) -> bool:
        return (
            observation.stop_fraction >= self._stop_fraction_floor
            and observation.plan_change_fraction
            <= self._plan_change_fraction_ceiling
            and observation.loss_rate >= self._anchor_loss_rate_floor
        )

    def observe(self, observation: PlanHealthObservation) -> dict[str, object]:
        """Record one update and return a sticky quarantine decision."""
        if self._recent_anchor and observation.update <= self._recent_anchor[-1].update:
            raise ValueError("structured-plan health updates must increase")
        if observation.opponent_update == 0:
            self._recent_anchor.append(observation)
        if (
            observation.update >= self._warmup_updates
            and len(self._recent_anchor) == self._anchor_panels
            and all(self._collapsed(item) for item in self._recent_anchor)
        ):
            self._quarantined = True
        return self.report(observation)

    def report(
        self,
        current: PlanHealthObservation | None = None,
    ) -> dict[str, object]:
        """Return the evidence behind the current quarantine state."""
        return {
            "kind": "repeated-direct-anchor-loss-and-action-stasis",
            "quarantined": self._quarantined,
            "current": None if current is None else current.summary(),
            "recent_anchor_panels": [
                {
                    **observation.summary(),
                    "collapsed": self._collapsed(observation),
                }
                for observation in self._recent_anchor
            ],
        }

    def state_dict(self) -> dict[str, object]:
        """Return update-boundary state needed for exact resume semantics."""
        return {
            "state_version": PLAN_HEALTH_STATE_VERSION,
            "quarantined": self._quarantined,
            "recent_anchor_panels": [
                observation.payload() for observation in self._recent_anchor
            ],
        }

    def load_state_dict(self, value: object, *, completed_update: int) -> None:
        """Validate and restore the bounded anchor evidence window."""
        if not isinstance(value, Mapping) or set(value) != {
            "state_version",
            "quarantined",
            "recent_anchor_panels",
        }:
            raise ValueError("structured-plan health checkpoint is incomplete")
        raw_quarantined = value.get("quarantined")
        raw_observations = value.get("recent_anchor_panels")
        if (
            value.get("state_version") != PLAN_HEALTH_STATE_VERSION
            or not isinstance(raw_quarantined, bool)
            or not isinstance(raw_observations, list)
            or len(raw_observations) > self._anchor_panels
        ):
            raise ValueError("structured-plan health checkpoint contract differs")
        observations: list[PlanHealthObservation] = []
        for raw_observation in raw_observations:
            if not isinstance(raw_observation, Mapping) or set(raw_observation) != {
                "update",
                "opponent_update",
                "stop_fraction",
                "plan_change_fraction",
                "wins",
                "ties",
                "losses",
            }:
                raise ValueError("structured-plan health observation is incomplete")
            raw_update = raw_observation.get("update")
            raw_opponent_update = raw_observation.get("opponent_update")
            raw_wins = raw_observation.get("wins")
            raw_ties = raw_observation.get("ties")
            raw_losses = raw_observation.get("losses")
            raw_stop = raw_observation.get("stop_fraction")
            raw_change = raw_observation.get("plan_change_fraction")
            if any(
                not isinstance(item, int) or isinstance(item, bool)
                for item in (
                    raw_update,
                    raw_opponent_update,
                    raw_wins,
                    raw_ties,
                    raw_losses,
                )
            ) or any(
                not isinstance(item, (int, float)) or isinstance(item, bool)
                for item in (raw_stop, raw_change)
            ):
                raise ValueError("structured-plan health observation is invalid")
            try:
                observation = PlanHealthObservation(
                    update=cast(int, raw_update),
                    opponent_update=cast(int, raw_opponent_update),
                    stop_fraction=float(cast(float, raw_stop)),
                    plan_change_fraction=float(cast(float, raw_change)),
                    wins=cast(int, raw_wins),
                    ties=cast(int, raw_ties),
                    losses=cast(int, raw_losses),
                )
            except ValueError as error:
                raise ValueError(
                    "structured-plan health observation is invalid"
                ) from error
            if (
                observation.opponent_update != 0
                or observation.update > completed_update
                or (
                    observations
                    and observation.update <= observations[-1].update
                )
            ):
                raise ValueError("structured-plan health observation lies outside the run")
            observations.append(observation)
        if raw_quarantined and not (
            len(observations) == self._anchor_panels
            and all(self._collapsed(observation) for observation in observations)
            and observations[-1].update >= self._warmup_updates
        ):
            raise ValueError("structured-plan health quarantine lacks direct evidence")
        self._recent_anchor = deque(observations, maxlen=self._anchor_panels)
        self._quarantined = raw_quarantined


__all__ = [
    "PLAN_HEALTH_STATE_VERSION",
    "PlanCollapseGuard",
    "PlanHealthObservation",
]
