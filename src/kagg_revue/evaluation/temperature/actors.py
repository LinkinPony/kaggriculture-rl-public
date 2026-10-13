"""Export a greedy evaluation control using the standard portable CPU exporter."""

from torch import Tensor, nn

from kagg_revue.policy.spatial.model import Policy


class GreedyPolicy(Policy):
    """Override only sampling, retaining all learned causal decoder conditioning."""

    def __init__(self, policy: Policy) -> None:
        """Wrap an independently loaded frozen checkpoint."""
        nn.Module.__init__(self)
        self.policy = policy
        self.layout = policy.layout

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Select each conditional maximum without consuming sampling randomness."""
        return self.policy.act(observations, steps, sample=False)
