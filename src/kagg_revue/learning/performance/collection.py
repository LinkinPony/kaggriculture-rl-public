"""Profile real mixed rollouts against fixed archived opponent draws."""

import json
import os
import time
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.archive import PopulationCache
from kagg_revue.learning.collection.matched import MatchedCollection
from kagg_revue.learning.collection.sampling import collect
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import seed_shard
from kagg_revue.learning.matchmaking.scheduler import Match
from kagg_revue.learning.state import member_path
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.memory.compilation import compile_actor
from kagg_revue.policy.memory.policy import MemoryPolicy


class TimedCache(PopulationCache):
    """Separate checkpoint authentication and deserialization from graph/weight updates."""

    payload_seconds: float = 0.0

    def _payload(self, name: str) -> dict[str, Any]:
        started = time.perf_counter()
        result = super()._payload(name)
        self.payload_seconds += time.perf_counter() - started
        return result


@hydra.main(version_base=None, config_path="../../../../configs", config_name="collection_profile")
def main(configuration: DictConfig) -> None:
    """Keep game counts, real policies, opponent choices and complete episodes fixed."""
    options = configuration.benchmark
    run = Path(options.run)
    state = json.loads((run / "state.json").read_text())
    config = Experiment.model_validate(state["protocol"])
    rank, world = int(options.rank), len(config.execution.devices) if config.execution else 1
    cpus = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, cpus[rank * len(cpus) // world : (rank + 1) * len(cpus) // world])
    torch.set_num_threads(2)
    torch.cuda.set_device(rank)
    torch.manual_seed(config.seed + rank * 1000000007)
    settings = runtime_settings(config).model_copy(update={"workers": int(options.workers)})
    device = torch.device(f"cuda:{rank}")
    actor, _ = load_policy(member_path(config, state, state["rl_initial"]), device)
    assert isinstance(actor, MemoryPolicy)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    learner = None
    if options.optimization_sizes:
        from kagg_revue.learning.sequences.critic import MemoryCritic
        from kagg_revue.learning.sequences.learner import SequenceLearner

        learner = SequenceLearner(settings, actor, MemoryCritic(actor.layout).to(device))
    else:
        compile_actor(actor)
    collection = MatchedCollection(config, settings, state, actor)
    cache = TimedCache(config, state)
    collection.cache = cache
    results = []
    for index, update in enumerate(options.updates):
        workers = options.worker_counts[index] if options.worker_counts else options.workers
        collection.settings = settings.model_copy(update={"workers": int(workers)})
        row = state["records"][int(update) - 1]
        counts = row["pfsp"]["population_games"]
        scripts = tuple(
            (name, count // world)
            for name, count in counts.items()
            if name not in {"self_play", "historical_self_play"}
        )
        match = Match(row["opponent"]["path"], scripts, row["pfsp"])
        cache.payload_seconds = 0.0
        graphs = len(cache.runtimes)
        learner_graphs = len(collection.runtimes)
        started = time.perf_counter()
        active, runtime, history, _, _ = collection.resolve(match, int(update), world)
        torch.cuda.synchronize(device)
        resolve_seconds = time.perf_counter() - started
        seeds = seed_shard(
            config,
            int(update),
            rank,
            world,
            counts=(counts["historical_self_play"], sum(count for _, count in scripts) * world),
        )
        rollout_started_at = time.time()
        rollout = collect(active, actor, runtime, seeds, history)
        result = {
            "update": int(update),
            "rank": rank,
            "workers": active.workers,
            "script": scripts,
            "opponent": row["opponent"],
            "resolve_seconds": resolve_seconds,
            "payload_seconds": cache.payload_seconds,
            "new_history_graph": len(cache.runtimes) != graphs,
            "new_learner_graph": len(collection.runtimes) != learner_graphs,
            "history_graphs": len(cache.runtimes),
            "rollout": rollout.timing,
            "rollout_started_at": rollout_started_at,
            "rollout_finished_at": time.time(),
            "total_seconds": time.perf_counter() - started,
            "physical_games": len(seeds),
            "cash": rollout.cash.tolist(),
        }
        results.append(result)
        display = {key: value for key, value in result.items() if key != "cash"}
        print(json.dumps(display), flush=True)
        if learner is not None:
            from kagg_revue.learning.performance.sequences import benchmark

            result["optimization_trials"] = benchmark(
                learner, rollout, list(options.optimization_sizes), int(options.optimizer_repeats)
            )
        write_json(
            Path(options.report),
            {
                "configuration": OmegaConf.to_container(options, resolve=True),
                "wait_policy": os.environ.get("OMP_WAIT_POLICY"),
                "results": results,
            },
        )
        del rollout


if __name__ == "__main__":
    main()
