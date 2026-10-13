"""Canonical tensor grammar for incremental production portfolios."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.plans.observation import (
    BOARD_SHAPE,
    ECONOMIC_STATE_FEATURES,
    GLOBAL_FEATURES,
    UNIT_SHAPE,
)

PRODUCTION_LINES = 8
LINE_FIELDS = 6
GLOBAL_FIELDS = 10

MODE_TOKENS = 2
LINE_OPERATION_TOKENS = 3
GLOBAL_OPERATION_TOKENS = 2
LINE_VALUE_TOKENS = 16
GLOBAL_VALUE_TOKENS = 16

_CASH_RESERVE_FIELD = 2
_SPEND_CAP_FIELD = 3
_INITIAL_CASH_RESERVE_MAX_TOKEN = 9
_INITIAL_SPEND_CAP_MIN_TOKEN = 5

CONTINUE = 0
STOP = 1

LINE_KEEP = 0
UPSERT = 1
RETIRE = 2

GLOBAL_KEEP = 0
GLOBAL_SET = 1

# Target, scale mode, priority, output reserve, price policy, optional yield.
LINE_FIELD_CARDINALITIES = (16, 2, 16, 16, 5, 2)
# Worker ceiling, land ceiling, cash reserve, spend cap, six task priorities.
GLOBAL_FIELD_CARDINALITIES = (16, 4, 16, 16, 16, 16, 16, 16, 16, 16)


def factor_width(
    production_lines: int = PRODUCTION_LINES,
    line_fields: int = LINE_FIELDS,
    global_fields: int = GLOBAL_FIELDS,
) -> int:
    """Return the fixed complete-action factor layout width."""
    return 1 + production_lines * (1 + line_fields) + 1 + global_fields


FACTOR_WIDTH = factor_width()


def _is_discrete(value: Tensor) -> bool:
    return not value.is_floating_point() and value.dtype != torch.bool


def _validate_cardinalities(
    values: Tensor,
    cardinalities: tuple[int, ...],
    name: str,
    *,
    rows: Tensor | None = None,
) -> None:
    selected = values if rows is None else values[rows]
    if selected.numel() == 0:
        return
    limits = torch.tensor(cardinalities, device=values.device)
    if bool(torch.any((selected < 0) | (selected >= limits))):
        raise ValueError(f"structured-plan {name} contains an invalid token")


@dataclass(frozen=True)
class PlanInputs:
    """Actor-visible inputs and the currently committed portfolio."""

    board: Tensor
    units: Tensor
    global_features: Tensor
    economic_state: Tensor
    features: Tensor
    journal: Tensor
    events: Tensor
    active_lines: Tensor
    active_line_mask: Tensor
    global_plan: Tensor

    @property
    def batch_size(self) -> int:
        """Return the number of independent decision roots."""
        return int(self.features.shape[0])

    @property
    def production_lines(self) -> int:
        """Return the fixed number of independently addressable line identities."""
        return int(self.active_lines.shape[1])

    def validate(
        self,
        *,
        observation_features: int,
        journal_features: int,
        event_features: int,
        production_lines: int,
        line_fields: int,
        global_fields: int,
        board_shape: tuple[int, int, int, int] = BOARD_SHAPE,
        unit_shape: tuple[int, int, int] = UNIT_SHAPE,
        global_features: int = GLOBAL_FEATURES,
        economic_state_features: int = ECONOMIC_STATE_FEATURES,
        validate_values: bool = True,
    ) -> None:
        """Reject tensors that do not follow the versioned portfolio ABI."""
        batch = self.batch_size
        expected = {
            "board": (batch, *board_shape),
            "units": (batch, *unit_shape),
            "global_features": (batch, global_features),
            "economic_state": (batch, economic_state_features),
            "features": (batch, observation_features),
            "journal": (batch, journal_features),
            "events": (batch, event_features),
            "active_lines": (batch, production_lines, line_fields),
            "active_line_mask": (batch, production_lines),
            "global_plan": (batch, global_fields),
        }
        for name, shape in expected.items():
            if getattr(self, name).shape != shape:
                raise ValueError(f"structured-plan {name} has the wrong shape")
        if not all(
            value.device == self.features.device
            for value in (
                self.board,
                self.units,
                self.global_features,
                self.economic_state,
                self.journal,
                self.events,
                self.active_lines,
                self.active_line_mask,
                self.global_plan,
            )
        ):
            raise ValueError("structured-plan inputs must share one device")
        if not all(
            value.is_floating_point()
            for value in (
                self.board,
                self.units,
                self.global_features,
                self.features,
                self.journal,
                self.events,
            )
        ):
            raise ValueError("structured-plan numeric observations must be floating point")
        if not _is_discrete(self.economic_state):
            raise ValueError("structured-plan economic state must use an integer tensor")
        if not _is_discrete(self.active_lines) or not _is_discrete(self.global_plan):
            raise ValueError("structured-plan portfolio tokens must use integer tensors")
        if self.active_line_mask.is_floating_point():
            raise ValueError("structured-plan active-line mask must be discrete")
        if not validate_values:
            return
        active = self.active_line_mask.bool()
        if bool(torch.any(self.active_lines[~active] != 0)):
            raise ValueError("inactive structured-plan lines must have canonical zero fields")
        _validate_cardinalities(
            self.active_lines,
            LINE_FIELD_CARDINALITIES,
            "active line",
            rows=active,
        )
        if bool(torch.any(active & (self.active_lines[..., 0] == 0))):
            raise ValueError("active structured-plan lines need a nonzero target")
        _validate_cardinalities(
            self.global_plan,
            GLOBAL_FIELD_CARDINALITIES,
            "global plan",
        )


@dataclass(frozen=True)
class PlanActions:
    """One canonical root decision and sparse portfolio patch."""

    mode: Tensor
    line_operations: Tensor
    line_values: Tensor
    global_operation: Tensor
    global_values: Tensor

    def validate(
        self,
        batch_size: int,
        production_lines: int,
        line_fields: int,
        global_fields: int,
    ) -> None:
        """Validate action shapes before teacher-forced likelihood replay."""
        expected = {
            "mode": (batch_size,),
            "line_operations": (batch_size, production_lines),
            "line_values": (batch_size, production_lines, line_fields),
            "global_operation": (batch_size,),
            "global_values": (batch_size, global_fields),
        }
        for name, shape in expected.items():
            value = getattr(self, name)
            if value.shape != shape:
                raise ValueError(f"structured-plan action {name} has the wrong shape")
            if not _is_discrete(value):
                raise ValueError("structured-plan action tokens must use integer tensors")


@dataclass(frozen=True)
class PlanConditionalMasks:
    """Every exact conditional legal mask for one complete portfolio action."""

    mode: Tensor
    line_operations: Tensor
    line_values: Tensor
    global_operation: Tensor
    global_values: Tensor
    factors: Tensor

    def validate(
        self,
        batch_size: int,
        production_lines: int,
        line_fields: int,
        global_fields: int,
    ) -> None:
        """Validate the complete conditional-mask layout."""
        expected = {
            "mode": (batch_size, MODE_TOKENS),
            "line_operations": (
                batch_size,
                production_lines,
                LINE_OPERATION_TOKENS,
            ),
            "line_values": (
                batch_size,
                production_lines,
                line_fields,
                LINE_VALUE_TOKENS,
            ),
            "global_operation": (batch_size, GLOBAL_OPERATION_TOKENS),
            "global_values": (
                batch_size,
                global_fields,
                GLOBAL_VALUE_TOKENS,
            ),
            "factors": (
                batch_size,
                factor_width(production_lines, line_fields, global_fields),
            ),
        }
        for name, shape in expected.items():
            if getattr(self, name).shape != shape:
                raise ValueError(f"structured-plan {name} mask has the wrong shape")

    def to(
        self,
        device: torch.device | str,
        *,
        non_blocking: bool = False,
    ) -> PlanConditionalMasks:
        """Move all masks together without changing boolean semantics."""
        return PlanConditionalMasks(
            mode=self.mode.to(device, non_blocking=non_blocking),
            line_operations=self.line_operations.to(
                device,
                non_blocking=non_blocking,
            ),
            line_values=self.line_values.to(device, non_blocking=non_blocking),
            global_operation=self.global_operation.to(
                device,
                non_blocking=non_blocking,
            ),
            global_values=self.global_values.to(
                device,
                non_blocking=non_blocking,
            ),
            factors=self.factors.to(device, non_blocking=non_blocking),
        )


def mode_mask(active_portfolio: Tensor) -> Tensor:
    """Keep STOP available only after a closed portfolio exists."""
    active = active_portfolio.bool()
    result = torch.zeros(
        (active.shape[0], MODE_TOKENS),
        dtype=torch.bool,
        device=active.device,
    )
    result[:, CONTINUE] = True
    result[:, STOP] = active
    return result


def line_operation_mask(
    active_line: Tensor,
    *,
    force_upsert: Tensor | None = None,
) -> Tensor:
    """Return line updates independently of the execution mode."""
    active = active_line.bool()
    result = torch.zeros(
        (active.shape[0], LINE_OPERATION_TOKENS),
        dtype=torch.bool,
        device=active.device,
    )
    result[:, LINE_KEEP] = True
    result[:, UPSERT] = True
    result[:, RETIRE] = active
    if force_upsert is not None:
        forced = force_upsert.bool()
        result[forced] = False
        result[forced, UPSERT] = True
    return result


def line_field_mask(field: int, upsert: Tensor) -> Tensor:
    """Return the field vocabulary, with canonical zero outside UPSERT."""
    if not 0 <= field < LINE_FIELDS:
        raise ValueError("structured-plan line field is outside the ABI")
    active = upsert.bool()
    result = torch.zeros(
        (active.shape[0], LINE_VALUE_TOKENS),
        dtype=torch.bool,
        device=active.device,
    )
    result[~active, 0] = True
    start = 1 if field == 0 else 0
    result[active, start : LINE_FIELD_CARDINALITIES[field]] = True
    return result


def global_operation_mask(initial: Tensor) -> Tensor:
    """Return KEEP/SET legality, forcing a closed initial global plan."""
    initial_rows = initial.bool()
    result = torch.zeros(
        (initial_rows.shape[0], GLOBAL_OPERATION_TOKENS),
        dtype=torch.bool,
        device=initial_rows.device,
    )
    result[:, GLOBAL_KEEP] = True
    result[:, GLOBAL_SET] = True
    result[initial_rows, GLOBAL_KEEP] = False
    return result


def global_field_mask(
    field: int,
    update: Tensor,
    *,
    initial: Tensor | None = None,
) -> Tensor:
    """Return global legality, including executable initial-budget bounds."""
    if not 0 <= field < GLOBAL_FIELDS:
        raise ValueError("structured-plan global field is outside the ABI")
    active = update.bool()
    initial_rows = torch.zeros_like(active) if initial is None else initial.bool()
    result = torch.zeros(
        (active.shape[0], GLOBAL_VALUE_TOKENS),
        dtype=torch.bool,
        device=active.device,
    )
    result[~active, 0] = True
    result[active, : GLOBAL_FIELD_CARDINALITIES[field]] = True
    if field == _CASH_RESERVE_FIELD:
        result[initial_rows, _INITIAL_CASH_RESERVE_MAX_TOKEN + 1 :] = False
    elif field == _SPEND_CAP_FIELD:
        result[initial_rows, :_INITIAL_SPEND_CAP_MIN_TOKEN] = False
    return result


__all__ = [
    "CONTINUE",
    "FACTOR_WIDTH",
    "GLOBAL_FIELDS",
    "GLOBAL_FIELD_CARDINALITIES",
    "GLOBAL_KEEP",
    "GLOBAL_OPERATION_TOKENS",
    "GLOBAL_SET",
    "GLOBAL_VALUE_TOKENS",
    "LINE_FIELDS",
    "LINE_FIELD_CARDINALITIES",
    "LINE_KEEP",
    "LINE_OPERATION_TOKENS",
    "LINE_VALUE_TOKENS",
    "MODE_TOKENS",
    "PRODUCTION_LINES",
    "PlanActions",
    "PlanConditionalMasks",
    "PlanInputs",
    "RETIRE",
    "STOP",
    "UPSERT",
    "factor_width",
    "global_field_mask",
    "global_operation_mask",
    "line_field_mask",
    "line_operation_mask",
    "mode_mask",
]
