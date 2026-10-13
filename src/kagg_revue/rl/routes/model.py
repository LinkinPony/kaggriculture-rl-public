"""Compact residual actor-critic for Kaito route choices."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import cast

from torch import Tensor, nn


@dataclass(frozen=True, slots=True)
class RouteActorArchitecture:
    """Checkpoint-bound route actor shape."""

    feature_width: int
    hidden_width: int
    feedforward_width: int
    prior_logit: float

    def record(self) -> dict[str, int | float]:
        """Return a JSON-safe architecture record."""
        return asdict(self)


class RouteActorCritic(nn.Module):
    """Learn residual route logits around the frozen Kaito proposal."""

    def __init__(self, architecture: RouteActorArchitecture) -> None:
        """Create an initially exact greedy copy of the proposal selector."""
        super().__init__()
        self.architecture = architecture
        self.trunk = nn.Sequential(
            nn.LayerNorm(architecture.feature_width),
            nn.Linear(architecture.feature_width, architecture.hidden_width),
            nn.SiLU(),
            nn.Linear(architecture.hidden_width, architecture.feedforward_width),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, architecture.hidden_width),
            nn.SiLU(),
        )
        self.actor = nn.Linear(architecture.hidden_width, 2)
        self.critic = nn.Linear(architecture.hidden_width, 1)
        nn.init.zeros_(self.actor.weight)
        nn.init.zeros_(self.actor.bias)
        nn.init.zeros_(self.critic.weight)
        nn.init.zeros_(self.critic.bias)

    def forward(self, features: Tensor, prior_actions: Tensor) -> tuple[Tensor, Tensor]:
        """Return binary route logits and paired-control value estimates."""
        if features.ndim != 2 or features.shape[1] != self.architecture.feature_width:
            raise ValueError("route actor features differ from its architecture")
        if prior_actions.shape != (features.shape[0],):
            raise ValueError("route actor prior actions differ in batch shape")
        hidden = self.trunk(features.float())
        logits = self.actor(hidden)
        direction = prior_actions.float().mul(2.0).sub(1.0)
        logits = logits.clone()
        logits[:, 1] = logits[:, 1] + direction * self.architecture.prior_logit
        values = self.critic(hidden).squeeze(-1)
        return cast(Tensor, logits), cast(Tensor, values)


__all__ = ["RouteActorArchitecture", "RouteActorCritic"]
