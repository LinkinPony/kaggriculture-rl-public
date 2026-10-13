"""Independent causal state representation for terminal outcome prediction."""

from __future__ import annotations

from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.effects.precision import full_precision
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.transformer import RMSNorm


class EffectCritic(nn.Module):
    """Learn visible economic state and history without actor gradients.

    Assets use shared encoders and explicit tile coordinates. The recurrent input contains
    the current observation and only the previous compiled action; no outcomes,
    current sampled action, hidden future events, or future RNG enter the model.
    Values are evaluated in complete episode batches at the rollout boundary.
    """

    coordinates: Tensor

    def __init__(self, architecture: ActorArchitecture) -> None:
        """Build separately owned feature encoders, memory, and W/D/L head."""
        super().__init__()
        width = architecture.model_width

        def encoder(features: int) -> nn.Sequential:
            return nn.Sequential(
                nn.Linear(features, width), RMSNorm(width), nn.SiLU(), nn.Linear(width, width)
            )

        channels, height, columns = architecture.board_shape[1:]
        self.board = encoder(channels + 2)
        self.units = encoder(architecture.unit_shape[-1])
        self.assets = nn.Linear(8 * width, width)
        y, x = torch.meshgrid(
            torch.linspace(-1, 1, height), torch.linspace(-1, 1, columns), indexing="ij"
        )
        self.register_buffer("coordinates", torch.stack((x, y), -1).flatten(0, 1))
        self.global_state = encoder(architecture.global_features)
        self.actions = nn.Embedding(architecture.action_tokens, width)
        self.quantity = nn.Linear(1, width, bias=False)
        self.input_norm = RMSNorm(width)
        self.memory = nn.GRU(width, width, batch_first=True)
        self.head = nn.Sequential(
            RMSNorm(2 * width + architecture.global_features),
            nn.Linear(2 * width + architecture.global_features, architecture.feedforward_width),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, 3),
        )

    @full_precision
    def forward(
        self,
        board: Tensor,
        units: Tensor,
        global_features: Tensor,
        actions: Tensor,
        quantities: Tensor,
        turn_mask: Tensor,
        decision_mask: Tensor,
    ) -> Tensor:
        """Predict once per official turn with a causal full-episode recurrence."""
        action_tokens = self.actions(actions.long())
        quantity_tokens = self.quantity(torch.log1p(quantities.float().clamp_min(0))[..., None])
        mask = decision_mask[..., None]
        action_summary = ((action_tokens + quantity_tokens) * mask).sum(-2)
        action_summary = action_summary / decision_mask.sum(-1).clamp_min(1)[..., None]
        previous = torch.cat((torch.zeros_like(action_summary[:, :1]), action_summary[:, :-1]), 1)
        tiles = board.float().flatten(-2).transpose(-1, -2)
        coordinates = self.coordinates.expand(*tiles.shape[:-1], 2)
        tile_features = self.board(torch.cat((tiles, coordinates), -1))
        unit_features = self.units(units.float())
        assets = torch.cat(
            (
                tile_features.mean(-2).flatten(-2),
                tile_features.amax(-2).flatten(-2),
                unit_features.mean(-2).flatten(-2),
                unit_features.amax(-2).flatten(-2),
            ),
            -1,
        )
        current = (
            self.input_norm(
                self.assets(assets) + self.global_state(global_features.float()) + previous
            )
            * turn_mask[..., None]
        )
        memory, _ = self.memory(current)
        return cast(Tensor, self.head(torch.cat((current, memory, global_features.float()), -1)))


__all__ = ["EffectCritic"]
