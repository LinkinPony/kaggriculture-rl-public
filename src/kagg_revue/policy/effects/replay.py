"""Reuse shared task encodings with exact conditional work and market replay."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import torch
from torch import Tensor

from kagg_revue.policy.effects.conditioning import condition_tasks, encode_tasks
from kagg_revue.policy.effects.data import EffectTensorState
from kagg_revue.policy.effects.precision import full_precision

if TYPE_CHECKING:
    from kagg_revue.policy.effects.model import EffectActorCritic
from kagg_revue.policy.effects.schema import EffectPolicyOutput, EffectSequenceContext


def evaluate_reused_work(
    model: EffectActorCritic,
    sequence: EffectSequenceContext,
    state: EffectTensorState,
    episodes: Tensor,
    turns: Tensor,
    candidates: EffectTensorState,
    *,
    critic_actor_gradient: bool = True,
    validate: bool = False,
) -> EffectPolicyOutput:
    """Score each work turn once and every projected market prefix separately.

    Legacy ranked work reuses scores; conditional work reuses root/candidate
    encodings. The union includes candidates made legal by later choices, and
    each original mask is applied before calculating its factor distribution.
    """
    count = episodes.numel()
    unique_rows = torch.arange(count, device=episodes.device)
    turn_surface = sequence.context.shape[0] * sequence.context.shape[1]
    keys = torch.where(
        state.phase == 0,
        episodes * sequence.context.shape[1] + turns,
        unique_rows + turn_surface,
    )
    unique, inverse = torch.unique(keys, sorted=True, return_inverse=True)
    representatives = torch.full_like(unique, count).scatter_reduce_(
        0,
        inverse,
        unique_rows,
        reduce="amin",
    )
    if representatives.numel() == count and not model.effects.architecture.task_conditioning:
        return model.evaluate_effect_sequence_context(
            sequence,
            state,
            episodes,
            turns,
            candidate_states=(candidates,),
            critic_actor_gradient=critic_actor_gradient,
            validate=validate,
        )

    def select(source: EffectTensorState) -> EffectTensorState:
        return EffectTensorState(
            **{
                name: getattr(source, name).index_select(0, representatives)
                for name in EffectTensorState.__dataclass_fields__
            }
        )

    union = (
        torch.zeros(
            (unique.numel(), candidates.candidate_mask.shape[1]),
            dtype=torch.int32,
            device=episodes.device,
        ).index_add_(0, inverse, candidates.candidate_mask.int())
        > 0
    )
    compact_candidates = replace(select(candidates), candidate_mask=union)
    if model.effects.architecture.task_conditioning:
        compact = select(state)
        compact = replace(
            compact,
            candidate_fields=compact_candidates.candidate_fields,
            candidate_features=compact_candidates.candidate_features,
            candidate_mask=compact_candidates.candidate_mask,
        )
        return _conditional_output(
            model,
            sequence,
            state,
            episodes,
            turns,
            candidates,
            compact,
            representatives,
            inverse,
            critic_actor_gradient=critic_actor_gradient,
        )
    output = model.evaluate_effect_sequence_context(
        sequence,
        select(state),
        episodes.index_select(0, representatives),
        turns.index_select(0, representatives),
        candidate_states=(compact_candidates,),
        critic_actor_gradient=critic_actor_gradient,
        validate=validate,
    )
    return EffectPolicyOutput(
        candidate_logits=output.candidate_logits.index_select(0, inverse).masked_fill(
            ~candidates.candidate_mask,
            -torch.inf,
        ),
        outcome_logits=output.outcome_logits.index_select(0, inverse),
    )


@full_precision
def _conditional_output(
    model: EffectActorCritic,
    sequence: EffectSequenceContext,
    state: EffectTensorState,
    episodes: Tensor,
    turns: Tensor,
    candidates: EffectTensorState,
    compact: EffectTensorState,
    representatives: Tensor,
    inverse: Tensor,
    *,
    critic_actor_gradient: bool,
) -> EffectPolicyOutput:
    """Retain work embeddings while keeping the large shared neural batches intact."""
    policy = model.effects
    work_rows = (state.phase == 0).nonzero().squeeze(-1)
    work_roots = (compact.phase == 0).nonzero().squeeze(-1)
    ep = episodes.index_select(0, representatives).long()
    ts = turns.index_select(0, representatives).long()
    encoding = encode_tasks(
        policy,
        sequence.context[ep, ts],
        sequence.tile_context[ep, ts],
        compact,
        None if sequence.strategy is None else sequence.strategy[ep, ts],
        sparse=True,
        candidate_cache_rows=work_roots,
    )
    logits = encoding.logits.index_select(0, inverse)
    if work_rows.numel():
        work_logits = condition_tasks(
            policy,
            encoding.index_select(inverse[work_rows]),
            state.work_prefix[work_rows],
            state.work_mask[work_rows],
            state.phase[work_rows],
        )
        logits = logits.index_copy(0, work_rows, work_logits)
    if sequence.outcome_logits is None:
        hidden = encoding.hidden if critic_actor_gradient else encoding.hidden.detach()
        values = policy.value_head(hidden).index_select(0, inverse)
    else:
        values = sequence.outcome_logits[episodes.long(), turns.long()]
    return EffectPolicyOutput(logits.masked_fill(~candidates.candidate_mask, -torch.inf), values)
