"""Exact GPU construction of native unit-task decision features."""

from __future__ import annotations

import torch
from torch import Tensor

from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.tasks.contract import TaskOperation
from kagg_revue.policy.tasks.gpu.assembly import assemble_decision_inputs
from kagg_revue.policy.tasks.gpu.candidates import candidate_surface
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    TaskCatalog,
    TaskDecisionInputs,
)

_ITEMS = 12
_FERTILIZER = 8
_WHEAT = 0
_RESOURCE_WIDTH_BASE = 300


def resource_keys(operations: Tensor, arguments: Tensor, units: Tensor) -> Tensor:
    """Return the native conflict key, or -1 when no resource is reserved."""
    result = torch.full_like(operations, -1)
    result = torch.where(
        operations == int(TaskOperation.PLANT), 100 + arguments, result
    )
    result = torch.where(
        operations == int(TaskOperation.PICKUP), 200 + arguments, result
    )
    result = torch.where(
        operations == int(TaskOperation.PLACE),
        _RESOURCE_WIDTH_BASE + units * _ITEMS + arguments,
        result,
    )
    result = torch.where(
        operations == int(TaskOperation.FERTILIZE),
        _RESOURCE_WIDTH_BASE + units * _ITEMS + _FERTILIZER,
        result,
    )
    return torch.where(
        operations == int(TaskOperation.FEED),
        _RESOURCE_WIDTH_BASE + units * _ITEMS + _WHEAT,
        result,
    )


def _factorized_resource_counts(
    rows: Tensor,
    current_units: Tensor,
    resource_counts: Tensor,
) -> Tensor:
    """Gather shared seed/shed and current-unit inventory reservations."""
    selected = resource_counts.index_select(0, rows)
    shared = torch.cat((selected[:, 100:105], selected[:, 200:212]), dim=1)
    units = current_units.index_select(0, rows).long()
    items = torch.arange(_ITEMS, device=rows.device)[None]
    carried_keys = _RESOURCE_WIDTH_BASE + units[:, None] * _ITEMS + items
    carried = selected.gather(1, carried_keys)
    return torch.cat((shared, carried), dim=1)


def decision_inputs(
    *,
    rows: Tensor,
    context: Tensor,
    economic_state: Tensor,
    current_units: Tensor,
    x: Tensor,
    y: Tensor,
    available: Tensor,
    first: Tensor,
    planning_count: Tensor,
    hour: Tensor,
    day: Tensor,
    days: Tensor,
    unit_counts: Tensor,
    history_counts: Tensor,
    successful: Tensor,
    failed: Tensor,
    forced: Tensor,
    optional: Tensor,
    reasons: Tensor,
    tape_sizes: Tensor,
    prefix_fields: Tensor,
    target_counts: Tensor,
    resource_counts: Tensor,
    catalog: TaskCatalog,
    layout: EconomicStateLayout,
    turns: int,
    prefix_capacity: int,
    prefix_length: int,
) -> TaskDecisionInputs:
    """Construct the exact native decision surface without leaving CUDA."""
    features, candidate_mask, arrival = candidate_surface(
        rows,
        economic_state,
        current_units,
        x,
        y,
        available,
        target_counts,
        resource_counts,
        catalog,
        layout,
        turns,
    )
    (
        root,
        active_prefix,
        prefix_mask,
        mode_mask,
        active_available,
        day_end,
    ) = assemble_decision_inputs(
        rows,
        current_units,
        hour,
        day,
        days,
        unit_counts,
        history_counts,
        successful,
        failed,
        forced,
        optional,
        reasons,
        tape_sizes,
        x,
        y,
        available,
        first,
        planning_count,
        prefix_fields,
        unit_limit=layout.unit_limit,
        board_size=layout.board_size,
        prefix_capacity=prefix_capacity,
        turns=turns,
    )
    return TaskDecisionInputs(
        context=context.index_select(0, rows),
        root_features=root,
        prefix_fields=active_prefix,
        prefix_mask=prefix_mask,
        candidate_features=features,
        candidate_mask=candidate_mask,
        candidate_arrivals=arrival.to(torch.int16),
        mode_mask=mode_mask,
        available_at=active_available,
        day_end=day_end,
        prefix_length=prefix_length,
    )


def factorized_decision_inputs(
    *,
    rows: Tensor,
    context: Tensor,
    economic_state: Tensor,
    current_units: Tensor,
    x: Tensor,
    y: Tensor,
    available: Tensor,
    first: Tensor,
    planning_count: Tensor,
    hour: Tensor,
    day: Tensor,
    days: Tensor,
    unit_counts: Tensor,
    history_counts: Tensor,
    successful: Tensor,
    failed: Tensor,
    forced: Tensor,
    optional: Tensor,
    reasons: Tensor,
    tape_sizes: Tensor,
    prefix_fields: Tensor,
    target_counts: Tensor,
    resource_counts: Tensor,
    layout: EconomicStateLayout,
    turns: int,
    prefix_capacity: int,
    prefix_length: int,
    history_window: int,
) -> FactorizedTaskDecisionInputs:
    """Gather the compact state used by the typed decoder."""
    (
        root,
        active_prefix,
        prefix_mask,
        mode_mask,
        active_available,
        day_end,
    ) = assemble_decision_inputs(
        rows,
        current_units,
        hour,
        day,
        days,
        unit_counts,
        history_counts,
        successful,
        failed,
        forced,
        optional,
        reasons,
        tape_sizes,
        x,
        y,
        available,
        first,
        planning_count,
        prefix_fields,
        unit_limit=layout.unit_limit,
        board_size=layout.board_size,
        prefix_capacity=history_window,
        source_prefix_capacity=prefix_capacity,
        turns=turns,
    )
    return FactorizedTaskDecisionInputs(
        context=context.index_select(0, rows),
        root_features=root,
        prefix_fields=active_prefix,
        prefix_mask=prefix_mask,
        economic_state=economic_state.index_select(0, rows),
        current_unit=current_units.index_select(0, rows),
        current_x=x.index_select(0, rows),
        current_y=y.index_select(0, rows),
        target_counts=target_counts.index_select(0, rows),
        resource_counts=_factorized_resource_counts(
            rows, current_units, resource_counts
        ),
        mode_mask=mode_mask,
        available_at=active_available,
        day_end=day_end,
        prefix_length=min(prefix_length, history_window),
    )


__all__ = ["decision_inputs", "factorized_decision_inputs", "resource_keys"]
