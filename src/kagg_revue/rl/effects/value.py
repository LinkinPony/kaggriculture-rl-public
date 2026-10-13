"""Coarse-boundary critic evaluation without factor or candidate transfers."""

from __future__ import annotations

from dataclasses import replace

import torch
from torch import Tensor

from kagg_revue.policy.effects.critic import EffectCritic
from kagg_revue.rl.effects.data import EffectRolloutBatch


@torch.no_grad()
def predict_turns(critic: EffectCritic, batch: EffectRolloutBatch, episodes: int = 8) -> Tensor:
    """Evaluate bounded complete-episode shards and return a compact CPU surface."""
    device = next(critic.parameters()).device
    result = torch.empty((*batch.turn_mask.shape, 3), dtype=torch.float32)
    names = (
        "board",
        "units",
        "global_features",
        "actions",
        "quantities",
        "turn_mask",
        "decision_mask",
    )
    for start in range(0, batch.episode_count, episodes):
        stop = min(start + episodes, batch.episode_count)
        inputs = [getattr(batch, name)[start:stop].to(device) for name in names]
        result[start:stop].copy_(critic(*inputs).float().cpu())
    return result


def attach_behavior_values(critic: EffectCritic, batch: EffectRolloutBatch) -> EffectRolloutBatch:
    """Broadcast the frozen critic's turn values through the native factor index."""
    probabilities = predict_turns(critic, batch).softmax(-1)
    values = probabilities[..., 2] - probabilities[..., 0]
    return replace(batch, old_value=values[batch.episode_index.long(), batch.turn_index.long()])


__all__ = ["attach_behavior_values", "predict_turns"]
