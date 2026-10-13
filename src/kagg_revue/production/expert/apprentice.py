"""Recoverable search/gradient-learning cycles with separately evaluated apprentices."""

import json
import os
import shutil
import time
from dataclasses import asdict
from datetime import UTC, datetime
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
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.expert.assessment import Assessment, parameter_changes
from kagg_revue.production.expert.budget import LearningBudget
from kagg_revue.production.expert.config import ApprenticeSettings
from kagg_revue.production.expert.curriculum import Curriculum
from kagg_revue.production.expert.imitation import ApprenticeLearner, fit_round
from kagg_revue.production.expert.telemetry import progress
from kagg_revue.production.reporting import retain_checkpoints
from kagg_revue.production.train import _gather


def _report(
    directory: Path,
    workers: list[dict[str, Any]],
    identity: dict[str, Any],
    expert: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    assessments = {worker["assessment"]["population"]: worker["assessment"] for worker in workers}
    outcomes = {}
    for population, assessment in assessments.items():
        for role in ("student", "expert", "origin"):
            panel = assessment[role]
            outcomes[f"{role} / {population}"] = {
                **{key: panel[key] for key in ("wins", "ties", "losses")},
                "mean_terminal_cash": panel["mean_cash"],
                "mean_cash_difference": panel["mean_cash_difference"],
            }
    write_json(
        directory / "evaluation-report.json",
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "decision_surface": "apprentice/expert/origin on fresh paired complete matches",
            "checkpoint": identity,
            "expert": expert,
            "source": source,
            "completion": {"complete": True},
            "execution": {"backend": "native", "deployment_budget_qualified": False},
            "decision": {
                "status": "retain_incumbent",
                "reasons": ["学生单独 argmax 执行；新种子选择集，未改变正式 incumbent。"],
            },
            "outcomes": outcomes,
        },
    )
    return assessments


def _rank(rank: int, resolved: dict[str, Any], rendezvous: str) -> None:
    setup_started = time.perf_counter()
    c = ApprenticeSettings.model_validate(resolved)
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
    loaded, saved = load_policy(
        Path(latest["path"]) if latest else p.checkpoint, torch.device("cpu")
    )
    student = cast(WorkPolicy, loaded.to(device)).eval().requires_grad_(True)
    if student.layout != ContractLayout.resolve(p):
        raise ValueError("apprentice architecture differs from the resolved checkpoint")
    update = int(saved["apprentice_update"]) if latest else 0
    budget = (
        LearningBudget(
            **saved.get(
                "learning_budget", {"fits": update, "optimizer_steps": update * c.learner_steps}
            )
        )
        if latest
        else LearningBudget()
    )
    expert_identity = (
        saved["expert"] if latest else {"path": str(c.teacher), "sha256": digest(c.teacher)}
    )
    teacher, _ = load_policy(Path(expert_identity["path"]), torch.device("cpu"))
    teacher = cast(WorkPolicy, teacher.to(device)).eval().requires_grad_(False)
    reference, _ = load_policy(c.reference, torch.device("cpu"))
    reference = reference.to(device).eval().requires_grad_(False)
    if teacher.layout != student.layout or reference.layout != student.layout:
        raise ValueError("student, expert and reference must share the exact no-table architecture")
    learner = ApprenticeLearner(c, student, teacher)
    if latest:
        previous = ApprenticeSettings.model_validate(saved["apprentice_configuration"]).model_dump(
            mode="json"
        )
        current = dict(resolved)
        previous.pop("generations")
        current.pop("generations")
        if previous != current:
            raise ValueError("changed apprentice experiments require an isolated output directory")
        learner.optimizer.load_state_dict(saved["optimizer"])
        torch.set_rng_state(saved["rank_rng"][rank]["cpu"])
        torch.cuda.set_rng_state(saved["rank_rng"][rank]["cuda"], device)
    del loaded, saved
    games = p.ppo.games_per_update // world
    runtime = ActorRuntime(
        student,
        2 * games - script_games(p, games),
        sample=False,
        precision=p.precision,
        bf16_reduced_precision_reduction=p.bf16_reduced_precision_reduction,
    )
    assessment = Assessment(p, reference, rank)
    curriculum = Curriculum(c, student, reference, rank)
    source = json.loads((directory / "source.json").read_text())
    first = True
    setup_seconds = time.perf_counter() - setup_started
    while update < c.generations:
        update += 1
        started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)
        search_result = None
        phase = time.perf_counter()
        if update > c.bootstrap_updates and update % c.search_interval == 0:
            search_result = curriculum.improve(student, teacher, update)
            if search_result["expert_replaced"]:
                expert_identity = search_result["expert"]
                budget.renew()
        search_seconds = time.perf_counter() - phase
        learned = budget.available(c.fits_per_expert)
        fitting = (
            fit_round(c, runtime, learner, rank, update)
            if learned
            else {
                "rollout": {"rollout_seconds": 0.0},
                "optimization": {
                    "actor_steps": 0,
                    "learner_seconds": 0.0,
                    "encoder_parameter_delta_l2": 0.0,
                    "learning_rate": c.learning_rate,
                },
                "data_seconds": 0.0,
                "data_rows": 0,
                "mean_cash": None,
            }
        )
        if learned:
            budget.record(c.learner_steps)
        local = {
            "rank": rank,
            **fitting,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
            "cold_actor_capture_seconds": runtime.capture_seconds if first else 0.0,
            "cold_target_capture_seconds": learner.capture_seconds if first else 0.0,
            "cold_setup_seconds": setup_seconds if first else 0.0,
        }
        phase = time.perf_counter()
        if learned and (update % c.evaluation_interval == 0 or update == c.generations):
            progress(directory, update, rank, "evaluate", 0, 3)
            local["assessment"] = assessment.run(
                student,
                teacher,
                c.validation_seed + (update - 1) * p.evaluation_games // 2,
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
            checkpoint = directory / "checkpoints" / f"update-{update:06d}.pt"
            save_policy(
                checkpoint,
                student,
                p,
                apprentice_update=update,
                training_phase="expert_iteration",
                expert=expert_identity,
                optimizer=learner.optimizer.state_dict(),
                rank_rng=rngs,
                apprentice_configuration=resolved,
                learning_budget=asdict(budget),
                provenance=source,
            )
            identity = {"path": str(checkpoint), "sha256": digest(checkpoint), "update": update}
            write_json(latest_path, identity)
            evaluations = (
                _report(directory, workers, identity, expert_identity, source)
                if "assessment" in local
                else {}
            )
            checkpoint_seconds = time.perf_counter() - phase
            elapsed = time.perf_counter() - started
            physical_games = (
                (p.ppo.games_per_update if learned else 0)
                + sum(w.get("assessment", {}).get("physical_games", 0) for w in workers)
                + (search_result["physical_games"] if search_result else 0)
            )
            record = {
                "update": update,
                "timestamp": time.time(),
                "training_phase": "expert_iteration",
                "checkpoint": identity,
                "expert": expert_identity,
                "source_revision": source["revision"],
                "workers": workers,
                "evaluation": evaluations,
                "search": search_result,
                "learning": {
                    "performed": learned,
                    "reason": "expert_fit" if learned else "expert_budget_exhausted",
                    "fits_per_expert": c.fits_per_expert,
                    **asdict(budget),
                },
                "physical_games": physical_games,
                "training_games": p.ppo.games_per_update if learned else 0,
                "physical_games_per_second": physical_games / elapsed,
                "update_seconds": elapsed,
                "checkpoint_seconds": checkpoint_seconds,
                "search_seconds": search_seconds,
                "mean_cash": sum(w["mean_cash"] for w in workers) / world if learned else None,
                "optimizer_steps": budget.optimizer_steps,
            }
            write_json(directory / "updates" / f"update-{update:06d}.json", record)
            with (directory / "metrics.jsonl").open("a") as stream:
                stream.write(json.dumps(record) + "\n")
            print(
                json.dumps(
                    {
                        key: value
                        for key, value in record.items()
                        if key not in {"workers", "evaluation", "search"}
                    }
                ),
                flush=True,
            )
            retain_checkpoints(checkpoint.parent, c.retain_generations)
            retain_checkpoints(directory / "experts", c.retain_generations)
            for old in (directory / "data").glob(
                f"update-{update - c.retain_generations:06d}-rank-*.npz"
            ):
                old.unlink()
            candidates = (
                directory / "candidates" / f"generation-{update - c.retain_generations:06d}"
            )
            if candidates.exists():
                shutil.rmtree(candidates)
            progress(directory, update, rank, "complete", 1, 1)
        dist.barrier()
        first = False
    if rank == 0:
        write_json(directory / "parameter-changes.json", parameter_changes(student, p.checkpoint))
    dist.destroy_process_group()


def launch(config: ApprenticeSettings) -> None:
    """Bind immutable inputs, exact resolved controls and clean source before spawning."""
    p, directory = config.production, config.production.output_dir
    assert p.checkpoint is not None
    directory.mkdir(parents=True, exist_ok=True)
    source = provenance(p)
    if not source["clean"]:
        raise ValueError("apprentice experiments require a clean source revision")
    inputs = {
        name: {"path": str(path), "sha256": digest(path)}
        for name, path in (
            ("student", p.checkpoint),
            ("teacher", config.teacher),
            ("reference", config.reference),
        )
    }
    if (directory / "inputs.json").exists() and json.loads(
        (directory / "inputs.json").read_text()
    ) != inputs:
        raise ValueError("apprentice input identities changed on resume")
    write_json(directory / "inputs.json", inputs)
    write_json(directory / "source.json", source)
    write_json(directory / "sources" / f"{source['revision']}.json", source)
    write_json(directory / "resolved-config.json", config.model_dump(mode="json"))
    status = directory / "run-status.json"
    write_json(status, {"status": "running", "pid": os.getpid(), "started_at": time.time()})
    rendezvous = (Path("tmp/parallel-policy") / f"apprentice-{time.time_ns()}").resolve()
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
    version_base=None, config_path="../../../../configs", config_name="production_apprentice"
)
def main(configuration: DictConfig) -> None:
    """Run the exact production search/gradient-learning experiment."""
    launch(ApprenticeSettings.model_validate(OmegaConf.to_container(configuration, resolve=True)))


if __name__ == "__main__":
    main()
