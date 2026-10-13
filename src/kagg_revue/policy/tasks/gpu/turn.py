"""CUDA Graph for the task actor's visible-turn encoding hot path."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.cuda.capture import serialized_graph_capture
from kagg_revue.policy.cuda.history import CudaStaticHistory
from kagg_revue.policy.model import TurnContext, TurnPolicyNet


@dataclass(frozen=True)
class TaskTurnInputs:
    """One fixed-shape visible turn copied into graph-owned storage."""

    board: Tensor
    units: Tensor
    global_features: Tensor
    previous_actions: Tensor
    previous_quantities: Tensor
    previous_mask: Tensor
    economic_state: Tensor | None

    def required(self) -> tuple[Tensor, ...]:
        """Return the non-optional tensors in stable field order."""
        return (
            self.board,
            self.units,
            self.global_features,
            self.previous_actions,
            self.previous_quantities,
            self.previous_mask,
        )


class TaskTurnGraph:
    """Incrementally encode scenes and temporal history inside one CUDA Graph."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        inputs: TaskTurnInputs,
        behavior_value: Callable[
            [Tensor, Tensor, Tensor, Tensor, Tensor | None, Tensor | None], Tensor
        ],
    ) -> None:
        """Warm and capture a fixed-batch task turn."""
        required = inputs.required()
        device = inputs.board.device
        batch = inputs.board.shape[0]
        if device.type != "cuda" or any(tensor.device != device for tensor in required):
            raise ValueError("task turn graph inputs must share one CUDA device")
        if any(tensor.shape[0] != batch for tensor in required):
            raise ValueError("task turn graph inputs have different batches")
        if actor.architecture.turn_fact_features:
            raise ValueError("task turn graph does not support derived turn facts")
        if actor.architecture.skill_tokens:
            raise ValueError("task turn graph does not support sampled skills")
        if (inputs.economic_state is None) != (actor.economics is None):
            raise ValueError("task turn graph economic state differs from the actor")
        if inputs.economic_state is not None and (
            inputs.economic_state.device != device or inputs.economic_state.shape[0] != batch
        ):
            raise ValueError("task turn graph economic state has a different batch")

        self._actor = actor
        self._behavior_value = behavior_value
        self._device = device
        self._maximum_replays = actor.architecture.max_history
        self._replays = 0
        self._inputs = TaskTurnInputs(
            board=torch.empty_like(inputs.board),
            units=torch.empty_like(inputs.units),
            global_features=torch.empty_like(inputs.global_features),
            previous_actions=torch.empty_like(inputs.previous_actions),
            previous_quantities=torch.empty_like(inputs.previous_quantities),
            previous_mask=torch.empty_like(inputs.previous_mask),
            economic_state=(
                None if inputs.economic_state is None else torch.empty_like(inputs.economic_state)
            ),
        )
        history_dtype = (
            torch.get_autocast_dtype("cuda")
            if torch.is_autocast_enabled("cuda")
            else next(actor.parameters()).dtype
        )
        self._history = CudaStaticHistory(actor, batch, history_dtype)
        self._install(inputs)
        started = time.perf_counter()
        self._context, self._value = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._history.reset()
        self._install(inputs)
        torch.cuda.current_stream(device).synchronize()
        self._graph = torch.cuda.CUDAGraph()
        with serialized_graph_capture(self._graph):
            self._context, self._value = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._history.reset()
        torch.cuda.current_stream(device).synchronize()
        self.capture_seconds = time.perf_counter() - started

    def _install(self, inputs: TaskTurnInputs) -> None:
        """Copy one turn into graph-owned fixed-address tensors."""
        for target, source in zip(self._inputs.required(), inputs.required(), strict=True):
            if target.shape != source.shape or target.dtype != source.dtype:
                raise ValueError("task turn graph input shape or dtype changed")
            target.copy_(source)
        if (self._inputs.economic_state is None) != (inputs.economic_state is None):
            raise ValueError("task turn graph economic input mode changed")
        if self._inputs.economic_state is not None and inputs.economic_state is not None:
            if (
                self._inputs.economic_state.shape != inputs.economic_state.shape
                or self._inputs.economic_state.dtype != inputs.economic_state.dtype
            ):
                raise ValueError("task turn graph economic input shape or dtype changed")
            self._inputs.economic_state.copy_(inputs.economic_state)

    def _run(self) -> tuple[TurnContext, Tensor]:
        """Execute the graphable scene, history, and behavior-value program."""
        economic_features: Tensor | None = None
        if self._actor.economics is not None:
            economic_state = self._inputs.economic_state
            if economic_state is None:
                raise RuntimeError("task turn graph lost its economic state")
            economic_features = self._actor.economics.turn_features(
                economic_state,
                self._inputs.global_features,
            )
        scene = self._actor.scene(
            self._inputs.board,
            self._inputs.units,
            self._inputs.global_features,
            self._inputs.previous_actions,
            self._inputs.previous_quantities,
            self._inputs.previous_mask,
            economic_features=economic_features,
        )
        context, _skill = self._history.start_turn(scene)
        value = self._behavior_value(
            context.memory[:, 0],
            self._inputs.global_features,
            scene.memory,
            scene.memory_mask,
            economic_features,
            context.strategy,
        )
        return context, value

    def decode(self, inputs: TaskTurnInputs) -> tuple[TurnContext, Tensor]:
        """Install and replay one visible turn without a host synchronization."""
        if self._replays >= self._maximum_replays:
            raise RuntimeError("task turn graph exceeded history capacity")
        self._install(inputs)
        self._graph.replay()
        self._replays += 1
        return self._context, self._value

    def reset(self) -> None:
        """Reset episode history while retaining the captured CUDA program."""
        with torch.inference_mode():
            self._history.reset()
        self._replays = 0

    def close(self) -> None:
        """Release graph-private allocations at the collector boundary."""
        self._graph.reset()
        del self._graph
        del self._context
        del self._value
        del self._history
        del self._inputs
        del self._actor
        del self._behavior_value


__all__ = ["TaskTurnGraph", "TaskTurnInputs"]
