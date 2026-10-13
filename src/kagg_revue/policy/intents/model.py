"""Pointer actor and W/D/L critic for canonical intent successors."""

from __future__ import annotations

from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.intents.data import IntentTensorState
from kagg_revue.policy.intents.encoding import (
    IntentCandidateEncoder,
    IntentStateEncoder,
    TypedEmbeddings,
)
from kagg_revue.policy.intents.schema import (
    IntentArchitecture,
    IntentPolicyOutput,
    IntentSelection,
)
from kagg_revue.policy.model import TurnPolicyNet
from kagg_revue.policy.transformer import HistoryState, RMSNorm


class IntentPolicy(nn.Module):
    """Vectorized pointer policy over native canonical candidates."""

    def __init__(self, architecture: IntentArchitecture) -> None:
        """Create state, candidate, policy, and outcome heads."""
        super().__init__()
        self.architecture = architecture
        typed = TypedEmbeddings(architecture)
        self.state_encoder = IntentStateEncoder(architecture, typed)
        self.candidate_encoder = IntentCandidateEncoder(architecture, typed)
        width = architecture.model_width
        self.tile_context = nn.Sequential(
            RMSNorm(architecture.context_width),
            nn.Linear(architecture.context_width, width, bias=False),
            RMSNorm(width),
        )
        self.query = nn.Linear(width, width, bias=False)
        self.key = nn.Linear(width, width, bias=False)
        self.residual = nn.Sequential(
            nn.Linear(2 * width, architecture.feedforward_width, bias=False),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, 1),
        )
        self.value_head = nn.Sequential(
            RMSNorm(width),
            nn.Linear(width, architecture.feedforward_width, bias=False),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, 3),
        )
        self.scale = width**-0.5

    def _residual_scores(self, hidden: Tensor, candidates: Tensor) -> Tensor:
        """Factor the shared state half out of the candidate residual MLP."""
        first = cast(nn.Linear, self.residual[0])
        last = cast(nn.Linear, self.residual[2])
        width = hidden.shape[-1]
        state_residual = F.linear(hidden, first.weight[:, :width], first.bias)[:, None]
        candidate_residual = F.linear(candidates, first.weight[:, width:])
        return cast(Tensor, last(F.silu(state_residual + candidate_residual)).squeeze(-1))

    def _pointer_scores(self, hidden: Tensor, candidates: Tensor) -> Tensor:
        """Move the linear key projection to the shared query side."""
        query = self.query(hidden)
        candidate_query = F.linear(query, self.key.weight.T)
        return cast(Tensor, (candidate_query[:, None] * candidates).sum(dim=-1) * self.scale)

    def _score(
        self,
        hidden: Tensor,
        encoded_tiles: Tensor,
        state: IntentTensorState,
    ) -> IntentPolicyOutput:
        candidates = self.candidate_encoder(
            state.candidate_fields, state.candidate_features, encoded_tiles
        )
        logits = self._pointer_scores(hidden, candidates)
        logits = logits + self._residual_scores(hidden, candidates)
        logits = logits.masked_fill(~state.candidate_mask, -torch.inf)
        return IntentPolicyOutput(
            candidate_logits=logits,
            outcome_logits=cast(Tensor, self.value_head(hidden)),
        )

    def _validate_inputs(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: IntentTensorState,
        *,
        validate: bool,
    ) -> None:
        if validate:
            state.validate()
        if context.shape != (state.batch_size, self.architecture.context_width):
            raise ValueError("intent turn context differs from the policy architecture")
        if tile_context.shape != (
            state.batch_size,
            self.architecture.tile_count,
            self.architecture.context_width,
        ):
            raise ValueError("intent tile context differs from the policy architecture")

    def forward(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: IntentTensorState,
        *,
        validate: bool = True,
    ) -> IntentPolicyOutput:
        """Score every candidate and one direct terminal W/D/L value."""
        self._validate_inputs(context, tile_context, state, validate=validate)
        encoded_tiles = cast(Tensor, self.tile_context(tile_context))
        hidden = self.state_encoder(context, encoded_tiles, state)
        return self._score(hidden, encoded_tiles, state)

    def forward_with_work_summary(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: IntentTensorState,
        work_summary: Tensor,
        *,
        validate: bool = True,
    ) -> IntentPolicyOutput:
        """Score candidates using a transaction-maintained work reduction."""
        self._validate_inputs(context, tile_context, state, validate=validate)
        encoded_tiles = cast(Tensor, self.tile_context(tile_context))
        hidden = self.state_encoder.forward_with_work_summary(
            context,
            encoded_tiles,
            state,
            work_summary,
        )
        return self._score(hidden, encoded_tiles, state)

    def prepare_turn(self, context: Tensor, tile_context: Tensor) -> tuple[Tensor, Tensor]:
        """Project immutable context once for all pseudo-steps in a turn."""
        encoded_context = cast(Tensor, self.state_encoder.context(context))
        encoded_tiles = cast(Tensor, self.tile_context(tile_context))
        return encoded_context, encoded_tiles

    def forward_prepared(
        self,
        encoded_context: Tensor,
        encoded_tiles: Tensor,
        state: IntentTensorState,
        work_summary: Tensor,
    ) -> IntentPolicyOutput:
        """Score one pseudo-step from cached turn-static projections."""
        hidden = self.state_encoder.forward_prepared(
            encoded_context,
            encoded_tiles,
            state,
            work_summary,
        )
        return self._score(hidden, encoded_tiles, state)

    def forward_cached(
        self,
        encoded_context: Tensor,
        encoded_tiles: Tensor,
        state: IntentTensorState,
        ledger_summary: Tensor,
        work_summary: Tensor,
        position_summary: Tensor,
        market_summary: Tensor,
    ) -> IntentPolicyOutput:
        """Score from transaction-maintained exact state reductions."""
        hidden = self.state_encoder.forward_summarized(
            encoded_context,
            state.phase,
            ledger_summary,
            work_summary,
            position_summary,
            market_summary,
        )
        return self._score(hidden, encoded_tiles, state)

    def forward_bucketed(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: IntentTensorState,
        candidate_counts: Tensor,
        *,
        validate: bool = True,
    ) -> IntentPolicyOutput:
        """Score learner rows without encoding their masked candidate padding."""
        if validate:
            state.validate()
        if candidate_counts.shape != (state.batch_size,):
            raise ValueError("intent candidate counts do not align with learner rows")
        candidate_width = state.candidate_fields.shape[1]
        counts = candidate_counts.detach().to(device="cpu", dtype=torch.long)
        if validate and bool(((counts < 1) | (counts > candidate_width)).any()):
            raise ValueError("intent candidate count exceeds its padded width")

        capacities: list[int] = []
        capacity = 1
        while capacity < candidate_width:
            capacities.append(capacity)
            capacity *= 2
        if not capacities or capacities[-1] != candidate_width:
            capacities.append(candidate_width)

        candidate_outputs: list[Tensor] = []
        outcome_outputs: list[Tensor] = []
        output_rows: list[Tensor] = []
        lower = 0
        for capacity in capacities:
            cpu_rows = ((counts > lower) & (counts <= capacity)).nonzero().squeeze(-1)
            lower = capacity
            if cpu_rows.numel() == 0:
                continue
            rows = cpu_rows.to(device=context.device)
            bucket = IntentTensorState(
                candidate_fields=state.candidate_fields[:, :capacity].index_select(0, rows),
                candidate_features=state.candidate_features[:, :capacity].index_select(0, rows),
                candidate_mask=state.candidate_mask[:, :capacity].index_select(0, rows),
                ledger=state.ledger.index_select(0, rows),
                status=state.status.index_select(0, rows),
                work_priorities=state.work_priorities.index_select(0, rows),
                work_orders=state.work_orders.index_select(0, rows),
                work_mask=state.work_mask.index_select(0, rows),
                positions=state.positions.index_select(0, rows),
                market_prefix=state.market_prefix.index_select(0, rows),
                market_mask=state.market_mask.index_select(0, rows),
                phase=state.phase.index_select(0, rows),
            )
            output = self(
                context.index_select(0, rows),
                tile_context.index_select(0, rows),
                bucket,
                validate=False,
            )
            candidate_outputs.append(
                F.pad(
                    output.candidate_logits,
                    (0, candidate_width - capacity),
                    value=-torch.inf,
                )
            )
            outcome_outputs.append(output.outcome_logits)
            output_rows.append(rows)
        if not output_rows:
            raise ValueError("intent learner bucket plan contains no rows")
        restore = torch.cat(output_rows).argsort()
        return IntentPolicyOutput(
            candidate_logits=torch.cat(candidate_outputs).index_select(0, restore),
            outcome_logits=torch.cat(outcome_outputs).index_select(0, restore),
        )

    def forward_value(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: IntentTensorState,
        *,
        validate: bool = True,
    ) -> IntentPolicyOutput:
        """Evaluate only the critic when the rollout cannot update the actor."""
        if validate:
            state.validate()
        encoded_tiles = cast(Tensor, self.tile_context(tile_context))
        hidden = self.state_encoder(context, encoded_tiles, state)
        return IntentPolicyOutput(
            candidate_logits=hidden.new_empty((state.batch_size, 0)),
            outcome_logits=cast(Tensor, self.value_head(hidden)),
        )

    def select(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: IntentTensorState,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
        validate: bool = True,
        compute_entropy: bool = True,
    ) -> IntentSelection:
        """Choose one successor and retain its exact behavior statistics."""
        output = self(context, tile_context, state, validate=validate)
        return self._select_output(
            output,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
        )

    def select_with_work_summary(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: IntentTensorState,
        work_summary: Tensor,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
        validate: bool = True,
        compute_entropy: bool = True,
    ) -> IntentSelection:
        """Choose a successor using an incrementally maintained work mean."""
        output = self.forward_with_work_summary(
            context,
            tile_context,
            state,
            work_summary,
            validate=validate,
        )
        return self._select_output(
            output,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
        )

    def select_prepared(
        self,
        encoded_context: Tensor,
        encoded_tiles: Tensor,
        state: IntentTensorState,
        work_summary: Tensor,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
        compute_entropy: bool = True,
    ) -> IntentSelection:
        """Choose from a pseudo-step with cached turn-static projections."""
        output = self.forward_prepared(
            encoded_context,
            encoded_tiles,
            state,
            work_summary,
        )
        return self._select_output(
            output,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
        )

    @staticmethod
    def _select_output(
        output: IntentPolicyOutput,
        *,
        sample: bool,
        generator: torch.Generator | None,
        compute_entropy: bool,
    ) -> IntentSelection:
        """Sample or greedily select from already computed policy logits."""
        probabilities = torch.softmax(output.candidate_logits.float(), dim=-1)
        indices = (
            torch.multinomial(probabilities, 1, generator=generator).squeeze(-1)
            if sample
            else probabilities.argmax(dim=-1)
        )
        selected = probabilities.gather(1, indices[:, None]).squeeze(1)
        log_probability = selected.clamp_min(torch.finfo(selected.dtype).tiny).log()
        entropy = (
            -(probabilities * probabilities.clamp_min(1e-30).log()).sum(dim=-1)
            if compute_entropy
            else torch.zeros_like(log_probability)
        )
        return IntentSelection(indices, log_probability, entropy, output.value)


class IntentActorCritic(nn.Module):
    """Attach the intent pointer to a causal pretrained turn encoder."""

    def __init__(self, actor: TurnPolicyNet, intents: IntentPolicy) -> None:
        """Validate and bind the shared context boundary."""
        super().__init__()
        if actor.architecture.model_width != intents.architecture.context_width:
            raise ValueError("intent context width differs from the turn encoder")
        if actor.architecture.board_shape[-1] != intents.architecture.board_size:
            raise ValueError("intent and turn encoder board sizes differ")
        self.actor = actor
        self.intents = intents

    def start_turn(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        previous_actions: Tensor,
        previous_quantities: Tensor,
        previous_mask: Tensor,
        history: HistoryState | None,
        strategy_state: Tensor | None,
        economic_state: Tensor | None,
    ) -> tuple[Tensor, Tensor, HistoryState, Tensor | None]:
        """Run the large official-state encoder exactly once for this turn."""
        context, next_history, next_strategy, _skill = self.actor.start_turn(
            board,
            units,
            global_features,
            previous_actions,
            previous_quantities,
            previous_mask,
            history,
            economic_state=economic_state,
            strategy_state=strategy_state,
            sample_skill=False,
        )
        tile_start = 1 + self.actor.architecture.latent_tokens
        tile_stop = tile_start + self.intents.architecture.tile_count
        return (
            context.memory[:, 0],
            context.memory[:, tile_start:tile_stop],
            next_history,
            next_strategy,
        )

    def evaluate_sequences(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        actions: Tensor,
        quantities: Tensor,
        turn_mask: Tensor,
        decision_mask: Tensor,
        state: IntentTensorState,
        episode_index: Tensor,
        turn_index: Tensor,
        economic_state: Tensor | None,
        *,
        candidate_counts: Tensor | None = None,
        value_only: bool = False,
        validate: bool = True,
    ) -> IntentPolicyOutput:
        """Reconstruct causal turn contexts for flattened pseudo-steps."""
        encoding = self.actor.encode_sequence(
            board,
            units,
            global_features,
            actions,
            quantities,
            turn_mask,
            decision_mask,
            economic_state=economic_state,
            compute_strategy=False,
        )
        episodes, turns = encoding.history.shape[:2]
        if episode_index.shape != turn_index.shape or episode_index.ndim != 1:
            raise ValueError("intent decision-to-turn indices must be aligned")
        rows = episode_index.long()
        columns = turn_index.long()
        if validate and bool(
            ((rows < 0) | (rows >= episodes) | (columns < 0) | (columns >= turns)).any()
        ):
            raise ValueError("intent decision refers outside its episode sequence")
        memory = encoding.memory.view(
            episodes, turns, encoding.memory.shape[1], encoding.memory.shape[2]
        )
        tile_start = 1 + self.actor.architecture.latent_tokens
        tile_stop = tile_start + self.intents.architecture.tile_count
        history = encoding.history[rows, columns]
        tiles = memory[rows, columns, tile_start:tile_stop]
        if value_only:
            return self.intents.forward_value(history, tiles, state, validate=validate)
        return (
            self.intents.forward_bucketed(
                history,
                tiles,
                state,
                candidate_counts,
                validate=validate,
            )
            if candidate_counts is not None
            else self.intents(history, tiles, state, validate=validate)
        )


__all__ = [
    "IntentActorCritic",
    "IntentArchitecture",
    "IntentPolicy",
    "IntentPolicyOutput",
    "IntentSelection",
]
