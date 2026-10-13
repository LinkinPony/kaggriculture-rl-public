"""PPO continuation with an evolving opponent archive and no automatic evaluation."""

import faulthandler
import fcntl
import json
import os
import signal
import time
from types import FrameType
from typing import Any

import numpy as np
import torch

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.checkpointing.writer import CheckpointWriter
from kagg_revue.learning.collection.matched import MatchedCollection
from kagg_revue.learning.collection.pipeline import PipelineCollection
from kagg_revue.learning.collection.population import outcomes, script_games
from kagg_revue.learning.collection.rewards import margin_diagnostics
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.curriculum import collect_update, create_bank
from kagg_revue.learning.distributed import (
    any_stop,
    barrier,
    gather,
    rank_world,
    restore_rng,
    seed_shard,
)
from kagg_revue.learning.matchmaking.defaults import training_defaults
from kagg_revue.learning.matchmaking.migration import restored_statistics
from kagg_revue.learning.matchmaking.scheduler import Matchmaker
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.learning.pretraining.train import initialize
from kagg_revue.learning.progress import publish
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.learning.telemetry import combine


class StopRequest:
    """Finish the current atomic update before stopping on TERM or INT."""

    requested = False

    def handle(self, number: int, frame: FrameType | None) -> None:
        """Record a signal without interrupting an optimizer or checkpoint write."""
        self.requested = True


def _train(
    config: Experiment,
    settings: RuntimeSettings,
    state: dict[str, Any],
    stop: StopRequest,
) -> None:
    rank, world = rank_world()
    device = torch.device(settings.devices[rank])
    torch.manual_seed(config.seed)
    actor, payload = artifacts.load_member(config, state, state["latest"], device)
    if config.population.pfsp is not None and state["completed_update"] and "pfsp" not in state:
        raise ValueError("PFSP continuation requires saved or explicitly initialized statistics")
    bank = create_bank(config, actor)
    if bank is not None:
        qualification = bank.prepare()
        if rank == 0:
            write_json(config.output_dir / "source-qualification.json", qualification)
            print(json.dumps({"phase": "source_qualification", **qualification}), flush=True)
    learner: Learner
    critic: PrefixCritic
    if config.memory_turns:
        from kagg_revue.learning.sequences.critic import MemoryCritic
        from kagg_revue.learning.sequences.learner import SequenceLearner
        from kagg_revue.policy.memory.policy import MemoryPolicy

        assert isinstance(actor, MemoryPolicy)
        recurrent_critic = MemoryCritic(actor.layout).to(device)
        critic = recurrent_critic
        reference: MemoryPolicy | None = None
        if settings.ppo.reference_kl_weight > 0:
            root, _ = artifacts.load_member(config, state, "initial.pt", device)
            assert isinstance(root, MemoryPolicy)
            reference = root
        learner = SequenceLearner(settings, actor, recurrent_critic, reference)
    else:
        critic = PrefixCritic(actor.layout).to(device)
        learner = Learner(settings, actor, critic, None)
    if state["completed_update"]:
        if payload["update"] != state["completed_update"]:
            raise ValueError("latest checkpoint and completed update disagree")
        critic.load_state_dict(payload["critic"])
        learner.restore_optimizers(payload["actor_optimizer"], payload["critic_optimizer"])
        restore_rng(payload, device, config, state=state)
        if (
            "pfsp" in state
            and state["pfsp"]["started_update"] <= state["completed_update"]
            and restored_statistics(payload.get("pfsp"), state) != state["pfsp"]
        ):
            raise ValueError("PFSP checkpoint statistics differ from the committed ledger")
    else:
        if config.initial_critic is not None:
            critic.load_state_dict(payload["critic"], strict=True)
        if rank:
            torch.manual_seed(config.seed + 1000000007 * rank)
    del payload
    games = config.games // world
    collection = MatchedCollection(config, settings, state, actor)
    pipeline = (
        PipelineCollection(config, actor, collection.cache)
        if config.execution is not None and config.execution.pipeline_groups == 2
        else None
    )
    preparation_started = time.perf_counter()
    (pipeline or collection).prepare(world)
    if rank == 0:
        print(
            json.dumps(
                {
                    "phase": "inference_prepared",
                    "seconds": time.perf_counter() - preparation_started,
                    "row_counts": sorted((pipeline or collection).runtimes),
                }
            ),
            flush=True,
        )
    matchmaking = Matchmaker(config, state) if config.population.pfsp is not None else None
    barrier()
    with CheckpointWriter(config, settings, state, learner) as writer:
        completed_games = sum(row["physical_games"] for row in state["records"])
        for update in range(state["completed_update"] + 1, config.updates + 1):
            if any_stop(stop.requested, device):
                stop.requested = True
                break
            started = time.perf_counter()
            torch.cuda.reset_peak_memory_stats(device)
            match = matchmaking.select(update, world) if matchmaking else None
            opponent_started = time.perf_counter()
            if pipeline is None:
                active_settings, runtime, history_runtime, name, historical_games = (
                    collection.resolve(match, update, world)
                )
                opponent_seconds = time.perf_counter() - opponent_started
                rollout, restart = collect_update(
                    config, active_settings, actor, runtime, history_runtime, bank, update
                )
            else:
                active_settings, name, historical_games = collection.selection(match, update, world)
                seeds = seed_shard(
                    config,
                    update,
                    rank,
                    world,
                    counts=(historical_games * world, script_games(active_settings, games) * world),
                )
                groups = pipeline.groups(active_settings, seeds, name)
                opponent_seconds = time.perf_counter() - opponent_started
                rollout = pipeline.collect(active_settings, groups)
                restart = {
                    "start_step": 0,
                    "split": "fresh",
                    "official_prefix_actions_in_ppo": 0,
                    "mean_cash_change": float(
                        rollout.cash.mean() - config.environment.get("startingMoney", 3000)
                    ),
                    "policy_transitions": games * settings.turns,
                }
            reward_metrics = margin_diagnostics(rollout, active_settings)
            if config.learning_rate_warmup_updates:
                learner.schedule(update)
            optimization = learner.update(rollout)
            cash = rollout.cash
            against_history = cash[games - historical_games :]
            worker = {
                "rank": rank,
                "device": str(device),
                "physical_games": games,
                "cpu_affinity": sorted(os.sched_getaffinity(0)),
                "native_workers": settings.workers,
                "restart": restart,
                "mean_cash": float(cash.mean()),
                "history_score": float(
                    (np.sign(against_history[:, 0] - against_history[:, 1]) + 1).mean() / 2
                )
                if historical_games
                else None,
                "populations": outcomes(cash, list(rollout.opponents)),
                "rollout": rollout.timing,
                "land": rollout.land,
                "optimization": optimization,
                "reward_values": sorted(torch.unique(rollout.returns).tolist()),
                "cash_reward_weight": active_settings.ppo.cash_weight,
                "win_reward_weight": active_settings.ppo.win_weight,
                **reward_metrics,
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
                "update_seconds": time.perf_counter() - started,
                "opponent_seconds": opponent_seconds,
            }
            del rollout
            completed_games += config.games
            metrics = {
                "update": update,
                "physical_games": config.games,
                "cumulative_physical_games": completed_games,
                "opponent": {"path": name, "sha256": state["members"][name]} if name else None,
                "pool": list(state["pool"]),
                **combine(config, gather(worker)),
            }
            checkpoint_started = time.perf_counter()
            writer.finish()
            if matchmaking is not None and match is not None:
                matchmaking.observe(match, update, metrics["populations"])
                metrics["pfsp"] = match.report
            writer.record(update, metrics)
            if rank == 0:
                publish(config, state, "reinforcement_learning", update=update, world_size=world)
                # Include foreground snapshot/publication and any prior-save backpressure.
                # Background write latency is recorded separately in checkpoint-timing.jsonl.
                cycle = {
                    "update": update,
                    "full_update_seconds": time.perf_counter() - started,
                    "checkpoint_seconds": time.perf_counter() - checkpoint_started,
                    "async_checkpoint": writer.asynchronous,
                    "checkpoint_update": state["completed_update"],
                    "finished_at": time.time(),
                }
                with (config.output_dir / "cycle-timing.jsonl").open("a") as stream:
                    stream.write(json.dumps(cycle) + "\n")
                print(json.dumps(metrics), flush=True)
        writer.flush()
        barrier()


def _run(config: Experiment) -> None:
    """Run one random-root policy with authenticated, synchronous GPU workers."""
    device = torch.device(config.device)
    if device.type != "cuda":
        raise ValueError("training requires a CUDA device; use CPU only for component checks")
    if config.deterministic:
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.use_deterministic_algorithms(config.deterministic)
    torch.cuda.set_device(device)
    torch.set_num_threads(config.cpu_threads)
    settings = runtime_settings(config)
    faulthandler.register(signal.SIGUSR1, all_threads=True)
    state = artifacts.restore(config) if config.resume else artifacts.create(config, settings)
    artifacts.publish_metrics(config, state)
    status_path = config.output_dir / "run-status.json"
    stop = StopRequest()
    handlers = {
        number: signal.signal(number, stop.handle) for number in (signal.SIGTERM, signal.SIGINT)
    }
    write_json(
        status_path,
        {
            "status": "running",
            "pid": os.getpid(),
            "started_at": time.time(),
            "run_id": state["run_id"],
            "resumed": config.resume,
            "devices": list(settings.devices),
            "world_size": len(settings.devices),
        },
    )
    status = "failed"
    try:
        publish(config, state, "initializing")
        if (
            config.demonstrations is not None
            and config.demonstrations.distributed
            and "rl_initial" not in state
        ):
            from kagg_revue.learning.launch import parallel

            parallel(config, stop, pretraining=True)
            state = json.loads((config.output_dir / "state.json").read_text())
        else:
            initialize(config, settings, state, lambda: stop.requested)
        if not stop.requested and not config.pretraining_only:
            if config.population.sources and state["completed_update"] == 0:
                from kagg_revue.learning.matchmaking.imports import (
                    import_opponents,
                    registered,
                    transition,
                )

                if not config.resume or not registered(config, state):
                    import_opponents(config, state)
                    transition(config, state, config)
                    artifacts.write_ledger(config.output_dir, state)
            publish(config, state, "reinforcement_learning")
            if config.execution is not None and len(config.execution.devices) > 1:
                from kagg_revue.learning.launch import parallel

                parallel(config, stop)
                state = json.loads((config.output_dir / "state.json").read_text())
            else:
                _train(config, settings, state, stop)
        status = "stopped" if stop.requested else "complete"
    finally:
        if (config.output_dir / "state.json").exists():
            state = json.loads((config.output_dir / "state.json").read_text())
        publish(config, state, status)
        write_json(
            status_path,
            {
                "status": status,
                "pid": os.getpid(),
                "ended_at": time.time(),
                "run_id": state["run_id"],
                "completed_update": state["completed_update"],
            },
        )
        for number, handler in handlers.items():
            signal.signal(number, handler)


def run(config: Experiment) -> None:
    """Hold one nonblocking writer lock throughout initialization and every learner rank."""
    config = training_defaults(config)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    with (config.output_dir / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _run(config)
