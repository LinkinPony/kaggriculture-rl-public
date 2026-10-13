"""Recurrent pointer actor and W/D/L critic for atomic effects."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.effects.conditioning import condition_tasks, encode_tasks
from kagg_revue.policy.effects.data import EffectTensorState
from kagg_revue.policy.effects.encoding import (
    EffectCandidateEncoder,
    EffectEmbeddings,
    EffectStateEncoder,
)
from kagg_revue.policy.effects.precision import full_precision
from kagg_revue.policy.effects.schema import (
    EffectArchitecture,
    EffectPolicyOutput,
    EffectSelection,
)
from kagg_revue.policy.effects.scoring import sparse_candidate_scores
from kagg_revue.policy.transformer import RMSNorm


class EffectPolicy(nn.Module):
    """Vectorized pointer policy over complete atomic-effect candidates."""

    def __init__(self, architecture: EffectArchitecture) -> None:
        """Create shared typed encoders, pointer scorer, and W/D/L head."""
        super().__init__()
        self.architecture = architecture
        typed = EffectEmbeddings(architecture)
        self.state_encoder = EffectStateEncoder(architecture, typed)
        self.candidate_encoder = EffectCandidateEncoder(architecture, typed)
        width = architecture.model_width
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
        self.prefix_query: nn.Sequential | None = None
        if architecture.task_conditioning:
            self.prefix_query = nn.Sequential(
                RMSNorm(2 * width),
                nn.Linear(2 * width, width),
                nn.SiLU(),
                nn.Linear(width, width, bias=False),
            )
            nn.init.zeros_(cast(nn.Linear, self.prefix_query[-1]).weight)
        self.scale = width**-0.5

    def _prepare_candidate_scoring(self, hidden: Tensor) -> tuple[Tensor, Tensor]:
        """Project the state-dependent halves shared by every candidate."""
        query = cast(Tensor, self.query(hidden))
        candidate_query = F.linear(query, self.key.weight.T)
        first = cast(nn.Linear, self.residual[0])
        width = hidden.shape[-1]
        state_part = F.linear(hidden, first.weight[:, :width], first.bias)[:, None]
        return candidate_query, state_part

    def _prepared_candidate_scores(
        self,
        candidate_query: Tensor,
        state_part: Tensor,
        candidates: Tensor,
    ) -> Tensor:
        """Score candidates using the prepared state-dependent projections."""
        first = cast(nn.Linear, self.residual[0])
        last = cast(nn.Linear, self.residual[2])
        width = candidate_query.shape[-1]
        pointer = (candidate_query[:, None] * candidates).sum(dim=-1) * self.scale
        candidate_part = F.linear(candidates, first.weight[:, width:])
        residual = last(F.silu(state_part + candidate_part)).squeeze(-1)
        return cast(Tensor, pointer + residual)

    def _candidate_scores(self, hidden: Tensor, candidates: Tensor) -> Tensor:
        """Score already encoded candidates from one shared state encoding."""
        candidate_query, state_part = self._prepare_candidate_scoring(hidden)
        return self._prepared_candidate_scores(
            candidate_query,
            state_part,
            candidates,
        )

    def _validate_inputs(
        self,
        context: Tensor,
        tile_context: Tensor,
        strategy: Tensor | None,
        state: EffectTensorState,
        *,
        validate: bool,
    ) -> None:
        if validate:
            state.validate()
        expected_context = (state.batch_size, self.architecture.context_width)
        if context.shape != expected_context:
            raise ValueError("effect turn context differs from its architecture")
        expected_tiles = (
            state.batch_size,
            self.architecture.tile_count,
            self.architecture.context_width,
        )
        if tile_context.shape != expected_tiles:
            raise ValueError("effect tile context differs from its architecture")
        if strategy is not None and strategy.shape != expected_context:
            raise ValueError("effect strategy summary differs from its architecture")

    def _encode(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: EffectTensorState,
        strategy: Tensor | None = None,
        *,
        validate: bool = True,
        mask_candidates: bool = True,
        entity_capacity: int | None = None,
    ) -> tuple[Tensor, Tensor]:
        """Return masked pointer scores and the shared state representation."""
        self._validate_inputs(
            context,
            tile_context,
            strategy,
            state,
            validate=validate,
        )
        if self.architecture.task_conditioning:
            encoding = encode_tasks(
                self, context, tile_context, state, strategy, entity_capacity=entity_capacity
            )
            logits = condition_tasks(
                self, encoding, state.work_prefix, state.work_mask, state.phase
            )
            if mask_candidates:
                logits = logits.masked_fill(~state.candidate_mask, -torch.inf)
            return logits, encoding.hidden
        hidden = self.state_encoder(context, strategy, state, entity_capacity=entity_capacity)
        candidates = self.candidate_encoder(
            state.candidate_fields,
            state.candidate_features,
            tile_context,
        )
        logits = self._candidate_scores(hidden, candidates)
        if mask_candidates:
            logits = logits.masked_fill(~state.candidate_mask, -torch.inf)
        return logits, hidden

    @full_precision
    def forward_logits(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: EffectTensorState,
        strategy: Tensor | None = None,
        *,
        validate: bool = True,
        entity_capacity: int | None = None,
    ) -> Tensor:
        """Score policy factors without evaluating the unused critic head."""
        logits, _hidden = self._encode(
            context,
            tile_context,
            state,
            strategy,
            validate=validate,
            entity_capacity=entity_capacity,
        )
        return logits

    @full_precision
    def forward(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: EffectTensorState,
        strategy: Tensor | None = None,
        *,
        critic_actor_gradient: bool = True,
        validate: bool = True,
        mask_candidates: bool = True,
        entity_capacity: int | None = None,
    ) -> EffectPolicyOutput:
        """Score complete tuples and one direct terminal W/D/L value.

        A ranked-work cache must retain unmasked scores: a later prefix can
        make an initially unavailable request legal. Callers that disable
        masking must apply the current native mask before every selection.
        """
        logits, hidden = self._encode(
            context,
            tile_context,
            state,
            strategy,
            validate=validate,
            mask_candidates=mask_candidates,
            entity_capacity=entity_capacity,
        )
        return EffectPolicyOutput(
            candidate_logits=logits,
            outcome_logits=cast(
                Tensor,
                self.value_head(hidden if critic_actor_gradient else hidden.detach()),
            ),
        )

    @full_precision
    def forward_bucketed(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: EffectTensorState,
        candidate_counts: Tensor,
        strategy: Tensor | None = None,
        *,
        critic_actor_gradient: bool = True,
        validate: bool = True,
    ) -> EffectPolicyOutput:
        """Score learner rows without evaluating rollout-wide padding."""
        self._validate_inputs(
            context,
            tile_context,
            strategy,
            state,
            validate=validate,
        )
        if candidate_counts.shape != (state.batch_size,):
            raise ValueError("effect candidate counts do not align with rows")
        maximum = state.candidate_fields.shape[1]
        counts = candidate_counts.detach().to(device="cpu", dtype=torch.long)
        if validate and bool(((counts < 1) | (counts > maximum)).any()):
            raise ValueError("effect candidate count exceeds its padded width")

        capacities: list[int] = []
        capacity = 1
        while capacity < maximum:
            capacities.append(capacity)
            capacity *= 2
        if not capacities or capacities[-1] != maximum:
            capacities.append(maximum)

        # State entities and the critic are independent of candidate width.  Encoding
        # them separately in every candidate bucket fragmented a production learner
        # microbatch into many tiny Transformer/value-head launches.
        hidden = self.state_encoder(context, strategy, state)
        outcome_logits = cast(
            Tensor,
            self.value_head(hidden if critic_actor_gradient else hidden.detach()),
        )
        projected_tiles = self.candidate_encoder.project_tiles(tile_context)
        candidate_query, state_part = self._prepare_candidate_scoring(hidden)

        score_parts: list[Tensor] = []
        row_parts: list[Tensor] = []
        lower = 0
        for capacity in capacities:
            cpu_rows = ((counts > lower) & (counts <= capacity)).nonzero().squeeze(-1)
            lower = capacity
            if cpu_rows.numel() == 0:
                continue
            rows = cpu_rows.to(device=context.device)
            fields = state.candidate_fields.index_select(0, rows)[:, :capacity]
            features = state.candidate_features.index_select(0, rows)[:, :capacity]
            candidates = self.candidate_encoder.forward_projected(
                fields,
                features,
                projected_tiles.index_select(0, rows),
            )
            logits = self._prepared_candidate_scores(
                candidate_query.index_select(0, rows),
                state_part.index_select(0, rows),
                candidates,
            ).masked_fill(
                ~state.candidate_mask.index_select(0, rows)[:, :capacity],
                -torch.inf,
            )
            score_parts.append(
                F.pad(
                    logits,
                    (0, maximum - capacity),
                    value=-torch.inf,
                )
            )
            row_parts.append(rows)
        if not row_parts:
            raise ValueError("effect learner bucket plan contains no rows")
        restore = torch.cat(row_parts).argsort()
        return EffectPolicyOutput(
            candidate_logits=torch.cat(score_parts).index_select(0, restore),
            outcome_logits=outcome_logits,
        )

    @full_precision
    def forward_sharded(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: EffectTensorState,
        candidate_states: Sequence[EffectTensorState],
        strategy: Tensor | None = None,
        *,
        critic_actor_gradient: bool = True,
        validate: bool = True,
    ) -> EffectPolicyOutput:
        """Score compact candidate-width shards with one shared state encoding."""
        self._validate_inputs(
            context,
            tile_context,
            strategy,
            state,
            validate=validate,
        )
        if not candidate_states:
            raise ValueError("effect learner candidate shards are empty")
        if validate:
            for candidate_state in candidate_states:
                candidate_state.validate()
        if sum(item.batch_size for item in candidate_states) != state.batch_size:
            raise ValueError("effect learner candidate shards do not align with state rows")

        hidden = self.state_encoder(context, strategy, state)
        outcome_logits = cast(
            Tensor,
            self.value_head(hidden if critic_actor_gradient else hidden.detach()),
        )
        projected_tiles = self.candidate_encoder.project_tiles(tile_context)
        candidate_query, state_part = self._prepare_candidate_scoring(hidden)
        maximum = max(item.candidate_fields.shape[1] for item in candidate_states)
        score_parts: list[Tensor] = []
        offset = 0
        for candidate_state in candidate_states:
            stop = offset + candidate_state.batch_size
            logits = sparse_candidate_scores(
                self,
                candidate_query[offset:stop],
                state_part[offset:stop],
                projected_tiles[offset:stop],
                candidate_state,
            )
            score_parts.append(F.pad(logits, (0, maximum - logits.shape[1]), value=-torch.inf))
            offset = stop
        return EffectPolicyOutput(
            candidate_logits=torch.cat(score_parts),
            outcome_logits=outcome_logits,
        )

    @full_precision
    def forward_value(
        self,
        context: Tensor,
        state: EffectTensorState,
        strategy: Tensor | None = None,
        *,
        critic_actor_gradient: bool = True,
        validate: bool = True,
    ) -> EffectPolicyOutput:
        """Evaluate only the official-turn critic when actor updates are disabled."""
        if validate:
            state.validate()
        expected = (state.batch_size, self.architecture.context_width)
        if context.shape != expected or (strategy is not None and strategy.shape != expected):
            raise ValueError("effect critic context differs from its architecture")
        hidden = self.state_encoder(context, strategy, state)
        return EffectPolicyOutput(
            candidate_logits=hidden.new_empty((state.batch_size, 0)),
            outcome_logits=cast(
                Tensor,
                self.value_head(hidden if critic_actor_gradient else hidden.detach()),
            ),
        )

    def select(
        self,
        context: Tensor,
        tile_context: Tensor,
        state: EffectTensorState,
        strategy: Tensor | None = None,
        *,
        sample: bool,
        generator: torch.Generator | None = None,
        validate: bool = True,
        compute_entropy: bool = True,
    ) -> EffectSelection:
        """Select one complete tuple and retain behavior statistics."""
        output = self(
            context,
            tile_context,
            state,
            strategy,
            validate=validate,
        )
        return self.select_output(
            output,
            sample=sample,
            generator=generator,
            compute_entropy=compute_entropy,
        )

    @staticmethod
    def select_output(
        output: EffectPolicyOutput,
        *,
        sample: bool,
        candidate_mask: Tensor | None = None,
        generator: torch.Generator | None = None,
        compute_entropy: bool = True,
    ) -> EffectSelection:
        """Select from cached logits under the current exact hard mask.

        Work factors call this repeatedly with the one immutable turn-level score
        tensor and the native mask after each accepted ranked request. Market
        factors instead obtain a newly scored output after every prefix update.
        """
        return EffectPolicy.select_logits(
            output.candidate_logits,
            output.value,
            sample=sample,
            candidate_mask=candidate_mask,
            generator=generator,
            compute_entropy=compute_entropy,
        )

    @staticmethod
    def select_logits(
        logits: Tensor,
        value: Tensor,
        *,
        sample: bool,
        candidate_mask: Tensor | None = None,
        generator: torch.Generator | None = None,
        compute_entropy: bool = True,
    ) -> EffectSelection:
        """Select a factor when its official-turn critic is already cached."""
        if value.shape != logits.shape[:1]:
            raise ValueError("effect cached values do not align with policy rows")
        if candidate_mask is not None:
            if candidate_mask.shape != logits.shape:
                raise ValueError("effect cached mask does not align with logits")
            if candidate_mask.dtype != torch.bool:
                raise ValueError("effect cached mask must be boolean")
            if bool((candidate_mask.sum(dim=1) < 1).any()):
                raise ValueError("effect cached mask removed every candidate")
            logits = logits.masked_fill(~candidate_mask, -torch.inf)
        probabilities = torch.softmax(logits.float(), dim=-1)
        candidate_log_probabilities = probabilities.log()
        indices = (
            torch.multinomial(probabilities, 1, generator=generator).squeeze(-1)
            if sample
            else probabilities.argmax(dim=-1)
        )
        log_probability = candidate_log_probabilities.gather(
            1,
            indices[:, None],
        ).squeeze(1)
        entropy = (
            -(probabilities * probabilities.clamp_min(1e-30).log()).sum(dim=-1)
            if compute_entropy
            else torch.zeros_like(log_probability)
        )
        return EffectSelection(
            indices=indices,
            log_probability=log_probability,
            candidate_log_probabilities=candidate_log_probabilities,
            entropy=entropy,
            value=value,
        )
