"""Compare serial and overlapped collection using identical partitions and random draws."""

import json
import os
import time
from pathlib import Path

import hydra
import numpy as np
import torch
from omegaconf import DictConfig

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.matched import MatchedCollection
from kagg_revue.learning.collection.pipeline import PipelineCollection
from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import seed_shard
from kagg_revue.learning.matchmaking.scheduler import Match
from kagg_revue.learning.state import member_path
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.memory.compilation import compile_actor
from kagg_revue.policy.memory.policy import MemoryPolicy


@hydra.main(version_base=None, config_path="../../../../configs", config_name="pipeline_profile")
def main(configuration: DictConfig) -> None:
    """Use full real games and require bit-exact tapes before reporting a speedup."""
    options = configuration.benchmark
    run = Path(options.run)
    state = json.loads((run / "state.json").read_text())
    config = Experiment.model_validate(state["protocol"])
    assert config.execution is not None
    rank, world = int(options.rank), len(config.execution.devices)
    cpus = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, cpus[rank * len(cpus) // world : (rank + 1) * len(cpus) // world])
    torch.set_num_threads(2)
    device = torch.device(f"cuda:{rank}")
    torch.cuda.set_device(device)
    actor, _ = load_policy(member_path(config, state, state["rl_initial"]), device)
    assert isinstance(actor, MemoryPolicy)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    compile_actor(actor)
    collection = MatchedCollection(config, runtime_settings(config), state, actor)
    pipeline = PipelineCollection(config, actor, collection.cache)
    pipeline.prepare(world)
    results = []
    for update in options.updates:
        row = state["records"][int(update) - 1]
        counts = row["pfsp"]["population_games"]
        scripts = tuple(
            (name, count // world)
            for name, count in counts.items()
            if name not in {"self_play", "historical_self_play"}
        )
        match = Match(row["opponent"]["path"], scripts, row["pfsp"])
        active, name, history = collection.selection(match, int(update), world)
        seeds = seed_shard(
            config,
            int(update),
            rank,
            world,
            counts=(history * world, sum(count for _, count in scripts) * world),
        )
        for repeat in range(int(options.repeats)):
            reference: Rollout | None = None
            for overlap in (False, True):
                groups = pipeline.groups(active, seeds, name)
                torch.manual_seed(config.seed + rank * 1000000007 + repeat)
                started_at = time.time()
                rollout = pipeline.collect(active, groups, overlap=overlap)
                result = {
                    "update": update,
                    "repeat": repeat,
                    "overlap": overlap,
                    "started_at": started_at,
                    "finished_at": time.time(),
                    "rollout": rollout.timing,
                }
                if reference is not None:
                    checks = {
                        key: torch.equal(getattr(reference, key), getattr(rollout, key))
                        for key in (
                            "observations",
                            "actions",
                            "log_probabilities",
                            "steps",
                            "returns",
                            "weights",
                        )
                    }
                    checks["cash"] = np.array_equal(reference.cash, rollout.cash)
                    checks["opponents"] = reference.opponents == rollout.opponents
                    if not all(checks.values()):
                        raise ValueError(
                            f"pipelined collection differs from serial reference: {checks}"
                        )
                    result["exact_serial_equivalence"] = checks
                else:
                    reference = rollout
                results.append(result)
                print(json.dumps(result), flush=True)
                write_json(Path(options.report), {"results": results})


if __name__ == "__main__":
    main()
