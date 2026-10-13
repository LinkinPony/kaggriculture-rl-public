"""Fixed-batch CUDA Graph for one task-policy decision."""

from __future__ import annotations

import time

import torch

from kagg_revue.policy.cuda.capture import serialized_graph_capture
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    TaskDecisionInputs,
)
from kagg_revue.policy.tasks.model import UnitTaskPolicy
from kagg_revue.policy.tasks.schema import TaskPolicyOutput


class TaskDecisionGraph:
    """Capture launch-heavy task inference while exact features remain mutable."""

    def __init__(
        self,
        policy: UnitTaskPolicy,
        generator: torch.Generator,
    ) -> None:
        """Bind a task policy and lazily specialize to its rollout batch."""
        if next(policy.parameters()).device.type != "cuda":
            raise ValueError("task decision graph requires a CUDA policy")
        self._policy = policy
        self._generator = generator
        self._inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs | None = None
        self._output: TaskPolicyOutput | None = None
        self._graph: torch.cuda.CUDAGraph | None = None
        self.capture_seconds = 0.0

    @staticmethod
    def _allocate(
        inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs,
    ) -> TaskDecisionInputs | FactorizedTaskDecisionInputs:
        """Allocate fixed-address mirrors for every policy input."""
        if isinstance(inputs, FactorizedTaskDecisionInputs):
            return FactorizedTaskDecisionInputs(
                context=torch.empty_like(inputs.context),
                root_features=torch.empty_like(inputs.root_features),
                prefix_fields=torch.empty_like(inputs.prefix_fields),
                prefix_mask=torch.empty_like(inputs.prefix_mask),
                economic_state=torch.empty_like(inputs.economic_state),
                current_unit=torch.empty_like(inputs.current_unit),
                current_x=torch.empty_like(inputs.current_x),
                current_y=torch.empty_like(inputs.current_y),
                target_counts=torch.empty_like(inputs.target_counts),
                resource_counts=torch.empty_like(inputs.resource_counts),
                mode_mask=torch.empty_like(inputs.mode_mask),
                available_at=torch.empty_like(inputs.available_at),
                day_end=torch.empty_like(inputs.day_end),
                prefix_length=inputs.prefix_fields.shape[1],
            )
        return TaskDecisionInputs(
            context=torch.empty_like(inputs.context),
            root_features=torch.empty_like(inputs.root_features),
            prefix_fields=torch.empty_like(inputs.prefix_fields),
            prefix_mask=torch.empty_like(inputs.prefix_mask),
            candidate_features=torch.empty_like(inputs.candidate_features),
            candidate_mask=torch.empty_like(inputs.candidate_mask),
            candidate_arrivals=torch.empty_like(inputs.candidate_arrivals),
            mode_mask=torch.empty_like(inputs.mode_mask),
            available_at=torch.empty_like(inputs.available_at),
            day_end=torch.empty_like(inputs.day_end),
            prefix_length=inputs.prefix_fields.shape[1],
        )

    def _install(
        self, inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs
    ) -> None:
        """Copy exact features into graph-owned storage."""
        targets = self._inputs
        if targets is None:
            raise RuntimeError("task decision graph has not been allocated")
        if type(targets) is not type(inputs):
            raise ValueError("task decision graph input contract changed")
        for name in inputs.__dataclass_fields__:
            if name == "prefix_length":
                continue
            target = getattr(targets, name)
            source = getattr(inputs, name)
            if target.shape != source.shape or target.dtype != source.dtype:
                raise ValueError("task decision graph input shape or dtype changed")
            target.copy_(source)

    def _capture(
        self, inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs
    ) -> None:
        """Warm and capture the first fixed-shape decision batch."""
        self._inputs = self._allocate(inputs)
        self._install(inputs)
        device = inputs.context.device
        started = time.perf_counter()
        self._output = self._policy.rollout(
            self._inputs,
            sample=True,
            generator=self._generator,
            validate_inputs=False,
            compute_entropy=False,
        )
        torch.cuda.current_stream(device).synchronize()
        self._install(inputs)
        graph = torch.cuda.CUDAGraph()
        graph.register_generator_state(self._generator)
        with serialized_graph_capture(graph):
            self._output = self._policy.rollout(
                self._inputs,
                sample=True,
                generator=self._generator,
                validate_inputs=False,
                compute_entropy=False,
            )
        torch.cuda.current_stream(device).synchronize()
        self._graph = graph
        self.capture_seconds = time.perf_counter() - started

    def decode(
        self, inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs
    ) -> TaskPolicyOutput:
        """Replay one exact decision with a fixed full rollout batch."""
        if self._graph is None:
            self._capture(inputs)
        self._install(inputs)
        graph = self._graph
        output = self._output
        if graph is None or output is None:
            raise RuntimeError("task decision graph capture did not produce outputs")
        graph.replay()
        return output

    def close(self) -> None:
        """Release graph-private allocations at the collector boundary."""
        if self._graph is not None:
            self._graph.reset()
        self._graph = None
        self._inputs = None
        self._output = None


__all__ = ["TaskDecisionGraph"]
