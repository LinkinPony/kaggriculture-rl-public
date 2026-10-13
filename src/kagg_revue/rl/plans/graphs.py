"""Exact-shape CUDA Graph replay for launch-bound plan event inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

import torch
from torch import Tensor

from kagg_revue.policy.plans.grammar import PlanActions, PlanInputs
from kagg_revue.policy.plans.model import (
    StructuredPlanBehaviorOutput,
    StructuredPlanPolicy,
)

PlanEventOutput: TypeAlias = StructuredPlanBehaviorOutput | PlanActions
_TensorSignature: TypeAlias = tuple[
    int,
    int,
    tuple[int, ...],
    tuple[int, ...],
    torch.dtype,
]
_InputSignature: TypeAlias = tuple[_TensorSignature, ...]


@dataclass(frozen=True)
class _CapturedEvent:
    """One static-address exact-batch event graph and its live outputs."""

    graph: torch.cuda.CUDAGraph
    inputs: PlanInputs
    history: Tensor
    strategy: Tensor | None
    output: PlanEventOutput


def _input_signature(inputs: PlanInputs) -> _InputSignature:
    """Identify the fixed exchange storage read by a captured event graph."""
    return tuple(
        (
            value.data_ptr(),
            int(value.storage_offset()),
            tuple(value.shape),
            tuple(value.stride()),
            value.dtype,
        )
        for value in (
            inputs.board,
            inputs.units,
            inputs.global_features,
            inputs.economic_state,
            inputs.features,
            inputs.journal,
            inputs.events,
            inputs.active_lines,
            inputs.active_line_mask,
            inputs.global_plan,
        )
    )


class PlanEventGraphCache:
    """Capture only recurring exact event shapes without padding RNG draws."""

    def __init__(
        self,
        policy: StructuredPlanPolicy,
        generator: torch.Generator,
        *,
        device: torch.device,
        record_statistics: bool,
        maximum_batch_size: int,
    ) -> None:
        """Bind a model, generator, and bounded set of exact batch shapes."""
        if device.type != "cuda" or device.index is None:
            raise ValueError("structured-plan event graphs require indexed CUDA")
        if maximum_batch_size < 1:
            raise ValueError("structured-plan event graph capacity must be positive")
        if generator.device != device:
            raise ValueError("structured-plan event graph generator is on another device")
        self._policy = policy
        self._generator = generator
        self._device = device
        self._record_statistics = record_statistics
        self._maximum_batch_size = maximum_batch_size
        self._captures: dict[_InputSignature, _CapturedEvent] = {}
        self._capture_count = 0
        self._replay_count = 0
        self._eager_count = 0

    def matches(
        self,
        policy: StructuredPlanPolicy,
        generator: torch.Generator,
    ) -> bool:
        """Return whether this cache remains bound to the live model and RNG."""
        return self._policy is policy and self._generator is generator

    def counters(self) -> tuple[int, int, int]:
        """Return cumulative capture, replay, and eager production calls."""
        return self._capture_count, self._replay_count, self._eager_count

    def _run(
        self,
        inputs: PlanInputs,
        history: Tensor,
        strategy: Tensor | None,
    ) -> PlanEventOutput:
        """Execute one event through the ordinary eager policy entry point."""
        with (
            torch.cuda.device(self._device),
            torch.inference_mode(),
            torch.autocast(device_type="cuda", dtype=torch.bfloat16),
        ):
            if self._record_statistics:
                return self._policy.rollout_behavior_event(
                    inputs,
                    history,
                    strategy,
                    generator=self._generator,
                    validate_inputs=False,
                )
            return self._policy.sample_actions_event(
                inputs,
                history,
                strategy,
                generator=self._generator,
                validate_inputs=False,
            )

    def _capture(
        self,
        inputs: PlanInputs,
        history: Tensor,
        strategy: Tensor | None,
        signature: _InputSignature,
    ) -> _CapturedEvent:
        """Warm and capture one exact shape without consuming rollout RNG."""
        saved_generator_state = self._generator.get_state()
        static_history = history.clone()
        static_strategy = strategy.clone() if strategy is not None else None
        for _ in range(3):
            self._run(inputs, static_history, static_strategy)
        torch.cuda.synchronize(self._device)
        self._generator.set_state(saved_generator_state)

        graph = torch.cuda.CUDAGraph()
        graph.register_generator_state(self._generator)
        with torch.cuda.graph(graph):
            output = self._run(inputs, static_history, static_strategy)
        torch.cuda.synchronize(self._device)
        self._generator.set_state(saved_generator_state)
        captured = _CapturedEvent(
            graph=graph,
            inputs=inputs,
            history=static_history,
            strategy=static_strategy,
            output=output,
        )
        self._captures[signature] = captured
        self._capture_count += 1
        return captured

    def infer(
        self,
        inputs: PlanInputs,
        history: Tensor,
        strategy: Tensor | None,
    ) -> PlanEventOutput:
        """Replay a captured exact shape or use eager for larger events."""
        if inputs.batch_size > self._maximum_batch_size:
            self._eager_count += 1
            return self._run(inputs, history, strategy)
        signature = _input_signature(inputs)
        captured = self._captures.get(signature)
        if captured is None:
            captured = self._capture(inputs, history, strategy, signature)
        captured.history.copy_(history)
        if captured.strategy is not None:
            if strategy is None:
                raise ValueError("structured-plan event graph strategy is absent")
            captured.strategy.copy_(strategy)
        elif strategy is not None:
            raise ValueError("structured-plan event graph gained unexpected strategy")
        captured.graph.replay()
        self._replay_count += 1
        return captured.output


__all__ = ["PlanEventGraphCache", "PlanEventOutput"]
