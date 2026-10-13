"""Check fixed-shape padding without duplicating an observed PPO transition."""

from types import SimpleNamespace
from typing import cast

import torch

from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.sequences.tape import SequenceTape
from kagg_revue.policy.memory.policy import MemoryPolicy


def test_padded_trajectory_and_time_boundaries() -> None:
    """Both padded seats and padded future turns must have exactly zero loss mass."""
    clocks = torch.arange(5)[:, None].expand(-1, 3)
    seats = torch.arange(3)[None].expand(5, -1)

    def weights(
        actions: torch.Tensor, steps: torch.Tensor, observations: torch.Tensor
    ) -> torch.Tensor:
        assert int(steps.max()) < 5
        return torch.ones_like(actions)

    rollout = cast(
        Rollout,
        SimpleNamespace(
            steps=clocks.flatten(),
            observations=torch.stack((clocks, seats), -1).flatten(0, 1),
            actions=torch.zeros(15, 1),
            log_probabilities=torch.zeros(15, 1),
            returns=torch.ones(15),
            weights=torch.ones(15),
        ),
    )
    policy = cast(
        MemoryPolicy,
        SimpleNamespace(
            layout=SimpleNamespace(observation=SimpleNamespace(turns=5)),
            field_weights=weights,
        ),
    )
    tape = SequenceTape(rollout, policy, chunk_turns=3)
    seen: list[tuple[int, ...]] = []
    for indices in tape.batches(2):
        mass = 0.0
        for chunk in tape.chunks(indices):
            assert chunk.observations.shape == (3, 2, 2)
            mass += float(chunk.weights.sum())
            seen.extend(map(tuple, chunk.observations[chunk.weights > 0].tolist()))
        assert mass == float(tape.mass(indices))
    assert sorted(seen) == [(turn, seat) for turn in range(5) for seat in range(3)]
