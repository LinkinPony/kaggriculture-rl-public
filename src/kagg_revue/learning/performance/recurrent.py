"""Fixed-checkpoint measurements of the actual mixed recurrent PPO pipeline."""

import copy
import json
import time
from dataclasses import fields
from pathlib import Path
from typing import Any, cast

import hydra
import torch
import torch._inductor.config as compiler
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.matched import MatchedCollection
from kagg_revue.learning.collection.pipeline import PipelineCollection
from kagg_revue.learning.collection.population import script_games
from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import restore_rng, seed_shard
from kagg_revue.learning.matchmaking.scheduler import Matchmaker
from kagg_revue.learning.sequences.critic import MemoryCritic
from kagg_revue.learning.sequences.learner import SequenceLearner
from kagg_revue.learning.sequences.tape import SequenceTape
from kagg_revue.policy.memory.policy import MemoryPolicy


def _copy_rollout(rollout: Rollout, device: torch.device) -> Rollout:
    values: dict[str, Any] = {
        field.name: value.to(device) if isinstance(value, torch.Tensor) else value
        for field in fields(rollout)
        for value in [getattr(rollout, field.name)]
    }
    return Rollout(**values)


def _profile(learner: SequenceLearner, rollout: Rollout, output: Path) -> None:
    """Profile one full-sized middle-of-episode segment after compiler warmup."""
    tape = SequenceTape(rollout, learner.actor, learner.settings.sequence_chunk_turns)
    indices = next(tape.batches(learner.episodes))
    actor_state = learner.actor.memory.temporal.empty(len(indices), learner.device)
    critic_state = learner.sequence_critic.memory.temporal.empty(len(indices), learner.device)
    chunks = iter(tape.chunks(indices))
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
        for _ in range(8):
            chunk = next(chunks)
            _, _, actor_state = learner.actor_sequence(
                chunk.observations, chunk.steps, actor_state, chunk.actions
            )
            _, _, critic_state = learner.critic_sequence(
                chunk.observations, chunk.steps, critic_state, chunk.actions, chunk.fields
            )
    chunk = next(chunks)
    mass = tape.mass(indices)

    def operation() -> None:
        learner.actor_optimizer.zero_grad(set_to_none=True)
        learner.critic_optimizer.zero_grad(set_to_none=True)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            with torch.profiler.record_function("actor_sequence"):
                _, logits, _ = learner.actor_sequence(
                    chunk.observations, chunk.steps, actor_state, chunk.actions
                )
            with torch.profiler.record_function("critic_sequence"):
                value, prefixes, _ = learner.critic_sequence(
                    chunk.observations, chunk.steps, critic_state, chunk.actions, chunk.fields
                )
            with torch.profiler.record_function("objectives"):
                loss, _ = learner.objectives.actor(
                    logits.flatten(0, 1),
                    chunk.actions.flatten(0, 1),
                    chunk.behavior.flatten(0, 1),
                    torch.ones_like(chunk.behavior).flatten(0, 1),
                    chunk.fields.flatten(0, 1),
                    chunk.weights.flatten(),
                    mass,
                    1.0,
                )
                losses = learner.objectives.value(
                    value.flatten(),
                    prefixes.flatten(0, 1),
                    chunk.returns.flatten(),
                    chunk.fields.flatten(0, 1),
                    chunk.weights.flatten(),
                    mass,
                )
        with torch.profiler.record_function("actor_backward"):
            loss.backward()  # type: ignore[no-untyped-call]
        with torch.profiler.record_function("critic_backward"):
            losses[0].backward()  # type: ignore[no-untyped-call]

    operation()
    torch.cuda.synchronize()
    with torch.profiler.profile(
        activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA],
        record_shapes=False,
    ) as profile:
        operation()
        torch.cuda.synchronize()
    profile.export_chrome_trace(str(output.with_suffix(".trace.json")))
    output.with_suffix(".profile.txt").write_text(
        profile.key_averages().table(sort_by="self_device_time_total", row_limit=60)
    )


def benchmark(options: dict[str, Any]) -> None:
    """Restore weights, both Adam states and RNG before every measured repetition."""
    run, output = Path(options["run"]), Path(options["output"])
    identity = artifacts.source_identity()
    state = json.loads((run / "state.json").read_text())
    config = Experiment.model_validate(state["protocol"])
    assert config.execution is not None and len(config.execution.devices) == 1
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    torch.set_num_threads(config.execution.cpu_threads_per_rank)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    torch.backends.cudnn.benchmark = bool(options.get("cudnn_benchmark", False))
    if options.get("temporal_dense"):
        from kagg_revue.learning.performance.temporal import dense_attention
        from kagg_revue.policy.memory import temporal

        temporal.relative_attention = dense_attention  # type: ignore[attr-defined]
    if options.get("entity_options"):
        from kagg_revue.learning.performance.kernels import attention
        from kagg_revue.policy.spatial import encoder

        encoder.masked_attention = attention(options["entity_options"])  # type: ignore[attr-defined]
    settings = runtime_settings(config)
    actor, payload = artifacts.load_member(config, state, state["latest"], device)
    assert isinstance(actor, MemoryPolicy)
    critic = MemoryCritic(actor.layout).to(device)
    learner = SequenceLearner(settings, actor, critic)
    collection = MatchedCollection(config, settings, state, actor)
    if collection.cache is not None and not options.get("compile_history", True):
        collection.cache.config = config.model_copy(update={"compile": False})
    pipeline = PipelineCollection(config, actor, collection.cache)
    update = state["completed_update"] + 1
    match = Matchmaker(config, state).select(update, 1)
    active, name, history = collection.selection(match, update, 1)
    name = options.get("history") or name
    seeds = seed_shard(config, update, 0, 1, counts=(history, script_games(active, config.games)))
    fixed_rollout = None
    if options.get("tape"):
        fixed_rollout = _copy_rollout(
            torch.load(options["tape"], map_location="cpu", weights_only=False), device
        )
    measurements = []
    for repeat in range(options["repeats"]):
        actor.load_state_dict(payload["model"])
        critic.load_state_dict(payload["critic"])
        learner.restore_optimizers(
            copy.deepcopy(payload["actor_optimizer"]), copy.deepcopy(payload["critic_optimizer"])
        )
        restore_rng(payload, device, config, state=state)
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
        started = time.perf_counter()
        groups = pipeline.groups(active, seeds, name) if fixed_rollout is None else None
        prepared = time.perf_counter()
        rollout = pipeline.collect(active, groups) if groups is not None else fixed_rollout
        assert rollout is not None
        collected = time.perf_counter()
        optimization = learner.update(rollout)
        elapsed = time.perf_counter() - started
        record = {
            "repeat": repeat,
            "seconds": elapsed,
            "prepare_seconds": prepared - started,
            "collection_seconds": collected - prepared,
            "optimization": optimization,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "rollout": rollout.timing if groups is not None else None,
        }
        measurements.append(record)
        write_json(
            output,
            {
                "options": options,
                "run_id": state["run_id"],
                "checkpoint_sha256": state["members"][state["latest"]],
                "update": state["completed_update"],
                "source_sha256": identity["source_sha256"],
                "torch": torch.__version__,
                "gpu": torch.cuda.get_device_name(device),
                "measurements": measurements,
            },
        )
        print(json.dumps(record), flush=True)
        if repeat == 0 and options.get("save_tape"):
            torch.save(_copy_rollout(rollout, torch.device("cpu")), options["save_tape"])
        if repeat == options["repeats"] - 1 and options.get("profile"):
            _profile(learner, rollout, output)
        if repeat == options["repeats"] - 1 and options.get("verify_history") and groups:
            from kagg_revue.learning.performance.history import verify

            frozen = next((group.history for group in groups if group.history), None)
            if frozen is not None:
                write_json(output.with_suffix(".history.json"), verify(frozen, rollout))
        del rollout


@hydra.main(version_base=None, config_path="../../../../configs", config_name="hopper_recurrent")
def main(configuration: DictConfig) -> None:
    """Benchmark an immutable snapshot; never publish to its training ledger."""
    options = OmegaConf.to_container(configuration.benchmark, resolve=True)
    assert isinstance(options, dict)
    with compiler.patch(options.get("compiler", {})):
        benchmark(cast(dict[str, Any], options))


if __name__ == "__main__":
    main()
