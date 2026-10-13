"""Read-only observers overlapped with conditional-program GPU turns."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray


class ProgramRolloutObserver(Protocol):
    """Consume frozen pre-action engine states without changing behavior."""

    def start_group(
        self,
        keys: Sequence[tuple[int, int]],
        engines: Sequence[Any],
        players: NDArray[np.int64],
        turns: int,
    ) -> None:
        """Initialize storage and native sessions for one rollout group."""

    def begin_turn(
        self,
        engines: Sequence[Any],
        players: NDArray[np.int64],
    ) -> None:
        """Begin asynchronous observation of the current frozen state."""

    def finish_turn(self) -> None:
        """Release completed snapshots before the live engines are advanced."""

    def finish_group(self) -> None:
        """Publish one complete group after the official horizon."""


__all__ = ["ProgramRolloutObserver"]
