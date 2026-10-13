"""Recoverable full-network policy iteration from counterfactual native state branches."""

import json
import os
import time
from pathlib import Path
from typing import Any, cast

import hydra
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.collection.population import script_games
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.branching.config import BranchSettings
from kagg_revue.production.branching.evidence import (
    StudentAssessment,
    evaluation_report,
    search_summary,
)
from kagg_revue.production.branching.learner import BranchLearner
from kagg_revue.production.branching.rollout import StateSearch
from kagg_revue.production.branching.verification import verify_forks
from kagg_revue.production.expert.assessment import parameter_changes
from kagg_revue.production.expert.telemetry import progress
from kagg_revue.production.reporting import retain_checkpoints
from kagg_revue.production.train import _gather


def _rank(rank: int, resolved: dict[str, Any], rendezvous: str) -> None:
    started = time.perf_counter()
    c = BranchSettings.model_validate(resolved)
    p, directory = c.production, c.production.output_dir
    device = torch.device(p.devices[rank])
    torch.cuda.set_device(device)
    torch.set_num_threads(p.cpu_threads)
    torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = (
        p.bf16_reduced_precision_reduction
    )
    world = len(p.devices)
    dist.init_process_group(
        "nccl", init_method=rendezvous, rank=rank, world_size=world, device_id=device
    )
    torch.manual_seed(p.seed + rank)
    latest_path = directory / "checkpoints/latest.json"
    latest = json.loads(latest_path.read_text()) if latest_path.exists() else None
    assert p.checkpoint is not None
    initial, _ = load_policy(p.checkpoint, torch.device("cpu"))
    initial = initial.to(device).eval().requires_grad_(False)
    loaded, saved = load_policy(
        Path(latest["path"]) if latest else p.checkpoint, torch.device("cpu")
    )
    student = cast(WorkPolicy, loaded.to(device)).eval().requires_grad_(True)
    alternate, _ = load_policy(c.continuation, torch.device("cpu"))
    alternate = cast(WorkPolicy, alternate.to(device)).eval().requires_grad_(False)
    reference, _ = load_policy(c.reference, torch.device("cpu"))
    reference = reference.to(device).eval().requires_grad_(False)
    if any(
        model.layout != ContractLayout.resolve(p)
        for model in (student, alternate, reference, initial)
    ):
        raise ValueError("state-branch actors must share the resolved no-table architecture")
    update = int(saved["branch_update"]) if latest else 0
    optimizer_steps = int(saved["optimizer_steps"]) if latest else 0
    if rank == 0 and not latest:
        audit = verify_forks(p, initial)
        audit["source"] = json.loads((directory / "source.json").read_text())
        write_json(directory / "fork-parity.json", audit)
    dist.barrier()
    search = StateSearch(c, student, alternate, rank)
    learner = BranchLearner(c, student)
    assessment = StudentAssessment(p, reference, rank)
    if latest:
        before, after = dict(saved["branch_configuration"]), dict(resolved)
        before.pop("updates")
        after.pop("updates")
        if before != after:
            raise ValueError("changed state-branch experiments require an isolated run")
        learner.optimizer.load_state_dict(saved["optimizer"])
        torch.set_rng_state(saved["rank_rng"][rank]["cpu"])
        torch.cuda.set_rng_state(saved["rank_rng"][rank]["cuda"], device)
    del saved, loaded
    source = json.loads((directory / "source.json").read_text())
    setup_seconds = time.perf_counter() - started
    first = True
    while update < c.updates:
        update += 1
        started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)
        tape = search.run(student, update)
        counterfactual = search_summary(tape)
        progress(directory, update, rank, "learn", 0, c.learner_steps)
        optimization = learner.update(tape)
        optimizer_steps += optimization["actor_steps"]
        phase = time.perf_counter()
        data = directory / "data" / f"update-{update:06d}-rank-{rank}.npz"
        tape.save(data)
        data_seconds = time.perf_counter() - phase
        assert tape.prefix_cash is not None
        selfplay = search.games - script_games(p, search.games)
        local = {
            "rank": rank,
            "rollout": tape.timing,
            "optimization": optimization,
            "search": counterfactual,
            "data": str(data),
            "data_seconds": data_seconds,
            "mean_cash": float(
                (tape.prefix_cash[:selfplay].mean(1).sum() + tape.prefix_cash[selfplay:, 0].sum())
                / search.games
            ),
            "cold_setup_seconds": setup_seconds if first else 0.0,
            "cold_actor_capture_seconds": search.capture_seconds if first else 0.0,
        }
        del tape
        phase = time.perf_counter()
        if update <= 3 or update % c.evaluation_interval == 0 or update == c.updates:
            progress(directory, update, rank, "evaluate", 0, 4)
            local["assessment"] = assessment.run_student(
                student,
                initial,
                alternate,
                p.evaluation_seed + (update - 1) * p.evaluation_games // 2,
                directory / "evaluation" / f"update-{update:06d}-rank-{rank}.json",
            )
        local["evaluation_seconds"] = time.perf_counter() - phase
        local["peak_allocated_bytes"] = torch.cuda.max_memory_allocated(device)
        local["peak_reserved_bytes"] = torch.cuda.max_memory_reserved(device)
        workers = _gather(local, world)
        rngs = _gather(
            {"cpu": torch.get_rng_state(), "cuda": torch.cuda.get_rng_state(device)}, world
        )
        if rank == 0:
            phase = time.perf_counter()
            progress(directory, update, rank, "checkpoint", 0, 1)
            path = directory / "checkpoints" / f"update-{update:06d}.pt"
            save_policy(
                path,
                student,
                p,
                branch_update=update,
                training_phase="state_branch",
                optimizer_steps=optimizer_steps,
                optimizer=learner.optimizer.state_dict(),
                rank_rng=rngs,
                branch_configuration=resolved,
                provenance=source,
            )
            identity = {"path": str(path), "sha256": digest(path), "update": update}
            write_json(latest_path, identity)
            evaluation = (
                evaluation_report(directory, workers, identity, source)
                if "assessment" in local
                else {}
            )
            checkpoint_seconds = time.perf_counter() - phase
            elapsed = time.perf_counter() - started
            physical_games = p.ppo.games_per_update + sum(
                w["search"]["physical_games"] + w.get("assessment", {}).get("physical_games", 0)
                for w in workers
            )
            summary = {
                key: sum(w["search"][key] for w in workers)
                for key in (
                    "roots",
                    "improved_roots",
                    "script_improved_roots",
                    "selfplay_improved_roots",
                    "informative_pairs",
                )
            }
            summary["hindsight_labels_only"] = True
            record = {
                "update": update,
                "timestamp": time.time(),
                "training_phase": "state_branch",
                "checkpoint": identity,
                "source_revision": source["revision"],
                "workers": workers,
                "evaluation": evaluation,
                "search": summary,
                "optimizer_steps": optimizer_steps,
                "physical_games": physical_games,
                "training_games": p.ppo.games_per_update,
                "physical_games_per_second": physical_games / elapsed,
                "update_seconds": elapsed,
                "checkpoint_seconds": checkpoint_seconds,
                "search_seconds": max(w["rollout"]["rollout_seconds"] for w in workers),
                "mean_cash": sum(w["mean_cash"] for w in workers) / world,
            }
            write_json(directory / "updates" / f"update-{update:06d}.json", record)
            with (directory / "metrics.jsonl").open("a") as stream:
                stream.write(json.dumps(record) + "\n")
            print(
                json.dumps(
                    {
                        key: value
                        for key, value in record.items()
                        if key not in {"workers", "evaluation"}
                    }
                ),
                flush=True,
            )
            retain_checkpoints(path.parent, c.retain_checkpoints)
            for old in (directory / "data").glob(
                f"update-{update - c.retain_checkpoints:06d}-rank-*.npz"
            ):
                old.unlink()
            progress(directory, update, rank, "complete", 1, 1)
        dist.barrier()
        first = False
    if rank == 0:
        write_json(directory / "parameter-changes.json", parameter_changes(student, p.checkpoint))
    dist.destroy_process_group()


def launch(config: BranchSettings) -> None:
    """Bind exact inputs and clean source before launching a recoverable production job."""
    p, directory = config.production, config.production.output_dir
    assert p.checkpoint is not None
    directory.mkdir(parents=True, exist_ok=True)
    source = provenance(p)
    if not source["clean"]:
        raise ValueError("state-branch training requires a clean source revision")
    inputs = {
        name: {"path": str(path), "sha256": digest(path)}
        for name, path in (
            ("student", p.checkpoint),
            ("continuation", config.continuation),
            ("reference", config.reference),
        )
    }
    if (directory / "inputs.json").exists() and json.loads(
        (directory / "inputs.json").read_text()
    ) != inputs:
        raise ValueError("state-branch input identities changed on resume")
    write_json(directory / "inputs.json", inputs)
    write_json(directory / "source.json", source)
    write_json(directory / "sources" / f"{source['revision']}.json", source)
    write_json(directory / "resolved-config.json", config.model_dump(mode="json"))
    status = directory / "run-status.json"
    write_json(status, {"status": "running", "pid": os.getpid(), "started_at": time.time()})
    rendezvous = (Path("tmp/state-branch") / f"rendezvous-{time.time_ns()}").resolve()
    rendezvous.parent.mkdir(parents=True, exist_ok=True)
    try:
        mp.spawn(  # type: ignore[attr-defined, no-untyped-call]
            _rank,
            args=(config.model_dump(mode="json"), rendezvous.as_uri()),
            nprocs=len(p.devices),
            join=True,
        )
        write_json(status, {"status": "completed", "pid": os.getpid(), "ended_at": time.time()})
    except BaseException:
        write_json(status, {"status": "failed", "pid": os.getpid(), "ended_at": time.time()})
        raise
    finally:
        rendezvous.unlink(missing_ok=True)


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="production_branching"
)
def main(configuration: DictConfig) -> None:
    """Start state-rooted search and actual actor preference learning."""
    launch(BranchSettings.model_validate(OmegaConf.to_container(configuration, resolve=True)))


if __name__ == "__main__":
    main()
