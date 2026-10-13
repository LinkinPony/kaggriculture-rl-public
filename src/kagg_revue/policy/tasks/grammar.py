"""Tensor grammar and exact conditional masks for unit-task decisions."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.tasks.contract import SuffixMode, TaskOperation

TASK_FACTOR_COUNT = 5
FACTORIZED_TASK_FACTOR_COUNT = 7
NONE_ARGUMENT = 12
FACTORIZED_RESOURCE_COUNT = 5 + 12 + 12


def _is_discrete(value: Tensor) -> bool:
    return not value.is_floating_point() and value.dtype != torch.bool


@dataclass(frozen=True)
class TaskCatalog:
    """Static joint operation-argument-target catalog from the native ABI."""

    operations: Tensor
    arguments: Tensor
    targets: Tensor
    requires_quantity: Tensor
    operation_turns: Tensor

    @property
    def candidate_count(self) -> int:
        """Return the fixed catalog width."""
        return int(self.operations.numel())

    def validate(self) -> None:
        """Reject a catalog that can introduce aliases or movement actions."""
        candidates = self.candidate_count
        if candidates < 2:
            raise ValueError("unit-task catalog needs END and semantic tasks")
        if self.operations.shape != (candidates,):
            raise ValueError("unit-task catalog operations must be a vector")
        if self.arguments.shape != (candidates,):
            raise ValueError("unit-task catalog arguments must be a vector")
        if self.targets.shape != (candidates, 2):
            raise ValueError("unit-task catalog targets must have shape [C,2]")
        if self.requires_quantity.shape != (candidates,):
            raise ValueError("unit-task quantity flags must be a vector")
        if self.operation_turns.shape != (candidates,):
            raise ValueError("unit-task operation durations must be a vector")
        if not all(
            _is_discrete(value)
            for value in (
                self.operations,
                self.arguments,
                self.targets,
                self.operation_turns,
            )
        ):
            raise ValueError("unit-task catalog identities must use integer tensors")
        if self.requires_quantity.is_floating_point():
            raise ValueError("unit-task quantity flags must be discrete")
        if int(self.operations[0]) != int(TaskOperation.END):
            raise ValueError("unit-task candidate zero must be END")
        if bool(torch.any(self.operations[1:] == int(TaskOperation.END))):
            raise ValueError("unit-task END must have one canonical spelling")
        if bool(
            torch.any(
                (self.operations < int(TaskOperation.END))
                | (self.operations > int(TaskOperation.CARE))
            )
        ):
            raise ValueError("unit-task catalog contains an unknown operation")
        expected_turns = self.operations >= int(TaskOperation.PICKUP)
        if not torch.equal(self.operation_turns.bool(), expected_turns):
            raise ValueError("unit-task official operation durations differ")
        expected_quantity = (self.operations == int(TaskOperation.PICKUP)) | (
            self.operations == int(TaskOperation.PLACE)
        )
        if not torch.equal(self.requires_quantity.bool(), expected_quantity):
            raise ValueError("unit-task quantity flags differ from the language")

    def to(self, device: torch.device | str) -> TaskCatalog:
        """Move the complete immutable catalog to one device."""
        return TaskCatalog(
            operations=self.operations.to(device),
            arguments=self.arguments.to(device),
            targets=self.targets.to(device),
            requires_quantity=self.requires_quantity.to(device),
            operation_turns=self.operation_turns.to(device),
        )


@dataclass(frozen=True)
class TaskDecisionInputs:
    """Actor-visible state and exact native candidate surface for one task."""

    context: Tensor
    root_features: Tensor
    prefix_fields: Tensor
    prefix_mask: Tensor
    candidate_features: Tensor
    candidate_mask: Tensor
    candidate_arrivals: Tensor
    mode_mask: Tensor
    available_at: Tensor
    day_end: Tensor
    prefix_length: int | None = None

    @property
    def batch_size(self) -> int:
        """Return the number of independent task prefixes."""
        return int(self.context.shape[0])

    def validate(
        self,
        *,
        context_width: int,
        root_features: int,
        prefix_capacity: int,
        task_fields: int,
        candidate_count: int,
        candidate_features: int,
        time_tokens: int,
    ) -> None:
        """Validate shapes, devices, masks, and day-local time bounds."""
        batch = self.batch_size
        expected = {
            "context": (batch, context_width),
            "root_features": (batch, root_features),
            "prefix_fields": (batch, prefix_capacity, task_fields),
            "prefix_mask": (batch, prefix_capacity),
            "candidate_features": (batch, candidate_count, candidate_features),
            "candidate_mask": (batch, candidate_count),
            "candidate_arrivals": (batch, candidate_count),
            "mode_mask": (batch, 2),
            "available_at": (batch,),
            "day_end": (batch,),
        }
        for name, shape in expected.items():
            if getattr(self, name).shape != shape:
                raise ValueError(f"unit-task {name} has the wrong shape")
        if self.prefix_length is not None and not (
            0 <= self.prefix_length <= prefix_capacity
        ):
            raise ValueError("unit-task active prefix length is outside the ABI")
        values = tuple(getattr(self, name) for name in expected)
        if not all(value.device == self.context.device for value in values):
            raise ValueError("unit-task decision tensors must share one device")
        if not self.context.is_floating_point() or not self.root_features.is_floating_point():
            raise ValueError("unit-task context and root features must be floating point")
        if not self.candidate_features.is_floating_point():
            raise ValueError("unit-task candidate features must be floating point")
        for value in (
            self.prefix_fields,
            self.candidate_arrivals,
            self.available_at,
            self.day_end,
        ):
            if not _is_discrete(value):
                raise ValueError("unit-task identities and times must use integer tensors")
        if self.prefix_mask.is_floating_point() or self.candidate_mask.is_floating_point():
            raise ValueError("unit-task masks must be discrete")
        if self.mode_mask.is_floating_point():
            raise ValueError("unit-task mode mask must be discrete")
        prefix_mask = self.prefix_mask.bool()
        if bool(torch.any(prefix_mask[:, 1:] & ~prefix_mask[:, :-1])):
            raise ValueError("unit-task prefix mask must be contiguous")
        if not bool(self.candidate_mask[:, 0].bool().all()):
            raise ValueError("unit-task END must always be legal")
        if not bool(self.mode_mask.bool().any(dim=1).all()):
            raise ValueError("unit-task suffix mode has an empty legal set")
        if bool(torch.any((self.available_at < 0) | (self.available_at >= time_tokens))):
            raise ValueError("unit-task available time is outside the time vocabulary")
        if bool(
            torch.any(
                (self.day_end < self.available_at)
                | (self.day_end >= time_tokens)
            )
        ):
            raise ValueError("unit-task day end is outside the time vocabulary")


@dataclass(frozen=True)
class FactorizedTaskDecisionInputs:
    """Compact state for typed task decoding without a dense candidate surface."""

    context: Tensor
    root_features: Tensor
    prefix_fields: Tensor
    prefix_mask: Tensor
    economic_state: Tensor
    current_unit: Tensor
    current_x: Tensor
    current_y: Tensor
    target_counts: Tensor
    resource_counts: Tensor
    mode_mask: Tensor
    available_at: Tensor
    day_end: Tensor
    prefix_length: int | None = None

    @property
    def batch_size(self) -> int:
        """Return the number of independent task prefixes."""
        return int(self.context.shape[0])

    def validate(
        self,
        *,
        context_width: int,
        root_features: int,
        prefix_capacity: int,
        task_fields: int,
        time_tokens: int,
        board_size: int,
        unit_limit: int,
        economic_state_width: int,
    ) -> None:
        """Validate the compact planner state and its exact dimensions."""
        batch = self.batch_size
        tiles = board_size * board_size
        expected = {
            "context": (batch, context_width),
            "root_features": (batch, root_features),
            "prefix_fields": (batch, prefix_capacity, task_fields),
            "prefix_mask": (batch, prefix_capacity),
            "economic_state": (batch, economic_state_width),
            "current_unit": (batch,),
            "current_x": (batch,),
            "current_y": (batch,),
            "target_counts": (batch, tiles),
            "resource_counts": (batch, FACTORIZED_RESOURCE_COUNT),
            "mode_mask": (batch, 2),
            "available_at": (batch,),
            "day_end": (batch,),
        }
        for name, shape in expected.items():
            if getattr(self, name).shape != shape:
                raise ValueError(f"factorized unit-task {name} has the wrong shape")
        if self.prefix_length is not None and not (
            0 <= self.prefix_length <= prefix_capacity
        ):
            raise ValueError("factorized unit-task prefix length is outside the ABI")
        values = tuple(getattr(self, name) for name in expected)
        if not all(value.device == self.context.device for value in values):
            raise ValueError("factorized unit-task tensors must share one device")
        if not self.context.is_floating_point() or not self.root_features.is_floating_point():
            raise ValueError("factorized task context and root must be floating point")
        for name in (
            "prefix_fields",
            "economic_state",
            "current_unit",
            "current_x",
            "current_y",
            "target_counts",
            "resource_counts",
            "available_at",
            "day_end",
        ):
            if not _is_discrete(getattr(self, name)):
                raise ValueError("factorized task identities must use integer tensors")
        if self.prefix_mask.is_floating_point() or self.mode_mask.is_floating_point():
            raise ValueError("factorized task masks must be discrete")
        prefix_mask = self.prefix_mask.bool()
        if bool(torch.any(prefix_mask[:, 1:] & ~prefix_mask[:, :-1])):
            raise ValueError("factorized task prefix mask must be contiguous")
        if not bool(self.mode_mask.bool().any(dim=1).all()):
            raise ValueError("factorized task mode has an empty legal set")
        if bool(
            torch.any(
                (self.current_unit < 0)
                | (self.current_unit >= unit_limit)
                | (self.current_x < 0)
                | (self.current_x >= board_size)
                | (self.current_y < 0)
                | (self.current_y >= board_size)
            )
        ):
            raise ValueError("factorized task planning cursor is outside the ABI")
        if bool(torch.any((self.available_at < 0) | (self.available_at >= time_tokens))):
            raise ValueError("factorized task available time is outside the vocabulary")
        if bool(
            torch.any(
                (self.day_end < self.available_at)
                | (self.day_end >= time_tokens)
            )
        ):
            raise ValueError("factorized task day end is outside the vocabulary")


@dataclass(frozen=True)
class TaskActions:
    """One suffix-boundary choice and one conditional task token."""

    mode: Tensor
    candidate: Tensor
    quantity: Tensor
    earliest: Tensor
    deadline: Tensor

    def validate(self, batch_size: int) -> None:
        """Validate action vector shape and integer identity."""
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if value.shape != (batch_size,) or not _is_discrete(value):
                raise ValueError(f"unit-task action {name} must be an integer vector")


@dataclass(frozen=True)
class TaskConditionalMasks:
    """Stored exact masks for every conditional task-level factor."""

    mode: Tensor
    candidate: Tensor
    quantity: Tensor
    earliest: Tensor
    deadline: Tensor
    factors: Tensor

    def validate(
        self,
        batch_size: int,
        candidate_count: int,
        maximum_quantity: int,
        time_tokens: int,
    ) -> None:
        """Validate the persisted behavior-mask layout."""
        expected = {
            "mode": (batch_size, 2),
            "candidate": (batch_size, candidate_count),
            "quantity": (batch_size, maximum_quantity),
            "earliest": (batch_size, time_tokens),
            "deadline": (batch_size, time_tokens),
            "factors": (batch_size, TASK_FACTOR_COUNT),
        }
        for name, shape in expected.items():
            value = getattr(self, name)
            if value.shape != shape:
                raise ValueError(f"unit-task {name} mask has the wrong shape")
            if value.is_floating_point():
                raise ValueError("unit-task conditional masks must be discrete")
            if name != "factors" and not bool(value.bool().any(dim=1).all()):
                raise ValueError(f"unit-task {name} mask has an empty legal set")

    def to(
        self,
        device: torch.device | str,
        *,
        non_blocking: bool = False,
    ) -> TaskConditionalMasks:
        """Move all stored masks together."""
        return TaskConditionalMasks(
            **{
                name: getattr(self, name).to(device, non_blocking=non_blocking)
                for name in self.__dataclass_fields__
            }
        )


@dataclass(frozen=True)
class FactorizedTaskMasks:
    """Exact masks for the typed operation, argument, and target grammar."""

    mode: Tensor
    operation: Tensor
    argument: Tensor
    target: Tensor
    quantity: Tensor
    earliest: Tensor
    deadline: Tensor
    factors: Tensor

    def validate(
        self,
        batch_size: int,
        operation_tokens: int,
        argument_tokens: int,
        target_tokens: int,
        maximum_quantity: int,
        time_tokens: int,
    ) -> None:
        """Validate every conditional grammar mask."""
        expected = {
            "mode": (batch_size, 2),
            "operation": (batch_size, operation_tokens),
            "argument": (batch_size, argument_tokens),
            "target": (batch_size, target_tokens),
            "quantity": (batch_size, maximum_quantity),
            "earliest": (batch_size, time_tokens),
            "deadline": (batch_size, time_tokens),
            "factors": (batch_size, FACTORIZED_TASK_FACTOR_COUNT),
        }
        for name, shape in expected.items():
            value = getattr(self, name)
            if value.shape != shape:
                raise ValueError(f"factorized unit-task {name} mask has the wrong shape")
            if value.is_floating_point():
                raise ValueError("factorized unit-task masks must be discrete")
            if name != "factors" and not bool(value.bool().any(dim=1).all()):
                raise ValueError(f"factorized unit-task {name} mask is empty")

    def to(
        self,
        device: torch.device | str,
        *,
        non_blocking: bool = False,
    ) -> FactorizedTaskMasks:
        """Move all stored masks together."""
        return FactorizedTaskMasks(
            **{
                name: getattr(self, name).to(device, non_blocking=non_blocking)
                for name in self.__dataclass_fields__
            }
        )


def factorized_operation_mask(inputs: FactorizedTaskDecisionInputs) -> Tensor:
    """Return operation lookahead using only language geometry and time."""
    batch = inputs.batch_size
    device = inputs.context.device
    remaining = inputs.day_end - inputs.available_at
    mask = torch.zeros((batch, 16), dtype=torch.bool, device=device)
    mask[:, int(TaskOperation.END)] = True
    mask[:, int(TaskOperation.WAIT)] = remaining >= 1
    mask[:, int(TaskOperation.POSITION)] = remaining >= 1
    board_size = int(round(inputs.target_counts.shape[1] ** 0.5))
    half = board_size // 2
    warehouse_distance = torch.minimum(
        (inputs.current_x - (half - 1)).abs(),
        (inputs.current_x - half).abs(),
    ) + torch.minimum(
        (inputs.current_y - (half - 1)).abs(),
        (inputs.current_y - half).abs(),
    )
    warehouse_reachable = warehouse_distance + 1 <= remaining
    mask[:, int(TaskOperation.PICKUP)] = warehouse_reachable
    mask[:, int(TaskOperation.DROP)] = warehouse_reachable
    any_official = remaining >= 1
    mask[:, int(TaskOperation.PLACE) :] = any_official[:, None]
    return mask


def factorized_argument_mask(
    inputs: FactorizedTaskDecisionInputs,
    operation: Tensor,
    *,
    arguments: Tensor | None = None,
) -> Tensor:
    """Return the language arguments with target-feasibility lookahead."""
    device = inputs.context.device
    if arguments is None:
        arguments = torch.arange(NONE_ARGUMENT + 1, device=device)[None]
    no_argument = ~(
        (operation == int(TaskOperation.PICKUP))
        | (operation == int(TaskOperation.PLACE))
        | (operation == int(TaskOperation.PLANT))
    )
    pickup = operation == int(TaskOperation.PICKUP)
    plant = operation == int(TaskOperation.PLANT)
    place = operation == int(TaskOperation.PLACE)
    remaining = inputs.day_end - inputs.available_at
    board_size = int(round(inputs.target_counts.shape[1] ** 0.5))
    half = board_size // 2
    warehouse_distance = torch.minimum(
        (inputs.current_x - (half - 1)).abs(),
        (inputs.current_x - half).abs(),
    ) + torch.minimum(
        (inputs.current_y - (half - 1)).abs(),
        (inputs.current_y - half).abs(),
    )
    warehouse_reachable = warehouse_distance + 1 <= remaining
    return (
        (no_argument[:, None] & (arguments == NONE_ARGUMENT))
        | (pickup[:, None] & (arguments < 12))
        | (plant[:, None] & (arguments < 5))
        | (
            place[:, None]
            & (
                ((arguments < 9) & warehouse_reachable[:, None])
                | ((arguments >= 9) & (arguments < 12))
            )
        )
    )


def factorized_target_mask(
    inputs: FactorizedTaskDecisionInputs,
    operation: Tensor,
    argument: Tensor,
    *,
    target_x: Tensor | None = None,
    target_y: Tensor | None = None,
) -> Tensor:
    """Return exact target spellings after operation and argument selection."""
    tiles = inputs.target_counts.shape[1]
    board_size = int(round(tiles**0.5))
    if (target_x is None) != (target_y is None):
        raise ValueError("factorized target coordinates must be provided together")
    if target_x is None or target_y is None:
        indices = torch.arange(tiles, device=inputs.context.device)
        target_x = indices % board_size
        target_y = indices // board_size
    distance = (
        (inputs.current_x[:, None] - target_x).abs()
        + (inputs.current_y[:, None] - target_y).abs()
    )
    official = operation >= int(TaskOperation.PICKUP)
    completion = inputs.available_at[:, None] + distance + official[:, None]
    mask = completion <= inputs.day_end[:, None]
    position = operation == int(TaskOperation.POSITION)
    mask &= ~position[:, None] | (distance > 0)
    half = board_size // 2
    warehouse = (
        ((target_x == half - 1) | (target_x == half))
        & ((target_y == half - 1) | (target_y == half))
    )
    constrained = (operation == int(TaskOperation.PICKUP)) | (
        operation == int(TaskOperation.DROP)
    )
    # PLACE with ordinary inventory is constrained to a warehouse entrance.
    # Animal PLACE keeps the full board target language.
    constrained |= (operation == int(TaskOperation.PLACE)) & (argument < 9)
    mask &= ~constrained[:, None] | warehouse[None]
    targetless = (operation == int(TaskOperation.END)) | (
        operation == int(TaskOperation.WAIT)
    )
    mask &= ~targetless[:, None]
    return torch.cat((mask, targetless[:, None]), dim=1)


def factorized_arrival(
    inputs: FactorizedTaskDecisionInputs,
    operation: Tensor,
    target: Tensor,
) -> Tensor:
    """Return compiler arrival time for one typed selection."""
    tiles = inputs.target_counts.shape[1]
    board_size = int(round(tiles**0.5))
    safe_target = target.clamp(0, tiles - 1)
    target_x = safe_target % board_size
    target_y = safe_target // board_size
    distance = (inputs.current_x - target_x).abs() + (
        inputs.current_y - target_y
    ).abs()
    targetless = (operation == int(TaskOperation.END)) | (
        operation == int(TaskOperation.WAIT)
    )
    return torch.where(targetless, inputs.available_at, inputs.available_at + distance)


def factorized_conditional_masks(
    inputs: FactorizedTaskDecisionInputs,
    catalog: TaskCatalog,
    actions: TaskActions,
    *,
    maximum_quantity: int,
    time_tokens: int,
) -> FactorizedTaskMasks:
    """Derive all typed masks from compact state and a selected catalog spelling."""
    batch = inputs.batch_size
    device = inputs.context.device
    selected = actions.candidate.clamp(0, catalog.candidate_count - 1)
    operation = catalog.operations[selected]
    raw_argument = catalog.arguments[selected]
    argument = torch.where(
        raw_argument >= 0,
        raw_argument,
        torch.full_like(raw_argument, NONE_ARGUMENT),
    )
    targets = catalog.targets[selected]
    board_size = int(round(inputs.target_counts.shape[1] ** 0.5))
    target = torch.where(
        targets[:, 0] >= 0,
        targets[:, 1] * board_size + targets[:, 0],
        torch.full_like(targets[:, 0], inputs.target_counts.shape[1]),
    )
    rewrite = actions.mode == int(SuffixMode.REWRITE)
    operation_mask = factorized_operation_mask(inputs)
    operation_tokens = torch.arange(16, device=device)[None]
    operation_mask = torch.where(
        rewrite[:, None],
        operation_mask,
        operation_tokens == int(TaskOperation.END),
    )
    argument_mask = factorized_argument_mask(inputs, operation)
    argument_tokens = torch.arange(NONE_ARGUMENT + 1, device=device)[None]
    argument_mask = torch.where(
        rewrite[:, None], argument_mask, argument_tokens == NONE_ARGUMENT
    )
    target_mask = factorized_target_mask(inputs, operation, argument)
    target_tokens = torch.arange(
        inputs.target_counts.shape[1] + 1, device=device
    )[None]
    target_mask = torch.where(
        rewrite[:, None],
        target_mask,
        target_tokens == inputs.target_counts.shape[1],
    )

    is_end = operation == int(TaskOperation.END)
    active_task = rewrite & ~is_end
    needs_quantity = catalog.requires_quantity[selected].bool() & rewrite
    quantity_tokens = torch.arange(maximum_quantity, device=device)[None]
    quantity = needs_quantity[:, None] | (quantity_tokens == 0)

    times = torch.arange(time_tokens, device=device)[None]
    available = inputs.available_at[:, None]
    day_end = inputs.day_end[:, None]
    arrival = factorized_arrival(inputs, operation, target)[:, None]
    turns = catalog.operation_turns[selected][:, None]
    wait = operation[:, None] == int(TaskOperation.WAIT)
    earliest = active_task[:, None] & (times >= available) & (times <= day_end)
    earliest &= ~wait | (times > available)
    earliest &= torch.maximum(arrival, times) + turns <= day_end
    earliest |= ~active_task[:, None] & (times == 0)
    chosen_earliest = actions.earliest.clamp(0, time_tokens - 1)[:, None]
    completion = torch.maximum(arrival, chosen_earliest) + turns
    deadline = active_task[:, None] & (times >= completion) & (times <= day_end)
    deadline |= ~active_task[:, None] & (times == 0)

    factors = torch.zeros(
        (batch, FACTORIZED_TASK_FACTOR_COUNT), dtype=torch.bool, device=device
    )
    factors[:, 0] = inputs.mode_mask.bool().sum(dim=1) > 1
    factors[:, 1] = rewrite & (operation_mask.sum(dim=1) > 1)
    factors[:, 2] = rewrite & (argument_mask.sum(dim=1) > 1)
    factors[:, 3] = rewrite & (target_mask.sum(dim=1) > 1)
    factors[:, 4] = needs_quantity & (maximum_quantity > 1)
    factors[:, 5] = active_task & (earliest.sum(dim=1) > 1)
    factors[:, 6] = active_task & (deadline.sum(dim=1) > 1)
    return FactorizedTaskMasks(
        mode=inputs.mode_mask.bool(),
        operation=operation_mask,
        argument=argument_mask,
        target=target_mask,
        quantity=quantity,
        earliest=earliest,
        deadline=deadline,
        factors=factors,
    )


def selected_arrivals(
    inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs,
    catalog: TaskCatalog,
    actions: TaskActions,
) -> Tensor:
    """Return compiler arrivals from either the legacy or compact contract."""
    selected = actions.candidate.clamp(0, catalog.candidate_count - 1)
    if isinstance(inputs, TaskDecisionInputs):
        return inputs.candidate_arrivals.gather(1, selected[:, None]).squeeze(1)
    operation = catalog.operations[selected]
    targets = catalog.targets[selected]
    board_size = int(round(inputs.target_counts.shape[1] ** 0.5))
    target = torch.where(
        targets[:, 0] >= 0,
        targets[:, 1] * board_size + targets[:, 0],
        torch.full_like(targets[:, 0], inputs.target_counts.shape[1]),
    )
    return factorized_arrival(inputs, operation, target)


def conditional_masks(
    inputs: TaskDecisionInputs,
    catalog: TaskCatalog,
    actions: TaskActions,
    *,
    maximum_quantity: int,
    time_tokens: int,
) -> TaskConditionalMasks:
    """Derive exact post-selection masks from the native prefix facts."""
    batch = inputs.batch_size
    rows = torch.arange(batch, device=inputs.context.device)
    mode = inputs.mode_mask.bool()
    rewrite = actions.mode == int(SuffixMode.REWRITE)
    selected = actions.candidate.clamp(0, catalog.candidate_count - 1)
    operation = catalog.operations[selected]
    is_end = operation == int(TaskOperation.END)
    needs_quantity = catalog.requires_quantity[selected].bool()

    quantity = torch.zeros(
        (batch, maximum_quantity), dtype=torch.bool, device=inputs.context.device
    )
    quantity[:, 0] = True
    quantity[rewrite & ~is_end & needs_quantity] = True

    times = torch.arange(time_tokens, device=inputs.context.device)[None]
    available = inputs.available_at[:, None]
    day_end = inputs.day_end[:, None]
    arrival = inputs.candidate_arrivals[rows, selected][:, None]
    turns = catalog.operation_turns[selected][:, None]
    is_wait = operation[:, None] == int(TaskOperation.WAIT)
    active_task = rewrite[:, None] & ~is_end[:, None]
    earliest = active_task & (times >= available) & (times <= day_end)
    earliest &= ~is_wait | (times > available)
    completion_by_time = torch.maximum(arrival, times) + turns
    earliest &= completion_by_time <= day_end
    inactive = ~active_task[:, 0]
    earliest[inactive] = False
    earliest[inactive, 0] = True

    selected_earliest = actions.earliest.clamp(0, time_tokens - 1)[:, None]
    completion = torch.maximum(arrival, selected_earliest) + turns
    deadline = active_task & (times >= completion) & (times <= day_end)
    deadline[inactive] = False
    deadline[inactive, 0] = True

    factors = torch.zeros(
        (batch, TASK_FACTOR_COUNT), dtype=torch.bool, device=inputs.context.device
    )
    factors[:, 0] = mode.sum(dim=1) > 1
    factors[:, 1] = rewrite & (inputs.candidate_mask.bool().sum(dim=1) > 1)
    factors[:, 2] = rewrite & ~is_end & needs_quantity & (maximum_quantity > 1)
    factors[:, 3] = active_task[:, 0] & (earliest.sum(dim=1) > 1)
    factors[:, 4] = active_task[:, 0] & (deadline.sum(dim=1) > 1)
    return TaskConditionalMasks(
        mode=mode,
        candidate=inputs.candidate_mask.bool(),
        quantity=quantity,
        earliest=earliest,
        deadline=deadline,
        factors=factors,
    )


__all__ = [
    "FACTORIZED_TASK_FACTOR_COUNT",
    "FACTORIZED_RESOURCE_COUNT",
    "NONE_ARGUMENT",
    "TASK_FACTOR_COUNT",
    "FactorizedTaskDecisionInputs",
    "FactorizedTaskMasks",
    "TaskActions",
    "TaskCatalog",
    "TaskConditionalMasks",
    "TaskDecisionInputs",
    "conditional_masks",
    "factorized_arrival",
    "factorized_argument_mask",
    "factorized_conditional_masks",
    "factorized_operation_mask",
    "factorized_target_mask",
    "selected_arrivals",
]
