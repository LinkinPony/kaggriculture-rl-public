"""Portable recurrent actor with explicit, independently owned episode buffers."""

import torch
from torch import Tensor, nn

from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.memory.temporal import InferenceState


def empty_inputs(policy: MemoryPolicy) -> tuple[Tensor, Tensor, Tensor]:
    """Allocate batch-one FP32 caches in the serialized actor's tensor-only ABI."""
    state = policy.memory.temporal.inference_empty(1, torch.device("cpu"))
    return torch.stack(state.keys), torch.stack(state.values), state.turns


class RecurrentActor(nn.Module):
    """Return the selected program and updated caches without mutating shared model state."""

    def __init__(self, policy: MemoryPolicy, temperature: float) -> None:
        """Preserve the trained temporal attention and requested conditional sampling."""
        super().__init__()
        self.policy = policy
        self.temperature = temperature

    def forward(
        self, observations: Tensor, steps: Tensor, keys: Tensor, values: Tensor, turns: Tensor
    ) -> tuple[Tensor, Tensor, Tensor, Tensor]:
        """Advance one observation using only the supplied seat's causal memory."""
        state = InferenceState(tuple(keys.unbind(0)), tuple(values.unbind(0)), turns)
        actions, _, following = self.policy.step(
            observations,
            steps,
            state,
            sample=self.temperature > 0,
            temperature=self.temperature if self.temperature > 0 else 1.0,
        )
        return actions, torch.stack(following.keys), torch.stack(following.values), following.turns
