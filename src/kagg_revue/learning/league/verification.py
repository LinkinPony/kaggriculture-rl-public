"""Full-size BC/PPO numerical qualification from previously trained weights."""

import json
import math
import os
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

import hydra
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.distributed import bind_cpus, gather
from kagg_revue.learning.league.collection import collect
from kagg_revue.learning.league.config import MEMBERS, League
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.inference import ActorRuntime


def _finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, torch.Tensor):
        return bool(value.isfinite().all())
    if isinstance(value, dict):
        return all(_finite(item) for item in value.values())
    if isinstance(value, (tuple, list)):
        return all(_finite(item) for item in value)
    return True


def _worker(rank: int, values: dict[str, Any], options: dict[str, Any], rendezvous: str) -> None:
    config = League.model_validate(values)
    settings = runtime_settings(config.experiment)
    device = torch.device(settings.devices[rank])
    bind_cpus(rank, len(settings.devices))
    torch.set_num_threads(2)
    torch.cuda.set_device(device)
    torch.backends.cuda.enable_cudnn_sdp(False)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    dist.init_process_group(
        "nccl",
        init_method=rendezvous,
        rank=rank,
        world_size=len(settings.devices),
        device_id=device,
        timeout=timedelta(minutes=30),
    )
    directory = Path(options["run"])
    learners, origins = [], {}
    for name in MEMBERS:
        child = directory / name
        state = json.loads((child / "state.json").read_text())
        checkpoint = child / state["latest"]
        if digest(checkpoint) != state["members"][state["latest"]]:
            raise ValueError("qualification checkpoint changed")
        actor, _ = load_policy(checkpoint, device)
        origins[name] = {"path": str(checkpoint), "sha256": digest(checkpoint)}
        torch.manual_seed(config.experiment.seed + 1)
        critic = PrefixCritic(actor.layout).to(device)
        learners.append(Learner(settings, actor, critic, None))
    torch.manual_seed(config.experiment.seed + rank + 990)
    count = config.trajectories_per_member // len(settings.devices)
    runtimes = [
        ActorRuntime(
            learner.policy,
            count,
            sample=True,
            temperature=settings.ppo.temperature,
            precision=settings.precision,
            bf16_reduced_precision_reduction=False,
            compile_inference=True,
        )
        for learner in learners
    ]
    output = Path(options["output"])
    report: dict[str, Any] = {
        "source": options["source"],
        "origins": origins,
        "updates": [],
        "qualification_only": True,
    }
    for update in range(1, options["updates"] + 1):
        started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)
        tapes, worker = collect(config, settings, runtimes, update)
        optimization = {}
        for name, learner, tape in zip(MEMBERS, learners, tapes, strict=True):
            # The training loss checks alone do not validate the sampled tape.
            if not _finite(vars(tape)):
                raise ValueError(f"nonfinite rollout tape for {name}")
            optimization[name] = learner.update(tape)
            if not _finite(
                [
                    learner.policy.state_dict(),
                    learner.critic.state_dict(),
                    learner.actor_optimizer.state_dict(),
                    learner.critic_optimizer.state_dict(),
                ]
            ):
                raise ValueError(f"nonfinite PPO parameters or optimizer for {name}")
        del tapes
        worker.update(
            optimization=optimization,
            seconds=time.perf_counter() - started,
            peak_bytes=torch.cuda.max_memory_allocated(device),
        )
        rows = gather(worker)
        if rank == 0:
            report["updates"].append({"update": update, "workers": rows})
            write_json(output, report)
            print(
                json.dumps(
                    {
                        "phase": "qualification_ppo",
                        "update": update,
                        "seconds": max(row["seconds"] for row in rows),
                    }
                ),
                flush=True,
            )
    dist.destroy_process_group()


@hydra.main(version_base=None, config_path="../../../../configs", config_name="league_verification")
def main(configuration: DictConfig) -> None:
    """Run isolated real-weight tests without changing any formal training artifact."""
    values: Any = OmegaConf.to_container(configuration.league, resolve=True)
    values["experiment"] = OmegaConf.to_container(configuration.experiment, resolve=True)
    config = League.model_validate(values)
    options: Any = OmegaConf.to_container(configuration.verification, resolve=True)
    options["source"] = artifacts.source_identity()["source_sha256"]
    path = Path("tmp/league-distributed") / f"verification-{os.getpid()}-{time.time_ns()}"
    path.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("TORCHINDUCTOR_COMPILE_THREADS", "8")
    try:
        mp.spawn(  # type: ignore[attr-defined,no-untyped-call]
            _worker,
            args=(config.model_dump(mode="json"), options, path.resolve().as_uri()),
            nprocs=len(runtime_settings(config.experiment).devices),
            join=True,
        )
        if artifacts.source_identity()["source_sha256"] != options["source"]:
            raise ValueError("source changed during numerical qualification")
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
