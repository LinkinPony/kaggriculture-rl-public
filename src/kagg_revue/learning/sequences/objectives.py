"""Bounded fused reductions over recurrent policy and value outputs."""

import torch
from torch import Tensor
from torch.nn import functional as F

from kagg_revue.learning.optimization.prefix import prefix_surrogate, prefix_value_rows
from kagg_revue.learning.optimization.settings import OptimizationSettings
from kagg_revue.policy.compilation import options as compilation_options
from kagg_revue.policy.spatial.model import log_probabilities, scale_logits


class SequenceObjectives:
    """Keep the established losses while avoiding repeated probability materialization."""

    def __init__(self, settings: OptimizationSettings, compile: bool, device: torch.device) -> None:
        """Compile loss reductions independently of the bounded network components."""
        self.settings = settings
        if compile:
            for name in ("actor", "value", "divergence"):
                setattr(
                    self,
                    name,
                    torch.compile(
                        getattr(self, name),
                        fullgraph=True,
                        dynamic=False,
                        options=compilation_options(device),
                    ),
                )

    def actor(
        self,
        logits: Tensor,
        actions: Tensor,
        behavior: Tensor,
        credit: Tensor,
        fields: Tensor,
        weights: Tensor,
        mass: Tensor,
        temperature: float,
    ) -> tuple[Tensor, Tensor]:
        """Fuse likelihood, conditional PPO, entropy and weighted reductions."""
        logits = scale_logits(logits, temperature)
        distribution = F.log_softmax(logits, -1)
        likelihood = distribution.gather(-1, actions[..., None]).squeeze(-1)
        gain, kl = prefix_surrogate(likelihood - behavior, fields, credit, self.settings.clip)
        entropy = -(F.softmax(logits, -1) * distribution).sum(-1)
        loss = (
            (-gain - self.settings.entropy_weight * (entropy * fields).sum(-1)) * weights
        ).sum() / mass
        return loss, (kl * weights).sum() / mass

    def anchor(
        self,
        logits: Tensor,
        reference_logits: Tensor,
        fields: Tensor,
        weights: Tensor,
        mass: Tensor,
        temperature: float,
    ) -> Tensor:
        """Exact per-field KL(policy || reference) under the same teacher-forced prefix."""
        current = F.log_softmax(scale_logits(logits.float(), temperature), -1)
        reference = F.log_softmax(scale_logits(reference_logits.float(), temperature), -1)
        terms = torch.where(current > -1e30, current.exp() * (current - reference), 0.0)
        return (((terms.sum(-1) * fields).sum(-1)) * weights).sum() / mass

    def value(
        self,
        values: Tensor,
        prefixes: Tensor,
        returns: Tensor,
        fields: Tensor,
        weights: Tensor,
        mass: Tensor,
    ) -> Tensor:
        """Reduce state and exclusive-prefix errors without changing their weights."""
        losses = prefix_value_rows(
            values, prefixes, returns, fields, self.settings.prefix_value_weight
        )
        return torch.stack([(loss * weights).sum() / mass for loss in losses])

    def divergence(
        self,
        logits: Tensor,
        actions: Tensor,
        behavior: Tensor,
        fields: Tensor,
        weights: Tensor,
        mass: Tensor,
        temperature: float,
    ) -> Tensor:
        """Evaluate the unchanged conditional KL estimator after a candidate step."""
        difference = log_probabilities(logits, actions, temperature) - behavior
        _, kl = prefix_surrogate(
            difference, fields, torch.zeros_like(difference), self.settings.clip
        )
        return (kl * weights).sum() / mass
