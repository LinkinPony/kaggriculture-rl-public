"""Score compact legal candidate rows through the authoritative pointer model."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.effects.data import EffectTensorState
from kagg_revue.policy.effects.encoding import compiled_flat_candidate_forward

if TYPE_CHECKING:
    from kagg_revue.policy.effects.model import EffectPolicy


def sparse_candidate_scores(
    policy: EffectPolicy,
    query: Tensor,
    state_part: Tensor,
    projected_tiles: Tensor,
    state: EffectTensorState,
) -> Tensor:
    """Skip masked candidates whose logits have no effect on any objective."""
    rows, columns = state.candidate_mask.nonzero(as_tuple=True)
    fields = state.candidate_fields[rows, columns]
    features = state.candidate_features[rows, columns]
    encoder = policy.candidate_encoder
    candidates = (
        compiled_flat_candidate_forward(encoder, fields, features, projected_tiles, rows)
        if query.device.type == "cuda" and torch.is_grad_enabled()
        else encoder.forward_flattened(fields, features, projected_tiles, rows)
    )
    first = cast(nn.Linear, policy.residual[0])
    last = cast(nn.Linear, policy.residual[2])
    pointer = (query.index_select(0, rows) * candidates).sum(dim=-1) * policy.scale
    residual = last(
        F.silu(
            state_part.index_select(0, rows).squeeze(1)
            + F.linear(candidates, first.weight[:, query.shape[-1] :]),
        )
    ).squeeze(-1)
    logits = query.new_full(state.candidate_mask.shape, -torch.inf)
    return logits.index_put((rows, columns), pointer + residual)
