"""Neural capacity and checkpoint semantics, independent of training data."""

from typing import Literal

from pydantic import Field, model_validator

from kagg_revue.configuration import FrozenSettings


class ModelSettings(FrozenSettings):
    """Model capacity and semantic identity, independent from data geometry."""

    architecture: Literal["spatial-v1", "entities-v2", "work-v1", "grounded-v1", "grounded-v2"] = (
        "spatial-v1"
    )
    depth: int = Field(default=2, gt=0)
    heads: int = Field(default=4, gt=0)
    expansion: int = Field(default=3, gt=0)
    critic_width: int = Field(default=128, gt=0)
    critic_depth: int = Field(default=0, ge=0)
    time_prior: bool = True
    prior_scale: float = Field(default=1.0, ge=0, le=1)
    operation_quantity_bias: bool = False
    market_budget: bool = False
    agronomy: bool = False
    derived: bool = False
    gated: bool = False  # Entity blocks only; temporal and fusion gates are independent.
    memory_turns: int = Field(default=0, ge=0)
    memory_width: int = Field(default=256, gt=0, multiple_of=8)
    memory_layers: int = Field(default=2, gt=0)
    memory_tokens: int = Field(default=4, gt=0)
    joint_units: bool = False  # Units decode in slot order, seeing earlier units' choices.

    @model_validator(mode="after")
    def validate_quantity_offsets(self) -> "ModelSettings":
        """Reject a checkpoint semantic switch unsupported by its decoder."""
        if self.agronomy and self.architecture != "grounded-v2":
            raise ValueError("agronomy features require grounded-v2")
        if self.joint_units and self.architecture != "grounded-v2":
            raise ValueError("joint unit decoding requires the typed grounded decoder")
        if self.derived and not self.agronomy:
            raise ValueError("derived features require the unchanged agronomy v4 prefix")
        if (self.gated or self.memory_turns) and self.architecture != "grounded-v2":
            raise ValueError("gated memory requires grounded-v2 semantics")
        if self.memory_turns and self.memory_width % self.heads:
            raise ValueError("memory width must divide by the attention head count")
        if self.market_budget and self.architecture != "grounded-v2":
            raise ValueError("market budget features require the typed grounded decoder")
        if self.operation_quantity_bias and self.architecture not in {"grounded-v1", "grounded-v2"}:
            raise ValueError("operation quantity biases require the grounded decoder")
        return self


class GeometrySettings(FrozenSettings):
    """Observation and action geometry usable without an optimizer or training data."""

    unit_limit: int = Field(gt=0)
    width: int = Field(gt=0)
    decision_interval: int = Field(gt=0)
    late_replanning_days: int = Field(default=0, ge=0)
    late_decision_interval: int | None = Field(default=None, gt=0)
    quantity_max: int = Field(gt=0)
    quantity_extra: tuple[int, ...]
    environment: dict[str, int | float]
    model: ModelSettings = Field(default_factory=ModelSettings)

    @model_validator(mode="after")
    def validate_geometry(self) -> "GeometrySettings":
        """Bind quantities, native capacity and attention dimensions consistently."""
        if self.width % self.model.heads or self.unit_limit > 32:
            raise ValueError("attention width must divide by head count and units must fit the ABI")
        if self.model.critic_depth and self.model.critic_width % self.model.heads:
            raise ValueError("critic width must divide by attention head count")
        if any(q <= self.quantity_max for q in self.quantity_extra):
            raise ValueError("extra quantity symbols must extend the exact integer range")
        required = {"episodeSteps", "boardSize", "turnsPerDay", "maxMarketOrdersPerTurn"}
        if not required <= self.environment.keys():
            raise ValueError("environment must specify official horizon and action geometry")
        if self.environment["episodeSteps"] < 2:
            raise ValueError("a game must have at least one transition")
        if bool(self.late_replanning_days) != (self.late_decision_interval is not None):
            raise ValueError("late replanning requires both a day count and an interval")
        return self

    @property
    def quantities(self) -> tuple[int, ...]:
        """Return the exact action quantity vocabulary."""
        return tuple(range(1, self.quantity_max + 1)) + tuple(sorted(set(self.quantity_extra)))

    @property
    def turns(self) -> int:
        """Return actual engine transitions, excluding the terminal observation."""
        return int(self.environment["episodeSteps"]) - 1
