"""Conditional categorical exploration confined to random trajectory windows."""

import torch
from torch import Tensor

from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.model import sample_categorical
from kagg_revue.policy.spatial.work import WorkPolicy


class SearchPolicy(WorkPolicy):
    """Keep the original decoder and legality masks; vary only selection in search."""

    starts: Tensor
    ends: Tensor
    search_temperature: Tensor

    def __init__(self, layout: ContractLayout, count: int) -> None:
        """Allocate fixed-address controls which remain outside saved neural weights."""
        super().__init__(layout)
        self.register_buffer("starts", torch.zeros(count, dtype=torch.long), persistent=False)
        self.register_buffer("ends", torch.zeros(count, dtype=torch.long), persistent=False)
        self.register_buffer("search_temperature", torch.ones(()), persistent=False)
        self.active_search = torch.zeros(count, dtype=torch.bool)

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Condition later fields on the actually chosen exploratory prefix."""
        self.active_search = (steps >= self.starts) & (steps < self.ends)
        return super().act(observations, steps, sample=sample, temperature=temperature)

    def choose(
        self, scores: Tensor, teacher: Tensor | None, sample: bool, temperature: float | Tensor
    ) -> Tensor:
        """Sample selected lanes and use argmax for every frozen continuation lane."""
        if teacher is not None:
            return teacher
        sampled = sample_categorical(scores / self.search_temperature, 1.0)
        mask = self.active_search.reshape((-1,) + (1,) * (scores.ndim - 2))
        return torch.where(mask, sampled, scores.argmax(-1))
