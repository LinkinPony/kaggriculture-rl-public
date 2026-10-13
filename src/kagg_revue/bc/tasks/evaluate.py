"""Official smoke and GPU-batched evaluation for a unit-task BC checkpoint."""

from __future__ import annotations

import gc
import json
import statistics
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.tasks.config import TaskBcSettings
from kagg_revue.bc.tasks.prepare import resolve_task_bc_settings
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.runtime import BaselineAgent
from kagg_revue.policy.tasks.native import NativeTaskContract
from kagg_revue.rl.tasks.checkpoint import load_task_checkpoint
from kagg_revue.rl.tasks.rollout import (
    TaskRolloutCollector,
    TaskRolloutReport,
    task_rollout_jobs,
)
from kagg_revue.rl.tasks.runtime import TaskTapeAgent


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def _official_smoke(
    backend: BackendApi,
    candidate: TaskTapeAgent,
    environment: Mapping[str, object],
    seed: int,
    transitions: int,
    *,
    act_timeout_seconds: float,
    remaining_overage_seconds: float,
) -> list[dict[str, object]]:
    """Exercise both candidate seats briefly through the reference boundary."""
    rows: list[dict[str, object]] = []
    for candidate_seat in (0, 1):
        engine = backend.engine(seed=seed, configuration=dict(environment))
        opponent = BaselineAgent(backend, engine.configuration)
        candidate.reset()
        total_seconds = 0.0
        maximum_seconds = 0.0
        remaining = remaining_overage_seconds
        completed = 0
        while completed < transitions:
            if bool(engine.done):
                raise RuntimeError("official BC smoke ended before its transition budget")
            started = time.perf_counter()
            candidate_action = candidate.act(
                cast(Mapping[str, Any], engine.observation(candidate_seat))
            )
            elapsed = time.perf_counter() - started
            total_seconds += elapsed
            maximum_seconds = max(maximum_seconds, elapsed)
            remaining -= max(0.0, elapsed - act_timeout_seconds)
            if remaining < 0.0:
                raise TimeoutError("official BC smoke exhausted candidate overage")
            opponent_seat = 1 - candidate_seat
            opponent_action = opponent.act(
                cast(Mapping[str, Any], engine.observation(opponent_seat))
            )
            actions = [opponent_action, opponent_action]
            actions[candidate_seat] = candidate_action
            engine.step(actions[0], actions[1])
            completed += 1
        rows.append(
            {
                "seed": seed,
                "candidate_seat": candidate_seat,
                "transitions": completed,
                "candidate_total_seconds": total_seconds,
                "candidate_max_seconds": maximum_seconds,
                "candidate_remaining_overage_seconds": remaining,
                "candidate_diagnostics": candidate.diagnostics(),
            }
        )
    return rows


def _fast_rows(
    rollout: TaskRolloutReport,
    expected_transitions: int,
) -> list[dict[str, object]]:
    """Project retained training episodes onto direct match outcomes only."""
    rows: list[dict[str, object]] = []
    for episode in rollout.episodes:
        trajectory = episode.trajectory
        transitions = len(trajectory.turns)
        rows.append(
            {
                "candidate_id": "unit_task_bc",
                "opponent_id": trajectory.opponent_id,
                "seed": trajectory.seed,
                "candidate_seat": trajectory.seat,
                "candidate_money": trajectory.terminal_cash,
                "opponent_money": trajectory.opponent_cash,
                "margin": trajectory.terminal_cash - trajectory.opponent_cash,
                "outcome": trajectory.outcome,
                "candidate_error": None,
                "opponent_error": None,
                "done": transitions == expected_transitions,
                "transitions": transitions,
            }
        )
    return rows


def _summary(
    rows: Sequence[Mapping[str, object]],
    rollout: TaskRolloutReport,
) -> dict[str, object]:
    """Summarize one direct-outcome matchup without introducing a proxy."""
    if not rows:
        raise ValueError("cannot summarize an empty GPU BC matchup")
    outcomes = [int(cast(int, row["outcome"])) for row in rows]
    cash = [float(cast(float, row["candidate_money"])) for row in rows]
    margins = [float(cast(float, row["margin"])) for row in rows]
    return {
        "games": len(rows),
        "wins": sum(value > 0 for value in outcomes),
        "ties": sum(value == 0 for value in outcomes),
        "losses": sum(value < 0 for value in outcomes),
        "mean_terminal_cash": statistics.fmean(cash),
        "mean_cash_difference": statistics.fmean(margins),
        "errors": sum(row["candidate_error"] is not None for row in rows),
        "max_batched_actor_seconds": rollout.maximum_actor_seconds,
        "minimum_remaining_overage_seconds": rollout.remaining_overage_seconds,
    }


def _valid(
    rows: Sequence[Mapping[str, object]],
    expected: set[tuple[str, int, int]],
    expected_transitions: int,
) -> bool:
    actual = {
        (
            str(row["opponent_id"]),
            int(cast(int, row["seed"])),
            int(cast(int, row["candidate_seat"])),
        )
        for row in rows
    }
    return actual == expected and all(
        bool(row["done"])
        and int(cast(int, row["transitions"])) == expected_transitions
        and row["candidate_error"] is None
        and row["opponent_error"] is None
        for row in rows
    )


def evaluate_task_bc(
    raw_settings: TaskBcSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Smoke the reference boundary, then run complete matches in GPU batches."""
    root = repository_root.resolve()
    settings = resolve_task_bc_settings(raw_settings, root)
    if not settings.evaluation.enabled:
        return {"status": "disabled"}
    report_path = settings.output_dir / "evaluation-report.json"
    games_path = settings.output_dir / "evaluation-games.json"
    if report_path.exists() or games_path.exists():
        raise FileExistsError("task BC evaluation outputs already exist")
    training_path = settings.output_dir / "training-report.json"
    training = json.loads(training_path.read_text(encoding="utf-8"))
    if not isinstance(training, Mapping) or training.get("status") != "training_complete":
        raise ValueError("task BC evaluation lacks a complete training report")
    best = training.get("best")
    checkpoint_record = best.get("checkpoint") if isinstance(best, Mapping) else None
    checkpoint = settings.output_dir / "checkpoints" / "best.pt"
    if (
        not isinstance(checkpoint_record, Mapping)
        or not checkpoint.is_file()
        or checkpoint_record.get("sha256") != sha256_file(checkpoint)
    ):
        raise ValueError("task BC best checkpoint differs from training report")

    backend = load_backend(root)
    resolved_environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    device = torch.device(settings.evaluation.device)
    if device.type != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("task BC heavy evaluation requires an available GPU")
    torch.set_num_threads(settings.evaluation.cpu_threads)

    candidate_runtime = TaskTapeAgent(
        backend,
        resolved_environment,
        checkpoint,
        settings.evaluation.device,
        settings.abi.unit_limit,
        settings.abi.maximum_quantity,
        sample=False,
        cpu_threads=settings.evaluation.cpu_threads,
        act_timeout_seconds=settings.evaluation.act_timeout_seconds,
        remaining_overage_seconds=settings.evaluation.remaining_overage_seconds,
    )
    smoke_rows = _official_smoke(
        backend,
        candidate_runtime,
        resolved_environment,
        settings.evaluation.seeds[0],
        settings.evaluation.smoke_transitions,
        act_timeout_seconds=settings.evaluation.act_timeout_seconds,
        remaining_overage_seconds=settings.evaluation.remaining_overage_seconds,
    )
    print(json.dumps({"official_reference_smoke": smoke_rows}), flush=True)
    del candidate_runtime
    gc.collect()
    torch.cuda.empty_cache()

    contract = NativeTaskContract.from_spec(
        cast(
            Mapping[str, object],
            backend.unit_task_spec(
                resolved_environment,
                settings.abi.unit_limit,
                settings.abi.maximum_quantity,
            ),
        )
    )
    model, _metadata = load_task_checkpoint(
        checkpoint,
        contract,
        device,
        include_optimizer=False,
    )
    opponent_weight = 1.0 / len(settings.evaluation.opponents)
    opponent_weights = {
        opponent: opponent_weight for opponent in settings.evaluation.opponents
    }
    jobs = task_rollout_jobs(
        settings.evaluation.seeds,
        settings.evaluation.opponents,
    )
    batch_games = min(settings.evaluation.batch_games, len(jobs))
    groups = (len(jobs) + batch_games - 1) // batch_games
    actor_streams = min(settings.evaluation.actor_streams, groups)
    collector = TaskRolloutCollector(
        backend,
        model,
        contract,
        root,
        settings.evaluation.public_agent_manifest,
        resolved_environment,
        opponent_weights,
        device,
        batch_games=batch_games,
        cpu_workers=settings.evaluation.cpu_threads,
        actor_streams=actor_streams,
        sampling_seed=settings.evaluation.seeds[0],
        act_timeout_seconds=settings.evaluation.act_timeout_seconds,
        remaining_overage_seconds=settings.evaluation.remaining_overage_seconds,
        initial_actor=checkpoint,
    )
    print(
        json.dumps(
            {
                "gpu_native_batch": {
                    "games": len(jobs),
                    "batch_games": batch_games,
                    "actor_streams": actor_streams,
                }
            }
        ),
        flush=True,
    )
    try:
        rollout = collector.collect(
            settings.evaluation.seeds,
            sample=False,
            full_panel=True,
        )
        opponent_identities = collector.opponent_identities
    finally:
        collector.release_cuda_graphs()

    expected_transitions = cast(int, resolved_environment["episodeSteps"]) - 1
    rows = _fast_rows(rollout, expected_transitions)
    expected = {
        (opponent, seed, seat)
        for opponent in settings.evaluation.opponents
        for seed in settings.evaluation.seeds
        for seat in (0, 1)
    }
    valid = _valid(rows, expected, expected_transitions)
    matchups: dict[str, object] = {}
    for opponent in settings.evaluation.opponents:
        opponent_rows = [row for row in rows if row["opponent_id"] == opponent]
        matchups[opponent] = {
            "scratch_unit_task_bc": _summary(opponent_rows, rollout)
        }
        print(
            json.dumps(
                {"opponent": opponent, "summary": matchups[opponent]},
                sort_keys=True,
            ),
            flush=True,
        )

    _write_json(games_path, rows)
    report: dict[str, object] = {
        "schema_version": "unit-task-scratch-bc-evaluation-v2",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "complete" if valid else "invalid_matches",
        "source": source_identity(root),
        "decision_surface": ["win", "loss", "tie"],
        "diagnostic_surface": ["terminal cash", "terminal cash difference"],
        "promotion_authority": False,
        "reason": "configured post-BC diagnostic panel; no confirmation gate was run",
        "seeds": list(settings.evaluation.seeds),
        "paired_seats": True,
        "resolved_environment": resolved_environment,
        "matchups": matchups,
        "routing": {
            "official_reference": "smoke_only",
            "heavy_panel": "gpu_native_batch",
        },
        "official_reference_smoke": {
            "status": "complete",
            "transitions_per_seat": settings.evaluation.smoke_transitions,
            "rows": smoke_rows,
        },
        "execution": {
            "device": settings.evaluation.device,
            "batch_games": batch_games,
            "actor_streams": actor_streams,
            "act_timeout_seconds": settings.evaluation.act_timeout_seconds,
            "remaining_overage_seconds": (
                settings.evaluation.remaining_overage_seconds
            ),
            "maximum_batched_actor_seconds": rollout.maximum_actor_seconds,
            "minimum_remaining_overage_seconds": (
                rollout.remaining_overage_seconds
            ),
            "phase_seconds": dict(rollout.phase_seconds),
            "expected_transitions_per_game": expected_transitions,
            "all_matches_valid": valid,
        },
        "opponents": opponent_identities,
        "checkpoint": {
            "path": str(checkpoint),
            "sha256": sha256_file(checkpoint),
        },
        "training_report": {
            "path": str(training_path),
            "sha256": sha256_file(training_path),
        },
        "games": {
            "path": str(games_path),
            "sha256": sha256_file(games_path),
            "count": len(rows),
        },
    }
    _write_json(report_path, report)
    return report


__all__ = ["evaluate_task_bc"]
