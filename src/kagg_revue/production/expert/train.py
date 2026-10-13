"""Recoverable dual-GPU expert iteration over complete official-rule matches."""

import json
import os
import time
from pathlib import Path
from typing import Any, cast

import hydra
import numpy as np
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.evaluation import panel
from kagg_revue.production.expert.config import ExpertSettings
from kagg_revue.production.expert.learning import Learner
from kagg_revue.production.expert.proposals import SearchPolicy
from kagg_revue.production.expert.search import Search
from kagg_revue.production.train import _gather


def _comparison(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, int]:
    delta = np.array([g["outcome"] for g in candidate["games"]]) - np.array(
        [g["outcome"] for g in baseline["games"]]
    )
    return {
        "better": int((delta > 0).sum()),
        "same": int((delta == 0).sum()),
        "worse": int((delta < 0).sum()),
        "wdl_gain": int(delta.sum()),
    }


def _rank(rank: int, resolved: dict[str, Any], rendezvous: str) -> None:
    config = ExpertSettings.model_validate(resolved)
    p = config.production
    world = len(p.devices)
    device = torch.device(p.devices[rank])
    torch.cuda.set_device(device)
    torch.set_num_threads(p.cpu_threads)
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = (
        p.bf16_reduced_precision_reduction
    )
    if world > 1:
        dist.init_process_group(
            "nccl", init_method=rendezvous, rank=rank, world_size=world, device_id=device
        )
    torch.manual_seed(p.seed + rank)
    directory = p.output_dir
    latest_path = directory / "checkpoints/latest.json"
    latest = json.loads(latest_path.read_text()) if latest_path.exists() else None
    assert p.checkpoint is not None
    checkpoint = Path(latest["path"]) if latest else p.checkpoint
    loaded, saved = load_policy(checkpoint, torch.device("cpu"))
    if latest:
        previous = dict(saved["expert_configuration"])
        current = dict(resolved)
        previous.pop("iterations")
        current.pop("iterations")
        if previous != current:
            raise ValueError("changed experiments require an isolated output directory")
    student = cast(WorkPolicy, loaded.to(device)).eval()
    if student.layout != ContractLayout.resolve(p):
        raise ValueError("resolved experiment architecture differs from the actual checkpoint")
    root = WorkPolicy(student.layout).to(device).eval()
    root.load_state_dict(student.state_dict())
    count = p.ppo.games_per_update // world
    search_policy = (
        SearchPolicy(student.layout, count + int(count * (1 - p.ppo.script_fraction)))
        .to(device)
        .eval()
    )
    search_policy.requires_grad_(False)
    search_policy.load_state_dict(student.state_dict())
    search = Search(config, search_policy)
    learner = Learner(config, student, root)
    update = int(saved["expert_update"]) if latest else 0
    if latest:
        learner.optimizer.load_state_dict(saved["optimizer"])
        torch.set_rng_state(saved["rank_rng"][rank]["cpu"])
        torch.cuda.set_rng_state(saved["rank_rng"][rank]["cuda"], device)
    del saved, loaded
    source = provenance(p) if rank == 0 else {}
    if rank == 0:
        if not source["clean"]:
            raise ValueError("experiment requires a clean source revision")
        write_json(directory / "source.json", source)
        write_json(directory / "resolved-config.json", resolved)
        write_json(
            directory / "baseline.json", {"path": str(p.checkpoint), "sha256": digest(p.checkpoint)}
        )
        if not (directory / "evaluation/baseline-selection.json").exists():
            baseline, extra = load_policy(p.checkpoint, torch.device("cpu"))
            del extra
            baseline = baseline.to(device)
            write_json(
                directory / "evaluation/baseline-selection.json",
                panel(p, baseline, p.evaluation_seed),
            )
            write_json(
                directory / "evaluation/baseline-confirmation.json",
                panel(p, baseline, p.confirmation_seed),
            )
            del baseline
        baseline_panel = json.loads((directory / "evaluation/baseline-selection.json").read_text())
    if world > 1:
        dist.barrier()
    while update < config.iterations:
        update += 1
        started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)
        root.load_state_dict(student.state_dict())
        search_policy.load_state_dict(student.state_dict())
        seed_start = p.ppo.seed_start + (update - 1) * p.ppo.games_per_update + rank * count
        # Script games repeat seeds across seats, within the update's reserved range.
        seeds = [seed_start + i // 2 for i in range(count)]
        result = search.run(seeds)
        phase = time.perf_counter()
        shard = directory / "data" / f"update-{update:04d}-rank-{rank}.npz"
        shard.parent.mkdir(parents=True, exist_ok=True)
        selected = result.expert.valid & result.improved[None]
        np.savez_compressed(
            shard,
            observations=result.expert.observations[selected].cpu().numpy(),
            actions=result.expert.actions[selected].cpu().numpy(),
            steps=result.expert.steps[selected].cpu().numpy(),
        )
        data_seconds = time.perf_counter() - phase
        optimization = learner.update(result)
        local = {
            "rank": rank,
            "search": result.report,
            "optimization": optimization,
            "data_seconds": data_seconds,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
        }
        del result
        ranks = _gather(local, world)
        rngs = _gather(
            {"cpu": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state(device)}, world
        )
        if rank == 0:
            checkpoint = directory / "checkpoints" / f"update-{update:04d}.pt"
            save_policy(
                checkpoint,
                student,
                p,
                expert_update=update,
                training_phase="expert_iteration",
                optimizer=learner.optimizer.state_dict(),
                rank_rng=rngs,
                expert_configuration=resolved,
                provenance=source,
            )
            write_json(
                latest_path,
                {"path": str(checkpoint), "update": update, "sha256": digest(checkpoint)},
            )
            record: dict[str, Any] = {
                "update": update,
                "ranks": ranks,
                "checkpoint": str(checkpoint),
                "source_revision": source["revision"],
            }
            if update % config.evaluation_interval == 0 or update == config.iterations:
                evaluation = panel(p, student, p.evaluation_seed)
                evaluation.update(
                    checkpoint=str(checkpoint),
                    sha256=digest(checkpoint),
                    paired_to_baseline=_comparison(evaluation, baseline_panel),
                )
                write_json(directory / "evaluation" / f"selection-{update:04d}.json", evaluation)
                record["selection"] = {k: v for k, v in evaluation.items() if k != "games"}
            record["update_seconds"] = time.perf_counter() - started
            record["search_physical_games_per_second"] = (
                p.ppo.games_per_update
                * (1 + len(config.proposals))
                / max(r["search"]["search_seconds"] for r in ranks)
            )
            record["end_to_end_physical_games_per_second"] = (
                p.ppo.games_per_update * (1 + len(config.proposals)) / record["update_seconds"]
            )
            record["cold_actor_capture_seconds"] = (
                search.runtime.capture_seconds if update == 1 else 0
            )
            write_json(directory / "updates" / f"{update:04d}.json", record)
            with (directory / "metrics.jsonl").open("a") as stream:
                stream.write(json.dumps(record) + "\n")
            print(json.dumps({k: v for k, v in record.items() if k != "ranks"}), flush=True)
        if world > 1:
            dist.barrier()
    if rank == 0:
        confirmation = panel(p, student, p.confirmation_seed)
        baseline_confirm = json.loads(
            (directory / "evaluation/baseline-confirmation.json").read_text()
        )
        confirmation.update(
            checkpoint=str(checkpoint),
            sha256=digest(checkpoint),
            paired_to_baseline=_comparison(confirmation, baseline_confirm),
        )
        write_json(directory / "evaluation/confirmation.json", confirmation)
    if world > 1:
        dist.destroy_process_group()


def launch(config: ExpertSettings) -> None:
    """Run a finite reproducible challenger without changing deployment selection."""
    directory = config.production.output_dir
    directory.mkdir(parents=True, exist_ok=True)
    status = directory / "run-status.json"
    latest_path = directory / "checkpoints/latest.json"
    if status.exists() and latest_path.exists():
        previous_status = json.loads(status.read_text())
        latest = json.loads(latest_path.read_text())
        if previous_status["status"] == "completed" and latest["update"] >= config.iterations:
            print({"status": "already_completed", "directory": str(directory)}, flush=True)
            return
    write_json(status, {"status": "running", "pid": os.getpid(), "started_at": time.time()})
    rendezvous = (Path("tmp") / "parallel-policy" / f"expert-{time.time_ns()}").resolve()
    rendezvous.parent.mkdir(parents=True, exist_ok=True)
    try:
        mp.spawn(  # type: ignore[attr-defined, no-untyped-call]
            _rank,
            args=(config.model_dump(mode="json"), rendezvous.as_uri()),
            nprocs=len(config.production.devices),
            join=True,
        )
        write_json(status, {"status": "completed", "pid": os.getpid(), "ended_at": time.time()})
    except BaseException:
        write_json(status, {"status": "failed", "pid": os.getpid(), "ended_at": time.time()})
        raise
    finally:
        rendezvous.unlink(missing_ok=True)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="production_expert")
def main(configuration: DictConfig) -> None:
    """Resolve and validate the complete experiment before allocating GPU resources."""
    launch(ExpertSettings.model_validate(OmegaConf.to_container(configuration, resolve=True)))


if __name__ == "__main__":
    main()
