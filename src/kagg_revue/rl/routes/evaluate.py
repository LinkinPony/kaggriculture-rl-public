"""Complete-match selection and confirmation for route-PPO checkpoints."""

from __future__ import annotations

import json
import statistics
import subprocess
import time
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.rl.routes.config import RoutePpoSettings
from kagg_revue.rl.routes.evaluation_config import RouteEvaluationSettings
from kagg_revue.rl.routes.model import RouteActorArchitecture, RouteActorCritic
from kagg_revue.rl.routes.rollout import RouteGameResult, RouteJob, RouteRolloutCollector
from kagg_revue.rl.routes.train import _architecture, _artifact_identities, _resolve


def _revision(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _resolve_evaluation(
    settings: RouteEvaluationSettings,
    root: Path,
) -> RouteEvaluationSettings:
    def path(value: Path) -> Path:
        return value.resolve() if value.is_absolute() else (root / value).resolve()

    return settings.model_copy(
        update={"run_dir": path(settings.run_dir), "output_dir": path(settings.output_dir)}
    )


def _checkpoint_update(path: Path) -> int:
    prefix = "checkpoint-"
    if not path.stem.startswith(prefix):
        raise ValueError(f"route checkpoint has an invalid name: {path.name}")
    return int(path.stem[len(prefix) :])


def _checkpoint_paths(settings: RouteEvaluationSettings) -> tuple[Path, ...]:
    directory = settings.run_dir / "checkpoints" / "permanent"
    paths: tuple[Path, ...]
    if settings.checkpoint_set == "single":
        if settings.checkpoint_update is None:
            raise RuntimeError("single route checkpoint update disappeared after validation")
        paths = (directory / f"checkpoint-{settings.checkpoint_update:08d}.pt",)
    else:
        paths = tuple(sorted(directory.glob("checkpoint-*.pt"), key=_checkpoint_update))
    if not paths or any(not path.is_file() for path in paths):
        raise FileNotFoundError("route evaluation checkpoint set is incomplete")
    updates = tuple(_checkpoint_update(path) for path in paths)
    if len(set(updates)) != len(updates):
        raise ValueError("route evaluation checkpoint set repeats an update")
    return paths


def _jobs(
    settings: RoutePpoSettings,
    evaluation: RouteEvaluationSettings,
) -> tuple[RouteJob, ...]:
    default_start = (
        settings.selection_seed_start
        if evaluation.panel == "selection"
        else settings.confirmation_seed_start
    )
    start = evaluation.seed_start if evaluation.seed_start is not None else default_start
    count = (
        evaluation.seed_count
        if evaluation.seed_count is not None
        else settings.evaluation_seed_count
    )
    seeds = range(start, start + count)
    return tuple(
        (seed, seat, opponent)
        for opponent in settings.opponents
        for seed in seeds
        for seat in (0, 1)
    )


def _summarize_outcomes(values: Sequence[int]) -> dict[str, int]:
    return {
        "games": len(values),
        "wins": sum(value > 0 for value in values),
        "ties": sum(value == 0 for value in values),
        "losses": sum(value < 0 for value in values),
    }


def _game_summary(games: Sequence[RouteGameResult]) -> dict[str, object]:
    candidate = [game.outcome for game in games]
    direct = [game.direct_outcome for game in games]
    deltas = [left - right for left, right in zip(candidate, direct, strict=True)]

    def opponent_summary(opponent: str) -> dict[str, object]:
        rows = tuple(game for game in games if game.opponent_id == opponent)
        return {
            "candidate": _summarize_outcomes([game.outcome for game in rows]),
            "direct_control": _summarize_outcomes([game.direct_outcome for game in rows]),
            "paired_terminal_outcome": {
                "better": sum(game.outcome > game.direct_outcome for game in rows),
                "same": sum(game.outcome == game.direct_outcome for game in rows),
                "worse": sum(game.outcome < game.direct_outcome for game in rows),
            },
            "mean_terminal_cash": statistics.fmean(game.terminal_cash for game in rows),
            "mean_cash_difference": statistics.fmean(
                game.terminal_cash - game.opponent_cash for game in rows
            ),
        }

    return {
        "candidate": _summarize_outcomes(candidate),
        "direct_control": _summarize_outcomes(direct),
        "paired_terminal_outcome": {
            "better": sum(delta > 0 for delta in deltas),
            "same": sum(delta == 0 for delta in deltas),
            "worse": sum(delta < 0 for delta in deltas),
        },
        "mean_terminal_cash": statistics.fmean(game.terminal_cash for game in games),
        "mean_cash_difference": statistics.fmean(
            game.terminal_cash - game.opponent_cash for game in games
        ),
        "opponents": {
            opponent: opponent_summary(opponent)
            for opponent in sorted({game.opponent_id for game in games})
        },
    }


def _selection_gate(summary: Mapping[str, Any]) -> dict[str, bool]:
    candidate = cast(Mapping[str, int], summary["candidate"])
    direct = cast(Mapping[str, int], summary["direct_control"])
    paired = cast(Mapping[str, int], summary["paired_terminal_outcome"])
    opponents = cast(Mapping[str, Mapping[str, Any]], summary["opponents"])
    incumbent = cast(Mapping[str, int], opponents["kaito_v48"]["candidate"])
    population_noninferior = (
        candidate["wins"] >= direct["wins"] and candidate["losses"] <= direct["losses"]
    )
    paired_positive = paired["better"] > paired["worse"]
    incumbent_positive = incumbent["wins"] > incumbent["losses"]
    return {
        "population_wdl_noninferior": population_noninferior,
        "paired_terminal_outcome_positive": paired_positive,
        "incumbent_head_to_head_positive": incumbent_positive,
        "passes": population_noninferior and paired_positive and incumbent_positive,
    }


def _architecture_from_checkpoint(raw: Mapping[str, object]) -> RouteActorArchitecture:
    architecture = raw.get("architecture")
    if not isinstance(architecture, Mapping):
        raise ValueError("route checkpoint lacks an architecture")
    return RouteActorArchitecture(
        feature_width=int(architecture["feature_width"]),
        hidden_width=int(architecture["hidden_width"]),
        feedforward_width=int(architecture["feedforward_width"]),
        prior_logit=float(architecture["prior_logit"]),
    )


def _game_record(update: int, game: RouteGameResult) -> dict[str, object]:
    return {
        "checkpoint_update": update,
        "opponent_id": game.opponent_id,
        "seed": game.seed,
        "seat": game.seat,
        "outcome": game.outcome,
        "direct_outcome": game.direct_outcome,
        "terminal_cash": game.terminal_cash,
        "opponent_cash": game.opponent_cash,
        "selected_route": game.selected_route,
    }


def evaluate_route_checkpoints(
    raw_training: RoutePpoSettings,
    raw_evaluation: RouteEvaluationSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Evaluate a predeclared checkpoint grid using complete paired matches."""
    root = repository_root.resolve()
    training = _resolve(raw_training, root)
    evaluation = _resolve_evaluation(raw_evaluation, root)
    output_root = (root / "outputs").resolve()
    run_inside_outputs = evaluation.run_dir.is_relative_to(output_root)
    evaluation_inside_outputs = evaluation.output_dir.is_relative_to(output_root)
    if not run_inside_outputs or not evaluation_inside_outputs:
        raise ValueError("route evaluation paths escaped outputs/")
    if evaluation.output_dir.exists():
        raise FileExistsError(f"route evaluation output already exists: {evaluation.output_dir}")
    source = cast(Mapping[str, object], source_identity(root))
    if bool(source["worktree_dirty"]):
        raise RuntimeError("formal route evaluation requires a clean worktree")
    resolved_path = evaluation.run_dir / "resolved-settings.json"
    if not resolved_path.is_file():
        raise FileNotFoundError("route PPO run lacks resolved settings")
    run_identity = cast(Mapping[str, Any], json.loads(resolved_path.read_text(encoding="utf-8")))
    checkpoints = _checkpoint_paths(evaluation)
    backend = load_backend(root)
    expected_artifacts = _artifact_identities(backend, training)
    expected_architecture = _architecture(training)
    device = torch.device(training.device)
    generator = torch.Generator(device=device)
    generator.manual_seed(training.seed + 404)
    collector_environment = cast(Mapping[str, object], run_identity["resolved_environment"])
    jobs = _jobs(training, evaluation)
    checkpoint_reports: list[dict[str, object]] = []
    all_games: list[dict[str, object]] = []
    direct_identity: tuple[tuple[int, float, float], ...] | None = None
    started = time.perf_counter()
    for index, checkpoint_path in enumerate(checkpoints, start=1):
        raw_checkpoint = cast(
            Mapping[str, Any],
            torch.load(checkpoint_path, map_location=device, weights_only=False),
        )
        update = int(raw_checkpoint["update"])
        if update != _checkpoint_update(checkpoint_path):
            raise ValueError("route checkpoint filename and payload update differ")
        if raw_checkpoint.get("settings_contract") != training.checkpoint_contract():
            raise ValueError("route checkpoint settings differ from the evaluation profile")
        if raw_checkpoint.get("artifact_identities") != expected_artifacts:
            raise ValueError("route checkpoint artifacts differ from the evaluation runtime")
        if raw_checkpoint.get("source_revision") != run_identity.get("source_revision"):
            raise ValueError("route checkpoint and run source revisions differ")
        architecture = _architecture_from_checkpoint(raw_checkpoint)
        if architecture != expected_architecture:
            raise ValueError("route checkpoint architecture differs from the evaluation profile")
        runtime_architecture = (
            replace(architecture, prior_logit=evaluation.prior_logit_override)
            if evaluation.prior_logit_override is not None
            else architecture
        )
        model = RouteActorCritic(runtime_architecture).to(device)
        model.load_state_dict(raw_checkpoint["model_state_dict"])
        collector = RouteRolloutCollector(
            backend,
            model,
            collector_environment,
            unit_limit=training.rollout.unit_limit,
            cpu_workers=training.rollout.cpu_workers,
            action_generator=generator,
        )
        rollout = collector.collect(jobs, sample=False)
        current_direct = tuple(
            (game.direct_outcome, game.direct_terminal_cash, game.direct_opponent_cash)
            for game in rollout.games
        )
        if direct_identity is None:
            direct_identity = current_direct
        elif current_direct != direct_identity:
            raise RuntimeError("same-job DIRECT control changed across route checkpoints")
        summary = _game_summary(rollout.games)
        gate = _selection_gate(summary)
        checkpoint_report = {
            "update": update,
            "checkpoint": {
                "path": str(checkpoint_path.relative_to(root)),
                "sha256": sha256_file(checkpoint_path),
                "source_revision": raw_checkpoint["source_revision"],
            },
            "policy": {
                "checkpoint_prior_logit": architecture.prior_logit,
                "runtime_prior_logit": runtime_architecture.prior_logit,
            },
            "outcomes": summary,
            "selection_gate": gate,
            "selected_routes": {
                str(route): sum(game.selected_route == route for game in rollout.games)
                for route in range(6)
            },
            "prior_agreement": float(
                (rollout.actions == rollout.prior_actions).mean()
            ),
            "execution": rollout.diagnostics,
        }
        checkpoint_reports.append(checkpoint_report)
        all_games.extend(_game_record(update, game) for game in rollout.games)
        print(
            json.dumps(
                {
                    "completed_checkpoints": index,
                    "total_checkpoints": len(checkpoints),
                    "update": update,
                    "outcomes": summary["candidate"],
                    "paired": summary["paired_terminal_outcome"],
                    "gate": gate,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        del collector, model, rollout, raw_checkpoint
        torch.cuda.empty_cache()

    def rank_key(report: Mapping[str, Any]) -> tuple[int, int, int]:
        outcomes = cast(Mapping[str, Any], report["outcomes"])
        paired = cast(Mapping[str, int], outcomes["paired_terminal_outcome"])
        candidate = cast(Mapping[str, int], outcomes["candidate"])
        return (
            paired["better"] - paired["worse"],
            -candidate["losses"],
            candidate["wins"],
        )

    eligible = [
        report
        for report in checkpoint_reports
        if cast(Mapping[str, bool], report["selection_gate"])["passes"]
    ]
    selected = max(eligible, key=rank_key) if eligible else None
    diagnostic_leader = max(checkpoint_reports, key=rank_key)
    evaluation.output_dir.mkdir(parents=True)
    (evaluation.output_dir / "resolved-settings.json").write_text(
        json.dumps(
            {
                "route_ppo": training.model_dump(mode="json"),
                "evaluation": evaluation.model_dump(mode="json"),
            },
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )
    report: dict[str, object] = {
        "schema_version": "event-route-ppo-complete-match-evaluation-v1",
        "decision_surface": "complete official-rule terminal W/D/L",
        "cash_role": "diagnostic only",
        "panel": {
            "name": evaluation.panel,
            "opponents": list(training.opponents),
            "seed_start": jobs[0][0] if jobs else None,
            "seed_count": (
                evaluation.seed_count
                if evaluation.seed_count is not None
                else training.evaluation_seed_count
            ),
            "paired_seats": True,
            "games_per_checkpoint": len(jobs),
        },
        "evaluation_source": {
            "revision": _revision(root),
            **dict(source),
        },
        "training_run": {
            "path": str(evaluation.run_dir.relative_to(root)),
            "resolved_settings_sha256": sha256_file(resolved_path),
            "source_revision": run_identity["source_revision"],
            "artifact_identities": expected_artifacts,
        },
        "checkpoint_reports": checkpoint_reports,
        "selection": {
            "rule": (
                "pass all direct W/D/L gates, then maximize paired better-minus-worse; "
                "ties use fewer losses then more wins"
            ),
            "selected_update": selected["update"] if selected is not None else None,
            "diagnostic_leader_update": diagnostic_leader["update"],
            "eligible_updates": [report["update"] for report in eligible],
        },
        "games": all_games,
        "elapsed_seconds": time.perf_counter() - started,
    }
    report_path = evaluation.output_dir / "evaluation-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return {
        "report": str(report_path),
        "checkpoints": len(checkpoint_reports),
        "selected_update": selected["update"] if selected is not None else None,
        "diagnostic_leader_update": diagnostic_leader["update"],
        "elapsed_seconds": report["elapsed_seconds"],
    }


__all__ = ["evaluate_route_checkpoints"]
