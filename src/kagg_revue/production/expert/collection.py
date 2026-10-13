"""Bounded state samples from complete apprentice-controlled native games."""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor

from kagg_revue.learning.collection.population import (
    create_training_batch,
    episode_weights,
    script_games,
)
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.production.config import Settings


@dataclass
class StateTape:
    """Uniform decision samples with equal physical-game mass across both populations."""

    observations: Tensor
    steps: Tensor
    weights: Tensor
    cash: np.ndarray[Any, Any]
    opponents: tuple[str, ...]
    timing: dict[str, float]

    def save(self, path: Path) -> None:
        """Stream one compact array per shard; teacher identity lives in the update manifest."""
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            observations=self.observations.cpu().numpy(),
            steps=self.steps.short().cpu().numpy(),
            weights=self.weights.half().cpu().numpy(),
        )


def collect_states(
    settings: Settings, runtime: ActorRuntime, seeds: list[int], samples: int
) -> StateTape:
    """Keep rules and encoding native, inference graphed, and state selection on device."""
    started = time.perf_counter()
    device, layout = runtime.device, runtime.policy.layout
    games = len(seeds)
    scripts = script_games(settings, games)
    selfplay = games - scripts
    count = selfplay * 2 + scripts
    batch = create_training_batch(settings, seeds)
    # Independent uniform subsets of decisions, selected before any game outcomes.
    times = torch.rand(layout.decisions, count, device=device).argsort(0)[:samples].sort(0).values
    slots = torch.full((layout.decisions, count), -1, device=device, dtype=torch.long)
    slots.scatter_(0, times, torch.arange(samples, device=device)[:, None].expand_as(times))
    observations = torch.zeros(
        (samples, count, layout.observation.features), device=device, dtype=torch.float16
    )
    lanes = torch.arange(count, device=device)
    encoding = inference = native = 0.0
    for decision, span in enumerate(layout.spans):
        phase = time.perf_counter()
        batch.observe_into(runtime.host.numpy())
        encoding += time.perf_counter() - phase
        phase = time.perf_counter()
        runtime.act(decision)
        slot = slots[decision].clamp_min(0)
        observations[slot, lanes] = torch.where(
            (slots[decision] >= 0)[:, None], runtime.observations, observations[slot, lanes]
        )
        inference += time.perf_counter() - phase
        phase = time.perf_counter()
        batch.advance(runtime.selected.numpy(), span)
        native += time.perf_counter() - phase
    torch.cuda.synchronize(device)
    return StateTape(
        observations.flatten(0, 1),
        times.flatten(),
        torch.tensor(episode_weights(selfplay, scripts), device=device).repeat(samples),
        batch.cash(settings.turns),
        batch.opponents,
        {
            "rollout_seconds": time.perf_counter() - started,
            "encoding_seconds": encoding,
            "inference_seconds": inference,
            "native_seconds": native,
            "collation_seconds": 0.0,
        },
    )
