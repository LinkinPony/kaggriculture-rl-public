"""Measure native-script changes with the real frozen learner and rollout pipeline."""

import gc
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.matched import MatchedCollection
from kagg_revue.learning.collection.pipeline import PipelineCollection
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import seed_shard
from kagg_revue.learning.matchmaking.scheduler import Match
from kagg_revue.native import _revue_native
from kagg_revue.policy.checkpoints import load_policy


class Benchmark(FrozenSettings):
    """Freeze inputs independently of the training process's advancing checkpoint."""

    state: Path
    checkpoint: Path
    opponents: tuple[str, ...]
    report: Path
    rank: int = Field(default=0, ge=0)
    update: int = Field(default=157, ge=1)
    repeats: int = Field(default=2, ge=2)
    memory_fraction: float = Field(default=0.30, gt=0, le=1)
    save_likelihoods: bool = False


def fingerprint(value: torch.Tensor) -> str:
    """Hash complete tapes in bounded chunks without a second full host copy."""
    result = hashlib.sha256()
    for start in range(0, len(value), 8192):
        chunk = value[start : start + 8192]
        result.update(chunk.detach().cpu().contiguous().numpy().tobytes())
    return result.hexdigest()


def benchmark(options: Benchmark) -> dict[str, Any]:
    """Keep neural RNG, physical games, partitions, weights and opponent identity fixed."""
    state = json.loads(options.state.read_text())
    config = Experiment.model_validate(state["protocol"])
    assert config.execution is not None and config.script_population is not None
    world = len(config.execution.devices)
    if options.rank >= world or not set(options.opponents) <= set(config.script_population.agents):
        raise ValueError("benchmark must use the archived rank and registered script opponents")
    cpus = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(
        0, cpus[options.rank * len(cpus) // world : (options.rank + 1) * len(cpus) // world]
    )
    torch.set_num_threads(config.execution.cpu_threads_per_rank)
    device = torch.device(config.execution.devices[options.rank])
    torch.cuda.set_device(device)
    torch.cuda.set_per_process_memory_fraction(options.memory_fraction, device)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    actor, payload = load_policy(options.checkpoint, device)
    del payload
    actor.eval()
    if config.memory_turns:
        from kagg_revue.policy.memory.compilation import compile_actor

        compile_actor(actor)  # type: ignore[arg-type]
    collection = MatchedCollection(config, runtime_settings(config), state, actor)
    pipeline = PipelineCollection(config, actor, collection.cache)
    pooled = int(config.games * config.population.fraction)
    if pooled % (2 * world):
        raise ValueError("this benchmark requires a fixed, seat-balanced script count")
    panels: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "complete": False,
        "configuration": options.model_dump(mode="json"),
        "checkpoint_sha256": digest(options.checkpoint),
        "binary_sha256": digest(Path(_revue_native.__file__)),
        "scope": "one real training rank, full pipeline rollout; excludes optimizer and setup",
        "panels": panels,
    }
    with torch.inference_mode():
        for name in options.opponents:
            match = Match(
                "",
                ((name, pooled // world),),
                {"population_games": {"self_play": config.games - pooled, name: pooled}},
            )
            active, history_name, history = collection.selection(match, options.update, world)
            assert history == 0 and history_name is None
            seeds = seed_shard(config, options.update, options.rank, world, counts=(0, pooled))
            reference = None
            for repeat in range(options.repeats):
                groups = pipeline.groups(active, seeds, None)
                torch.manual_seed(config.seed + options.rank * 1000000007 + options.update)
                rollout = pipeline.collect(active, groups)
                tapes = {
                    key: fingerprint(getattr(rollout, key))
                    for key in (
                        "observations",
                        "actions",
                        "log_probabilities",
                        "returns",
                        "weights",
                    )
                }
                tapes["cash"] = hashlib.sha256(rollout.cash.tobytes()).hexdigest()
                if reference is not None and tapes != reference:
                    raise ValueError("identical learner RNG and games produced different tapes")
                reference = tapes
                row = {
                    "opponent": name,
                    "repeat": repeat,
                    "physical_games": len(seeds),
                    "script_games": pooled // world,
                    "timing": rollout.timing,
                    "tapes": tapes,
                    "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
                }
                if options.save_likelihoods and repeat == 0:
                    destination = options.report.with_suffix("") / f"{name}-likelihoods.pt"
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    torch.save(rollout.log_probabilities.cpu(), destination)
                    row["likelihoods"] = str(destination)
                panels.append(row)
                write_json(options.report, report)
                print(json.dumps(row), flush=True)
                del rollout, groups
                gc.collect()
    report["complete"] = True
    write_json(options.report, report)
    return report


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="script_pipeline_profile"
)
def main(configuration: DictConfig) -> None:
    """Run an isolated, reproducible performance panel without modifying the learner."""
    options = Benchmark.model_validate(
        OmegaConf.to_container(configuration.benchmark, resolve=True)
    )
    benchmark(options)


if __name__ == "__main__":
    main()
