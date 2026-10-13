"""Reactive paired matches between independently frozen neural policies."""

from typing import Any

import numpy as np
import torch
from torch import Tensor, nn

from kagg_revue.evaluation.games import _complete, _summary
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.native.batches import create_selfplay_batch
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.memory.policy import MemoryPolicy, RecurrentExecution
from kagg_revue.policy.spatial.model import Policy


class PairedPolicy(Policy):
    """Give each network only its own actor-safe native observations."""

    learner_rows: Tensor
    opponent_rows: Tensor

    def __init__(
        self,
        learner: Policy,
        opponent: Policy,
        games: int,
        *,
        learner_temperature: float | None = None,
        opponent_temperature: float | None = None,
    ) -> None:
        """Assign both seats on repeated seeds without changing either neural policy."""
        nn.Module.__init__(self)
        if not learner.layout.same_interface(opponent.layout):
            raise ValueError("paired actors must share the observation and action ABI")
        self.layout = learner.layout
        self.learner, self.opponent = learner, opponent
        self.learner_temperature = learner_temperature
        self.opponent_temperature = opponent_temperature
        device = next(learner.parameters()).device
        self.left_memory = (
            RecurrentExecution(learner, games, device)
            if isinstance(learner, MemoryPolicy)
            else None
        )
        self.right_memory = (
            RecurrentExecution(opponent, games, device)
            if isinstance(opponent, MemoryPolicy)
            else None
        )
        device = next(learner.parameters()).device
        indices = torch.arange(games, device=device)
        self.register_buffer("learner_rows", 2 * indices + indices % 2, persistent=False)
        self.register_buffer("opponent_rows", 2 * indices + 1 - indices % 2, persistent=False)

    def reset_memory(self) -> None:
        """Clear each independent seat history before a paired episode batch."""
        for memory in (self.left_memory, self.right_memory):
            if memory is not None:
                memory.reset()

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Decode both complete programs in one captured neural/native handshake."""
        left_act = self.left_memory.act if self.left_memory is not None else self.learner.act
        right_act = self.right_memory.act if self.right_memory is not None else self.opponent.act
        left, left_probabilities = left_act(
            observations[self.learner_rows],
            steps[self.learner_rows],
            sample=sample and self.learner_temperature != 0,
            temperature=(
                temperature if self.learner_temperature is None else self.learner_temperature or 1.0
            ),
        )
        right, right_probabilities = right_act(
            observations[self.opponent_rows],
            steps[self.opponent_rows],
            sample=sample and self.opponent_temperature != 0,
            temperature=(
                temperature
                if self.opponent_temperature is None
                else self.opponent_temperature or 1.0
            ),
        )
        actions = torch.empty(
            (len(observations), self.layout.factors), device=left.device, dtype=left.dtype
        )
        probabilities = torch.empty_like(actions, dtype=torch.float32)
        actions[self.learner_rows], actions[self.opponent_rows] = left, right
        probabilities[self.learner_rows], probabilities[self.opponent_rows] = (
            left_probabilities,
            right_probabilities,
        )
        return actions, probabilities


class NeuralMatches:
    """Reuse one fixed graph while candidate parameter values change between panels."""

    def __init__(
        self,
        settings: RuntimeSettings,
        learner: Policy,
        opponent: Policy,
        *,
        sample: bool = False,
        learner_temperature: float | None = None,
        opponent_temperature: float | None = None,
    ) -> None:
        """Retain the same full-game count and the original models' numerical semantics."""
        self.settings = settings
        self.policy = PairedPolicy(
            learner,
            opponent,
            settings.evaluation_games,
            learner_temperature=learner_temperature,
            opponent_temperature=opponent_temperature,
        )
        self.runtime = ActorRuntime(
            self.policy,
            settings.evaluation_games * 2,
            sample=sample,
            temperature=settings.ppo.temperature,
            precision=settings.precision,
            bf16_reduced_precision_reduction=settings.bf16_reduced_precision_reduction,
        )

    def run(self, seed: int) -> dict[str, Any]:
        """Return learner-first direct WDL for complete common-seed seat pairs."""
        p, runtime = self.settings, self.runtime
        seeds = [seed + index // 2 for index in range(p.evaluation_games)]
        batch = create_selfplay_batch(p, seeds)
        cash, timing = _complete(p, runtime, batch, selfplay=True)
        seats = np.arange(len(seeds)) % 2
        cash = np.where(seats[:, None] == 0, cash, cash[:, ::-1])
        result = _summary(
            cash,
            [(game_seed, int(seats[i]), "frozen_neural") for i, game_seed in enumerate(seeds)],
            timing,
        )
        result.update(sample=runtime.sample)
        return result
