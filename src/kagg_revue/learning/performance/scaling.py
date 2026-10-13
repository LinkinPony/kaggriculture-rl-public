"""Measure architecture ablations on complete native games without changing a run."""

import copy
import json
import os
import time
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.matched import MatchedCollection
from kagg_revue.learning.collection.pipeline import PipelineCollection
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.learning.matchmaking.scheduler import Match
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.learning.performance.peers import create_peer
from kagg_revue.learning.performance.stateless import profile_microbatch
from kagg_revue.learning.performance.telemetry import GpuTelemetry
from kagg_revue.learning.sequences.critic import MemoryCritic
from kagg_revue.learning.sequences.learner import SequenceLearner
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.memory.policy import MemoryPolicy


def _restore(module: torch.nn.Module, weights: dict[str, torch.Tensor]) -> None:
    """Reuse checkpoint weights for memory-only changes, keeping new position buffers."""
    state = module.state_dict()
    for name, value in state.items():
        if name.endswith(".relative"):
            continue
        if name not in weights or value.shape != weights[name].shape:
            raise ValueError(f"checkpoint does not support this architecture: {name}")
        state[name] = weights[name]
    module.load_state_dict(state)


def benchmark(options: dict[str, Any], telemetry: GpuTelemetry) -> None:
    """Separate cold compilation from repeated complete collection and PPO updates."""
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise ValueError("these experiments must be launched with CUDA_VISIBLE_DEVICES=1")
    torch.set_num_threads(2)
    torch.cuda.set_device(0)
    device = torch.device("cuda:0")
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    state = json.loads(Path(options["state"]).read_text())
    output = Path(options["output"])
    execution = {**state["protocol"]["execution"], "devices": ["cuda:0"]}
    changes = options.get("changes", {})
    execution.update(options.get("execution", {}))
    protocol = {
        **state["protocol"],
        "execution": execution,
        "demonstrations": None,
        "cash_weight": 0.0,
        "cash_margin": None,
        "updates": 1,
        **changes,
    }
    fraction = float(options.get("history_fraction", 0.7))
    games = int(protocol["games"])
    block = 4 if options.get("same_model_history") else 2
    history_games = 0 if options.get("selfplay") else block * round(games * fraction / block)
    if options.get("selfplay"):
        protocol.update(population={"fraction": 0.0}, script_population=None)
    elif options.get("same_model_history"):
        protocol.update(population={"fraction": history_games / games}, script_population=None)
    config = Experiment.model_validate(protocol)
    settings = runtime_settings(config)
    torch.manual_seed(config.seed)
    actor = random_policy(ContractLayout.resolve(settings), config.seed, config.exploration).to(
        device
    )
    critic: PrefixCritic = (
        MemoryCritic(actor.layout)
        if isinstance(actor, MemoryPolicy)
        else PrefixCritic(actor.layout)
    ).to(device)
    total_parameters = sum(p.numel() for model in (actor, critic) for p in model.parameters())
    minimum, maximum = options.get("parameters_min"), options.get("parameters_max")
    if (minimum is not None and total_parameters < minimum) or (
        maximum is not None and total_parameters > maximum
    ):
        raise ValueError(
            f"Actor + Critic capacity {total_parameters} violates the requested budget"
        )
    checkpoint = Path(options["checkpoint"])
    if digest(checkpoint) != state["members"][state["latest"]]:
        raise ValueError("benchmark checkpoint differs from the frozen ledger")
    if options["initialization"] == "checkpoint":
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        _restore(actor, payload["model"])
        _restore(critic, payload["critic"])
        del payload
    elif options["initialization"] != "random":
        raise ValueError("initialization must be checkpoint or random")
    actor_start = {key: value.detach().cpu().clone() for key, value in actor.state_dict().items()}
    critic_start = {key: value.detach().cpu().clone() for key, value in critic.state_dict().items()}
    learner: Learner
    if isinstance(actor, MemoryPolicy):
        assert isinstance(critic, MemoryCritic)
        learner = SequenceLearner(settings, actor, critic)
    else:
        learner = Learner(settings, actor, critic, None)
    actor_optimizer = copy.deepcopy(learner.actor_optimizer.state_dict())
    critic_optimizer = copy.deepcopy(learner.critic_optimizer.state_dict())
    collection = MatchedCollection(config, settings, state, actor)
    history_name = None if not history_games else options["history"]
    history_hash = state["members"][history_name] if history_name else None
    if options.get("same_model_history") and history_games:
        collection.cache, history_name, history_hash = create_peer(config, settings, output)
    pipeline = PipelineCollection(config, actor, collection.cache)
    match = Match(
        history_name or "",
        (),
        {"population_games": {"historical_self_play": history_games}},
    )
    active, name, _ = collection.selection(match, state["completed_update"] + 1, 1)
    if options.get("same_model_history"):
        active = active.model_copy(
            update={"ppo": active.ppo.model_copy(update={"concurrent_history_inference": True})}
        )
    seeds = list(range(int(options["seed_start"]), int(options["seed_start"]) + config.games))
    results: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "options": options,
        "resolved_protocol": config.model_dump(mode="json"),
        "physical_gpu": 1,
        "cpu_affinity": sorted(os.sched_getaffinity(0)),
        "benchmark_source_sha256": digest(Path(__file__)),
        "gpu": torch.cuda.get_device_name(device),
        "torch": torch.__version__,
        "checkpoint_sha256": digest(checkpoint),
        "actor_parameters": sum(p.numel() for p in actor.parameters()),
        "critic_parameters": sum(p.numel() for p in critic.parameters()),
        "total_parameters": total_parameters,
        "history": name,
        "history_sha256": history_hash,
        "history_games": history_games,
        "selfplay_games": config.games - history_games,
        "reward": "pure terminal WDL",
        "optimizer_initialization": "fresh Adam state, reset before every repetition",
        "scope": "Full native 719-turn games and real PPO updates; excludes checkpoint IO, "
        "evaluation and opponent switching. Fixed opponent when present, not pool average. "
        "Architecture changes alter trajectories; random policies do not measure skill.",
        "measurements": results,
    }
    write_json(output, report)
    for repeat in range(int(options["repeats"])):
        actor.load_state_dict(actor_start)
        critic.load_state_dict(critic_start)
        learner.restore_optimizers(copy.deepcopy(actor_optimizer), copy.deepcopy(critic_optimizer))
        torch.manual_seed(config.seed)
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
        telemetry.mark(repeat, "prepare")
        started = time.perf_counter()
        groups = pipeline.groups(active, seeds, name)
        torch.cuda.synchronize(device)
        prepared = time.perf_counter()
        telemetry.mark(repeat, "collect")
        rollout = pipeline.collect(active, groups)
        torch.cuda.synchronize(device)
        collected = time.perf_counter()
        telemetry.mark(repeat, "learn")
        optimization = learner.update(rollout)
        torch.cuda.synchronize(device)
        seconds = time.perf_counter() - started
        row = {
            "repeat": repeat,
            "cold": repeat == 0,
            "seconds": seconds,
            "prepare_seconds": prepared - started,
            "collection_seconds": collected - prepared,
            "physical_games_per_second": config.games / seconds,
            "training_rows": len(rollout.steps),
            "collected_rows": len(rollout.steps),
            "optimized_fraction": 1.0,
            "rollout": rollout.timing,
            "optimization": optimization,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "return_values": torch.unique(rollout.returns).tolist(),
            "mean_terminal_cash": float(rollout.cash.mean()),
        }
        if optimization["actor_steps"] == 0 or optimization["actor_early_stop"]:
            row["warning"] = "Incomplete actor work: do not use as a full PPO speedup."
        results.append(row)
        write_json(output, report)
        print(json.dumps(row), flush=True)
        if repeat == int(options["repeats"]) - 1 and options.get("profile"):
            telemetry.mark(repeat, "profile")
            profile_microbatch(learner, rollout, output)
        del rollout, groups


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="learning_scaling_profile"
)
def main(configuration: DictConfig) -> None:
    """Resolve one explicit GPU1 ablation, leaving the production ledger read-only."""
    options = OmegaConf.to_container(configuration.benchmark, resolve=True)
    assert isinstance(options, dict)
    resolved = {str(key): value for key, value in options.items()}
    with GpuTelemetry(Path(resolved["output"]), physical_gpu=1) as telemetry:
        benchmark(resolved, telemetry)


if __name__ == "__main__":
    main()
