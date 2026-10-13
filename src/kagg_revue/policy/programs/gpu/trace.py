"""CUDA-resident rollout trace accumulation for conditional programs."""

# mypy: disable-error-code="no-untyped-def,untyped-decorator"

from __future__ import annotations

import numpy as np
import torch
import triton  # type: ignore[import-untyped]
import triton.language as tl  # type: ignore[import-untyped]
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.programs.grammar import ProgramDecisionInputs
from kagg_revue.policy.programs.schema import ProgramStepOutput


@triton.jit
def _append_program_trace_kernel(
    rows,
    actions,
    masks,
    quantity_max,
    joint_log_probability,
    factor_counts,
    values,
    next_hidden,
    stored_actions,
    stored_masks,
    stored_quantity_max,
    counts,
    stored_joint_log_probability,
    stored_factor_counts,
    stored_values,
    prefix_hidden,
    MAX_DECISIONS: tl.constexpr,
    ACTION_WIDTH: tl.constexpr,
    MASK_WIDTH: tl.constexpr,
    HIDDEN_WIDTH: tl.constexpr,
    BLOCK: tl.constexpr,
):
    local_row = tl.program_id(0)
    model_row = tl.load(rows + local_row)
    position = tl.load(counts + model_row)
    offset = tl.arange(0, BLOCK)
    trace_base = model_row * MAX_DECISIONS + position

    action_present = offset < ACTION_WIDTH
    action = tl.load(
        actions + local_row * ACTION_WIDTH + offset,
        mask=action_present,
        other=0,
    )
    tl.store(
        stored_actions + trace_base * ACTION_WIDTH + offset,
        action,
        mask=action_present,
    )

    mask_present = offset < MASK_WIDTH
    mask = tl.load(
        masks + local_row * MASK_WIDTH + offset,
        mask=mask_present,
        other=0,
    )
    tl.store(
        stored_masks + trace_base * MASK_WIDTH + offset,
        mask,
        mask=mask_present,
    )

    hidden_present = offset < HIDDEN_WIDTH
    hidden = tl.load(
        next_hidden + local_row * HIDDEN_WIDTH + offset,
        mask=hidden_present,
        other=0.0,
    )
    tl.store(
        prefix_hidden + model_row * HIDDEN_WIDTH + offset,
        hidden,
        mask=hidden_present,
    )

    first_lane = offset == 0
    tl.store(
        stored_quantity_max + trace_base + offset,
        tl.load(quantity_max + local_row),
        mask=first_lane,
    )
    accumulated_log_probability = tl.load(stored_joint_log_probability + model_row)
    tl.store(
        stored_joint_log_probability + model_row + offset,
        accumulated_log_probability + tl.load(joint_log_probability + local_row),
        mask=first_lane,
    )
    accumulated_factors = tl.load(stored_factor_counts + model_row)
    tl.store(
        stored_factor_counts + model_row + offset,
        accumulated_factors + tl.load(factor_counts + local_row),
        mask=first_lane,
    )
    tl.store(
        stored_values + model_row + offset,
        tl.load(values + local_row),
        mask=first_lane & (position == 0),
    )
    tl.store(counts + model_row + offset, position + 1, mask=first_lane)


class ProgramGpuTrace:
    """Append compact behavior data on CUDA and download once per turn."""

    def __init__(
        self,
        batch: int,
        maximum_decisions: int,
        mask_width: int,
        prefix_hidden: Tensor,
    ) -> None:
        """Allocate one bounded trace and retain the mutable policy prefix."""
        device = prefix_hidden.device
        hidden_width = prefix_hidden.shape[1]
        self._maximum_decisions = maximum_decisions
        self._mask_width = mask_width
        self._hidden_width = hidden_width
        self._prefix_hidden = prefix_hidden
        self._actions = torch.zeros((batch, maximum_decisions, 9), dtype=torch.int64, device=device)
        self._masks = torch.zeros(
            (batch, maximum_decisions, mask_width), dtype=torch.bool, device=device
        )
        self._quantity_max = torch.zeros(
            (batch, maximum_decisions), dtype=torch.int64, device=device
        )
        self._counts = torch.zeros(batch, dtype=torch.int16, device=device)
        self._joint_log_probability = torch.zeros(batch, dtype=torch.float32, device=device)
        self._factor_counts = torch.zeros(batch, dtype=torch.int32, device=device)
        self._values = torch.zeros(batch, dtype=torch.float32, device=device)
        self._host = tuple(
            torch.empty_like(value, device="cpu", pin_memory=True)
            for value in (
                self._actions,
                self._masks,
                self._quantity_max,
                self._counts,
                self._joint_log_probability,
                self._values,
                self._factor_counts,
            )
        )

    def append(
        self,
        rows: Tensor,
        actions: Tensor,
        masks: Tensor,
        quantity_max: Tensor,
        joint_log_probability: Tensor,
        factor_counts: Tensor,
        values: Tensor,
        next_hidden: Tensor,
        active_rows: int,
    ) -> None:
        """Append one compact graph output without synchronizing the host."""
        block = triton.next_power_of_2(max(9, self._mask_width, self._hidden_width))
        _append_program_trace_kernel[(active_rows,)](
            rows,
            actions,
            masks,
            quantity_max,
            joint_log_probability,
            factor_counts,
            values,
            next_hidden,
            self._actions,
            self._masks,
            self._quantity_max,
            self._counts,
            self._joint_log_probability,
            self._factor_counts,
            self._values,
            self._prefix_hidden,
            MAX_DECISIONS=self._maximum_decisions,
            ACTION_WIDTH=9,
            MASK_WIDTH=self._mask_width,
            HIDDEN_WIDTH=self._hidden_width,
            BLOCK=block,
            num_warps=4,
        )

    def copy_to_host(
        self,
    ) -> tuple[
        NDArray[np.int64],
        NDArray[np.bool_],
        NDArray[np.int64],
        NDArray[np.int16],
        NDArray[np.float32],
        NDArray[np.float32],
        NDArray[np.int16],
    ]:
        """Download the complete turn trace with one final synchronization."""
        device_values = (
            self._actions,
            self._masks,
            self._quantity_max,
            self._counts,
            self._joint_log_probability,
            self._values,
            self._factor_counts,
        )
        for host, value in zip(self._host, device_values, strict=True):
            host.copy_(value, non_blocking=True)
        torch.cuda.current_stream(self._actions.device).synchronize()
        return (
            self._host[0].numpy(),
            self._host[1].numpy(),
            self._host[2].numpy(),
            self._host[3].numpy(),
            self._host[4].numpy(),
            self._host[5].numpy(),
            self._host[6].numpy().astype(np.int16),
        )


@triton.jit
def _append_full_program_trace_kernel(
    rows,
    active,
    scalars,
    root,
    option,
    reservations,
    actions,
    masks,
    quantity_max,
    joint_log_probability,
    factor_counts,
    values,
    stored_scalars,
    stored_root,
    stored_option,
    stored_reservations,
    stored_actions,
    stored_masks,
    stored_quantity_max,
    counts,
    stored_joint_log_probability,
    stored_factor_counts,
    stored_values,
    MAX_DECISIONS: tl.constexpr,
    ROOT_WIDTH: tl.constexpr,
    OPTION_WIDTH: tl.constexpr,
    TILE_COUNT: tl.constexpr,
    ACTION_WIDTH: tl.constexpr,
    MASK_WIDTH: tl.constexpr,
    BLOCK: tl.constexpr,
):
    local_row = tl.program_id(0)
    enabled = tl.load(active + local_row) != 0
    model_row = tl.load(rows + local_row)
    position = tl.load(counts + model_row)
    offset = tl.arange(0, BLOCK)
    trace_base = model_row * MAX_DECISIONS + position

    scalar_present = enabled & (offset < 7)
    tl.store(
        stored_scalars + trace_base * 7 + offset,
        tl.load(scalars + local_row * 7 + offset, mask=scalar_present, other=0),
        mask=scalar_present,
    )
    root_present = enabled & (offset < ROOT_WIDTH)
    tl.store(
        stored_root + trace_base * ROOT_WIDTH + offset,
        tl.load(root + local_row * ROOT_WIDTH + offset, mask=root_present, other=0.0),
        mask=root_present,
    )
    option_present = enabled & (offset < OPTION_WIDTH)
    tl.store(
        stored_option + trace_base * OPTION_WIDTH + offset,
        tl.load(option + local_row * OPTION_WIDTH + offset, mask=option_present, other=0),
        mask=option_present,
    )
    reservation_present = enabled & (offset < TILE_COUNT)
    tl.store(
        stored_reservations + trace_base * TILE_COUNT + offset,
        tl.load(
            reservations + local_row * TILE_COUNT + offset,
            mask=reservation_present,
            other=0,
        ),
        mask=reservation_present,
    )
    action_present = enabled & (offset < ACTION_WIDTH)
    tl.store(
        stored_actions + trace_base * ACTION_WIDTH + offset,
        tl.load(
            actions + local_row * ACTION_WIDTH + offset,
            mask=action_present,
            other=0,
        ),
        mask=action_present,
    )
    mask_present = enabled & (offset < MASK_WIDTH)
    tl.store(
        stored_masks + trace_base * MASK_WIDTH + offset,
        tl.load(
            masks + local_row * MASK_WIDTH + offset,
            mask=mask_present,
            other=0,
        ),
        mask=mask_present,
    )
    first = enabled & (offset == 0)
    tl.store(
        stored_quantity_max + trace_base + offset,
        tl.load(quantity_max + local_row),
        mask=first,
    )
    old_joint = tl.load(stored_joint_log_probability + model_row)
    tl.store(
        stored_joint_log_probability + model_row + offset,
        old_joint + tl.load(joint_log_probability + local_row),
        mask=first,
    )
    old_factors = tl.load(stored_factor_counts + model_row)
    tl.store(
        stored_factor_counts + model_row + offset,
        old_factors + tl.load(factor_counts + local_row),
        mask=first,
    )
    tl.store(
        stored_values + model_row + offset,
        tl.load(values + local_row),
        mask=first & (position == 0),
    )
    tl.store(counts + model_row + offset, position + 1, mask=first)


def _full_actions(output: ProgramStepOutput) -> Tensor:
    actions = output.actions
    return torch.stack(
        (
            actions.control,
            actions.task,
            actions.target,
            actions.argument,
            actions.direction,
            actions.raw_operation,
            actions.quantity_mode,
            actions.exact_quantity,
            actions.market_order,
        ),
        dim=1,
    )


def _full_masks(output: ProgramStepOutput) -> Tensor:
    masks = output.masks
    return torch.cat(
        (
            masks.control,
            masks.direction,
            masks.task,
            masks.argument,
            masks.target,
            masks.raw_operation,
            masks.quantity_mode,
            masks.market_order,
            masks.market_item,
        ),
        dim=1,
    )


class ProgramGpuFullTrace:
    """Complete device trace for a conditional-graph turn."""

    def __init__(
        self,
        batch: int,
        maximum_decisions: int,
        root_width: int,
        option_width: int,
        tile_count: int,
        mask_width: int,
        device: torch.device,
    ) -> None:
        """Allocate fixed device and pinned-host trace storage."""
        self.maximum_decisions = maximum_decisions
        self.root_width = root_width
        self.option_width = option_width
        self.tile_count = tile_count
        self.mask_width = mask_width
        specs = (
            ((batch, maximum_decisions, 7), torch.int16),
            ((batch, maximum_decisions, root_width), torch.float32),
            ((batch, maximum_decisions, option_width), torch.int32),
            ((batch, maximum_decisions, tile_count), torch.int16),
            ((batch, maximum_decisions, 9), torch.int64),
            ((batch, maximum_decisions, mask_width), torch.bool),
            ((batch, maximum_decisions), torch.int64),
            ((batch,), torch.int16),
            ((batch,), torch.float32),
            ((batch,), torch.float32),
            ((batch,), torch.int16),
        )
        self.device_values = tuple(
            torch.zeros(shape, dtype=dtype, device=device) for shape, dtype in specs
        )
        self.host_values = tuple(
            torch.empty_like(value, device="cpu", pin_memory=True) for value in self.device_values
        )

    def reset(self) -> None:
        """Clear one turn without reallocating graph-visible addresses."""
        for value in self.device_values:
            value.zero_()

    def append(
        self,
        rows: Tensor,
        active: Tensor,
        inputs: ProgramDecisionInputs,
        output: ProgramStepOutput,
    ) -> None:
        """Append one compacted policy output without host synchronization."""
        scalars = torch.stack(
            (
                inputs.phase,
                inputs.unit_index,
                inputs.market_slot,
                inputs.unit_count,
                inputs.current_x,
                inputs.current_y,
                inputs.forced,
            ),
            dim=1,
        )
        actions = _full_actions(output)
        masks = _full_masks(output)
        block = triton.next_power_of_2(
            max(
                7,
                self.root_width,
                self.option_width,
                self.tile_count,
                9,
                self.mask_width,
            )
        )
        (
            stored_scalars,
            stored_root,
            stored_option,
            stored_reservations,
            stored_actions,
            stored_masks,
            stored_quantity_max,
            counts,
            stored_joint,
            stored_values,
            stored_factors,
        ) = self.device_values
        _append_full_program_trace_kernel[(rows.shape[0],)](
            rows,
            active,
            scalars,
            inputs.root_features,
            inputs.option_features,
            inputs.target_reservations,
            actions,
            masks,
            output.masks.quantity_max,
            output.joint_log_probability,
            output.factor_counts,
            output.value,
            stored_scalars,
            stored_root,
            stored_option,
            stored_reservations,
            stored_actions,
            stored_masks,
            stored_quantity_max,
            counts,
            stored_joint,
            stored_factors,
            stored_values,
            MAX_DECISIONS=self.maximum_decisions,
            ROOT_WIDTH=self.root_width,
            OPTION_WIDTH=self.option_width,
            TILE_COUNT=self.tile_count,
            ACTION_WIDTH=9,
            MASK_WIDTH=self.mask_width,
            BLOCK=block,
            num_warps=4,
        )

    def enqueue_to_host(self) -> None:
        """Enqueue the single turn-boundary transfer on the current stream."""
        for host, value in zip(self.host_values, self.device_values, strict=True):
            host.copy_(value, non_blocking=True)

    def enqueue_to_device(self, destinations: tuple[Tensor, ...]) -> None:
        """Persist one turn into rollout-owned HBM without visiting the host."""
        if len(destinations) != len(self.device_values):
            raise ValueError("program trace destination count differs from its ABI")
        for destination, value in zip(destinations, self.device_values, strict=True):
            if (
                destination.shape != value.shape
                or destination.dtype != value.dtype
                or destination.device != value.device
            ):
                raise ValueError("program trace destination changed shape, dtype, or device")
            destination.copy_(value, non_blocking=True)

    def host_arrays(self) -> tuple[NDArray[np.generic], ...]:
        """Expose pinned buffers after their owning stream was synchronized."""
        return tuple(value.numpy() for value in self.host_values)

    def copy_to_host(self) -> tuple[NDArray[np.generic], ...]:
        """Download all training-required fields once after the turn graph."""
        self.enqueue_to_host()
        torch.cuda.current_stream(self.device_values[0].device).synchronize()
        return self.host_arrays()


__all__ = ["ProgramGpuFullTrace", "ProgramGpuTrace"]
