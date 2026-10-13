"""Mutable CUDA state for one turn of autoregressive unit-task planning."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import Tensor

from kagg_revue.policy.economics.layout import EconomicStateLayout
from kagg_revue.policy.tasks.gpu.features import (
    decision_inputs,
    factorized_decision_inputs,
    resource_keys,
)
from kagg_revue.policy.tasks.gpu.transitions import apply_selection
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    TaskActions,
    TaskCatalog,
    TaskDecisionInputs,
)
from kagg_revue.policy.tasks.native import NativeTaskContract

_TASK_FIELDS = 9
_RESOURCE_BASE = 300
_ITEMS = 12


def _host_array(raw: Mapping[str, Any], key: str, dtype: np.dtype[Any]) -> np.ndarray:
    return np.ascontiguousarray(raw[key], dtype=dtype)


@dataclass
class TaskPlanningState:
    """All task-session state needed between the two native turn boundaries."""

    contract: NativeTaskContract
    layout: EconomicStateLayout
    economic_state: Tensor
    active: Tensor
    hour: Tensor
    day: Tensor
    days: Tensor
    unit_counts: Tensor
    history_counts: Tensor
    successful: Tensor
    failed: Tensor
    forced: Tensor
    prefix_fields: Tensor
    replan: Tensor
    optional: Tensor
    reasons: Tensor
    tape_sizes: Tensor
    current_unit: Tensor
    x: Tensor
    y: Tensor
    available: Tensor
    first: Tensor
    planning_count: Tensor
    target_counts: Tensor
    resource_counts: Tensor
    initial_prefix_length: int

    @classmethod
    def from_native(
        cls,
        raw: Mapping[str, Any],
        economic_state: Tensor,
        contract: NativeTaskContract,
    ) -> TaskPlanningState:
        """Move one compact snapshot to the policy device and derive conflicts."""
        if economic_state.device.type not in {"cpu", "cuda"} or economic_state.dtype not in {
            torch.int32,
            torch.int64,
        }:
            raise ValueError("unit-task planning requires compact integer state")
        batch = economic_state.shape[0]
        device = economic_state.device
        layout = EconomicStateLayout.create(contract.board_size, contract.unit_limit)
        if economic_state.shape != (batch, layout.width):
            raise ValueError("unit-task economic state differs from its compact ABI")

        def tensor(key: str, dtype: torch.dtype) -> Tensor:
            value = np.asarray(raw[key])
            return torch.as_tensor(value, dtype=dtype, device=device)

        history_host = _host_array(raw, "history_counts", np.dtype(np.int16))
        initial_prefix_length = int(history_host.max(initial=0))
        active = tensor("requires_decision", torch.bool)
        hour = tensor("hour", torch.long)
        unit_counts = tensor("unit_counts", torch.long)
        history_counts = torch.as_tensor(history_host, dtype=torch.long, device=device)
        prefix_fields = tensor("prefix_fields", torch.int32)
        replan = tensor("replan_mask", torch.bool)
        optional = tensor("optional_mask", torch.bool)
        reasons = tensor("replan_reasons", torch.long)
        tape_sizes = tensor("tape_sizes", torch.long)
        expected = {
            "active": (batch,),
            "prefix_fields": (batch, contract.prefix_capacity, _TASK_FIELDS),
            "replan": (batch, contract.unit_limit),
            "optional": (batch, contract.unit_limit),
            "reasons": (batch, contract.unit_limit),
            "tape_sizes": (batch, contract.unit_limit),
        }
        values = locals()
        for name, shape in expected.items():
            if values[name].shape != shape:
                raise ValueError(f"unit-task snapshot {name} has the wrong shape")

        current_unit = replan.to(torch.int8).argmax(dim=1).long()
        rows = torch.arange(batch, device=device)
        position_x = layout.positions + current_unit * 2
        x = economic_state[rows, position_x].long()
        y = economic_state[rows, position_x + 1].long()
        available = hour.clone()
        first = active.clone()
        planning_count = torch.zeros(batch, dtype=torch.long, device=device)

        prefix_positions = torch.arange(
            contract.prefix_capacity, device=device
        )[None]
        prefix_mask = prefix_positions < history_counts[:, None]
        record_active = prefix_mask & (prefix_fields[..., 8] == 0)
        record_unit = prefix_fields[..., 0].long().clamp(0, contract.unit_limit - 1)
        target_x = prefix_fields[..., 3].long() - 1
        target_y = prefix_fields[..., 4].long() - 1
        target_valid = record_active & (target_x >= 0) & (target_y >= 0)
        target = (target_y.clamp_min(0) * contract.board_size + target_x.clamp_min(0))
        tiles = contract.board_size * contract.board_size
        target_counts = torch.zeros(
            (batch, tiles),
            dtype=torch.int32,
            device=device,
        )
        current = current_unit[:, None]
        current_reservation = active[:, None] & (record_unit == current)
        target_valid &= ~current_reservation
        flat_target = (rows[:, None] * tiles + target).reshape(-1)
        target_counts.view(-1).scatter_add_(
            0,
            flat_target,
            target_valid.reshape(-1).to(torch.int32),
        )

        operation = prefix_fields[..., 1].long()
        argument = prefix_fields[..., 2].long() - 1
        resource = resource_keys(operation, argument, record_unit).long()
        resource_valid = record_active & ~current_reservation & (resource >= 0)
        resource_width = _RESOURCE_BASE + contract.unit_limit * _ITEMS
        resource_counts = torch.zeros(
            (batch, resource_width),
            dtype=torch.int32,
            device=device,
        )
        flat_resource = (
            rows[:, None] * resource_width
            + resource.clamp(0, resource_width - 1)
        ).reshape(-1)
        resource_counts.view(-1).scatter_add_(
            0,
            flat_resource,
            resource_valid.reshape(-1).to(torch.int32),
        )
        return cls(
            contract=contract,
            layout=layout,
            economic_state=economic_state,
            active=active,
            hour=hour,
            day=tensor("day", torch.long),
            days=tensor("days", torch.long),
            unit_counts=unit_counts,
            history_counts=history_counts,
            successful=tensor("successful_tasks", torch.long),
            failed=tensor("failed_tasks", torch.long),
            forced=tensor("forced_ends", torch.long),
            prefix_fields=prefix_fields,
            replan=replan,
            optional=optional,
            reasons=reasons,
            tape_sizes=tape_sizes,
            current_unit=current_unit,
            x=x,
            y=y,
            available=available,
            first=first,
            planning_count=planning_count,
            target_counts=target_counts,
            resource_counts=resource_counts,
            initial_prefix_length=initial_prefix_length,
        )

    def inputs(
        self,
        rows: Tensor,
        context: Tensor,
        catalog: TaskCatalog,
        *,
        prefix_length: int,
        factorized: bool = False,
        history_window: int | None = None,
    ) -> TaskDecisionInputs | FactorizedTaskDecisionInputs:
        """Build one active sub-batch of exact decision inputs."""
        if factorized:
            if history_window is None:
                raise ValueError("factorized task inputs require a history window")
            return factorized_decision_inputs(
                rows=rows,
                context=context,
                economic_state=self.economic_state,
                current_units=self.current_unit,
                x=self.x,
                y=self.y,
                available=self.available,
                first=self.first,
                planning_count=self.planning_count,
                hour=self.hour,
                day=self.day,
                days=self.days,
                unit_counts=self.unit_counts,
                history_counts=self.history_counts,
                successful=self.successful,
                failed=self.failed,
                forced=self.forced,
                optional=self.optional,
                reasons=self.reasons,
                tape_sizes=self.tape_sizes,
                prefix_fields=self.prefix_fields,
                target_counts=self.target_counts,
                resource_counts=self.resource_counts,
                layout=self.layout,
                turns=self.contract.time_token_count - 1,
                prefix_capacity=self.contract.prefix_capacity,
                prefix_length=prefix_length,
                history_window=history_window,
            )
        return decision_inputs(
            rows=rows,
            context=context,
            economic_state=self.economic_state,
            current_units=self.current_unit,
            x=self.x,
            y=self.y,
            available=self.available,
            first=self.first,
            planning_count=self.planning_count,
            hour=self.hour,
            day=self.day,
            days=self.days,
            unit_counts=self.unit_counts,
            history_counts=self.history_counts,
            successful=self.successful,
            failed=self.failed,
            forced=self.forced,
            optional=self.optional,
            reasons=self.reasons,
            tape_sizes=self.tape_sizes,
            prefix_fields=self.prefix_fields,
            target_counts=self.target_counts,
            resource_counts=self.resource_counts,
            catalog=catalog,
            layout=self.layout,
            turns=self.contract.time_token_count - 1,
            prefix_capacity=self.contract.prefix_capacity,
            prefix_length=prefix_length,
        )

    def apply(
        self,
        rows: Tensor,
        actions: TaskActions,
        catalog: TaskCatalog,
        arrivals: Tensor,
    ) -> None:
        """Apply one sampled active sub-batch to the resident planning state."""
        apply_selection(
            rows,
            actions,
            arrivals,
            catalog,
            self.economic_state,
            self.active,
            self.hour,
            self.history_counts,
            self.forced,
            self.prefix_fields,
            self.replan,
            self.optional,
            self.tape_sizes,
            self.current_unit,
            self.x,
            self.y,
            self.available,
            self.first,
            self.planning_count,
            self.target_counts,
            self.resource_counts,
            self.layout,
            self.contract.prefix_capacity,
            self.contract.time_token_count - 1,
        )


__all__ = ["TaskPlanningState"]
