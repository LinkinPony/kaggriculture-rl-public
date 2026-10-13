"""Fused prefix objectives that avoid materializing large intermediate probability tensors."""

import torch
from torch import Tensor
from torch.nn import functional as F

from kagg_revue.learning.optimization.prefix import (
    PrefixCritic,
    prefix_surrogate,
    prefix_value_rows,
)
from kagg_revue.learning.optimization.settings import OptimizationSettings
from kagg_revue.policy.grounded.typed import TypedGroundedPolicy
from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.spatial.model import Policy, scale_logits


class PrefixLosses:
    """Compile forward, causal masks and row reductions in one graph per objective."""

    def __init__(
        self, policy: Policy, critic: PrefixCritic, settings: OptimizationSettings
    ) -> None:
        """Bind unchanged prefix PPO equations to the live optimizer parameters."""
        self.policy = policy
        self.critic = critic
        self.settings = settings
        self.compact = isinstance(policy, TypedGroundedPolicy) and not isinstance(
            policy, MemoryPolicy
        )

    def actor(
        self,
        observations: Tensor,
        steps: Tensor,
        actions: Tensor,
        behavior: Tensor,
        credit: Tensor,
        weights: Tensor,
        mass: Tensor,
        temperature: float,
    ) -> tuple[Tensor, Tensor]:
        """Return weighted PPO loss and KL, including the existing entropy objective."""
        fields = self.policy.field_weights(actions, steps, observations)
        if self.compact:
            assert isinstance(self.policy, TypedGroundedPolicy)
            logits = self.policy.compact_logits(observations, actions)
            columns = self.policy.semantic_fields
            fields, actions = fields[:, columns], actions[:, columns]
            behavior, credit = behavior[:, columns], credit[:, columns]
        else:
            logits = self.policy(observations, steps, actions)
        logits = scale_logits(logits, temperature)
        log_distribution = F.log_softmax(logits, -1)
        probabilities = log_distribution.gather(-1, actions[..., None]).squeeze(-1)
        gain, kl = prefix_surrogate(probabilities - behavior, fields, credit, self.settings.clip)
        loss = -(gain * weights).sum() / mass
        if self.settings.entropy_weight:
            entropy = -(F.softmax(logits, -1) * log_distribution).sum(-1)
            entropy = (entropy * fields).sum(-1)
            loss = loss - self.settings.entropy_weight * (entropy * weights).sum() / mass
        return loss, (kl * weights).sum() / mass

    def value(
        self,
        observations: Tensor,
        steps: Tensor,
        actions: Tensor,
        returns: Tensor,
        weights: Tensor,
        mass: Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        """Fit the same state and exclusive-prefix terminal-return targets."""
        fields = self.policy.field_weights(actions, steps, observations)
        predictions, prefixes = self.critic.prefixes(
            observations, actions, fields, compact=self.compact
        )
        losses, state, prefix = prefix_value_rows(
            predictions, prefixes, returns, fields, self.settings.prefix_value_weight
        )
        return tuple((loss * weights).sum() / mass for loss in (losses, state, prefix))  # type: ignore[return-value]

    def divergence(
        self,
        observations: Tensor,
        steps: Tensor,
        actions: Tensor,
        behavior: Tensor,
        weights: Tensor,
        mass: Tensor,
        temperature: float,
    ) -> Tensor:
        """Recheck the full logical minibatch after the guarded optimizer step."""
        _, kl = self.actor(
            observations,
            steps,
            actions,
            behavior,
            torch.zeros_like(behavior),
            weights,
            mass,
            temperature,
        )
        return kl
