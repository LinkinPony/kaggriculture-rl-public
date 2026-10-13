"""Held-out complete-match decision for a unit-task challenger."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.evaluate import AgentFactory, run_paired_panel, summarize_games
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.runtime import BaselineAgent
from kagg_revue.rl.evaluate import advancement_decision, compare_paired_outcomes
from kagg_revue.rl.tasks.config import TaskRlSettings
from kagg_revue.rl.tasks.incumbent import incumbent_factory
from kagg_revue.rl.tasks.runtime import TaskTapeAgent
from kagg_revue.rl.tasks.train import resolve_task_settings


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"unit-task evaluation {name} is not numeric")
    return int(value)


def _strict_improvement(summary: Mapping[str, object]) -> bool:
    return _integer(summary["wins"], "wins") > _integer(
        summary["losses"], "losses"
    )


def _valid(rows: Sequence[Mapping[str, object]], transitions: int) -> bool:
    return all(
        bool(row["done"])
        and _integer(row["transitions"], "transitions") == transitions
        and row["candidate_error"] is None
        and row["opponent_error"] is None
        for row in rows
    )


def _training_report(output_dir: Path) -> dict[str, object]:
    path = output_dir / "training-report.json"
    if not path.is_file():
        raise FileNotFoundError("unit-task evaluation lacks a training report")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("unit-task training report is not a mapping")
    return cast(dict[str, object], raw)


def _checkpoint(output_dir: Path, report: Mapping[str, object]) -> Path:
    path = output_dir / "checkpoints" / "latest.pt"
    latest = report.get("latest")
    if not path.is_file() or not isinstance(latest, Mapping):
        raise FileNotFoundError("unit-task evaluation lacks a final checkpoint")
    record = latest.get("checkpoint")
    if not isinstance(record, Mapping) or record.get("sha256") != sha256_file(path):
        raise ValueError("unit-task final checkpoint differs from its training report")
    return path


def _validate_resolved_profile(
    output_dir: Path,
    settings: TaskRlSettings,
) -> None:
    path = output_dir / "resolved-settings.json"
    if not path.is_file():
        raise FileNotFoundError("unit-task evaluation lacks resolved training settings")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping) or raw.get("unit_task_rl") != settings.model_dump(
        mode="json"
    ):
        raise ValueError("unit-task evaluation profile differs from the trained run")


def _validate_training_initialization(
    training: Mapping[str, object],
    settings: TaskRlSettings,
) -> None:
    """Match evaluation to either an actor-only or complete initial artifact."""
    source_actor = training.get("initial_actor")
    if not isinstance(source_actor, Mapping):
        raise ValueError("unit-task training report lacks actor provenance")
    if settings.initial_actor is not None:
        if (
            Path(str(source_actor.get("path"))).resolve()
            != settings.initial_actor.resolve()
            or source_actor.get("sha256") != sha256_file(settings.initial_actor)
        ):
            raise ValueError("unit-task initial actor differs from its training report")
        return
    checkpoint = settings.initial_task_checkpoint
    initialization = training.get("initialization")
    if checkpoint is None or not isinstance(initialization, Mapping):
        raise ValueError("unit-task complete initialization differs from training")
    record = initialization.get("checkpoint")
    if (
        not isinstance(record, Mapping)
        or Path(str(record.get("path"))).resolve() != checkpoint.resolve()
        or record.get("sha256") != sha256_file(checkpoint)
    ):
        raise ValueError("unit-task complete initialization differs from training")


def _challenger_factory(
    backend: BackendApi,
    settings: TaskRlSettings,
    checkpoint: Path,
) -> AgentFactory:
    runtime = TaskTapeAgent(
        backend,
        settings.environment,
        checkpoint,
        settings.device,
        settings.abi.unit_limit,
        settings.abi.maximum_quantity,
        cpu_threads=settings.cpu_threads,
        act_timeout_seconds=settings.act_timeout_seconds,
        remaining_overage_seconds=settings.remaining_overage_seconds,
    )

    def factory(configuration: Mapping[str, Any]) -> TaskTapeAgent:
        if dict(configuration) != settings.environment:
            raise ValueError("unit-task evaluation environment changed within its panel")
        return runtime

    return factory


def _opponent_factories(
    backend: BackendApi,
    settings: TaskRlSettings,
) -> tuple[dict[str, AgentFactory], dict[str, object], int]:
    manifest = backend.load_public_agent_manifest(settings.public_agent_manifest)
    records = manifest.by_id()
    factories: dict[str, AgentFactory] = {}
    identities: dict[str, object] = {}
    public = 0
    for opponent_id in settings.evaluation_opponents:
        if opponent_id == "deterministic_incumbent":

            def baseline(configuration: Mapping[str, Any]) -> BaselineAgent:
                return BaselineAgent(backend, configuration)

            factories[opponent_id] = baseline
            identities[opponent_id] = {"kind": "deterministic_incumbent"}
            continue
        record = records.get(opponent_id)
        if record is None:
            raise KeyError(f"unit-task evaluation opponent is absent: {opponent_id}")

        def notebook(
            configuration: Mapping[str, Any],
            record: Any = record,
        ) -> Any:
            return backend.public_agent_runtime(record, backend.repository_root, configuration)

        factories[opponent_id] = notebook
        identities[opponent_id] = {
            "kind": "public_notebook",
            "notebook_ref": record.notebook_ref,
            "notebook_id": record.notebook_id,
            "artifact_sha256": record.sha256,
        }
        public += 1
    return factories, identities, public


def _phase(
    name: str,
    seeds: Sequence[int],
    backend: BackendApi,
    settings: TaskRlSettings,
    challenger: AgentFactory,
    incumbent: AgentFactory,
    opponents: Mapping[str, AgentFactory],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    started = time.perf_counter()
    challenger_population: list[dict[str, object]] = []
    incumbent_population: list[dict[str, object]] = []
    matchups: dict[str, object] = {}
    for opponent_id, opponent in opponents.items():
        challenger_rows, challenger_summary = run_paired_panel(
            backend,
            "unit_task_challenger",
            challenger,
            opponent_id,
            opponent,
            seeds,
            settings,
        )
        incumbent_rows, incumbent_summary = run_paired_panel(
            backend,
            "initial_actor_incumbent",
            incumbent,
            opponent_id,
            opponent,
            seeds,
            settings,
        )
        challenger_population.extend(challenger_rows)
        incumbent_population.extend(incumbent_rows)
        matchups[opponent_id] = {
            "challenger": challenger_summary,
            "incumbent": incumbent_summary,
            "paired_outcome_comparison": compare_paired_outcomes(
                challenger_rows, incumbent_rows
            ),
        }
    head_rows, head_summary = run_paired_panel(
        backend,
        "unit_task_challenger",
        challenger,
        "initial_actor_incumbent",
        incumbent,
        seeds,
        settings,
    )
    population_comparison = compare_paired_outcomes(
        challenger_population,
        incumbent_population,
    )
    rows = [*challenger_population, *incumbent_population, *head_rows]
    return (
        {
            "name": name,
            "seeds": list(seeds),
            "matchups": matchups,
            "population": {
                "challenger": summarize_games(challenger_population),
                "incumbent": summarize_games(incumbent_population),
                "paired_outcome_comparison": population_comparison,
            },
            "head_to_head": head_summary,
            "elapsed_seconds": time.perf_counter() - started,
        },
        rows,
    )


def _population_comparison(phase: Mapping[str, object]) -> Mapping[str, object]:
    population = cast(Mapping[str, object], phase["population"])
    return cast(Mapping[str, object], population["paired_outcome_comparison"])


def evaluate_task_tape(
    raw_settings: TaskRlSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Apply selection and conditional confirmation on direct paired W/D/L."""
    root = repository_root.resolve()
    settings = resolve_task_settings(raw_settings, root)
    report_path = settings.output_dir / "evaluation-report.json"
    games_path = settings.output_dir / "evaluation-games.json"
    if report_path.exists() or games_path.exists():
        raise FileExistsError("unit-task evaluation outputs already exist")
    training = _training_report(settings.output_dir)
    checkpoint = _checkpoint(settings.output_dir, training)
    _validate_training_initialization(training, settings)
    backend = load_backend(root)
    resolved_environment = cast(
        dict[str, object],
        backend.engine(seed=0, configuration=settings.environment).configuration,
    )
    settings = settings.model_copy(update={"environment": resolved_environment})
    _validate_resolved_profile(settings.output_dir, settings)
    challenger = _challenger_factory(backend, settings, checkpoint)
    incumbent, incumbent_artifact = incumbent_factory(settings.incumbent)
    training_artifacts = training.get("opponents")
    if (
        not isinstance(training_artifacts, Mapping)
        or training_artifacts.get("named_incumbent") != incumbent_artifact
    ):
        raise ValueError("unit-task named incumbent differs from its training run")
    opponents, opponent_identities, public_count = _opponent_factories(
        backend, settings
    )
    expected_transitions = _integer(
        resolved_environment["episodeSteps"], "episodeSteps"
    ) - 1
    selection, selection_rows = _phase(
        "selection",
        settings.selection_seeds,
        backend,
        settings,
        challenger,
        incumbent,
        opponents,
    )
    selection_valid = _valid(selection_rows, expected_transitions)
    selection_passed = (
        selection_valid
        and _strict_improvement(_population_comparison(selection))
        and _strict_improvement(
            cast(Mapping[str, object], selection["head_to_head"])
        )
    )
    confirmation: dict[str, object] | None = None
    confirmation_rows: list[dict[str, object]] = []
    if selection_passed:
        confirmation, confirmation_rows = _phase(
            "confirmation",
            settings.confirmation_seeds,
            backend,
            settings,
            challenger,
            incumbent,
            opponents,
        )
    confirmation_valid = confirmation is not None and _valid(
        confirmation_rows, expected_transitions
    )
    current_source = source_identity(root)
    training_source = training.get("source")
    clean_source = (
        isinstance(training_source, Mapping)
        and not bool(training_source.get("worktree_dirty", True))
        and not bool(current_source["worktree_dirty"])
        and training_source.get("commit") == current_source["commit"]
        and training_source.get("source_tree_sha256")
        == current_source["source_tree_sha256"]
    )
    decision = advancement_decision(
        selection_population=_population_comparison(selection),
        selection_head_to_head=cast(
            Mapping[str, object], selection["head_to_head"]
        ),
        confirmation_population=(
            _population_comparison(confirmation)
            if confirmation is not None
            else None
        ),
        confirmation_head_to_head=(
            cast(Mapping[str, object], confirmation["head_to_head"])
            if confirmation is not None
            else None
        ),
        evidence_valid=training.get("status") == "training_complete"
        and selection_valid
        and (bool(confirmation_valid) if confirmation is not None else True),
        clean_source=clean_source,
        public_opponents=public_count,
    )
    all_rows = [*selection_rows, *confirmation_rows]
    games_path.write_text(
        json.dumps(all_rows, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    result: dict[str, object] = {
        "schema_version": "unit-task-evaluation-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "source": current_source,
        "training_source": training_source,
        "resolved_settings": settings.model_dump(mode="json"),
        "decision_surface": ["win", "loss", "tie"],
        "diagnostic_surface": ["terminal cash", "cash difference"],
        "selection": selection,
        "confirmation": confirmation
        or {
            "status": "skipped",
            "reason": "selection paired W/D/L gate did not pass",
            "seeds_reserved": list(settings.confirmation_seeds),
        },
        "decision": decision,
        "execution": {
            "act_timeout_seconds": settings.act_timeout_seconds,
            "remaining_overage_seconds": settings.remaining_overage_seconds,
            "timeout_enforced": True,
            "expected_transitions_per_game": expected_transitions,
            "all_matches_valid": selection_valid
            and (bool(confirmation_valid) if confirmation is not None else True),
        },
        "opponents": opponent_identities,
        "incumbent": incumbent_artifact,
        "checkpoint": {
            "path": str(checkpoint),
            "sha256": sha256_file(checkpoint),
        },
        "training_report": {
            "path": str(settings.output_dir / "training-report.json"),
            "sha256": sha256_file(settings.output_dir / "training-report.json"),
        },
        "games": {
            "path": str(games_path),
            "sha256": sha256_file(games_path),
            "count": len(all_rows),
        },
    }
    report_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return result


__all__ = ["evaluate_task_tape"]
