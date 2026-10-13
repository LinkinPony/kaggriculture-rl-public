"""Checkpointed observation, action and decision-clock contracts."""

from dataclasses import asdict, dataclass, replace
from typing import Any

from kagg_revue.native.features import Layout
from kagg_revue.policy.settings import GeometrySettings


@dataclass(frozen=True)
class NetworkShape:
    """Checkpointed network semantics; old checkpoints retain their original model."""

    architecture: str = "spatial-v1"
    depth: int = 2
    heads: int = 4
    expansion: int = 3
    critic_width: int = 128
    critic_depth: int = 0
    time_prior: bool = True
    prior_scale: float = 1.0
    operation_quantity_bias: bool = False
    market_budget: bool = False
    agronomy: bool = False
    derived: bool = False
    gated: bool = False  # Entity encoder gates; memory keeps its own gated residuals.
    memory_turns: int = 0
    memory_width: int = 256
    memory_layers: int = 2
    memory_tokens: int = 4
    joint_units: bool = False


def layout_record(layout: "ContractLayout") -> dict[str, Any]:
    """Serialize a layout, omitting a disabled joint decoder to keep archived identities."""
    record = asdict(layout)
    if not layout.network.joint_units:
        record["network"].pop("joint_units")
    return record


@dataclass(frozen=True)
class ContractLayout:
    """One categorical factor per operating choice, with spatial roles."""

    observation: Layout
    board_size: int
    interval: int
    network: NetworkShape = NetworkShape()
    late_start: int = 0
    late_interval: int = 0

    def same_interface(self, other: "ContractLayout") -> bool:
        """Compare executable semantics independently of network capacity and priors."""
        return (
            self.board_size == other.board_size
            and self.work == other.work
            and self.starts == other.starts
            and self.spans == other.spans
            and self.cardinalities == other.cardinalities
            and replace(self.observation, width=0) == replace(other.observation, width=0)
        )

    @property
    def cells(self) -> int:
        """Return independently controlled production locations."""
        return self.board_size**2

    @property
    def factors(self) -> int:
        """Return all spatial, workforce and market factors."""
        if self.work:
            return self.work_factors + self.capacity * self.observation.markets * 2
        return self.cells * 4 + 5 + 18

    @property
    def cardinalities(self) -> list[int]:
        """Return action semantics shared with the native contract validator."""
        if self.work:
            quantities = len(self.observation.quantities)
            return [self.cells + 1, 44, quantities, self.capacity] * (
                self.observation.units * (self.capacity + 1)
            ) + [23, quantities] * (self.capacity * self.observation.markets)
        return [10, 4, 4, 4] * self.cells + [self.observation.units, 4, 16, 16, 16] + [16] * 18

    @property
    def work(self) -> bool:
        """Identify the checkpointed ordered-work and explicit-market language."""
        return self.network.architecture in {"work-v1", "grounded-v1", "grounded-v2"}

    @property
    def capacity(self) -> int:
        """Return the largest actual execution interval."""
        return max(self.spans)

    @property
    def work_factors(self) -> int:
        """Return destination, operation, quantity and release fields for all jobs."""
        return self.observation.units * (self.capacity + 1) * 4

    @property
    def vocabulary_size(self) -> int:
        """Return the dense neural vocabulary width required by the action ABI."""
        return max(self.cardinalities) if self.work else 32

    @property
    def decisions(self) -> int:
        """Return the number of complete macro transitions in one game."""
        return len(self.starts)

    @property
    def starts(self) -> tuple[int, ...]:
        """Return official turn boundaries, including optional finer terminal control."""
        if self.late_interval:
            return (
                *range(0, self.late_start, self.interval),
                *range(self.late_start, self.observation.turns, self.late_interval),
            )
        return tuple(range(0, self.observation.turns, self.interval))

    @property
    def spans(self) -> tuple[int, ...]:
        """Cover each official transition exactly once, including the partial final interval."""
        starts = self.starts
        ends = (*starts[1:], self.observation.turns)
        return tuple(end - start for start, end in zip(starts, ends, strict=True))

    @classmethod
    def resolve(cls, settings: GeometrySettings) -> "ContractLayout":
        """Bind the real game geometry to one explicit replanning cadence."""
        return cls(
            Layout.resolve(settings),
            int(settings.environment["boardSize"]),
            settings.decision_interval,
            NetworkShape(**settings.model.model_dump()),
            max(
                0,
                (
                    (settings.turns + int(settings.environment["turnsPerDay"]) - 1)
                    // int(settings.environment["turnsPerDay"])
                    - settings.late_replanning_days
                )
                * int(settings.environment["turnsPerDay"]),
            )
            if settings.late_replanning_days
            else 0,
            settings.late_decision_interval or 0,
        )
