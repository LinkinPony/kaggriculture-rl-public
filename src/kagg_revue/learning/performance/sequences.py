"""Measure full-trajectory optimization with fixed initial parameters and RNG."""

import copy
import time
from typing import Any

import torch

from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.sequences.learner import SequenceLearner


def benchmark(
    learner: SequenceLearner, rollout: Rollout, sizes: list[int], repeats: int
) -> list[dict[str, Any]]:
    """Keep the real behavior tape and optimizer start identical for each batch size."""
    actor = copy.deepcopy(learner.actor.state_dict())
    critic = copy.deepcopy(learner.sequence_critic.state_dict())
    cpu_rng = torch.get_rng_state()
    cuda_rng = torch.cuda.get_rng_state(learner.device)
    results = []
    for size in sizes:
        learner.episodes = size
        torch.cuda.empty_cache()
        for repeat in range(repeats):
            learner.actor.load_state_dict(actor)
            learner.sequence_critic.load_state_dict(critic)
            learner.actor_optimizer.state.clear()
            learner.critic_optimizer.state.clear()
            torch.set_rng_state(cpu_rng)
            torch.cuda.set_rng_state(cuda_rng, learner.device)
            torch.cuda.synchronize(learner.device)
            torch.cuda.reset_peak_memory_stats(learner.device)
            started = time.perf_counter()
            started_at = time.time()
            result = learner.update(rollout)
            torch.cuda.synchronize(learner.device)
            record = {
                "trajectories": size,
                "repeat": repeat,
                "wall_seconds": time.perf_counter() - started,
                "started_at": started_at,
                "finished_at": time.time(),
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(learner.device),
                "optimization": result,
            }
            results.append(record)
            print(record, flush=True)
    return results
