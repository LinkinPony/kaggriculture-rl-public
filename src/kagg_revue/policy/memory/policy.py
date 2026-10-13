"""Recurrent grounded actor with an unchanged competition action language."""

import torch
from torch import Tensor

from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.encoder import ContextEncoder
from kagg_revue.policy.grounded.typed import TypedGroundedPolicy
from kagg_revue.policy.memory.scene import SceneMemory
from kagg_revue.policy.memory.temporal import InferenceState, MemoryState
from kagg_revue.policy.spatial.model import log_probabilities


class MemoryPolicy(TypedGroundedPolicy):
    """Expose explicit temporal state for teacher forcing and online inference."""

    def __init__(self, layout: ContractLayout) -> None:
        """Preserve typed heads, quantity conditioning and budget features."""
        super().__init__(layout)
        self.memory = SceneMemory(layout.observation.width, layout.network)

    def sequence(
        self,
        observations: Tensor,
        steps: Tensor,
        state: MemoryState,
        actions: Tensor | None = None,
        *,
        sample: bool = False,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor, MemoryState]:
        """Process contiguous observations without reading future labels or frames."""
        turns, batch = observations.shape[:2]
        flat = observations.flatten(0, 1)
        assert isinstance(self.encoder, ContextEncoder)
        encoded, valid = self.encoder.tokens(flat)
        encoded, next_state = self.memory(
            encoded.reshape(turns, batch, *encoded.shape[1:]),
            valid.reshape(turns, batch, -1),
            state,
            steps,
        )
        selected, logits = self.decode_encoded(
            encoded.flatten(0, 1),
            flat,
            None if actions is None else actions.flatten(0, 1),
            sample,
            temperature,
        )
        return (
            selected.reshape(turns, batch, -1),
            logits.reshape(turns, batch, *logits.shape[1:]),
            next_state,
        )

    def forward(self, observations: Tensor, steps: Tensor, actions: Tensor | None = None) -> Tensor:
        """Reject independent-row scoring that would silently erase temporal context."""
        raise RuntimeError("memory policies require sequence() and explicit causal state")

    def step(
        self,
        observations: Tensor,
        steps: Tensor,
        state: InferenceState,
        *,
        sample: bool,
        temperature: float | Tensor,
    ) -> tuple[Tensor, Tensor, InferenceState]:
        """Sample one turn without reprojecting the previous 384 turns."""
        assert isinstance(self.encoder, ContextEncoder)
        encoded, valid = self.encoder.tokens(observations)
        encoded, next_state = self.memory.step(encoded, valid, state, steps[:1])
        selected, logits = self.decode_encoded(encoded, observations, None, sample, temperature)
        return selected, logits, next_state

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Require a persistent inference runtime rather than a stateless callback."""
        raise RuntimeError("memory policies require ActorRuntime with persistent temporal state")


class RecurrentExecution:
    """Graph-compatible fixed buffers, owned by one episode batch and one policy."""

    def __init__(
        self,
        policy: MemoryPolicy,
        count: int,
        device: torch.device,
        dtype: torch.dtype = torch.float32,
    ) -> None:
        """Allocate memory in a dedicated runtime, never in policy parameters."""
        self.policy = policy
        self.state = policy.memory.temporal.inference_empty(count, device, dtype)

    def reset(self) -> None:
        """Erase all episode state at a game boundary or after graph warmup."""
        for layer in (*self.state.keys, *self.state.values):
            layer.zero_()
        self.state.turns.fill_(-1)

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Update memory once per observation, after computing its action distribution."""
        actions, logits, state = self.policy.step(
            observations,
            steps,
            self.state,
            sample=sample,
            temperature=temperature,
        )
        for buffer, value in zip(
            (*self.state.keys, *self.state.values), (*state.keys, *state.values), strict=True
        ):
            buffer.copy_(value)
        self.state.turns.copy_(state.turns)
        return actions, log_probabilities(logits, actions, temperature)
