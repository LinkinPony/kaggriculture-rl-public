"""Shared task encodings and inexpensive prefix-conditioned pointer queries."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.effects.data import EffectTensorState
from kagg_revue.policy.effects.encoding import compiled_flat_candidate_forward
from kagg_revue.policy.effects.precision import full_precision

if TYPE_CHECKING:
    from kagg_revue.policy.effects.model import EffectPolicy


@dataclass(frozen=True)
class TaskEncoding:
    """One immutable candidate surface for a batch of official work turns."""

    logits: Tensor
    hidden: Tensor
    candidates: Tensor
    candidate_rows: Tensor | None = None

    def index_select(self, rows: Tensor) -> TaskEncoding:
        """Gather roots while preserving gradients into shared candidate encodings."""
        cached = rows
        if self.candidate_rows is not None:
            lookup = rows.new_full((self.hidden.shape[0],), -1)
            lookup[self.candidate_rows] = torch.arange(
                self.candidate_rows.numel(), device=rows.device
            )
            cached = lookup[rows]
        return TaskEncoding(
            self.logits.index_select(0, rows),
            self.hidden.index_select(0, rows),
            self.candidates.index_select(0, cached),
        )


@full_precision
def encode_tasks(
    policy: EffectPolicy,
    context: Tensor,
    tiles: Tensor,
    state: EffectTensorState,
    strategy: Tensor | None,
    *,
    sparse: bool = False,
    entity_capacity: int | None = None,
    candidate_cache_rows: Tensor | None = None,
) -> TaskEncoding:
    """Encode a root and its candidates once, independent of work prefix length."""
    root = replace(state, work_mask=state.work_mask & (state.phase != 0)[:, None])
    hidden = policy.state_encoder(context, strategy, root, entity_capacity=entity_capacity)
    if sparse:
        rows, columns = state.candidate_mask.nonzero(as_tuple=True)
        encoder = policy.candidate_encoder
        fields = state.candidate_fields[rows, columns]
        features = state.candidate_features[rows, columns]
        projected = encoder.project_tiles(tiles)
        compact = (
            compiled_flat_candidate_forward(encoder, fields, features, projected, rows)
            if context.device.type == "cuda" and torch.is_grad_enabled()
            else encoder.forward_flattened(fields, features, projected, rows)
        )
        query, state_part = policy._prepare_candidate_scoring(hidden)
        pointer = (query.index_select(0, rows) * compact).sum(-1) * policy.scale
        first = cast(nn.Linear, policy.residual[0])
        last = cast(nn.Linear, policy.residual[2])
        residual = last(
            F.silu(
                state_part.index_select(0, rows).squeeze(1)
                + F.linear(compact, first.weight[:, hidden.shape[-1] :])
            )
        ).squeeze(-1)
        logits = hidden.new_full(state.candidate_mask.shape, -torch.inf)
        logits = logits.index_put((rows, columns), pointer + residual)
        if candidate_cache_rows is None:
            candidates = compact.new_zeros((*state.candidate_mask.shape, hidden.shape[-1]))
            candidates = candidates.index_put((rows, columns), compact)
        else:
            lookup = rows.new_full((hidden.shape[0],), -1)
            lookup[candidate_cache_rows] = torch.arange(
                candidate_cache_rows.numel(), device=rows.device
            )
            cached = lookup[rows]
            retained = cached >= 0
            candidates = compact.new_zeros(
                (candidate_cache_rows.numel(), state.candidate_mask.shape[1], hidden.shape[-1])
            )
            candidates = candidates.index_put(
                (cached[retained], columns[retained]), compact[retained]
            )
    else:
        if candidate_cache_rows is not None:
            raise ValueError("partial task caches require sparse candidate encoding")
        candidates = policy.candidate_encoder(
            state.candidate_fields, state.candidate_features, tiles
        )
        logits = policy._candidate_scores(hidden, candidates)
    return TaskEncoding(logits, hidden, candidates, candidate_cache_rows)


@full_precision
def condition_tasks(
    policy: EffectPolicy,
    encoding: TaskEncoding,
    prefix: Tensor,
    prefix_mask: Tensor,
    phase: Tensor,
) -> Tensor:
    """Change candidate odds using the selected tasks, quantities, and unit bindings."""
    if policy.prefix_query is None:
        raise ValueError("task conditioning requires a prefix decoder")
    mask = prefix_mask & (phase == 0)[:, None]
    actions = policy.state_encoder._actions(prefix, 2)
    if policy.architecture.prefix_encoding == "joint_action_v2":
        # Nonlinearity before pooling preserves request/target/unit bindings.
        # Summing additive field embeddings alone loses those associations.
        actions = F.silu(actions)
    elif policy.architecture.prefix_encoding != "field_sum_v1":
        raise ValueError("unsupported task prefix encoding")
    summary = (actions * mask[..., None]).sum(1)
    count = mask.sum(1, keepdim=True)
    summary = summary / count.clamp_min(1).sqrt()
    query = policy.prefix_query(torch.cat((encoding.hidden, summary), -1))
    query = query * (count > 0)
    correction = torch.bmm(encoding.candidates, query[..., None]).squeeze(-1)
    return cast(Tensor, encoding.logits + correction * policy.scale)


__all__ = ["TaskEncoding", "condition_tasks", "encode_tasks"]
