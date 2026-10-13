"""H200 batched prefill for compiler-known unit actions."""

from __future__ import annotations

import torch
from torch import Tensor

from kagg_revue.policy.cuda.categorical import sample_action, sample_quantity
from kagg_revue.policy.cuda.session import (
    GpuPolicyStateLayout,
    compile_policy_legal,
    select_policy_actions,
)
from kagg_revue.policy.economics.transition import project_market_selection
from kagg_revue.policy.model import ActionState, TurnContext, TurnPolicyNet
from kagg_revue.policy.vocabulary import CURRENT_ACTIONS


class H200ForcedMarketProgram:
    """Batch a known unit prefix and autoregress only over market factors."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        batch: int,
        device: torch.device,
        layout: GpuPolicyStateLayout,
        has_quantity: Tensor,
        generator: torch.Generator,
        forced_tokens: Tensor,
        forced_quantities: Tensor,
        *,
        track_log_probability: bool,
    ) -> None:
        """Allocate fixed graph inputs, outputs, and suffix workspaces."""
        architecture = actor.architecture
        decisions = architecture.max_decisions
        actions = architecture.action_tokens
        if architecture.action_tokens != CURRENT_ACTIONS.action_tokens:
            raise ValueError("H200 market graph requires the current action ABI")
        if has_quantity.shape != (actions,):
            raise ValueError("H200 market quantity mask differs from the actor ABI")
        if (
            forced_tokens.shape != (decisions, batch)
            or forced_quantities.shape != forced_tokens.shape
            or forced_tokens.device != device
            or forced_quantities.device != device
        ):
            raise ValueError("forced unit actions differ from the market graph")
        if (
            actor.economics is None
            or architecture.model_width != 256
            or architecture.action_layers != 2
            or layout.unit_limit != 32
            or decisions != 42
        ):
            raise ValueError("market prefill requires the H200 production actor")

        self._actor = actor
        self._device = device
        self._layout = layout
        self._has_quantity = has_quantity
        self._generator = generator
        self._forced_tokens = forced_tokens
        self._forced_quantities = forced_quantities
        self._tokens = torch.empty(
            (decisions, batch), dtype=torch.long, device=device
        )
        self._quantities = torch.empty_like(self._tokens)
        self._phases = torch.empty_like(self._tokens)
        self._decisions = torch.empty(
            (decisions, batch), dtype=torch.bool, device=device
        )
        self._legal = torch.empty(
            (decisions, batch, actions), dtype=torch.bool, device=device
        )
        self._log_probabilities = (
            torch.empty(
                (decisions, batch), dtype=torch.float32, device=device
            )
            if track_log_probability
            else None
        )
        self._uniform = torch.empty(
            (decisions, 2, batch), dtype=torch.float32, device=device
        )

        unit_limit = layout.unit_limit
        market_steps = decisions - unit_limit
        self._action_indices = torch.arange(actions, device=device)
        self._unit_positions = torch.arange(unit_limit, device=device)
        self._market_offsets = torch.arange(market_steps, device=device)
        self._unit_counts = torch.empty(
            batch, dtype=torch.long, device=device
        )
        self._prefix_valid = torch.empty(
            (unit_limit, batch), dtype=torch.bool, device=device
        )
        self._prefix_phases = torch.zeros(
            (unit_limit, batch), dtype=torch.long, device=device
        )
        self._prefix_economic = torch.empty(
            (unit_limit, batch, architecture.economic_prefix_features),
            dtype=torch.float32,
            device=device,
        )
        self._market_positions = torch.empty(
            (market_steps, batch), dtype=torch.long, device=device
        )
        self._market_legal = torch.empty(
            (market_steps, batch, actions), dtype=torch.bool, device=device
        )
        self._market_phases = torch.empty(
            (market_steps, batch), dtype=torch.long, device=device
        )
        self._market_decisions = torch.empty(
            (market_steps, batch), dtype=torch.bool, device=device
        )
        self._market_tokens = torch.empty(
            (market_steps, batch), dtype=torch.long, device=device
        )
        self._market_quantities = torch.empty_like(self._market_tokens)
        self._market_log_probabilities = torch.empty(
            (market_steps, batch), dtype=torch.float32, device=device
        )
        self._begin_token = torch.full(
            (batch,),
            actor.action.begin_token,
            dtype=torch.long,
            device=device,
        )
        self._zero_quantity = torch.zeros(
            batch, dtype=torch.long, device=device
        )

    def _decode_market_position(
        self,
        context: TurnContext,
        state: Tensor,
        action_state: ActionState,
        previous_token: Tensor,
        previous_quantity: Tensor,
        legal: Tensor,
        phases: Tensor,
        decisions: Tensor,
        positions: Tensor,
        token: Tensor,
        quantity: Tensor,
        log_probability: Tensor | None,
        action_uniform: Tensor,
        quantity_uniform: Tensor,
    ) -> ActionState:
        """Decode one unknown market factor after the batched prefix."""
        economics = self._actor.economics
        if economics is None:
            raise RuntimeError("H200 market economics disappeared")
        safe_phase = torch.where(decisions, phases, torch.zeros_like(phases))
        economic_prefix = economics.prefix_features(state, safe_phase)
        economic_candidates = economics.candidate_features(state, safe_phase)
        logits, hidden, next_state = self._actor.action.next_cached_fixed(
            previous_token,
            previous_quantity,
            safe_phase,
            context,
            action_state,
            positions,
            None,
            None,
            economic_prefix,
            economic_candidates,
            None,
        )
        sample_action(
            logits,
            legal,
            decisions,
            action_uniform,
            token,
            log_probability,
        )
        quantity_logits = self._actor.action.quantity_logits(
            hidden,
            token,
            None,
            economics.quantity_features(state, token),
        )
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
        project_market_selection(
            state,
            token,
            quantity,
            phases,
            decisions,
            economics.layout,
        )
        return next_state

    def run(
        self,
        context: TurnContext,
        state: Tensor,
        *,
        conditional: bool,
        action_head_noise: Tensor | None = None,
    ) -> ActionState:
        """Prefill compiler-known unit actions and sample the market suffix."""
        if action_head_noise is not None:
            raise ValueError("H200 forced-prefix prefill does not use head noise")
        forced_tokens = self._forced_tokens
        forced_quantities = self._forced_quantities
        economics = self._actor.economics
        if economics is None:
            raise RuntimeError("H200 market economics disappeared")
        unit_limit = self._layout.unit_limit
        market_steps = self._actor.architecture.max_decisions - unit_limit
        self._tokens.zero_()
        self._quantities.zero_()
        self._legal.zero_()
        self._phases.fill_(2)
        self._decisions.zero_()
        if self._log_probabilities is not None:
            self._log_probabilities.zero_()
        torch.rand(
            self._uniform.shape,
            dtype=torch.float32,
            device=self._device,
            generator=self._generator,
            out=self._uniform,
        )
        self._unit_counts.copy_(state[:, 1])
        self._prefix_valid.copy_(
            self._unit_positions[:, None] < self._unit_counts[None]
        )
        self._market_positions.copy_(
            self._unit_counts[None] + self._market_offsets[:, None]
        )
        valid_prefix = self._prefix_valid
        self._tokens[:unit_limit].copy_(
            torch.where(
                valid_prefix,
                forced_tokens[:unit_limit],
                torch.zeros_like(forced_tokens[:unit_limit]),
            )
        )
        self._quantities[:unit_limit].copy_(
            torch.where(
                valid_prefix,
                forced_quantities[:unit_limit],
                torch.zeros_like(forced_quantities[:unit_limit]),
            )
        )
        self._phases[:unit_limit].masked_fill_(valid_prefix, 0)
        self._decisions[:unit_limit].copy_(valid_prefix)
        self._legal[:unit_limit].copy_(
            valid_prefix[:, :, None]
            & (
                forced_tokens[:unit_limit, :, None]
                == self._action_indices[None, None]
            )
        )
        for position in range(unit_limit):
            self._prefix_economic[position].copy_(
                economics.prefix_features(
                    state,
                    self._prefix_phases[position],
                )
            )
            select_policy_actions(
                state,
                forced_tokens[position],
                forced_quantities[position],
                self._layout,
                self._prefix_valid[position],
            )
        action_state = self._actor.action.prefill_fixed(
            forced_tokens[:unit_limit].transpose(0, 1),
            forced_quantities[:unit_limit].transpose(0, 1),
            self._prefix_phases.transpose(0, 1),
            self._prefix_valid.transpose(0, 1),
            context,
            self._prefix_economic.transpose(0, 1),
        )
        last_unit = (self._unit_counts - 1).clamp(0, unit_limit - 1)
        previous_token = forced_tokens[:unit_limit].gather(
            0, last_unit[None]
        ).squeeze(0)
        previous_quantity = forced_quantities[:unit_limit].gather(
            0, last_unit[None]
        ).squeeze(0)
        previous_token = torch.where(
            self._unit_counts > 0,
            previous_token,
            self._begin_token,
        )
        previous_quantity = torch.where(
            self._unit_counts > 0,
            previous_quantity,
            self._zero_quantity,
        )
        for suffix in range(market_steps):
            legal = self._market_legal[suffix]
            phases = self._market_phases[suffix]
            decisions = self._market_decisions[suffix]
            token = self._market_tokens[suffix]
            quantity = self._market_quantities[suffix]
            positions = self._market_positions[suffix]
            log_probability = (
                self._market_log_probabilities[suffix]
                if self._log_probabilities is not None
                else None
            )
            compile_policy_legal(
                state,
                legal,
                phases,
                decisions,
                self._layout,
            )
            token.zero_()
            quantity.zero_()
            if log_probability is not None:
                log_probability.zero_()
            predicate = decisions.any()
            arguments = (
                context,
                state,
                action_state,
                previous_token,
                previous_quantity,
                legal,
                phases,
                decisions,
                positions,
                token,
                quantity,
                log_probability,
                self._uniform[:, 0].gather(
                    0, positions[None]
                ).squeeze(0),
                self._uniform[:, 1].gather(
                    0, positions[None]
                ).squeeze(0),
            )
            if conditional:
                graph = torch.cuda.CUDAGraph.get_currently_capturing_graph()
                graph.begin_capture_to_if_node(  # type: ignore[no-untyped-call]
                    predicate
                )
                try:
                    action_state = self._decode_market_position(*arguments)
                finally:
                    graph.end_capture_to_conditional_node()  # type: ignore[no-untyped-call]
            else:
                action_state = self._decode_market_position(*arguments)
            position_index = positions[None]
            self._tokens.scatter_(0, position_index, token[None])
            self._quantities.scatter_(0, position_index, quantity[None])
            self._phases.scatter_(0, position_index, phases[None])
            self._decisions.scatter_(0, position_index, decisions[None])
            self._legal.scatter_(
                0,
                position_index[:, :, None].expand(
                    1, legal.shape[0], legal.shape[1]
                ),
                legal[None],
            )
            if self._log_probabilities is not None and log_probability is not None:
                self._log_probabilities.scatter_(
                    0,
                    position_index,
                    log_probability[None],
                )
            previous_token = token
            previous_quantity = quantity
        return action_state

    @property
    def tokens(self) -> Tensor:
        """Return selected tokens as ``[decision, batch]``."""
        return self._tokens

    @property
    def quantities(self) -> Tensor:
        """Return selected quantities as ``[decision, batch]``."""
        return self._quantities

    @property
    def phases(self) -> Tensor:
        """Return pre-selection phases as ``[decision, batch]``."""
        return self._phases

    @property
    def decisions(self) -> Tensor:
        """Return the active prefix mask as ``[decision, batch]``."""
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


__all__ = ["H200ForcedMarketProgram"]
