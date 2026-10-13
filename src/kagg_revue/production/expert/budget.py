"""Bound repeated fitting to an unchanged expert without counting searches as learning."""

from dataclasses import dataclass


@dataclass
class LearningBudget:
    """Persist actual fitting and optimizer counts independently of search rounds."""

    fits: int = 0
    optimizer_steps: int = 0

    def available(self, limit: int | None) -> bool:
        """Allow unlimited baseline fitting or a bounded number per accepted expert."""
        return limit is None or self.fits < limit

    def renew(self) -> None:
        """Only a newly accepted expert renews its fitting budget."""
        self.fits = 0

    def record(self, steps: int) -> None:
        """Count only completed gradient learning, keeping lifetime optimizer progress."""
        self.fits += 1
        self.optimizer_steps += steps
