"""Actor-visible policy conservation bounds for derived-facts-v1."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

IntArray = NDArray[np.int64]
FloatArray = NDArray[np.float32]
_INT64_MAX = np.iinfo(np.int64).max


def _vector(snapshot: Mapping[str, Any], name: str, products: int) -> IntArray:
    value = np.asarray(snapshot[name], dtype=np.int64)
    if value.shape != (products,):
        raise ValueError(f"{name} must have one value per product")
    return value.copy()


def _saturate(value: int) -> np.int64:
    return np.int64(max(0, min(value, int(_INT64_MAX))))


@dataclass
class OpponentInventoryBounds:
    """Conservative product-holding bounds from public market flow.

    The upper bound adds every product harvest or fertilizer collection the
    opponent could have completed from its visible unit positions. Public
    market conservation then subtracts the smallest opponent inventory
    contribution compatible with our own requested order bounds. Price-floor
    sales and shed overflow can only reduce true holdings, so ignoring them
    preserves the upper-bound invariant.
    """

    products: int
    lower: IntArray = field(init=False)
    upper: IntArray = field(init=False)
    _step: int | None = field(init=False, default=None)
    _market: IntArray | None = field(init=False, default=None)
    _town: IntArray | None = field(init=False, default=None)
    _unit_gain: IntArray | None = field(init=False, default=None)
    _own_flow: IntArray | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Allocate fixed-width nonnegative bounds."""
        if self.products < 1:
            raise ValueError("products must be positive")
        self.lower = np.zeros(self.products, dtype=np.int64)
        self.upper = np.zeros(self.products, dtype=np.int64)

    def reset(self) -> None:
        """Forget episode-local public-flow history."""
        self.lower.fill(0)
        self.upper.fill(0)
        self._step = None
        self._market = None
        self._town = None
        self._unit_gain = None
        self._own_flow = None

    def update(self, snapshot: Mapping[str, Any]) -> tuple[IntArray, IntArray]:
        """Consume the next public snapshot and return safe current bounds."""
        raw_step = snapshot["step"]
        if not isinstance(raw_step, int) or isinstance(raw_step, bool) or raw_step < 0:
            raise ValueError("flow snapshot step must be a nonnegative integer")
        step = raw_step
        market = _vector(snapshot, "market_inventory", self.products)
        town = _vector(snapshot, "town_consumption", self.products)
        unit_gain = _vector(snapshot, "opponent_unit_gain_upper", self.products)
        if np.any(town < 0) or np.any(unit_gain < 0):
            raise ValueError("flow snapshot bounds cannot be negative")

        contiguous = self._step is not None and step == self._step + 1
        if step == 0:
            self.reset()
        elif not contiguous:
            self.reset()
            # A mid-episode attachment has no authenticated prefix from which
            # to derive a finite inventory upper bound.
            self.upper.fill(_INT64_MAX)
        elif (
            self._market is not None
            and self._town is not None
            and self._unit_gain is not None
            and self._own_flow is not None
        ):
            for product in range(self.products):
                public_net = (
                    int(market[product]) - int(self._market[product]) + int(self._town[product])
                )
                own_maximum = int(self._own_flow[product, 1])
                opponent_minimum = public_net - own_maximum
                next_upper = (
                    int(self.upper[product]) + int(self._unit_gain[product]) - opponent_minimum
                )
                self.upper[product] = _saturate(next_upper)
        else:
            self.upper.fill(_INT64_MAX)

        self.lower.fill(0)
        self._step = step
        self._market = market
        self._town = town
        self._unit_gain = unit_gain
        self._own_flow = None
        return self.lower.copy(), self.upper.copy()

    def record_own_flow(self, bounds: Any) -> None:
        """Record selected-order public inventory effects for the next update."""
        value = np.asarray(bounds, dtype=np.int64)
        if value.shape != (self.products, 2):
            raise ValueError("own market flow bounds must have shape [products, 2]")
        if np.any(value[:, 0] > value[:, 1]):
            raise ValueError("own market flow lower bound exceeds its upper bound")
        self._own_flow = value.copy()


@dataclass(frozen=True)
class DerivedFactTurn:
    """Fact tensors aligned with one complete numeric action sequence."""

    turn: FloatArray
    prefix: FloatArray
    candidates: FloatArray


class DerivedFactEpisodeEncoder:
    """Replay actor-visible facts through the same native session as deployment."""

    def __init__(self, products: int) -> None:
        """Create episode-local hidden-inventory bounds."""
        self._bounds = OpponentInventoryBounds(products)

    def reset(self) -> None:
        """Reset all actor-visible history at an episode boundary."""
        self._bounds.reset()

    def encode_turn(
        self,
        session: Any,
        tokens: Sequence[int] | IntArray,
        quantities: Sequence[int] | IntArray,
    ) -> DerivedFactTurn:
        """Encode facts before replaying each selected numeric decision."""
        token_values = np.asarray(tokens, dtype=np.int64)
        quantity_values = np.asarray(quantities, dtype=np.int64)
        if (
            token_values.ndim != 1
            or quantity_values.ndim != 1
            or token_values.shape != quantity_values.shape
        ):
            raise ValueError("fact replay tokens and quantities must be matching vectors")

        lower, upper = self._bounds.update(session.flow_snapshot())
        turn = np.asarray(session.turn_facts(lower, upper), dtype=np.float32)
        prefixes: list[FloatArray] = []
        candidates: list[FloatArray] = []
        for token, quantity in zip(token_values, quantity_values, strict=True):
            prefixes.append(np.asarray(session.prefix_facts(), dtype=np.float32))
            candidates.append(np.asarray(session.candidate_facts(), dtype=np.float32))
            session.select(int(token), int(quantity))
        if int(session.phase) != 2:
            raise ValueError("fact replay action is incomplete")
        self._bounds.record_own_flow(session.own_market_flow_bounds())
        if not prefixes:
            raise ValueError("fact replay action has no decisions")
        return DerivedFactTurn(
            turn=turn,
            prefix=np.stack(prefixes),
            candidates=np.stack(candidates),
        )


__all__ = [
    "DerivedFactEpisodeEncoder",
    "DerivedFactTurn",
    "OpponentInventoryBounds",
]
