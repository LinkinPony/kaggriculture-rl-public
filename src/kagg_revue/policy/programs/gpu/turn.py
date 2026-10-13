"""CUDA Graph for conditional-program visible-turn encoding."""

from __future__ import annotations

import time
from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.policy.cuda.capture import (
    capture_safe_graph_replay,
    serialized_graph_capture,
)
from kagg_revue.policy.cuda.history import CudaStaticHistory
from kagg_revue.policy.model import TurnContext, TurnPolicyNet


@dataclass(frozen=True)
class ProgramTurnInputs:
    """Fixed-shape visible tensors copied into graph-owned storage."""

    board: Tensor
    units: Tensor
    global_features: Tensor
    previous_actions: Tensor
    previous_quantities: Tensor
    previous_mask: Tensor
    economic_state: Tensor | None

    def required(self) -> tuple[Tensor, ...]:
        """Return non-optional inputs in stable copy order."""
        return (
            self.board,
            self.units,
            self.global_features,
            self.previous_actions,
            self.previous_quantities,
            self.previous_mask,
        )


class ProgramTurnGraph:
    """Incrementally encode the actor scene and history at fixed addresses."""

    def __init__(self, actor: TurnPolicyNet, inputs: ProgramTurnInputs) -> None:
        """Warm and capture one fixed-batch deterministic actor turn."""
        required = inputs.required()
        device = inputs.board.device
        batch = inputs.board.shape[0]
        if device.type != "cuda" or any(value.device != device for value in required):
            raise ValueError("program turn graph inputs must share one CUDA device")
        if any(value.shape[0] != batch for value in required):
            raise ValueError("program turn graph inputs have different batches")
        if actor.architecture.turn_fact_features or actor.architecture.skill_tokens:
            raise ValueError("program turn graph requires deterministic actor context")
        if (inputs.economic_state is None) != (actor.economics is None):
            raise ValueError("program turn graph economic state differs from actor")
        if inputs.economic_state is not None and (
            inputs.economic_state.device != device
            or inputs.economic_state.shape[0] != batch
        ):
            raise ValueError("program turn graph economic input has a different batch")
        self._actor = actor
        self._device = device
        self._maximum_replays = actor.architecture.max_history
        self._replays = 0
        self._inputs = ProgramTurnInputs(
            board=torch.empty_like(inputs.board),
            units=torch.empty_like(inputs.units),
            global_features=torch.empty_like(inputs.global_features),
            previous_actions=torch.empty_like(inputs.previous_actions),
            previous_quantities=torch.empty_like(inputs.previous_quantities),
            previous_mask=torch.empty_like(inputs.previous_mask),
            economic_state=(
                None
                if inputs.economic_state is None
                else torch.empty_like(inputs.economic_state)
            ),
        )
        history_dtype = (
            torch.get_autocast_dtype("cuda")
            if torch.is_autocast_enabled("cuda")
            else next(actor.parameters()).dtype
        )
        self._history = CudaStaticHistory(
            actor, batch, history_dtype, include_strategy=False
        )
        self._install(inputs)
        started = time.perf_counter()
        self._context = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._history.reset()
        self._install(inputs)
        torch.cuda.current_stream(device).synchronize()
        self._graph = torch.cuda.CUDAGraph()
        with serialized_graph_capture(self._graph):
            self._context = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._history.reset()
        torch.cuda.current_stream(device).synchronize()
        self.capture_seconds = time.perf_counter() - started

    def _install(self, inputs: ProgramTurnInputs) -> None:
        for target, source in zip(
            self._inputs.required(), inputs.required(), strict=True
        ):
            if target.shape != source.shape or target.dtype != source.dtype:
                raise ValueError("program turn graph input shape or dtype changed")
            target.copy_(source)
        stored_economic = self._inputs.economic_state
        incoming_economic = inputs.economic_state
        if (stored_economic is None) != (incoming_economic is None):
            raise ValueError("program turn graph economic input mode changed")
        if stored_economic is not None and incoming_economic is not None:
            if (
                stored_economic.shape != incoming_economic.shape
                or stored_economic.dtype != incoming_economic.dtype
            ):
                raise ValueError("program turn graph economic input shape changed")
            stored_economic.copy_(incoming_economic)

    def _run(self) -> TurnContext:
        economic_features: Tensor | None = None
        if self._actor.economics is not None:
            economic_state = self._inputs.economic_state
            if economic_state is None:
                raise RuntimeError("program turn graph lost economic state")
            economic_features = self._actor.economics.turn_features(
                economic_state, self._inputs.global_features
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
        return context

    def decode(self, inputs: ProgramTurnInputs) -> TurnContext:
        """Copy one turn and replay without a host-side layer dispatch loop."""
        if self._replays >= self._maximum_replays:
            raise RuntimeError("program turn graph exceeded actor history capacity")
        self._install(inputs)
        capture_safe_graph_replay(self._graph)
        self._replays += 1
        return self._context

    def reset(self) -> None:
        """Reset episode history while retaining captured allocations."""
        with torch.inference_mode():
            self._history.reset()
        self._replays = 0

    def close(self) -> None:
        """Release graph-private allocations at the collector boundary."""
        self._graph.reset()
        del self._graph
        del self._context
        del self._history
        del self._inputs
        del self._actor


__all__ = ["ProgramTurnGraph", "ProgramTurnInputs"]
