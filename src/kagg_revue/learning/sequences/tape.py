"""Time-major views and episode-preserving minibatches for recurrent PPO."""

from collections.abc import Iterator
from dataclasses import dataclass

import torch
from torch import Tensor

from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.policy.memory.policy import MemoryPolicy


@dataclass
class Chunk:
    """One contiguous segment, carrying its immutable behavior likelihoods."""

    observations: Tensor
    actions: Tensor
    behavior: Tensor
    returns: Tensor
    weights: Tensor
    steps: Tensor
    fields: Tensor
    section: slice


class SequenceTape:
    """Keep seat identity constant across all chunks of a complete episode."""

    def __init__(self, rollout: Rollout, policy: MemoryPolicy, chunk_turns: int) -> None:
        """Reject truncated starts rather than constructing an invented empty memory."""
        turns = policy.layout.observation.turns
        rows = len(rollout.steps)
        if rows % turns:
            raise ValueError("recurrent PPO requires complete trajectories")
        self.count = rows // turns
        expected = torch.arange(turns, device=rollout.steps.device)[:, None].expand(-1, self.count)
        if not torch.equal(rollout.steps.reshape(turns, self.count), expected):
            raise ValueError("rollout clocks differ from complete time-major episodes")
        self.turns, self.chunk_turns, self.policy = turns, chunk_turns, policy
        self.observations = rollout.observations.reshape(turns, self.count, -1)
        self.actions = rollout.actions.long().reshape(turns, self.count, -1)
        self.behavior = rollout.log_probabilities.reshape(turns, self.count, -1)
        self.returns = rollout.returns.reshape(turns, self.count)
        self.weights = rollout.weights.reshape(turns, self.count)
        self.device = rollout.steps.device
        self.fields = policy.field_weights(
            self.actions.flatten(0, 1), rollout.steps, rollout.observations
        ).reshape_as(self.actions)

    def batches(self, size: int, *, shuffle: bool = False) -> Iterator[Tensor]:
        """Keep one static batch shape; -1 denotes a loss-free duplicate trajectory."""
        ordering = (
            torch.randperm(self.count, device=self.device)
            if shuffle
            else torch.arange(self.count, device=self.device)
        )
        for indices in torch.split(ordering, size):
            yield torch.cat((indices, indices.new_full((size - len(indices),), -1)))

    def mass(self, indices: Tensor) -> Tensor:
        """Exclude padded seats from minibatch normalization."""
        return (self.weights[:, indices.clamp_min(0)] * (indices >= 0)[None]).sum()

    def select(self, values: Tensor, section: slice, indices: Tensor) -> Tensor:
        """Pad the final time segment; later causal queries cannot alter real outputs."""
        result = values[section][:, indices.clamp_min(0)]
        missing = self.chunk_turns - len(result)
        if missing:
            result = torch.cat((result, result[-1:].expand(missing, *result.shape[1:])))
        return result

    def chunks(self, indices: Tensor) -> Iterator[Chunk]:
        """Never shuffle time, omit a context frame, or switch seats inside a sequence."""
        for start in range(0, self.turns, self.chunk_turns):
            stop = min(start + self.chunk_turns, self.turns)
            section = slice(start, stop)
            observations = self.select(self.observations, section, indices)
            actions = self.select(self.actions, section, indices).long()
            steps = torch.arange(start, start + self.chunk_turns, device=self.device)
            weights = self.select(self.weights, section, indices)
            weights = weights * ((steps < stop)[:, None] & (indices >= 0)[None])
            fields = self.select(self.fields, section, indices)
            yield Chunk(
                observations,
                actions,
                self.select(self.behavior, section, indices),
                self.select(self.returns, section, indices),
                weights,
                steps,
                fields,
                section,
            )
