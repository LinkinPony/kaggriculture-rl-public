"""Measure full-size league rounds from an immutable checkpoint without writing it."""

import copy
import hashlib
import os
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

import hydra
import orjson
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.distributed import bind_cpus, gather
from kagg_revue.learning.league.collection import collect
from kagg_revue.learning.league.config import League
from kagg_revue.learning.league.training import _learners
from kagg_revue.policy.inference import ActorRuntime


def _worker(rank: int, options: dict[str, Any], rendezvous: str) -> None:
    root = Path(options["run"])
    state = orjson.loads((root / "league.json").read_bytes())
    config = League.model_validate(state["protocol"])
    settings = runtime_settings(config.experiment)
    device = torch.device(settings.devices[rank])
    bind_cpus(rank, len(settings.devices))
    torch.cuda.set_device(device)
    assert config.experiment.execution is not None
    torch.set_num_threads(config.experiment.execution.cpu_threads_per_rank)
    torch.backends.cuda.enable_cudnn_sdp(config.cudnn_attention)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    dist.init_process_group(
        "nccl",
        init_method=rendezvous,
        rank=rank,
        world_size=len(settings.devices),
        device_id=device,
        timeout=timedelta(minutes=30),
    )
    learners = _learners(config, state)
    runtimes = [
        ActorRuntime(
            learner.policy,
            config.trajectories_per_member // len(settings.devices),
            sample=True,
            temperature=settings.ppo.temperature,
            precision=settings.precision,
            bf16_reduced_precision_reduction=False,
            compile_inference=True,
        )
        for learner in learners
    ]
    checkpoint = root / state["latest"]
    if digest(checkpoint) != state["checkpoints"][state["latest"]]:
        raise ValueError("benchmark checkpoint changed")
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    output = Path(options["output"])
    report: dict[str, Any] = {
        "run_id": state["run_id"],
        "completed_update": state["completed_update"],
        "checkpoint_sha256": digest(checkpoint),
        "source_sha256": options["source_sha256"],
        "protocol": state["protocol"],
        "concurrent_inference": options["concurrent_inference"],
        "qualification_only": True,
        "measurements": [],
    }
    for iteration in range(options["repetitions"]):
        for name, learner in zip(config.members, learners, strict=True):
            saved = payload["models"][name]
            learner.policy.load_state_dict(saved["actor"])
            learner.critic.load_state_dict(saved["critic"])
            learner.restore_optimizers(
                copy.deepcopy(saved["actor_optimizer"]), copy.deepcopy(saved["critic_optimizer"])
            )
        torch.set_rng_state(payload["rng"]["workers"][rank]["cpu"])
        torch.cuda.set_rng_state(payload["rng"]["workers"][rank]["cuda"], device)
        dist.barrier()
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
        started = time.perf_counter()
        tapes, worker = collect(
            config,
            settings,
            runtimes,
            state["completed_update"] + 1,
            concurrent_inference=options["concurrent_inference"],
        )
        if options["sample_path"] and rank == 0 and iteration == 0:
            tape = tapes[0]
            indices = torch.linspace(0, len(tape.steps) - 1, 2880, device=device).long()
            torch.save(
                {
                    name: getattr(tape, name)[indices].cpu()
                    for name in ("observations", "actions", "steps", "log_probabilities")
                },
                options["sample_path"],
            )
        optimization: dict[str, Any] = {}
        for name, learner, tape in zip(config.members, learners, tapes, strict=True):
            if (
                options["profile"]
                and iteration == options["repetitions"] - 1
                and name == config.members[0]
            ):
                with torch.profiler.profile(
                    activities=[
                        torch.profiler.ProfilerActivity.CPU,
                        torch.profiler.ProfilerActivity.CUDA,
                    ],
                ) as profiler:
                    optimization[name] = learner.update(tape)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.with_suffix(f".rank{rank}.profile.txt").write_text(
                    profiler.key_averages().table(sort_by="self_cuda_time_total", row_limit=50)
                    + "\n"
                    + profiler.key_averages().table(sort_by="self_cpu_time_total", row_limit=35)
                )
                profiler.export_chrome_trace(str(output.with_suffix(f".rank{rank}.trace.json")))
            else:
                optimization[name] = learner.update(tape)
        worker.update(
            optimization=optimization,
            seconds=time.perf_counter() - started,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(device),
        )
        worker["action_sha256"] = {
            name: hashlib.sha256(tape.actions.cpu().numpy().tobytes()).hexdigest()
            for name, tape in zip(config.members, tapes, strict=True)
        }
        del tapes
        rows = gather(worker)
        valid_training = all(
            member["actor_steps"] > 0 and member["critic_steps"] > 0
            for row in rows
            for member in row["optimization"].values()
        )
        differences = {}
        for name, learner in zip(config.members, learners, strict=True):
            for role, module in (("actor", learner.policy), ("critic", learner.critic)):
                parameters = torch.cat([p.detach().flatten() for p in module.parameters()])
                reference = parameters.clone()
                dist.broadcast(reference, src=0)
                differences[f"{name}/{role}"] = float((parameters - reference).abs().max())
        if any(value != 0 for worker_diff in gather(differences) for value in worker_diff.values()):
            raise ValueError("benchmark learner ranks diverged")
        if rank == 0:
            report["measurements"].append(
                {
                    "iteration": iteration,
                    "workers": rows,
                    "seconds": max(row["seconds"] for row in rows),
                    "maximum_rank_parameter_difference": 0.0,
                    "all_actors_and_critics_updated": valid_training,
                    "profiled": bool(
                        options["profile"] and iteration == options["repetitions"] - 1
                    ),
                }
            )
            write_json(output, report)
            print(
                orjson.dumps(
                    {"iteration": iteration, "seconds": report["measurements"][-1]["seconds"]}
                ).decode(),
                flush=True,
            )
        if options["require_actor_updates"] and not valid_training:
            raise ValueError("a skipped actor update is not a valid throughput measurement")
    dist.destroy_process_group()


@hydra.main(version_base=None, config_path="../../../../configs", config_name="league_benchmark")
def main(configuration: DictConfig) -> None:
    """Run repeatable measurements with each round reset to the same saved state."""
    options: Any = OmegaConf.to_container(configuration.benchmark, resolve=True)
    options["source_sha256"] = artifacts.source_identity()["source_sha256"]
    state = orjson.loads((Path(options["run"]) / "league.json").read_bytes())
    devices = runtime_settings(League.model_validate(state["protocol"]).experiment).devices
    path = Path("tmp/league-distributed") / f"benchmark-{os.getpid()}-{time.time_ns()}"
    path.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("TORCHINDUCTOR_COMPILE_THREADS", "8")
    try:
        mp.spawn(  # type: ignore[attr-defined,no-untyped-call]
            _worker,
            args=(options, path.resolve().as_uri()),
            nprocs=len(devices),
            join=True,
        )
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
