"""CUDA Graph for one complete stateful autoregressive policy turn."""

from __future__ import annotations

import time

import torch
from torch import Tensor

from kagg_revue.policy.cuda.capture import serialized_graph_capture
from kagg_revue.policy.cuda.categorical import sample_action, sample_quantity
from kagg_revue.policy.cuda.forced_market import H200ForcedMarketProgram
from kagg_revue.policy.cuda.session import (
    GpuPolicyStateLayout,
    compile_policy_legal,
    select_policy_actions,
)
from kagg_revue.policy.economics.transition import project_market_selection
from kagg_revue.policy.model import ActionState, TurnContext, TurnPolicyNet
from kagg_revue.policy.vocabulary import CURRENT_ACTIONS


class _PolicyTurnProgram:
    """Fixed-shape action program reusable inside a larger CUDA Graph."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        batch: int,
        device: torch.device,
        layout: GpuPolicyStateLayout,
        has_quantity: Tensor,
        generator: torch.Generator,
        *,
        track_log_probability: bool = False,
    ) -> None:
        """Allocate outputs and randomness for one fixed batch."""
        architecture = actor.architecture
        if architecture.action_tokens != CURRENT_ACTIONS.action_tokens:
            raise ValueError("whole-turn GPU policy requires the current native action ABI")
        if has_quantity.shape != (architecture.action_tokens,):
            raise ValueError("whole-turn GPU quantity mask differs from the actor ABI")
        if architecture.max_decisions < layout.unit_limit + 1:
            raise ValueError("whole-turn graph cannot hold the unit prefix")
        self._actor = actor
        self._device = device
        self._layout = layout
        self._has_quantity = has_quantity
        self._generator = generator
        decisions = architecture.max_decisions
        actions = architecture.action_tokens
        self._legal = torch.empty(
            (decisions, batch, actions), dtype=torch.bool, device=self._device
        )
        self._phases = torch.empty((decisions, batch), dtype=torch.long, device=self._device)
        self._decisions = torch.empty((decisions, batch), dtype=torch.bool, device=self._device)
        self._tokens = torch.empty((decisions, batch), dtype=torch.long, device=self._device)
        self._quantities = torch.empty_like(self._tokens)
        self._log_probabilities = (
            torch.empty((decisions, batch), dtype=torch.float32, device=self._device)
            if track_log_probability
            else None
        )
        self._uniform = torch.empty(
            (decisions, 2, batch),
            dtype=torch.float32,
            device=self._device,
        )

    def _decode_position(
        self,
        context: TurnContext,
        state: Tensor,
        action_state: ActionState,
        previous_token: Tensor | None,
        previous_quantity: Tensor | None,
        legal: Tensor,
        phases: Tensor,
        decisions: Tensor,
        position: int,
        action_uniform: Tensor,
        quantity_uniform: Tensor,
        action_head_noise: Tensor | None,
    ) -> tuple[Tensor, Tensor, ActionState]:
        """Capture or execute one active autoregressive position."""
        decoder = self._actor.action
        safe_phase = torch.where(decisions, phases, torch.zeros_like(phases))
        economic_prefix = (
            None
            if self._actor.economics is None
            else self._actor.economics.prefix_features(state, safe_phase)
        )
        economic_candidates = (
            None
            if self._actor.economics is None
            else self._actor.economics.candidate_features(state, safe_phase)
        )
        logits, hidden, next_state = decoder.next_cached(
            previous_token,
            previous_quantity,
            safe_phase,
            context,
            action_state,
            economic_prefix_facts=economic_prefix,
            economic_candidate_facts=economic_candidates,
            action_head_noise=action_head_noise,
        )
        log_probability = (
            None if self._log_probabilities is None else self._log_probabilities[position]
        )
        token = self._tokens[position]
        sample_action(
            logits,
            legal,
            decisions,
            action_uniform,
            token,
            log_probability,
        )
        economic_quantities = (
            None
            if self._actor.economics is None
            else self._actor.economics.quantity_features(state, token)
        )
        quantity_logits = decoder.quantity_logits(
            hidden,
            token,
            None,
            economic_quantities,
        )
        quantity = self._quantities[position]
        sample_quantity(
            quantity_logits,
            token,
            self._has_quantity,
            quantity_uniform,
            quantity,
            log_probability,
        )
        select_policy_actions(
            state,
            token,
            quantity,
            self._layout,
            decisions,
        )
        if self._actor.economics is not None:
            project_market_selection(
                state,
                token,
                quantity,
                phases,
                decisions,
                self._actor.economics.layout,
            )
        return token, quantity, next_state

    def run(
        self,
        context: TurnContext,
        state: Tensor,
        *,
        conditional: bool,
        action_head_noise: Tensor | None = None,
    ) -> ActionState:
        """Run the complete fixed-shape action program."""
        decoder = self._actor.action
        action_state = decoder.initial_state(context)
        previous_token: Tensor | None = None
        previous_quantity: Tensor | None = None
        torch.rand(
            self._uniform.shape,
            dtype=torch.float32,
            device=self._device,
            generator=self._generator,
            out=self._uniform,
        )
        for position in range(self._actor.architecture.max_decisions):
            legal = self._legal[position]
            phases = self._phases[position]
            decisions = self._decisions[position]
            compile_policy_legal(state, legal, phases, decisions, self._layout)
            predicate = decisions.any()
            action_uniform = self._uniform[position, 0]
            quantity_uniform = self._uniform[position, 1]
            self._tokens[position].zero_()
            self._quantities[position].zero_()
            if self._log_probabilities is not None:
                self._log_probabilities[position].zero_()
            if conditional:
                graph = torch.cuda.CUDAGraph.get_currently_capturing_graph()
                graph.begin_capture_to_if_node(predicate)  # type: ignore[no-untyped-call]
                try:
                    token, quantity, action_state = self._decode_position(
                        context,
                        state,
                        action_state,
                        previous_token,
                        previous_quantity,
                        legal,
                        phases,
                        decisions,
                        position,
                        action_uniform,
                        quantity_uniform,
                        action_head_noise,
                    )
                finally:
                    graph.end_capture_to_conditional_node()  # type: ignore[no-untyped-call]
            else:
                token, quantity, action_state = self._decode_position(
                    context,
                    state,
                    action_state,
                    previous_token,
                    previous_quantity,
                    legal,
                    phases,
                    decisions,
                    position,
                    action_uniform,
                    quantity_uniform,
                    action_head_noise,
                )
            previous_token = token
            previous_quantity = quantity
        return action_state

    @property
    def tokens(self) -> Tensor:
        """Return graph-owned selected tokens as ``[decision, batch]``."""
        return self._tokens

    @property
    def quantities(self) -> Tensor:
        """Return graph-owned selected quantities as ``[decision, batch]``."""
        return self._quantities

    @property
    def phases(self) -> Tensor:
        """Return graph-owned pre-selection phases as ``[decision, batch]``."""
        return self._phases

    @property
    def decisions(self) -> Tensor:
        """Return the exact active prefix mask as ``[decision, batch]``."""
        return self._decisions

    @property
    def legal(self) -> Tensor:
        """Return exact legal masks as ``[decision, batch, action]``."""
        return self._legal

    @property
    def log_probabilities(self) -> Tensor | None:
        """Return selected behavior log probabilities when requested."""
        return self._log_probabilities

    @property
    def generator(self) -> torch.Generator:
        """Return the graph-registered rollout generator."""
        return self._generator


class CudaPolicyTurnGraph:
    """Capture decoder, legality, sampling, and state transition as one graph."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        context: TurnContext,
        policy_state: Tensor,
        layout: GpuPolicyStateLayout,
        has_quantity: Tensor,
        generator: torch.Generator,
        *,
        forced_tokens: Tensor | None = None,
        forced_quantities: Tensor | None = None,
        track_log_probability: bool = False,
    ) -> None:
        """Warm and capture the fixed-shape whole-turn program."""
        if context.memory.device.type != "cuda" or policy_state.device.type != "cuda":
            raise ValueError("whole-turn CUDA Graph inputs must reside on CUDA")
        if context.memory.shape[0] != policy_state.shape[0]:
            raise ValueError("whole-turn context and policy state batch differ")
        self._device = context.memory.device
        self._context = TurnContext(
            memory=torch.empty_like(context.memory),
            memory_mask=torch.empty_like(context.memory_mask),
            strategy=(torch.empty_like(context.strategy) if context.strategy is not None else None),
            strategy_mask=(
                torch.empty_like(context.strategy_mask)
                if context.strategy_mask is not None
                else None
            ),
        )
        self._state = torch.empty_like(policy_state)
        if (forced_tokens is None) != (forced_quantities is None):
            raise ValueError("forced whole-turn actions must coexist")
        self._forced_tokens = None if forced_tokens is None else torch.empty_like(forced_tokens)
        self._forced_quantities = (
            None if forced_quantities is None else torch.empty_like(forced_quantities)
        )
        if self._forced_tokens is not None and forced_tokens is not None:
            self._forced_tokens.copy_(forced_tokens)
        if self._forced_quantities is not None and forced_quantities is not None:
            self._forced_quantities.copy_(forced_quantities)
        if self._forced_tokens is not None and self._forced_quantities is not None:
            self._program: _PolicyTurnProgram | H200ForcedMarketProgram = (
                H200ForcedMarketProgram(
                    actor,
                    policy_state.shape[0],
                    self._device,
                    layout,
                    has_quantity,
                    generator,
                    self._forced_tokens,
                    self._forced_quantities,
                    track_log_probability=track_log_probability,
                )
            )
        else:
            self._program = _PolicyTurnProgram(
                actor,
                policy_state.shape[0],
                self._device,
                layout,
                has_quantity,
                generator,
                track_log_probability=track_log_probability,
            )
        self._context.memory.copy_(context.memory)
        self._context.memory_mask.copy_(context.memory_mask)
        if self._context.strategy is not None and context.strategy is not None:
            self._context.strategy.copy_(context.strategy)
        if self._context.strategy_mask is not None and context.strategy_mask is not None:
            self._context.strategy_mask.copy_(context.strategy_mask)
        self._state.copy_(policy_state)
        started = time.perf_counter()
        self._decoder_state: ActionState | None = self._program.run(
            self._context,
            self._state,
            conditional=False,
        )
        torch.cuda.current_stream(self._device).synchronize()
        self._state.copy_(policy_state)
        self._graph = torch.cuda.CUDAGraph()
        self._graph.register_generator_state(generator)
        with serialized_graph_capture(self._graph):
            self._decoder_state = self._program.run(
                self._context,
                self._state,
                conditional=True,
            )
        torch.cuda.current_stream(self._device).synchronize()
        self.capture_seconds = time.perf_counter() - started

    def start_turn(
        self,
        context: TurnContext,
        policy_state: Tensor,
        forced_tokens: Tensor | None = None,
        forced_quantities: Tensor | None = None,
    ) -> None:
        """Install one new fixed-shape batch before replay."""
        if (
            context.memory.shape != self._context.memory.shape
            or context.memory_mask.shape != self._context.memory_mask.shape
            or (context.strategy is None) != (self._context.strategy is None)
            or (context.strategy_mask is None) != (self._context.strategy_mask is None)
            or policy_state.shape != self._state.shape
        ):
            raise ValueError("whole-turn CUDA Graph input shape changed")
        self._context.memory.copy_(context.memory)
        self._context.memory_mask.copy_(context.memory_mask)
        if self._context.strategy is not None and context.strategy is not None:
            if context.strategy.shape != self._context.strategy.shape:
                raise ValueError("whole-turn CUDA Graph strategy shape changed")
            self._context.strategy.copy_(context.strategy)
        if self._context.strategy_mask is not None and context.strategy_mask is not None:
            if context.strategy_mask.shape != self._context.strategy_mask.shape:
                raise ValueError("whole-turn CUDA Graph strategy mask shape changed")
            self._context.strategy_mask.copy_(context.strategy_mask)
        self._state.copy_(policy_state)
        if (forced_tokens is None) != (self._forced_tokens is None):
            raise ValueError("forced whole-turn token mode changed")
        if (forced_quantities is None) != (self._forced_quantities is None):
            raise ValueError("forced whole-turn quantity mode changed")
        if self._forced_tokens is not None and forced_tokens is not None:
            if forced_tokens.shape != self._forced_tokens.shape:
                raise ValueError("forced whole-turn token shape changed")
            self._forced_tokens.copy_(forced_tokens)
        if self._forced_quantities is not None and forced_quantities is not None:
            if forced_quantities.shape != self._forced_quantities.shape:
                raise ValueError("forced whole-turn quantity shape changed")
            self._forced_quantities.copy_(forced_quantities)

    def replay(self) -> None:
        """Execute the entire action turn without a host synchronization."""
        self._graph.replay()

    @property
    def tokens(self) -> Tensor:
        """Return graph-owned selected tokens as ``[decision, batch]``."""
        return self._program.tokens

    @property
    def quantities(self) -> Tensor:
        """Return graph-owned selected quantities as ``[decision, batch]``."""
        return self._program.quantities

    @property
    def phases(self) -> Tensor:
        """Return graph-owned pre-selection phases as ``[decision, batch]``."""
        return self._program.phases

    @property
    def decisions(self) -> Tensor:
        """Return the exact active prefix mask as ``[decision, batch]``."""
        return self._program.decisions

    @property
    def legal(self) -> Tensor:
        """Return exact legal masks as ``[decision, batch, action]``."""
        return self._program.legal

    @property
    def final_phases(self) -> Tensor:
        """Return each session phase after the graph's last transition."""
        return self._state[:, 4]

    @property
    def log_probabilities(self) -> Tensor | None:
        """Return joint behavior log probabilities when requested."""
        return self._program.log_probabilities

    def close(self) -> None:
        """Release graph-private allocations after the rollout boundary."""
        self._graph.reset()
        del self._graph
        del self._decoder_state
        del self._program
        del self._context
        del self._state
        del self._forced_tokens
        del self._forced_quantities


__all__ = ["CudaPolicyTurnGraph"]
