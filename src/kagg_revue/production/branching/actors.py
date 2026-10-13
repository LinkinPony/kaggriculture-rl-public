"""Fixed-buffer mixed self-play/script continuation with independently controlled seats."""

import torch
from torch import Tensor, nn

from kagg_revue.policy.spatial.model import Policy


class ContinuationPolicy(Policy):
    """Change the learned player's frozen continuation while keeping its opponent fixed."""

    own_rows: Tensor
    opponent_rows: Tensor

    def __init__(self, actor: Policy, opponent: Policy, selfplay_seats: Tensor, scripts: int):
        """Bind game ownership once; no actor receives the other player's observation."""
        nn.Module.__init__(self)
        self.layout, self.actor, self.opponent = actor.layout, actor, opponent
        device = next(actor.parameters()).device
        games = len(selfplay_seats)
        indices = torch.arange(games, device=device)
        self.register_buffer(
            "own_rows",
            torch.cat(
                (2 * indices + selfplay_seats, torch.arange(scripts, device=device) + 2 * games)
            ),
            persistent=False,
        )
        self.register_buffer("opponent_rows", 2 * indices + 1 - selfplay_seats, persistent=False)

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Decode the same bounded mixed population for each continuation ensemble member."""
        own, own_lp = self.actor.act(
            observations[self.own_rows], steps[self.own_rows], sample=False
        )
        rival, rival_lp = self.opponent.act(
            observations[self.opponent_rows], steps[self.opponent_rows], sample=False
        )
        actions = torch.empty((len(steps), self.layout.factors), dtype=own.dtype, device=own.device)
        probabilities = torch.empty_like(actions, dtype=torch.float32)
        actions[self.own_rows], actions[self.opponent_rows] = own, rival
        probabilities[self.own_rows], probabilities[self.opponent_rows] = own_lp, rival_lp
        return actions, probabilities
