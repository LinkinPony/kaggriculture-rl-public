"""Remove only past-turn context while retaining every learned computation."""

import torch
from torch import Tensor, nn

from kagg_revue.evaluation.neural import PairedPolicy
from kagg_revue.policy.memory.policy import MemoryPolicy, RecurrentExecution
from kagg_revue.policy.spatial.model import Policy


class HistoryPolicy(Policy):
    """Use one frozen actor with a graph-safe switch for clearing its history."""

    history_enabled: Tensor

    def __init__(self, actor: MemoryPolicy, count: int, dtype: torch.dtype = torch.float32) -> None:
        """Keep learned tensors shared; own only this batch's transient memory."""
        nn.Module.__init__(self)
        self.actor = actor
        self.layout = actor.layout
        device = next(actor.parameters()).device
        self.execution = RecurrentExecution(actor, count, device, dtype)
        self.register_buffer("history_enabled", torch.tensor(True, device=device), persistent=False)

    def reset_memory(self) -> None:
        """Erase all episode context before a new batch."""
        self.execution.reset()

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Optionally clear all cached turns immediately before the normal forward pass."""
        disabled = ~self.history_enabled
        state = self.execution.state
        for value in (*state.keys, *state.values):
            value.masked_fill_(disabled, 0)
        state.turns.masked_fill_(disabled, -1)
        return self.execution.act(observations, steps, sample=sample, temperature=temperature)


class HistoryDuel(PairedPolicy):
    """Give each seat an isolated cache while using exactly the same actor weights."""

    def __init__(self, actor: MemoryPolicy, count: int, dtype: torch.dtype) -> None:
        """Alternate full-history seats across common-seed mirror games."""
        full, reset = HistoryPolicy(actor, count, dtype), HistoryPolicy(actor, count, dtype)
        reset.history_enabled.fill_(False)
        super().__init__(full, reset, count)

    def reset_memory(self) -> None:
        """Reset both wrappers, whose states deliberately live outside actor parameters."""
        assert isinstance(self.learner, HistoryPolicy)
        assert isinstance(self.opponent, HistoryPolicy)
        self.learner.reset_memory()
        self.opponent.reset_memory()
