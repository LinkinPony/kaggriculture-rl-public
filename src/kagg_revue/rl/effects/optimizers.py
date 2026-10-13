"""Separately owned actor and critic AdamW states with atomic checkpointing."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import Any

from torch import Tensor, nn
from torch.optim import AdamW, Optimizer


class IndependentAdamW(Optimizer):
    """Expose two independent optimizers through the existing checkpoint ABI."""

    def __init__(
        self,
        actor: Sequence[nn.Parameter],
        critic: Sequence[nn.Parameter],
        *,
        actor_lr: float,
        critic_lr: float,
        weight_decay: float,
        fused: bool,
    ) -> None:
        """Allocate disjoint parameter ownership and independent Adam clocks."""
        if {id(p) for p in actor} & {id(p) for p in critic}:
            raise ValueError("independent optimizers cannot share parameters")
        super().__init__([{"params": actor}, {"params": critic}], {})
        self.actor = AdamW(actor, lr=actor_lr, weight_decay=weight_decay, fused=fused)
        self.critic = AdamW(critic, lr=critic_lr, weight_decay=weight_decay, fused=fused)
        self._refresh()

    def _refresh(self) -> None:
        self.param_groups = self.actor.param_groups + self.critic.param_groups
        self.state = defaultdict(dict)
        self.state.update(self.actor.state)
        self.state.update(self.critic.state)

    def state_dict(self) -> dict[str, Any]:
        """Store both optimizers explicitly rather than sharing update clocks."""
        return {"actor": self.actor.state_dict(), "critic": self.critic.state_dict()}

    def load_state_dict(self, state_dict: dict[str, Any]) -> None:
        """Restore both components and reconnect the public group references."""
        self.actor.load_state_dict(state_dict["actor"])
        self.critic.load_state_dict(state_dict["critic"])
        self._refresh()

    def zero_grad(self, set_to_none: bool = True) -> None:
        """Clear both disjoint gradient sets."""
        self.actor.zero_grad(set_to_none=set_to_none)
        self.critic.zero_grad(set_to_none=set_to_none)

    def step(self, closure: Callable[[], float] | None = None) -> Tensor | None:  # type: ignore[override]
        """Advance both components when no policy rollback is required."""
        if closure is not None:
            raise ValueError("effect optimizers do not accept closures")
        self.actor.step()
        self.critic.step()
        self._refresh()
        return None


__all__ = ["IndependentAdamW"]
