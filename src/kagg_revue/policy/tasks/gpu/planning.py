"""One CUDA graph for candidate construction, task policy, and transition."""

from __future__ import annotations

import time
from copy import copy
from dataclasses import dataclass, fields

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.cuda.capture import serialized_graph_capture
from kagg_revue.policy.tasks.gpu.recording import record_task_rollout_rows
from kagg_revue.policy.tasks.gpu.state import TaskPlanningState
from kagg_revue.policy.tasks.grammar import (
    FACTORIZED_TASK_FACTOR_COUNT,
    FactorizedTaskDecisionInputs,
    TaskCatalog,
    TaskDecisionInputs,
    selected_arrivals,
)
from kagg_revue.policy.tasks.model import UnitTaskPolicy
from kagg_revue.policy.tasks.schema import TaskPolicyOutput

_H200_TASK_BUCKET_ROWS = 64


def _clone_state(state: TaskPlanningState) -> TaskPlanningState:
    result = copy(state)
    for field in fields(state):
        value = getattr(state, field.name)
        if isinstance(value, Tensor):
            setattr(result, field.name, value.clone())
    return result


def _copy_state(target: TaskPlanningState, source: TaskPlanningState) -> None:
    if target.contract != source.contract or target.layout != source.layout:
        raise ValueError("task planning graph state contract changed")
    for field in fields(target):
        target_value = getattr(target, field.name)
        source_value = getattr(source, field.name)
        if isinstance(target_value, Tensor):
            if not isinstance(source_value, Tensor):
                raise TypeError("task planning graph tensor field changed type")
            if (
                target_value.shape != source_value.shape
                or target_value.dtype != source_value.dtype
            ):
                raise ValueError("task planning graph state shape changed")
            target_value.copy_(source_value)
    target.initial_prefix_length = source.initial_prefix_length


@dataclass
class _GraphVariant:
    """One compacted-row CUDA graph specialization."""

    graph: torch.cuda.CUDAGraph
    rows: Tensor
    host_rows: Tensor
    host_row_values: NDArray[np.int64]
    inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs
    output: TaskPolicyOutput
    uniforms: Tensor | None


class TaskPlanningGraph:
    """Capture the complete fixed-batch autoregressive task step."""

    def __init__(
        self,
        policy: UnitTaskPolicy,
        generator: torch.Generator,
        maximum_decisions: int,
    ) -> None:
        """Create an empty graph specialized on its first planning batch."""
        if next(policy.parameters()).device.type != "cuda":
            raise ValueError("task planning graph requires a CUDA policy")
        if maximum_decisions < 1:
            raise ValueError("task planning graph capacity must be positive")
        self._policy = policy
        self._generator = generator
        self._maximum_decisions = maximum_decisions
        self._catalog: TaskCatalog | None = None
        self._state: TaskPlanningState | None = None
        self._context: Tensor | None = None
        self._selections: Tensor | None = None
        self._counts: Tensor | None = None
        self._old_log_probability: Tensor | None = None
        self._old_values: Tensor | None = None
        self._host_active: Tensor | None = None
        self._host_active_values: NDArray[np.bool_] | None = None
        self._host_selections: Tensor | None = None
        self._host_counts: Tensor | None = None
        self._host_old_log_probability: Tensor | None = None
        self._host_old_values: Tensor | None = None
        self._variants: dict[int, _GraphVariant] = {}
        self.capture_seconds = 0.0

    def _allocate(self, source: TaskPlanningState, context: Tensor) -> None:
        self._state = _clone_state(source)
        self._context = torch.empty_like(context)
        self._context.copy_(context)
        batch = context.shape[0]
        device = context.device
        self._catalog = self._policy.catalog()
        self._selections = torch.zeros(
            (batch, self._maximum_decisions, 5),
            dtype=torch.int16,
            device=device,
        )
        self._counts = torch.zeros(batch, dtype=torch.int16, device=device)
        self._old_log_probability = torch.zeros(
            (batch, self._maximum_decisions),
            dtype=torch.float32,
            device=device,
        )
        self._old_values = torch.zeros_like(self._old_log_probability)
        self._host_active = torch.empty_like(
            source.active,
            device="cpu",
            pin_memory=True,
        )
        self._host_active_values = self._host_active.numpy()
        self._host_selections = torch.empty_like(
            self._selections,
            device="cpu",
            pin_memory=True,
        )
        self._host_counts = torch.empty_like(
            self._counts,
            device="cpu",
            pin_memory=True,
        )
        self._host_old_log_probability = torch.empty_like(
            self._old_log_probability,
            device="cpu",
            pin_memory=True,
        )
        self._host_old_values = torch.empty_like(
            self._old_values,
            device="cpu",
            pin_memory=True,
        )

    def _storage(self) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        values = (
            self._selections,
            self._counts,
            self._old_log_probability,
            self._old_values,
        )
        if any(value is None for value in values):
            raise RuntimeError("task planning graph storage is absent")
        return tuple(values)  # type: ignore[return-value]

    def _host_storage(self) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        values = (
            self._host_selections,
            self._host_counts,
            self._host_old_log_probability,
            self._host_old_values,
        )
        if any(value is None for value in values):
            raise RuntimeError("task planning graph host storage is absent")
        return tuple(values)  # type: ignore[return-value]

    def _install(self, source: TaskPlanningState, context: Tensor) -> None:
        state = self._state
        stored_context = self._context
        if state is None or stored_context is None:
            raise RuntimeError("task planning graph has not been allocated")
        if (
            stored_context.shape != context.shape
            or stored_context.dtype != context.dtype
        ):
            raise ValueError("task planning graph context shape changed")
        _copy_state(state, source)
        stored_context.copy_(context)
        for value in self._storage():
            value.zero_()

    def _step(
        self,
        rows: Tensor,
        uniforms: Tensor | None = None,
    ) -> tuple[
        TaskDecisionInputs | FactorizedTaskDecisionInputs, TaskPolicyOutput
    ]:
        state = self._state
        context = self._context
        catalog = self._catalog
        if state is None or context is None or catalog is None:
            raise RuntimeError("task planning graph is not initialized")
        selections, counts, old_log_probability, old_values = self._storage()
        inputs = state.inputs(
            rows,
            context,
            catalog,
            prefix_length=state.contract.prefix_capacity,
            factorized=self._policy.factorized is not None,
            history_window=self._policy.architecture.history_window,
        )
        if uniforms is None:
            output = self._policy.rollout(
                inputs,
                sample=True,
                generator=self._generator,
                validate_inputs=False,
                compute_entropy=False,
            )
        else:
            if not isinstance(inputs, FactorizedTaskDecisionInputs):
                raise RuntimeError("factorized task graph received pooled inputs")
            uniforms.uniform_(generator=self._generator)
            output = self._policy.rollout(
                inputs,
                sample=True,
                generator=None,
                uniforms=uniforms,
                validate_inputs=False,
                compute_entropy=False,
            )
        record_task_rollout_rows(
            rows,
            state.active,
            output.actions,
            output.joint_log_probability,
            output.value,
            selections,
            counts,
            old_log_probability,
            old_values,
        )
        arrivals = selected_arrivals(
            inputs, catalog, output.actions
        ).contiguous()
        state.apply(rows, output.actions, catalog, arrivals)
        return inputs, output

    def _restore(
        self,
        state: TaskPlanningState,
        storage: tuple[Tensor, Tensor, Tensor, Tensor],
    ) -> None:
        current = self._state
        if current is None:
            raise RuntimeError("task planning graph state is absent")
        _copy_state(current, state)
        for target, source in zip(self._storage(), storage, strict=True):
            target.copy_(source)

    def _capture_variant(
        self,
        bucket: int,
        row_values: NDArray[np.int64],
    ) -> _GraphVariant:
        state = self._state
        context = self._context
        if state is None or context is None:
            raise RuntimeError("task planning graph is not initialized")
        device = context.device
        saved_state = _clone_state(state)
        storage = self._storage()
        saved_storage = (
            storage[0].clone(),
            storage[1].clone(),
            storage[2].clone(),
            storage[3].clone(),
        )
        rows = torch.as_tensor(
            row_values, dtype=torch.long, device=device
        ).clone()
        use_explicit_uniforms = self._policy.factorized is not None
        warm_uniforms = (
            torch.empty(
                (FACTORIZED_TASK_FACTOR_COUNT, bucket),
                dtype=torch.float32,
                device=device,
            )
            if use_explicit_uniforms
            else None
        )
        started = time.perf_counter()
        warm_inputs, warm_output = self._step(rows, warm_uniforms)
        torch.cuda.current_stream(device).synchronize()
        self._restore(saved_state, saved_storage)
        del warm_inputs, warm_output, warm_uniforms
        graph = torch.cuda.CUDAGraph()
        graph.register_generator_state(self._generator)
        uniforms = (
            torch.empty(
                (FACTORIZED_TASK_FACTOR_COUNT, bucket),
                dtype=torch.float32,
                device=device,
            )
            if use_explicit_uniforms
            else None
        )
        with serialized_graph_capture(graph):
            inputs, output = self._step(rows, uniforms)
        torch.cuda.current_stream(device).synchronize()
        self._restore(saved_state, saved_storage)
        host_rows = torch.empty(
            bucket,
            dtype=torch.long,
            device="cpu",
            pin_memory=True,
        )
        variant = _GraphVariant(
            graph,
            rows,
            host_rows,
            host_rows.numpy(),
            inputs,
            output,
            uniforms,
        )
        self._variants[bucket] = variant
        self.capture_seconds += time.perf_counter() - started
        return variant

    def _variant(
        self, active_rows: NDArray[np.int64]
    ) -> tuple[_GraphVariant, NDArray[np.int64]]:
        state = self._state
        if state is None or active_rows.ndim != 1 or not active_rows.size:
            raise ValueError("task planning graph needs active row identities")
        batch = state.active.shape[0]
        if int(active_rows.min()) < 0 or int(active_rows.max()) >= batch:
            raise ValueError("task planning graph active row lies outside its batch")
        active_count = int(active_rows.size)
        bucket = (
            1 << (active_count - 1).bit_length()
            if active_count <= _H200_TASK_BUCKET_ROWS
            else (
                (active_count + _H200_TASK_BUCKET_ROWS - 1)
                // _H200_TASK_BUCKET_ROWS
                * _H200_TASK_BUCKET_ROWS
            )
        )
        bucket = min(batch, bucket)
        if bucket == active_rows.size:
            padded = active_rows
        else:
            active_mask = np.zeros(batch, dtype=np.bool_)
            active_mask[active_rows] = True
            inactive = np.flatnonzero(~active_mask).astype(
                np.int64, copy=False
            )
            padded = np.concatenate(
                (active_rows, inactive[: bucket - active_rows.size])
            )
        variant = self._variants.get(bucket)
        if variant is None:
            variant = self._capture_variant(bucket, padded)
        return variant, padded

    def begin(self, state: TaskPlanningState, context: Tensor) -> None:
        """Install one turn boundary and clear its device-side task tape."""
        if self._state is None:
            self._allocate(state, context)
        self._install(state, context)

    def replay(
        self,
        active_rows: NDArray[np.int64],
        steps: int = 1,
    ) -> int:
        """Advance compacted active rows with the smallest captured bucket."""
        if steps < 1:
            raise ValueError("task planning graph replay count must be positive")
        variant, padded = self._variant(active_rows)
        np.copyto(variant.host_row_values, padded)
        variant.rows.copy_(variant.host_rows, non_blocking=True)
        for _ in range(steps):
            variant.graph.replay()
        return int(padded.size) * steps

    def active_host(self) -> NDArray[np.bool_]:
        """Synchronize only the small row-activity vector."""
        state = self._state
        target = self._host_active
        values = self._host_active_values
        if state is None or target is None or values is None:
            raise RuntimeError("task planning graph state is absent")
        target.copy_(state.active, non_blocking=True)
        torch.cuda.current_stream(state.active.device).synchronize()
        return values

    def host_tape(
        self,
    ) -> tuple[
        NDArray[np.int16],
        NDArray[np.int16],
        NDArray[np.float32],
        NDArray[np.float32],
    ]:
        """Stage only the live task-tape prefix for this turn."""
        selections, counts, old_log_probability, old_values = self._storage()
        (
            selection_target,
            count_target,
            log_probability_target,
            value_target,
        ) = self._host_storage()
        count_target.copy_(counts, non_blocking=True)
        selection_target.copy_(selections, non_blocking=True)
        log_probability_target.copy_(old_log_probability, non_blocking=True)
        value_target.copy_(old_values, non_blocking=True)
        torch.cuda.current_stream(counts.device).synchronize()
        count_values = np.array(
            count_target.numpy(),
            dtype=np.int16,
            order="C",
            copy=True,
        )
        live_width = max(1, int(count_values.max(initial=0)))
        if live_width > self._maximum_decisions:
            raise RuntimeError("task planning graph tape count exceeds its capacity")
        return (
            np.array(
                selection_target[:, :live_width].numpy(),
                dtype=np.int16,
                order="C",
                copy=True,
            ),
            count_values,
            np.array(
                log_probability_target[:, :live_width].numpy(),
                dtype=np.float32,
                order="C",
                copy=True,
            ),
            np.array(
                value_target[:, :live_width].numpy(),
                dtype=np.float32,
                order="C",
                copy=True,
            ),
        )

    def close(self) -> None:
        """Release graph-private allocations at the collector boundary."""
        for variant in self._variants.values():
            variant.graph.reset()
        self._variants.clear()
        self._catalog = None
        self._state = None
        self._context = None
        self._selections = None
        self._counts = None
        self._old_log_probability = None
        self._old_values = None
        self._host_active = None
        self._host_active_values = None
        self._host_selections = None
        self._host_counts = None
        self._host_old_log_probability = None
        self._host_old_values = None


__all__ = ["TaskPlanningGraph"]
