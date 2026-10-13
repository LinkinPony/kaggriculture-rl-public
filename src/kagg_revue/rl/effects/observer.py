"""Optional read-only observers for complete atomic-effect rollouts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray


class EffectRolloutObserver(Protocol):
    """Observe official states and replace training-only factor labels."""

    def start_group(
        self,
        keys: Sequence[tuple[int, int]],
        engines: Sequence[Any],
        players: NDArray[np.int64],
        turns: int,
    ) -> None:
        """Start one fixed-order rollout group."""

    def begin_turn(
        self,
        engines: Sequence[Any],
        players: NDArray[np.int64],
        turn: int,
    ) -> None:
        """Observe the pre-action official state for one turn."""

    def relabel_buckets(
        self,
        buckets: Sequence[Mapping[str, Any]],
    ) -> list[Mapping[str, Any]]:
        """Replace behavior selections with labels for the observed states."""

    def finish_group(self) -> None:
        """Close one successfully exported rollout group."""


__all__ = ["EffectRolloutObserver"]
