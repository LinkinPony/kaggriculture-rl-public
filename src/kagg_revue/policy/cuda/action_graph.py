"""CUDA Graph replay for fixed-shape autoregressive action decoding."""

from __future__ import annotations

import time

import torch
from torch import Tensor

from kagg_revue.policy.model import ActionState, TurnContext, TurnPolicyNet


class CudaActionGraphs:
    """Capture every decoder position once and replay it with mutable inputs."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        context: TurnContext,
        has_quantity: Tensor,
        generator: torch.Generator,
        action_head_noise: Tensor | None = None,
    ) -> None:
        """Warm and capture one fixed batch/memory shape on the current stream."""
        if context.memory.device.type != "cuda":
            raise ValueError("CUDA action graphs require CUDA context tensors")
        self._actor = actor
        self._device = context.memory.device
        self._generator = generator
        batch = context.memory.shape[0]
        architecture = actor.architecture
        self._context = TurnContext(
            memory=torch.empty_like(context.memory),
            memory_mask=torch.empty_like(context.memory_mask),
            strategy=(
                torch.empty_like(context.strategy)
                if context.strategy is not None
                else None
            ),
            strategy_mask=(
                torch.empty_like(context.strategy_mask)
                if context.strategy_mask is not None
                else None
            ),
        )
        self._phase = torch.zeros(batch, dtype=torch.long, device=self._device)
        self._legal = torch.ones(
            (batch, architecture.action_tokens),
            dtype=torch.bool,
            device=self._device,
        )
        self._has_quantity = has_quantity
        self._action_head_noise = (
            torch.empty_like(action_head_noise) if action_head_noise is not None else None
        )
        if self._action_head_noise is not None and action_head_noise is not None:
            self._action_head_noise.copy_(action_head_noise)
        self._graphs: list[torch.cuda.CUDAGraph] = []
        self._tokens: list[Tensor] = []
        self._quantities: list[Tensor] = []
        self._state: ActionState | None = None
        self._context.memory.copy_(context.memory)
        self._context.memory_mask.copy_(context.memory_mask)
        if self._context.strategy is not None and context.strategy is not None:
            self._context.strategy.copy_(context.strategy)
        if self._context.strategy_mask is not None and context.strategy_mask is not None:
            self._context.strategy_mask.copy_(context.strategy_mask)
        started = time.perf_counter()
        self._warm()
        self._capture()
        torch.cuda.current_stream(self._device).synchronize()
        self.capture_seconds = time.perf_counter() - started

    def _warm(self) -> None:
        """Initialize CUDA libraries outside graph capture."""
        decoder = self._actor.action
        state = decoder.initial_state(self._context)
        token = torch.zeros(self._phase.shape, dtype=torch.long, device=self._device)
        quantity = torch.zeros_like(token)
        for position in range(self._actor.architecture.max_decisions):
            _, _, state = decoder.next_cached(
                None if position == 0 else token,
                None if position == 0 else quantity,
                self._phase,
                self._context,
                state,
                action_head_noise=self._action_head_noise,
            )
        torch.cuda.current_stream(self._device).synchronize()

    def _capture(self) -> None:
        """Capture linked graphs whose cache and token outputs share storage."""
        decoder = self._actor.action
        pool = torch.cuda.graph_pool_handle()
        state: ActionState | None = None
        for position in range(self._actor.architecture.max_decisions):
            graph = torch.cuda.CUDAGraph()
            graph.register_generator_state(self._generator)
            with torch.cuda.graph(graph, pool=pool):
                if position == 0:
                    state = decoder.initial_state(self._context)
                if state is None:
                    raise RuntimeError("CUDA action graph lacks decoder state")
                logits, hidden, state = decoder.next_cached(
                    None if position == 0 else self._tokens[-1],
                    None if position == 0 else self._quantities[-1],
                    self._phase,
                    self._context,
                    state,
                    action_head_noise=self._action_head_noise,
                )
                probabilities = torch.softmax(
                    logits.float().masked_fill(~self._legal, -torch.inf), dim=-1
                )
                token = torch.multinomial(
                    probabilities,
                    1,
                    generator=self._generator,
                ).squeeze(-1)
                quantity_logits = decoder.quantity_logits(hidden, token, None)
                sampled = self._actor.choose_quantity(
                    quantity_logits,
                    sample=True,
                    generator=self._generator,
                )
                quantity = torch.where(
                    self._has_quantity[token], sampled, torch.zeros_like(sampled)
                )
            self._graphs.append(graph)
            self._tokens.append(token)
            self._quantities.append(quantity)
        self._state = state

    def start_turn(self, context: TurnContext, action_head_noise: Tensor | None = None) -> None:
        """Install the new turn memory before replaying decoder position zero."""
        if (
            context.memory.shape != self._context.memory.shape
            or context.memory_mask.shape != self._context.memory_mask.shape
            or (context.strategy is None) != (self._context.strategy is None)
            or (context.strategy_mask is None) != (self._context.strategy_mask is None)
        ):
            raise ValueError("CUDA action graph context shape changed")
        self._context.memory.copy_(context.memory)
        self._context.memory_mask.copy_(context.memory_mask)
        if self._context.strategy is not None and context.strategy is not None:
            if context.strategy.shape != self._context.strategy.shape:
                raise ValueError("CUDA action graph strategy shape changed")
            self._context.strategy.copy_(context.strategy)
        if self._context.strategy_mask is not None and context.strategy_mask is not None:
            if context.strategy_mask.shape != self._context.strategy_mask.shape:
                raise ValueError("CUDA action graph strategy mask shape changed")
            self._context.strategy_mask.copy_(context.strategy_mask)
        if (self._action_head_noise is None) != (action_head_noise is None):
            raise ValueError("CUDA action graph noise presence changed")
        if self._action_head_noise is not None and action_head_noise is not None:
            if action_head_noise.shape != self._action_head_noise.shape:
                raise ValueError("CUDA action graph noise shape changed")
            self._action_head_noise.copy_(action_head_noise)

    def step(self, position: int, phase: Tensor, legal: Tensor) -> tuple[Tensor, Tensor]:
        """Replay one position after updating its native legality inputs."""
        if position < 0 or position >= len(self._graphs):
            raise IndexError("CUDA action graph position is out of range")
        self._phase.copy_(phase)
        self._legal.copy_(legal)
        self._graphs[position].replay()
        return self._tokens[position], self._quantities[position]

    def close(self) -> None:
        """Release graph-private allocations at the rollout ownership boundary."""
        for graph in self._graphs:
            graph.reset()
        self._graphs.clear()
        self._tokens.clear()
        self._quantities.clear()
        self._state = None
        del self._context
        del self._phase
        del self._legal
        del self._has_quantity
        del self._action_head_noise
        del self._actor
        del self._generator


__all__ = ["CudaActionGraphs"]
